# Copernicus Data Space authentication

The downloader uses **sentinelhub-py** which requires OAuth credentials.
Create a free account at <https://dataspace.copernicus.eu/> and generate an
application to obtain a client ID and secret.

1. Visit <https://dataspace.copernicus.eu/> and register.
2. In the dashboard create a new OAuth client and note its ID and secret.
3. Export them before running `download_sentinel.py`:

```bash
export SENTINELHUB_CLIENT_ID=<your client id>
export SENTINELHUB_CLIENT_SECRET=<your client secret>
export SH_BASE_URL=https://sh.dataspace.copernicus.eu
export SH_AUTH_BASE_URL=https://identity.dataspace.copernicus.eu
```

Downloads are cached under `data/raw/<SATELLITE>` based on the selected
location and date range. Requests are sent to
`https://sh.dataspace.copernicus.eu`. If the directory already exists the
cached files will be reused.

> **Note**
> Network access to `sh.dataspace.copernicus.eu` is required. Configure a proxy
> if your environment restricts outbound HTTPS connections.
