import ctypes
import json
import os
import signal
import subprocess
import time

VIRTUAL_SINK = "vc_sink"
VIRTUAL_MIC = "vc_mic"
PR_SET_PDEATHSIG = 1


def _die_with_parent():
    ctypes.CDLL("libc.so.6").prctl(PR_SET_PDEATHSIG, signal.SIGTERM)


def _dump():
    result = subprocess.run(["pw-dump"], capture_output=True, text=True, check=True)
    return json.JSONDecoder().raw_decode(result.stdout.lstrip())[0]


def _props(objects, kind):
    return [
        (o["id"], o["info"]["props"])
        for o in objects
        if o.get("type") == f"PipeWire:Interface:{kind}"
    ]


def _devices(media_class, exclude):
    return [
        (p["node.name"], p.get("node.description", p["node.name"]))
        for _, p in _props(_dump(), "Node")
        if p.get("media.class") == media_class and p.get("node.name") != exclude
    ]


def list_sources():
    return _devices("Audio/Source", VIRTUAL_MIC)


def list_sinks():
    return _devices("Audio/Sink", VIRTUAL_SINK)


def _loopback(name, capture_props, playback_props):
    return subprocess.Popen(
        [
            "pw-loopback",
            "-n",
            name,
            f"--capture-props={capture_props}",
            f"--playback-props={playback_props}",
        ],
        stdout=subprocess.DEVNULL,
        preexec_fn=_die_with_parent,
    )


def _target(node):
    return f"target.object={node}" if node else ""


def _wait_node(name, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if any(p.get("node.name") == name for _, p in _props(_dump(), "Node")):
            return
        time.sleep(0.1)
    raise RuntimeError(f"PipeWire node {name} did not show up")


def start_virtual_mic():
    process = _loopback(
        "voice-changer",
        f'media.class=Audio/Sink node.name={VIRTUAL_SINK} node.description="VoiceChanger Sink" audio.position=[MONO]',
        f'media.class=Audio/Source node.name={VIRTUAL_MIC} node.description="VoiceChanger Mic" audio.position=[MONO]',
    )
    _wait_node(VIRTUAL_SINK)
    return process


def start_passthrough(source):
    return _loopback("vc-passthrough", _target(source), _target(VIRTUAL_SINK))


def start_monitor(sink):
    return _loopback(
        "vc-monitor",
        f"{_target(VIRTUAL_SINK)} stream.capture.sink=true node.passive=true",
        _target(sink),
    )


def play_file(path, target, volume):
    decoder = subprocess.Popen(
        ["ffmpeg", "-loglevel", "error", "-i", str(path), "-f", "s16le", "-ac", "2", "-ar", "48000", "-"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        preexec_fn=_die_with_parent,
    )
    player = subprocess.Popen(
        [
            "pw-cat", "--playback", "--format", "s16", "--rate", "48000", "--channels", "2",
            "--volume", str(volume), *(["--target", target] if target else []), "-",
        ],
        stdin=decoder.stdout,
        preexec_fn=_die_with_parent,
    )
    decoder.stdout.close()
    return [decoder, player]


def stop(process):
    if process and process.poll() is None:
        process.terminate()
        process.wait(timeout=5)


def _own_streams():
    objects = _dump()
    pid = str(os.getpid())
    clients = {
        i for i, p in _props(objects, "Client") if str(p.get("application.process.id")) == pid
    }
    return {
        p["media.class"]: i
        for i, p in _props(objects, "Node")
        if p.get("client.id") in clients
    }


def _set_target(node_id, target):
    command = ["pw-metadata", str(node_id), "target.object", target] if target else [
        "pw-metadata", "-d", str(node_id), "target.object"
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, check=True)


def wait_own_streams(timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        streams = _own_streams()
        if {"Stream/Input/Audio", "Stream/Output/Audio"} <= streams.keys():
            return streams
        time.sleep(0.2)
    raise RuntimeError("Audio streams did not show up in PipeWire")


def route_input(streams, source):
    _set_target(streams["Stream/Input/Audio"], source)


def route_output_to_virtual_mic(streams):
    _set_target(streams["Stream/Output/Audio"], VIRTUAL_SINK)
