#!/usr/bin/env bash
set -euo pipefail

python -m src.pipeline.download --config configs/download.yaml
python -m src.pipeline.preprocess --config configs/preprocess.yaml
python -m src.pipeline.train --config configs/train.yaml
python -m src.pipeline.predict --config configs/predict.yaml

