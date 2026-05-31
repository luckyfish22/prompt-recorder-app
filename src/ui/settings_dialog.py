from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                 QLineEdit, QPushButton, QCheckBox, QComboBox,
                                 QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt
from src.ui.theme import COLORS, FONT_SIZE_SMALL
from src.ui.category_manager import CategoryManager
from src import autostart


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._categories = list(config.categories)
        self.setWindowTitle("Settings")
        self.setMinimumSize(480, 420)
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 18px; color: {COLORS['text_primary']}; font-weight: bold;")
        layout.addWidget(title)

        # API Key group
        api_group = QGroupBox("DeepSeek API")
        api_group.setStyleSheet(self._group_style())
        api_form = QFormLayout(api_group)
        api_form.setSpacing(10)
        api_form.setContentsMargins(16, 20, 16, 16)

        self._api_key_input = QLineEdit()
        self._api_key_input.setEchoMode(QLineEdit.Password)
        self._api_key_input.setPlaceholderText("sk-...")
        api_form.addRow("API Key:", self._api_key_input)

        self._show_key_btn = QPushButton("Show")
        self._show_key_btn.setProperty("secondary", True)
        self._show_key_btn.setFixedWidth(60)
        self._show_key_btn.clicked.connect(self._toggle_key_visibility)
        api_form.addRow("", self._show_key_btn)

        layout.addWidget(api_group)

        # Model
        model_layout = QHBoxLayout()
        model_layout.setSpacing(12)
        model_label = QLabel("Model:")
        model_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px;")
        model_layout.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.addItems(["deepseek-chat", "deepseek-reasoner"])
        self._model_combo.setCursor(Qt.PointingHandCursor)
        model_layout.addWidget(self._model_combo, stretch=1)
        layout.addLayout(model_layout)

        # Optimization toggle
        self._optimization_check = QCheckBox("Enable optimization suggestions")
        self._optimization_check.setCursor(Qt.PointingHandCursor)
        self._optimization_check.setToolTip("When disabled, only classification is performed without optimization.")
        layout.addWidget(self._optimization_check)

        self._autostart_check = QCheckBox("Auto-start with Windows")
        self._autostart_check.setCursor(Qt.PointingHandCursor)
        self._autostart_check.setToolTip("Launch to system tray when Windows starts.")
        layout.addWidget(self._autostart_check)

        # Category management
        cat_layout = QHBoxLayout()
        cat_label = QLabel("Custom categories:")
        cat_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 14px;")
        cat_layout.addWidget(cat_label)

        self._manage_cat_btn = QPushButton("Manage categories...")
        self._manage_cat_btn.setProperty("secondary", True)
        self._manage_cat_btn.setCursor(Qt.PointingHandCursor)
        self._manage_cat_btn.clicked.connect(self._open_category_manager)
        cat_layout.addWidget(self._manage_cat_btn)
        cat_layout.addStretch()
        layout.addLayout(cat_layout)

        layout.addStretch()

        # Save / Cancel
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("secondary", True)
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _group_style(self):
        return f"""
            QGroupBox {{
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 20px;
                font-size: 14px;
                color: {COLORS['text_primary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 6px;
                color: {COLORS['text_secondary']};
            }}
        """

    def _load_config(self):
        self._api_key_input.setText(self._config.api_key)
        idx = self._model_combo.findText(self._config.model)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
        self._optimization_check.setChecked(self._config.enable_optimization)
        self._autostart_check.setChecked(self._config.enable_autostart)

    def _toggle_key_visibility(self):
        if self._api_key_input.echoMode() == QLineEdit.Password:
            self._api_key_input.setEchoMode(QLineEdit.Normal)
            self._show_key_btn.setText("Hide")
        else:
            self._api_key_input.setEchoMode(QLineEdit.Password)
            self._show_key_btn.setText("Show")

    def _open_category_manager(self):
        dlg = CategoryManager(self._categories, self)
        if dlg.exec_() == QDialog.Accepted:
            self._categories = dlg.get_categories()

    def _save(self):
        self._config.set("api_key", self._api_key_input.text().strip())
        self._config.set("model", self._model_combo.currentText())
        self._config.set("enable_optimization", self._optimization_check.isChecked())
        enable_autostart = self._autostart_check.isChecked()
        self._config.set("enable_autostart", enable_autostart)
        self._config.set("categories", self._categories)
        autostart.set_autostart(enable_autostart)
        self.accept()
