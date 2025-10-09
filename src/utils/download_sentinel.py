#!/usr/bin/env python
"""Download Sentinel-2 imagery using sentinelhub-py."""
from __future__ import annotations

import argparse
import os
import shutil
import tarfile
from pathlib import Path

import yaml
import rasterio
import numpy as np
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
from oauthlib.oauth2.rfc6749.errors import InvalidClientError
import sys

SH_BASE_URL="https://sh.dataspace.copernicus.eu"
SH_TOKEN_URL="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

#BANDS = ["B02", "B03", "B04", "B08", "B11", "QA60"] # Sentinel-2 L1C bands
DEFAULT_BANDS = ["B02", "B03", "B04", "B08", "B11", "SCL", "dataMask"] # Sentinel-2 L2A bands

# QA60 is L1C cloud mask, not available in L2A
# SCL is L2A scene classification
# CLP is L2A cloud probability.but not available in L2A CDSE
# dataMask is L2A data mask (valid pixels)
# This repository derives cloud masks from the SCL and dataMask bands.

def split_band_stack(stack_path: Path, bands: list[str]) -> None:
    """Split a multi-band GeoTIFF into separate single-band files."""
    with rasterio.open(stack_path) as src:
        meta = src.meta.copy()
        if src.count < len(bands):
            raise ValueError("Band stack has fewer layers than expected")
        for i, name in enumerate(bands, 1):
            meta.update(count=1)
            out = stack_path.parent / f"{name}.tif"
            with rasterio.open(out, "w", **meta) as dst:
                dst.write(src.read(i), 1)

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
    base = Path(satellite)
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
    parser.add_argument("--bands", nargs="+", help="Bands to request")
    parser.add_argument("--output", help="Output directory")
    parser.add_argument(
        "--name",
        help="Optional folder name created under the satellite directory",
    )
    parser.add_argument("--buffer", type=float, default=0.005, help="BBox buffer in degrees")
    parser.add_argument("--max-cloud", type=float, default=None, help="Maximum cloud cover percentage")
    parser.add_argument("--min-valid", type=float, default=None, help="Minimum percent of valid pixels")
    parser.add_argument("--zip-output", action="store_true", help="Create ZIP archive of output directory")
    parser.add_argument(
        "--sh-base-url",
        default=SH_BASE_URL,
        type=str,
        help="Sentinel Hub service URL",
    )
    parser.add_argument(
        "--sh-token-url",
        default=SH_TOKEN_URL,
        type=str,
        help="Sentinel Hub auth URL",
    )
    args = parser.parse_args()
    if args.config:
        with open(args.config) as f:
            cfg = yaml.safe_load(f)
        args.lat = cfg["lat"]
        args.lon = cfg["lon"]
        args.start = cfg["start"]
        args.end = cfg["end"]
        args.satellite = cfg.get("satellite", args.satellite)
        args.buffer = cfg.get("buffer", args.buffer)
        args.max_cloud = cfg.get("max_cloud", args.max_cloud)
        args.min_valid = cfg.get("min_valid", args.min_valid)
        args.zip_output = cfg.get("zip_output", args.zip_output)
        args.name = cfg.get("name", args.name)
    if None in {args.lat, args.lon, args.start, args.end}:
        parser.error("lat, lon, start and end must be provided")
    if args.bands is None:
        args.bands = DEFAULT_BANDS
    return args


