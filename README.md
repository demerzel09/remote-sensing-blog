# remote-sensing-blog

This project is licensed under the MIT License.

## 日本語の説明

このプロジェクトはリモートセンシングデータを用いた簡単な分類ワークフローを示します。必要なデータは複数バンドのGeoTIFFとSCL・dataMaskバンド、学習用ラベルです。

1. `cloudmask.py` でSCL/dataMaskから雲マスクを作成します。
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
シーン分類(`SCL`)・データマスク(`MASK`) バンド、学習用ラベル(`labels.tif`) を配置します。

```bash
data/raw/
├── B02.tif
├── B03.tif
├── B04.tif
├── B08.tif
├── B11.tif
├── SCL.tif
├── MASK.tif
└── labels.tif
```

### 学習用ラベル `labels.tif`

モデルの学習には入力画像と同じ範囲・解像度を持つラベルラスタ `labels.tif` が必要です。
このファイルはリポジトリには含まれていません。ユーザー自身で作成するか外部ソースから入手してください。
外部ソースから入手する場合は次の「WorldCover からラベルを作成する」を参照してください。

#### WorldCover タイルをダウンロードする

ESA の **WorldCover** データセットの一部を取得する例として、
`scripts/worldcover_to_labels.sh` は `src/utils/download_worldcover_datasets.py` を
呼び出します。デフォルトでは九州周辺をカバーする緯度経度範囲
`30 129 34 132` を指定し、2021 年版 (`v200/2021/map/`) のタイルを
`data/wc2021_kyusyu_bbox` 以下に保存します。

```bash
bash scripts/worldcover_to_labels.sh
```

#### WorldCover タイルだけを取得する

特定地域の WorldCover タイルをまとめてダウンロードしたい場合は
`src/utils/download_worldcover_datasets.py` を使用します。国名を指定する
`--country` オプション、または緯度経度で範囲を与える `--bbox` オプション
のいずれかを指定してください。

```bash
# 国単位で取得
python -m src.utils.download_worldcover_datasets \
    --country Japan --output data/worldcover

# 緯度経度範囲を指定
python -m src.utils.download_worldcover_datasets \
    --bbox 34 135 36 138 --output data/worldcover
```

バージョンは `--version` で `v100/2020/map/` または `v200/2021/map/` を選択
できます（デフォルトは `v100/2020/map/`）。

### 3. Sentinel-2 土地利用分類の実行と表示

まず以下のコマンドで分類を実行してラスタを生成します。

```bash
python -m src.classification.pipeline \
  --bands data/raw/B02.tif data/raw/B03.tif data/raw/B04.tif data/raw/B08.tif data/raw/B11.tif \
  --scl data/raw/SCL.tif \
  --mask data/raw/MASK.tif \
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

Python 3.10 or higher is required because the code uses new union type
annotations such as `str | Path`.



## Structure

```
remote_sensing/
├── __init__.py
├── analysis.py        # NDVI and other analysis routines
├── data_loader.py     # Input/output helpers for raster data
├── pipeline.py        # Command line pipeline
└── polygon.py         # Placeholder for polygon support
```

`src/` contains the main raster classification workflow built on top of
`rasterio`. The `remote_sensing/` folder is a small example that works with raw
NumPy arrays only.

| Package | Purpose |
| ------- | ------- |
| `src/` | Full raster-based classification pipeline |
| `remote_sensing/` | Minimal NDVI example using NumPy |

## Data requirements

- Sentinel/Landsat like bands saved as individual GeoTIFF files
- ``SCL`` and optional ``dataMask`` bands to detect clouds
- A raster of training labels for model fitting

### Automated Sentinel‑2 download

You can fetch sample imagery directly from the Copernicus Data Space using
`src/utils/download_sentinel.py`. The script relies on **sentinelhub-py** and
queries the `https://sh.dataspace.copernicus.eu` service. Downloads are cached
under `data/raw/<OUTPUT>/<SATELLITE>/<lat_lon_dates>` based on location and time range. For the
example scripts this becomes `data/raw/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31`.
The directory also contains a copy of `download.yaml` which later steps read to
determine which bands were saved.

> **Note**
> The download scripts require outbound HTTPS access to
> `sh.dataspace.copernicus.eu`. Connection issues such as timeouts or "No route to host"
> usually mean your network is restricted. Configure a proxy if needed.

```bash
export SENTINELHUB_CLIENT_ID=<your client id>
export SENTINELHUB_CLIENT_SECRET=<your client secret>
python -m src.utils.download_sentinel \
  --lat 35.6 \
  --lon 139.7 \
  --start 2024-01-01 \
  --end 2024-01-31 \
  --buffer 0.005 \
  --split-bands
```

The `--buffer` option (or a `buffer` field in `download.yaml`) sets how wide the
bounding box around the coordinate should be. Add `--split-bands` (or set
`split_bands: true` in `download.yaml`) to store each band as its own TIFF
instead of the default `BANDS.tif` stack.

If the target folder already exists the previously downloaded data will be
reused.

See [docs/sentinelhub_setup.md](docs/sentinelhub_setup.md) for details on
creating an account and setting these variables.

## Usage

1. Run `cloudmask.py` to derive a boolean mask of clouds from the SCL/dataMask bands.
2. Use `stack_bands.py` to create a cloud-masked stack of bands.
3. Compute NDVI and NDWI features with `features.py`.
4. Train a RandomForest model using `train_model.py` and your label raster.
5. Apply the model with `predict.py` to generate a classification raster.
6. View results in a Streamlit app (`app.py`).

For a one-shot workflow using Sentinel‑2 bands you can also execute:

```bash
python -m src.classification.pipeline --help
```

### Config based Sentinel-2 workflow

Each processing step accepts a YAML configuration file and writes a copy of
that file into its output directory for reference. Example configs are in the
`configs/` directory. Run the full workflow with:

```bash
bash scripts/run_sentinel2_pipeline.sh
```

Individual steps can also be executed via the helper scripts in `scripts/`:

```bash
bash scripts/download_sentinel2.sh
bash scripts/preprocess_sentinel2.sh
bash scripts/train_model.sh
bash scripts/predict_sentinel2.sh
```
`preprocess_sentinel2.sh` が出力する `features.npz` はダウンロードディレクトリ内の
`preprocess/` サブフォルダに保存されます。`train_model.sh` はこの場所から特徴量を読み込みます。



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

