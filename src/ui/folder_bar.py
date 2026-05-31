from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QLabel,
                                 QScrollArea, QMenu, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QCursor
from src.db import database
from src.ui.theme import COLORS, FONT_CAPTION

FOLDER_MIME = "application/x-promptrecorder-prompt-id"


class _FolderTab(QWidget):
    clicked = pyqtSignal(object)  # emits folder dict or None for "All"
    renamed = pyqtSignal(object, str)
    deleted = pyqtSignal(object)
    drop_received = pyqtSignal(object)

    def __init__(self, folder: dict | None):
        super().__init__()
        self._folder = folder  # None = "All"
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu)
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(0)

        name = self._folder["name"] if self._folder else "All"
        self._label = QLabel(name)
        self._label.setStyleSheet(self._tab_style(False))
        layout.addWidget(self._label)

    def _tab_style(self, selected):
        color = COLORS["primary"] if selected else COLORS["text_secondary"]
        weight = "bold" if selected else "normal"
        underline = f"border-bottom: 2px solid {COLORS['primary']};" if selected else "border-bottom: 2px solid transparent;"
        return (
            f"color: {color}; font-size: {FONT_CAPTION}px; font-weight: {weight}; "
            f"{underline} background: transparent; padding: 2px 2px;"
        )

    def set_selected(self, selected: bool):
        self._selected = selected
        self._label.setStyleSheet(self._tab_style(selected))

    @property
    def folder(self):
        return self._folder

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._folder)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self._folder is not None:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
            dlg = QDialog(self)
            dlg.setWindowTitle("Rename Folder")
            dlg.setMinimumWidth(300)
            dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")
            layout = QVBoxLayout(dlg)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(12)
            label = QLabel("New name:")
            label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
            layout.addWidget(label)
            edit = QLineEdit()
            edit.setText(self._folder["name"])
            edit.selectAll()
            layout.addWidget(edit)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            btn_box.accepted.connect(dlg.accept)
            btn_box.rejected.connect(dlg.reject)
            layout.addWidget(btn_box)
            if dlg.exec_() == QDialog.Accepted and edit.text().strip() and edit.text().strip() != self._folder["name"]:
                self.renamed.emit(self._folder, edit.text().strip())

    def _on_context_menu(self, pos):
        if self._folder is None:
            return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 4px 0px;
                color: {COLORS['text_primary']};
                font-size: {FONT_CAPTION}px;
            }}
            QMenu::item {{ padding: 6px 24px; }}
            QMenu::item:selected {{ background-color: {COLORS['accent_bg']}; }}
        """)
        menu.addAction("Rename").triggered.connect(
            lambda: self.mouseDoubleClickEvent(None))
        menu.addAction("Delete").triggered.connect(
            lambda: self.deleted.emit(self._folder))
        menu.exec_(QCursor.pos())

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(FOLDER_MIME):
            event.acceptProposedAction()
            self.setStyleSheet(
                f"background-color: {COLORS['accent_bg']}; border-radius: 6px;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("")
        if event.mimeData().hasFormat(FOLDER_MIME):
            prompt_id = int(event.mimeData().data(FOLDER_MIME).data().decode())
            target_id = self._folder["id"] if self._folder else None
            database.move_prompt_to_folder(prompt_id, target_id)
            self.drop_received.emit(self._folder)
            event.acceptProposedAction()


class FolderBar(QWidget):
    folder_changed = pyqtSignal(object)  # folder dict or None (All)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs: list[_FolderTab] = []
        self._current = None
        self.setAcceptDrops(True)
        self._init_ui()
        self._select_all()

    def _init_ui(self):
        self.setFixedHeight(38)
        self.setStyleSheet(f"background-color: {COLORS['surface']}; border-bottom: 1px solid {COLORS['border']};")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setFixedHeight(36)
        self._scroll.setWidgetResizable(True)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QHBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(4, 0, 4, 0)
        self._scroll_layout.setSpacing(2)

        # "All" tab
        all_tab = self._make_tab(None)
        self._scroll_layout.addWidget(all_tab)
        self._tabs.append(all_tab)

        # Custom folder tabs
        self._rebuild_tabs()

        self._scroll_layout.addStretch()
        self._scroll.setWidget(self._scroll_content)
        layout.addWidget(self._scroll, stretch=1)

        # "+" button
        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("<span style='font-size:16px'>New folder</span>")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 16px;
                font-size: 22px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
            }}
        """)
        add_btn.clicked.connect(self._add_folder)
        layout.addWidget(add_btn)

    def _make_tab(self, folder):
        tab = _FolderTab(folder)
        tab.clicked.connect(self._on_tab_clicked)
        tab.renamed.connect(self._on_rename)
        tab.deleted.connect(self._on_delete)
        tab.drop_received.connect(self._on_drop)
        return tab

    def _rebuild_tabs(self):
        # Remove all tabs except "All" (index 0)
        while self._scroll_layout.count() > 2:  # 0=All, 1=stretch
            item = self._scroll_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        self._tabs = [self._tabs[0]]  # keep All

        folders = database.get_all_folders()
        for f in folders:
            tab = self._make_tab(f)
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, tab)
            self._tabs.append(tab)

    def _on_tab_clicked(self, folder):
        self._select(folder)
        folder_id = folder["id"] if folder else None
        self.folder_changed.emit(folder_id)

    def _select(self, folder):
        self._current = folder
        for tab in self._tabs:
            tab.set_selected(tab.folder is folder)

    def _select_all(self):
        self._select(None)
        self.folder_changed.emit(None)

    def _add_folder(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
        dlg = QDialog(self)
        dlg.setWindowTitle("New Folder")
        dlg.setMinimumWidth(300)
        dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        label = QLabel("Folder name:")
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
        layout.addWidget(label)
        edit = QLineEdit()
        layout.addWidget(edit)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_() == QDialog.Accepted and edit.text().strip():
            database.add_folder(edit.text().strip())
            self._rebuild_tabs()

    def _on_rename(self, folder, new_name):
        database.rename_folder(folder["id"], new_name)
        self._rebuild_tabs()

    def _on_delete(self, folder):
        reply = QMessageBox.question(
            self, "Delete Folder",
            f'Delete "{folder["name"]}"?\nPrompts in this folder will return to "All".',
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            database.delete_folder(folder["id"])
            if self._current and self._current["id"] == folder["id"]:
                self._select_all()
            self._rebuild_tabs()
            self.folder_changed.emit(None)

    def _on_drop(self, folder):
        # Re-select current folder to refresh history
        if self._current:
            folder_id = self._current["id"] if self._current else None
        else:
            folder_id = None
        self.folder_changed.emit(folder_id)

    # Accept drops on the bar itself (between tabs)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(FOLDER_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat(FOLDER_MIME):
            prompt_id = int(event.mimeData().data(FOLDER_MIME).data().decode())
            # Dropped on bar itself → move to "All" (None)
            database.move_prompt_to_folder(prompt_id, None)
            folder_id = self._current["id"] if self._current else None
            self.folder_changed.emit(folder_id)
            event.acceptProposedAction()

    def _on_folder_reorder(self, src_folder_id: int, target_folder_id: int):
        """Move src folder right after target folder, then rebuild."""
        ids = [tab.folder["id"] for tab in self._tabs if tab.folder]
        if src_folder_id not in ids or target_folder_id not in ids:
            return
        ids.remove(src_folder_id)
        target_idx = ids.index(target_folder_id)
        ids.insert(target_idx + 1, src_folder_id)
        for pos, fid in enumerate(ids):
            database.update_folder_position(fid, pos)
        self._rebuild_tabs()
        self.folders_reordered.emit()

    def select_folder(self, folder_id):
        """Select a folder tab by ID. None selects 'All'."""
        if folder_id is None:
            self._select_all()
            return
        for tab in self._tabs:
            if tab.folder and tab.folder["id"] == folder_id:
                self._select(tab.folder)
                self.folder_changed.emit(folder_id)
                return
        self._select_all()

    @property
    def current_folder_id(self):
        if self._current and isinstance(self._current, dict):
            return self._current["id"]
        return None
