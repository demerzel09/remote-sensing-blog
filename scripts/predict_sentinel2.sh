#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
MODEL_DIR="data/outputs/model_example"
OUTPUT_DIR="data/outputs/prediction_example"
CONFIG="configs/predict.yaml"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/ofukuoka"
    --output-dir "$OUTPUT_DIR"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/oita"
    --output-dir "$OUTPUT_DIR"


