from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio

from ..preprocess.cloudmask import cloud_mask


def apply_cloud_mask(scene_dir: Path) -> None:
    """Mask cloudy pixels in all band files of a scene folder."""
    band_stack = scene_dir / "BANDS.tif"
    scl_file = scene_dir / "SCL.tif"
    mask_file = scene_dir / "MASK.tif"

    if not band_stack.exists() or not scl_file.exists():
        return

    mask = cloud_mask(scl_file, mask_file if mask_file.exists() else None)

    with rasterio.open(band_stack) as src:
        data = src.read().astype("float32")
        meta = src.meta.copy()
    data[:, mask] = -9999.0
    meta.update(dtype="float32", nodata=-9999.0)
    tmp = scene_dir / "BANDS.tmp.tif"
    with rasterio.open(tmp, "w", **meta) as dst:
        dst.write(data)
    tmp.replace(band_stack)

    for band_file in scene_dir.glob("B??.tif"):
        if band_file.name in {"SCL.tif", "MASK.tif"}:
            continue
        with rasterio.open(band_file) as src:
            arr = src.read(1).astype("float32")
            meta = src.meta.copy()
        arr[mask] = -9999.0
        meta.update(dtype="float32", nodata=-9999.0)
        tmp_band = band_file.with_suffix(".tmp.tif")
        with rasterio.open(tmp_band, "w", **meta) as dst:
            dst.write(arr, 1)
        tmp_band.replace(band_file)


def apply_cloud_mask_to_directory(out_dir: Path) -> None:
    """Apply cloud masking to all dated subfolders."""
    for sub in out_dir.iterdir():
        if sub.is_dir():
            apply_cloud_mask(sub)
