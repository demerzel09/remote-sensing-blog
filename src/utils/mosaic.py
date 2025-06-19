from __future__ import annotations

"""Utility functions to mosaic raster files."""

from pathlib import Path
from typing import Iterable

import rasterio
from rasterio.merge import merge
import yaml

from .download_sentinel import split_band_stack, DEFAULT_BANDS


def mosaic_rasters(raster_paths: Iterable[Path], output_path: Path) -> Path:
    """Merge multiple rasters into a single file.

    Parameters
    ----------
    raster_paths : Iterable[Path]
        Paths to GeoTIFF files to merge. All must have the same band structure.
    output_path : Path
        Where to save the mosaicked image.
    """
    srcs = [rasterio.open(p) for p in raster_paths]
    mosaic, transform = merge(srcs)
    meta = srcs[0].meta.copy()
    meta.update(
        {
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": transform,
            "count": mosaic.shape[0],
        }
    )
    for s in srcs:
        s.close()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(mosaic)
    return output_path


def mosaic_sentinel_directory(out_dir: Path) -> Path:
    """Mosaic subdirectories produced by ``download_sentinel``.

    Parameters
    ----------
    out_dir : Path
        Directory containing dated subfolders with ``BANDS.tif`` and optional
        ``SCL.tif``/``MASK.tif`` files.
    """
    subdirs = [d for d in out_dir.iterdir() if d.is_dir()]
    if not subdirs:
        raise FileNotFoundError("No scene folders found for mosaicking")

    def _collect(name: str) -> list[Path]:
        paths = [d / name for d in subdirs if (d / name).exists()]
        return paths if len(paths) == len(subdirs) else []

    band_paths = _collect("BANDS.tif")
    if not band_paths:
        raise FileNotFoundError("BANDS.tif not found in scene folders")
    mosaic_rasters(band_paths, out_dir / "BANDS.tif")

    cfg_path = out_dir / "download.yaml"
    spectral = DEFAULT_BANDS
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text())
        spectral = [b for b in cfg.get("bands", DEFAULT_BANDS) if b not in {"SCL", "dataMask"}]
    split_band_stack(out_dir / "BANDS.tif", spectral)

    scl_paths = _collect("SCL.tif")
    if scl_paths:
        mosaic_rasters(scl_paths, out_dir / "SCL.tif")

    mask_paths = _collect("MASK.tif")
    if mask_paths:
        mosaic_rasters(mask_paths, out_dir / "MASK.tif")

    return out_dir / "BANDS.tif"
