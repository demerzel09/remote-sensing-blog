#!/usr/bin/env bash
set -euo pipefail

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"



# Example paths. WORLD_COVER will be downloaded as a ZIP archive and
# extracted if the TIFF does not already exist.

WORLD_COVER="data/worldcover/ESA_WorldCover_10m_2021_v100_Map.tif"
REFERENCE="data/raw/B02.tif"
OUTPUT="data/raw/labels.tif"

python -m src.utils.worldcover_to_labels \
    --worldcover "$WORLD_COVER" \
    --reference "$REFERENCE" \
    --output "$OUTPUT"
