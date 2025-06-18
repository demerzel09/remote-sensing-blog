#!/usr/bin/env python
"""Create label raster by clipping ESA WorldCover to match Sentinel-2 imagery."""
from __future__ import annotations

import argparse
from pathlib import Path

import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np
from urllib.request import urlretrieve

from urllib.error import HTTPError
import sys

import tempfile
import zipfile
import shutil

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clip WorldCover to target raster")
    p.add_argument(
        "--worldcover",
        default="data/worldcover/ESA_WorldCover_10m_2021_v100_Map.tif",
        help="Path to WorldCover TIFF (will be downloaded if missing)",
    )
    p.add_argument("--reference", required=True, help="Raster to match (e.g. B02)")
    p.add_argument("--output", required=True, help="Output labels.tif path")
    p.add_argument(
        "--url",
        default="https://esa-worldcover.s3.amazonaws.com/v100/2021/map/ESA_WorldCover_10m_2021_v100_Map.zip",
        help="ZIP URL for WorldCover when downloading",
    )

    return p.parse_args()


def main() -> None:
    args = parse_args()

    wc_path = Path(args.worldcover)
    if not wc_path.exists():
        print(f"Downloading WorldCover data from {args.url}")
        wc_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            urlretrieve(args.url, wc_path)
        except HTTPError as e:
            print(
                f"Failed to download WorldCover. Check URL or network: {args.url}"
            )
            sys.exit(1)

            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / Path(args.url).name
                urlretrieve(args.url, zip_path)
                with zipfile.ZipFile(zip_path) as zf:
                    tif_member = None
                    for name in zf.namelist():
                        if name.lower().endswith('.tif'):
                            tif_member = name
                            break
                    if tif_member is None:
                        raise RuntimeError('TIFF not found in ZIP archive')
                    zf.extract(tif_member, path=tmpdir)
                    shutil.move(Path(tmpdir) / tif_member, wc_path)
        except Exception as e:
            raise RuntimeError(
                'Failed to download or extract WorldCover dataset. '
                'Verify the URL or supply --url.'
            ) from e

    args.worldcover = str(wc_path)

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
