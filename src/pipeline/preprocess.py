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


def main() -> None:
    parser = argparse.ArgumentParser(description="Preprocess Sentinel bands")
    parser.add_argument("--config", required=True, help="YAML config file")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    mask = cloud_mask(cfg["qa"])
    stack, meta = stack_bands(cfg["bands"], mask)
    features = compute_features(stack, red_idx=2, nir_idx=3, swir_idx=4)

    out_path = Path(cfg.get("features_out", "data/processed/features.npz"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out_path, features=features)
    with open(out_path.with_suffix(".meta.json"), "w") as f:
        json.dump(meta, f)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
