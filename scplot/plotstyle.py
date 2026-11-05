# -*- coding: utf-8 -*-
"""专业科学绘图样式引擎：matplotlib 中文字体、配色、坐标系样式。

负责让所有图表呈现 Origin / SigmaPlot 级别的专业观感：
- 中文字体自动探测（微软雅黑 / 黑体 / 宋体 / Noto Sans CJK）
- 科学配色序列（避免 AI 味的高饱和渐变，采用克制、可打印的学术色）
- 统一刻度、边框、字号、网格样式
"""
from __future__ import annotations

import matplotlib
matplotlib.use("QtAgg")

from matplotlib import rcParams, font_manager
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# 中文字体探测
# ---------------------------------------------------------------------------
_CJK_CANDIDATES = [
    "Microsoft YaHei", "微软雅黑", "Microsoft YaHei UI",
    "SimHei", "黑体",
    "PingFang SC", "Hiragino Sans GB",
    "Noto Sans CJK SC", "Source Han Sans SC",
    "SimSun", "宋体",
]

_SERIF_CANDIDATES = [
    "SimSun", "宋体", "NSimSun", "Microsoft YaHei", "微软雅黑",
]

def _available_fonts() -> set:
    try:
        names = {f.name for f in font_manager.fontManager.ttflist}
    except Exception:
        names = set()
    return names


def detect_cjk_font() -> str:
    """返回可用的中文字体名，找不到则回退 DejaVu Sans。"""
    avail = _available_fonts()
    for name in _CJK_CANDIDATES:
        if name in avail:
            return name
    return "DejaVu Sans"


def detect_serif_font() -> str:
    avail = _available_fonts()
    for name in _SERIF_CANDIDATES:
        if name in avail:
            return name
    return detect_cjk_font()


CJK_FONT = detect_cjk_font()
SERIF_FONT = detect_serif_font()


# ---------------------------------------------------------------------------
# 学术配色序列（克制、可打印、色盲友好）
# ---------------------------------------------------------------------------
# 主序列：以黑、红、蓝、绿、橙为主体，避免霓虹色
COLOR_SERIES = {
    "default": ["#1f2a44", "#d64541", "#2e6da4", "#3a7d44", "#e08a1e",
                "#7b4b94", "#1f8a8a", "#8a6d3b", "#555555", "#c0397a"],
    "colorblind": ["#1f2a44", "#e69f00", "#56b4e9", "#009e73", "#f0e442",
                   "#0072b2", "#d55e00", "#cc79a7", "#999999", "#000000"],
    "grayscale": ["#111111", "#444444", "#777777", "#aaaaaa", "#222222",
                  "#555555", "#888888", "#bbbbbb", "#333333", "#666666"],
}

# 涨红跌绿（中国市场惯例）
UP_COLOR = "#d64541"
DOWN_COLOR = "#3a7d44"


def get_colors(series: str = "default") -> list:
    return list(COLOR_SERIES.get(series, COLOR_SERIES["default"]))


# ---------------------------------------------------------------------------
# 全局 rcParams 初始化
# ---------------------------------------------------------------------------
def apply_global_style():
    """应用全局 matplotlib 样式。"""
    rcParams["font.sans-serif"] = [CJK_FONT, "DejaVu Sans"]
    rcParams["font.family"] = "sans-serif"
    rcParams["axes.unicode_minus"] = False

    # 字号体系（适合学术期刊与屏幕）
    rcParams["font.size"] = 11
    rcParams["axes.titlesize"] = 13
    rcParams["axes.labelsize"] = 12
    rcParams["xtick.labelsize"] = 10.5
    rcParams["ytick.labelsize"] = 10.5
    rcParams["legend.fontsize"] = 10
    rcParams["figure.titlesize"] = 14

    # 刻度方向：朝内（专业风格）
    rcParams["xtick.direction"] = "in"
    rcParams["ytick.direction"] = "in"
    rcParams["xtick.top"] = True
    rcParams["ytick.right"] = True
    rcParams["xtick.minor.visible"] = True
    rcParams["ytick.minor.visible"] = True

    # 轴脊线
    rcParams["axes.linewidth"] = 1.0
    rcParams["axes.spines.top"] = False
    rcParams["axes.spines.right"] = False

    # 网格：仅横向浅灰虚线
    rcParams["axes.grid"] = False
    rcParams["grid.color"] = "#c9c9c9"
    rcParams["grid.linestyle"] = "--"
    rcParams["grid.linewidth"] = 0.6
    rcParams["grid.alpha"] = 0.7

    rcParams["figure.dpi"] = 100
    rcParams["savefig.dpi"] = 300
    rcParams["savefig.bbox"] = "tight"
    rcParams["legend.frameon"] = False
    rcParams["errorbar.capsize"] = 3

    # 颜色循环
    rcParams["axes.prop_cycle"] = matplotlib.cycler(
        color=get_colors("default"))


apply_global_style()
