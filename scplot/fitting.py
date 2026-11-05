# -*- coding: utf-8 -*-
"""曲线拟合模块：线性/多项式/非线性拟合 + 酶动力学米氏方程。"""
from __future__ import annotations

import numpy as np
from scipy.optimize import curve_fit

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QWidget, QTableWidget, QTableWidgetItem,
    QLabel, QDialogButtonBox, QMessageBox, QTextEdit, QCheckBox, QDoubleSpinBox,
    QSpinBox, QGroupBox, QHeaderView, QAbstractItemView,
)


# ---------------------------------------------------------------------------
# 拟合模型定义
# ---------------------------------------------------------------------------
class FitModel:
    def __init__(self, key, name, func, p0_func, pnames, equation):
        self.key = key
        self.name = name
        self.func = func          # f(x, *params)
        self.p0_func = p0_func    # (x, y) -> 初始参数 list
        self.pnames = pnames
        self.equation = equation


def _lin(x, a, b): return a + b * x
def _poly2(x, a, b, c): return a + b * x + c * x * x
def _poly3(x, a, b, c, d): return a + b * x + c * x * x + d * x ** 3
def _exp(x, a, b): return a * np.exp(b * x)
def _exp_decay(x, a, b, c): return a * np.exp(-b * x) + c
def _log(x, a, b): return a + b * np.log(x)
def _power(x, a, b): return a * np.power(x, b)
def _gauss(x, a, b, c, d): return a * np.exp(-((x - b) ** 2) / (2 * c * c)) + d
def _lorentz(x, a, b, c, d): return a / (1 + ((x - b) / c) ** 2) + d
def _sigmoid(x, a, b, c, d): return d + (a - d) / (1 + (x / c) ** b)
def _michaelis(x, vmax, km): return vmax * x / (km + x)


def _p0_lin(x, y): return [np.mean(y) - np.polyfit(x, y, 1)[0] * np.mean(x), np.polyfit(x, y, 1)[0]]
def _p0_poly2(x, y):
    c = np.polyfit(x, y, 2); return list(c[::-1])
def _p0_poly3(x, y):
    c = np.polyfit(x, y, 3); return list(c[::-1])
def _p0_exp(x, y):
    b = (np.log(max(y[-1], 1e-9)) - np.log(max(y[0], 1e-9))) / (x[-1] - x[0]) if x[-1] != x[0] else 0.1
    return [max(y[0], 1e-9), b]
def _p0_exp_decay(x, y):
    return [max(y[0], 1e-9) - min(y), 1.0 / max(x[-1] - x[0], 1e-6), min(y)]
def _p0_log(x, y):
    xs = np.log(np.clip(x, 1e-9, None))
    b = np.polyfit(xs, y, 1)[0]; a = np.mean(y) - b * np.mean(xs)
    return [a, b]
def _p0_power(x, y):
    xs = np.log(np.clip(x, 1e-9, None)); ys = np.log(np.clip(y, 1e-9, None))
    b = np.polyfit(xs, ys, 1)[0]; a = np.exp(np.mean(ys) - b * np.mean(xs))
    return [a, b]
def _p0_gauss(x, y):
    d = min(y); a = max(y) - d; b = x[np.argmax(y)]; c = (max(x) - min(x)) / 6 or 1
    return [a, b, c, d]
def _p0_lorentz(x, y):
    d = min(y); a = max(y) - d; b = x[np.argmax(y)]; c = (max(x) - min(x)) / 6 or 1
    return [a, b, c, d]
def _p0_sigmoid(x, y):
    d = min(y); a = max(y); c = np.median(x); b = 1.0
    return [a, b, c, d]
def _p0_michaelis(x, y):
    vmax = max(y) * 1.05; km = np.median(x)
    return [vmax, km]


