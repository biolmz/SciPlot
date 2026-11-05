# -*- coding: utf-8 -*-
"""数据工作表模块：仿 Origin 的 workbook。

- 多列数据模型，列类型（X / Y / Z / 误差 / 标签 / 忽略）
- CSV / TXT / Excel 导入，自动推断列类型
- 单元格编辑、行列增删、排序、统计、填充
- 导出 CSV / Excel
"""
from __future__ import annotations

import csv
import os
import re

from PySide6.QtCore import Qt, Signal, QModelIndex
from PySide6.QtGui import QColor, QFont, QAction, QCursor, QKeySequence
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QAbstractItemView, QMenu, QHeaderView,
    QMessageBox, QInputDialog, QFileDialog, QWidget, QVBoxLayout, QLabel,
)

import numpy as np


# ---------------------------------------------------------------------------
# 列类型定义（仿 Origin 约定）
# ---------------------------------------------------------------------------
CTYPE_X = "X"          # 自变量
CTYPE_Y = "Y"          # 因变量
CTYPE_Z = "Z"          # 三维
CTYPE_LABEL = "L"      # 标签列
CTYPE_YERR = "YErr"    # Y 误差
CTYPE_XERR = "XErr"    # X 误差
CTYPE_IGNORE = "I"     # 忽略

CTYPE_NAMES = {
    CTYPE_X: "X 自变量",
    CTYPE_Y: "Y 因变量",
    CTYPE_Z: "Z 数据",
    CTYPE_LABEL: "标签列",
    CTYPE_YERR: "Y 误差",
    CTYPE_XERR: "X 误差",
    CTYPE_IGNORE: "忽略列",
}

CTYPE_ORDER = [CTYPE_X, CTYPE_Y, CTYPE_Z, CTYPE_LABEL, CTYPE_YERR, CTYPE_XERR, CTYPE_IGNORE]


def _try_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def parse_numeric(s):
    """把字符串转 float，失败返回 None。"""
    if s is None:
        return None
    s = str(s).strip()
    if s == "" or s.lower() in ("nan", "none", "na", "null", "—", "-"):
        return None
    # 处理千分位逗号
    s2 = s.replace(",", "")
    try:
        return float(s2)
    except ValueError:
        return None


def column_letter(i: int) -> str:
    """0 -> 'A', 25 -> 'Z', 26 -> 'AA'"""
    out = ""
    i += 1
    while i > 0:
        i, r = divmod(i - 1, 26)
        out = chr(65 + r) + out
    return out


