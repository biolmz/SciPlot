# -*- coding: utf-8 -*-
"""专业桌面软件外观（QSS 主题系统）。

设计目标：像 Origin / OriginPro / SigmaPlot 一样的专业学术软件观感，
去 AI 味——无夸张圆角、无霓虹渐变、无 emoji，克制的强调色与紧凑排版。
默认浅色学术主题，内置深色主题可切换。
"""
from __future__ import annotations


# 强调色（专业仪器蓝，类似 Origin 的蓝灰）
ACCENT = "#2b6cb0"
ACCENT_DARK = "#1f4e7a"
ACCENT_LIGHT = "#e3edf7"

# 浅色主题调色板
LIGHT = {
    "window": "#f2f3f5",
    "panel": "#ffffff",
    "panel_alt": "#fafbfc",
    "border": "#d5d9de",
    "border_dark": "#c2c7cd",
    "text": "#1c2733",
    "text_dim": "#5b6672",
    "text_faint": "#8a939c",
    "accent": ACCENT,
    "accent_dark": ACCENT_DARK,
    "accent_light": ACCENT_LIGHT,
    "hover": "#e8f0f8",
    "selected": "#d6e6f5",
    "toolbar": "#eceef1",
    "menu": "#ffffff",
    "titlebar": "#ffffff",
    "status": "#e9ecf0",
    "table_header": "#eef1f4",
    "table_grid": "#e2e5e9",
    "table_sel": "#d6e6f5",
    "input": "#ffffff",
}

# 深色主题调色板
DARK = {
    "window": "#1e2228",
    "panel": "#262b32",
    "panel_alt": "#2a3038",
    "border": "#3a424c",
    "border_dark": "#4a525d",
    "text": "#e2e6ea",
    "text_dim": "#a5adb8",
    "text_faint": "#79828c",
    "accent": "#4d8fd1",
    "accent_dark": "#6ea8de",
    "accent_light": "#2e3d4f",
    "hover": "#323a44",
    "selected": "#33465c",
    "toolbar": "#22272e",
    "menu": "#262b32",
    "titlebar": "#262b32",
    "status": "#22272e",
    "table_header": "#2d333b",
    "table_grid": "#3a424c",
    "table_sel": "#33465c",
    "input": "#20252b",
}


