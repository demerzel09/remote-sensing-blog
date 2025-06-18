#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"



# Example paths. The required WorldCover tile will be downloaded if missing.

WORLD_COVER_DIR="data/worldcover"
TILE="N35E139"
REFERENCE="data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31/B02.tif"
OUTPUT="data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31/labels.tif"

python -m src.utils.worldcover_to_labels \
    --worldcover-dir "$WORLD_COVER_DIR" \
    --tile "$TILE" \
    --reference "$REFERENCE" \
    --output "$OUTPUT"
