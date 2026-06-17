import sys
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtGui import QCursor
from src.ui.floating_window import FloatingWindow
from src.ui.main_window import MainWindow
from src.ui.theme import set_app_font
from src.config_loader import config

SERVER_NAME = "PromptRecorderSingleInstance"


def _create_tray_icon():
    """Generate a tray icon — artistic 'P' letter."""
    size = 32
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Artistic P
    font = QFont("Georgia", 18)
    font.setItalic(True)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor("#D97757"))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "P")
    painter.end()

    return QIcon(pixmap)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Prompt Recorder")
    app.setQuitOnLastWindowClosed(False)
    set_app_font(app, config.font_family)

    # Single-instance check
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(500):
        # Another instance is running — notify it and exit
        socket.disconnectFromServer()
        sys.exit(0)
    server = QLocalServer()
    server.listen(SERVER_NAME)

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
            font-size: 18px;
        }
        QMenu::item { padding: 6px 24px; }
        QMenu::item:selected { background-color: #F5F2EF; }
    """)
    def _restart():
        window.hide()
        floating.hide()
        tray.hide()
        os.execl(sys.executable, sys.executable, *sys.argv)

    open_action = tray_menu.addAction("Open Main Window")
    restart_action = tray_menu.addAction("Restart")
    restart_action.triggered.connect(_restart)
    tray_menu.addSeparator()
    quit_action = tray_menu.addAction("Exit")

    # Create windows first (needed by menu actions)
    floating = FloatingWindow()
    window = MainWindow(floating_window=floating)

    # Tray click → left=floating window, right=popup menu (auto-dismiss)
    def on_tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            floating.show()
            floating.raise_()
            floating.activateWindow()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            tray_menu.popup(QCursor.pos())
    tray.activated.connect(on_tray_activated)

    # Menu actions
    open_action.triggered.connect(window.restore)
    quit_action.triggered.connect(app.quit)

    # Floating window connections
    floating.show_main_requested.connect(window.restore)

    # When second instance tries to launch, bring windows to front
    def _on_second_instance():
        floating.show()
        floating.raise_()
        floating.activateWindow()
        window.restore()
    server.newConnection.connect(_on_second_instance)

    # Show
    tray.show()
    floating.show_and_position()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
