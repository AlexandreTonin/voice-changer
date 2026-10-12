#!/bin/sh
cd "$(dirname "$(readlink -f "$0")")"
PYTHONPATH="$PWD/src" exec .venv/bin/python -m voice_changer "$@"
