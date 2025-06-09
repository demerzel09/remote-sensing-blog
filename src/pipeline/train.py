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
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    data = np.load(cfg["features"])["features"]
    with rasterio.open(cfg["labels"]) as src:
        labels = src.read(1)

    clf = train_model(data, labels, n_estimators=cfg.get("n_estimators", 100))

    model_path = Path(cfg.get("model_out", "outputs/model.pkl"))
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, model_path)

    shutil.copy(args.config, model_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
