from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from voice_changer.config import LATENCY_PRESETS

PITCH_RANGE = range(-12, 13)
STATUS_COLORS = {
    "on": "#2ecc71",
    "off": "#7f8c8d",
    "loading": "#f39c12",
    "training": "#f39c12",
    "error": "#e74c3c",
}
STATUS_LABELS = {
    "on": "Voice changer: ON",
    "off": "Voice changer: OFF",
    "loading": "Loading voice…",
    "training": "Training… (passthrough)",
    "error": "Error loading voice",
}


def _icon(color):
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(6, 6, 52, 52)
    painter.end()
    return QIcon(pixmap)


class Tray(QObject):
    toggled = Signal()
    voice_selected = Signal(str)
    pitch_selected = Signal(int)
    latency_selected = Signal(str)
    input_selected = Signal(object)
    monitor_selected = Signal(object)
    autostart_toggled = Signal(bool)
    sound_selected = Signal(str)
    sound_stopped = Signal()
    manager_requested = Signal()
    quit_requested = Signal()

    def __init__(self, state_provider):
        super().__init__()
        self._state_provider = state_provider
        self._menu = QMenu()
        self._menu.aboutToShow.connect(self.refresh)
        self._icon = QSystemTrayIcon()
        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._on_activated)

    def show(self):
        self.refresh()
        self._icon.show()

    def refresh(self):
        state = self._state_provider()
        status = state["status"]
        self._icon.setIcon(_icon(STATUS_COLORS[status]))
        self._icon.setToolTip(STATUS_LABELS[status])
        self._build_menu(state)

    def notify(self, message):
        self._icon.showMessage("Voice Changer", message)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggled.emit()

    def _build_menu(self, state):
        menu = self._menu
        menu.clear()
        status = menu.addAction(STATUS_LABELS[state["status"]])
        status.setEnabled(False)
        toggle = menu.addAction("Disable" if state["enabled"] else "Enable")
        toggle.setEnabled(bool(state["voice"]) and state["status"] != "training")
        toggle.triggered.connect(self.toggled.emit)
        menu.addSeparator()
        self._add_choices(
            "Voice", [(v, v) for v in state["voices"]], state["voice"], self.voice_selected
        )
        pitch = self._add_choices(
            "Pitch", [(p, f"{p:+d}") for p in PITCH_RANGE], state["pitch"], self.pitch_selected
        )
        pitch.menuAction().setEnabled(bool(state["voice"]))
        self._add_choices(
            "Latency", [(k, f"{k} ({int(v * 1000)} ms)") for k, v in LATENCY_PRESETS.items()],
            state["latency"], self.latency_selected,
        )
        self._add_choices(
            "Input device", [(None, "System default"), *state["sources"]], state["input"],
            self.input_selected,
        )
        self._add_choices(
            "Monitor", [(None, "Off"), *state["sinks"]], state["monitor"], self.monitor_selected
        )
        self._build_soundboard(state["sounds"])
        menu.addSeparator()
        menu.addAction("Open Voice Changer…").triggered.connect(self.manager_requested.emit)
        autostart = menu.addAction("Start on login")
        autostart.setCheckable(True)
        autostart.setChecked(state["autostart"])
        autostart.toggled.connect(self.autostart_toggled.emit)
        menu.addAction("Quit").triggered.connect(self.quit_requested.emit)

    def _build_soundboard(self, sounds):
        submenu = self._menu.addMenu("Soundboard")
        for name in sounds:
            submenu.addAction(name).triggered.connect(lambda _=False, n=name: self.sound_selected.emit(n))
        if not sounds:
            submenu.addAction("(no sounds)").setEnabled(False)
        submenu.addSeparator()
        submenu.addAction("Stop").triggered.connect(self.sound_stopped.emit)

    def _add_choices(self, title, options, current, signal):
        submenu = self._menu.addMenu(title)
        group = QActionGroup(submenu)
        for value, label in options:
            action = QAction(label, group)
            action.setCheckable(True)
            action.setChecked(value == current)
            action.triggered.connect(lambda _=False, v=value: signal.emit(v))
            submenu.addAction(action)
        if not options:
            submenu.addAction("(none)").setEnabled(False)
        return submenu
