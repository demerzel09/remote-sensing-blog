#!/usr/bin/env python3
"""Mosaic Sentinel date folders into single-band TIFFs.

This utility expects a directory containing subfolders named by
acquisition timestamp (e.g. ``2024-01-01T103000``). Each subfolder
should already contain individual band files such as ``B02.tif`` or
``SCL.tif`` produced by :mod:`src.utils.download_sentinel`.

The script merges each band across all subfolders and writes the
mosaicked band back to the output directory while preserving the
original file names.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

import rasterio
from rasterio.merge import merge


def mosaic_date_folders(input_dir: Path, output_dir: Path | None = None) -> Path:
    """Merge bands across date subfolders."""
    input_dir = Path(input_dir)
    if output_dir is None:
        output_dir = input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    sub_dirs = [p for p in sorted(input_dir.iterdir()) if p.is_dir()]
    if not sub_dirs:
        raise FileNotFoundError(f"No subfolders found in {input_dir}")

    band_files = sorted(f.name for f in sub_dirs[0].glob("*.tif"))
    for name in band_files:
        paths = [d / name for d in sub_dirs if (d / name).exists()]
        if not paths:
            continue
        srcs = [rasterio.open(p) for p in paths]
        mosaic, transform = merge(srcs)
        meta = srcs[0].meta.copy()
        for src in srcs:
            src.close()
        meta.update(transform=transform, height=mosaic.shape[1], width=mosaic.shape[2])
        out_path = output_dir / name
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(mosaic)
        print(f"Saved {out_path}")

    dl_yaml = input_dir / "download.yaml"
    if dl_yaml.exists():
        shutil.copy(dl_yaml, output_dir / "download.yaml")

    return output_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Mosaic dated subfolders of Sentinel bands")
    p.add_argument("--input-dir", required=True, help="Directory with dated folders")
    p.add_argument("--output-dir", help="Destination for mosaicked bands")
    args = p.parse_args()

    out = mosaic_date_folders(Path(args.input_dir), Path(args.output_dir) if args.output_dir else None)
    print(f"\u2705  Mosaicked bands written to {out}")


if __name__ == "__main__":
    main()
