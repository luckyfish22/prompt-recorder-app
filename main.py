import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt
from src.ui.floating_window import FloatingWindow
from src.ui.main_window import MainWindow


def _create_tray_icon():
    """Generate a simple tray icon (orange circle)."""
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#D97757"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(4, 4, size - 8, size - 8)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "P")
    painter.end()

    return QIcon(pixmap)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Prompt Recorder")
    app.setQuitOnLastWindowClosed(False)

    tray = QSystemTrayIcon()
    tray.setIcon(_create_tray_icon())
    tray.setToolTip("Prompt Recorder")

    # Tray context menu
    tray_menu = QMenu()
    tray_menu.setStyleSheet("""
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #E8E4DF;
            border-radius: 4px;
            padding: 4px 0px;
            color: #1A1A1A;
            font-size: 14px;
        }
        QMenu::item { padding: 6px 24px; }
        QMenu::item:selected { background-color: #F5F2EF; }
    """)
    open_action = tray_menu.addAction("打开主窗口")
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction("退出")
    tray.setContextMenu(tray_menu)

    # Create windows
    floating = FloatingWindow()
    window = MainWindow(floating_window=floating)

    # Tray click → restore
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            window.restore()
    tray.activated.connect(on_tray_activated)

    # Menu actions
    open_action.triggered.connect(window.restore)
    quit_action.triggered.connect(app.quit)

    # Floating window connections
    floating.show_main_requested.connect(window.restore)

    # Show
    tray.show()
    floating.show_and_position()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
