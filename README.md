# remote-sensing-blog


## 日本語の説明

このプロジェクトはリモートセンシングデータを用いた簡単な分類ワークフローを示します。必要なデータは複数バンドのGeoTIFFと雲判定用のQAバンド、学習用ラベルです。

1. `cloudmask.py` でQAバンドから雲マスクを作成します。
2. `stack_bands.py` でマスクを適用したバンドスタックを作成します。
3. `features.py` でNDVI・NDWIを計算します。
4. `train_model.py` でRandomForest分類器を学習させます。
5. `predict.py` で分類結果ラスタを生成します。
6. `app.py` をStreamlitで実行し、folium地図上で結果を確認できます。

This repository contains a minimal example of a Python pipeline for basic remote sensing analysis. The code is structured for future extensions such as polygon data integration and asset value analysis.



## Structure

```
remote_sensing/
├── __init__.py
├── analysis.py        # NDVI and other analysis routines
├── data_loader.py     # Input/output helpers for raster data
├── pipeline.py        # Command line pipeline
└── polygon.py         # Placeholder for polygon support
```

## Data requirements

- Sentinel/Landsat like bands saved as individual GeoTIFF files
- A QA band from which clouds can be detected
- A raster of training labels for model fitting

## Usage

1. Run `cloudmask.py` to derive a boolean mask of clouds from the QA band.
2. Use `stack_bands.py` to create a cloud-masked stack of bands.
3. Compute NDVI and NDWI features with `features.py`.
4. Train a RandomForest model using `train_model.py` and your label raster.
5. Apply the model with `predict.py` to generate a classification raster.
6. View results in a Streamlit app (`app.py`).

## Running the pipeline

The `remote_sensing.pipeline` module exposes a `run_pipeline` function and a simple CLI. It expects preprocessed NumPy arrays for the red and near-infrared bands.

```bash
python -m remote_sensing.pipeline path/to/red.npy path/to/nir.npy path/to/out.npy
```

This will produce an NDVI array saved to the provided output path.

## Future work

- Implement real raster loading and saving using libraries such as `rasterio`.
- Integrate polygon data via `remote_sensing.polygon` to mask areas or join with external datasets.
- Extend the analysis for asset value estimation or other domain specific metrics.

Feel free to adapt the modules or add new ones to suit your workflow.

