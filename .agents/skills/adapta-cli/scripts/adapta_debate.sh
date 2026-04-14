#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 ]]; then
  echo "Usage: adapta_debate.sh <config.json> <rounds>=3 \"<prompt>\" <output-name> [extra adapta debate flags]" >&2
  exit 1
fi

CONFIG_PATH=$1
ROUNDS=$2
PROMPT_TEXT=$3
OUTPUT_NAME=$4
shift 4

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Debate config not found: $CONFIG_PATH" >&2
  exit 1
fi

if ! [[ "$ROUNDS" =~ ^[0-9]+$ ]]; then
  echo "Rounds must be a positive integer." >&2
  exit 1
fi

if (( ROUNDS < 3 )); then
  echo "Use at least 3 rounds to let the agents iterate." >&2
  exit 1
fi

DEBATE_DIR=${DEBATE_OUTPUT_DIR:-debate}
mkdir -p "$DEBATE_DIR"

echo "Existing debate outputs in $DEBATE_DIR (latest first):"
if compgen -G "$DEBATE_DIR/*" > /dev/null; then
  ls -1t "$DEBATE_DIR"
else
  echo "(none recorded yet)"
fi

if [[ "$OUTPUT_NAME" = /* ]]; then
  OUTPUT_PATH="$OUTPUT_NAME"
elif [[ "$OUTPUT_NAME" == ${DEBATE_DIR}/* ]]; then
  OUTPUT_PATH="$OUTPUT_NAME"
else
  OUTPUT_PATH="${DEBATE_DIR}/$OUTPUT_NAME"
fi

if [[ -f "$OUTPUT_PATH" ]]; then
  echo "Output already exists: $OUTPUT_PATH" >&2
  exit 1
fi

adapta debate \
  --config "$CONFIG_PATH" \
  --rounds "$ROUNDS" \
  --prompt "$PROMPT_TEXT" \
  --output "$OUTPUT_PATH" \
  "$@"
