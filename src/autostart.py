"""Manage Windows startup shortcut for auto-launch."""
import os
import sys

STARTUP_DIR = os.path.join(
    os.getenv("APPDATA", ""),
    r"Microsoft\Windows\Start Menu\Programs\Startup"
)
SHORTCUT_NAME = "PromptRecorder.lnk"


def _get_shortcut_path():
    return os.path.join(STARTUP_DIR, SHORTCUT_NAME)


def _get_python_path():
    return sys.executable


def _get_app_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))


def create_shortcut():
    """Create a .vbs launcher in the Startup folder to avoid console window."""
    if not os.path.exists(STARTUP_DIR):
        os.makedirs(STARTUP_DIR, exist_ok=True)

    vbs_path = os.path.join(STARTUP_DIR, "PromptRecorder.vbs")
    pythonw = _get_python_path().replace("python.exe", "pythonw.exe")
    app_path = _get_app_path()
    working_dir = os.path.dirname(app_path)

    vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{working_dir}"
WshShell.Run """{pythonw}"" ""{app_path}""", 0, False
'''
    with open(vbs_path, "w") as f:
        f.write(vbs_content)


def remove_shortcut():
    vbs_path = os.path.join(STARTUP_DIR, "PromptRecorder.vbs")
    lnk_path = os.path.join(STARTUP_DIR, "PromptRecorder.lnk")
    for p in (vbs_path, lnk_path):
        if os.path.exists(p):
            os.remove(p)


def is_autostart_enabled():
    vbs_path = os.path.join(STARTUP_DIR, "PromptRecorder.vbs")
    lnk_path = os.path.join(STARTUP_DIR, "PromptRecorder.lnk")
    return os.path.exists(vbs_path) or os.path.exists(lnk_path)


def set_autostart(enable: bool):
    if enable:
        create_shortcut()
    else:
        remove_shortcut()