class WorkSheet:
    """一张数据工作表：若干列数据。"""

    def __init__(self, name: str = "工作表1"):
        self.name = name
        self.columns: list[dict] = []   # 每列: {name, ctype, values:list}
        self._init_default()

    def _init_default(self):
        self.columns = [
            {"name": "A", "ctype": CTYPE_X, "values": []},
            {"name": "B", "ctype": CTYPE_Y, "values": []},
        ]

    # -- 基本操作 --
    def add_column(self, name=None, ctype=CTYPE_Y, before=None):
        if name is None:
            name = column_letter(len(self.columns))
        col = {"name": name, "ctype": ctype, "values": []}
        if before is None:
            self.columns.append(col)
        else:
            self.columns.insert(before, col)
        return col

    def remove_column(self, idx):
        if len(self.columns) <= 1:
            return False
        del self.columns[idx]
        return True

    def ncols(self):
        return len(self.columns)

    def nrows(self):
        return max((len(c["values"]) for c in self.columns), default=0)

    def col_names(self):
        return [f"{c['name']}({c['ctype']})" for c in self.columns]

    def numeric_data(self, idx, include_label=False):
        """取第 idx 列的数值（忽略缺失），返回 numpy 数组。"""
        vals = []
        for v in self.columns[idx]["values"]:
            f = parse_numeric(v) if not isinstance(v, (int, float)) else float(v)
            if f is not None:
                vals.append(f)
        return np.array(vals, dtype=float)

    def numeric_pairs(self, x_idx, y_idx):
        """提取成对的 (x, y) 数值（剔除任一缺失的行）。"""
        xs, ys = [], []
        xcol = self.columns[x_idx]["values"]
        ycol = self.columns[y_idx]["values"]
        n = max(len(xcol), len(ycol))
        for i in range(n):
            xv = parse_numeric(xcol[i]) if i < len(xcol) else None
            yv = parse_numeric(ycol[i]) if i < len(ycol) else None
            if xv is not None and yv is not None:
                xs.append(xv)
                ys.append(yv)
        return np.array(xs), np.array(ys)

    # -- 导入 --
    @classmethod
    def from_file(cls, path: str):
        ext = os.path.splitext(path)[1].lower()
        if ext in (".xlsx", ".xls"):
            return cls._from_excel(path)
        return cls._from_delimited(path)

    @classmethod
    def _from_delimited(cls, path: str):
        """读 CSV/TXT，自动探测分隔符。"""
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            sample = f.read(4096)
        # 探测分隔符
        for line in sample.splitlines()[:5]:
            line = line.strip()
            if not line:
                continue
            if "\t" in line:
                delim = "\t"
            elif "," in line:
                delim = ","
            elif ";" in line:
                delim = ";"
            else:
                delim = r"\s+"
            break
        else:
            delim = ","

        rows = []
        with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.reader(f, delimiter=delim if delim != r"\s+" else None,
                                skipinitialspace=True)
            for row in reader:
                if delim == r"\s+":
                    row = row[0].split()
                rows.append([c.strip() for c in row])

        return cls._from_rows(rows, os.path.basename(path))

    @classmethod
    def _from_excel(cls, path: str):
        try:
            import pandas as pd
        except ImportError:
            raise RuntimeError("读取 Excel 需要 pandas")
        df = pd.read_excel(path, header=None, dtype=object)
        rows = df.astype(object).where(df.notna(), "").values.tolist()
        rows = [["" if v is None else str(v) for v in r] for r in rows]
        return cls._from_rows(rows, os.path.basename(path))

    @classmethod
    def _from_rows(cls, rows: list, name: str):
        """把原始行列表转成工作表，自动推断列类型与表头。"""
        if not rows:
            ws = cls(name)
            return ws
        # 统一列数
        ncols = max(len(r) for r in rows)
        for r in rows:
            r.extend([""] * (ncols - len(r)))

        # 判断第一行是否为表头（含非数字文本）
        header_row = rows[0]
        header_is_text = all(
            parse_numeric(v) is None and v.strip() != "" for v in header_row
        )
        data = rows[1:] if header_is_text else rows

        ws = cls(name)
        ws.columns = []
        for ci in range(ncols):
            colname = str(header_row[ci]).strip() if header_is_text else column_letter(ci)
            if not colname:
                colname = column_letter(ci)
            values = [data[ri][ci] for ri in range(len(data))]
            # 推断类型：全数字 -> 数值列；否则文本列
            numeric_count = sum(1 for v in values if parse_numeric(v) is not None)
            nonempty = sum(1 for v in values if str(v).strip() != "")
            if nonempty == 0:
                ctype = CTYPE_Y
            elif numeric_count / max(nonempty, 1) >= 0.8:
                ctype = CTYPE_Y
            else:
                ctype = CTYPE_LABEL
            ws.columns.append({"name": colname, "ctype": ctype, "values": values})

        # 第一列默认为 X，其余为 Y（纯数值时）
        if ws.ncols() >= 2 and ws.columns[0]["ctype"] != CTYPE_LABEL:
            ws.columns[0]["ctype"] = CTYPE_X
        return ws

    # -- 导出 --
    def to_csv(self, path: str):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([f"{c['name']}({c['ctype']})" for c in self.columns])
            n = self.nrows()
            for i in range(n):
                w.writerow([
                    c["values"][i] if i < len(c["values"]) else ""
                    for c in self.columns
                ])

    def to_excel(self, path: str):
        import pandas as pd
        data = {}
        for c in self.columns:
            key = f"{c['name']}({c['ctype']})"
            vals = c["values"] + [""] * (self.nrows() - len(c["values"]))
            data[key] = vals
        pd.DataFrame(data).to_excel(path, index=False)


