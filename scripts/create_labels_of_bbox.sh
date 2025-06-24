#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/fukuoka"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/kitakyusyu"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/oita"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/hita"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/karatzu"

python -m src.utils.worldcover_to_label --worldcover "data/wc2021_kyusyu_bbox" \
    --sentinel-dir "data/example_run/Sentinel-2/aso"
