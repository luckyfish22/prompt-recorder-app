from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QComboBox, QPushButton,
                                 QApplication, QSizePolicy, QMenu, QLineEdit,
                                 QLabel, QFrame, QVBoxLayout, QWidgetAction)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QThread, QPoint
import math
from PyQt5.QtGui import QMouseEvent, QCursor, QPainter, QPen, QColor, QPainterPath
from src.db import database
from src.ui.theme import COLORS, FONT_FLOAT
from src.config_loader import config
from src.api.deepseek_client import DeepSeekClient

TRANSLATION_PROMPT = """You are a Chinese-English translator.
- If the input is Chinese, translate to natural English.
- If the input is English, translate to natural Chinese.
- Return ONLY the translation, no explanations, no quotes, no prefixes."""

COMMAND_EXPLAIN_PROMPT = """You are a technical assistant. Explain the given CLI command, Python function/class/module, or programming keyword.

- Explain its **name origin** (etymology, abbreviation, naming background)
- Briefly describe **what it does**
- Respond in Chinese
- Keep it concise

Format:
名称来源：…
功能：…

Return ONLY the final answer, no prefixes or meta-commentary."""

def _make_translate_icon(size=28):
    """Draw a translate icon: two overlapping rounded rects."""
    from PyQt5.QtGui import QPixmap, QIcon
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    m = 2
    w = size - 2 * m
    half = w * 3 // 4
    off = w // 4
    # Left block
    painter.setBrush(QColor(COLORS["primary"]))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(m, m + off, half, half, 4, 4)
    # Right block (slightly offset)
    c2 = QColor(COLORS["primary"])
    c2.setAlpha(160)
    painter.setBrush(c2)
    painter.drawRoundedRect(m + off, m, half, half, 4, 4)
    painter.end()
    return QIcon(pix)

def _make_command_icon(size=28):
    """Draw a command-line icon: >_ symbol."""
    from PyQt5.QtGui import QPixmap, QIcon, QFont
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QColor(COLORS["primary"]))
    font = QFont("Consolas", 16)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignCenter, ">_")
    painter.end()
    return QIcon(pix)



