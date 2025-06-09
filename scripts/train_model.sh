#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
INPUT_DIR="data/processed/example_run"
OUTPUT_DIR="outputs/model_example"
CONFIG="configs/train.yaml"

python -m src.pipeline.train --config "$CONFIG" \
    --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR"

