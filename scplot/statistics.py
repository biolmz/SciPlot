# -*- coding: utf-8 -*-
"""统计分析模块：描述性统计、假设检验、相关性、ANOVA。"""
from __future__ import annotations

import numpy as np
from scipy import stats

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QLabel, QDialogButtonBox, QMessageBox, QPlainTextEdit,
    QGroupBox, QRadioButton, QCheckBox, QSpinBox, QButtonGroup, QTextEdit,
    QAbstractItemView,
)

from .worksheet import WorkSheet


def describe(data: np.ndarray) -> dict:
    """描述性统计。"""
    data = data[np.isfinite(data)]
    n = len(data)
    if n == 0:
        return {"样本数": 0}
    return {
        "样本数 (N)": n,
        "均值 (Mean)": float(np.mean(data)),
        "标准差 (SD)": float(np.std(data, ddof=1)) if n > 1 else 0.0,
        "标准误 (SEM)": float(stats.sem(data)) if n > 1 else 0.0,
        "最小值": float(np.min(data)),
        "最大值": float(np.max(data)),
        "中位数": float(np.median(data)),
        "Q1 (25%)": float(np.percentile(data, 25)),
        "Q3 (75%)": float(np.percentile(data, 75)),
        "总和": float(np.sum(data)),
        "方差": float(np.var(data, ddof=1)) if n > 1 else 0.0,
        "偏度 (Skewness)": float(stats.skew(data)) if n > 2 else 0.0,
        "峰度 (Kurtosis)": float(stats.kurtosis(data)) if n > 3 else 0.0,
    }


def _fmt_p(p: float) -> str:
    if p < 0.0001:
        return "< 0.0001"
    return f"{p:.4f}"


def one_sample_ttest(data, mu0=0.0):
    """单样本 t 检验。"""
    data = data[np.isfinite(data)]
    t, p = stats.ttest_1samp(data, mu0)
    return {
        "样本数": len(data), "均值": float(np.mean(data)),
        "标准差": float(np.std(data, ddof=1)) if len(data) > 1 else 0.0,
        "t 值": float(t), "自由度 df": len(data) - 1,
        "p 值": float(p),
        "结论": "有显著性差异 (p<0.05)" if p < 0.05 else "无显著性差异 (p≥0.05)",
    }


def independent_ttest(d1, d2, equal_var=False):
    """独立样本 t 检验。"""
    d1 = d1[np.isfinite(d1)]; d2 = d2[np.isfinite(d2)]
    if len(d1) < 2 or len(d2) < 2:
        raise ValueError("每组至少需要 2 个数据点")
    t, p = stats.ttest_ind(d1, d2, equal_var=equal_var)
    return {
        "组1样本数": len(d1), "组2样本数": len(d2),
        "组1均值±SD": f"{np.mean(d1):.4f} ± {np.std(d1, ddof=1):.4f}",
        "组2均值±SD": f"{np.mean(d2):.4f} ± {np.std(d2, ddof=1):.4f}",
        "t 值": float(t), "自由度 df": len(d1) + len(d2) - 2,
        "p 值": float(p),
        "结论": "有显著性差异 (p<0.05)" if p < 0.05 else "无显著性差异 (p≥0.05)",
    }


def paired_ttest(d1, d2):
    """配对样本 t 检验。"""
    d1 = np.array(d1, dtype=float); d2 = np.array(d2, dtype=float)
    mask = np.isfinite(d1) & np.isfinite(d2)
    d1, d2 = d1[mask], d2[mask]
    if len(d1) < 3:
        raise ValueError("配对数据至少需要 3 对")
    t, p = stats.ttest_rel(d1, d2)
    diff = d1 - d2
    return {
        "配对样本数": len(d1),
        "差值均值": float(np.mean(diff)),
        "差值标准差": float(np.std(diff, ddof=1)),
        "t 值": float(t), "自由度 df": len(d1) - 1,
        "p 值": float(p),
        "结论": "有显著性差异 (p<0.05)" if p < 0.05 else "无显著性差异 (p≥0.05)",
    }


