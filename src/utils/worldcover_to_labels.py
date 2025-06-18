#!/usr/bin/env python
"""Create label raster by clipping ESA WorldCover to match Sentinel‑2 imagery.

Version 200 of WorldCover distributes 1°×1° tiles instead of a single global
archive.  This utility downloads only the required tiles based on a tile name
like ``N35E139`` or a geographic bounding box.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
from urllib.request import urlretrieve

from urllib.error import HTTPError
import sys

import math

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clip WorldCover to target raster")
    p.add_argument("--tile", help="WorldCover tile name, e.g. N35E139")
    p.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Bounding box to determine required tiles",
    )
    p.add_argument(
        "--worldcover-dir",
        default="data/worldcover",
        help="Directory to store/download WorldCover tiles",
    )
    p.add_argument(
        "--base-url",
        default="https://esa-worldcover.s3.amazonaws.com/v200/2021/map",
        help="Base URL for WorldCover tiles",
    )
    p.add_argument("--reference", required=True, help="Raster to match (e.g. B02)")
    p.add_argument("--output", required=True, help="Output labels.tif path")

    return p.parse_args()


def main() -> None:
    args = parse_args()

    if not args.tile and not args.bbox:
        print("Specify --tile or --bbox")
        sys.exit(1)

    worldcover_dir = Path(args.worldcover_dir)
    worldcover_dir.mkdir(parents=True, exist_ok=True)

    def tiles_from_bbox(bbox: tuple[float, float, float, float]) -> list[str]:
        min_lon, min_lat, max_lon, max_lat = bbox
        tiles: list[str] = []
        for lat in range(math.floor(min_lat), math.ceil(max_lat)):
            for lon in range(math.floor(min_lon), math.ceil(max_lon)):
                ns = "N" if lat >= 0 else "S"
                ew = "E" if lon >= 0 else "W"
                tiles.append(f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}")
        return tiles

    tiles = [args.tile.upper()] if args.tile else tiles_from_bbox(tuple(args.bbox))

    tile_paths: list[Path] = []
    for tile in tiles:
        path = worldcover_dir / f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        if not path.exists():
            url = f"{args.base_url}/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
            print(f"Downloading {tile} from {url}")
            try:
                urlretrieve(url, path)
            except HTTPError:
                print(f"Failed to download WorldCover tile: {url}")
                sys.exit(1)
        tile_paths.append(path)

    with rasterio.open(args.reference) as ref:
        dst_transform = ref.transform
        dst_crs = ref.crs
        dst_height = ref.height
        dst_width = ref.width
        dst_profile = ref.profile.copy()
        dst_profile.update(count=1, dtype=rasterio.uint8, compress="lzw")

        data = np.zeros((dst_height, dst_width), dtype=rasterio.uint8)

        for tile_path in tile_paths:
            with rasterio.open(tile_path) as src:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=data,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.nearest,
                    dst_nodata=0,
                )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **dst_profile) as dst:
        dst.write(data, 1)


if __name__ == "__main__":
    main()
