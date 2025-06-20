import argparse
import json
import joblib
import shutil
from pathlib import Path

import numpy as np
import yaml

from ..classification.predict import predict_model
from ..preprocess.cloudmask import cloud_mask
from ..preprocess.stack_bands import stack_bands
from ..preprocess.features import compute_features
from .preprocess import split_band_stack


def main() -> None:
    parser = argparse.ArgumentParser(description="Run model inference")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--input-dir", required=True, help="Directory containing the dataset")
    parser.add_argument("--model-dir", required=True, help="Directory with trained model")
    parser.add_argument("--output-dir", required=True, help="Directory for prediction result")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    input_dir = Path(args.input_dir)
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    features_path = input_dir / "preprocess" / cfg["features"]
    if features_path.exists():
        data = np.load(features_path)["features"]
        meta_path = (
            input_dir
            / "preprocess"
            / Path(cfg.get("meta", Path(cfg["features"]).with_suffix(".meta.json"))).name
        )
        with open(meta_path) as f:
            meta = json.load(f)
    else:
        dl_cfg_path = input_dir / "download.yaml"
        if dl_cfg_path.exists():
            dl_cfg = yaml.safe_load(dl_cfg_path.read_text())
            spectral = [b for b in dl_cfg.get("bands", []) if b not in {"SCL", "dataMask"}]
            stack = input_dir / "BANDS.tif"
            if stack.exists():
                missing = [b for b in spectral if not (input_dir / f"{b}.tif").exists()]
                if missing:
                    split_band_stack(stack, spectral)
            else:
                raise ValueError("BANDS.tif not found in input directory")

            bands = [input_dir / f"{b}.tif" for b in spectral]
            scl_path = input_dir / "SCL.tif" if "SCL" in dl_cfg.get("bands", []) else input_dir / Path(cfg["scl"]).name
            mask_path = (
                input_dir / "MASK.tif" if "dataMask" in dl_cfg.get("bands", []) else input_dir / Path(cfg.get("mask", "")).name if cfg.get("mask") else None
            )
        else:
            bands = [input_dir / Path(p).name for p in cfg["bands"]]
            scl_path = input_dir / Path(cfg["scl"]).name
            mask_path = input_dir / Path(cfg.get("mask", "")).name if cfg.get("mask") else None

        mask = cloud_mask(scl_path, mask_path)
        stack, meta = stack_bands(bands, mask)
        data = compute_features(stack, red_idx=2, nir_idx=3, swir_idx=4)

    clf = joblib.load(model_dir / cfg["model"])
    out_path = output_dir / "prediction.tif"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predict_model(clf, data, meta, out_path)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
