from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt
from src.ui.theme import COLORS, FONT_SIZE_SMALL, MONO_FONT


class InputPanel(QWidget):
    analyze_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QLabel("输入提示词")
        header.setStyleSheet(f"font-size: {FONT_SIZE_SMALL + 2}px; color: {COLORS['text_secondary']}; font-weight: bold;")
        layout.addWidget(header)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("在此输入或粘贴提示词...")
        self._text_edit.setFontFamily(MONO_FONT)
        self._text_edit.setMinimumHeight(200)
        layout.addWidget(self._text_edit, stretch=1)

        self._analyze_btn = QPushButton("分析")
        self._analyze_btn.setCursor(Qt.PointingHandCursor)
        self._analyze_btn.clicked.connect(self._on_analyze)
        layout.addWidget(self._analyze_btn)

    def _on_analyze(self):
        text = self._text_edit.toPlainText().strip()
        if text:
            self._analyze_btn.setEnabled(False)
            self._analyze_btn.setText("分析中...")
            self.analyze_requested.emit(text)

    def on_analysis_done(self):
        self._analyze_btn.setEnabled(True)
        self._analyze_btn.setText("分析")

    def clear(self):
        self._text_edit.clear()
