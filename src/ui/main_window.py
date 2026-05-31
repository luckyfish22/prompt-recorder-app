from PyQt5.QtWidgets import (QMainWindow, QSplitter, QHBoxLayout, QVBoxLayout,
                                 QWidget, QPushButton, QLabel, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from src.config_loader import config
from src.api.deepseek_client import DeepSeekClient
from src.services.categorizer import Categorizer
from src.services.optimizer import Optimizer
from src.db import database
from src.ui.theme import STYLESHEET, COLORS, FONT_SIZE_SMALL
from src.ui.input_panel import InputPanel
from src.ui.result_panel import ResultPanel
from src.ui.history_panel import HistoryPanel
from src.ui.settings_dialog import SettingsDialog


class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)

    def __init__(self, prompt_text: str, client: DeepSeekClient, enable_optimization: bool):
        super().__init__()
        self._prompt = prompt_text
        self._client = client
        self._enable_optimization = enable_optimization

    def run(self):
        try:
            categorizer = Categorizer(self._client)
            title, category = categorizer.classify(self._prompt)

            optimized = ""
            notes = ""
            if self._enable_optimization:
                self.progress.emit("正在优化...")
                optimizer = Optimizer(self._client)
                optimized, notes = optimizer.optimize(self._prompt)

            self.finished.emit({
                "title": title,
                "category": category,
                "optimized": optimized,
                "notes": notes,
            })
        except Exception as e:
            self.finished.emit({"error": str(e)})


class MainWindow(QMainWindow):
    def __init__(self, floating_window=None):
        super().__init__()
        self._floating = floating_window
        self._client = DeepSeekClient(config.api_key, config.model)
        self._current_prompt = ""
        self._current_title = ""
        self._current_category = ""
        self._current_optimized = ""
        self._current_notes = ""
        self._worker = None

        self.setWindowTitle("Prompt Recorder")
        self.setMinimumSize(900, 500)
        self.resize(1200, 750)
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
        title_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("Prompt Recorder")
        title.setStyleSheet(f"font-size: 16px; color: {COLORS['text_primary']}; font-weight: bold; border: none;")

        self._settings_btn = QPushButton("设置")
        self._settings_btn.setProperty("secondary", True)
        self._settings_btn.setCursor(Qt.PointingHandCursor)
        self._settings_btn.clicked.connect(self._open_settings)

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self._settings_btn)

        # Three-panel splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        self._input_panel = InputPanel()
        self._result_panel = ResultPanel()
        self._history_panel = HistoryPanel()

        splitter.addWidget(self._input_panel)
        splitter.addWidget(self._result_panel)
        splitter.addWidget(self._history_panel)
        splitter.setSizes([400, 400, 400])

        # Status bar
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_SIZE_SMALL}px; padding: 4px 16px; "
            f"background: {COLORS['bg']}; border-top: 1px solid {COLORS['border']};"
        )

        root_layout.addWidget(title_bar)
        root_layout.addWidget(splitter, stretch=1)
        root_layout.addWidget(self._status)

        # Connect signals
        self._input_panel.analyze_requested.connect(self._on_analyze)
        self._result_panel.accept_clicked.connect(self._on_accept)
        self._result_panel.keep_clicked.connect(self._on_keep)
        self._history_panel.prompt_selected.connect(self._on_history_select)

    def _on_analyze(self, text: str):
        self._current_prompt = text
        self._result_panel.clear()
        self._status.setText("正在分析...")

        self._client.update_config(config.api_key, config.model)

        self._worker = AnalysisWorker(text, self._client, config.enable_optimization)
        self._worker.progress.connect(lambda msg: self._status.setText(msg))
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.start()

    def _on_analysis_done(self, result: dict):
        self._input_panel.on_analysis_done()
        self._worker = None

        if "error" in result:
            self._result_panel.clear()
            self._status.setText(f"错误: {result['error']}")
            QMessageBox.warning(self, "分析失败", f"API 调用出错:\n{result['error']}")
            return

        self._current_title = result.get("title", "")
        self._current_category = result["category"]
        self._current_optimized = result.get("optimized", "")
        self._current_notes = result.get("notes", "")

        self._result_panel.show_result(
            original=self._current_prompt,
            category=self._current_category,
            optimized=self._current_optimized,
            notes=self._current_notes,
            optimization_enabled=config.enable_optimization,
        )
        self._status.setText("分析完成")

    def _on_accept(self):
        self._save_prompt(is_optimized=1)
        self._status.setText("已保存（采用优化版）")

    def _on_keep(self):
        self._save_prompt(is_optimized=0)
        self._status.setText("已保存（保留原文）")

    def _save_prompt(self, is_optimized: int):
        cat_id = self._ensure_category(self._current_category)
        optimized_text = self._current_optimized if is_optimized else None
        database.save_prompt(
            title=self._current_title,
            original_text=self._current_prompt,
            category_id=cat_id,
            optimized_text=optimized_text,
            is_optimized=is_optimized,
            optimization_note=self._current_notes if self._current_notes else None,
        )
        self._history_panel.refresh()
        if self._floating:
            self._floating.refresh()

    def _ensure_category(self, name: str) -> int:
        cats = database.get_all_categories()
        for c in cats:
            if c["name"] == name:
                return c["id"]
        database.add_category(name)
        cats = database.get_all_categories()
        for c in cats:
            if c["name"] == name:
                return c["id"]
        return 0

    def _on_history_select(self, data: dict):
        self._result_panel.clear()
        cat_name = data.get("category_name", "未分类")
        optimized = data.get("optimized_text", "")
        notes = data.get("optimization_note", "")
        self._result_panel.show_result(
            original=data["original_text"],
            category=cat_name,
            optimized=optimized,
            notes=notes if notes else "",
            optimization_enabled=bool(optimized),
        )
        self._result_panel._accept_btn.setVisible(False)
        self._result_panel._keep_btn.setVisible(False)
        self._result_panel._save_btn.setVisible(False)

    def _open_settings(self):
        dlg = SettingsDialog(config, self)
        if dlg.exec_() == QDialog.Accepted:
            self._client.update_config(config.api_key, config.model)
            self._status.setText("设置已保存")

    def _check_first_run(self):
        if not config.api_key:
            QMessageBox.information(
                self, "欢迎使用",
                "首次使用请先配置 DeepSeek API Key。\n\n"
                "点击确定后进入设置页面。"
            )
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
