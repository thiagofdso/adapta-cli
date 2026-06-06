#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: adapta_persona.sh <answers.json> [model] [additional adapta persona flags]" >&2
  exit 1
fi

ANSWERS_PATH=$1
if [[ ! -f "$ANSWERS_PATH" ]]; then
  echo "Persona answers file not found: $ANSWERS_PATH" >&2
  exit 1
fi
shift

DEFAULT_MODEL=${ADAPTA_MODEL:-gpt}
if [[ $# -gt 0 ]]; then
  MODEL=$1
  shift
else
  MODEL=$DEFAULT_MODEL
fi

adapta persona --model "$MODEL" --input-file "$ANSWERS_PATH" "$@"
