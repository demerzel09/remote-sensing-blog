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
    data = np.load(features_path)["features"]
    meta_path = input_dir / "preprocess" / Path(cfg.get("meta", Path(cfg["features"]).with_suffix(".meta.json"))).name
    with open(meta_path) as f:
        meta = json.load(f)

    clf = joblib.load(model_dir / cfg["model"])
    out_path = output_dir / "prediction.tif"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predict_model(clf, data, meta, out_path)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
