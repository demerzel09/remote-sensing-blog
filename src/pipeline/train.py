import argparse
import joblib
import shutil
from pathlib import Path

import numpy as np
import rasterio
import yaml

from ..classification.train_model import train_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train classification model")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--output-dir", required=True, help="Directory for model")
    parser.add_argument(
        "--verbose",
        type=int,
        default=0,
        help="Verbosity level for RandomForest training",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    output_dir = Path(args.output_dir)

    input_dirs = [Path(d) for d in cfg.get("input_dirs", [])]

    feature_arrays = []
    label_arrays = []

    for d in input_dirs:
        features_path = d / "preprocess" / cfg["features"]
        features = np.load(features_path)["features"]
        feature_arrays.append(features.reshape(features.shape[0], -1))

        labels_path = d / cfg["labels"]
        with rasterio.open(labels_path) as src:
            labels = src.read(1)
        label_arrays.append(labels.flatten())

    if not feature_arrays:
        raise ValueError("No input directories provided in config")

    data = np.hstack(feature_arrays)
    labels = np.hstack(label_arrays)

    sample_fraction = cfg.get("sample_fraction")
    if sample_fraction:
        n_samples = data.shape[1]
        size = int(n_samples * sample_fraction)
        rng = np.random.default_rng(0)
        idx = rng.choice(n_samples, size=size, replace=False)
        data = data[:, idx]
        labels = labels[idx]

    clf = train_model(
        data,
        labels,
        n_estimators=cfg.get("n_estimators", 100),
        max_depth=cfg.get("max_depth"),
        max_samples=cfg.get("max_samples"),
        verbose=args.verbose,
    )

    model_path = output_dir / cfg.get("model_name", "model.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_path)

    shutil.copy(args.config, model_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
