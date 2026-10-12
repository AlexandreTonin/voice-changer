import os
import shutil
import sys

from voice_changer.config import APPLIO_DIR, TRAINING_DIR
from voice_changer.voices import install_voice

SAMPLE_RATE = 40000
BATCH_SIZE = 8


def stage(label):
    print(f"STAGE {label}", flush=True)


def check(result):
    print(result, flush=True)
    if "failed" in result.lower():
        sys.exit(1)


def latest_weights(model_dir, name):
    weights = list(model_dir.glob(f"{name}_*e_*s.pth"))
    return max(weights, key=lambda p: p.stat().st_mtime)


def train(name, dataset, epochs):
    import core
    from rvc.lib.tools.prerequisites_download import prequisites_download_pipeline

    cores = os.cpu_count()
    stage("Downloading base models")
    prequisites_download_pipeline(False, True, False)
    stage("Preparing audio")
    check(core.run_preprocess_script(
        name, dataset, SAMPLE_RATE, cores, "Automatic", False, False, 0.7, 3.0, 0.3
    ))
    stage("Extracting features")
    check(core.run_extract_script(name, "rmvpe", cores, 0, SAMPLE_RATE, "contentvec"))
    stage("Training")
    check(core.run_train_script(
        name, epochs, True, False, epochs, SAMPLE_RATE, BATCH_SIZE, 0, True, False
    ))
    stage("Saving voice")
    model_dir = TRAINING_DIR / name
    install_voice(name, latest_weights(model_dir, name), model_dir / f"{name}.index")
    shutil.rmtree(model_dir)


if __name__ == "__main__":
    os.chdir(APPLIO_DIR)
    sys.path.insert(0, str(APPLIO_DIR))
    train(sys.argv[1], sys.argv[2], int(sys.argv[3]))
