import argparse
import json
import joblib
import shutil
from pathlib import Path

import numpy as np
import yaml

from ..classification.predict import predict_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Run model inference")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--features-dir", required=True, help="Directory with features file")
    parser.add_argument("--model-dir", required=True, help="Directory with trained model")
    parser.add_argument("--output-dir", required=True, help="Directory for prediction result")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    features_dir = Path(args.features_dir)
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    features_path = features_dir / Path(cfg["features"]).name
    data = np.load(features_path)["features"]
    meta_path = features_dir / Path(cfg.get("meta", Path(cfg["features"]).with_suffix(".meta.json"))).name
    with open(meta_path) as f:
        meta = json.load(f)

    clf = joblib.load(model_dir / Path(cfg["model"]).name)
    out_path = output_dir / Path(cfg.get("output", "prediction.tif")).name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predict_model(clf, data, meta, out_path)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
