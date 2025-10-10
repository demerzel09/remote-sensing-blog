#!/usr/bin/env python3
"""
Apply morphological operations to prediction difference rasters.

This module is reused both by the CLI defined here and by
``src.pipeline.predict`` when the difference overlay is generated during
inference.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Tuple

import numpy as np
import rasterio
from numpy.lib.stride_tricks import sliding_window_view


def _binary_erode(mask: np.ndarray) -> np.ndarray:
    """Erode a boolean mask using a 3×3 structuring element."""
    if not mask.any():
        return mask
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    windows = sliding_window_view(padded, (3, 3))
    return windows.all(axis=(-1, -2))


def _binary_dilate(mask: np.ndarray) -> np.ndarray:
    """Dilate a boolean mask using a 3×3 structuring element."""
    if not mask.any():
        return mask
    padded = np.pad(mask, 1, mode="constant", constant_values=False)
    windows = sliding_window_view(padded, (3, 3))
    return windows.any(axis=(-1, -2))


def apply_morphology(
    mismatch_mask: np.ndarray,
    valid_mask: np.ndarray,
    erode_count: int = 0,
    dilate_count: int = 0,
) -> np.ndarray:
    """
    Apply erosion/dilation to a mismatch mask, clamped to a validity mask.
    """
    result = mismatch_mask & valid_mask
    for _ in range(max(erode_count, 0)):
        result = _binary_erode(result)
        result &= valid_mask
    for _ in range(max(dilate_count, 0)):
        result = _binary_dilate(result)
        result &= valid_mask
    return result


def highlight_rgba_from_mask(mask: np.ndarray) -> np.ndarray:
    """Return an RGBA uint8 array with red pixels where ``mask`` is True."""
    rgba = np.zeros((4, mask.shape[0], mask.shape[1]), dtype=np.uint8)
    rgba[0][mask] = 255  # Red channel
    rgba[3][mask] = 255  # Alpha channel
    return rgba


def save_highlight_rgba(
    path: Path,
    highlight_mask: np.ndarray,
    base_meta: dict,
    valid_mask: np.ndarray | None = None,
) -> None:
    """Write an RGBA raster that highlights mismatch pixels."""
    meta = base_meta.copy()
    meta.update(count=4, dtype="uint8")
    meta.pop("nodata", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **meta) as dst:
        dst.write(highlight_rgba_from_mask(highlight_mask))
        if valid_mask is None:
            valid_mask = np.ones_like(highlight_mask, dtype=bool)
        dataset_mask = np.zeros(highlight_mask.shape, dtype=np.uint8)
        dataset_mask[valid_mask] = 255
        dst.write_mask(dataset_mask)


def _iter_difference_files(root: Path, pattern: str) -> Iterable[Path]:
    if root.is_file():
        if root.name == pattern:
            yield root
        return
    yield from root.rglob(pattern)


def _load_difference_as_mask(path: Path) -> Tuple[np.ndarray, np.ndarray, dict]:
    """
    Load a difference raster and return (mismatch_mask, valid_mask, meta).
    """
    with rasterio.open(path) as src:
        data = src.read()
        meta = src.meta.copy()
        dataset_mask = src.dataset_mask()
        nodata = src.nodata

    if data.ndim != 3:
        raise ValueError(f"Unexpected raster dimensions for {path}: {data.shape}")

    if data.shape[0] == 1:
        band = data[0]
        mismatch = band == 1
        valid = np.ones_like(band, dtype=bool)
        if nodata is not None:
            valid &= band != nodata
    else:
        # Assume RGBA; red channel stores highlights.
        mismatch = data[0] > 0
        valid = np.ones_like(mismatch, dtype=bool)

    if dataset_mask.size:
        valid &= dataset_mask > 0

    return mismatch.astype(bool), valid, meta


def _process_file(
    path: Path,
    erode_count: int,
    dilate_count: int,
    overwrite: bool,
) -> Path | None:
    model_suffix = f"E{erode_count}D{dilate_count}"
    out_path = path.with_name(f"{path.stem}{model_suffix}{path.suffix}")
    if out_path.exists() and not overwrite:
        print(f"[skip] {out_path} already exists")
        return out_path

    mismatch, valid, meta = _load_difference_as_mask(path)
    highlight = apply_morphology(mismatch, valid, erode_count, dilate_count)
    save_highlight_rgba(out_path, highlight, meta, valid)
    print(f"[ok] {out_path}")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply erosion/dilation to difference.tif files recursively."
    )
    parser.add_argument(
        "--root",
        required=True,
        help="Root directory to search for difference rasters.",
    )
    parser.add_argument(
        "--pattern",
        default="difference.tif",
        help="File name pattern to search for (default: difference.tif).",
    )
    parser.add_argument(
        "--erode",
        type=int,
        default=2,
        help="Number of erosion iterations (default: 2).",
    )
    parser.add_argument(
        "--dilate",
        type=int,
        default=2,
        help="Number of dilation iterations (default: 2).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing output rasters.",
    )
    args = parser.parse_args()

    if args.erode < 0 or args.dilate < 0:
        raise ValueError("Erode and dilate counts must be non-negative integers.")

    root = Path(args.root).expanduser().resolve()
    for difference_path in _iter_difference_files(root, args.pattern):
        _process_file(difference_path, args.erode, args.dilate, args.overwrite)


if __name__ == "__main__":
    main()
