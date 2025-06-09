#!/usr/bin/env python
"""Download Sentinel data into the data/raw directory with caching."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Tuple

from sentinelsat import SentinelAPI


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
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--satellite", default="Sentinel-2", help="Satellite platform name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = build_output_dir(args.satellite, args.lat, args.lon, args.start, args.end)

    if any(out_dir.iterdir()):
        print(f"Using cached data in {out_dir}")
        return

    user = os.getenv("SENTINEL_USER")
    password = os.getenv("SENTINEL_PASSWORD")
    if not user or not password:
        raise RuntimeError("Set SENTINEL_USER and SENTINEL_PASSWORD environment variables")

    api = SentinelAPI(user, password, "https://scihub.copernicus.eu/dhus")
    footprint = f"POINT({args.lon} {args.lat})"
    products = api.query(
        footprint,
        date=(args.start, args.end),
        platformname=args.satellite,
        processinglevel="Level-2A",
    )

    if not products:
        print("No products found for given parameters")
        return

    api.download_all(products, directory_path=str(out_dir))
    print(f"Downloaded {len(products)} product(s) to {out_dir}")


if __name__ == "__main__":
    main()
