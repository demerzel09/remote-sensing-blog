#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
OUTPUT_DIR="data/outputs/model_example"
# The training script reads feature directories from $CONFIG
CONFIG="configs/train.yaml"

VERBOSE="1"

python -m src.pipeline.train --config "$CONFIG" \
    --output-dir "$OUTPUT_DIR" \
    --verbose "${VERBOSE:-0}"

