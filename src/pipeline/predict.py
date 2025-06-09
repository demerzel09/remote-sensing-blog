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
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    data = np.load(cfg["features"])["features"]
    with open(cfg.get("meta", Path(cfg["features"]).with_suffix(".meta.json"))) as f:
        meta = json.load(f)

    clf = joblib.load(cfg["model"])
    out_path = Path(cfg.get("output", "outputs/prediction.tif"))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predict_model(clf, data, meta, out_path)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
