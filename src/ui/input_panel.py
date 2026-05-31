from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QTextEdit
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeyEvent
from src.ui.theme import COLORS, MONO_FONT


class InputPanel(QWidget):
    save_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Type or paste your prompt here...")
        self._text_edit.setFontFamily(MONO_FONT)
        self._text_edit.setMinimumHeight(200)
        self._text_edit.installEventFilter(self)
        layout.addWidget(self._text_edit, stretch=1)

        self._save_btn = QPushButton("Save")
        self._save_btn.setCursor(Qt.PointingHandCursor)
        self._save_btn.clicked.connect(self._on_save)
        layout.addWidget(self._save_btn)

    def eventFilter(self, obj, event):
        if obj is self._text_edit and event.type() == QKeyEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not event.modifiers():
                self._on_save()
                return True
        return super().eventFilter(obj, event)

    def _on_save(self):
        text = self._text_edit.toPlainText().strip()
        if text:
            self.save_requested.emit(text)
            self._text_edit.clear()

    def clear(self):
        self._text_edit.clear()
