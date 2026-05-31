from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget,
                                 QListWidgetItem, QLabel, QHBoxLayout, QMenu,
                                 QAction, QApplication, QAbstractItemView,
                                 QInputDialog, QDialog, QPushButton, QTextEdit,
                                 QDialogButtonBox)
from PyQt5.QtCore import pyqtSignal, Qt, QMimeData, QPoint, QItemSelectionModel, QTimer
from PyQt5.QtGui import QCursor, QDrag
from src.db import database
from src.ui.theme import COLORS, FONT_BODY, FONT_CAPTION, FONT_MICRO
from src.ui.folder_bar import FOLDER_MIME

REORDER_MIME = "application/x-promptrecorder-reorder"


class _GripLabel(QLabel):
    """Drag handle for reordering prompts within the list."""

    drag_started = pyqtSignal(int)  # prompt_id

    def __init__(self, prompt_id: int):
        super().__init__("⠁⠁")
        self._prompt_id = prompt_id
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)
        self.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 14px; "
            f"background: transparent; border: none; padding: 0px 4px;"
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self._drag_start_pos is not None:
            if (event.pos() - self._drag_start_pos).manhattanLength() >= 8:
                self.setCursor(Qt.OpenHandCursor)
                mime = QMimeData()
                mime.setData(REORDER_MIME, str(self._prompt_id).encode())
                drag = QDrag(self)
                drag.setMimeData(mime)
                drag.exec_(Qt.MoveAction)
                self._drag_start_pos = None
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_pos = None
        self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)


