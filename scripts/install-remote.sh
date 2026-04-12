#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <repo-url> [ref]" >&2
  exit 1
fi

REPO_URL="$1"
REF="${2:-}"
PYTHON_BIN="${PYTHON:-python3}"

if printf '%s' "$REPO_URL" | grep -q '^file://'; then
  LOCAL_PATH="${REPO_URL#file://}"
  "$PYTHON_BIN" -m pip install "$LOCAL_PATH"
elif [ -n "$REF" ]; then
  "$PYTHON_BIN" -m pip install "git+$REPO_URL@$REF"
else
  "$PYTHON_BIN" -m pip install "git+$REPO_URL"
fi
