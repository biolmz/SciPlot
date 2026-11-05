# -*- coding: utf-8 -*-
"""绘图引擎：专业科学作图。

- matplotlib 嵌入 Qt，交互式缩放/平移
- 折线 / 散点 / 柱状 / 箱线 / 直方图 / 饼图
- 多曲线叠加、误差棒、双 Y 轴
- 坐标轴自定义、对数轴、网格、图例、标题
- 导出 PNG / SVG / PDF / EPS / EMF
"""
from __future__ import annotations

import os

import numpy as np

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QSizePolicy,
    QDialog, QFormLayout, QComboBox, QPushButton, QCheckBox, QLabel,
    QListWidget, QListWidgetItem, QGroupBox, QGridLayout, QSpinBox,
    QDoubleSpinBox, QDialogButtonBox, QTabWidget, QLineEdit, QColorDialog,
    QMessageBox, QFileDialog, QSplitter,
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from . import plotstyle
from .worksheet import WorkSheet, CTYPE_X, CTYPE_Y, CTYPE_Z, CTYPE_LABEL, CTYPE_YERR, CTYPE_XERR, CTYPE_IGNORE


# ---------------------------------------------------------------------------
# 画布 + 工具栏
# ---------------------------------------------------------------------------
_TOOLBAR_TRANSLATION = {
    "Home": "复位视图", "Back": "后退视图", "Forward": "前进视图",
    "Pan": "平移", "Zoom": "框选缩放", "Subplots": "子图设置",
    "Customize": "更多设置", "Save": "保存图像",
}


class SciNavToolbar(NavigationToolbar2QT):
    """中文化的导航工具栏。"""

    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)
        self.setMovable(False)
        self.setIconSize(self.iconSize() * 0.85)
        self._translate()

    def _translate(self):
        for a in self.actions():
            txt = a.text()
            for k, v in _TOOLBAR_TRANSLATION.items():
                if txt == k:
                    a.setText(v)
                    a.setToolTip(v)
            if txt == "Save":
                a.setText("保存图像")
                a.setToolTip("保存图像")


