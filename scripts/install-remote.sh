#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <repo-url> [ref]" >&2
  exit 1
fi

REPO_URL="$1"
REF="${2:-}"
PYTHON_BIN="${PYTHON:-python3}"
PIPX_BIN="${PIPX_BIN:-}"
INSTALL_HOME="${INSTALL_HOME:-$HOME/.local/share/adapta-cli}"
BIN_HOME="${BIN_HOME:-$HOME/.local/bin}"

INSTALL_TARGET=""

if printf '%s' "$REPO_URL" | grep -q '^file://'; then
  LOCAL_PATH="${REPO_URL#file://}"
  INSTALL_TARGET="$LOCAL_PATH"
elif [ -n "$REF" ]; then
  INSTALL_TARGET="git+$REPO_URL@$REF"
else
  INSTALL_TARGET="git+$REPO_URL"
fi

if [ -n "$PIPX_BIN" ]; then
  "$PIPX_BIN" install "$INSTALL_TARGET" --force
elif command -v pipx >/dev/null 2>&1; then
  pipx install "$INSTALL_TARGET" --force
elif "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pipx install "$INSTALL_TARGET" --force
else
  VENV_DIR="$INSTALL_HOME/venv"
  mkdir -p "$INSTALL_HOME" "$BIN_HOME"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
  "$VENV_DIR/bin/pip" install "$INSTALL_TARGET"
  ln -sf "$VENV_DIR/bin/adapta" "$BIN_HOME/adapta"
  echo "adapta instalado em $VENV_DIR e linkado em $BIN_HOME/adapta" >&2
  echo "Se necessário, adicione $BIN_HOME ao PATH." >&2
fi
