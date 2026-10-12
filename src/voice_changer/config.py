import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLIO_DIR = ROOT / "vendor" / "Applio"
DATA_DIR = ROOT / "data"
VOICES_DIR = DATA_DIR / "voices"
DATASETS_DIR = DATA_DIR / "datasets"
SOUNDS_DIR = DATA_DIR / "sounds"
TRAINING_DIR = DATA_DIR / "training"
APPLIO_CONFIG_DIR = DATA_DIR / "applio"
CONFIG_FILE = DATA_DIR / "config.json"

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".opus")
AUDIO_FILTER = f"Audio ({' '.join('*' + e for e in AUDIO_EXTENSIONS)})"

LATENCY_PRESETS = {"Low": 0.1, "Balanced": 0.2, "Quality": 0.35}

DEFAULTS = {
    "enabled": False,
    "voice": None,
    "latency": "Balanced",
    "input": None,
    "monitor": None,
    "hotkey": "<ctrl>+<alt>+v",
    "sound_volume": 80,
}


def applio_env():
    return {
        "APPLIO_LOGS_DIR": str(TRAINING_DIR),
        "APPLIO_CONFIG_DIR": str(APPLIO_CONFIG_DIR),
    }


def load_config():
    try:
        return {**DEFAULTS, **json.loads(CONFIG_FILE.read_text())}
    except (FileNotFoundError, json.JSONDecodeError):
        return dict(DEFAULTS)


def save_config(config):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
