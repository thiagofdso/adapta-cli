#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: adapta_prompt.sh \"<prompt text>\" [additional adapta prompt flags]" >&2
  exit 1
fi

DEFAULT_MODEL=${ADAPTA_MODEL_OVERRIDE:-${ADAPTA_MODEL:-gpt}}
PROMPT_TEXT=$1
shift || true

adapta prompt --model "${DEFAULT_MODEL}" --prompt "${PROMPT_TEXT}" "$@"
