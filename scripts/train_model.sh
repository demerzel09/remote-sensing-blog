#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 INPUT_DIR OUTPUT_DIR CONFIG" >&2
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
CONFIG="$3"

python -m src.pipeline.train --config "$CONFIG" \
    --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR"

