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
Downloads Sentinel imagery from the Copernicus Open Access Hub.
It caches files inside `data/raw/<SATELLITE>` based on the selected location and
 date range.

Example usage:

```bash
export SENTINEL_USER=<your username>
export SENTINEL_PASSWORD=<your password>
python scripts/download_sentinel.py --lat 35.6 --lon 139.7 --start 2024-01-01 --end 2024-01-31
```
