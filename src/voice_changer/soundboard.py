import shutil

from voice_changer import pipewire
from voice_changer.config import AUDIO_EXTENSIONS, SOUNDS_DIR


def list_sounds():
    if not SOUNDS_DIR.exists():
        return []
    return sorted(
        p.name for p in SOUNDS_DIR.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    )


def add_sounds(files):
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for file in files:
        shutil.copy(file, SOUNDS_DIR)


def delete_sound(name):
    (SOUNDS_DIR / name).unlink(missing_ok=True)


class Player:
    def __init__(self):
        self._processes = []

    def play(self, name, volume, local):
        self.stop()
        path = SOUNDS_DIR / name
        self._processes = pipewire.play_file(path, pipewire.VIRTUAL_SINK, volume)
        if local:
            self._processes += pipewire.play_file(path, None, volume)

    def stop(self):
        for process in self._processes:
            pipewire.stop(process)
        self._processes = []
