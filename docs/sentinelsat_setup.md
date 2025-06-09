# Using Sentinelsat

This project uses **sentinelsat** to download Sentinel imagery from the Copernicus Data Space Ecosystem. You need a valid account in order to authenticate.

1. Visit <https://shapps.dataspace.copernicus.eu/dashboard/#/> and sign up for an account.
2. After registration, note your username and password.
3. Set them as environment variables before running `download_sentinel.py`:

```bash
export SENTINEL_USER=<your username>
export SENTINEL_PASSWORD=<your password>
```

The script will cache downloaded products under `data/raw/<SATELLITE>` based on the provided coordinates and date range. Subsequent runs with the same parameters will reuse the cached files.

> **Note**
> Downloads are performed over HTTPS to `apihub.copernicus.eu`. If you
> experience timeouts or errors like "No route to host", your environment
> might block outbound connections. Configure network access or use an
> HTTPS proxy if necessary.
