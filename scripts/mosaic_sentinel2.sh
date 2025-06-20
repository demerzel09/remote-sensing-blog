#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/fukuoka" \
--method best

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/kitakyusyu" \
--method best

python -m src.pipeline.mosaic \
    --input-dir "data/example_run/Sentinel-2/oita" \
--method best