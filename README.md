<div align="center">

# Voice Changer

Local, real-time AI voice changer for Ubuntu, controlled from the tray.
Train a voice from your own audio files and use it as your microphone in Discord or any other app.

![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04-E95420?logo=ubuntu&logoColor=white)
![Python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)
![CUDA](https://img.shields.io/badge/GPU-CUDA-76B900?logo=nvidia&logoColor=white)
![License](https://img.shields.io/github/license/AlexandreTonin/voice-changer)

[Requirements](#requirements) •
[Install](#install) •
[Usage](#usage) •
[Soundboard](#soundboard) •
[How it works](#how-it-works)

</div>

---

Voice conversion uses RVC v2 through [Applio](https://github.com/IAHispano/Applio). Everything runs locally on your GPU, with no account or upload.

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

The tray menu also has:

- **Pitch:** shifts the converted voice from -12 to +12 semitones. Saved per voice.
- **Latency:** Low (100 ms), Balanced (200 ms, default) or Quality (350 ms). Larger chunks sound better but delay your voice more.
- **Input device:** which microphone to convert. Defaults to the system one.
- **Start on login:** adds the app to `~/.config/autostart`.

Tray icon colors: green = on, gray = off, orange = loading or training, red = error.

## Soundboard

Open the **Soundboard** tab in the window, or use the **Soundboard** menu in the tray. Click a sound to play it into VoiceChanger Mic. You also hear it on your default output, or through the Monitor when that is on. Playing a new sound stops the current one. Add sounds with **Add sounds…**, or drop audio files into `data/sounds/`. Right-click a sound to delete it. The volume slider applies to every sound.

## How it works

```
 Microphone ──► RVC engine (Applio, GPU) ──► VoiceChanger Sink ──► VoiceChanger Mic ──► Discord
                                                  ▲     │
                       Soundboard (ffmpeg) ───────┘     └──► Monitor (headphones, optional)
```

The app creates a virtual sink/source pair with `pw-loopback`. The converted audio goes into **VoiceChanger Sink**, and PipeWire exposes it as **VoiceChanger Mic**, a regular input device any app can pick. When the voice changer is off or a voice is training, a second loopback sends the raw microphone straight to the sink, so the mic never goes silent. Soundboard clips are decoded by `ffmpeg` and played into the same sink with `pw-cat`.

## Data

Everything lives in `data/` (git-ignored): `config.json`, `voices/<name>/` (model, index and pitch), `datasets/<name>/` (copies of the uploaded audio) and `sounds/` (soundboard files).

## Tests

```sh
PYTHONPATH=src .venv/bin/python tests/test_hotkey.py
```

## License

[MIT](LICENSE). Applio, cloned into `vendor/` during install, has its own [license](https://github.com/IAHispano/Applio/blob/main/LICENSE).
