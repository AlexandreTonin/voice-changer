from PySide6.QtCore import QObject

from voice_changer import autostart, pipewire, soundboard, voices
from voice_changer.config import LATENCY_PRESETS, load_config, save_config
from voice_changer.engine import Engine
from voice_changer.hotkey import Hotkey
from voice_changer.manager_window import ManagerWindow
from voice_changer.trainer import Trainer
from voice_changer.tray import Tray


class App(QObject):
    def __init__(self, qt_app):
        super().__init__()
        self._qt_app = qt_app
        self._config = load_config()
        self._engine_state = "idle"
        self._manager = None
        self._monitor = None
        self._player = soundboard.Player()
        self._virtual_mic = pipewire.start_virtual_mic()

        self._engine = Engine()
        self._engine.state_changed.connect(self._on_engine_state)
        self._trainer = Trainer()
        self._trainer.progress.connect(self._on_train_progress)
        self._trainer.finished.connect(self._on_train_finished)
        self._hotkey = Hotkey()
        self._hotkey.triggered.connect(self._toggle)
        self._hotkey.set(self._config["hotkey"])
        self._tray = self._create_tray()

        self._engine.set_enabled(self._config["enabled"])
        self._engine.set_source(self._config["input"])
        self._apply_monitor()
        self._load_voice()
        self._tray.show()

    def _create_tray(self):
        tray = Tray(self._tray_state)
        tray.toggled.connect(self._toggle)
        tray.voice_selected.connect(self._select_voice)
        tray.pitch_selected.connect(self._select_pitch)
        tray.latency_selected.connect(self._select_latency)
        tray.input_selected.connect(self._select_input)
        tray.monitor_selected.connect(self._select_monitor)
        tray.sound_selected.connect(self._play_sound)
        tray.sound_stopped.connect(self._player.stop)
        tray.autostart_toggled.connect(autostart.set_enabled)
        tray.manager_requested.connect(self._open_manager)
        tray.quit_requested.connect(self._quit)
        return tray

    def _status(self):
        if self._trainer.running:
            return "training"
        if self._engine_state in ("loading", "error"):
            return self._engine_state
        return "on" if self._engine_state == "ready" and self._config["enabled"] else "off"

    def _tray_state(self):
        voice = self._config["voice"]
        return {
            "status": self._status(),
            "enabled": self._config["enabled"],
            "voices": voices.list_voices(),
            "voice": voice,
            "pitch": voices.get_pitch(voice) if voice else 0,
            "latency": self._config["latency"],
            "sources": pipewire.list_sources(),
            "input": self._config["input"],
            "sinks": pipewire.list_sinks(),
            "monitor": self._config["monitor"],
            "sounds": soundboard.list_sounds(),
            "autostart": autostart.is_enabled(),
        }

    def _update(self, **changes):
        self._config.update(changes)
        save_config(self._config)

    def _load_voice(self):
        voice = self._config["voice"]
        if voice not in voices.list_voices():
            self._update(voice=None)
            self._engine.unload()
            return
        self._engine.set_pitch(voices.get_pitch(voice))
        self._engine.load(*voices.model_paths(voice), LATENCY_PRESETS[self._config["latency"]])

    def _apply_monitor(self):
        pipewire.stop(self._monitor)
        sink = self._config["monitor"]
        self._monitor = pipewire.start_monitor(sink) if sink else None

    def _on_engine_state(self, state, message):
        self._engine_state = state
        if state == "error":
            self._tray.notify(f"Could not load voice: {message}")
        self._tray.refresh()

    def _toggle(self):
        if not self._config["voice"] or self._trainer.running:
            return
        self._update(enabled=not self._config["enabled"])
        self._engine.set_enabled(self._config["enabled"])
        self._tray.refresh()

    def _select_voice(self, voice):
        self._update(voice=voice)
        self._load_voice()

    def _select_pitch(self, pitch):
        voices.set_pitch(self._config["voice"], pitch)
        self._engine.set_pitch(pitch)

    def _select_latency(self, latency):
        self._update(latency=latency)
        if not self._trainer.running:
            self._load_voice()

    def _select_input(self, source):
        self._update(input=source)
        self._engine.set_source(source)

    def _select_monitor(self, sink):
        self._update(monitor=sink)
        self._apply_monitor()

    def _play_sound(self, name):
        self._player.play(name, self._config["sound_volume"] / 100, local=not self._config["monitor"])

    def _open_manager(self):
        if not self._manager:
            self._manager = ManagerWindow(self._config["hotkey"], self._config["sound_volume"])
            self._manager.soundboard.play_requested.connect(self._play_sound)
            self._manager.soundboard.stop_requested.connect(self._player.stop)
            self._manager.soundboard.volume_changed.connect(lambda v: self._update(sound_volume=v))
            self._manager.train_requested.connect(self._start_training)
            self._manager.cancel_requested.connect(self._trainer.cancel)
            self._manager.voice_renamed.connect(self._rename_voice)
            self._manager.voice_deleted.connect(self._delete_voice)
            self._manager.hotkey_changed.connect(self._change_hotkey)
        self._manager.show()
        self._manager.raise_()
        self._manager.activateWindow()

    def _start_training(self, name, files, epochs):
        try:
            self._trainer.start(name, files, epochs)
        except OSError as error:
            self._manager.show_result(f"Could not start training: {error}")
            return
        self._engine.unload()
        self._manager.set_training(True)
        self._tray.refresh()

    def _on_train_progress(self, percent, text):
        if self._manager:
            self._manager.show_progress(percent, text)

    def _on_train_finished(self, ok, name, message):
        if self._manager:
            self._manager.set_training(False)
            self._manager.show_result(message)
        self._tray.notify(message)
        if ok and not self._config["voice"]:
            self._update(voice=name)
        self._load_voice()

    def _rename_voice(self, old, new):
        voices.rename_voice(old, new)
        if self._config["voice"] == old:
            self._update(voice=new)
        self._tray.refresh()

    def _delete_voice(self, name):
        voices.delete_voice(name)
        if self._config["voice"] == name:
            self._update(voice=None, enabled=False)
            self._engine.set_enabled(False)
            self._load_voice()
        self._tray.refresh()

    def _change_hotkey(self, combo):
        self._update(hotkey=combo)
        self._hotkey.set(combo)

    def _quit(self):
        self._hotkey.stop()
        self._player.stop()
        self._trainer.cancel()
        self._engine.shutdown()
        pipewire.stop(self._monitor)
        pipewire.stop(self._virtual_mic)
        self._qt_app.quit()
