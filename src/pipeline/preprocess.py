import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import rasterio
import yaml

from ..preprocess.cloudmask import cloud_mask
from ..preprocess.stack_bands import stack_bands
from ..preprocess.features import compute_features

# 雲をマスクして cloud_mask()
# NDVI and NDWI 特徴を抽出する compute_features()

def split_band_stack(stack_path: Path, bands: list[str]) -> None:
    """Split a multi-band GeoTIFF into separate single-band files."""
    with rasterio.open(stack_path) as src:
        meta = src.meta.copy()
        if src.count < len(bands):
            raise ValueError("Band stack has fewer layers than expected")
        for i, name in enumerate(bands, 1):
            meta.update(count=1)
            out = stack_path.parent / f"{name}.tif"
            with rasterio.open(out, "w", **meta) as dst:
                dst.write(src.read(i), 1)
    stack_path.unlink()


def split_band_stack(stack_path: Path, bands: list[str]) -> None:
    """Split a multi-band GeoTIFF into separate single-band files."""
    with rasterio.open(stack_path) as src:
        meta = src.meta.copy()
        if src.count < len(bands):
            raise ValueError("Band stack has fewer layers than expected")
        for i, name in enumerate(bands, 1):
            meta.update(count=1)
            out = stack_path.parent / f"{name}.tif"
            with rasterio.open(out, "w", **meta) as dst:
                dst.write(src.read(i), 1)

def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess Sentinel bands")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--input-dir", required=True, help="Directory with raw bands")
    parser.add_argument("--output-dir", required=True, help="Directory for features")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    dl_cfg_path = input_dir / "download.yaml"
    if dl_cfg_path.exists():
        with open(dl_cfg_path) as f:
            dl_cfg = yaml.safe_load(f)

        spectral = [b for b in dl_cfg.get("bands", []) if b not in {"SCL", "dataMask"}]
        if not dl_cfg.get("split_bands", False):
            stack = input_dir / "BANDS.tif"
            if stack.exists():
                split_band_stack(stack, spectral)
                dl_cfg["split_bands"] = True
            else:
                raise ValueError(
                    "split_bands must be true when preprocessing downloaded data"
                )

        bands = [input_dir / f"{b}.tif" for b in spectral]
        if "SCL" in dl_cfg.get("bands", []):
            scl_path = input_dir / "SCL.tif"
        else:
            scl_path = input_dir / Path(cfg["scl"]).name
        if "dataMask" in dl_cfg.get("bands", []):
            mask_path = input_dir / "MASK.tif"
        else:
            mask_path = input_dir / Path(cfg.get("mask", "")).name if cfg.get("mask") else None
    else:
        bands = [input_dir / Path(p).name for p in cfg["bands"]]
        scl_path = input_dir / Path(cfg["scl"]).name
        mask_path = input_dir / Path(cfg.get("mask", "")).name if cfg.get("mask") else None

    mask = cloud_mask(scl_path, mask_path)
    stack, meta = stack_bands(bands, mask)
    features = compute_features(stack, red_idx=2, nir_idx=3, swir_idx=4)

    out_path = output_dir / Path(cfg.get("features_out", "features.npz")).name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_path, features=features)

    meta_json = meta.copy()
    if "crs" in meta_json and hasattr(meta_json["crs"], "to_string"):
        meta_json["crs"] = meta_json["crs"].to_string()

    with open(out_path.with_suffix(".meta.json"), "w") as f:
        json.dump(meta_json, f)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)
    if dl_cfg_path.exists():
        shutil.copy(dl_cfg_path, out_path.parent / dl_cfg_path.name)


if __name__ == "__main__":
    main()
