#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 FEATURES_DIR MODEL_DIR OUTPUT_DIR CONFIG" >&2
    exit 1
fi

FEATURES_DIR="$1"
MODEL_DIR="$2"
OUTPUT_DIR="$3"
CONFIG="$4"

python -m src.pipeline.predict --config "$CONFIG" \
    --features-dir "$FEATURES_DIR" --model-dir "$MODEL_DIR" \
    --output-dir "$OUTPUT_DIR"