def oneway_anova(groups):
    """单因素方差分析 + Tukey 事后检验。"""
    groups = [g[np.isfinite(g)] for g in groups]
    groups = [g for g in groups if len(g) > 0]
    if len(groups) < 2:
        raise ValueError("至少需要 2 组数据")
    f, p = stats.f_oneway(*groups)
    result = {
        "组数": len(groups),
        "总样本数": sum(len(g) for g in groups),
        "F 值": float(f), "p 值": float(p),
        "结论": "组间存在显著差异 (p<0.05)" if p < 0.05 else "组间无显著差异 (p≥0.05)",
    }
    # 各组均值±SD
    for i, g in enumerate(groups, 1):
        result[f"组{i} 均值±SD"] = f"{np.mean(g):.4f} ± {np.std(g, ddof=1):.4f} (n={len(g)})"

    # Tukey HSD 事后检验
    posthoc = None
    if p < 0.05 and len(groups) >= 2:
        try:
            from statsmodels.stats.multicomp import pairwise_tukeyhsd
            all_data = np.concatenate(groups)
            labels = np.concatenate([np.full(len(g), f"组{i+1}") for i, g in enumerate(groups)])
            res = pairwise_tukeyhsd(all_data, labels, alpha=0.05)
            posthoc = str(res)
        except ImportError:
            posthoc = None
    return result, posthoc


