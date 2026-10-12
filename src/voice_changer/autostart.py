from pathlib import Path

from voice_changer.config import ROOT

DESKTOP_FILE = Path.home() / ".config" / "autostart" / "voice-changer.desktop"

ENTRY = f"""[Desktop Entry]
Type=Application
Name=Voice Changer
Exec={ROOT / "run.sh"}
Icon=audio-input-microphone
X-GNOME-Autostart-enabled=true
"""


def is_enabled():
    return DESKTOP_FILE.exists()


def set_enabled(enabled):
    if enabled:
        DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)
        DESKTOP_FILE.write_text(ENTRY)
    else:
        DESKTOP_FILE.unlink(missing_ok=True)