class PlotCanvas(QWidget):
    """包含 Figure、Canvas 与导航工具栏的绘图面板。"""

    def __init__(self, parent=None, figure=None):
        super().__init__(parent)
        self.figure = figure if figure is not None else Figure(figsize=(6.5, 4.8), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = SciNavToolbar(self.canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, 1)

        self._ax = None

    def clear(self):
        self.figure.clear()
        self.canvas.draw_idle()

    def set_axes(self, ax):
        self._ax = ax
        self.canvas.draw_idle()

    def replace_figure(self, fig):
        """用新的 Figure 替换当前画布。"""
        self.layout().removeWidget(self.toolbar)
        self.layout().removeWidget(self.canvas)
        self.toolbar.deleteLater()
        self.canvas.deleteLater()
        self.figure = fig
        self.canvas = FigureCanvasQTAgg(fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = SciNavToolbar(self.canvas, self)
        self.layout().addWidget(self.toolbar)
        self.layout().addWidget(self.canvas, 1)


# ---------------------------------------------------------------------------
# 绘图核心
# ---------------------------------------------------------------------------
PLOT_TYPES = {
    "line": "折线图",
    "scatter": "散点图",
    "line_scatter": "折线+散点",
    "bar": "柱状图",
    "box": "箱线图",
    "hist": "直方图",
    "pie": "饼图",
    "area": "面积图",
    "step": "阶梯图",
    "errorbar": "误差棒图",
}

MARKERS = {
    "无": "", "圆点": "o", "方块": "s", "三角": "^", "倒三角": "v",
    "菱形": "D", "五角星": "*", "十字": "+", "叉": "x",
}

LINESTYLES = {
    "实线": "-", "虚线": "--", "点线": ":", "点划线": "-.", "无": "",
}

COLOR_NAMES = {
    "自动": None, "深蓝": "#1f2a44", "红": "#d64541", "蓝": "#2e6da4",
    "绿": "#3a7d44", "橙": "#e08a1e", "紫": "#7b4b94", "青": "#1f8a8a",
    "黑": "#111111", "灰": "#888888", "粉": "#c0397a", "棕": "#8a6d3b",
}


def _series_colors(n):
    cols = plotstyle.get_colors("default")
    return [cols[i % len(cols)] for i in range(n)]


def build_plot(cfg: dict) -> Figure:
    """根据配置字典绘制图形，返回 Figure。cfg 由 PlotConfigDialog 产出。"""
    fig = Figure(figsize=(cfg.get("fig_w", 6.5), cfg.get("fig_h", 4.8)), dpi=100)
    ptype = cfg["ptype"]
    sheet: WorkSheet = cfg["sheet"]

    # 饼图 / 直方图 / 箱线图：单轴特殊处理
    if ptype == "pie":
        _draw_pie(fig, cfg, sheet)
        return fig
    if ptype == "hist":
        _draw_hist(fig, cfg, sheet)
        return fig
    if ptype == "box":
        _draw_box(fig, cfg, sheet)
        return fig

    # 常规 XY 图
    ax = fig.add_subplot(111)
    x_idx = cfg.get("x_idx")
    y_indices = cfg.get("y_indices") or []
    colors = _series_colors(max(len(y_indices), 1))

    marker_cn = cfg.get("marker", "无")
    marker = MARKERS.get(marker_cn, "o")
    for k, y_idx in enumerate(y_indices):
        color = cfg.get("colors", {}).get(y_idx) or colors[k % len(colors)]
        label = cfg.get("labels", {}).get(y_idx) or sheet.columns[y_idx]["name"]
        xs, ys = sheet.numeric_pairs(x_idx, y_idx)

        ls = cfg.get("linestyle", "实线")
        lw = cfg.get("linewidth", 1.5)
        ms = cfg.get("markersize", 5)

        # 误差列
        yerr = None
        xerr = None
        err_y = cfg.get("err_y", {}).get(y_idx)
        err_x = cfg.get("err_x", {}).get(y_idx)
        if err_y is not None:
            yerr = sheet.numeric_data(err_y)
        if err_x is not None:
            xerr = sheet.numeric_data(err_x)

        if ptype == "scatter":
            ax.scatter(xs, ys, s=ms * ms, c=color, marker=marker or "o",
                       label=label, edgecolors="white", linewidths=0.5, zorder=3)
        elif ptype == "line":
            ax.plot(xs, ys, color=color, linestyle=LINESTYLES[ls], linewidth=lw,
                    label=label, zorder=3)
        elif ptype == "line_scatter":
            ax.plot(xs, ys, color=color, linestyle=LINESTYLES[ls], linewidth=lw,
                    marker=marker or "o", markersize=ms, label=label,
                    markerfacecolor=color, markeredgecolor="white",
                    markeredgewidth=0.5, zorder=3)
        elif ptype == "bar":
            ax.bar(xs, ys, color=color, label=label, alpha=0.85, zorder=3)
        elif ptype == "area":
            ax.fill_between(xs, ys, color=color, alpha=0.35, label=label, zorder=2)
            ax.plot(xs, ys, color=color, linewidth=lw, zorder=3)
        elif ptype == "step":
            ax.step(xs, ys, where="mid", color=color, linewidth=lw, label=label, zorder=3)
        elif ptype == "errorbar":
            ax.errorbar(xs, ys, yerr=yerr, xerr=xerr, fmt=marker or "o",
                        color=color, linewidth=lw, markersize=ms, capsize=3,
                        label=label, zorder=3)

    _apply_axis_style(ax, cfg, sheet, x_idx, y_indices)

    # 图例
    if cfg.get("show_legend", True) and y_indices:
        loc_map = {"右上": "best", "右下": "lower right", "左上": "upper left",
                   "左下": "lower left", "上中": "upper center", "图外": "upper right"}
        ax.legend(loc=loc_map.get(cfg.get("legend_loc", "右上"), "best"),
                  frameon=cfg.get("legend_frame", False))

    fig.tight_layout()
    return fig


def _apply_axis_style(ax, cfg, sheet, x_idx, y_indices):
    """统一坐标轴样式。"""
    title = cfg.get("title", "")
    if title:
        ax.set_title(title, pad=12)
    xlabel = cfg.get("xlabel") or (
        sheet.columns[x_idx]["name"] if x_idx is not None else "")
    ylabel = cfg.get("ylabel")
    if ylabel:
        ax.set_ylabel(ylabel)
    elif len(y_indices) == 1:
        ax.set_ylabel(sheet.columns[y_indices[0]]["name"])
    if xlabel:
        ax.set_xlabel(xlabel)

    # 范围
    xmin = cfg.get("xmin"); xmax = cfg.get("xmax")
    ymin = cfg.get("ymin"); ymax = cfg.get("ymax")
    if xmin is not None and xmax is not None and xmin < xmax:
        ax.set_xlim(xmin, xmax)
    if ymin is not None and ymax is not None and ymin < ymax:
        ax.set_ylim(ymin, ymax)

    # 对数轴
    if cfg.get("log_x"):
        ax.set_xscale("log")
    if cfg.get("log_y"):
        ax.set_yscale("log")

    # 网格
    if cfg.get("grid"):
        ax.grid(True, axis="both", linestyle="--", linewidth=0.6, color="#c9c9c9", alpha=0.7)
        ax.set_axisbelow(True)


def _draw_pie(fig, cfg, sheet):
    ax = fig.add_subplot(111)
    val_idx = cfg["y_indices"][0] if cfg.get("y_indices") else 0
    lbl_idx = cfg.get("label_idx")
    vals = sheet.numeric_data(val_idx)
    labels = None
    if lbl_idx is not None:
        labels = [str(v) for v in sheet.columns[lbl_idx]["values"]]
    colors = _series_colors(len(vals))
    wedges, texts, autotexts = ax.pie(
        vals, labels=labels, autopct="%1.1f%%", colors=colors,
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=1.2))
    for t in autotexts:
        t.set_color("white"); t.set_fontsize(9)
    for t in texts:
        t.set_fontsize(10)
    if cfg.get("title"):
        ax.set_title(cfg["title"], pad=12)
    ax.set_aspect("equal")
    fig.tight_layout()


def _draw_hist(fig, cfg, sheet):
    ax = fig.add_subplot(111)
    val_idx = cfg["y_indices"][0] if cfg.get("y_indices") else 0
    vals = sheet.numeric_data(val_idx)
    bins = cfg.get("bins", 10) or 10
    color = cfg.get("colors", {}).get(val_idx) or plotstyle.get_colors()[1]
    ax.hist(vals, bins=bins, color=color, edgecolor="white", alpha=0.85,
            density=cfg.get("density", False))
    if cfg.get("title"):
        ax.set_title(cfg["title"], pad=12)
    xlbl = cfg.get("xlabel") or sheet.columns[val_idx]["name"]
    if xlbl:
        ax.set_xlabel(xlbl)
    ax.set_ylabel("频数" if not cfg.get("density", False) else "频率密度")
    if cfg.get("grid"):
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, color="#c9c9c9", alpha=0.7)
    fig.tight_layout()


