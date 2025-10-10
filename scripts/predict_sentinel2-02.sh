#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
MODEL_DIR="data/outputs/model_example02"
CONFIG="configs/predict.yaml"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/fukuoka" \
    --output-dir "data/outputs/prediction_example-02/fukuoka"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/hita" \
    --output-dir "data/outputs/prediction_example-02/hita"



