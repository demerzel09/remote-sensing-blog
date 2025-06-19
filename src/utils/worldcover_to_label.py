#!/usr/bin/env python3
"""Create a label raster from ESA WorldCover tiles.

This utility crops and reprojects WorldCover data to match
Sentinel-2 imagery downloaded with :mod:`src.utils.download_sentinel`.

Example
-------
```bash
python -m src.utils.worldcover_to_label \
    --worldcover data/wc2021_kyusyu_bbox \
    --sentinel-dir data/example_run/Sentinel-2/35.6_139.7_2024-01-01_2024-01-31 \
    --output labels.tif
```
"""

from __future__ import annotations

import argparse
from pathlib import Path
import yaml
import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling
from rasterio.windows import from_bounds


def parse_bbox(cfg: dict) -> tuple[float, float, float, float]:
    """Return lon/lat bounding box from a download configuration."""
    lat = cfg["lat"]
    lon = cfg["lon"]
    buffer = cfg.get("buffer", 0.0)
    return (
        lon - buffer,
        lat - buffer,
        lon + buffer,
        lat + buffer,
    )


def load_reference_meta(sentinel_dir: Path, cfg: dict) -> dict:
    """Load raster metadata from a Sentinel band to match resolution and CRS."""
    band = cfg.get("bands", ["B02"])[0]
    path = sentinel_dir / f"{band}.tif"
    if not path.exists():
        tiffs = list(sentinel_dir.glob("*.tif"))
        if not tiffs:
            raise FileNotFoundError("No Sentinel band TIFFs found")
        path = tiffs[0]
    with rasterio.open(path) as src:
        meta = src.meta.copy()
    meta.update(count=1, dtype="uint8")
    return meta


def main() -> None:
    p = argparse.ArgumentParser(description="Convert WorldCover tiles to label raster")
    p.add_argument("--worldcover", required=True, help="Directory with WorldCover GeoTIFFs")
    p.add_argument(
        "--sentinel-dir",
        required=True,
        help="Sentinel download directory containing download.yaml",
    )
    p.add_argument("--output", help="Output label path; defaults to <sentinel-dir>/labels.tif")
    args = p.parse_args()

    wc_dir = Path(args.worldcover)
    s2_dir = Path(args.sentinel_dir)
    out_path = Path(args.output) if args.output else s2_dir / "labels.tif"

    cfg = yaml.safe_load((s2_dir / "download.yaml").read_text())
    bbox = parse_bbox(cfg)

    meta = load_reference_meta(s2_dir, cfg)

    wc_files = sorted(wc_dir.glob("*.tif"))
    if not wc_files:
        raise FileNotFoundError(f"No WorldCover tiles found in {wc_dir}")
    srcs = [rasterio.open(fp) for fp in wc_files]
    mosaic, transform = merge(srcs)
    for src in srcs:
        src.close()

    window = from_bounds(*bbox, transform=transform)
    mosaic = mosaic[
        :,
        int(window.row_off) : int(window.row_off + window.height),
        int(window.col_off) : int(window.col_off + window.width),
    ]
    transform = rasterio.windows.transform(window, transform)

    dest = np.zeros((1, meta["height"], meta["width"]), dtype=np.uint8)
    reproject(
        source=mosaic,
        destination=dest,
        src_transform=transform,
        src_crs="EPSG:4326",
        dst_transform=meta["transform"],
        dst_crs=meta["crs"],
        resampling=Resampling.nearest,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(out_path, "w", **meta) as dst:
        dst.write(dest)
    print(f"Saved label raster to {out_path}")


if __name__ == "__main__":
    main()
