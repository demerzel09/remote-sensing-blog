#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CONFIG="configs/preprocess.yaml"  # features_out path; band names loaded from download.yaml

python -m src.pipeline.preprocess --config "$CONFIG" \
--input-dir "data/example_run/Sentinel-2/33.5890_130.2730_2024-01-01_2024-01-31" \

python -m src.pipeline.preprocess --config "$CONFIG" \
--input-dir "data/example_run/Sentinel-2/33.9160_130.7450_2024-01-01_2024-02-16" \

python -m src.pipeline.preprocess --config "$CONFIG" \
--input-dir "data/example_run/Sentinel-2/33.3800_131.4680_2024-01-01_2024-02-16" \
