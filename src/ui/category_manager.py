from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                                 QMessageBox)
from PyQt5.QtCore import Qt
from src.ui.theme import COLORS, FONT_SIZE_SMALL


class CategoryManager(QDialog):
    def __init__(self, categories: list, parent=None):
        super().__init__(parent)
        self._categories = list(categories)
        self.setWindowTitle("Manage Categories")
        self.setMinimumSize(400, 350)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")
        self._init_ui()
        self._populate_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("Custom Categories")
        header.setStyleSheet(f"font-size: {FONT_SIZE_SMALL + 2}px; color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(header)

        desc = QLabel("Add your common categories. AI will prioritize these when classifying.")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE_SMALL}px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._list = QListWidget()
        layout.addWidget(self._list, stretch=1)

        add_layout = QHBoxLayout()
        add_layout.setSpacing(8)
        self._input = QLineEdit()
        self._input.setPlaceholderText("Enter new category name...")
        self._input.returnPressed.connect(self._add)
        add_layout.addWidget(self._input)

        add_btn = QPushButton("Add")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._add)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        del_btn = QPushButton("Delete Selected")
        del_btn.setProperty("secondary", True)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self._delete)
        layout.addWidget(del_btn)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        done_btn = QPushButton("Done")
        done_btn.setCursor(Qt.PointingHandCursor)
        done_btn.clicked.connect(self.accept)
        btn_layout.addWidget(done_btn)

        layout.addLayout(btn_layout)

    def _populate_list(self):
        self._list.clear()
        for cat in self._categories:
            item = QListWidgetItem(cat)
            self._list.addItem(item)

    def _add(self):
        name = self._input.text().strip()
        if not name:
            return
        if name in self._categories:
            QMessageBox.warning(self, "Duplicate", f"Category \"{name}\" already exists.")
            return
        self._categories.append(name)
        self._input.clear()
        self._populate_list()

    def _delete(self):
        current = self._list.currentItem()
        if current:
            name = current.text()
            self._categories.remove(name)
            self._populate_list()

    def get_categories(self):
        return self._categories
