# -*- coding: utf-8 -*-
"""主窗口：菜单、工具栏、数据表与图形面板的组织。"""
from __future__ import annotations

import os

import numpy as np

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap, QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QSplitter, QFileDialog, QMessageBox,
    QApplication, QToolBar, QLabel, QWidget, QStyle, QDialog, QVBoxLayout,
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit,
    QCheckBox, QComboBox, QFormLayout, QDialogButtonBox,
)

from matplotlib.figure import Figure

from . import styles, plotstyle
from .worksheet import WorkSheet, WorkSheetView
from .plotting import PlotCanvas, PlotConfigDialog, build_plot, export_figure
from .statistics import StatisticsDialog
from .fitting import FitDialog, predict
from .bio import BioAnalysisDialog


def _app_icon() -> QIcon:
    """程序化绘制应用图标：深蓝底 + 折线图。"""
    pm = QPixmap(128, 128)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    # 圆角底
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#2b6cb0"))
    p.drawRoundedRect(0, 0, 128, 128, 20, 20)
    # 网格参考点
    pts = [(22, 88), (50, 58), (72, 72), (96, 40)]
    # 折线
    pen = QPen(QColor("white"), 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline([__import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(x, y) for x, y in pts])
    # 数据点
    p.setPen(Qt.NoPen)
    p.setBrush(QColor("#e08a1e"))
    for x, y in pts:
        p.drawEllipse(x - 7, y - 7, 14, 14)
    # 坐标轴
    pen2 = QPen(QColor("white"), 4, Qt.SolidLine, Qt.RoundCap)
    pen2.setColor(QColor(255, 255, 255, 200))
    p.setPen(pen2)
    p.drawLine(22, 96, 22, 24)
    p.drawLine(22, 96, 110, 96)
    p.end()
    return QIcon(pm)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark = False
        self.sheet_counter = 1
        self.plot_counter = 1
        self.setWindowTitle("SciPlot —— 科学数据分析与绘图")
        self.resize(1280, 800)
        self.setWindowIcon(_app_icon())

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_statusbar()
        self._apply_theme()

        # 初始空工作表
        self._new_sheet()

    # ------------------------------------------------------------------
    # UI 构建
    # ------------------------------------------------------------------
    def _build_ui(self):
        splitter = QSplitter(Qt.Horizontal)
        # 左侧数据表
        self.data_tabs = QTabWidget()
        self.data_tabs.setTabsClosable(True)
        self.data_tabs.tabCloseRequested.connect(self._close_sheet)
        self.data_tabs.currentChanged.connect(self._update_status)
        # 右侧图形
        self.plot_tabs = QTabWidget()
        self.plot_tabs.setTabsClosable(True)
        self.plot_tabs.tabCloseRequested.connect(self._close_plot)
        self.plot_tabs.setDocumentMode(False)
        splitter.addWidget(self.data_tabs)
        splitter.addWidget(self.plot_tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([560, 700])
        self.setCentralWidget(splitter)

    def _build_menu(self):
        mb = self.menuBar()

        # 文件
        m_file = mb.addMenu("文件(&F)")
        m_file.addAction(self._act("新建工作表", self._new_sheet, "Ctrl+N"))
        m_file.addAction(self._act("导入数据…", self._import_data, "Ctrl+O"))
        m_file.addSeparator()
        m_file.addAction(self._act("保存工作表…", self._save_sheet, "Ctrl+S"))
        m_file.addAction(self._act("工作表另存为 Excel…", self._save_sheet_excel))
        m_file.addSeparator()
        m_file.addAction(self._act("导出当前图形…", self._export_current_plot, "Ctrl+E"))
        m_file.addSeparator()
        m_file.addAction(self._act("退出", self.close, "Ctrl+Q"))

        # 数据
        m_data = mb.addMenu("数据(&D)")
        m_data.addAction(self._act("添加列", self._add_column))
        m_data.addAction(self._act("插入行", self._insert_row))
        m_data.addAction(self._act("删除选中行", self._delete_selected_rows))
        m_data.addSeparator()
        m_data.addAction(self._act("转置工作表", self._transpose))

        # 绘图
        m_plot = mb.addMenu("绘图(&P)")
        m_plot.addAction(self._act("新建图形…", self._new_plot, "Ctrl+G"))

        # 分析
        m_ana = mb.addMenu("分析(&A)")
        m_ana.addAction(self._act("统计分析…", self._statistics))
        m_ana.addAction(self._act("曲线拟合…", self._fitting))
        m_ana.addSeparator()
        m_ana.addAction(self._act("化学 / 生物分析…", self._bio_analysis))

        # 视图
        m_view = mb.addMenu("视图(&V)")
        self.act_theme = self._act("切换深色主题", self._toggle_theme)
        m_view.addAction(self.act_theme)

        # 帮助
        m_help = mb.addMenu("帮助(&H)")
        m_help.addAction(self._act("关于 SciPlot", self._about))

    def _build_toolbar(self):
        tb = QToolBar("主工具栏")
        tb.setObjectName("main_toolbar")
        tb.setMovable(False)
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        style = self.style()
        def add(icon, text, slot, tip):
            a = QAction(icon, text, self)
            a.triggered.connect(slot)
            a.setToolTip(tip)
            tb.addAction(a)
            return a

        add(style.standardIcon(QStyle.SP_FileIcon), "新建", self._new_sheet, "新建工作表 (Ctrl+N)")
        add(style.standardIcon(QStyle.SP_DialogOpenButton), "导入", self._import_data, "导入数据 (Ctrl+O)")
        add(style.standardIcon(QStyle.SP_DialogSaveButton), "保存", self._save_sheet, "保存工作表 (Ctrl+S)")
        tb.addSeparator()
        self.act_plot_tb = add(self._line_icon(), "绘图", self._new_plot, "新建图形 (Ctrl+G)")
        tb.addSeparator()
        add(self._stats_icon(), "统计", self._statistics, "统计分析")
        add(self._fit_icon(), "拟合", self._fitting, "曲线拟合")
        add(self._bio_icon(), "化生分析", self._bio_analysis, "化学/生物分析")
        tb.addSeparator()
        self.act_theme_tb = add(style.standardIcon(QStyle.SP_BrowserReload), "主题", self._toggle_theme, "切换深色/浅色主题")

    def _build_statusbar(self):
        self.status_lbl = QLabel("就绪")
        self.dim_lbl = QLabel("")
        self.statusBar().addWidget(self.status_lbl, 1)
        self.statusBar().addPermanentWidget(self.dim_lbl)

    def _act(self, text, slot, shortcut=None):
        a = QAction(text, self)
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        return a

    # ------------------------------------------------------------------
    # 程序化图标
    # ------------------------------------------------------------------
    def _line_icon(self):
        pm = QPixmap(20, 20); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#2b6cb0"), 2, Qt.SolidLine, Qt.RoundCap))
        p.drawPolyline([__import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(2, 16),
                        __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(7, 9),
                        __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(11, 12),
                        __import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(18, 4)])
        p.setPen(Qt.NoPen); p.setBrush(QColor("#d64541"))
        for x, y in [(2, 16), (7, 9), (11, 12), (18, 4)]:
            p.drawEllipse(x - 2, y - 2, 4, 4)
        p.end()
        return QIcon(pm)

    def _stats_icon(self):
        pm = QPixmap(20, 20); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        for x, h in [(2, 16), (6, 10), (10, 13), (14, 6), (17, 9)]:
            p.setBrush(QColor("#2e6da4"))
            p.drawRoundedRect(x, 20 - h, 3, h, 1, 1)
        p.end()
        return QIcon(pm)

    def _fit_icon(self):
        pm = QPixmap(20, 20); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#3a7d44"), 2, Qt.SolidLine, Qt.RoundCap))
        import math
        pts = []
        for i in range(21):
            x = i
            y = 18 - (math.exp(i / 20 * 2.2) - 1) / (math.exp(2.2) - 1) * 14
            pts.append(__import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(x, int(y)))
        p.drawPolyline(pts)
        p.end()
        return QIcon(pm)

    def _bio_icon(self):
        pm = QPixmap(20, 20); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#7b4b94"), 2, Qt.SolidLine, Qt.RoundCap))
        # 六边形（分子）
        import math
        pts = []
        cx, cy, r = 10, 10, 6
        for i in range(7):
            a = i * 2 * math.pi / 6 - math.pi / 2
            pts.append(__import__("PySide6.QtCore", fromlist=["QPoint"]).QPoint(int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
        p.drawPolygon(pts)
        p.end()
        return QIcon(pm)

    # ------------------------------------------------------------------
    # 主题
    # ------------------------------------------------------------------
    def _apply_theme(self):
        QApplication.instance().setStyleSheet(styles.get_qss(self.dark))
        pal = styles.get_palette(self.dark)
        # matplotlib 背景同步
        plotstyle.rcParams["figure.facecolor"] = pal["panel"]
        plotstyle.rcParams["axes.facecolor"] = pal["panel"]
        plotstyle.rcParams["axes.edgecolor"] = pal["text"]
        plotstyle.rcParams["axes.labelcolor"] = pal["text"]
        plotstyle.rcParams["text.color"] = pal["text"]
        plotstyle.rcParams["xtick.color"] = pal["text"]
        plotstyle.rcParams["ytick.color"] = pal["text"]

    def _toggle_theme(self):
        self.dark = not self.dark
        self._apply_theme()

    # ------------------------------------------------------------------
    # 工作表管理
    # ------------------------------------------------------------------
    def current_sheet_view(self) -> WorkSheetView | None:
        w = self.data_tabs.currentWidget()
        return w if isinstance(w, WorkSheetView) else None

    def _new_sheet(self):
        ws = WorkSheet(f"工作表{self.sheet_counter}")
        self.sheet_counter += 1
        view = WorkSheetView(ws)
        view.data_changed.connect(self._update_status)
        view.status_message.connect(lambda m: self.status_lbl.setText(m))
        self.data_tabs.addTab(view, ws.name)
        self.data_tabs.setCurrentWidget(view)
        self._update_status()

    def _import_data(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "导入数据", "",
            "数据文件 (*.csv *.txt *.dat *.xlsx *.xls);;CSV (*.csv);;文本 (*.txt *.dat);;Excel (*.xlsx *.xls);;所有文件 (*)")
        if not path:
            return
        try:
            ws = WorkSheet.from_file(path)
            view = WorkSheetView(ws)
            view.data_changed.connect(self._update_status)
            self.data_tabs.addTab(view, ws.name)
            self.data_tabs.setCurrentWidget(view)
            self.status_lbl.setText(f"已导入 {os.path.basename(path)}")
            self._update_status()
        except Exception as e:
            QMessageBox.critical(self, "导入失败", f"无法读取文件：\n{e}")

    def _close_sheet(self, idx):
        self.data_tabs.removeTab(idx)

    def _save_sheet(self):
        view = self.current_sheet_view()
        if not view:
            return
        path, _ = QFileDialog.getSaveFileName(self, "保存工作表", "数据.csv", "CSV (*.csv)")
        if not path:
            return
        view._commit_pending()
        view.sheet.to_csv(path)
        self.status_lbl.setText(f"已保存 {os.path.basename(path)}")

    def _save_sheet_excel(self):
        view = self.current_sheet_view()
        if not view:
            return
        path, _ = QFileDialog.getSaveFileName(self, "导出 Excel", "数据.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        view._commit_pending()
        view.sheet.to_excel(path)
        self.status_lbl.setText(f"已导出 {os.path.basename(path)}")

    def _add_column(self):
        view = self.current_sheet_view()
        if not view:
            return
        view._commit_pending()
        view.sheet.add_column()
        view.reload()

    def _insert_row(self):
        view = self.current_sheet_view()
        if not view:
            return
        view._commit_pending()
        for col in view.sheet.columns:
            col["values"].append("")
        view.reload()

    def _delete_selected_rows(self):
        view = self.current_sheet_view()
        if view:
            view._delete_rows()

    def _transpose(self):
        view = self.current_sheet_view()
        if not view:
            return
        view._commit_pending()
        ws = view.sheet
        ncols, nrows = ws.ncols(), ws.nrows()
        new_cols = []
        for ri in range(nrows):
            vals = [c["values"][ri] if ri < len(c["values"]) else "" for c in ws.columns]
            new_cols.append({"name": f"R{ri+1}", "ctype": "Y" if ri > 0 else "X", "values": vals})
        ws.columns = new_cols
        view.reload()

    # ------------------------------------------------------------------
    # 图形管理
    # ------------------------------------------------------------------
    def _add_plot_tab(self, fig: Figure, title: str):
        canvas = PlotCanvas(figure=fig)
        self.plot_tabs.addTab(canvas, title)
        self.plot_tabs.setCurrentWidget(canvas)

    def _current_plot_canvas(self):
        w = self.plot_tabs.currentWidget()
        return w if isinstance(w, PlotCanvas) else None

    def _close_plot(self, idx):
        self.plot_tabs.removeTab(idx)

    def _new_plot(self):
        view = self.current_sheet_view()
        if not view:
            QMessageBox.information(self, "提示", "请先新建或导入数据。")
            return
        view._commit_pending()
        dlg = PlotConfigDialog(view.sheet, self)
        if dlg.exec():
            try:
                fig = build_plot(dlg.cfg)
                title = f"图形{self.plot_counter}"
                self.plot_counter += 1
                self._add_plot_tab(fig, title)
                self.status_lbl.setText("图形已创建")
            except Exception as e:
                QMessageBox.critical(self, "绘图失败", str(e))

    def _export_current_plot(self):
        canvas = self._current_plot_canvas()
        if canvas:
            export_figure(canvas.figure, self)

    # ------------------------------------------------------------------
    # 分析
    # ------------------------------------------------------------------
    def _statistics(self):
        view = self.current_sheet_view()
        if not view:
            QMessageBox.information(self, "提示", "请先新建或导入数据。")
            return
        view._commit_pending()
        dlg = StatisticsDialog(view.sheet, self)
        dlg.exec()

    def _fitting(self):
        view = self.current_sheet_view()
        if not view:
            QMessageBox.information(self, "提示", "请先新建或导入数据。")
            return
        view._commit_pending()
        dlg = FitDialog(view.sheet, self, plot_callback=self._show_fit_plot)
        dlg.exec()

    def _show_fit_plot(self, result):
        x, y, popt, model, y_pred, r2, adj_r2, rmse, x_idx, y_idx = result
        fig = Figure(figsize=(6.5, 4.8), dpi=100)
        ax = fig.add_subplot(111)
        ax.scatter(x, y, s=40, color="#2e6da4", edgecolors="white",
                   linewidths=0.8, zorder=3, label="实验数据")
        xs = np.linspace(min(x), max(x), 400)
        ax.plot(xs, model.func(xs, *popt), "-", color="#d64541", linewidth=2,
                label="拟合曲线")
        ax.set_xlabel(self._col_name(x_idx))
        ax.set_ylabel(self._col_name(y_idx))
        ax.legend(frameon=False)
        ax.set_title(f"曲线拟合  R² = {r2:.4f}", pad=10)
        fig.tight_layout()
        title = f"拟合图{self.plot_counter}"
        self.plot_counter += 1
        self._add_plot_tab(fig, title)

    def _col_name(self, idx):
        view = self.current_sheet_view()
        if view and 0 <= idx < view.sheet.ncols():
            return view.sheet.columns[idx]["name"]
        return ""

    def _bio_analysis(self):
        view = self.current_sheet_view()
        if not view:
            QMessageBox.information(self, "提示", "请先新建或导入数据。")
            return
        view._commit_pending()
        dlg = BioAnalysisDialog(view.sheet, self, plot_callback=self._show_bio_fig)
        dlg.exec()

    def _show_bio_fig(self, fig, title):
        self._add_plot_tab(fig, title)

    # ------------------------------------------------------------------
    # 状态与关于
    # ------------------------------------------------------------------
    def _update_status(self):
        view = self.current_sheet_view()
        if view:
            n = view.sheet.nrows()
            c = view.sheet.ncols()
            self.dim_lbl.setText(f"{view.sheet.name}  |  {c} 列 × {n} 行")
        else:
            self.dim_lbl.setText("")

    def _about(self):
        QMessageBox.about(
            self, "关于 SciPlot",
            "<h3>SciPlot 科学数据分析与绘图</h3>"
            "<p>版本 1.0.0</p>"
            "<p>面向化学与生物学实验数据处理的桌面软件。</p>"
            "<p>主要功能：<br>"
            "· 数据工作表与多格式导入导出<br>"
            "· 专业科学作图（折线/散点/柱状/箱线/直方图/饼图）<br>"
            "· 统计分析（t 检验、ANOVA、相关分析）<br>"
            "· 曲线拟合（线性/多项式/非线性）<br>"
            "· 化学/生物专用（酶动力学、标准曲线、IC50、峰分析）</p>")
