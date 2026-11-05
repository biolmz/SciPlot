# -*- coding: utf-8 -*-
"""SciPlot —— 科学数据分析与绘图软件。"""

__version__ = "1.0.0"
__app_name__ = "SciPlot"
__app_title__ = "SciPlot 科学数据分析与绘图"

from . import styles, plotstyle, worksheet, plotting, statistics, fitting, bio

__all__ = [
    "styles", "plotstyle", "worksheet", "plotting",
    "statistics", "fitting", "bio",
]