def correlation(x, y, method="pearson"):
    """相关分析。"""
    x = np.array(x, dtype=float); y = np.array(y, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    if len(x) < 3:
        raise ValueError("至少需要 3 对数据")
    if method == "pearson":
        r, p = stats.pearsonr(x, y)
    elif method == "spearman":
        r, p = stats.spearmanr(x, y)
    else:
        r, p = stats.kendalltau(x, y)
    strength = ""
    ar = abs(r)
    if ar < 0.2: strength = "极弱"
    elif ar < 0.4: strength = "弱"
    elif ar < 0.6: strength = "中等"
    elif ar < 0.8: strength = "强"
    else: strength = "极强"
    return {
        "样本数": len(x),
        "相关系数 r": float(r),
        "p 值": float(p),
        "相关强度": strength,
        "方向": "正相关" if r > 0 else "负相关",
        "结论": "显著相关 (p<0.05)" if p < 0.05 else "不显著 (p≥0.05)",
    }


def normality_test(data):
    """Shapiro-Wilk 正态性检验。"""
    data = data[np.isfinite(data)]
    w, p = stats.shapiro(data)
    return {
        "样本数": len(data),
        "W 统计量": float(w), "p 值": float(p),
        "结论": "符合正态分布 (p≥0.05)" if p >= 0.05 else "偏离正态分布 (p<0.05)",
    }


# ---------------------------------------------------------------------------
# 统计对话框
# ---------------------------------------------------------------------------
class StatisticsDialog(QDialog):
    """统计分析工作台。"""

    def __init__(self, sheet: WorkSheet, parent=None):
        super().__init__(parent)
        self.sheet = sheet
        self.setWindowTitle("统计分析")
        self.setMinimumSize(760, 540)
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        # 左侧：方法选择
        left = QVBoxLayout()
        left.addWidget(QLabel("分析方法"))
        self.cmb_method = QComboBox()
        self.cmb_method.addItem("描述性统计", "describe")
        self.cmb_method.addItem("单样本 t 检验", "ttest1")
        self.cmb_method.addItem("独立样本 t 检验", "ttest_ind")
        self.cmb_method.addItem("配对样本 t 检验", "ttest_pair")
        self.cmb_method.addItem("单因素方差分析 (ANOVA)", "anova")
        self.cmb_method.addItem("相关分析", "corr")
        self.cmb_method.addItem("正态性检验", "norm")
        self.cmb_method.currentIndexChanged.connect(self._on_method_changed)
        left.addWidget(self.cmb_method)

        left.addWidget(QLabel("选择数据列（多选）"))
        self.lst_cols = QListWidget()
        self.lst_cols.setSelectionMode(QListWidget.ExtendedSelection)
        left.addWidget(self.lst_cols, 1)

        self.cmb_corr = QComboBox()
        self.cmb_corr.addItem("Pearson 线性相关", "pearson")
        self.cmb_corr.addItem("Spearman 秩相关", "spearman")
        self.cmb_corr.addItem("Kendall 秩相关", "kendall")
        self.cmb_corr.setVisible(False)
        left.addWidget(self.cmb_corr)

        btn_run = QPushButton("开始分析")
        btn_run.setDefault(True)
        btn_run.clicked.connect(self._run)
        left.addWidget(btn_run)
        root.addLayout(left, 0)

        # 右侧：结果
        right = QVBoxLayout()
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        self.txt_result.setPlaceholderText("分析结果将在此显示，可直接复制。")
        right.addWidget(self.txt_result, 1)
        btn_copy = QPushButton("复制结果")
        btn_copy.clicked.connect(self._copy)
        right.addWidget(btn_copy)
        root.addLayout(right, 1)

        self._refresh_cols()

    def _refresh_cols(self):
        self.lst_cols.clear()
        for i, c in enumerate(self.sheet.columns):
            if c["ctype"] in ("L", "I"):
                continue
            item = QListWidgetItem(f"{c['name']}  [{c['ctype']}]")
            item.setData(Qt.UserRole, i)
            self.lst_cols.addItem(item)

    def _on_method_changed(self):
        m = self.cmb_method.currentData()
        self.cmb_corr.setVisible(m == "corr")
        if m == "corr":
            self.lst_cols.setSelectionMode(QListWidget.ExtendedSelection)
        elif m in ("ttest_ind", "ttest_pair"):
            self.lst_cols.setSelectionMode(QListWidget.ExtendedSelection)
        elif m == "anova":
            self.lst_cols.setSelectionMode(QListWidget.ExtendedSelection)
        else:
            self.lst_cols.setSelectionMode(QListWidget.ExtendedSelection)

    def _selected_idx(self):
        return [self.lst_cols.item(i).data(Qt.UserRole)
                for i in range(self.lst_cols.count())
                if self.lst_cols.item(i).isSelected()]

    def _run(self):
        method = self.cmb_method.currentData()
        idxs = self._selected_idx()
        try:
            if method == "describe":
                if not idxs:
                    raise ValueError("请选择至少一列")
                lines = []
                for idx in idxs:
                    name = self.sheet.columns[idx]["name"]
                    d = self.sheet.numeric_data(idx)
                    lines.append(f"===== 列 {name} 描述性统计 =====")
                    for k, v in describe(d).items():
                        if isinstance(v, float):
                            lines.append(f"  {k:<16} {v:.6g}")
                        else:
                            lines.append(f"  {k:<16} {v}")
                    lines.append("")
                self._show("\n".join(lines))

            elif method == "ttest1":
                if len(idxs) != 1:
                    raise ValueError("单样本 t 检验请选择 1 列")
                d = self.sheet.numeric_data(idxs[0])
                r = one_sample_ttest(d)
                self._show_dict("单样本 t 检验", r)

            elif method == "ttest_ind":
                if len(idxs) != 2:
                    raise ValueError("独立样本 t 检验请选择 2 列")
                d1 = self.sheet.numeric_data(idxs[0])
                d2 = self.sheet.numeric_data(idxs[1])
                r = independent_ttest(d1, d2)
                self._show_dict("独立样本 t 检验", r)

            elif method == "ttest_pair":
                if len(idxs) != 2:
                    raise ValueError("配对样本 t 检验请选择 2 列")
                d1 = self.sheet.numeric_data(idxs[0])
                d2 = self.sheet.numeric_data(idxs[1])
                r = paired_ttest(d1, d2)
                self._show_dict("配对样本 t 检验", r)

            elif method == "anova":
                if len(idxs) < 2:
                    raise ValueError("方差分析请选择至少 2 列（每组数据一列）")
                groups = [self.sheet.numeric_data(i) for i in idxs]
                r, posthoc = oneway_anova(groups)
                lines = self._dict_lines("单因素方差分析", r)
                if posthoc:
                    lines.append("\n===== Tukey HSD 事后检验 =====")
                    lines.append(posthoc)
                self._show("\n".join(lines))

            elif method == "corr":
                if len(idxs) != 2:
                    raise ValueError("相关分析请选择 2 列")
                x = self.sheet.numeric_data(idxs[0])
                y = self.sheet.numeric_data(idxs[1])
                r = correlation(x, y, self.cmb_corr.currentData())
                self._show_dict(
                    f"相关分析（{self.cmb_corr.currentText()}）", r)

            elif method == "norm":
                if not idxs:
                    raise ValueError("请选择至少一列")
                lines = []
                for idx in idxs:
                    name = self.sheet.columns[idx]["name"]
                    lines.append(f"===== 列 {name} Shapiro-Wilk 正态性检验 =====")
                    lines.extend(self._dict_lines("", normality_test(self.sheet.numeric_data(idx))))
                    lines.append("")
                self._show("\n".join(lines))

        except Exception as e:
            QMessageBox.warning(self, "分析失败", str(e))

    def _dict_lines(self, title, d):
        lines = []
        if title:
            lines.append(f"===== {title} =====")
        for k, v in d.items():
            if isinstance(v, float):
                if "p" in k.lower() or "P 值" in k:
                    lines.append(f"  {k:<14} {_fmt_p(v)}")
                else:
                    lines.append(f"  {k:<14} {v:.6g}")
            else:
                lines.append(f"  {k:<14} {v}")
        return lines

    def _show_dict(self, title, d):
        self._show("\n".join(self._dict_lines(title, d)))

    def _show(self, text):
        self.txt_result.setPlainText(text)

    def _copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.txt_result.toPlainText())
        QMessageBox.information(self, "已复制", "结果已复制到剪贴板。")
