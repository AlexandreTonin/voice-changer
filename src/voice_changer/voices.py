import json
import re
import shutil

from voice_changer.config import VOICES_DIR

NAME_PATTERN = re.compile(r"^[\w-]{1,40}$")


def is_valid_name(name):
    return bool(NAME_PATTERN.match(name))


def list_voices():
    if not VOICES_DIR.exists():
        return []
    return sorted(p.name for p in VOICES_DIR.iterdir() if (p / "model.pth").exists())


def model_paths(name):
    voice_dir = VOICES_DIR / name
    return voice_dir / "model.pth", voice_dir / "model.index"


def install_voice(name, pth, index):
    voice_dir = VOICES_DIR / name
    voice_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(pth, voice_dir / "model.pth")
    shutil.copy(index, voice_dir / "model.index")


def get_pitch(name):
    try:
        return json.loads((VOICES_DIR / name / "meta.json").read_text())["pitch"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return 0


def set_pitch(name, pitch):
    (VOICES_DIR / name / "meta.json").write_text(json.dumps({"pitch": pitch}))


def rename_voice(old, new):
    (VOICES_DIR / old).rename(VOICES_DIR / new)


def delete_voice(name):
    shutil.rmtree(VOICES_DIR / name)
