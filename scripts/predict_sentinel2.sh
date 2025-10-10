#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
MODEL_DIR="data/outputs/model_example"
CONFIG="configs/predict.yaml"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/fukuoka" \
    --output-dir "data/outputs/prediction_example/fukuoka"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/aso" \
    --output-dir "data/outputs/prediction_example/aso"

python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/hita" \
    --output-dir "data/outputs/prediction_example/hita"

# (For reference) train data by training model
python -m src.pipeline.predict --config "$CONFIG" \
    --model-dir "$MODEL_DIR" \
    --input-dir "data/example_run/Sentinel-2/oita" \
    --output-dir "data/outputs/prediction_example/oita"


