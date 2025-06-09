#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DOWNLOAD_DIR="data/raw/example_run"
FEATURE_DIR="data/processed/example_run"
MODEL_DIR="outputs/model_example"
PREDICT_DIR="outputs/prediction_example"

bash "$SCRIPT_DIR/download_sentinel2.sh" "$DOWNLOAD_DIR" configs/download.yaml
bash "$SCRIPT_DIR/preprocess_sentinel2.sh" "$DOWNLOAD_DIR" "$FEATURE_DIR" configs/preprocess.yaml
bash "$SCRIPT_DIR/train_model.sh" "$FEATURE_DIR" "$MODEL_DIR" configs/train.yaml
bash "$SCRIPT_DIR/predict_sentinel2.sh" "$FEATURE_DIR" "$MODEL_DIR" "$PREDICT_DIR" configs/predict.yaml

