from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QPushButton, QTextEdit, QFrame, QScrollArea,
                                 QWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from src.config_loader import config
from src.api.deepseek_client import DeepSeekClient
from src.services.optimizer import Optimizer
from src.ui.theme import COLORS, STYLESHEET, FONT_CAPTION


class _AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def __init__(self, prompt_text: str, client: DeepSeekClient, enable_optimization: bool):
        super().__init__()
        self._prompt = prompt_text
        self._client = client
        self._enable_optimization = enable_optimization

    def run(self):
        try:
            title = self._prompt.replace("\n", " ")[:50]
            optimized = ""
            notes = ""
            if self._enable_optimization:
                self.progress.emit("Optimizing...")
                optimizer = Optimizer(self._client)
                optimized, notes = optimizer.optimize(self._prompt)

            self.finished.emit({
                "title": title,
                "optimized": optimized,
                "notes": notes,
            })
        except Exception as e:
            self.finished.emit({"error": str(e)})


class AnalysisDialog(QDialog):
    """Popup window for AI optimization of a saved prompt."""

    def __init__(self, prompt_data: dict, parent=None):
        super().__init__(parent)
        self._prompt_data = prompt_data
        self._worker = None
        self._client = DeepSeekClient(config.api_key, config.model)
        self._result = None

        self.setWindowTitle("AI Analysis")
        self.setMinimumSize(550, 420)
        self.resize(600, 500)
        self.setStyleSheet(STYLESHEET)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._init_ui()
        self._start_analysis()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self._status_label = QLabel("Analyzing...")
        self._status_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;"
        )
        layout.addWidget(self._status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)

        self._original_label = QLabel("Original")
        self._original_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
        self._original_label.setVisible(False)
        self._content_layout.addWidget(self._original_label)

        self._original_text = QTextEdit()
        self._original_text.setReadOnly(True)
        self._original_text.setMaximumHeight(100)
        self._original_text.setVisible(False)
        self._content_layout.addWidget(self._original_text)

        self._optimized_label = QLabel("Optimized")
        self._optimized_label.setStyleSheet(f"color: {COLORS['primary']}; font-size: {FONT_CAPTION}px; font-weight: bold;")
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
            f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px; "
            f"background: {COLORS['accent_bg']}; padding: 10px; border-radius: 4px;"
        )
        self._notes_label.setVisible(False)
        self._content_layout.addWidget(self._notes_label)

        self._content_layout.addStretch()
        scroll.setWidget(self._content)
        layout.addWidget(scroll, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._accept_btn = QPushButton("Accept Optimized")
        self._accept_btn.setCursor(Qt.PointingHandCursor)
        self._accept_btn.clicked.connect(self._on_accept)
        self._accept_btn.setVisible(False)
        btn_layout.addWidget(self._accept_btn)

        self._keep_btn = QPushButton("Keep Original")
        self._keep_btn.setProperty("secondary", True)
        self._keep_btn.setCursor(Qt.PointingHandCursor)
        self._keep_btn.clicked.connect(self._on_keep)
        self._keep_btn.setVisible(False)
        btn_layout.addWidget(self._keep_btn)

        self._close_btn = QPushButton("Close")
        self._close_btn.setProperty("secondary", True)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self.reject)
        self._close_btn.setVisible(False)
        btn_layout.addWidget(self._close_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _start_analysis(self):
        self._client.update_config(config.api_key, config.model)
        self._worker = _AnalysisWorker(
            self._prompt_data["original_text"], self._client, config.enable_optimization
        )
        self._worker.progress.connect(lambda msg: self._status_label.setText(msg))
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.start()

    def _on_analysis_done(self, result: dict):
        self._worker = None

        if "error" in result:
            self._status_label.setText(f"Error: {result['error']}")
            self._close_btn.setVisible(True)
            return

        self._status_label.setText("Analysis complete")
        self._original_label.setVisible(True)
        self._original_text.setVisible(True)
        self._original_text.setPlainText(self._prompt_data["original_text"])

        optimized = result.get("optimized", "")
        notes = result.get("notes", "")

        if config.enable_optimization and optimized:
            self._optimized_label.setVisible(True)
            self._optimized_text.setVisible(True)
            self._optimized_text.setPlainText(optimized)
            self._notes_label.setVisible(True)
            self._notes_label.setText(notes if notes else "")
            self._accept_btn.setVisible(True)
            self._keep_btn.setVisible(True)
        else:
            self._accept_btn.setVisible(False)
            self._keep_btn.setVisible(False)

        self._close_btn.setVisible(True)

        self._analysis_result = {
            "title": result.get("title", ""),
            "optimized": optimized,
            "notes": notes,
        }

    def _on_accept(self):
        r = self._analysis_result
        self._result = {
            "is_optimized": True,
            "optimized_text": r["optimized"],
            "title": r["title"],
            "notes": r["notes"],
        }
        self.accept()

    def _on_keep(self):
        r = self._analysis_result
        self._result = {
            "is_optimized": False,
            "optimized_text": "",
            "title": r["title"],
            "notes": r["notes"],
        }
        self.accept()

    def get_result(self):
        return self._result
