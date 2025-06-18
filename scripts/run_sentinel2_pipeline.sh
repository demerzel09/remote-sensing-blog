#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Simply invoke each helper script which defines its own paths
bash "$SCRIPT_DIR/download_sentinel2.sh"
bash "$SCRIPT_DIR/preprocess_sentinel2.sh"
bash "$SCRIPT_DIR/worldcover_to_labels.sh"
bash "$SCRIPT_DIR/train_model.sh"
bash "$SCRIPT_DIR/predict_sentinel2.sh"

