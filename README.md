# remote-sensing-blog


## 日本語の説明

このプロジェクトはリモートセンシングデータを用いた簡単な分類ワークフローを示します。必要なデータは複数バンドのGeoTIFFと雲判定用のQAバンド、学習用ラベルです。

1. `cloudmask.py` でQAバンドから雲マスクを作成します。
2. `stack_bands.py` でマスクを適用したバンドスタックを作成します。
3. `features.py` でNDVI・NDWIを計算します。
4. `train_model.py` でRandomForest分類器を学習させます。
5. `predict.py` で分類結果ラスタを生成します。
6. `app.py` をStreamlitで実行し、folium地図上で結果を確認できます。

## Directory layout

```
data/
    raw/        # Original satellite downloads and label rasters
    processed/  # Intermediate files generated during processing
notebooks/      # Exploratory notebooks
scripts/        # Utility scripts such as data download helpers
outputs/        # Final prediction rasters and reports
```

Raw GeoTIFFs and labels should be stored in `data/raw/`. Intermediate files
written by the pipeline can be kept under `data/processed/`.

## Sentinel-2 を用いた土地利用分類

`data/raw/` フォルダに以下の Sentinel-2 バンド (`B02`, `B03`, `B04`, `B08`, `B11`) と
QA バンド(`QA60`)、学習用ラベル(`labels.tif`) を配置します。

```bash
data/raw/
├── B02.tif
├── B03.tif
├── B04.tif
├── B08.tif
├── B11.tif
├── QA60.tif
└── labels.tif
```

### 3. ランドサット・土地利用分類の実行と表示

まず以下のコマンドで分類を実行してラスタを生成します。

```bash
python -m src.classification.pipeline \
  --bands data/raw/B02.tif data/raw/B03.tif data/raw/B04.tif data/raw/B08.tif data/raw/B11.tif \
  --qa data/raw/QA60.tif \
  --labels data/raw/labels.tif \
  --output outputs/prediction.tif
```

生成された `outputs/prediction.tif` を表示するには次のコマンドを実行します。

```bash
streamlit run src/app.py
```

This repository contains a minimal example of a Python pipeline for basic remote sensing analysis. The code is structured for future extensions such as polygon data integration and asset value analysis.

## Installation
Use the helper script to create a virtual environment and install the dependencies:

```bash
bash scripts/setup_env.sh
```



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

### Automated Sentinel‑2 download

You can fetch sample imagery directly from the Copernicus Open Access Hub using
`scripts/download_sentinel.py`. The script caches downloads under
`data/raw/<SATELLITE>` based on location and time range.

```bash
export SENTINEL_USER=<your username>
export SENTINEL_PASSWORD=<your password>
python scripts/download_sentinel.py \
  --lat 35.6 \
  --lon 139.7 \
  --start 2024-01-01 \
  --end 2024-01-31
```

If the target folder already exists the previously downloaded data will be
reused.

## Usage

1. Run `cloudmask.py` to derive a boolean mask of clouds from the QA band.
2. Use `stack_bands.py` to create a cloud-masked stack of bands.
3. Compute NDVI and NDWI features with `features.py`.
4. Train a RandomForest model using `train_model.py` and your label raster.
5. Apply the model with `predict.py` to generate a classification raster.
6. View results in a Streamlit app (`app.py`).

For a one-shot workflow using Sentinel‑2 bands you can also execute:

```bash
python -m src.classification.pipeline --help
```


## Running the pipeline

Before executing the pipeline make sure the environment is ready:

```bash
bash scripts/setup_env.sh
```

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

