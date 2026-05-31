from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QTextEdit, QFrame, QScrollArea)
from PyQt5.QtCore import pyqtSignal, Qt
from src.ui.theme import COLORS, FONT_SIZE_SMALL


class ResultPanel(QWidget):
    accept_clicked = pyqtSignal()
    keep_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._optimized_text_value = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("分析结果")
        header.setStyleSheet(f"font-size: {FONT_SIZE_SMALL + 2}px; color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: transparent; border: none; }}")

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(12)

        self._category_label = QLabel()
        self._category_label.setStyleSheet(
            f"background: {COLORS['accent_bg']}; color: {COLORS['primary']}; "
            f"padding: 4px 12px; border-radius: 12px; font-size: {FONT_SIZE_SMALL}px; font-weight: bold;"
        )
        self._category_label.setVisible(False)
        self._content_layout.addWidget(self._category_label)

        self._original_label = QLabel("原文")
        self._original_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE_SMALL}px;")
        self._original_label.setVisible(False)
        self._content_layout.addWidget(self._original_label)

        self._original_text = QTextEdit()
        self._original_text.setReadOnly(True)
        self._original_text.setMaximumHeight(120)
        self._original_text.setVisible(False)
        self._content_layout.addWidget(self._original_text)

        self._optimized_label = QLabel("优化版")
        self._optimized_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: {FONT_SIZE_SMALL}px; font-weight: bold;")
        self._optimized_label.setVisible(False)
        self._content_layout.addWidget(self._optimized_label)

        self._optimized_text = QTextEdit()
        self._optimized_text.setReadOnly(True)
        self._optimized_text.setMaximumHeight(150)
        self._optimized_text.setVisible(False)
        self._content_layout.addWidget(self._optimized_text)

        self._notes_label = QLabel()
        self._notes_label.setWordWrap(True)
        self._notes_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE_SMALL}px; "
            f"background: {COLORS['accent_bg']}; padding: 10px; border-radius: 4px;"
        )
        self._notes_label.setVisible(False)
        self._content_layout.addWidget(self._notes_label)

        self._content_layout.addStretch()
        scroll.setWidget(self._content)
        layout.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._accept_btn = QPushButton("采用优化")
        self._accept_btn.setCursor(Qt.PointingHandCursor)
        self._accept_btn.clicked.connect(lambda: self.accept_clicked.emit())
        self._accept_btn.setVisible(False)
        btn_layout.addWidget(self._accept_btn)

        self._keep_btn = QPushButton("保留原文")
        self._keep_btn.setProperty("secondary", True)
        self._keep_btn.setCursor(Qt.PointingHandCursor)
        self._keep_btn.clicked.connect(lambda: self.keep_clicked.emit())
        self._keep_btn.setVisible(False)
        btn_layout.addWidget(self._keep_btn)

        self._save_btn = QPushButton("保存")
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(lambda: self.keep_clicked.emit())
        self._save_btn.setVisible(False)
        btn_layout.addWidget(self._save_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def show_result(self, original: str, category: str, optimized: str = "", notes: str = "", optimization_enabled: bool = True):
        self._optimized_text_value = optimized

        self._category_label.setText(category)
        self._category_label.setVisible(True)

        self._original_label.setVisible(True)
        self._original_text.setVisible(True)
        self._original_text.setPlainText(original)

        if optimization_enabled and optimized:
            self._optimized_label.setVisible(True)
            self._optimized_text.setVisible(True)
            self._optimized_text.setPlainText(optimized)
            self._notes_label.setVisible(True)
            self._notes_label.setText(notes if notes else "")
            self._accept_btn.setVisible(True)
            self._keep_btn.setVisible(True)
            self._save_btn.setVisible(False)
        else:
            self._optimized_label.setVisible(False)
            self._optimized_text.setVisible(False)
            self._notes_label.setVisible(False)
            self._accept_btn.setVisible(False)
            self._keep_btn.setVisible(False)
            self._save_btn.setVisible(True)

    def clear(self):
        self._category_label.setVisible(False)
        self._original_label.setVisible(False)
        self._original_text.setVisible(False)
        self._optimized_label.setVisible(False)
        self._optimized_text.setVisible(False)
        self._notes_label.setVisible(False)
        self._accept_btn.setVisible(False)
        self._keep_btn.setVisible(False)
        self._save_btn.setVisible(False)

    def get_optimized_text(self):
        return self._optimized_text_value