def _draw_box(fig, cfg, sheet):
    ax = fig.add_subplot(111)
    y_indices = cfg.get("y_indices") or []
    data, names, colors = [], [], []
    cols = _series_colors(max(len(y_indices), 1))
    for k, yi in enumerate(y_indices):
        d = sheet.numeric_data(yi)
        if len(d):
            data.append(d)
            names.append(cfg.get("labels", {}).get(yi) or sheet.columns[yi]["name"])
            colors.append(cfg.get("colors", {}).get(yi) or cols[k % len(cols)])
    if not data:
        return
    bp = ax.boxplot(data, labels=names, patch_artist=True, showmeans=True,
                    meanprops=dict(marker="D", markerfacecolor="white",
                                   markeredgecolor="black", markersize=6))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    if cfg.get("title"):
        ax.set_title(cfg["title"], pad=12)
    if cfg.get("ylabel"):
        ax.set_ylabel(cfg["ylabel"])
    if cfg.get("grid"):
        ax.grid(True, axis="y", linestyle="--", linewidth=0.6, color="#c9c9c9", alpha=0.7)
        ax.set_axisbelow(True)
    fig.tight_layout()


# ---------------------------------------------------------------------------
# 绘图配置对话框
# ---------------------------------------------------------------------------
class PlotConfigDialog(QDialog):
    """专业绘图设置对话框，返回配置字典。"""

    def __init__(self, sheet: WorkSheet, parent=None):
        super().__init__(parent)
        self.sheet = sheet
        self.cfg = None
        self.setWindowTitle("新建图形")
        self.setMinimumSize(720, 560)
        self._build()
        self._refresh_y_list()

    def _build(self):
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        # ---- 页1：图类型与数据 ----
        page1 = QWidget()
        g = QGridLayout(page1)
        g.setContentsMargins(12, 12, 12, 12)

        g.addWidget(QLabel("图形类型："), 0, 0)
        self.cmb_type = QComboBox()
        for k, v in PLOT_TYPES.items():
            self.cmb_type.addItem(v, k)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        g.addWidget(self.cmb_type, 0, 1, 1, 2)

        g.addWidget(QLabel("X 数据列："), 1, 0)
        self.cmb_x = QComboBox()
        g.addWidget(self.cmb_x, 1, 1, 1, 2)

        g.addWidget(QLabel("Y 数据列（可多选）："), 2, 0, Qt.AlignTop)
        self.lst_y = QListWidget()
        self.lst_y.setSelectionMode(QListWidget.ExtendedSelection)
        self.lst_y.itemSelectionChanged.connect(self._on_y_selection)
        g.addWidget(self.lst_y, 2, 1, 1, 2)

        g.addWidget(QLabel("标签列（饼图用）："), 3, 0)
        self.cmb_label = QComboBox()
        self.cmb_label.addItem("（无）", None)
        g.addWidget(self.cmb_label, 3, 1, 1, 2)

        # 误差列选择
        g.addWidget(QLabel("Y 误差列："), 4, 0)
        self.cmb_err = QComboBox()
        self.cmb_err.addItem("（无）", None)
        g.addWidget(self.cmb_err, 4, 1, 1, 2)

        g.setColumnStretch(2, 1)
        g.setRowStretch(2, 1)
        tabs.addTab(page1, "类型与数据")

        # ---- 页2：曲线样式 ----
        page2 = QWidget()
        f = QFormLayout(page2)
        f.setContentsMargins(12, 12, 12, 12)
        self.cmb_marker = QComboBox()
        for k in MARKERS:
            self.cmb_marker.addItem(k, k)
        self.cmb_marker.setCurrentText("圆点")
        f.addRow("数据点标记：", self.cmb_marker)

        self.cmb_ls = QComboBox()
        for k in LINESTYLES:
            self.cmb_ls.addItem(k, k)
        self.cmb_ls.setCurrentText("实线")
        f.addRow("线条样式：", self.cmb_ls)

        self.sp_lw = QDoubleSpinBox(); self.sp_lw.setRange(0.1, 10); self.sp_lw.setValue(1.5); self.sp_lw.setSingleStep(0.1)
        f.addRow("线条宽度：", self.sp_lw)

        self.sp_ms = QDoubleSpinBox(); self.sp_ms.setRange(1, 30); self.sp_ms.setValue(6)
        f.addRow("标记大小：", self.sp_ms)

        self.chk_legend = QCheckBox("显示图例"); self.chk_legend.setChecked(True)
        f.addRow("", self.chk_legend)

        self.cmb_legloc = QComboBox()
        for loc in ["右上", "右下", "左上", "左下", "上中", "图外"]:
            self.cmb_legloc.addItem(loc)
        f.addRow("图例位置：", self.cmb_legloc)

        self.chk_legframe = QCheckBox("图例边框")
        f.addRow("", self.chk_legframe)
        tabs.addTab(page2, "曲线样式")

        # ---- 页3：坐标轴 ----
        page3 = QWidget()
        f3 = QFormLayout(page3)
        f3.setContentsMargins(12, 12, 12, 12)
        self.edt_title = QLineEdit()
        f3.addRow("图形标题：", self.edt_title)
        self.edt_xlabel = QLineEdit()
        f3.addRow("X 轴标签：", self.edt_xlabel)
        self.edt_ylabel = QLineEdit()
        f3.addRow("Y 轴标签：", self.edt_ylabel)

        hx = QHBoxLayout()
        self.sp_xmin = QDoubleSpinBox(); self.sp_xmin.setRange(-1e15, 1e15); self.sp_xmin.setDecimals(6)
        self.sp_xmax = QDoubleSpinBox(); self.sp_xmax.setRange(-1e15, 1e15); self.sp_xmax.setDecimals(6)
        self.sp_xmin.setSpecialValueText("自动"); self.sp_xmax.setSpecialValueText("自动")
        self.sp_xmin.setValue(0); self.sp_xmax.setValue(0)
        hx.addWidget(QLabel("最小")); hx.addWidget(self.sp_xmin)
        hx.addWidget(QLabel("最大")); hx.addWidget(self.sp_xmax)
        f3.addRow("X 轴范围：", hx)

        hy = QHBoxLayout()
        self.sp_ymin = QDoubleSpinBox(); self.sp_ymin.setRange(-1e15, 1e15); self.sp_ymin.setDecimals(6)
        self.sp_ymax = QDoubleSpinBox(); self.sp_ymax.setRange(-1e15, 1e15); self.sp_ymax.setDecimals(6)
        self.sp_ymin.setSpecialValueText("自动"); self.sp_ymax.setSpecialValueText("自动")
        self.sp_ymin.setValue(0); self.sp_ymax.setValue(0)
        hy.addWidget(QLabel("最小")); hy.addWidget(self.sp_ymin)
        hy.addWidget(QLabel("最大")); hy.addWidget(self.sp_ymax)
        f3.addRow("Y 轴范围：", hy)

        self.chk_logx = QCheckBox("X 轴对数刻度")
        self.chk_logy = QCheckBox("Y 轴对数刻度")
        self.chk_grid = QCheckBox("显示网格线"); self.chk_grid.setChecked(False)
        f3.addRow("", self.chk_logx)
        f3.addRow("", self.chk_logy)
        f3.addRow("", self.chk_grid)

        hsize = QHBoxLayout()
        self.sp_fw = QDoubleSpinBox(); self.sp_fw.setRange(3, 20); self.sp_fw.setValue(6.5); self.sp_fw.setSingleStep(0.1)
        self.sp_fh = QDoubleSpinBox(); self.sp_fh.setRange(2, 20); self.sp_fh.setValue(4.8); self.sp_fh.setSingleStep(0.1)
        hsize.addWidget(QLabel("宽")); hsize.addWidget(self.sp_fw)
        hsize.addWidget(QLabel("高")); hsize.addWidget(self.sp_fh)
        f3.addRow("画布尺寸(英寸)：", hsize)
        tabs.addTab(page3, "坐标轴")

        # ---- 按钮 ----
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("绘制")
        btns.button(QDialogButtonBox.Cancel).setText("取消")
        btns.accepted.connect(self._on_ok)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def _refresh_y_list(self):
        self.lst_y.blockSignals(True)
        self.lst_y.clear()
        self.cmb_x.clear()
        self.cmb_label.clear(); self.cmb_label.addItem("（无）", None)
        self.cmb_err.clear(); self.cmb_err.addItem("（无）", None)

        for i, c in enumerate(self.sheet.columns):
            disp = f"{c['name']}  [{c['ctype']}]"
            self.cmb_x.addItem(disp, i)
            if c["ctype"] not in (CTYPE_LABEL, CTYPE_IGNORE):
                item = QListWidgetItem(disp)
                item.setData(Qt.UserRole, i)
                self.lst_y.addItem(item)
            if c["ctype"] in (CTYPE_LABEL,):
                self.cmb_label.addItem(disp, i)
            if c["ctype"] in (CTYPE_YERR, CTYPE_XERR, CTYPE_Y, CTYPE_X, CTYPE_Z):
                self.cmb_err.addItem(disp, i)

        # 默认选中
        x_idx, y_idx = self.sheet.default_x_y() if hasattr(self.sheet, "default_x_y") else (None, None)
        from .worksheet import WorkSheetView
        # 简单推断
        if x_idx is None or y_idx is None:
            x_idx = self.cmb_x.itemData(0)
            if self.lst_y.count() > 1:
                y_idx = self.lst_y.item(1).data(Qt.UserRole)
            else:
                y_idx = self.lst_y.item(0).data(Qt.UserRole) if self.lst_y.count() else None
        if x_idx is not None:
            for i in range(self.cmb_x.count()):
                if self.cmb_x.itemData(i) == x_idx:
                    self.cmb_x.setCurrentIndex(i); break
        if y_idx is not None:
            for i in range(self.lst_y.count()):
                if self.lst_y.item(i).data(Qt.UserRole) == y_idx:
                    self.lst_y.item(i).setSelected(True)
        self.lst_y.blockSignals(False)

    def _on_type_changed(self):
        ptype = self.cmb_type.currentData()
        is_single = ptype in ("pie", "hist")
        self.lst_y.setSelectionMode(
            QListWidget.SingleSelection if is_single else QListWidget.ExtendedSelection)

    def _on_y_selection(self):
        pass

    def _on_ok(self):
        y_indices = [self.lst_y.item(i).data(Qt.UserRole)
                     for i in range(self.lst_y.count())
                     if self.lst_y.item(i).isSelected()]
        ptype = self.cmb_type.currentData()
        if not y_indices and ptype not in ("pie",):
            QMessageBox.warning(self, "提示", "请至少选择一个 Y 数据列。")
            return
        x_idx = self.cmb_x.currentData()
        label_idx = self.cmb_label.currentData()
        err_idx = self.cmb_err.currentData()

        def _range(sp):
            v = sp.value()
            return None if v == 0 else v

        self.cfg = {
            "ptype": ptype,
            "sheet": self.sheet,
            "x_idx": x_idx,
            "y_indices": y_indices,
            "label_idx": label_idx,
            "title": self.edt_title.text().strip(),
            "xlabel": self.edt_xlabel.text().strip(),
            "ylabel": self.edt_ylabel.text().strip(),
            "xmin": _range(self.sp_xmin), "xmax": _range(self.sp_xmax),
            "ymin": _range(self.sp_ymin), "ymax": _range(self.sp_ymax),
            "log_x": self.chk_logx.isChecked(),
            "log_y": self.chk_logy.isChecked(),
            "grid": self.chk_grid.isChecked(),
            "marker": self.cmb_marker.currentData(),
            "linestyle": self.cmb_ls.currentData(),
            "linewidth": self.sp_lw.value(),
            "markersize": self.sp_ms.value(),
            "show_legend": self.chk_legend.isChecked(),
            "legend_loc": self.cmb_legloc.currentText(),
            "legend_frame": self.chk_legframe.isChecked(),
            "fig_w": self.sp_fw.value(), "fig_h": self.sp_fh.value(),
            "err_y": {y_indices[0]: err_idx} if err_idx is not None and y_indices else {},
        }
        self.accept()


# ---------------------------------------------------------------------------
# 导出
# ---------------------------------------------------------------------------
EXPORT_FORMATS = {
    "PNG 图像 (*.png)": ".png",
    "SVG 矢量 (*.svg)": ".svg",
    "PDF 文档 (*.pdf)": ".pdf",
    "EPS 矢量 (*.eps)": ".eps",
    "TIFF 图像 (*.tiff)": ".tiff",
}


def export_figure(fig: Figure, parent=None) -> bool:
    """弹出保存对话框并导出图形。"""
    filter_str = ";;".join(EXPORT_FORMATS.keys())
    path, _ = QFileDialog.getSaveFileName(parent, "导出图形", "graph.png", filter_str)
    if not path:
        return False
    ext = os.path.splitext(path)[1].lower()
    if not ext:
        path += ".png"
    try:
        fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
        return True
    except Exception as e:
        QMessageBox.critical(parent, "导出失败", str(e))
        return False
