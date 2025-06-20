#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG="configs/preprocess.yaml"  # features_out path; band names loaded from download.yaml

python -m src.pipeline.preprocess --config "$CONFIG" \
    --input-dir "data/example_run/Sentinel-2/hita" \

python -m src.pipeline.preprocess --config "$CONFIG" \
    --input-dir "data/example_run/Sentinel-2/karatzu" \

python -m src.pipeline.preprocess --config "$CONFIG" \
    --input-dir "data/example_run/Sentinel-2/aso" \
