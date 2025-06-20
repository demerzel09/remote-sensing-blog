#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
FEATURES_DIR="data/processed/example_run"
MODEL_DIR="data/outputs/model_example"
OUTPUT_DIR="data/outputs/prediction_example"
CONFIG="configs/predict.yaml"

python -m src.pipeline.predict --config "$CONFIG" \
    --features-dir "$FEATURES_DIR" --model-dir "$MODEL_DIR" \
    --output-dir "$OUTPUT_DIR"