class _ModeToggle(QPushButton):
    """Toggle button that draws a square with a diagonal slash."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(28, 28)
        self.setCursor(Qt.PointingHandCursor)
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        s = 4
        w = self.width() - 2 * s
        h = self.height() - 2 * s
        color = QColor(COLORS["primary"] if self._active else COLORS["text_secondary"])
        pen = QPen(color)
        pen.setWidthF(1.8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(s, s, w, h, 4, 4)
        pad = 5
        painter.drawLine(s + w - pad, s + pad, s + pad, s + h - pad)


class _TranslationWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, text: str, client: DeepSeekClient, system_prompt: str = TRANSLATION_PROMPT):
        super().__init__()
        self._text = text
        self._client = client
        self._system_prompt = system_prompt

    def run(self):
        try:
            result = self._client.chat(self._system_prompt, self._text, temperature=0.3)
            self.finished.emit(result.strip())
        except Exception:
            pass


class FloatingWindow(QWidget):
    show_main_requested = pyqtSignal()
    folder_selected = pyqtSignal(object)  # folder_id or None (All)

    def __init__(self):
        super().__init__(flags=Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self._drag_pos = None
        self._query_mode = None  # None, "translate", "explain"
        self._trans_timer = QTimer(self)
        self._trans_timer.setSingleShot(True)
        self._trans_timer.timeout.connect(self._do_translate)
        self._cmd_timer = QTimer(self)
        self._cmd_timer.setSingleShot(True)
        self._cmd_timer.timeout.connect(self._do_explain)
        self._trans_worker = None
        # Pre-init to avoid AttributeError in eventFilter during _init_ui
        self._trans_input = None
        self._cmd_input = None
        self._client = DeepSeekClient(config.api_key, config.model)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        self.setFixedHeight(52)
        self.setMinimumWidth(340)
        self.resize(420, 52)
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

        # Mode toggle button — square with diagonal slash
        self._mode_btn = _ModeToggle()
        self._mode_btn.setToolTip("<span style='font-size:18px'>Query: translate / explain commands</span>")
        self._mode_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 5px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_bg']};
            }}
        """)
        self._mode_btn.clicked.connect(self._show_mode_menu)
        layout.addWidget(self._mode_btn)

        # Translation input (hidden in normal mode)
        self._trans_input = QLineEdit()
        self._trans_input.setPlaceholderText("Type to translate…")
        self._trans_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: {FONT_FLOAT}px;
                padding: 2px 4px;
            }}
            QLineEdit:focus {{
                border: none;
                background-color: {COLORS['accent_bg']};
                border-radius: 4px;
            }}
        """)
        self._trans_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self._trans_input.customContextMenuRequested.connect(self._on_trans_context_menu)
        self._trans_input.textChanged.connect(self._on_trans_text_changed)
        self._trans_input.installEventFilter(self)
        self._trans_input.hide()
        layout.addWidget(self._trans_input, stretch=1)

        # Command/function explain input (hidden in normal mode)
        self._cmd_input = QLineEdit()
        self._cmd_input.setPlaceholderText("Type a command or function name to explain…")
        self._cmd_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: {FONT_FLOAT}px;
                padding: 2px 4px;
            }}
            QLineEdit:focus {{
                border: none;
                background-color: {COLORS['accent_bg']};
                border-radius: 4px;
            }}
        """)
        self._cmd_input.setContextMenuPolicy(Qt.CustomContextMenu)
        self._cmd_input.customContextMenuRequested.connect(self._on_trans_context_menu)
        self._cmd_input.textChanged.connect(self._on_cmd_text_changed)
        self._cmd_input.installEventFilter(self)
        self._cmd_input.hide()
        layout.addWidget(self._cmd_input, stretch=1)

        # Translation result popup (dropdown below input)
        self._trans_popup = QFrame()
        self._trans_popup.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self._trans_popup.setMinimumWidth(300)
        self._trans_popup.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)
        popup_layout = QVBoxLayout(self._trans_popup)
        popup_layout.setContentsMargins(12, 10, 12, 10)
        self._trans_label = QLabel("")
        self._trans_label.setWordWrap(True)
        self._trans_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: {FONT_FLOAT}px; "
            f"border: none; background: transparent; "
            f"padding: 4px 2px; line-height: 1.5;"
        )
        self._trans_label.setCursor(Qt.PointingHandCursor)
        self._trans_label.mousePressEvent = lambda e: self._copy_translation()
        popup_layout.addWidget(self._trans_label)
        self._trans_popup.hide()

        self._combo = QComboBox()
        self._combo.setCursor(Qt.PointingHandCursor)
        self._combo.setMaximumWidth(220)
        self._combo.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._combo.setStyleSheet(f"""
            QComboBox {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};

                font-size: {FONT_FLOAT}px;
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
                font-size: {FONT_FLOAT}px;
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

        # Star button — Edge-style favorites dropdown
        self._star_btn = QPushButton("★")
        self._star_btn.setFixedSize(36, 36)
        self._star_btn.setCursor(Qt.PointingHandCursor)
        self._star_btn.setToolTip("Favorites")
        self._star_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 13px;
                font-size: 20px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
            }}
        """)
        self._star_btn.clicked.connect(self._show_favorites_menu)
        layout.addWidget(self._star_btn)

        self._main_btn = QPushButton("+")
        self._main_btn.setFixedSize(36, 36)
        self._main_btn.setCursor(Qt.PointingHandCursor)
        self._main_btn.setToolTip("Open main window")
        self._main_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
                border: none;
                border-radius: 13px;
                font-size: 24px;
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
            escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            self._combo.setItemData(idx, f"<span style='font-size:18px'>{escaped}</span>", Qt.ToolTipRole)
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

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._query_mode is not None:
            self._trans_popup.hide()

    def show_and_position(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - self.width() - 20
        y = screen.top() + 20
        self.move(x, y)
        self.show()

    # --- Query modes (translate / explain) ---

    def _show_mode_menu(self):
        """Show dropdown menu, or exit to normal mode if already in a query mode."""
        if self._query_mode is not None:
            self._exit_query_mode()
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px;
            }}
        """)

        icon_size = 24

        is_translate = self._query_mode == "translate"
        is_explain = self._query_mode == "explain"

        def _make_icon_action(menu, icon_func, active):
            pix = icon_func(icon_size).pixmap(icon_size, icon_size)
            w = QWidget()
            w.setFixedSize(icon_size + 14, icon_size + 12)
            if active:
                w.setStyleSheet(f"background: {COLORS['accent_bg']}; border-radius: 4px;")
            lay = QHBoxLayout(w)
            lay.setContentsMargins(0, 0, 0, 0)
            lbl = QLabel()
            lbl.setPixmap(pix)
            lbl.setFixedSize(icon_size, icon_size)
            lay.addWidget(lbl, alignment=Qt.AlignCenter)
            act = QWidgetAction(menu)
            act.setDefaultWidget(w)
            menu.addAction(act)
            return act

        trans_action = _make_icon_action(menu, _make_translate_icon, is_translate)
        cmd_action = _make_icon_action(menu, _make_command_icon, is_explain)

        action = menu.exec_(self._mode_btn.mapToGlobal(
            self._mode_btn.rect().bottomLeft() + QPoint(0, 4)))

        if action == trans_action:
            if is_translate:
                self._exit_query_mode()
            else:
                self._enter_mode("translate")
        elif action == cmd_action:
            if is_explain:
                self._exit_query_mode()
            else:
                self._enter_mode("explain")

    def _enter_mode(self, mode: str):
        self._query_mode = mode
        self._mode_btn.set_active(True)
        self._combo.hide()
        self._star_btn.hide()

        if mode == "translate":
            self._cmd_input.hide()
            self._trans_input.show()
            self._trans_input.setFocus()
        else:  # explain
            self._trans_input.hide()
            self._cmd_input.show()
            self._cmd_input.setFocus()

        self.resize(460, 52)

    def _exit_query_mode(self):
        self._query_mode = None
        self._mode_btn.set_active(False)
        self._trans_input.hide()
        self._cmd_input.hide()
        self._trans_popup.hide()
        self._trans_input.clear()
        self._cmd_input.clear()
        self._combo.show()
        self._star_btn.show()
        self.resize(420, 52)

    def _on_trans_text_changed(self, text: str):
        if not text.strip():
            self._trans_popup.hide()
            return
        self._trans_timer.stop()
        self._trans_timer.start(500)

    def _do_translate(self):
        text = self._trans_input.text().strip()
        if not text or not self._client.is_configured:
            return
        self._trans_worker = _TranslationWorker(text, self._client, TRANSLATION_PROMPT)
        self._trans_worker.finished.connect(self._on_translation_result)
        self._trans_worker.start()

    def _on_cmd_text_changed(self, text: str):
        if not text.strip():
            self._trans_popup.hide()
            return
        self._cmd_timer.stop()
        self._cmd_timer.start(500)

    def _do_explain(self):
        text = self._cmd_input.text().strip()
        if not text or not self._client.is_configured:
            return
        self._trans_worker = _TranslationWorker(text, self._client, COMMAND_EXPLAIN_PROMPT)
        self._trans_worker.finished.connect(self._on_translation_result)
        self._trans_worker.start()

    def _on_translation_result(self, text: str):
        if not text:
            return
        self._trans_label.setText(text)
        # Position popup below the floating window, clamped to its width
        max_w = self.width() - 20  # 10px margin each side
        self._trans_popup.setMaximumWidth(max_w)
        self._trans_popup.adjustSize()
        w = min(self._trans_popup.width(), max_w)
        pos = self.mapToGlobal(QPoint(10, self.height() + 4))
        self._trans_popup.move(pos)
        self._trans_popup.resize(w, self._trans_popup.height())
        self._trans_popup.show()

    def _on_trans_context_menu(self, pos):
        menu = self._trans_input.createStandardContextMenu()
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: 14px;
            }}
            QMenu::item {{ padding: 4px 20px; }}
            QMenu::item:selected {{ background-color: {COLORS['accent_bg']}; }}
            QMenu::separator {{ height: 1px; background: {COLORS['border']}; margin: 3px 10px; }}
        """)
        menu.exec_(self._trans_input.mapToGlobal(pos))

    def _copy_translation(self):
        text = self._trans_label.text()
        if text:
            QApplication.clipboard().setText(text)

    def _show_favorites_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_FLOAT}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
        """)

        # "All" submenu
        all_menu = menu.addMenu("  All")
        all_menu.addAction("Open in main window").triggered.connect(
            lambda: self._on_folder_clicked(None))
        all_menu.addSeparator()
        self._fill_prompt_items(all_menu, None)

        folders = database.get_all_folders()
        if folders:
            menu.addSeparator()
            self._build_folder_favorites(menu, folders, None)

        menu.exec_(self._star_btn.mapToGlobal(self._star_btn.rect().bottomLeft()))

    def _build_folder_favorites(self, parent_menu, folders, parent_id):
        """Recursively build folder submenus for the favorites menu."""
        children = [f for f in folders if f.get("parent_id") == parent_id]
        for f in children:
            has_children = any(sf.get("parent_id") == f["id"] for sf in folders)
            folder_menu = parent_menu.addMenu(f"  {f['name']}")
            folder_menu.addAction("Open in main window").triggered.connect(
                lambda checked, fid=f["id"]: self._on_folder_clicked(fid))
            folder_menu.addSeparator()
            if has_children:
                self._build_folder_favorites(folder_menu, folders, f["id"])
            self._fill_prompt_items(folder_menu, f["id"])

    def _fill_prompt_items(self, menu, folder_id):
        prompts = database.get_all_prompts(folder_id=folder_id)
        if not prompts:
            empty = menu.addAction("  (empty)")
            empty.setEnabled(False)
            return
        for p in prompts[:30]:
            title = p.get("title") or p["original_text"].replace("\n", " ")[:25]
            text = p.get("optimized_text") or p["original_text"]
            action = menu.addAction(f"  {title}")
            action.triggered.connect(lambda checked, t=text: self._copy_prompt(t))

    def _copy_prompt(self, text: str):
        QApplication.clipboard().setText(text)

    def _on_folder_clicked(self, folder_id):
        self.folder_selected.emit(folder_id)
        self.show_main_requested.emit()

    def _on_context_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_FLOAT}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
        """)
        menu.addAction("Open Main Window").triggered.connect(self.show_main_requested.emit)
        menu.addAction("Hide Window").triggered.connect(self.hide)
        menu.addSeparator()
        menu.addAction("Exit").triggered.connect(QApplication.instance().quit)
        menu.exec_(QCursor.pos())

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonDblClick:
            if obj is self._trans_input or obj is self._cmd_input:
                obj.paste()
                return True
        return super().eventFilter(obj, event)