FIT_MODELS = [
    FitModel("linear", "线性  y = a + bx", _lin, _p0_lin, ["a", "b"], "y = a + b·x"),
    FitModel("poly2", "二次多项式  y = a + bx + cx²", _poly2, _p0_poly2, ["a", "b", "c"], "y = a + b·x + c·x²"),
    FitModel("poly3", "三次多项式", _poly3, _p0_poly3, ["a", "b", "c", "d"], "y = a + b·x + c·x² + d·x³"),
    FitModel("exp", "指数增长  y = a·e^(bx)", _exp, _p0_exp, ["a", "b"], "y = a·e^(b·x)"),
    FitModel("expdecay", "指数衰减  y = a·e^(-bx) + c", _exp_decay, _p0_exp_decay, ["a", "b", "c"], "y = a·e^(-b·x) + c"),
    FitModel("log", "对数  y = a + b·ln(x)", _log, _p0_log, ["a", "b"], "y = a + b·ln(x)"),
    FitModel("power", "幂函数  y = a·x^b", _power, _p0_power, ["a", "b"], "y = a·x^b"),
    FitModel("gauss", "高斯峰  y = a·e^(-(x-b)²/2c²) + d", _gauss, _p0_gauss, ["a(峰高)", "b(峰位)", "c(峰宽)", "d(基线)"], "y = a·exp(-(x-b)²/(2c²)) + d"),
    FitModel("lorentz", "洛伦兹峰", _lorentz, _p0_lorentz, ["a(峰高)", "b(峰位)", "c(半宽)", "d(基线)"], "y = a/(1+((x-b)/c)²) + d"),
    FitModel("sigmoid", "S 型曲线 (四参数)", _sigmoid, _p0_sigmoid, ["a(上限)", "b(斜率)", "c(EC50)", "d(下限)"], "y = d + (a-d)/(1+(x/c)^b)"),
    FitModel("michaelis", "米氏方程  v = Vmax·[S]/(Km+[S])", _michaelis, _p0_michaelis, ["Vmax", "Km"], "v = Vmax·[S] / (Km + [S])"),
]


MODEL_BY_KEY = {m.key: m for m in FIT_MODELS}


def fit_curve(x, y, model_key):
    """执行拟合，返回 (参数数组, 协方差, 模型, 预测函数)。"""
    model = MODEL_BY_KEY[model_key]
    p0 = model.p0_func(x, y)
    try:
        popt, pcov = curve_fit(model.func, x, y, p0=p0, maxfev=20000)
    except RuntimeError:
        popt, pcov = curve_fit(model.func, x, y, p0=p0, maxfev=200000)
    return popt, pcov, model


def goodness_of_fit(y_obs, y_pred, n_params):
    """计算 R²、校正 R²、RMSE。"""
    ss_res = np.sum((y_obs - y_pred) ** 2)
    ss_tot = np.sum((y_obs - np.mean(y_obs)) ** 2)
    n = len(y_obs)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - n_params - 1) if n > n_params + 1 else float("nan")
    rmse = np.sqrt(ss_res / n)
    return r2, adj_r2, rmse


def predict(model, popt, x):
    return model.func(np.asarray(x, dtype=float), *popt)


