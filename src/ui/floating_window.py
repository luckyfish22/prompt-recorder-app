from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QPushButton,
                                 QApplication, QSizePolicy, QMenu)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
import math
from PyQt5.QtGui import QMouseEvent, QCursor, QPainter, QPen, QColor, QPainterPath
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
        self.setFixedHeight(46)
        self.setMinimumWidth(300)
        self.resize(380, 46)
        self.setAttribute(Qt.WA_Hover, True)
        self.setObjectName("floatingWindow")
        self.setStyleSheet(f"""
            #floatingWindow {{
                background-color: {COLORS['surface']};
                border-radius: 10px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        self._combo = QComboBox()
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.setMaximumWidth(220)
        self._combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
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
        layout.addWidget(self._combo)

        layout.addStretch()

        self._main_btn = QPushButton("+")
        self._main_btn.setFixedSize(28, 28)
        self._main_btn.setCursor(Qt.PointingHandCursor)
        self._main_btn.setToolTip("Open main window")
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
            self._combo.addItem("(No records)")
            self._combo.setItemData(0, "", Qt.UserRole)
            return

        self._combo.addItem("Copy recent prompts...")
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

    def _paint_blob_path(self, w, h, inset, r, variation, seed):
        """Generate an organic paint-spread path by perturbing rounded-rect perimeter."""
        path = QPainterPath()
        n = 60  # samples per edge
        # Build perimeter points with normal offsets from centroid
        pts = self._sample_organic_outline(w, h, inset, r, variation, seed, n)
        if not pts:
            return path
        # Smooth the points into a path
        path.moveTo(pts[0][0], pts[0][1])
        for i in range(1, len(pts)):
            x0, y0 = pts[i - 1]
            x1, y1 = pts[i]
            # Use quadTo with midpoint as control for smooth curve
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            path.quadTo(x0, y0, mx, my)
        # Close the loop
        x0, y0 = pts[-1]
        x1, y1 = pts[0]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        path.quadTo(x0, y0, mx, my)
        path.closeSubpath()
        return path

    def _sample_organic_outline(self, w, h, inset, r, variation, seed, n):
        """Sample n points along each of the 4 sides + 4 corners, perturbed outward."""
        pts = []
        total_len = 2 * (w - 2 * r) + 2 * (h - 2 * r) + 2 * math.pi * r
        if total_len <= 0:
            return [(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset)]
        # We'll walk the perimeter in small steps
        steps = n * 4 + n // 2  # total sample count
        for i in range(steps):
            t = i / steps  # 0..1 around perimeter
            # Get base position on rounded rectangle
            bx, by, nx, ny = self._point_on_rounded_rect(w, h, inset, r, t)
            # Perturb along normal
            # Use multiple sine waves for organic feel
            freq1 = 5.3 + seed * 1.7
            freq2 = 11.7 + seed * 2.3
            freq3 = 23.1 + seed * 0.9
            phase1 = seed * 0.7
            phase2 = seed * 1.3 + 1.2
            phase3 = seed * 2.1 + 3.8
            wave = (math.sin(t * math.pi * 2 * freq1 + phase1) * 1.0 +
                    math.sin(t * math.pi * 2 * freq2 + phase2) * 0.6 +
                    math.sin(t * math.pi * 2 * freq3 + phase3) * 0.35)
            offset = wave * variation
            px = bx + nx * offset
            py = by + ny * offset
            pts.append((px, py))
        return pts

    def _point_on_rounded_rect(self, w, h, inset, r, t):
        """Get (x, y, nx, ny) at parametric t (0..1) on a rounded rectangle perimeter."""
        iw = w - inset * 2  # inner width
        ih = h - inset * 2  # inner height
        cr = max(1, r - inset * 0.5)  # corner radius for this layer

        # Segment lengths
        top_len = iw - 2 * cr
        right_len = ih - 2 * cr
        corner_len = (math.pi / 2) * cr
        total = 2 * top_len + 2 * right_len + 4 * corner_len
        if total <= 0:
            return w / 2, h / 2, 0, -1

        dist = t * total

        # Top edge (left to right)
        seg = top_len
        if dist < seg:
            x = inset + cr + dist
            y = inset
            return x, y, 0, -1

        # Top-right corner
        dist -= seg
        seg = corner_len
        if dist < seg:
            angle = (dist / corner_len) * (math.pi / 2)
            cx, cy = inset + iw - cr, inset + cr
            px = cx + cr * math.cos(-math.pi / 2 + angle)
            py = cy + cr * math.sin(-math.pi / 2 + angle)
            nx = math.cos(-math.pi / 2 + angle)
            ny = math.sin(-math.pi / 2 + angle)
            return px, py, nx, ny

        # Right edge
        dist -= seg
        seg = right_len
        if dist < seg:
            x = inset + iw
            y = inset + cr + dist
            return x, y, 1, 0

        # Bottom-right corner
        dist -= seg
        seg = corner_len
        if dist < seg:
            angle = (dist / corner_len) * (math.pi / 2)
            cx, cy = inset + iw - cr, inset + ih - cr
            px = cx + cr * math.cos(0 + angle)
            py = cy + cr * math.sin(0 + angle)
            nx = math.cos(0 + angle)
            ny = math.sin(0 + angle)
            return px, py, nx, ny

        # Bottom edge
        dist -= seg
        seg = top_len
        if dist < seg:
            x = inset + iw - cr - dist
            y = inset + ih
            return x, y, 0, 1

        # Bottom-left corner
        dist -= seg
        seg = corner_len
        if dist < seg:
            angle = (dist / corner_len) * (math.pi / 2)
            cx, cy = inset + cr, inset + ih - cr
            px = cx + cr * math.cos(math.pi / 2 + angle)
            py = cy + cr * math.sin(math.pi / 2 + angle)
            nx = math.cos(math.pi / 2 + angle)
            ny = math.sin(math.pi / 2 + angle)
            return px, py, nx, ny

        # Left edge
        dist -= seg
        seg = right_len
        if dist < seg:
            x = inset
            y = inset + ih - cr - dist
            return x, y, -1, 0

        # Top-left corner
        dist -= seg
        angle = min(1.0, dist / corner_len) * (math.pi / 2)
        cx, cy = inset + cr, inset + cr
        px = cx + cr * math.cos(math.pi + angle)
        py = cy + cr * math.sin(math.pi + angle)
        nx = math.cos(math.pi + angle)
        ny = math.sin(math.pi + angle)
        return px, py, nx, ny

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = 10
        primary = QColor(COLORS["primary"])
        # Deeper, more saturated orange — shift toward pure orange
        base = QColor(
            max(0, primary.red() - 10),
            primary.green() - 7,
            max(0, primary.blue() - 20)
        )

        layers = [
            (8, 10, 0.05, 12.0),
            (6, 8,  0.10, 9.0),
            (4, 6,  0.18, 6.0),
            (3, 4,  0.30, 4.0),
            (1, 2.5, 0.55, 2.5),
            (0, 2,   1.0,  0.0),
        ]

        painter.setBrush(Qt.NoBrush)
        for spread, width, alpha, variation in layers:
            c = QColor(base.red(), base.green(), base.blue(), int(255 * alpha))
            pen = QPen(c)
            pen.setWidthF(width)
            painter.setPen(pen)
            path = self._paint_blob_path(w, h, spread, r, variation, spread)
            painter.drawPath(path)

        # White fill
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(COLORS["surface"]))
        fill_inset = 9
        fill_path = QPainterPath()
        fill_path.addRoundedRect(fill_inset, fill_inset,
                                 w - fill_inset * 2, h - fill_inset * 2, 6, 6)
        painter.drawPath(fill_path)

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
        menu.addAction("Open Main Window").triggered.connect(self.show_main_requested.emit)
        menu.addSeparator()
        menu.addAction("Exit").triggered.connect(QApplication.instance().quit)
        menu.exec_(QCursor.pos())
