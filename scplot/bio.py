# -*- coding: utf-8 -*-
"""化学 / 生物学专用分析模块。

- 酶动力学：米氏方程拟合 Km / Vmax，双倒数 (Lineweaver-Burk) 图
- 标准曲线：朗伯-比尔定律线性拟合 + 未知样品浓度反算
- IC50 / EC50：四参数 Logistic 剂量-响应拟合
- 峰分析：寻峰、峰面积积分、半峰宽 (FWHM)
"""
from __future__ import annotations

import numpy as np
from scipy import signal, integrate
from scipy.optimize import curve_fit

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QPushButton,
    QWidget, QLabel, QMessageBox, QTextEdit, QTabWidget, QDoubleSpinBox,
    QGroupBox, QSpinBox, QCheckBox,
)

from .fitting import FitModel, fit_curve, predict, goodness_of_fit, _michaelis


# ---------------------------------------------------------------------------
# 酶动力学
# ---------------------------------------------------------------------------
def enzyme_kinetics(S, v):
    """拟合米氏方程，返回 (Vmax, Km, r2, 模型, 拟合预测)。"""
    S = np.asarray(S, dtype=float); v = np.asarray(v, dtype=float)
    mask = np.isfinite(S) & np.isfinite(v) & (S >= 0) & (v >= 0)
    S, v = S[mask], v[mask]
    if len(S) < 3:
        raise ValueError("至少需要 3 组 [S]-v 数据")
    popt, pcov, model = fit_curve(S, v, "michaelis")
    v_pred = predict(model, popt, S)
    r2, _, _ = goodness_of_fit(v, v_pred, 2)
    return popt[0], popt[1], r2, S, v, v_pred


def enzyme_kinetics_figure(S, v, vmax, km):
    """酶动力学图：主图 + 双倒数子图。"""
    from matplotlib.figure import Figure
    fig = Figure(figsize=(9, 4), dpi=100)
    ax1 = fig.add_subplot(121)
    ss = np.linspace(min(S) * 0.9, max(S) * 1.1, 200)
    ax1.plot(ss, _michaelis(ss, vmax, km), "-", color="#d64541", linewidth=2,
             label="米氏方程拟合")
    ax1.scatter(S, v, s=48, color="#2e6da4", edgecolors="white",
                linewidths=1, zorder=3, label="实验数据")
    ax1.axhline(vmax, color="#888", linestyle="--", linewidth=1)
    ax1.text(max(S) * 0.98, vmax * 0.92, f"Vmax = {vmax:.4g}",
             ha="right", va="bottom", color="#555")
    ax1.set_xlabel("[S] 底物浓度")
    ax1.set_ylabel("v 反应速率")
    ax1.legend(frameon=False, loc="lower right")

    ax2 = fig.add_subplot(122)
    inv_s = 1.0 / S; inv_v = 1.0 / v
    slope = km / vmax; intercept = 1.0 / vmax
    xs = np.linspace(min(inv_s) * 0.8, max(inv_s) * 1.2, 100)
    ax2.plot(xs, slope * xs + intercept, "-", color="#3a7d44", linewidth=2,
             label="Lineweaver-Burk 拟合")
    ax2.scatter(inv_s, inv_v, s=48, color="#2e6da4", edgecolors="white",
                linewidths=1, zorder=3, label="双倒数数据")
    ax2.axhline(intercept, color="#888", linestyle=":", linewidth=1)
    ax2.axvline(-1.0 / km, color="#888", linestyle=":", linewidth=1)
    ax2.set_xlabel("1/[S]")
    ax2.set_ylabel("1/v")
    ax2.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 标准曲线
