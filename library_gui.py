#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图书管理系统 - PyQt5 图形界面版
================================
基于原有 CLI 程序逻辑，复用 config / file_handler / utils 模块，不改动原有代码。
功能：
  1. 图书管理 —— 新增 / 查看（分页翻页）/ 查询 / 修改 / 删除
  2. 借阅管理 —— 借出 / 归还 / 记录查询（全部 / 未归还 / 已归还）
  3. 数据统计 —— 总览 / 分类统计表格（区分实体册数与图书种数）/ 逾期提醒
运行方式：python library_gui.py  （需安装 PyQt5，使用系统 Python C:\\Python312）
"""

import sys
import datetime
import re

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem, QDialog,
    QFormLayout, QMessageBox, QHeaderView, QSpinBox, QLineEdit,
    QAbstractItemView, QFrame, QComboBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ===== 复用原有模块 =====
from config import initialSize, eachSize   # 首屏2条 / 后续每页5条
from file_handler import load_data, save_data
import utils   # makePage / local_pages（分页逻辑与CLI完全一致）


# ================================================================
#  工具函数（从原 CLI 程序中提取，保持逻辑一致）
# ================================================================

def find_indices_by_keys(data, pattern, keys=None, flags=0):
    """
    限定搜索特定键的正则匹配（与原 CLI find_indices_by_keys 逻辑一致）。
    """
    regex = re.compile(pattern, flags)
    indices = []
    if isinstance(keys, str):
        keys = [keys]
    for i, d in enumerate(data):
        check_keys = keys if keys else d.keys()
        for key in check_keys:
            val = d.get(key)
            if isinstance(val, str) and regex.search(val):
                indices.append(i)
                break
    return indices


def safe_int(val, default=0):
    """安全转 int，兼容原 CLI 中可能残留的字符串型库存数量。"""
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            try:
                return int(float(val))
            except ValueError:
                return default
    return default


def format_datetime(dt):
    """格式化 datetime / ISO 字符串为 'YYYY-MM-DD HH:MM:SS'。"""
    if dt is None or dt == "":
        return ""
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(dt, str):
        try:
            return datetime.datetime.fromisoformat(dt).strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return dt
    return str(dt)


def format_timedelta(td):
    """格式化 timedelta 为 'X天Y小时Z分钟'。"""
    if td is None or td == "":
        return ""
    if isinstance(td, datetime.timedelta):
        total = int(td.total_seconds())
        days = total // 86400
        hours = (total % 86400) // 3600
        minutes = (total % 3600) // 60
        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        return "".join(parts) if parts else "不足1分钟"
    return str(td)


def is_borrowed(b):
    """判断借阅记录是否为未归还（兼容 '已借出' 和 'borrowed' 两种写法）。"""
    return b.get("status") in ("已借出", "borrowed")


# ================================================================
#  对话框
# ================================================================

class AddBookDialog(QDialog):
    """新增图书对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增图书")
        self.setMinimumWidth(360)
        layout = QFormLayout(self)

        self.bookname_input = QLineEdit()
        self.author_input = QLineEdit()
        self.isbn_input = QLineEdit()
        self.category_input = QLineEdit()
        self.amount_input = QSpinBox()
        self.amount_input.setRange(1, 999999)
        self.amount_input.setValue(1)

        layout.addRow("书名：", self.bookname_input)
        layout.addRow("作者：", self.author_input)
        layout.addRow("ISBN：", self.isbn_input)
        layout.addRow("分类：", self.category_input)
        layout.addRow("库存数量：", self.amount_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确认添加")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "书名": self.bookname_input.text().strip(),
            "作者": self.author_input.text().strip(),
            "ISBN": self.isbn_input.text().strip(),
            "分类": self.category_input.text().strip(),
            "库存数量": self.amount_input.value(),
            "增加时间": str(datetime.datetime.now()),
        }


