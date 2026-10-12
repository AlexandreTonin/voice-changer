import os
import re
import shutil
import signal
import subprocess
import sys
import threading

from PySide6.QtCore import QObject, Signal

from voice_changer.config import APPLIO_DIR, DATASETS_DIR, ROOT, TRAINING_DIR, applio_env

EPOCH_PATTERN = re.compile(r"\| epoch=(\d+) \| step=\d+ \| (?!batch=)")


def copy_dataset(name, files):
    dataset = DATASETS_DIR / name
    shutil.rmtree(dataset, ignore_errors=True)
    dataset.mkdir(parents=True)
    for file in files:
        shutil.copy(file, dataset)
    return dataset


class Trainer(QObject):
    progress = Signal(int, str)
    finished = Signal(bool, str, str)

    def __init__(self):
        super().__init__()
        self._process = None

    @property
    def running(self):
        return self._process is not None

    def start(self, name, files, epochs):
        dataset = copy_dataset(name, files)
        self._process = subprocess.Popen(
            [sys.executable, "-u", "-m", "voice_changer.train_job", name, str(dataset), str(epochs)],
            cwd=APPLIO_DIR,
            env={**os.environ, **applio_env(), "PYTHONPATH": str(ROOT / "src")},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        threading.Thread(target=self._watch, args=(name, epochs), daemon=True).start()

    def cancel(self):
        process = self._process
        if process:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def _watch(self, name, epochs):
        stage = ""
        for line in self._process.stdout:
            if line.startswith("STAGE "):
                stage = line[6:].strip()
                self.progress.emit(0, stage)
            elif match := EPOCH_PATTERN.search(line):
                epoch = int(match.group(1))
                self.progress.emit(epoch * 100 // epochs, f"{stage} {epoch}/{epochs}")
        code = self._process.wait()
        self._process = None
        if code == 0:
            self.finished.emit(True, name, f"Voice '{name}' is ready")
        else:
            shutil.rmtree(TRAINING_DIR / name, ignore_errors=True)
            self.finished.emit(False, name, f"Training '{name}' failed or was cancelled")
