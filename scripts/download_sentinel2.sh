#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 OUTPUT_DIR CONFIG" >&2
    exit 1
fi

OUTPUT_DIR="$1"
CONFIG="$2"

python -m src.pipeline.download --config "$CONFIG" --output "$OUTPUT_DIR"

