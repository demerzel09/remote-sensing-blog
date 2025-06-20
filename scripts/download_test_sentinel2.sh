#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run. The YAML now includes the list of
# bands to download.
OUTPUT_DIR="data/example_run"

python -m src.pipeline.download --output "$OUTPUT_DIR" \
--config "configs/download_hita.yaml" \
--name hita

python -m src.pipeline.download --output "$OUTPUT_DIR" \
--config "configs/download_karatzu.yaml"
--name karatzu

python -m src.pipeline.download --output "$OUTPUT_DIR" \
--config "configs/download_aso.yaml"
--name aso