def download_sentinel(
    lat: float,
    lon: float,
    start: str,
    end: str,
    satellite: str = "Sentinel-2",
    out_dir: str | Path | None = None,
    name: str | None = None,
    buffer: float = 0.005,
    resolution: int = 10,
    sh_base_url: str | None = None,
    sh_token_url: str | None = None,
    bands: list[str] | None = None,
    max_cloud: float | None = None,
    min_valid: float | None = None,
    zip_output: bool = False,
) -> Path:
    """Download selected bands using sentinelhub."""
    if bands is None:
        bands = DEFAULT_BANDS
    if name:
        sub_dir = Path(satellite) / name
    else:
        sub_dir = build_output_dir(satellite, lat, lon, start, end)
    out_dir = Path(out_dir).joinpath(sub_dir) if out_dir else sub_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    client_id = os.getenv("SENTINELHUB_CLIENT_ID")
    client_secret = os.getenv("SENTINELHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Set SENTINELHUB_CLIENT_ID and SENTINELHUB_CLIENT_SECRET environment variables"
        )

    config = SHConfig()
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    # Use Copernicus Data Space unless overridden
    config.sh_base_url = sh_base_url
    # Authentication uses the identity service
    config.sh_token_url  = sh_token_url
    # CDSE 用コレクション (service_url=None)  ### changed ###
    S2_CDSE = DataCollection.SENTINEL2_L2A.define_from(
        name="SENTINEL2_L2A_CDSE",      # 任意の名前
        service_url=None               # ← ここを None に
    )

    bbox = BBox(
        (lon - buffer, lat - buffer, lon + buffer, lat + buffer), crs=CRS.WGS84
    )
    catalog = SentinelHubCatalog(config=config)
    print(config.sh_base_url)
    print(S2_CDSE.service_url)

    cloud_filter = None
    if max_cloud is not None:
        cloud_filter = f"eo:cloud_cover <= {max_cloud}"

    try:
        search = catalog.search(
            S2_CDSE,
            bbox=bbox,
            time=(start, end),
            filter=cloud_filter,
            fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"]},
            limit=50
        )
    except InvalidClientError:
        raise RuntimeError("認証失敗: CLIENT_ID / SECRET / URL を確認してください")

    print(f"search = {search.get_ids()}")
    items = list(search)
    print(f"search len = {len(items)}")
    if not items:
        sys.exit("⚠️  指定期間・範囲にシーンがありません")

    # Build evalscript dynamically based on selected bands
    spectral = [b for b in bands if b not in {"SCL", "dataMask"}]
    parts = []
    parts.append("//VERSION=3")
    parts.append("function setup() {")
    parts.append("  return {")
    input_list = ",".join(f'\"{b}\"' for b in bands)
    parts.append(f"    input: [{{ bands: [{input_list}] }}],")
    outputs = []
    outputs.append(
        f"      {{ id:\"default\", bands:{len(spectral)}, sampleType:\"FLOAT32\" }}"
    )
    if 'SCL' in bands:
        outputs.append("      { id:\"SCL\",     bands:1, sampleType:\"UINT8\"  }")
    if 'dataMask' in bands:
        outputs.append("      { id:\"MASK\",    bands:1, sampleType:\"UINT8\"  }")
    parts.append("    output: [")
    parts.append(",\n".join(outputs))
    parts.append("    ]")
    parts.append("  }")
    parts.append("}")
    parts.append("function evaluatePixel(s) {")
    lines = []
    lines.append(f"      default:[{','.join(f's.{b}' for b in spectral)}]")
    if 'SCL' in bands:
        lines.append("      SCL:[s.SCL]")
    if 'dataMask' in bands:
        lines.append("      MASK:[s.dataMask]")
    parts.append("  return {")
    parts.append(",\n".join(lines))
    parts.append("  };")
    parts.append("}")
    evalscript = "\n".join(parts)

    responses = [SentinelHubRequest.output_response("default", MimeType.TIFF)]
    if "SCL" in bands:
        responses.append(SentinelHubRequest.output_response("SCL", MimeType.TIFF))
    if "dataMask" in bands:
        responses.append(SentinelHubRequest.output_response("MASK", MimeType.TIFF))

    size = bbox_to_dimensions(bbox, resolution=resolution)

    results = []
    for item in items:
        dt_str = item["properties"]["datetime"]
        dt = datetime.fromisoformat(dt_str.replace("Z", ""))
        date_dir = out_dir / dt.strftime("%Y-%m-%dT%H%M%S")
        bands_file = date_dir / "BANDS.tif"
        if bands_file.exists():
            print(f"Skipping {dt_str}: {bands_file} already exists")
            continue
        date_dir.mkdir(parents=True, exist_ok=True)

        print(f"date_dir")


        request = SentinelHubRequest(
            data_folder=str(date_dir),
            evalscript=evalscript,
            input_data=[SentinelHubRequest.input_data(
                data_collection=S2_CDSE,
                time_interval=(dt_str, dt_str),
            )],
            responses=responses,
            bbox=bbox,
            size=size,
            config=config,
        )

        print(f"Downloading imagery for {dt_str} …")
        try:
            request.get_data(save_data=True)
        except InvalidClientError:
            sys.exit("❌  認証に失敗しました")

        # ----- Downloaded file handling -----
        file_path = Path(request.data_folder) / request.get_filename_list()[0]
        suffix = file_path.suffix.lower()

        if suffix == ".tar":
            with tarfile.open(file_path) as tar:
                tar.extractall(path=date_dir)

            (date_dir / "default.tif").rename(date_dir / "BANDS.tif")

            file_path.unlink()
        elif suffix in {".tif", ".tiff"}:
            shutil.move(str(file_path), date_dir / "BANDS.tif")
        else:
            sys.exit(f"❌  予期しないファイル形式: {file_path.name}")

        if min_valid is not None and "dataMask" in bands:
            mask_file = date_dir / "MASK.tif"
            if mask_file.exists():
                with rasterio.open(mask_file) as src:
                    dm = src.read(1)
                valid_pct = np.count_nonzero(dm) / dm.size * 100
                if valid_pct < min_valid:
                    print(f"Skipping {dt_str}: {valid_pct:.1f}% valid pixels")
                    shutil.rmtree(date_dir)
                    continue

        split_band_stack(date_dir / "BANDS.tif", spectral)
        results.append(date_dir)

    print(f"✅  Saved GeoTIFFs to {out_dir}")
    if zip_output:
        archive = shutil.make_archive(str(out_dir), "zip", root_dir=out_dir)
        print(f"Archived to {archive}")
    return out_dir


def download_from_config(
    config_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    sh_base_url: str | None = None,
    sh_token_url: str | None = None,
    name: str | None = None,
) -> Path:
    cfg = yaml.safe_load(Path(config_path).read_text())
    return download_sentinel(
        lat=cfg["lat"],
        lon=cfg["lon"],
        start=cfg["start"],
        end=cfg["end"],
        satellite=cfg.get("satellite", "Sentinel-2"),
        buffer=cfg.get("buffer", 0.005),
        out_dir=output_dir,
        name=name or cfg.get("name"),
        sh_base_url=sh_base_url,
        sh_token_url=sh_token_url,
        bands=cfg.get("bands", DEFAULT_BANDS),
        max_cloud=cfg.get("max_cloud"),
        min_valid=cfg.get("min_valid"),
        zip_output=cfg.get("zip_output", False),
    )


def main() -> None:
    args = parse_args()
    out_dir = download_sentinel(
        args.lat,
        args.lon,
        args.start,
        args.end,
        args.satellite,
        args.output,
        name=args.name,
        buffer=args.buffer,
        sh_base_url=args.sh_base_url,
        sh_token_url=args.sh_token_url,
        bands=args.bands,
        max_cloud=args.max_cloud,
        min_valid=args.min_valid,
        zip_output=args.zip_output,
    )
    if args.config:
        # Store the configuration under a standard name so other
        # commands can easily locate it later.
        shutil.copy(args.config, Path(out_dir) / "download.yaml")


if __name__ == "__main__":
    main()
