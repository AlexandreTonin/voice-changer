#!/bin/sh
set -e
cd "$(dirname "$(readlink -f "$0")")"

APPLIO_COMMIT=50487069bee19e10b38886570b111016f995642c
APT_PACKAGES="ffmpeg libportaudio2 libxcb-cursor0 pipewire-bin"

missing=""
for pkg in $APT_PACKAGES; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing="$missing $pkg"
done
if [ -n "$missing" ]; then
    sudo apt install -y $missing
fi

if [ ! -d vendor/Applio ]; then
    git clone https://github.com/IAHispano/Applio vendor/Applio
fi
git -C vendor/Applio fetch --quiet origin "$APPLIO_COMMIT" || true
git -C vendor/Applio checkout --quiet "$APPLIO_COMMIT"

[ -d .venv ] || uv venv --python 3.12 .venv
UV_HTTP_TIMEOUT=300 VIRTUAL_ENV=.venv uv pip install -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cu128 --index-strategy unsafe-best-match

(cd vendor/Applio && ../../.venv/bin/python -c \
    "from rvc.lib.tools.prerequisites_download import prequisites_download_pipeline as p, ensure_pretrained as e; p(False, True, False); e('HiFi-GAN', 40000)")

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/voice-changer.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Voice Changer
Exec=$PWD/run.sh
Icon=audio-input-microphone
Categories=AudioVideo;Audio;
DESKTOP

echo "Done. Start with ./run.sh or from the app launcher (Voice Changer)."
