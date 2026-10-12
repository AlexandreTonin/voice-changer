from pynput import keyboard
from PySide6.QtCore import QObject, Signal

MODIFIERS = {"ctrl": "<ctrl>", "alt": "<alt>", "shift": "<shift>", "meta": "<cmd>"}


def from_key_sequence(text):
    keys = []
    for part in text.split("+"):
        lower = part.lower()
        if lower in MODIFIERS:
            keys.append(MODIFIERS[lower])
        elif len(part) == 1:
            keys.append(lower)
        else:
            keys.append(f"<{lower}>")
    combo = "+".join(keys)
    keyboard.HotKey.parse(combo)
    return combo


def to_key_sequence(combo):
    names = {v: k.capitalize() for k, v in MODIFIERS.items()}
    return "+".join(names.get(k, k.strip("<>").upper()) for k in combo.split("+"))


class Hotkey(QObject):
    triggered = Signal()

    def __init__(self):
        super().__init__()
        self._listener = None

    def set(self, combo):
        self.stop()
        self._listener = keyboard.GlobalHotKeys({combo: self.triggered.emit})
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
