#!/usr/bin/env sh
set -eu

PROJECT_DIR="${1:-$(pwd)}"
PYTHON_BIN="${PYTHON:-python3}"

"$PYTHON_BIN" -m pip install "$PROJECT_DIR"
