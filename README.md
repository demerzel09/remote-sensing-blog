# remote-sensing-blog

This project provides a small remote sensing workflow for generating land cover classifications. Example scripts are located in the `src` directory and require multi-band raster data and a QA band containing cloud information.

## Directory layout

```
project_root/
├── data/             # input rasters and training labels
├── outputs/          # generated models and prediction rasters
├── src/              # processing modules
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

## 日本語の説明

このプロジェクトはリモートセンシングデータを用いた簡単な分類ワークフローを示します。必要なデータは複数バンドのGeoTIFFと雲判定用のQAバンド、学習用ラベルです。

1. `cloudmask.py` でQAバンドから雲マスクを作成します。
2. `stack_bands.py` でマスクを適用したバンドスタックを作成します。
3. `features.py` でNDVI・NDWIを計算します。
4. `train_model.py` でRandomForest分類器を学習させます。
5. `predict.py` で分類結果ラスタを生成します。
6. `app.py` をStreamlitで実行し、folium地図上で結果を確認できます。
