#!/usr/bin/env sh
set -eu

PROJECT_DIR="${1:-$(pwd)}"
PYTHON_BIN="${PYTHON:-python3}"
PIPX_BIN="${PIPX_BIN:-}"
INSTALL_HOME="${INSTALL_HOME:-$HOME/.local/share/adapta-cli}"
BIN_HOME="${BIN_HOME:-$HOME/.local/bin}"

if [ -n "$PIPX_BIN" ]; then
  "$PIPX_BIN" install "$PROJECT_DIR" --force
elif command -v pipx >/dev/null 2>&1; then
  pipx install "$PROJECT_DIR" --force
elif "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pipx install "$PROJECT_DIR" --force
else
  VENV_DIR="$INSTALL_HOME/venv"
  mkdir -p "$INSTALL_HOME" "$BIN_HOME"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
  "$VENV_DIR/bin/pip" install "$PROJECT_DIR"
  ln -sf "$VENV_DIR/bin/adapta" "$BIN_HOME/adapta"
  echo "adapta instalado em $VENV_DIR e linkado em $BIN_HOME/adapta" >&2
  echo "Se necessário, adicione $BIN_HOME ao PATH." >&2
fi
