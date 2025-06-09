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
    parser.add_argument("--input-dir", required=True, help="Directory with feature file")
    parser.add_argument("--output-dir", required=True, help="Directory for model")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    features_path = input_dir / Path(cfg["features"]).name
    data = np.load(features_path)["features"]
    with rasterio.open(cfg["labels"]) as src:
        labels = src.read(1)

    clf = train_model(data, labels, n_estimators=cfg.get("n_estimators", 100))

    model_path = output_dir / Path(cfg.get("model_out", "model.pkl")).name
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_path)

    shutil.copy(args.config, model_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
