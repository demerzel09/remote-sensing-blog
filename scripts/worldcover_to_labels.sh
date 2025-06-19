#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"



# Example options for downloading WorldCover tiles.
# The selected bounding box roughly covers the Kyushu area of Japan.

python -m src.utils.download_worldcover_datasets \
    --bbox 30 129 34 132 \
    --output "data/wc2021_kyusyu_bbox" \
    --version v200/2021/map/
