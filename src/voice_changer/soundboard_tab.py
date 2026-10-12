from pathlib import Path

from PySide6.QtCore import QFileSystemWatcher, Qt, QUrl, Signal
from PySide6.QtGui import QCursor, QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from voice_changer import soundboard
from voice_changer.config import AUDIO_FILTER, SOUNDS_DIR
COLUMNS = 3


class SoundboardTab(QWidget):
    play_requested = Signal(str)
    stop_requested = Signal()
    volume_changed = Signal(int)

    def __init__(self, volume):
        super().__init__()
        SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
        self._watcher = QFileSystemWatcher([str(SOUNDS_DIR)], self)
        self._watcher.directoryChanged.connect(self.refresh)
        layout = QVBoxLayout(self)
        layout.addLayout(self._build_toolbar())
        layout.addLayout(self._build_volume(volume))
        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setAlignment(Qt.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._grid_widget)
        layout.addWidget(scroll)
        layout.addWidget(QLabel("Right-click a sound to delete it"))
        self.refresh()

    def _build_toolbar(self):
        layout = QHBoxLayout()
        for label, slot in (
            ("Add sounds…", self._add),
            ("Open folder", self._open_folder),
            ("Stop", self.stop_requested.emit),
        ):
            button = QPushButton(label)
            button.clicked.connect(slot)
            layout.addWidget(button)
        return layout

    def _build_volume(self, volume):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Volume"))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(volume)
        slider.valueChanged.connect(self.volume_changed.emit)
        layout.addWidget(slider)
        return layout

    def refresh(self):
        while item := self._grid.takeAt(0):
            item.widget().deleteLater()
        for index, name in enumerate(soundboard.list_sounds()):
            self._grid.addWidget(self._sound_button(name), index // COLUMNS, index % COLUMNS)

    def _sound_button(self, name):
        button = QPushButton(Path(name).stem)
        button.setToolTip(name)
        button.setMinimumHeight(48)
        button.clicked.connect(lambda: self.play_requested.emit(name))
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(lambda _: self._show_menu(button, name))
        return button

    def _show_menu(self, button, name):
        menu = QMenu(button)
        menu.addAction("Delete").triggered.connect(lambda: self._delete(name))
        menu.exec(QCursor.pos())

    def _add(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Add sounds", "", AUDIO_FILTER)
        if files:
            soundboard.add_sounds(files)
            self.refresh()

    def _delete(self, name):
        if QMessageBox.question(self, "Delete sound", f"Delete '{name}'?") == QMessageBox.Yes:
            soundboard.delete_sound(name)
            self.refresh()

    def _open_folder(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(SOUNDS_DIR)))
