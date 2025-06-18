#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
# Match the directory created by the download step
INPUT_DIR="data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31"
CONFIG="configs/preprocess.yaml"  # features_out path; band names loaded from download.yaml

python -m src.pipeline.preprocess --config "$CONFIG" \
    --input-dir "$INPUT_DIR"

