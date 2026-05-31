from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QPushButton,
                                 QApplication, QSizePolicy, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QMouseEvent, QCursor
from src.db import database
from src.ui.theme import COLORS, FONT_SIZE, FONT_SIZE_SMALL, FONT_FAMILY


class FloatingWindow(QWidget):
    show_main_requested = pyqtSignal()

    def __init__(self):
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._drag_pos = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        self.setFixedHeight(36)
        self.setMinimumWidth(260)
        self.resize(320, 36)
        self.setAttribute(Qt.WA_Hover, True)
        self.setObjectName("floatingWindow")
        self.setStyleSheet(f"""
            #floatingWindow {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 6, 4)
        layout.setSpacing(6)

        self._combo = QComboBox()
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._combo.installEventFilter(self)
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-family: "{FONT_FAMILY}";
                font-size: {FONT_SIZE}px;
                padding: 2px 4px;
            }}
            QComboBox:hover {{
                background-color: {COLORS['accent_bg']};
                border-radius: 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                color: {COLORS['text_primary']};
                font-size: {FONT_SIZE}px;
                selection-background-color: {COLORS['accent_bg']};
                selection-color: {COLORS['text_primary']};
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 8px;
                border-radius: 3px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {COLORS['accent_bg']};
            }}
        """)
        self._combo.activated.connect(self._on_item_selected)
        layout.addWidget(self._combo, stretch=1)

        self._main_btn = QPushButton("+")
        self._main_btn.setFixedSize(26, 26)
        self._main_btn.setCursor(Qt.PointingHandCursor)
        self._main_btn.setToolTip("打开主窗口")
        self._main_btn.installEventFilter(self)
        self._main_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
                border: none;
                border-radius: 13px;
                font-size: {FONT_SIZE}px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary']};
                color: white;
            }}
        """)
        self._main_btn.clicked.connect(self.show_main_requested.emit)
        layout.addWidget(self._main_btn)

    def refresh(self):
        self._combo.clear()
        prompts = database.get_all_prompts()
        if not prompts:
            self._combo.addItem("(暂无记录)")
            self._combo.setItemData(0, "", Qt.UserRole)
            return

        self._combo.addItem("复制最近提示词...")
        self._combo.setItemData(0, "", Qt.UserRole)
        for p in prompts[:20]:
            title = p.get("title") or p["original_text"].replace("\n", " ")[:30]
            text = p.get("optimized_text") or p["original_text"]
            self._combo.addItem(f"  {title}", text)
            idx = self._combo.count() - 1
            self._combo.setItemData(idx, text, Qt.ToolTipRole)
        self._combo.setCurrentIndex(0)

    def _on_item_selected(self, index):
        text = self._combo.itemData(index, Qt.UserRole)
        if text:
            QApplication.clipboard().setText(text)
        self._combo.setCurrentIndex(0)

    def eventFilter(self, obj, event):
        """Forward mouse events from child widgets for drag support."""
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Global position relative to this floating window
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        elif event.type() == QEvent.MouseMove:
            if event.buttons() & Qt.LeftButton and self._drag_pos is not None:
                self.move(event.globalPos() - self._drag_pos)
                return True
        elif event.type() == QEvent.MouseButtonRelease:
            self._drag_pos = None
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def show_and_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.top() + 20
        self.move(x, y)
        self.show()

    def _on_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_SIZE}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
        """)
        menu.addAction("打开主窗口").triggered.connect(self.show_main_requested.emit)
        menu.addSeparator()
        menu.addAction("退出").triggered.connect(QApplication.instance().quit)
        menu.exec_(QCursor.pos())
