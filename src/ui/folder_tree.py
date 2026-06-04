"""Folder tree sidebar — hierarchical folder navigation with tree widget."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QMenu, QMessageBox,
                             QDialog, QLabel, QLineEdit, QDialogButtonBox,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QTimer
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QCursor, QFont
from src.db import database
from src.ui.theme import COLORS, FONT_CAPTION

FOLDER_MIME = "application/x-promptrecorder-prompt-id"


class FolderTree(QWidget):
    """Tree sidebar for hierarchical folder navigation."""

    folder_changed = pyqtSignal(object)  # emits folder_id (int) or None for "All"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_folder_id = None
        self._expanded_ids = set()
        self._init_ui()
        self._rebuild_tree()

    # ── UI construction ──────────────────────────────────────────

    def _init_ui(self):
        self.setMinimumWidth(160)
        self.setMaximumWidth(300)
        self.setStyleSheet(f"background-color: {COLORS['bg']};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(6)

        # Header: label + "+" button
        header = QHBoxLayout()
        header.setContentsMargins(4, 0, 4, 0)
        header.setSpacing(4)

        title = QLabel("Folders")
        title.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px; "
            f"font-weight: bold; border: none; background: transparent;"
        )
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(26, 26)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setToolTip("<span style='font-size:16px'>New root folder</span>")
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                border-radius: 13px;
                font-size: 20px;
                font-weight: bold;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
            }}
        """)
        add_btn.clicked.connect(self._add_root_folder)
        header.addWidget(add_btn)
        layout.addLayout(header)

        # Tree widget
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(16)
        self._tree.setAnimated(True)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemClicked.connect(self._on_item_clicked)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.itemExpanded.connect(self._on_item_expanded)
        self._tree.itemCollapsed.connect(self._on_item_collapsed)
        self._tree.setDragDropMode(QAbstractItemView.DropOnly)
        self._tree.setAcceptDrops(True)
        self._tree.viewport().setAcceptDrops(True)
        self._tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                color: {COLORS['text_primary']};
                font-size: {FONT_CAPTION}px;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 3px 4px;
                border-radius: 4px;
                min-height: 26px;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS['accent_bg']};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['accent_bg']};
                color: {COLORS['primary']};
            }}
        """)
        layout.addWidget(self._tree, stretch=1)

    # ── Tree building ────────────────────────────────────────────

    def _rebuild_tree(self):
        """Rebuild the full tree while preserving expand/selection state."""
        # Save current state
        prev_expanded = set(self._expanded_ids)
        prev_select = self._current_folder_id

        self._tree.blockSignals(True)
        self._tree.clear()

        # "All" item (always first)
        all_item = QTreeWidgetItem(["All"])
        all_item.setData(0, Qt.UserRole, None)  # None = "All"
        bold = QFont()
        bold.setBold(True)
        all_item.setFont(0, bold)
        all_item.setExpanded(True)
        self._tree.addTopLevelItem(all_item)

        # Build folder tree recursively
        folders = database.get_all_folders()
        # Build lookup: {id: folder_dict}
        folder_map = {f["id"]: f for f in folders}
        # Group by parent_id
        children_by_parent = {}  # parent_id -> [folder_dict, ...]
        for f in folders:
            pid = f.get("parent_id")
            children_by_parent.setdefault(pid, []).append(f)

        def _add_children(parent_item, parent_id):
            for f in children_by_parent.get(parent_id, []):
                item = QTreeWidgetItem([f["name"]])
                item.setData(0, Qt.UserRole, f)
                item.setToolTip(0, f["name"])
                if parent_item is None:
                    self._tree.addTopLevelItem(item)
                else:
                    parent_item.addChild(item)
                # Restore expand state
                if f["id"] in prev_expanded:
                    item.setExpanded(True)
                # Restore selection
                if f["id"] == prev_select:
                    self._tree.setCurrentItem(item)
                # Recurse
                if f["id"] in children_by_parent:
                    _add_children(item, f["id"])

        _add_children(None, None)

        # Restore "All" selection
        if prev_select is None:
            self._tree.setCurrentItem(all_item)

        self._tree.blockSignals(False)

    # ── Signal handlers ──────────────────────────────────────────

    def _on_item_clicked(self, item, col):
        folder_data = item.data(0, Qt.UserRole)
        if folder_data is None:
            # "All"
            self._current_folder_id = None
            self.folder_changed.emit(None)
        elif isinstance(folder_data, dict):
            fid = folder_data["id"]
            if fid != self._current_folder_id:
                self._current_folder_id = fid
                self.folder_changed.emit(fid)

    def _on_item_double_clicked(self, item, col):
        folder_data = item.data(0, Qt.UserRole)
        if folder_data and isinstance(folder_data, dict):
            self._rename_folder(folder_data)

    def _on_item_expanded(self, item):
        folder_data = item.data(0, Qt.UserRole)
        if folder_data and isinstance(folder_data, dict):
            self._expanded_ids.add(folder_data["id"])

    def _on_item_collapsed(self, item):
        folder_data = item.data(0, Qt.UserRole)
        if folder_data and isinstance(folder_data, dict):
            self._expanded_ids.discard(folder_data["id"])

    def _on_context_menu(self, pos):
        item = self._tree.itemAt(pos)
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
            QMenu::separator {{ height: 1px; background: {COLORS['border']}; margin: 3px 10px; }}
        """)

        if item is None:
            # Clicked on empty area — allow adding root folder
            menu.addAction("New Folder").triggered.connect(self._add_root_folder)
        else:
            folder_data = item.data(0, Qt.UserRole)
            if folder_data is None:
                # "All" item
                menu.addAction("New Folder").triggered.connect(self._add_root_folder)
            else:
                # Folder item
                menu.addAction("New Sub-folder").triggered.connect(
                    lambda: self._add_subfolder(folder_data))
                menu.addAction("Rename").triggered.connect(
                    lambda: self._rename_folder(folder_data))
                menu.addSeparator()
                menu.addAction("Delete").triggered.connect(
                    lambda: self._delete_folder(folder_data))

        menu.exec_(QCursor.pos())

    # ── Folder operations ────────────────────────────────────────

    def _add_root_folder(self):
        name = self._prompt_folder_name("New Folder", "Folder name:")
        if name:
            new_id = database.add_folder(name, parent_id=None)
            self._rebuild_tree()
            self._select_folder(new_id)

    def _add_subfolder(self, parent_data):
        name = self._prompt_folder_name("New Sub-folder", "Sub-folder name:")
        if name:
            new_id = database.add_folder(name, parent_id=parent_data["id"])
            # Ensure parent is expanded
            self._expanded_ids.add(parent_data["id"])
            self._rebuild_tree()
            self._select_folder(new_id)

    def _rename_folder(self, folder_data):
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
        edit.setText(folder_data["name"])
        edit.selectAll()
        layout.addWidget(edit)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_() == QDialog.Accepted and edit.text().strip() and edit.text().strip() != folder_data["name"]:
            database.rename_folder(folder_data["id"], edit.text().strip())
            self._rebuild_tree()
            self.folder_changed.emit(self._current_folder_id)

    def _delete_folder(self, folder_data):
        # Count descendants for warning
        sub_ids = database.get_subfolder_ids(folder_data["id"])
        descendant_count = len(sub_ids) - 1  # minus self

        msg = f'Delete "{folder_data["name"]}"?'
        if descendant_count > 0:
            msg += f'\n\nThis folder has {descendant_count} sub-folder(s), which will also be deleted.'
        msg += '\nPrompts in these folders will return to "All".'

        reply = QMessageBox.warning(
            self, "Delete Folder", msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            fid = folder_data["id"]
            database.delete_folder(fid)
            # If deleted folder or its descendants were selected, reset to All
            if self._current_folder_id and self._current_folder_id in sub_ids:
                self._current_folder_id = None
            self._expanded_ids.discard(fid)
            self._rebuild_tree()
            self.folder_changed.emit(self._current_folder_id)

    def _prompt_folder_name(self, title, label_text):
        """Show a dialog asking for a folder name. Returns str or None."""
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumWidth(300)
        dlg.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg']}; }}")
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        label = QLabel(label_text)
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: {FONT_CAPTION}px;")
        layout.addWidget(label)
        edit = QLineEdit()
        layout.addWidget(edit)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dlg.accept)
        btn_box.rejected.connect(dlg.reject)
        layout.addWidget(btn_box)
        if dlg.exec_() == QDialog.Accepted and edit.text().strip():
            return edit.text().strip()
        return None

    # ── Drag-drop support ────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat(FOLDER_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(FOLDER_MIME):
            item = self._tree.itemAt(self._tree.viewport().mapFrom(
                self.mapToGlobal(event.pos())))
            if item:
                self._tree.setCurrentItem(item)
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasFormat(FOLDER_MIME):
            prompt_id = int(event.mimeData().data(FOLDER_MIME).data().decode())
            item = self._tree.itemAt(self._tree.viewport().mapFrom(
                self.mapToGlobal(event.pos())))
            folder_data = item.data(0, Qt.UserRole) if item else None
            if folder_data and isinstance(folder_data, dict):
                target_id = folder_data["id"]
            else:
                target_id = None  # Dropped on "All" or empty area
            database.move_prompt_to_folder(prompt_id, target_id)
            # Refresh history by re-emitting current folder
            self.folder_changed.emit(self._current_folder_id)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    # ── Public API ───────────────────────────────────────────────

    def select_folder(self, folder_id):
        """Programmatically select a folder by ID. None selects 'All'."""
        self._current_folder_id = folder_id
        self._select_folder(folder_id)

    def _select_folder(self, folder_id):
        """Find item by folder_id and select it."""
        if folder_id is None:
            item = self._tree.topLevelItem(0)  # "All" is always first
            if item:
                self._tree.setCurrentItem(item)
            return

        def _find(parent, target):
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.UserRole)
                if data and isinstance(data, dict) and data["id"] == target:
                    self._tree.setCurrentItem(child)
                    return True
                if _find(child, target):
                    return True
            return False

        # Search from "All" item
        all_item = self._tree.topLevelItem(0)
        if all_item:
            if not _find(all_item, folder_id):
                # Search from root level (invisible root)
                for i in range(self._tree.topLevelItemCount()):
                    if _find(self._tree.topLevelItem(i), folder_id):
                        return

    @property
    def current_folder_id(self):
        return self._current_folder_id
