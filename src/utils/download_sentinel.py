#!/usr/bin/env python
"""Download Sentinel-2 imagery using sentinelhub-py."""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

import yaml
from datetime import datetime
from sentinelhub import (
    SHConfig,
    SentinelHubCatalog,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    BBox,
    CRS,
    bbox_to_dimensions,
)


def normalize_date(value: str) -> str:
    """Return date in YYYY-MM-DD format."""
    if "-" in value:
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            pass
    return datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")


def build_output_dir(satellite: str, lat: float, lon: float, start: str, end: str) -> Path:
    """Construct output directory based on query parameters."""
    base = Path("data/raw") / satellite
    loc = f"{lat:.4f}_{lon:.4f}"
    name = f"{loc}_{start}_{end}"
    out_dir = base / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Sentinel imagery")
    parser.add_argument("--config", help="YAML config with lat/lon/date params")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--start", help="Start date YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--end", help="End date YYYY-MM-DD or YYYYMMDD")
    parser.add_argument("--satellite", default="Sentinel-2", help="Platform name")
    parser.add_argument("--output", help="Output directory")
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


BANDS = ["B02", "B03", "B04", "B08", "B11", "QA60"]


def download_sentinel(
    lat: float,
    lon: float,
    start: str,
    end: str,
    satellite: str = "Sentinel-2",
    out_dir: str | Path | None = None,
    buffer: float = 0.005,
    resolution: int = 10,
) -> Path:
    """Download selected bands using sentinelhub."""
    if out_dir is None:
        out_dir = build_output_dir(satellite, lat, lon, start, end)
    else:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    if any(out_dir.iterdir()):
        print(f"Using cached data in {out_dir}")
        return out_dir

    client_id = os.getenv("SENTINELHUB_CLIENT_ID")
    client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET environment variables"
        )

    config = SHConfig()
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret

    bbox = BBox(
        (lon - buffer, lat - buffer, lon + buffer, lat + buffer), crs=CRS.WGS84
    )
    catalog = SentinelHubCatalog(config=config)
    search = catalog.search(
        DataCollection.SENTINEL2_L2A, bbox=bbox, time=(start, end), fields={"include": ["id"]}
    )
    if not list(search):
        print("No products found for given parameters")
        return out_dir

    size = bbox_to_dimensions(bbox, resolution=resolution)

    for band in BANDS:
        evalscript = f"""
        //VERSION=3
        function setup() {{
            return {{
                input: [{{bands: [\"{band}\"], units: \"DN\"}}],
                output: {{bands: 1, sampleType: \"UINT16\"}}
            }};
        }}
        function evaluatePixel(sample) {{
            return [sample.{band}];
        }}
        """
        request = SentinelHubRequest(
            data_folder=str(out_dir),
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=(start, end),
                )
            ],
            responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
            bbox=bbox,
            size=size,
            config=config,
        )
        request.get_data(save_data=True)
        saved = Path(request.get_filename_list()[0])
        (out_dir / f"{band}.tif").write_bytes(saved.read_bytes())
        saved.unlink()

    print(f"Downloaded {len(BANDS)} band TIFFs to {out_dir}")
    return out_dir


def download_from_config(
    config_path: str | Path, output_dir: str | Path | None = None
) -> Path:
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
        args.lat, args.lon, args.start, args.end, args.satellite, args.output
    )
    if args.config:
        shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
