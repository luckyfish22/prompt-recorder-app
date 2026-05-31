COLORS = {
    "primary": "#D97757",
    "primary_hover": "#C56545",
    "bg": "#FAFAF9",
    "surface": "#FFFFFF",
    "text_primary": "#1A1A1A",
    "text_secondary": "#6B6B6B",
    "border": "#E8E4DF",
    "accent_bg": "#F5F2EF",
}

FONT_FAMILY = "Microsoft YaHei"
MONO_FONT = "Consolas"
FONT_SIZE = 17
FONT_SIZE_SMALL = 14
FONT_SIZE_TITLE = 19

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS["bg"]};
}}

QLabel {{
    color: {COLORS["text_primary"]};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 8px;
    color: {COLORS["text_primary"]};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS["primary"]};
}}

QPushButton {{
    background-color: {COLORS["primary"]};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 24px;
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
}}

QPushButton:hover {{
    background-color: {COLORS["primary_hover"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["border"]};
    color: {COLORS["text_secondary"]};
}}

QPushButton[secondary="true"] {{
    background-color: transparent;
    color: {COLORS["text_secondary"]};
    border: 1px solid {COLORS["border"]};
}}

QPushButton[secondary="true"]:hover {{
    background-color: {COLORS["accent_bg"]};
}}

QListWidget {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    color: {COLORS["text_primary"]};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
    outline: none;
}}

QListWidget::item {{
    border-bottom: 1px solid {COLORS["border"]};
}}

QListWidget::item:hover {{
    background-color: {COLORS["accent_bg"]};
}}

QListWidget::item:selected {{
    background-color: {COLORS["accent_bg"]};
    color: {COLORS["text_primary"]};
}}

QSplitter::handle {{
    background-color: {COLORS["border"]};
    width: 1px;
}}

QScrollBar:vertical {{
    background: {COLORS["bg"]};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["border"]};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["text_secondary"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QComboBox {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 6px 12px;
    color: {COLORS["text_primary"]};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
}}

QComboBox:focus {{
    border-color: {COLORS["primary"]};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QCheckBox {{
    color: {COLORS["text_primary"]};
    font-family: "{FONT_FAMILY}";
    font-size: {FONT_SIZE}px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS["border"]};
    border-radius: 3px;
    background-color: {COLORS["surface"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["primary"]};
    border-color: {COLORS["primary"]};
}}
"""
