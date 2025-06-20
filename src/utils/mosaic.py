from __future__ import annotations

"""Utility functions to mosaic raster files."""

from pathlib import Path
from typing import Iterable

import rasterio
from rasterio.merge import merge
import numpy as np
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


def _prioritized_mosaic(band_paths: list[Path], scl_paths: list[Path], output_path: Path, method: str = "best") -> Path:
    """Composite scenes using SCL-based pixel priority.

    Parameters
    ----------
    band_paths : list[Path]
        ``BANDS.tif`` files from each scene.
    scl_paths : list[Path]
        ``SCL.tif`` files matching ``band_paths`` order.
    output_path : Path
        Where to save the composite image.
    method : {"best", "median"}
        Pixel selection strategy. ``"best"`` picks the best pixel by SCL
        priority. If multiple scenes share the same priority the pixels are
        blended using a weighted average that favors scenes with less overall
        cloud cover. ``"median"`` computes the median over clear pixels.
    """

    if method not in {"best", "median"}:
        raise ValueError("method must be 'best' or 'median'")

    band_srcs = [rasterio.open(p) for p in band_paths]
    scl_srcs = [rasterio.open(p) for p in scl_paths]

    bands_stack = np.stack([s.read() for s in band_srcs])
    scls = np.stack([s.read(1) for s in scl_srcs])
    meta = band_srcs[0].meta.copy()

    for s in band_srcs + scl_srcs:
        s.close()

    # Priority levels: clear < unclassified < cloudy/shadow
    priority = np.full_like(scls, 2, dtype=np.uint8)
    priority[np.isin(scls, [4, 5, 6])] = 0  # vegetation, bare, water
    priority[np.isin(scls, [7])] = 1        # unclassified

    h, w = priority.shape[1:]
    out = np.empty((bands_stack.shape[1], h, w), dtype=bands_stack.dtype)

    if method == "best":
        # Scene cloud fractions for weighting
        cloud_mask = np.isin(scls, (3, 7, 8, 9, 10, 11))
        cloud_frac = cloud_mask.mean(axis=(1, 2))
        weights = np.clip(1.0 - cloud_frac, 0.0, None)

        for r in range(h):
            for c in range(w):
                pr = priority[:, r, c]
                min_p = pr.min()
                idxs = np.where(pr == min_p)[0]
                if len(idxs) == 1:
                    out[:, r, c] = bands_stack[idxs[0], :, r, c]
                else:
                    w = weights[idxs]
                    total = w.sum()
                    if total == 0:
                        w = np.full_like(w, 1 / len(w))
                    else:
                        w = w / total
                    out[:, r, c] = np.sum(bands_stack[idxs, :, r, c] * w[:, None], axis=0)
    else:  # median composite
        mask = priority == 0
        expanded = mask[:, None, :, :]
        data = bands_stack.astype("float32")
        data[~expanded] = np.nan
        out = np.nanmedian(data, axis=0)
        nodata = meta.get("nodata", -9999.0)
        out = np.where(np.isnan(out), nodata, out).astype(bands_stack.dtype)

    meta.update({"height": h, "width": w, "count": out.shape[0]})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(output_path, "w", **meta) as dst:
        dst.write(out)

    return output_path


def mosaic_sentinel_directory(out_dir: Path, method: str = "best") -> Path:
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

    scl_paths = _collect("SCL.tif")
    if scl_paths and method in {"best", "median"}:
        _prioritized_mosaic(band_paths, scl_paths, out_dir / "BANDS.tif", method)
    else:
        mosaic_rasters(band_paths, out_dir / "BANDS.tif")

    cfg_path = out_dir / "download.yaml"
    spectral = DEFAULT_BANDS
    if cfg_path.exists():
        cfg = yaml.safe_load(cfg_path.read_text())
        spectral = [b for b in cfg.get("bands", DEFAULT_BANDS) if b not in {"SCL", "dataMask"}]
    split_band_stack(out_dir / "BANDS.tif", spectral)

    if scl_paths:
        mosaic_rasters(scl_paths, out_dir / "SCL.tif")

    mask_paths = _collect("MASK.tif")
    if mask_paths:
        mosaic_rasters(mask_paths, out_dir / "MASK.tif")

    return out_dir / "BANDS.tif"
