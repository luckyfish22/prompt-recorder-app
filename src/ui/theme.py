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

# ── Font sizes ──────────────────────────────────
#  修改以下数值即可全局调整字号，重启 app 生效。

FONT_BODY    = 22  # 正文：输入框、提示词列表项、按钮文字
FONT_HEADER  = 22  # 区域标题：各面板标题（"History"、"Input"）
FONT_CAPTION = 19  # 辅助标签：文件夹标签、状态栏、设置项标签
FONT_MICRO   = 15  # 微小文字：历史记录时间戳
FONT_FLOAT   = 17  # 悬浮窗：下拉框、翻译输入框
FONT_TITLE   = 28  # 主标题：顶部 "Prompt Recorder"

FONT_LIBRARY = [
    "Microsoft YaHei",
    "Segoe UI",
    "DengXian",
    "SimSun",
    "KaiTi",
    "FangSong",
    "Arial",
    "Times New Roman",
    "Georgia",
    "Consolas",
    "Cascadia Code",
]


def set_app_font(app, font_family: str):
    """Apply a font family globally across the app."""
    from PyQt5.QtGui import QFont
    global FONT_FAMILY
    FONT_FAMILY = font_family
    font = QFont(font_family, FONT_BODY)
    app.setFont(font)

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS["bg"]};
}}

QLabel {{
    color: {COLORS["text_primary"]};
    
    font-size: {FONT_BODY}px;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    padding: 8px;
    color: {COLORS["text_primary"]};
    
    font-size: {FONT_BODY}px;
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
    
    font-size: {FONT_BODY}px;
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
    
    font-size: {FONT_BODY}px;
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
    
    font-size: {FONT_BODY}px;
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
    
    font-size: {FONT_BODY}px;
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

QToolTip {{
    font-size: 12px;
}}

QMenu {{
    font-size: 16px;
}}
"""
