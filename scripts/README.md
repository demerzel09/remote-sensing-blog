# Utility scripts

This folder contains helper scripts for environment setup and data download.

## `setup_env.sh`
Creates a Python virtual environment under `venv/` and installs the packages listed in `requirements.txt`.
Run:

```bash
bash scripts/setup_env.sh
```

Activate the environment afterwards with:

```bash
source venv/bin/activate
```

## `download_sentinel.py`
Downloads Sentinel imagery from the Copernicus Data Space using the
`sentinelhub` service at `https://sh.dataspace.copernicus.eu`.
The module resides under `src/utils/` and caches files inside
`data/raw/<OUTPUT>/<SATELLITE>/<lat_lon_dates>` based on the selected location
and date range. When using `scripts/download_sentinel2.sh` this resolves to
`data/raw/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31`. The
generated folder also contains the used `download.yaml`, which
`preprocess_sentinel2.sh` reads to find the downloaded bands. When
run with a YAML configuration, the file is copied into the download directory for
future reference.

Example usage:

```bash
export SENTINELHUB_CLIENT_ID=<your client id>
export SENTINELHUB_CLIENT_SECRET=<your client secret>
export SH_BASE_URL=https://sh.dataspace.copernicus.eu
export SH_TOKEN_URL=https://identity.dataspace.copernicus.eu
python -m src.utils.download_sentinel \
  --lat 35.6 --lon 139.7 --start 2024-01-01 --end 2024-01-31 \
  --buffer 0.005
  --max-cloud 20
```

Specify `--buffer` or add a `buffer` field in a YAML config to control the
width of the downloaded area in degrees.
Use `--max-cloud` or `max_cloud:` in the YAML to filter scenes by cloud
percentage.

Use `--sh-base-url` and `--sh-token-url` to override the service and
authentication endpoints instead of the environment variables.

Pass the bands to download with `--bands` or a `bands:` array in the YAML
configuration. Bands are specified by their short identifiers such as `B02`.
When omitted, the default list (`B02`, `B03`, `B04`, `B08`, `B11`, `SCL`,
`dataMask`) is used.

Set `--zip-output` or `zip_output: true` in `download.yaml` to compress the
download folder after all scenes are retrieved. Use
`src/utils/mosaic_scenes.py` on the extracted archive to merge the dated
subfolders back into single-band images.

## `cloud_free_sentinel2.sh` and `mosaic_sentinel2.sh`
After downloading scenes you can remove cloudy pixels in each dated folder with
`cloud_free_sentinel2.sh`. The script invokes `src.pipeline.cloud_free` on the
download directory. Afterwards combine all dates into a single stack with
`mosaic_sentinel2.sh` which runs `src.pipeline.mosaic`.

## `run_sentinel2_pipeline.sh`
A helper script that runs the full Sentinel-2 workflow using the configuration
files stored in `configs/`. Each pipeline step copies its YAML configuration
into the corresponding output folder so parameters are recorded alongside the
results.

```bash
bash scripts/run_sentinel2_pipeline.sh
```

## `worldcover_to_labels.sh`
Downloads ESA WorldCover tiles using `src/utils/download_worldcover_datasets.py`.
The default parameters fetch 2021 tiles covering the Kyushu region of Japan
(`--bbox 30 129 34 132 --version v200/2021/map/`) and store them under
`data/wc2021_kyusyu_bbox`.

## `worldcover_to_label.py`
Cropping the downloaded tiles to match a Sentinel‑2 scene can be done with the
`src.utils.worldcover_to_label` command. Provide the tile directory and the
Sentinel download folder containing `download.yaml`:

```bash
python -m src.utils.worldcover_to_label \
  --worldcover data/wc2021_kyusyu_bbox \
  --sentinel-dir data/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31
```
