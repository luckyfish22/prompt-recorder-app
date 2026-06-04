from PyQt5.QtWidgets import (QMainWindow, QSplitter, QHBoxLayout, QVBoxLayout,
                                 QWidget, QPushButton, QLabel, QMessageBox, QDialog,
                                 QApplication)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QCloseEvent, QPainter, QFont, QPen, QColor, QFontMetrics
from src.config_loader import config
from src.api.deepseek_client import DeepSeekClient
from src.db import database
from src.ui.theme import STYLESHEET, COLORS, FONT_CAPTION, FONT_TITLE, MAX_TITLE_LENGTH, set_app_font
from src.ui.input_panel import InputPanel
from src.ui.history_panel import HistoryPanel
from src.ui.folder_tree import FolderTree
from src.ui.analysis_dialog import AnalysisDialog
from src.ui.settings_dialog import SettingsDialog


TITLE_SYSTEM_PROMPT = """Generate a concise, meaningful title for the following prompt.
Rules:
- Max 20 characters
- Capture the core topic or task
- Use the same language as the prompt
- Return ONLY the title text, no quotes, no prefixes, no explanation."""


class _TitleWorker(QThread):
    finished = pyqtSignal(int, str)  # prompt_id, title

    def __init__(self, prompt_id: int, prompt_text: str, client: DeepSeekClient):
        super().__init__()
        self._prompt_id = prompt_id
        self._prompt_text = prompt_text
        self._client = client

    def run(self):
        try:
            title = self._client.chat(TITLE_SYSTEM_PROMPT, self._prompt_text, temperature=0.3)
            title = title.strip().replace("\n", " ")[:MAX_TITLE_LENGTH]
            self.finished.emit(self._prompt_id, title)
        except Exception:
            pass  # Keep the temp title on failure


