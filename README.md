# Voice Changer

Local, real-time AI voice changer for Ubuntu, controlled from the tray. Train a voice from audio files (RVC v2 through [Applio](https://github.com/IAHispano/Applio)) and use it as your microphone in Discord or any other app.

## Requirements

- Ubuntu 24.04 (X11 session) with PipeWire
- NVIDIA GPU with CUDA (tested on an RTX 4060 8GB)
- [uv](https://docs.astral.sh/uv/)

## Install

```sh
./install.sh
```

Installs the apt packages it needs (`ffmpeg libportaudio2 libxcb-cursor0 pipewire-bin`), clones Applio at a pinned commit into `vendor/`, creates `.venv`, downloads the base models (~5 GB in total) and adds a "Voice Changer" launcher.

## Usage

```sh
./run.sh
```

1. Tray → **Open Voice Changer…** → **Voices** tab → enter a name, choose audio files, then click **Train**. Use 10–30 min of clean speech with no music or noise. 300 epochs take about 30–60 min. Voice conversion pauses while training runs.
2. Tray → **Voice** → pick the new voice. Left-click the tray icon or press the hotkey (default `Ctrl+Alt+V`) to turn it on or off.
3. In Discord, set the input device to **VoiceChanger Mic**. Turn off Krisp noise suppression and echo cancellation, because they distort the converted voice.

When the voice changer is off, VoiceChanger Mic passes your normal voice through. Use the **Monitor** menu to hear the output in your headphones.

## Soundboard

Open the **Soundboard** tab in the window, or use the **Soundboard** menu in the tray. Click a sound to play it into VoiceChanger Mic. You also hear it on your default output, or through the Monitor when that is on. Playing a new sound stops the current one. Add sounds with **Add sounds…**, or drop audio files into `data/sounds/`. Right-click a sound to delete it. The volume slider applies to every sound.

Tray icon colors: green = on, gray = off, orange = loading or training, red = error.

## Data

Everything lives in `data/` (git-ignored): `config.json`, `voices/<name>/` (model, index and pitch), `datasets/<name>/` (copies of the uploaded audio) and `sounds/` (soundboard files).

## Tests

```sh
PYTHONPATH=src .venv/bin/python tests/test_hotkey.py
```
