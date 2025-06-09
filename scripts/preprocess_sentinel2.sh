#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
INPUT_DIR="data/raw/example_run"
OUTPUT_DIR="data/processed/example_run"
CONFIG="configs/preprocess.yaml"

python -m src.pipeline.preprocess --config "$CONFIG" \
    --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR"