class _DragListWidget(QListWidget):
    """QListWidget that supports drag-out to folders and drag-reorder within."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setAcceptDrops(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDropIndicatorShown(True)
        self._reorder_drop_index = -1

    def startDrag(self, actions):
        item = self.currentItem()
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return
        mime = QMimeData()
        mime.setData(FOLDER_MIME, str(data["id"]).encode())
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setHotSpot(self.viewport().mapFromGlobal(QCursor.pos()))
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(REORDER_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(REORDER_MIME):
            event.acceptProposedAction()
            item = self.itemAt(event.pos())
            if item:
                row = self.row(item)
                rect = self.visualItemRect(item)
                if event.pos().y() > rect.center().y():
                    row += 1
                self._reorder_drop_index = row
            else:
                self._reorder_drop_index = self.count()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(REORDER_MIME):
            prompt_id = int(event.mimeData().data(REORDER_MIME).data().decode())
            target = self._reorder_drop_index
            self._reorder_drop_index = -1
            self.parent()._on_reorder(prompt_id, target)
            event.acceptProposedAction()
            QTimer.singleShot(0, self.clearSelection)
        else:
            super().dropEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.clearSelection()


class HistoryPanel(QWidget):
    prompt_selected = pyqtSignal(dict)
    prompt_deleted = pyqtSignal()
    analysis_requested = pyqtSignal(dict)
    prompt_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folder_id = None
        self._init_ui()
        self.refresh()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search...")
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._list = _DragListWidget(self)
        self._list.setCursor(Qt.PointingHandCursor)
        self._list.setContextMenuPolicy(Qt.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemPressed.connect(self._on_item_pressed)
        layout.addWidget(self._list, stretch=1)

    def refresh(self, search=None, folder_id=None):
        self._list.clear()
        self._list.clearSelection()
        prompts = database.get_all_prompts(search, folder_id)
        for p in prompts:
            widget = self._build_item_widget(p)
            item = QListWidgetItem()
            hint = widget.sizeHint()
            hint.setHeight(hint.height() + 6)
            item.setSizeHint(hint)
            item.setData(Qt.UserRole, p)
            self._list.addItem(item)
            self._list.setItemWidget(item, widget)
        self._list.clearSelection()

    def _build_item_widget(self, prompt: dict):
        w = QWidget()
        w.setAttribute(Qt.WA_TranslucentBackground)
        w.setStyleSheet("background: transparent;")

        # Tooltip: show full prompt text (HTML for larger font)
        text = prompt["original_text"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        optimized = prompt.get("optimized_text", "")
        if optimized:
            opt = optimized.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            text += f"<br><br><b>--- Optimized ---</b><br>{opt}"
        w.setToolTip(f"<div style='font-size:18px'>{text}</div>")

        outer = QHBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        # Drag grip handle
        grip = _GripLabel(prompt["id"])
        outer.addWidget(grip, alignment=Qt.AlignTop)

        inner = QVBoxLayout()
        inner.setContentsMargins(0, 10, 12, 10)
        inner.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.setContentsMargins(0, 0, 0, 0)

        title_text = prompt.get("title") or prompt["original_text"].replace("\n", " ")[:30]
        title_label = QLabel(title_text)
        title_label.setStyleSheet(
            f"color: {COLORS['text_primary']}; font-size: {FONT_BODY}px; font-weight: bold; "
            f"background: transparent; border: none;"
        )
        title_label.setWordWrap(False)
        top.addWidget(title_label, stretch=1)

        folder_name = prompt.get("folder_name", "")
        if folder_name:
            folder_label = QLabel(f" {folder_name} ")
            folder_label.setMinimumHeight(FONT_CAPTION + 12)
            folder_label.setStyleSheet(
                f"background: {COLORS['accent_bg']}; color: {COLORS['primary']}; "
                f"font-size: {FONT_CAPTION}px; border: none; "
                f"border-radius: {FONT_CAPTION // 2 + 6}px; padding: 0px 4px;"
            )
            top.addWidget(folder_label, alignment=Qt.AlignVCenter)

        inner.addLayout(top)

        time_label = QLabel(prompt.get("created_at", ""))
        time_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_MICRO}px; "
            f"background: transparent; border: none; padding: 0px;"
        )
        inner.addWidget(time_label)

        outer.addLayout(inner, stretch=1)
        return w

    def _on_search(self, text):
        self.refresh(text if text else None, self._folder_id)

    def _on_item_pressed(self, item):
        data = item.data(Qt.UserRole)
        if not data:
            return
        text = data.get("optimized_text") or data["original_text"]
        QApplication.clipboard().setText(text)
        self.prompt_selected.emit(data)

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_BODY}px;
            }}
            QMenu::item {{
                padding: 6px 24px;
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent_bg']};
            }}
        """)

        analyze_action = menu.addAction("AI Analysis")
        analyze_action.triggered.connect(lambda: self.analysis_requested.emit(data))

        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self._edit_prompt(data))

        # Move to Folder submenu
        move_menu = menu.addMenu("Move to Folder")
        move_menu.setStyleSheet(menu.styleSheet())
        folders = database.get_all_folders()
        current_folder = data.get("folder_id")
        all_action = move_menu.addAction("All (no folder)")
        all_action.triggered.connect(lambda: self._move_to_folder(data, None))
        if current_folder is None:
            all_action.setEnabled(False)
        if folders:
            move_menu.addSeparator()
            for f in folders:
                f_action = move_menu.addAction(f"  {f['name']}")
                f_action.triggered.connect(lambda checked, fid=f["id"]: self._move_to_folder(data, fid))
                if current_folder == f["id"]:
                    f_action.setEnabled(False)

        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self._delete_prompt(data))

        menu.exec_(QCursor.pos())

    def _edit_prompt(self, data: dict):
        dlg = QDialog(self)
        dlg.setWindowTitle("Edit Prompt")
        dlg.setMinimumSize(500, 350)
        dlg.resize(550, 400)
        dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title_label = QLabel("Title:")
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
        layout.addWidget(title_label)

        title_edit = QLineEdit()
        title_edit.setText(data.get("title") or data["original_text"].replace("\n", " ")[:30])
        layout.addWidget(title_edit)

        text_label = QLabel("Prompt text:")
        text_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
        layout.addWidget(text_label)

        text_edit = QTextEdit()
        text_edit.setPlainText(data["original_text"])
        layout.addWidget(text_edit, stretch=1)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)

        if dlg.exec_() == QDialog.Accepted:
            new_title = title_edit.text().strip()
            new_text = text_edit.toPlainText().strip()
            if new_title and new_text:
                database.update_prompt(
                    prompt_id=data["id"],
                    title=new_title,
                    original_text=new_text,
                )
                self.refresh(folder_id=self._folder_id)
                self.prompt_changed.emit()

    def _move_to_folder(self, data: dict, folder_id):
        database.move_prompt_to_folder(data["id"], folder_id)
        self.refresh(folder_id=self._folder_id)
        self.prompt_changed.emit()

    def _delete_prompt(self, data: dict):
        database.delete_prompt(data["id"])
        self.refresh(folder_id=self._folder_id)
        self.prompt_deleted.emit()

    def _on_reorder(self, prompt_id: int, target_index: int):
        """Reassign positions after a drag-reorder, then rebuild list."""
        ids = []
        source_index = -1
        for i in range(self._list.count()):
            d = self._list.item(i).data(Qt.UserRole)
            if d:
                ids.append(d["id"])
                if d["id"] == prompt_id:
                    source_index = i

        if prompt_id not in ids:
            return
        ids.remove(prompt_id)

        # When source is above target, removing source shifts target left by 1
        if source_index < target_index:
            target_index -= 1
        target_index = max(0, min(target_index, len(ids)))
        ids.insert(target_index, prompt_id)

        for pos, pid in enumerate(ids):
            database.update_prompt_position(pid, pos)

        self.refresh(folder_id=self._folder_id)
        self.prompt_changed.emit()