# ---------------------------------------------------------------------------
# 拟合对话框
# ---------------------------------------------------------------------------
class FitDialog(QDialog):
    """曲线拟合对话框。"""

    def __init__(self, sheet, parent=None, plot_callback=None):
        super().__init__(parent)
        self.sheet = sheet
        self.plot_callback = plot_callback
        self.result = None
        self.setWindowTitle("曲线拟合")
        self.setMinimumSize(700, 560)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        form = QFormLayout()
        self.cmb_x = QComboBox()
        self.cmb_y = QComboBox()
        form.addRow("X 数据列：", self.cmb_x)
        form.addRow("Y 数据列：", self.cmb_y)
        top.addLayout(form)

        model_box = QGroupBox("拟合模型")
        vb = QVBoxLayout(model_box)
        self.cmb_model = QComboBox()
        for m in FIT_MODELS:
            self.cmb_model.addItem(m.name, m.key)
        vb.addWidget(self.cmb_model)
        self.lbl_eq = QLabel("")
        self.lbl_eq.setWordWrap(True)
        vb.addWidget(self.lbl_eq)
        self.cmb_model.currentIndexChanged.connect(self._update_eq)
        top.addWidget(model_box, 1)
        root.addLayout(top)

        btn_row = QHBoxLayout()
        btn_fit = QPushButton("开始拟合")
        btn_fit.setDefault(True)
        btn_fit.clicked.connect(self._run)
        self.chk_plot = QCheckBox("拟合后绘制拟合曲线"); self.chk_plot.setChecked(True)
        btn_row.addWidget(btn_fit)
        btn_row.addWidget(self.chk_plot)
        btn_row.addStretch(1)
        root.addLayout(btn_row)

        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        root.addWidget(self.txt, 1)

        btn_copy = QPushButton("复制结果")
        btn_copy.clicked.connect(self._copy)
        root.addWidget(btn_copy)

        self._refresh()
        self._update_eq()

    def _refresh(self):
        self.cmb_x.clear(); self.cmb_y.clear()
        for i, c in enumerate(self.sheet.columns):
            if c["ctype"] in ("L", "I"):
                continue
            disp = f"{c['name']}  [{c['ctype']}]"
            self.cmb_x.addItem(disp, i)
            self.cmb_y.addItem(disp, i)
        if self.cmb_x.count() >= 2:
            self.cmb_x.setCurrentIndex(0)
            self.cmb_y.setCurrentIndex(1)

    def _update_eq(self):
        m = MODEL_BY_KEY[self.cmb_model.currentData()]
        self.lbl_eq.setText(m.equation)

    def _run(self):
        x_idx = self.cmb_x.currentData()
        y_idx = self.cmb_y.currentData()
        model_key = self.cmb_model.currentData()
        if x_idx is None or y_idx is None:
            QMessageBox.warning(self, "提示", "请选择数据列。")
            return
        x, y = self.sheet.numeric_pairs(x_idx, y_idx)
        if len(x) < 3:
            QMessageBox.warning(self, "提示", "有效数据点不足，至少需要 3 个。")
            return
        try:
            popt, pcov, model = fit_curve(x, y, model_key)
            y_pred = predict(model, popt, x)
            r2, adj_r2, rmse = goodness_of_fit(y, y_pred, len(popt))
        except Exception as e:
            QMessageBox.critical(self, "拟合失败", f"无法收敛：{e}\n可尝试更换模型或检查数据。")
            return

        self.result = (x, y, popt, model, y_pred, r2, adj_r2, rmse, x_idx, y_idx)

        # 输出结果
        lines = []
        lines.append(f"===== 拟合结果：{model.name} =====")
        lines.append(f"拟合方程：{model.equation}")
        lines.append("")
        lines.append("参数估计：")
        perr = np.sqrt(np.diag(pcov)) if pcov is not None else np.full(len(popt), np.nan)
        for name, v, e in zip(model.pnames, popt, perr):
            if np.isfinite(e):
                lines.append(f"  {name:<12} = {v:.6g}  ±  {e:.6g}")
            else:
                lines.append(f"  {name:<12} = {v:.6g}")
        lines.append("")
        lines.append(f"决定系数 R²     = {r2:.6f}")
        lines.append(f"校正 R² (adj)   = {adj_r2:.6f}")
        lines.append(f"均方根误差 RMSE = {rmse:.6g}")
        lines.append(f"拟合数据点数    = {len(x)}")
        self.txt.setPlainText("\n".join(lines))

        # 绘制拟合图
        if self.chk_plot.isChecked() and self.plot_callback:
            self.plot_callback(self.result)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.txt.toPlainText())
        QMessageBox.information(self, "已复制", "拟合结果已复制到剪贴板。")
