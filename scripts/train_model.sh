#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
INPUT_DIR="data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31"
OUTPUT_DIR="outputs/model_example"
CONFIG="configs/train.yaml"

python -m src.pipeline.train --config "$CONFIG" \
    --input-dir "$INPUT_DIR" --output-dir "$OUTPUT_DIR"

