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
```

Specify `--buffer` or add a `buffer` field in a YAML config to control the
width of the downloaded area in degrees.

Use `--sh-base-url` and `--sh-token-url` to override the service and
authentication endpoints instead of the environment variables.

Pass the bands to download with `--bands` or a `bands:` array in the YAML
configuration. Bands are specified by their short identifiers such as `B02`.
When omitted, the default list (`B02`, `B03`, `B04`, `B08`, `B11`, `SCL`,
`dataMask`) is used.

## `run_sentinel2_pipeline.sh`
A helper script that runs the full Sentinel-2 workflow using the configuration
files stored in `configs/`. Each pipeline step copies its YAML configuration
into the corresponding output folder so parameters are recorded alongside the
results.

```bash
bash scripts/run_sentinel2_pipeline.sh
```
