#!/usr/bin/env python
"""Download Sentinel data into the data/raw directory with caching."""

from __future__ import annotations

import argparse
import os
import shutil
import yaml
from pathlib import Path

from datetime import datetime
from sentinelsat import SentinelAPI


def normalize_date(value: str) -> str:
    """Return date in YYYYMMDD format."""
    if "-" in value:
        try:
            return datetime.strptime(value, "%Y-%m-%d").strftime("%Y%m%d")
        except ValueError:
            pass
    return value


def build_output_dir(satellite: str, lat: float, lon: float, start: str, end: str) -> Path:
    """Construct and create an output directory based on query parameters."""
    base = Path("data/raw") / satellite
    # limit decimals to 4 places to keep path short and consistent
    loc = f"{lat:.4f}_{lon:.4f}"
    name = f"{loc}_{start}_{end}"
    out_dir = base / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Sentinel imagery with caching")
    parser.add_argument("--config", help="YAML config file with download parameters")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--start", help="Start date YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--end", help="End date YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--satellite", default="Sentinel-2", help="Satellite platform name")
    parser.add_argument("--output", help="Output directory for downloaded data")
    args = parser.parse_args()
    if args.config:
        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        args.lat = cfg["lat"]
        args.lon = cfg["lon"]
        args.start = cfg["start"]
        args.end = cfg["end"]
        args.satellite = cfg.get("satellite", args.satellite)
    if None in {args.lat, args.lon, args.start, args.end}:
        parser.error("lat, lon, start and end must be provided")
    return args


def download_sentinel(
    lat: float,
    lon: float,
    start: str,
    end: str,
    satellite: str = "Sentinel-2",
    out_dir: str | Path | None = None,
) -> Path:
    """Download Sentinel products and return the output directory."""
    if out_dir is None:
        out_dir = build_output_dir(satellite, lat, lon, start, end)
    else:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    if any(out_dir.iterdir()):
        print(f"Using cached data in {out_dir}")
        return out_dir

    user = os.getenv("SENTINEL_USER")
    password = os.getenv("SENTINEL_PASSWORD")
    if not user or not password:
        raise RuntimeError("Set SENTINEL_USER and SENTINEL_PASSWORD environment variables")

    api = SentinelAPI(user, password, "https://scihub.copernicus.eu/dhus")
    footprint = f"POINT({lon} {lat})"
    norm_start = normalize_date(start)
    norm_end = normalize_date(end)
    products = api.query(
        footprint,
        date=(norm_start, norm_end),
        platformname=satellite,
        processinglevel="Level-2A",
    )

    if not products:
        print("No products found for given parameters")
        return out_dir

    api.download_all(products, directory_path=str(out_dir))
    print(f"Downloaded {len(products)} product(s) to {out_dir}")
    return out_dir


def download_from_config(config_path: str | Path, output_dir: str | Path | None = None) -> Path:
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    return download_sentinel(
        lat=cfg["lat"],
        lon=cfg["lon"],
        start=cfg["start"],
        end=cfg["end"],
        satellite=cfg.get("satellite", "Sentinel-2"),
        out_dir=output_dir,
    )


def main() -> None:
    args = parse_args()
    out_dir = download_sentinel(
        args.lat,
        args.lon,
        args.start,
        args.end,
        args.satellite,
        out_dir=args.output,
    )
    if args.config:
        shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
