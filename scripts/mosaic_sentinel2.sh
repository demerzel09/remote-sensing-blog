#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Match the directory created by the download step
RAW_DIR="data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31"

python -m src.pipeline.mosaic --input-dir "$RAW_DIR" --method best
