#!/usr/bin/env python
"""Create label raster by clipping ESA WorldCover to match Sentinel-2 imagery."""
from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clip WorldCover to target raster")
    p.add_argument("--worldcover", required=True, help="Path to WorldCover TIFF")
    p.add_argument("--reference", required=True, help="Raster to match (e.g. B02)")
    p.add_argument("--output", required=True, help="Output labels.tif path")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    with rasterio.open(args.reference) as ref:
        dst_transform = ref.transform
        dst_crs = ref.crs
        dst_height = ref.height
        dst_width = ref.width
        dst_profile = ref.profile.copy()
        dst_profile.update(count=1, dtype=rasterio.uint8, compress="lzw")

        with rasterio.open(args.worldcover) as src:
            data = np.empty((dst_height, dst_width), dtype=rasterio.uint8)
            reproject(
                source=rasterio.band(src, 1),
                destination=data,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest,
            )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **dst_profile) as dst:
        dst.write(data, 1)


if __name__ == "__main__":
    main()
