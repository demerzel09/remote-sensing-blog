# Copernicus Data Space authentication

The downloader uses **sentinelhub-py** which requires OAuth credentials.
Create a free account at <https://dataspace.copernicus.eu/> and generate an
application to obtain a client ID and secret.

1. Visit <https://dataspace.copernicus.eu/> and register.
2. In the dashboard create a new OAuth client and note its ID and secret.
3. Export them before running `download_sentinel.py` (or pass via CLI):

```bash
export SENTINELHUB_CLIENT_ID=<your client id>
export SENTINELHUB_CLIENT_SECRET=<your client secret>
```

Alternatively provide `--sh-base-url` and `--sh-token-url` when running
`download_sentinel.py` or the pipeline downloader to override these endpoints
without setting environment variables.

Downloads are cached under `data/raw/<OUTPUT>/<SATELLITE>/<lat_lon_dates>` based on the selected
location and date range. For instance the example scripts store files in
`data/raw/example_run/Sentinel-2/35.6000_139.7000_2024-01-01_2024-01-31`. Each folder includes
the original `download.yaml` which the preprocessing step reads back to locate
the bands. Requests are sent to `https://sh.dataspace.copernicus.eu`. If the
directory already exists the cached files will be reused.
Specify `max_cloud` in the YAML (or `--max-cloud` via CLI) to only download
scenes below that cloud cover percentage.

> **Note**
> Network access to `sh.dataspace.copernicus.eu` is required. Configure a proxy
> if your environment restricts outbound HTTPS connections.
