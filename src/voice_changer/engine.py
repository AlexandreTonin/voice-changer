import time
from concurrent.futures import ThreadPoolExecutor

import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from voice_changer import pipewire

SAMPLE_RATE = 48000
LOAD_TIMEOUT = 120


def _pipewire_device_index():
    return next(i for i, d in enumerate(sd.query_devices()) if d["name"] == "pipewire")


def _wait_ready(callbacks):
    deadline = time.monotonic() + LOAD_TIMEOUT
    while not callbacks.vc.ready:
        if time.monotonic() > deadline:
            raise RuntimeError("Voice model took too long to load")
        time.sleep(0.1)


class Engine(QObject):
    state_changed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._callbacks = None
        self._streams = None
        self._passthrough = None
        self._source = None
        self._enabled = False
        self._pitch = 0

    def set_enabled(self, enabled):
        self._enabled = enabled
        if self._callbacks:
            self._callbacks.pass_through = not enabled

    def set_pitch(self, pitch):
        self._pitch = pitch
        if self._callbacks:
            self._callbacks.audio.f0_up_key = pitch

    def set_source(self, source):
        self._source = source
        self._executor.submit(self._apply_source)

    def load(self, model, index, chunk):
        self._executor.submit(self._load, str(model), str(index), chunk)

    def unload(self):
        self._executor.submit(self._unload)

    def shutdown(self):
        self._executor.submit(self._teardown)
        self._executor.shutdown(wait=True)

    def _apply_source(self):
        if self._callbacks:
            pipewire.route_input(self._streams, self._source)
        else:
            self._start_passthrough()

    def _load(self, model, index, chunk):
        self._teardown()
        self.state_changed.emit("loading", "")
        try:
            self._start_engine(model, index, chunk)
            self.state_changed.emit("ready", "")
        except Exception as error:
            self._teardown()
            self._start_passthrough()
            self.state_changed.emit("error", str(error))

    def _start_engine(self, model, index, chunk):
        from rvc.realtime.callbacks import AudioCallbacks

        block = int(chunk * SAMPLE_RATE)
        callbacks = AudioCallbacks(
            pass_through=not self._enabled,
            block_frame=block,
            cross_fade_overlap_size=0.05,
            extra_convert_size=2.5,
            model_path=model,
            index_path=index,
            f0_method="rmvpe",
            embedder_model="contentvec",
            silent_threshold=-90,
            f0_up_key=self._pitch,
            index_rate=0.5,
            protect=0.5,
            output_audio_gain=0.0,
            audio_sample_rate=SAMPLE_RATE,
        )
        self._callbacks = callbacks
        _wait_ready(callbacks)
        device = _pipewire_device_index()
        callbacks.audio.run_audio_stream(
            block, device, device, None, 1, 1, 1, None, None, None, SAMPLE_RATE
        )
        self._streams = pipewire.wait_own_streams()
        pipewire.route_input(self._streams, self._source)
        pipewire.route_output_to_virtual_mic(self._streams)
        callbacks.audio.output_audio_gain = 1.0

    def _unload(self):
        self._teardown()
        self._start_passthrough()
        self.state_changed.emit("idle", "")

    def _start_passthrough(self):
        pipewire.stop(self._passthrough)
        self._passthrough = pipewire.start_passthrough(self._source)

    def _teardown(self):
        if self._callbacks:
            self._callbacks.audio.stop()
            self._callbacks.vc.stop()
            self._callbacks = None
            self._streams = None
        pipewire.stop(self._passthrough)
        self._passthrough = None