class EditBookDialog(QDialog):
    """修改图书对话框（ISBN 不可改，作为标识）"""

    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.setWindowTitle("修改图书信息")
        self.setMinimumWidth(360)
        layout = QFormLayout(self)

        self.isbn_label = QLineEdit(str(book.get("ISBN", "")))
        self.isbn_label.setReadOnly(True)
        self.bookname_input = QLineEdit(str(book.get("书名", "")))
        self.author_input = QLineEdit(str(book.get("作者", "")))
        self.category_input = QLineEdit(str(book.get("分类", "")))
        self.amount_input = QSpinBox()
        self.amount_input.setRange(0, 999999)
        self.amount_input.setValue(safe_int(book.get("库存数量", 0)))

        layout.addRow("ISBN（不可修改）：", self.isbn_label)
        layout.addRow("书名：", self.bookname_input)
        layout.addRow("作者：", self.author_input)
        layout.addRow("分类：", self.category_input)
        layout.addRow("库存数量：", self.amount_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确认修改")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "书名": self.bookname_input.text().strip(),
            "作者": self.author_input.text().strip(),
            "分类": self.category_input.text().strip(),
            "库存数量": self.amount_input.value(),
        }


class BorrowDialog(QDialog):
    """借出图书对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("借出图书")
        self.setMinimumWidth(360)
        layout = QFormLayout(self)

        self.book_input = QLineEdit()
        self.book_input.setPlaceholderText("输入书名或ISBN")
        self.borrower_input = QLineEdit()
        self.borrower_input.setPlaceholderText("输入借阅人姓名")

        layout.addRow("书名 / ISBN：", self.book_input)
        layout.addRow("借阅人：", self.borrower_input)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确认借出")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def get_data(self):
        return {
            "book_input": self.book_input.text().strip(),
            "borrower": self.borrower_input.text().strip(),
        }


class ReturnDialog(QDialog):
    """归还图书对话框 —— 列出所有未归还记录供选择"""

    def __init__(self, borrows, parent=None):
        super().__init__(parent)
        self.setWindowTitle("归还图书")
        self.setMinimumSize(620, 420)
        self.selected_borrow = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("请选择要归还的图书记录："))

        # 筛选栏
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("筛选借阅人："))
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("输入借阅人姓名筛选（可选）")
        self.filter_input.textChanged.connect(self._on_filter)
        filter_layout.addWidget(self.filter_input)
        layout.addLayout(filter_layout)

        # 未归还列表
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["借阅人", "书名", "ISBN", "借出日期", "已借天数"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        self.all_unreturned = [b for b in borrows if is_borrowed(b)]
        self.displayed = list(self.all_unreturned)
        self._populate()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("确认归还")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self._confirm)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _on_filter(self, text):
        text = text.strip()
        if text:
            self.displayed = [b for b in self.all_unreturned if text in str(b.get("borrower", ""))]
        else:
            self.displayed = list(self.all_unreturned)
        self._populate()

    def _populate(self):
        self.table.setRowCount(len(self.displayed))
        for i, b in enumerate(self.displayed):
            self.table.setItem(i, 0, QTableWidgetItem(str(b.get("borrower", ""))))
            self.table.setItem(i, 1, QTableWidgetItem(str(b.get("bookname", ""))))
            self.table.setItem(i, 2, QTableWidgetItem(str(b.get("isbn", ""))))
            self.table.setItem(i, 3, QTableWidgetItem(format_datetime(b.get("borrow_date"))))
            bd = b.get("borrow_date")
            if isinstance(bd, datetime.datetime):
                days = (datetime.datetime.now() - bd).days
                self.table.setItem(i, 4, QTableWidgetItem(f"{days} 天"))
            else:
                self.table.setItem(i, 4, QTableWidgetItem(""))

    def _confirm(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先选择要归还的图书！")
            return
        self.selected_borrow = self.displayed[row]
        self.accept()

    def get_selected_borrow(self):
        return self.selected_borrow


# ================================================================
#  主窗口
# ================================================================

class LibraryMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("图书管理系统 v2.0 (PyQt版)")
        self.setMinimumSize(920, 660)

        # ---------- 加载数据（与 CLI 一致） ----------
        self.books, self.borrows = load_data()
        if self.books == -1:
            self.books = []
            self.borrows = []

        # ---------- 分页 / 搜索状态 ----------
        self.current_display_list = self.books   # 当前表格展示的数据源
        self.current_page = 0
        self.is_search_mode = False

        # ---------- 构建 UI ----------
        self._init_ui()
        self._apply_style()
        self.refresh_book_table()

    # ------------------------------------------------------------------
    #  UI 构建
    # ------------------------------------------------------------------

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 顶部标题栏
        title = QLabel("图书管理系统 v2.0")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setFixedHeight(42)
        main_layout.addWidget(title)

        # Tab 容器
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_books = QWidget()
        self.tab_borrows = QWidget()
        self.tab_stats = QWidget()
        self.tabs.addTab(self.tab_books, "图书管理")
        self.tabs.addTab(self.tab_borrows, "借阅管理")
        self.tabs.addTab(self.tab_stats, "数据统计")
        self.tabs.currentChanged.connect(self._on_tab_changed)

        self._init_book_tab()
        self._init_borrow_tab()
        self._init_stats_tab()

    # ---- Tab 1: 图书管理 ----

    def _init_book_tab(self):
        layout = QVBoxLayout(self.tab_books)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 操作按钮栏
        bar = QHBoxLayout()
        for text, slot in [
            ("新增图书", self.add_book),
            ("查询图书", self.do_search),
            ("修改选中", self.edit_book),
            ("删除选中", self.delete_book),
            ("显示全部", self.reset_view),
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            bar.addWidget(btn)
        bar.addStretch()
        layout.addLayout(bar)

        # 搜索面板
        search_frame = QFrame()
        search_frame.setObjectName("panelFrame")
        sl = QHBoxLayout(search_frame)
        sl.setContentsMargins(8, 6, 8, 6)

        sl.addWidget(QLabel("书名:"))
        self.s_bookname = QLineEdit()
        sl.addWidget(self.s_bookname)

        sl.addWidget(QLabel("作者:"))
        self.s_author = QLineEdit()
        sl.addWidget(self.s_author)

        sl.addWidget(QLabel("ISBN:"))
        self.s_isbn = QLineEdit()
        sl.addWidget(self.s_isbn)

        sl.addWidget(QLabel("分类:"))
        self.s_category = QLineEdit()
        sl.addWidget(self.s_category)

        go_btn = QPushButton("搜索")
        go_btn.clicked.connect(self.do_search)
        sl.addWidget(go_btn)

        # 回车触发搜索
        for le in (self.s_bookname, self.s_author, self.s_isbn, self.s_category):
            le.returnPressed.connect(self.do_search)

        layout.addWidget(search_frame)

        # 图书表格
        self.book_table = QTableWidget()
        self.book_table.setColumnCount(6)
        self.book_table.setHorizontalHeaderLabels(
            ["书名", "作者", "ISBN", "分类", "库存数量", "增加时间"])
        self.book_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.book_table.setAlternatingRowColors(True)
        self.book_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.book_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.book_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.book_table.doubleClicked.connect(self.edit_book)
        layout.addWidget(self.book_table)

        # 分页控制栏
        pg = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel()
        self.page_info = QLabel(f"分页规则：首屏 {initialSize} 条 / 后续每页 {eachSize} 条")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn.clicked.connect(self.next_page)
        pg.addWidget(self.prev_btn)
        pg.addWidget(self.page_label)
        pg.addWidget(self.next_btn)
        pg.addStretch()
        pg.addWidget(self.page_info)
        layout.addLayout(pg)

    # ---- Tab 2: 借阅管理 ----

    def _init_borrow_tab(self):
        layout = QVBoxLayout(self.tab_borrows)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 操作按钮栏
        bar = QHBoxLayout()
        b1 = QPushButton("借出图书")
        b2 = QPushButton("归还图书")
        b1.clicked.connect(self.borrow_book)
        b2.clicked.connect(self.return_book)
        bar.addWidget(b1)
        bar.addWidget(b2)
        bar.addStretch()
        layout.addLayout(bar)

        # 筛选栏
        fl = QHBoxLayout()
        fl.addWidget(QLabel("筛选："))
        self.borrow_filter = QComboBox()
        self.borrow_filter.addItems(["全部记录", "未归还", "已归还"])
        self.borrow_filter.currentIndexChanged.connect(lambda: self.refresh_borrow_table())
        fl.addWidget(self.borrow_filter)
        fl.addStretch()
        layout.addLayout(fl)

        # 借阅记录表格
        self.borrow_table = QTableWidget()
        self.borrow_table.setColumnCount(8)
        self.borrow_table.setHorizontalHeaderLabels(
            ["ID", "ISBN", "书名", "借阅人", "借出日期", "归还日期", "借阅时长", "状态"])
        self.borrow_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.borrow_table.setAlternatingRowColors(True)
        self.borrow_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.borrow_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.borrow_table)

    # ---- Tab 3: 数据统计 ----

    def _init_stats_tab(self):
        layout = QVBoxLayout(self.tab_stats)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 总览信息卡片
        overview = QFrame()
        overview.setObjectName("statsFrame")
        ol = QHBoxLayout(overview)
        ol.setContentsMargins(12, 12, 12, 12)
        self.lbl_titles = QLabel()
        self.lbl_copies = QLabel()
        self.lbl_borrowed = QLabel()
        for lbl in (self.lbl_titles, self.lbl_copies, self.lbl_borrowed):
            lbl.setAlignment(Qt.AlignCenter)
            ol.addWidget(lbl)
        layout.addWidget(overview)

        # 分类统计
        cat_title = QLabel("分类统计（区分「实体册数」与「图书种数」）")
        cat_title.setStyleSheet("font-weight:bold; font-size:13px; margin-top:6px;")
        layout.addWidget(cat_title)

        self.cat_table = QTableWidget()
        self.cat_table.setColumnCount(3)
        self.cat_table.setHorizontalHeaderLabels(["分类", "实体册数", "图书种数"])
        self.cat_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cat_table.setAlternatingRowColors(True)
        self.cat_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.cat_table)

        # 逾期提醒
        od_title = QLabel("逾期提醒（借阅周期 30 天）")
        od_title.setStyleSheet("font-weight:bold; font-size:13px; margin-top:6px;")
        layout.addWidget(od_title)

        self.od_table = QTableWidget()
        self.od_table.setColumnCount(5)
        self.od_table.setHorizontalHeaderLabels(["借阅人", "书名", "ISBN", "借出日期", "逾期天数"])
        self.od_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.od_table.setAlternatingRowColors(True)
        self.od_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.od_table)

    # ------------------------------------------------------------------
    #  图书管理操作
    # ------------------------------------------------------------------

    def add_book(self):
        dlg = AddBookDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        d = dlg.get_data()
        if not d["书名"] or not d["ISBN"]:
            QMessageBox.warning(self, "提示", "书名和 ISBN 不能为空！")
            return
        # 检查 ISBN 是否已存在
        for b in self.books:
            if b.get("ISBN") == d["ISBN"]:
                QMessageBox.warning(self, "提示", f"ISBN 为 {d['ISBN']} 的图书已存在！")
                return
        self.books.append(d)
        save_data(self.books, self.borrows)
        self.reset_view()
        QMessageBox.information(self, "成功", "添加图书成功！")

    def do_search(self):
        """多字段模糊搜索，取交集（与 CLI 1.3 逻辑一致）"""
        bn = self.s_bookname.text().strip()
        au = self.s_author.text().strip()
        isb = self.s_isbn.text().strip()
        cat = self.s_category.text().strip()

        sets_list = []
        if bn:
            sets_list.append(set(find_indices_by_keys(self.books, rf"{bn}", "书名")))
        if au:
            sets_list.append(set(find_indices_by_keys(self.books, rf"{au}", "作者")))
        if isb:
            sets_list.append(set(find_indices_by_keys(self.books, re.escape(isb), "ISBN")))
        if cat:
            sets_list.append(set(find_indices_by_keys(self.books, rf"{cat}", "分类")))

        if not sets_list:
            common = set(range(len(self.books)))
        else:
            common = set.intersection(*sets_list)

        self.current_display_list = [self.books[i] for i in common]
        self.is_search_mode = True
        self.current_page = 0
        self.refresh_book_table()

        if len(self.current_display_list) == 0:
            QMessageBox.information(self, "查询结果", "未找到匹配的图书。")

    def reset_view(self):
        self.is_search_mode = False
        self.current_display_list = self.books
        self.current_page = 0
        self.s_bookname.clear()
        self.s_author.clear()
        self.s_isbn.clear()
        self.s_category.clear()
        self.refresh_book_table()

    def edit_book(self):
        row = self.book_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在表格中选择要修改的图书！")
            return
        pages = utils.local_pages
        if self.current_page >= len(pages):
            return
        page_data = pages[self.current_page]
        if row >= len(page_data):
            return
        book = page_data[row]
        dlg = EditBookDialog(book, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        d = dlg.get_data()
        # 非空即改（与 CLI 1.4 逻辑一致）
        if d["书名"]:
            book["书名"] = d["书名"]
        if d["作者"]:
            book["作者"] = d["作者"]
        if d["分类"]:
            book["分类"] = d["分类"]
        book["库存数量"] = d["库存数量"]
        save_data(self.books, self.borrows)
        self.refresh_book_table()
        QMessageBox.information(self, "成功", "修改图书信息成功！")

    def delete_book(self):
        row = self.book_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请先在表格中选择要删除的图书！")
            return
        pages = utils.local_pages
        if self.current_page >= len(pages):
            return
        page_data = pages[self.current_page]
        if row >= len(page_data):
            return
        book = page_data[row]
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除《{book.get('书名', '')}》(ISBN: {book.get('ISBN', '')})吗？\n此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            if book in self.books:
                self.books.remove(book)
            save_data(self.books, self.borrows)
            self.reset_view()
            QMessageBox.information(self, "成功", "删除图书成功！")

    # ---- 分页 ----

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_book_table()

    def next_page(self):
        pages = utils.local_pages
        if self.current_page < len(pages) - 1:
            self.current_page += 1
            self.refresh_book_table()

    # ------------------------------------------------------------------
    #  借阅管理操作
    # ------------------------------------------------------------------

    def borrow_book(self):
        dlg = BorrowDialog(self)
        if dlg.exec_() != QDialog.Accepted:
            return
        d = dlg.get_data()
        key = d["book_input"]
        borrower = d["borrower"]
        if not key or not borrower:
            QMessageBox.warning(self, "提示", "书名/ISBN 和借阅人不能为空！")
            return

        found = False
        for book in self.books:
            if book.get("书名") == key or book.get("ISBN") == key:
                found = True
                stock = safe_int(book.get("库存数量", 0))
                if stock > 0:
                    book["库存数量"] = stock - 1
                    new_id = max([safe_int(b.get("id", 0)) for b in self.borrows], default=-1) + 1
                    self.borrows.append({
                        "id": new_id,
                        "isbn": book["ISBN"],
                        "bookname": book["书名"],
                        "borrower": borrower,
                        "borrow_date": datetime.datetime.now(),
                        "return_date": None,
                        "status": "已借出",
                        "borrow_duration": "",
                    })
                    save_data(self.books, self.borrows)
                    self.refresh_book_table()
                    self.refresh_borrow_table()
                    QMessageBox.information(self, "成功", "借出图书成功！")
                else:
                    QMessageBox.warning(self, "提示", "库存不足，无法借出！")
                break
        if not found:
            QMessageBox.warning(self, "提示", "未找到该图书！")

    def return_book(self):
        unreturned = [b for b in self.borrows if is_borrowed(b)]
        if not unreturned:
            QMessageBox.information(self, "提示", "当前没有未归还的图书。")
            return
        dlg = ReturnDialog(self.borrows, self)
        if dlg.exec_() != QDialog.Accepted:
            return
        borrow = dlg.get_selected_borrow()
        if not borrow:
            return
        # 归还操作（与 CLI return_borrowrcd_oprt 逻辑一致）
        borrow["return_date"] = datetime.datetime.now()
        borrow["borrow_duration"] = borrow["return_date"] - borrow["borrow_date"]
        borrow["status"] = "已归还"
        # 库存 +1
        for book in self.books:
            if book.get("ISBN") == borrow.get("isbn"):
                book["库存数量"] = safe_int(book.get("库存数量", 0)) + 1
                break
        save_data(self.books, self.borrows)
        self.refresh_book_table()
        self.refresh_borrow_table()
        duration_str = format_timedelta(borrow["borrow_duration"])
        QMessageBox.information(self, "成功", f"归还图书成功！\n借阅时长：{duration_str}")

    # ------------------------------------------------------------------
    #  刷新表格
    # ------------------------------------------------------------------

    def refresh_book_table(self):
        """刷新图书表格（使用 utils.makePage 分页，逻辑与 CLI 完全一致）"""
        utils.makePage(self.current_display_list)
        pages = utils.local_pages

        if len(pages) == 0:
            self.book_table.setRowCount(0)
            self.page_label.setText("第 0/0 页")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        if self.current_page >= len(pages):
            self.current_page = len(pages) - 1
        if self.current_page < 0:
            self.current_page = 0

        page_data = pages[self.current_page]
        self.book_table.setRowCount(len(page_data))
        for i, book in enumerate(page_data):
            self.book_table.setItem(i, 0, QTableWidgetItem(str(book.get("书名", ""))))
            self.book_table.setItem(i, 1, QTableWidgetItem(str(book.get("作者", ""))))
            self.book_table.setItem(i, 2, QTableWidgetItem(str(book.get("ISBN", ""))))
            self.book_table.setItem(i, 3, QTableWidgetItem(str(book.get("分类", ""))))
            self.book_table.setItem(i, 4, QTableWidgetItem(str(book.get("库存数量", ""))))
            self.book_table.setItem(i, 5, QTableWidgetItem(format_datetime(book.get("增加时间"))))

        total = len(self.current_display_list)
        mode = "搜索结果" if self.is_search_mode else "全部图书"
        self.page_label.setText(f"第 {self.current_page + 1}/{len(pages)} 页  |  {mode}共 {total} 条")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < len(pages) - 1)

    def refresh_borrow_table(self):
        """刷新借阅记录表格"""
        idx = self.borrow_filter.currentIndex() if hasattr(self, "borrow_filter") else 0
        if idx == 1:
            display = [b for b in self.borrows if is_borrowed(b)]
        elif idx == 2:
            display = [b for b in self.borrows if b.get("status") == "已归还"]
        else:
            display = self.borrows

        self.borrow_table.setRowCount(len(display))
        for i, b in enumerate(display):
            self.borrow_table.setItem(i, 0, QTableWidgetItem(str(b.get("id", ""))))
            self.borrow_table.setItem(i, 1, QTableWidgetItem(str(b.get("isbn", ""))))
            self.borrow_table.setItem(i, 2, QTableWidgetItem(str(b.get("bookname", ""))))
            self.borrow_table.setItem(i, 3, QTableWidgetItem(str(b.get("borrower", ""))))
            self.borrow_table.setItem(i, 4, QTableWidgetItem(format_datetime(b.get("borrow_date"))))
            self.borrow_table.setItem(i, 5, QTableWidgetItem(format_datetime(b.get("return_date"))))
            self.borrow_table.setItem(i, 6, QTableWidgetItem(format_timedelta(b.get("borrow_duration"))))
            self.borrow_table.setItem(i, 7, QTableWidgetItem(str(b.get("status", ""))))

    def refresh_stats(self):
        """刷新数据统计（总览 + 分类统计表格 + 逾期提醒）"""
        # ---- 总览 ----
        total_titles = len(self.books)
        total_stock = sum(safe_int(b.get("库存数量", 0)) for b in self.books)
        borrowed_count = len([b for b in self.borrows if is_borrowed(b)])
        total_copies = total_stock + borrowed_count   # 实体总册数 = 库存 + 在借

        self.lbl_titles.setText(f"馆藏图书种数\n{total_titles} 种")
        self.lbl_copies.setText(f"馆藏图书总册数\n{total_copies} 册")
        self.lbl_borrowed.setText(f"在借册数\n{borrowed_count} 册")

        # ---- 分类统计（区分实体册数与图书种数） ----
        category_set = set(b.get("分类", "") for b in self.books if "分类" in b)
        cat_dict = {key: [0, 0] for key in category_set}   # [实体册数, 图书种数]

        for book in self.books:
            cat = book.get("分类")
            if cat in cat_dict:
                cat_dict[cat][0] += safe_int(book.get("库存数量", 0))   # 库存册数
                cat_dict[cat][1] += 1                                    # 图书种数

        # 借出的书加回实体册数
        for borrow in self.borrows:
            if is_borrowed(borrow):
                for book in self.books:
                    if book.get("ISBN") == borrow.get("isbn"):
                        cat = book.get("分类")
                        if cat in cat_dict:
                            cat_dict[cat][0] += 1
                        break

        self.cat_table.setRowCount(len(cat_dict) + 1)   # +1 合计行
        sum_copies = 0
        sum_titles = 0
        for i, (cat, vals) in enumerate(sorted(cat_dict.items())):
            self.cat_table.setItem(i, 0, QTableWidgetItem(cat))
            self.cat_table.setItem(i, 1, QTableWidgetItem(f"{vals[0]} 册"))
            self.cat_table.setItem(i, 2, QTableWidgetItem(f"{vals[1]} 种"))
            sum_copies += vals[0]
            sum_titles += vals[1]

        # 合计行
        r = len(cat_dict)
        for col, text in enumerate(["合计", f"{sum_copies} 册", f"{sum_titles} 种"]):
            item = QTableWidgetItem(text)
            item.setFont(QFont("", weight=QFont.Bold))
            self.cat_table.setItem(r, col, item)

        # ---- 逾期提醒 ----
        overdue = []
        for b in self.borrows:
            if is_borrowed(b):
                bd = b.get("borrow_date")
                if isinstance(bd, datetime.datetime):
                    if datetime.datetime.now() > bd + datetime.timedelta(days=30):
                        od_days = (datetime.datetime.now() - bd - datetime.timedelta(days=30)).days
                        overdue.append((b, od_days))

        self.od_table.setRowCount(len(overdue))
        for i, (b, days) in enumerate(overdue):
            self.od_table.setItem(i, 0, QTableWidgetItem(str(b.get("borrower", ""))))
            self.od_table.setItem(i, 1, QTableWidgetItem(str(b.get("bookname", ""))))
            self.od_table.setItem(i, 2, QTableWidgetItem(str(b.get("isbn", ""))))
            self.od_table.setItem(i, 3, QTableWidgetItem(format_datetime(b.get("borrow_date"))))
            self.od_table.setItem(i, 4, QTableWidgetItem(f"{days} 天"))

    # ------------------------------------------------------------------
    #  事件
    # ------------------------------------------------------------------

    def _on_tab_changed(self, index):
        if index == 0:
            self.refresh_book_table()
        elif index == 1:
            self.refresh_borrow_table()
        elif index == 2:
            self.refresh_stats()

    def closeEvent(self, event):
        save_data(self.books, self.borrows)
        reply = QMessageBox.question(
            self, "确认退出",
            "数据已自动保存。确定要退出系统吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # ------------------------------------------------------------------
    #  样式
    # ------------------------------------------------------------------

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f6fa; }
            QLabel#titleLabel {
                font-size: 18px; font-weight: bold; color: #ffffff;
                background-color: #2c3e50;
            }
            QTabWidget::pane { border: 1px solid #ccc; background: #ffffff; }
            QTabBar::tab {
                background: #dfe6e9; padding: 8px 24px; margin-right: 2px;
                border-top-left-radius: 4px; border-top-right-radius: 4px;
                font-size: 13px;
            }
            QTabBar::tab:selected { background: #2980b9; color: white; font-weight: bold; }
            QTabBar::tab:hover:!selected { background: #b2bec3; }
            QPushButton {
                background-color: #2980b9; color: white; border: none;
                padding: 6px 18px; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background-color: #3498db; }
            QPushButton:pressed { background-color: #2471a3; }
            QPushButton:disabled { background-color: #bdc3c7; }
            QTableWidget { gridline-color: #dcdde1; font-size: 13px; }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background-color: #2c3e50; color: white;
                font-weight: bold; padding: 6px; border: none;
            }
            QTableWidget::item:alternate { background-color: #f0f3f5; }
            QLineEdit {
                padding: 4px 8px; border: 1px solid #ccc;
                border-radius: 3px; font-size: 13px;
            }
            QFrame#panelFrame {
                background-color: #ecf0f1; border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QFrame#statsFrame {
                background-color: #ecf0f1; border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QFrame#statsFrame QLabel {
                font-size: 15px; font-weight: bold; color: #2c3e50; padding: 8px;
            }
            QComboBox {
                padding: 4px 8px; border: 1px solid #ccc;
                border-radius: 3px; font-size: 13px;
            }
            QSpinBox {
                padding: 4px 8px; border: 1px solid #ccc;
                border-radius: 3px; font-size: 13px;
            }
        """)


# ================================================================
#  主入口
# ================================================================

from time_wrapper_again import timer_with_final_popup
@timer_with_final_popup
def main():
    app = QApplication(sys.argv)
    app.setFont(QFont("Microsoft YaHei", 10))
    window = LibraryMainWindow()
    window.show()
    #sys.exit(app.exec_())
    # ⚠️ 注意：这里不要写 sys.exit(...)，而是直接返回退出码 #dpsk#2026.07.28#
    # ⚠️ 必须返回 app 以保持 QApplication 引用存活，否则之后 wrapper 中 QMessageBox 会报错
    exit_code = app.exec_()
    return app, exit_code


if __name__ == "__main__":
    main()