# ---------------------------------------------------------------------------
def std_curve(conc, abs_):
    """标准曲线线性拟合，返回 (斜率, 截距, r2)。"""
    conc = np.asarray(conc, dtype=float); abs_ = np.asarray(abs_, dtype=float)
    mask = np.isfinite(conc) & np.isfinite(abs_)
    conc, abs_ = conc[mask], abs_[mask]
    if len(conc) < 2:
        raise ValueError("标准曲线至少需要 2 个标准点")
    k, b = np.polyfit(conc, abs_, 1)
    pred = k * conc + b
    ss_res = np.sum((abs_ - pred) ** 2)
    ss_tot = np.sum((abs_ - np.mean(abs_)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return k, b, r2, conc, abs_, pred


def calc_unknown(k, b, abs_val):
    """由吸光度反算浓度。"""
    return (abs_val - b) / k if k != 0 else float("nan")


# ---------------------------------------------------------------------------
# IC50 / EC50
# ---------------------------------------------------------------------------
def _logistic4(x, bottom, top, hillslope, ic50):
    return bottom + (top - bottom) / (1 + (x / ic50) ** hillslope)


def fit_ic50(conc, response):
    """四参数 Logistic 拟合，返回 (ic50, 参数, r2)。"""
    conc = np.asarray(conc, dtype=float); response = np.asarray(response, dtype=float)
    mask = np.isfinite(conc) & np.isfinite(response) & (conc > 0)
    conc, response = conc[mask], response[mask]
    if len(conc) < 4:
        raise ValueError("IC50 拟合至少需要 4 个浓度点")
    bottom = min(response); top = max(response)
    p0 = [bottom, top, 1.0, np.median(conc)]
    try:
        popt, _ = curve_fit(_logistic4, conc, response, p0=p0, maxfev=20000)
    except RuntimeError:
        popt, _ = curve_fit(_logistic4, conc, response, p0=p0, maxfev=200000)
    pred = _logistic4(conc, *popt)
    ss_res = np.sum((response - pred) ** 2)
    ss_tot = np.sum((response - np.mean(response)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return popt[3], popt, r2, conc, response, pred


def ic50_figure(conc, response, popt, ic50):
    from matplotlib.figure import Figure
    fig = Figure(figsize=(6, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    xs = np.logspace(np.log10(min(conc) * 0.8), np.log10(max(conc) * 1.25), 300)
    ax.semilogx(xs, _logistic4(xs, *popt), "-", color="#d64541", linewidth=2,
                label="四参数拟合")
    ax.scatter(conc, response, s=52, color="#2e6da4", edgecolors="white",
               linewidths=1, zorder=3, label="实验数据")
    ax.axvline(ic50, color="#888", linestyle="--", linewidth=1)
    ax.text(ic50 * 1.03, np.mean(response), f"IC50 = {ic50:.4g}",
            color="#555", va="center")
    ax.set_xscale("log")
    ax.set_xlabel("浓度 (对数坐标)")
    ax.set_ylabel("响应 / 抑制率 (%)")
    ax.legend(frameon=False, loc="best")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 峰分析
# ---------------------------------------------------------------------------
def peak_analysis(x, y, height_ratio=0.05, min_distance=1):
    """寻峰并计算峰参数。返回 (peaks_df, figure)。"""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 3:
        raise ValueError("峰分析至少需要 3 个数据点")

    height = np.max(y) * height_ratio
    peaks, props = signal.find_peaks(y, height=height, distance=min_distance)
    if len(peaks) == 0:
        raise ValueError("未检测到明显峰，请降低峰高阈值")

    # 计算 FWHM
    fwhm_list = []
    for p in peaks:
        half = props["peak_heights"][list(peaks).index(p)] / 2
        # 向左找半高点
        left = p
        while left > 0 and y[left] > half:
            left -= 1
        right = p
        while right < len(y) - 1 and y[right] > half:
            right += 1
        fwhm = abs(x[right] - x[left])
        fwhm_list.append(fwhm)

    # 峰面积（梯形积分，整个区间基线为 0 的近似）
    areas = []
    for p in peaks:
        # 积分范围：峰左右各延伸到半高
        left = p
        while left > 0 and y[left] > props["peak_heights"][list(peaks).index(p)] * 0.02:
            left -= 1
        right = p
        while right < len(y) - 1 and y[right] > props["peak_heights"][list(peaks).index(p)] * 0.02:
            right += 1
        area = integrate.trapezoid(y[left:right + 1], x[left:right + 1])
        areas.append(area)

    results = []
    for i, p in enumerate(peaks):
        results.append({
            "峰编号": i + 1,
            "峰位置 (x)": float(x[p]),
            "峰高 (y)": float(props["peak_heights"][i]),
            "半峰宽 FWHM": fwhm_list[i],
            "峰面积": areas[i],
        })
    return results, (x, y, peaks)


def peak_figure(x, y, peaks):
    from matplotlib.figure import Figure
    fig = Figure(figsize=(7, 4.5), dpi=100)
    ax = fig.add_subplot(111)
    ax.plot(x, y, "-", color="#2e6da4", linewidth=1.4)
    ax.scatter(x[peaks], y[peaks], s=70, color="#d64541", edgecolors="white",
               linewidths=1.2, zorder=5, marker="v")
    for i, p in enumerate(peaks, 1):
        ax.annotate(f"{i}", (x[p], y[p]), textcoords="offset points",
                    xytext=(0, 12), ha="center", fontsize=10, color="#d64541",
                    fontweight="bold")
    ax.set_xlabel("x（波长 / 时间 / 保留时间）")
    ax.set_ylabel("y（信号强度）")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# 统一对话框
# ---------------------------------------------------------------------------
class BioAnalysisDialog(QDialog):
    """化学/生物分析工作台。"""

    def __init__(self, sheet, parent=None, plot_callback=None):
        super().__init__(parent)
        self.sheet = sheet
        self.plot_callback = plot_callback
        self.setWindowTitle("化学 / 生物分析")
        self.setMinimumSize(680, 560)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        tabs = QTabWidget()
        root.addWidget(tabs)

        # 酶动力学
        tabs.addTab(self._build_enzyme(), "酶动力学")
        tabs.addTab(self._build_std(), "标准曲线")
        tabs.addTab(self._build_ic50(), "IC50 / EC50")
        tabs.addTab(self._build_peak(), "峰分析")

    def _col_combo(self):
        c = QComboBox()
        for i, col in enumerate(self.sheet.columns):
            if col["ctype"] in ("L", "I"):
                continue
            c.addItem(f"{col['name']}  [{col['ctype']}]", i)
        return c

    def _build_enzyme(self):
        w = QWidget()
        v = QVBoxLayout(w)
        f = QFormLayout()
        self.enz_s = self._col_combo()
        self.enz_v = self._col_combo()
        f.addRow("底物浓度 [S] 列：", self.enz_s)
        f.addRow("反应速率 v 列：", self.enz_v)
        v.addLayout(f)
        btn = QPushButton("拟合米氏方程 (Km / Vmax)")
        btn.setDefault(True)
        btn.clicked.connect(self._run_enzyme)
        v.addWidget(btn)
        self.enz_txt = QTextEdit(); self.enz_txt.setReadOnly(True)
        v.addWidget(self.enz_txt, 1)
        if self.enz_s.count() >= 2:
            self.enz_s.setCurrentIndex(0); self.enz_v.setCurrentIndex(1)
        return w

    def _build_std(self):
        w = QWidget()
        v = QVBoxLayout(w)
        f = QFormLayout()
        self.std_c = self._col_combo()
        self.std_a = self._col_combo()
        f.addRow("标准品浓度列：", self.std_c)
        f.addRow("吸光度列：", self.std_a)
        v.addLayout(f)
        self.std_unknown = QDoubleSpinBox()
        self.std_unknown.setRange(-1e9, 1e9); self.std_unknown.setDecimals(6)
        self.std_unknown.setValue(0)
        f.addRow("未知样品吸光度：", self.std_unknown)
        btn = QPushButton("建立标准曲线并计算浓度")
        btn.setDefault(True)
        btn.clicked.connect(self._run_std)
        v.addWidget(btn)
        self.std_txt = QTextEdit(); self.std_txt.setReadOnly(True)
        v.addWidget(self.std_txt, 1)
        if self.std_c.count() >= 2:
            self.std_c.setCurrentIndex(0); self.std_a.setCurrentIndex(1)
        return w

    def _build_ic50(self):
        w = QWidget()
        v = QVBoxLayout(w)
        f = QFormLayout()
        self.ic_c = self._col_combo()
        self.ic_r = self._col_combo()
        f.addRow("浓度列：", self.ic_c)
        f.addRow("响应/抑制率列：", self.ic_r)
        v.addLayout(f)
        btn = QPushButton("拟合剂量-响应曲线 (IC50 / EC50)")
        btn.setDefault(True)
        btn.clicked.connect(self._run_ic50)
        v.addWidget(btn)
        self.ic_txt = QTextEdit(); self.ic_txt.setReadOnly(True)
        v.addWidget(self.ic_txt, 1)
        if self.ic_c.count() >= 2:
            self.ic_c.setCurrentIndex(0); self.ic_r.setCurrentIndex(1)
        return w

    def _build_peak(self):
        w = QWidget()
        v = QVBoxLayout(w)
        f = QFormLayout()
        self.pk_x = self._col_combo()
        self.pk_y = self._col_combo()
        f.addRow("X 数据列（波长/时间）：", self.pk_x)
        f.addRow("Y 信号列：", self.pk_y)
        self.pk_h = QDoubleSpinBox()
        self.pk_h.setRange(0.001, 1.0); self.pk_h.setDecimals(3); self.pk_h.setSingleStep(0.01)
        self.pk_h.setValue(0.05)
        f.addRow("峰高阈值（相对最高峰）：", self.pk_h)
        self.pk_d = QSpinBox(); self.pk_d.setRange(1, 1000); self.pk_d.setValue(1)
        f.addRow("最小峰间距（数据点）：", self.pk_d)
        v.addLayout(f)
        btn = QPushButton("寻峰并计算峰参数")
        btn.setDefault(True)
        btn.clicked.connect(self._run_peak)
        v.addWidget(btn)
        self.pk_txt = QTextEdit(); self.pk_txt.setReadOnly(True)
        v.addWidget(self.pk_txt, 1)
        if self.pk_x.count() >= 2:
            self.pk_x.setCurrentIndex(0); self.pk_y.setCurrentIndex(1)
        return w

    # -- 执行 --
    def _run_enzyme(self):
        try:
            S = self.sheet.numeric_data(self.enz_s.currentData())
            v = self.sheet.numeric_data(self.enz_v.currentData())
            vmax, km, r2, S, v, v_pred = enzyme_kinetics(S, v)
            lines = [
                "===== 酶动力学拟合（米氏方程）=====",
                f"Vmax = {vmax:.6g}",
                f"Km   = {km:.6g}",
                f"R²   = {r2:.6f}",
                "",
                f"催化效率 kcat/Km 相关参数可在已知酶浓度下计算。",
            ]
            self.enz_txt.setPlainText("\n".join(lines))
            if self.plot_callback:
                self.plot_callback(enzyme_kinetics_figure(S, v, vmax, km), "酶动力学分析")
        except Exception as e:
            QMessageBox.critical(self, "分析失败", str(e))

    def _run_std(self):
        try:
            c = self.sheet.numeric_data(self.std_c.currentData())
            a = self.sheet.numeric_data(self.std_a.currentData())
            k, b, r2, conc, abs_, pred = std_curve(c, a)
            unknown = self.std_unknown.value()
            cu = calc_unknown(k, b, unknown)
            lines = [
                "===== 标准曲线（朗伯-比尔定律）=====",
                f"回归方程：A = {k:.6g} × C + {b:.6g}",
                f"斜率 k = {k:.6g}",
                f"截距 b = {b:.6g}",
                f"决定系数 R² = {r2:.6f}",
                f"标准点数 = {len(conc)}",
                "",
                f"未知样品吸光度 A = {unknown:g}",
                f"反算浓度 C = (A - b) / k = {cu:.6g}",
            ]
            self.std_txt.setPlainText("\n".join(lines))
            if self.plot_callback:
                from matplotlib.figure import Figure
                fig = Figure(figsize=(6, 4.5), dpi=100)
                ax = fig.add_subplot(111)
                xs = np.linspace(min(conc) * 0.9, max(conc) * 1.1, 100)
                ax.plot(xs, k * xs + b, "-", color="#d64541", linewidth=2, label="线性拟合")
                ax.scatter(conc, abs_, s=52, color="#2e6da4", edgecolors="white",
                           linewidths=1, zorder=3, label="标准点")
                ax.scatter([cu], [unknown], s=90, color="#e08a1e", edgecolors="white",
                           linewidths=1.2, zorder=5, marker="*", label="未知样品")
                ax.set_xlabel("浓度 C")
                ax.set_ylabel("吸光度 A")
                ax.legend(frameon=False)
                fig.tight_layout()
                self.plot_callback(fig, "标准曲线")
        except Exception as e:
            QMessageBox.critical(self, "分析失败", str(e))

    def _run_ic50(self):
        try:
            c = self.sheet.numeric_data(self.ic_c.currentData())
            r = self.sheet.numeric_data(self.ic_r.currentData())
            ic50, popt, r2, conc, resp, pred = fit_ic50(c, r)
            lines = [
                "===== 剂量-响应拟合（四参数 Logistic）=====",
                f"IC50 / EC50 = {ic50:.6g}",
                f"下平台 (Bottom) = {popt[0]:.6g}",
                f"上平台 (Top)    = {popt[1]:.6g}",
                f"Hill 斜率       = {popt[2]:.6g}",
                f"R²              = {r2:.6f}",
            ]
            self.ic_txt.setPlainText("\n".join(lines))
            if self.plot_callback:
                self.plot_callback(ic50_figure(conc, resp, popt, ic50), "IC50 剂量-响应曲线")
        except Exception as e:
            QMessageBox.critical(self, "分析失败", str(e))

    def _run_peak(self):
        try:
            x = self.sheet.numeric_data(self.pk_x.currentData())
            y = self.sheet.numeric_data(self.pk_y.currentData())
            results, (x, y, peaks) = peak_analysis(x, y, self.pk_h.value(), self.pk_d.value())
            lines = ["===== 峰分析结果 =====", f"检测到 {len(results)} 个峰", ""]
            header = f"{'编号':<4} {'峰位置':>12} {'峰高':>14} {'半峰宽':>12} {'峰面积':>14}"
            lines.append(header)
            for r in results:
                lines.append(
                    f"{r['峰编号']:<4} {r['峰位置 (x)']:>12.4g} {r['峰高 (y)']:>14.4g} "
                    f"{r['半峰宽 FWHM']:>12.4g} {r['峰面积']:>14.4g}")
            self.pk_txt.setPlainText("\n".join(lines))
            if self.plot_callback:
                self.plot_callback(peak_figure(x, y, peaks), "峰分析")
        except Exception as e:
            QMessageBox.critical(self, "分析失败", str(e))
