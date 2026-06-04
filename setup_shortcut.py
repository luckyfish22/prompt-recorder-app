"""Generate an icon file and create a desktop shortcut for Prompt Recorder."""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Generate icon ---
ico_path = os.path.join(PROJECT_DIR, "prompt_recorder.ico")
img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# White circle background
circle_margin = 16
draw.ellipse([circle_margin, circle_margin, 256 - circle_margin, 256 - circle_margin],
             fill="white", outline="#D97757", width=4)

# Try Georgia italic bold, fall back gracefully
font = None
for name in ["Georgia", "georgia.ttf", "Times New Roman", "C:\\Windows\\Fonts\\georgiai.ttf"]:
    try:
        font = ImageFont.truetype(name, 130)
        break
    except (IOError, OSError):
        pass
if font is None:
    font = ImageFont.load_default()

# Draw "P" centered
bbox = draw.textbbox((0, 0), "P", font=font)
tw = bbox[2] - bbox[0]
th = bbox[3] - bbox[1]
x = (256 - tw) / 2 - bbox[0]
y = (256 - th) / 2 - bbox[1] - 8
draw.text((x, y), "P", fill="#D97757", font=font)

img.save(ico_path, format="ICO", sizes=[(256, 256)])
print(f"Icon saved to: {ico_path}")

# --- Create desktop shortcut ---
desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
shortcut_path = os.path.join(desktop, "Prompt Recorder.lnk")
bat_path = os.path.join(PROJECT_DIR, "run.bat")

ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
$Shortcut.TargetPath = 'cmd.exe'
$Shortcut.Arguments = '/c "{bat_path}"'
$Shortcut.IconLocation = '{ico_path}'
$Shortcut.WorkingDirectory = '{PROJECT_DIR}'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
Write-Host 'Shortcut created:' '{shortcut_path}'
"""
subprocess.run(["powershell", "-Command", ps], capture_output=False)
print(f"Desktop shortcut created: {shortcut_path}")
