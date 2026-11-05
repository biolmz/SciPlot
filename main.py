# -*- coding: utf-8 -*-
"""SciPlot 程序入口。"""
import sys
import os

# 兼容打包后的资源路径
if getattr(sys, "frozen", False):
    os.environ.setdefault("QT_PLUGIN_PATH", os.path.join(sys._MEIPASS, "qtplugins"))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from scplot import styles, plotstyle
from scplot.main_window import MainWindow


def main():
    # 高分屏适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("SciPlot")
    app.setOrganizationName("SciPlot")
    app.setApplicationDisplayName("SciPlot 科学数据分析与绘图")

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
