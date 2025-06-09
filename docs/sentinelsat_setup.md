# Using Sentinelsat

This project uses **sentinelsat** to download Sentinel imagery from the Copernicus Open Access Hub. You need a valid account in order to authenticate.

1. Visit <https://scihub.copernicus.eu/dhus/#/self-registration> and create an account.
2. After registration, note your username and password.
3. Set them as environment variables before running `download_sentinel.py`:

```bash
export SENTINEL_USER=<your username>
export SENTINEL_PASSWORD=<your password>
```

The script will cache downloaded products under `data/raw/<SATELLITE>` based on the provided coordinates and date range. Subsequent runs with the same parameters will reuse the cached files.
