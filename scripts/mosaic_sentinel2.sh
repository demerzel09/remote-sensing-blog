#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/hita" \
--method best

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/karatzu" \
--method best

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/aso" \
--method best