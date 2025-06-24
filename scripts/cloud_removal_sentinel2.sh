#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/fukuoka"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/kitakyusyu"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/oita"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/hita"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/karatzu"

python -m src.pipeline.cloud_removal \
    --input-dir "data/example_run/Sentinel-2/aso"