def build_qss(pal: dict) -> str:
    """根据调色板生成完整 QSS。"""
    c = pal
    return f"""
* {{
    font-family: "Microsoft YaHei", "微软雅黑", "Segoe UI", sans-serif;
    font-size: 12.5px;
    color: {c['text']};
}}
QMainWindow, QDialog {{
    background: {c['window']};
}}
QWidget {{
    background: transparent;
}}

/* ---------- 菜单栏 ---------- */
QMenuBar {{
    background: {c['titlebar']};
    border-bottom: 1px solid {c['border']};
    padding: 1px 2px;
}}
QMenuBar::item {{
    background: transparent;
    padding: 5px 10px;
    border-radius: 3px;
}}
QMenuBar::item:selected {{
    background: {c['hover']};
}}
QMenuBar::item:pressed {{
    background: {c['selected']};
}}
QMenu {{
    background: {c['menu']};
    border: 1px solid {c['border_dark']};
    padding: 4px;
}}
QMenu::item {{
    padding: 6px 26px 6px 12px;
    border-radius: 3px;
}}
QMenu::item:selected {{
    background: {c['accent']};
    color: #ffffff;
}}
QMenu::separator {{
    height: 1px;
    background: {c['border']};
    margin: 4px 8px;
}}
QMenu::right-arrow {{
    width: 8px; height: 8px;
}}

/* ---------- 工具栏 ---------- */
QToolBar {{
    background: {c['toolbar']};
    border: none;
    border-bottom: 1px solid {c['border']};
    padding: 3px 4px;
    spacing: 3px;
}}
QToolBar::separator {{
    width: 1px;
    background: {c['border']};
    margin: 4px 6px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 3px;
    padding: 4px 8px;
}}
QToolButton:hover {{
    background: {c['hover']};
    border-color: {c['border']};
}}
QToolButton:pressed {{
    background: {c['selected']};
}}
QToolButton:checked {{
    background: {c['selected']};
    border-color: {c['accent']};
}}

/* ---------- 停靠面板 ---------- */
QDockWidget {{
    titlebar-close-icon: none;
    titlebar-normal-icon: none;
    font-size: 12px;
}}
QDockWidget::title {{
    background: {c['panel_alt']};
    border: 1px solid {c['border']};
    border-bottom: none;
    padding: 6px 8px;
    text-align: left;
    font-weight: 600;
}}

/* ---------- 标签页 ---------- */
QTabWidget::pane {{
    border: 1px solid {c['border']};
    background: {c['panel']};
    top: -1px;
}}
QTabBar::tab {{
    background: {c['panel_alt']};
    border: 1px solid {c['border']};
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background: {c['panel']};
    border-bottom: 2px solid {c['accent']};
    color: {c['accent']};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    background: {c['hover']};
}}

/* ---------- 表格 ---------- */
QTableWidget, QTableView {{
    background: {c['panel']};
    alternate-background-color: {c['panel_alt']};
    gridline-color: {c['table_grid']};
    border: none;
    selection-background-color: {c['table_sel']};
    selection-color: {c['text']};
}}
QHeaderView::section {{
    background: {c['table_header']};
    color: {c['text']};
    border: none;
    border-right: 1px solid {c['table_grid']};
    border-bottom: 1px solid {c['table_grid']};
    padding: 5px 6px;
    font-weight: 600;
}}
QTableCornerButton::section {{
    background: {c['table_header']};
    border: none;
    border-bottom: 1px solid {c['table_grid']};
}}

/* ---------- 输入控件 ---------- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
    background: {c['input']};
    border: 1px solid {c['border_dark']};
    border-radius: 3px;
    padding: 4px 6px;
    selection-background-color: {c['selected']};
    selection-color: {c['text']};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus {{
    border-color: {c['accent']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background: {c['menu']};
    border: 1px solid {c['border_dark']};
    selection-background-color: {c['accent']};
    selection-color: #ffffff;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    background: {c['panel_alt']};
    border: none;
    width: 16px;
}}

/* ---------- 按钮 ---------- */
QPushButton {{
    background: {c['panel']};
    border: 1px solid {c['border_dark']};
    border-radius: 3px;
    padding: 5px 16px;
}}
QPushButton:hover {{
    background: {c['hover']};
    border-color: {c['accent']};
}}
QPushButton:pressed {{
    background: {c['selected']};
}}
QPushButton:default {{
    background: {c['accent']};
    border-color: {c['accent']};
    color: #ffffff;
    font-weight: 600;
}}
QPushButton:default:hover {{
    background: {c['accent_dark']};
}}
QPushButton:disabled {{
    color: {c['text_faint']};
    background: {c['panel_alt']};
}}

/* ---------- 滚动条 ---------- */
QScrollBar:vertical {{
    background: {c['panel_alt']};
    width: 12px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['border_dark']};
    border-radius: 5px;
    min-height: 24px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_faint']};
}}
QScrollBar:horizontal {{
    background: {c['panel_alt']};
    height: 12px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_dark']};
    border-radius: 5px;
    min-width: 24px;
    margin: 2px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0; width: 0;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}

/* ---------- 状态栏 ---------- */
QStatusBar {{
    background: {c['status']};
    border-top: 1px solid {c['border']};
    color: {c['text_dim']};
}}
QStatusBar::item {{
    border: none;
}}

/* ---------- 拆分器 ---------- */
QSplitter::handle {{
    background: {c['border']};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ---------- 其他 ---------- */
QGroupBox {{
    border: 1px solid {c['border']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {c['text_dim']};
}}
QCheckBox, QRadioButton {{
    spacing: 6px;
}}
QToolTip {{
    background: {c['text']};
    color: {c['panel']};
    border: none;
    padding: 5px 8px;
}}
QProgressBar {{
    border: 1px solid {c['border_dark']};
    border-radius: 3px;
    text-align: center;
    background: {c['panel_alt']};
}}
QProgressBar::chunk {{
    background: {c['accent']};
    border-radius: 2px;
}}
QListWidget, QTreeWidget {{
    background: {c['panel']};
    border: 1px solid {c['border']};
    alternate-background-color: {c['panel_alt']};
}}
QListWidget::item:selected, QTreeWidget::item:selected {{
    background: {c['selected']};
    color: {c['text']};
}}
QScrollArea {{ border: none; }}
QSplitter {{ background: {c['window']}; }}
"""


def get_qss(dark: bool = False) -> str:
    return build_qss(DARK if dark else LIGHT)


def get_palette(dark: bool = False) -> dict:
    return dict(DARK if dark else LIGHT)
