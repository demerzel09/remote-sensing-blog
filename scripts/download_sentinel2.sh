#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Hard coded paths for a single example run
OUTPUT_DIR="data/raw/example_run"
CONFIG="configs/download.yaml"

python -m src.pipeline.download --config "$CONFIG" --output "$OUTPUT_DIR" \
  # --api-url https://alternative.example.com/apihub

