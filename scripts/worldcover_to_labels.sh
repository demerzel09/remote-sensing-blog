#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Example paths. WORLD_COVER should point to the downloaded WorldCover TIFF.
WORLD_COVER="data/worldcover/ESA_WorldCover_10m_2021_v100_Map.tif"
REFERENCE="data/raw/B02.tif"
OUTPUT="data/raw/labels.tif"

python -m src.utils.worldcover_to_labels \
    --worldcover "$WORLD_COVER" \
    --reference "$REFERENCE" \
    --output "$OUTPUT"