# ---------------------------------------------------------------------------
# 表格视图
# ---------------------------------------------------------------------------
class WorkSheetView(QTableWidget):
    """展示与编辑一张工作表。"""

    data_changed = Signal()
    status_message = Signal(str)

    def __init__(self, sheet: WorkSheet, parent=None):
        super().__init__(parent)
        self.sheet = sheet
        self._loading = False

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        self.horizontalHeader().setContextMenuPolicy(Qt.CustomContextMenu)
        self.horizontalHeader().customContextMenuRequested.connect(self._header_menu)

        self.verticalHeader().setDefaultSectionSize(26)
        self.verticalHeader().setVisible(True)

        self.itemChanged.connect(self._on_item_changed)
        self.reload()

    # -- 刷新 --
    def reload(self):
        self._loading = True
        ncols = self.sheet.ncols()
        nrows = self.sheet.nrows()
        self.setRowCount(max(nrows, 1))
        self.setColumnCount(ncols)

        self.setHorizontalHeaderLabels(self.sheet.col_names())
        self.horizontalHeader().setDefaultSectionSize(96)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        for ci, col in enumerate(self.sheet.columns):
            for ri in range(len(col["values"])):
                v = col["values"][ri]
                item = QTableWidgetItem("" if v is None else str(v))
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if col["ctype"] in (CTYPE_X, CTYPE_Y, CTYPE_Z, CTYPE_YERR, CTYPE_XERR):
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                else:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                self.setItem(ri, ci, item)
        self._loading = False

    def _on_item_changed(self, item):
        if self._loading:
            return
        ri, ci = item.row(), item.column()
        text = item.text()
        # 同步到模型
        col = self.sheet.columns[ci]
        while len(col["values"]) <= ri:
            col["values"].append("")
        col["values"][ri] = text
        # 若需要，扩展行数
        if ri >= self.sheet.nrows() - 1:
            pass
        self.data_changed.emit()

    def _commit_pending(self):
        """把当前表格内容写回模型。"""
        for ci in range(self.columnCount()):
            col = self.sheet.columns[ci]
            vals = []
            for ri in range(self.rowCount()):
                item = self.item(ri, ci)
                vals.append(item.text() if item else "")
            col["values"] = vals

    # -- 右键菜单（列）--
    def _header_menu(self, pos):
        ci = self.horizontalHeader().logicalIndexAt(pos)
        if ci < 0:
            return
        menu = QMenu(self)
        set_x = menu.addAction("设为 X 列")
        set_y = menu.addAction("设为 Y 列")
        set_z = menu.addAction("设为 Z 列")
        set_err = menu.addAction("设为 Y 误差列")
        set_lbl = menu.addAction("设为标签列")
        set_ign = menu.addAction("设为忽略列")
        menu.addSeparator()
        act_ins = menu.addAction("左侧插入列")
        act_del = menu.addAction("删除此列")
        act_ren = menu.addAction("重命名列…")
        menu.addSeparator()
        act_sort = menu.addAction("整表按此列排序…")
        act_fill = menu.addAction("生成序列…")

        act = menu.exec(QCursor.pos())
        if act is None:
            return
        if act == set_x:
            self._set_ctype(ci, CTYPE_X)
        elif act == set_y:
            self._set_ctype(ci, CTYPE_Y)
        elif act == set_z:
            self._set_ctype(ci, CTYPE_Z)
        elif act == set_err:
            self._set_ctype(ci, CTYPE_YERR)
        elif act == set_lbl:
            self._set_ctype(ci, CTYPE_LABEL)
        elif act == set_ign:
            self._set_ctype(ci, CTYPE_IGNORE)
        elif act == act_ins:
            self._commit_pending()
            self.sheet.add_column(before=ci)
            self.reload()
            self.data_changed.emit()
        elif act == act_del:
            self._commit_pending()
            if self.sheet.remove_column(ci):
                self.reload()
                self.data_changed.emit()
            else:
                QMessageBox.information(self, "提示", "至少保留一列数据。")
        elif act == act_ren:
            name, ok = QInputDialog.getText(self, "重命名列", "列名称：",
                                            text=self.sheet.columns[ci]["name"])
            if ok and name.strip():
                self.sheet.columns[ci]["name"] = name.strip()
                self.reload()
        elif act == act_sort:
            self._sort_by_column(ci)
        elif act == act_fill:
            self._fill_sequence(ci)

    def _set_ctype(self, ci, ctype):
        self.sheet.columns[ci]["ctype"] = ctype
        self.reload()
        self.data_changed.emit()
        self.status_message.emit(f"列 {self.sheet.columns[ci]['name']} 已设为 {CTYPE_NAMES[ctype]}")

    def _sort_by_column(self, ci):
        self._commit_pending()
        # 数值排序
        pairs = []
        for ri in range(self.rowCount()):
            it = self.item(ri, ci)
            txt = it.text() if it else ""
            pairs.append((parse_numeric(txt), ri))
        have_num = any(p[0] is not None for p in pairs)
        if have_num:
            pairs.sort(key=lambda p: (p[0] is None, p[0] if p[0] is not None else 0))
        order = [p[1] for p in pairs]
        for col in self.sheet.columns:
            col["values"] = [col["values"][i] if i < len(col["values"]) else "" for i in order]
        self.reload()
        self.data_changed.emit()

    def _fill_sequence(self, ci):
        from PySide6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox
        dlg = QDialog(self)
        dlg.setWindowTitle("生成序列")
        form = QFormLayout(dlg)
        sp_start = QDoubleSpinBox(); sp_start.setRange(-1e12, 1e12); sp_start.setValue(0)
        sp_step = QDoubleSpinBox(); sp_step.setRange(-1e12, 1e12); sp_step.setValue(1)
        sp_n = QDoubleSpinBox(); sp_n.setRange(1, 1e6); sp_n.setDecimals(0); sp_n.setValue(self.rowCount() or 10)
        form.addRow("起始值：", sp_start)
        form.addRow("步长：", sp_step)
        form.addRow("点数：", sp_n)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec():
            n = int(sp_n.value())
            vals = [sp_start.value() + i * sp_step.value() for i in range(n)]
            self.sheet.columns[ci]["values"] = [f"{v:g}" for v in vals]
            self.reload()
            self.data_changed.emit()

    # -- 右键菜单（单元格）--
    def _context_menu(self, pos):
        item = self.itemAt(pos)
        menu = QMenu(self)
        if item is not None:
            act_cut = menu.addAction("剪切")
            act_copy = menu.addAction("复制")
            act_paste = menu.addAction("粘贴")
            menu.addSeparator()
            act_clear = menu.addAction("清除")
            act = menu.exec(QCursor.pos())
            if act == act_copy:
                self.copy()
            elif act == act_cut:
                self.cut()
            elif act == act_paste:
                self.paste()
            elif act == act_clear:
                for it in self.selectedItems():
                    it.setText("")
        else:
            act_insrow = menu.addAction("插入行")
            act_delrow = menu.addAction("删除行")
            act = menu.exec(QCursor.pos())
            if act == act_insrow:
                self._commit_pending()
                for col in self.sheet.columns:
                    col["values"].append("")
                self.reload()
            elif act == act_delrow:
                self._delete_rows()

    def _delete_rows(self):
        rows = sorted(set(i.row() for i in self.selectedIndexes()), reverse=True)
        if not rows:
            return
        self._commit_pending()
        for ri in rows:
            for col in self.sheet.columns:
                if ri < len(col["values"]):
                    del col["values"][ri]
        self.reload()
        self.data_changed.emit()

    # -- 数据访问便捷方法 --
    def selected_columns(self):
        """返回选中的列索引列表（按列选择）。"""
        idxs = sorted(set(i.column() for i in self.selectedIndexes()))
        return idxs if idxs else list(range(self.sheet.ncols()))

    def default_x_y(self):
        """自动找 X 列和第一个 Y 列。"""
        x_idx = None
        y_idx = None
        for i, c in enumerate(self.sheet.columns):
            if c["ctype"] == CTYPE_X and x_idx is None:
                x_idx = i
            elif c["ctype"] == CTYPE_Y and y_idx is None:
                y_idx = i
        if x_idx is None:
            # 第一列当 X
            for i, c in enumerate(self.sheet.columns):
                if c["ctype"] not in (CTYPE_LABEL, CTYPE_IGNORE, CTYPE_YERR, CTYPE_XERR):
                    x_idx = i
                    break
        if y_idx is None:
            for i, c in enumerate(self.sheet.columns):
                if c["ctype"] == CTYPE_Y:
                    y_idx = i
                    break
        if y_idx is None:
            for i, c in enumerate(self.sheet.columns):
                if i != x_idx and c["ctype"] not in (CTYPE_LABEL, CTYPE_IGNORE):
                    y_idx = i
                    break
        return x_idx, y_idx
