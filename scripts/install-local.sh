#!/usr/bin/env sh
set -eu

PROJECT_DIR="${1:-$(pwd)}"
PYTHON_BIN="${PYTHON:-python3}"
PIPX_BIN="${PIPX_BIN:-}"
INSTALL_HOME="${INSTALL_HOME:-$HOME/.local/share/adapta-cli}"
BIN_HOME="${BIN_HOME:-$HOME/.local/bin}"
PROJECT_VENV_DIR="$PROJECT_DIR/.venv"
ACTIVE_VENV_DIR="${VIRTUAL_ENV:-}"

if [ -n "$PIPX_BIN" ]; then
  "$PIPX_BIN" install "$PROJECT_DIR" --force
elif command -v pipx >/dev/null 2>&1; then
  pipx install "$PROJECT_DIR" --force
elif "$PYTHON_BIN" -m pipx --version >/dev/null 2>&1; then
  "$PYTHON_BIN" -m pipx install "$PROJECT_DIR" --force
else
  mkdir -p "$INSTALL_HOME" "$BIN_HOME"

  if [ -n "$ACTIVE_VENV_DIR" ] && [ -x "$ACTIVE_VENV_DIR/bin/python" ]; then
    VENV_DIR="$ACTIVE_VENV_DIR"
  elif [ -x "$PROJECT_VENV_DIR/bin/python" ]; then
    VENV_DIR="$PROJECT_VENV_DIR"
  else
    VENV_DIR="$PROJECT_VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null 2>&1
  "$VENV_DIR/bin/pip" install "$PROJECT_DIR"
  ln -sf "$VENV_DIR/bin/adapta" "$BIN_HOME/adapta"
  echo "adapta instalado em $VENV_DIR e linkado em $BIN_HOME/adapta" >&2
  echo "Se necessário, adicione $BIN_HOME ao PATH." >&2
fi
