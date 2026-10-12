from PySide6.QtCore import Signal
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from voice_changer import voices
from voice_changer.config import AUDIO_FILTER
from voice_changer.hotkey import from_key_sequence, to_key_sequence
from voice_changer.soundboard_tab import SoundboardTab


class ManagerWindow(QWidget):
    train_requested = Signal(str, list, int)
    cancel_requested = Signal()
    voice_renamed = Signal(str, str)
    voice_deleted = Signal(str)
    hotkey_changed = Signal(str)

    def __init__(self, hotkey, sound_volume):
        super().__init__()
        self.setWindowTitle("Voice Changer")
        self.setMinimumWidth(460)
        self._files = []
        self.soundboard = SoundboardTab(sound_volume)
        tabs = QTabWidget()
        tabs.addTab(self._build_voices_tab(hotkey), "Voices")
        tabs.addTab(self.soundboard, "Soundboard")
        QVBoxLayout(self).addWidget(tabs)
        self.refresh_voices()

    def _build_voices_tab(self, hotkey):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._build_voices())
        layout.addWidget(self._build_training())
        layout.addWidget(self._build_hotkey(hotkey))
        return page

    def _build_voices(self):
        box = QGroupBox("Voices")
        layout = QVBoxLayout(box)
        self._list = QListWidget()
        layout.addWidget(self._list)
        buttons = QHBoxLayout()
        rename = QPushButton("Rename…")
        rename.clicked.connect(self._rename)
        delete = QPushButton("Delete")
        delete.clicked.connect(self._delete)
        buttons.addWidget(rename)
        buttons.addWidget(delete)
        layout.addLayout(buttons)
        return box

    def _build_training(self):
        box = QGroupBox("Create voice")
        form = QFormLayout(box)
        self._name = QLineEdit()
        self._name.setPlaceholderText("letters, numbers, - or _")
        form.addRow("Name", self._name)
        pick = QPushButton("Choose audio files…")
        pick.clicked.connect(self._pick_files)
        self._files_label = QLabel("No files selected")
        form.addRow(pick, self._files_label)
        self._epochs = QSpinBox()
        self._epochs.setRange(10, 2000)
        self._epochs.setValue(300)
        form.addRow("Epochs", self._epochs)
        self._progress = QProgressBar()
        self._status = QLabel("Tip: 10–30 min of clean speech gives the best results")
        self._status.setWordWrap(True)
        form.addRow(self._progress)
        form.addRow(self._status)
        buttons = QHBoxLayout()
        self._train = QPushButton("Train")
        self._train.clicked.connect(self._start_training)
        self._cancel = QPushButton("Cancel")
        self._cancel.setEnabled(False)
        self._cancel.clicked.connect(self.cancel_requested.emit)
        buttons.addWidget(self._train)
        buttons.addWidget(self._cancel)
        form.addRow(buttons)
        return box

    def _build_hotkey(self, hotkey):
        box = QGroupBox("Toggle hotkey")
        layout = QHBoxLayout(box)
        self._hotkey = QKeySequenceEdit(QKeySequence(to_key_sequence(hotkey)))
        self._hotkey.setMaximumSequenceLength(1)
        save = QPushButton("Save")
        save.clicked.connect(self._save_hotkey)
        layout.addWidget(self._hotkey)
        layout.addWidget(save)
        return box

    def refresh_voices(self):
        self._list.clear()
        self._list.addItems(voices.list_voices())

    def set_training(self, running):
        self._train.setEnabled(not running)
        self._cancel.setEnabled(running)
        if running:
            self._progress.setValue(0)

    def show_progress(self, percent, text):
        self._progress.setValue(percent)
        self._status.setText(text)

    def show_result(self, message):
        self._status.setText(message)
        self.refresh_voices()

    def _selected(self):
        item = self._list.currentItem()
        return item.text() if item else None

    def _pick_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Choose audio files", "", AUDIO_FILTER)
        if files:
            self._files = files
            self._files_label.setText(f"{len(files)} file(s) selected")

    def _validate_new_name(self, name):
        if not voices.is_valid_name(name):
            return "Use only letters, numbers, - or _ (max 40)."
        if name in voices.list_voices():
            return f"Voice '{name}' already exists."
        return None

    def _start_training(self):
        name = self._name.text().strip()
        error = self._validate_new_name(name) or (None if self._files else "Choose audio files.")
        if error:
            QMessageBox.warning(self, "Voice Manager", error)
            return
        self.train_requested.emit(name, self._files, self._epochs.value())

    def _rename(self):
        old = self._selected()
        if not old:
            return
        new, ok = QInputDialog.getText(self, "Rename voice", "New name", text=old)
        new = new.strip()
        if not ok or new == old:
            return
        error = self._validate_new_name(new)
        if error:
            QMessageBox.warning(self, "Voice Manager", error)
            return
        self.voice_renamed.emit(old, new)
        self.refresh_voices()

    def _delete(self):
        name = self._selected()
        if name and QMessageBox.question(self, "Delete voice", f"Delete '{name}'?") == QMessageBox.Yes:
            self.voice_deleted.emit(name)
            self.refresh_voices()

    def _save_hotkey(self):
        sequence = self._hotkey.keySequence().toString()
        try:
            self.hotkey_changed.emit(from_key_sequence(sequence))
            self._status.setText(f"Hotkey saved: {sequence}")
        except ValueError:
            QMessageBox.warning(self, "Voice Manager", f"Invalid hotkey: {sequence or '(empty)'}")
