from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget,
                                 QListWidgetItem, QLabel, QHBoxLayout, QMenu,
                                 QAction, QApplication)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QCursor
from src.db import database
from src.ui.theme import COLORS, FONT_SIZE, FONT_SIZE_SMALL


class HistoryPanel(QWidget):
    prompt_selected = pyqtSignal(dict)
    prompt_deleted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("历史记录")
        header.setStyleSheet(f"font-size: {FONT_SIZE_SMALL + 2}px; color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(header)

        self._search = QLineEdit()
        self._search.setPlaceholderText("搜索...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setCursor(Qt.PointingHandCursor)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemPressed.connect(self._on_item_pressed)
        layout.addWidget(self._list, stretch=1)

    def refresh(self, search=None):
        self._list.clear()
        prompts = database.get_all_prompts(search)
        for p in prompts:
            widget = self._build_item_widget(p)
            item = QListWidgetItem()
            hint = widget.sizeHint()
            hint.setHeight(hint.height() + 6)
            item.setSizeHint(hint)
            item.setData(Qt.UserRole, p)
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)

    def _build_item_widget(self, prompt: dict):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.setContentsMargins(0, 0, 0, 0)

        title_text = prompt.get("title") or prompt["original_text"].replace("\n", " ")[:30]
        title_label = QLabel(title_text)
        title_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: {FONT_SIZE}px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        title_label.setWordWrap(False)
        top.addWidget(title_label, stretch=1)

        cat_name = prompt.get("category_name", "")
        if cat_name:
            cat = QLabel(f" {cat_name} ")
            cat.setMinimumHeight(FONT_SIZE_SMALL + 12)
            cat.setStyleSheet(
                f"background: {COLORS['accent_bg']}; color: {COLORS['primary']}; "
                f"font-size: {FONT_SIZE_SMALL}px; border: none; "
                f"border-radius: {FONT_SIZE_SMALL // 2 + 6}px; padding: 0px 4px;"
            )
            top.addWidget(cat, alignment=Qt.AlignVCenter)

        layout.addLayout(top)

        time_label = QLabel(prompt.get("created_at", ""))
        time_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE_SMALL - 1}px; "
            f"background: transparent; border: none; padding: 0px;"
        )
        layout.addWidget(time_label)

        return w

    def _on_search(self, text):
        self.refresh(text if text else None)

    def _on_item_pressed(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        # Left click: copy original text to clipboard
        text = data.get("optimized_text") or data["original_text"]
        QApplication.clipboard().setText(text)
        self.prompt_selected.emit(data)

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_SIZE}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
        """)

        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self._delete_prompt(data))

        menu.exec_(QCursor.pos())

    def _delete_prompt(self, data: dict):
        database.delete_prompt(data["id"])
        self.refresh()
        self.prompt_deleted.emit()