class _TitleLabel(QLabel):
    """Title label with painted stroke for extra boldness."""

    def __init__(self, text: str, color: str, size: int):
        super().__init__(text)
        self._color = QColor(color)
        self._size = size
        self.setMinimumHeight(size + 12)

    def sizeHint(self):
        fm = QFontMetrics(QFont(self.font().family(), self._size))
        sz = fm.size(0, self.text())
        return sz + QSize(sz.height() // 2 + 8, 12)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = QFont(self.font())
        font.setPixelSize(self._size)
        font.setItalic(True)
        font.setBold(True)
        painter.setFont(font)

        outline = QColor(
            max(0, self._color.red() - 50),
            max(0, self._color.green() - 40),
            max(0, self._color.blue() - 30),
        )
        pen = QPen(outline)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(self._color)
        rect = self.rect()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r = rect.translated(dx, dy)
            painter.drawText(r, Qt.AlignVCenter, self.text())


class MainWindow(QMainWindow):
    def __init__(self, floating_window=None):
        super().__init__()
        self._floating = floating_window
        self._client = DeepSeekClient(config.api_key, config.model)
        self._current_folder_id = None

        self.setWindowTitle("Prompt Recorder")
        self.setMinimumSize(700, 500)
        self.resize(1100, 750)
        self.setStyleSheet(STYLESHEET)

        self._init_ui()
        self._check_first_run()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setStyleSheet(f"background-color: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(16, 14, 16, 14)

        title = _TitleLabel("Prompt  Recorder", COLORS["primary"], FONT_TITLE)

        self._settings_btn = QPushButton("Settings")
        self._settings_btn.setProperty("secondary", True)
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.clicked.connect(self._open_settings)

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self._settings_btn)

        # Folder tree sidebar
        self._folder_tree = FolderTree()
        self._folder_tree.setFixedWidth(200)
        self._folder_tree.folder_changed.connect(self._on_folder_changed)

        # Two-panel splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._input_panel = InputPanel()
        self._history_panel = HistoryPanel()

        splitter.addWidget(self._input_panel)
        splitter.addWidget(self._history_panel)
        splitter.setSizes([400, 700])

        # Status bar
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px; padding: 4px 16px; "
            f"background: {COLORS['bg']}; border-top: 1px solid {COLORS['border']};"
        )

        # Right content area
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(splitter, stretch=1)
        content_layout.addWidget(self._status)

        # Main body: sidebar + content
        main_body = QHBoxLayout()
        main_body.setContentsMargins(0, 0, 0, 0)
        main_body.setSpacing(0)
        main_body.addWidget(self._folder_tree)
        main_body.addLayout(content_layout, stretch=1)

        root_layout.addWidget(title_bar)
        root_layout.addLayout(main_body, stretch=1)

        # Connect signals
        self._input_panel.save_requested.connect(self._on_save_prompt)
        self._history_panel.prompt_selected.connect(self._on_history_select)
        self._history_panel.prompt_deleted.connect(self._on_prompt_deleted)
        self._history_panel.analysis_requested.connect(self._on_analysis_requested)
        self._history_panel.prompt_changed.connect(self._on_prompt_changed)

        if self._floating:
            self._floating.folder_selected.connect(self._on_floating_folder_selected)

    def _on_floating_folder_selected(self, folder_id):
        self._folder_tree.select_folder(folder_id)

    def _on_prompt_changed(self):
        if self._floating:
            self._floating.refresh()

    def _on_save_prompt(self, text: str):
        title = text.replace("\n", " ")[:MAX_TITLE_LENGTH]
        prompt_id = database.save_prompt(
            title=title,
            original_text=text,
            folder_id=self._current_folder_id,
        )
        self._history_panel.refresh(folder_id=self._current_folder_id)
        if self._floating:
            self._floating.refresh()
        self._status.setText("Saved")

        # Async AI title generation
        if self._client.is_configured:
            self._title_worker = _TitleWorker(prompt_id, text, self._client)
            self._title_worker.finished.connect(self._on_title_generated)
            self._title_worker.start()

    def _on_title_generated(self, prompt_id: int, title: str):
        if title:
            database.update_prompt(prompt_id=prompt_id, title=title)
            self._history_panel.refresh(folder_id=self._current_folder_id)
            if self._floating:
                self._floating.refresh()

    def _on_analysis_requested(self, data: dict):
        self._status.setText("Analyzing...")
        dlg = AnalysisDialog(data, self)
        if dlg.exec_() == QDialog.Accepted:
            result = dlg.get_result()
            if result:
                database.update_prompt(
                    prompt_id=data["id"],
                    title=result["title"],
                    optimized_text=result["optimized_text"] if result["is_optimized"] else None,
                    is_optimized=1 if result["is_optimized"] else 0,
                    optimization_note=result["notes"] if result["notes"] else None,
                )
                self._history_panel.refresh(folder_id=self._current_folder_id)
                if self._floating:
                    self._floating.refresh()
                self._status.setText("Analysis saved")
        else:
            self._status.setText("")

    def _on_prompt_deleted(self):
        if self._floating:
            self._floating.refresh()

    def _on_folder_changed(self, folder_id):
        self._current_folder_id = folder_id
        self._history_panel._folder_id = folder_id
        self._history_panel.refresh(folder_id=folder_id)

    def _on_history_select(self, data: dict):
        # Left-click on history item — text already copied to clipboard by HistoryPanel
        self._status.setText("Copied to clipboard")

    def _open_settings(self):
        dlg = SettingsDialog(config, self)
        if dlg.exec_() == QDialog.Accepted:
            self._client.update_config(config.api_key, config.model)
            set_app_font(QApplication.instance(), config.font_family)
            self._status.setText("Settings saved")

    def _check_first_run(self):
        if not config.api_key:
            msg = QMessageBox(self)
            msg.setWindowTitle("Welcome")
            msg.setText("Please configure your DeepSeek API Key first.\n\nClick OK to open settings.")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.setStyleSheet(f"""
                QMessageBox {{ background-color: {COLORS['bg']}; }}
                QLabel {{ color: {COLORS['text_primary']}; font-size: {FONT_CAPTION}px; }}
                QPushButton {{
                    background-color: {COLORS['primary']};
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-size: {FONT_CAPTION}px;
                    min-width: 80px;
                }}
                QPushButton:hover {{ background-color: {COLORS['primary_hover']}; }}
            """)
            msg.exec_()
            self._open_settings()

    def closeEvent(self, event: QCloseEvent):
        if self._floating:
            self.hide()
            event.ignore()
        else:
            event.accept()

    def restore(self):
        self.show()
        self.raise_()
        self.activateWindow()
