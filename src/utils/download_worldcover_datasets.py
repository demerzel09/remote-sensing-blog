#!/usr/bin/env python3
import os
import argparse
import boto3
from botocore import UNSIGNED
from botocore.client import Config
import geopandas as gpd
import requests
import zipfile
import io
import shutil
from shapely.geometry import box


def get_tiles_for_country(country: str, tile_size: int = 3) -> list:
    """
    3x3度タイルID（例: 'N30E120'）のリストを返す。
    指定国の境界と重なるタイルを抽出。
    """
    # Natural Earth 国境データをダウンロード・展開
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    resp = requests.get(url)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        z.extractall("ne_temp")
    ne = gpd.read_file(os.path.join("ne_temp", "ne_110m_admin_0_countries.shp"))
    shutil.rmtree("ne_temp")

    # 国フィルタ
    country_row = ne[ne['NAME'] == country]
    if country_row.empty:
        raise ValueError(f"Country '{country}' not found in Natural Earth dataset.")
    geom_col = country_row.geometry
    country_geom = geom_col.union_all() if hasattr(geom_col, 'union_all') else geom_col.unary_union
    minx, miny, maxx, maxy = country_geom.bounds

    tile_ids = []
    lon_start = int(minx // tile_size * tile_size)
    lon_end = int(maxx // tile_size * tile_size)
    lat_start = int(miny // tile_size * tile_size)
    lat_end = int(maxy // tile_size * tile_size)
    for lon in range(lon_start, lon_end + tile_size, tile_size):
        for lat in range(lat_start, lat_end + tile_size, tile_size):
            tile_box = box(lon, lat, lon + tile_size, lat + tile_size)
            if tile_box.intersects(country_geom):
                lat_pref = 'N' if lat >= 0 else 'S'
                lon_pref = 'E' if lon >= 0 else 'W'
                tile_id = f"{lat_pref}{abs(lat):02d}{lon_pref}{abs(lon):03d}"
                tile_ids.append(tile_id)
    return sorted(tile_ids)


def get_tiles_for_bbox(bbox: list, tile_size: int = 3) -> list:
    """
    指定された緯度経度範囲 [LAT_MIN, LON_MIN, LAT_MAX, LON_MAX] で
    交差するタイルID（例: 'N30E120'）のリストを返す。
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    tile_ids = []
    lon_start = int(lon_min // tile_size * tile_size)
    lon_end = int(lon_max // tile_size * tile_size)
    lat_start = int(lat_min // tile_size * tile_size)
    lat_end = int(lat_max // tile_size * tile_size)
    for lon in range(lon_start, lon_end + tile_size, tile_size):
        for lat in range(lat_start, lat_end + tile_size, tile_size):
            lat_pref = 'N' if lat >= 0 else 'S'
            lon_pref = 'E' if lon >= 0 else 'W'
            tile_id = f"{lat_pref}{abs(lat):02d}{lon_pref}{abs(lon):03d}"
            tile_ids.append(tile_id)
    return sorted(tile_ids)


def download_worldcover(bucket: str, version_prefix: str, tiles: list, output_dir: str):
    """
    S3 から指定タイルリストをダウンロードする共通関数
    """
    if not tiles:
        print("No tiles to download.")
        return

    # prefix から version と year を抽出
    parts = version_prefix.strip('/').split('/')
    version_code, year = parts[0], parts[1]

    os.makedirs(output_dir, exist_ok=True)
    s3 = boto3.client(
        's3', config=Config(signature_version=UNSIGNED), region_name='eu-central-1'
    )

    for tile in tiles:
        filename = f"ESA_WorldCover_10m_{year}_{version_code}_{tile}_Map.tif"
        key = f"{version_prefix}{filename}"
        try:
            s3.head_object(Bucket=bucket, Key=key)
        except s3.exceptions.ClientError:
            print(f"Skipping {tile}: {filename} not found")
            continue
        local_path = os.path.join(output_dir, filename)
        print(f"Downloading s3://{bucket}/{key} -> {local_path}")
        s3.download_file(bucket, key, local_path)

    print("All tiles downloaded.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Download ESA WorldCover tiles by country or bounding box'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--country', '-c',
        help='Country name (e.g. Japan), get_tiles_for_country を使用'
    )
    group.add_argument(
        '--bbox', nargs=4, type=float, metavar=('LAT_MIN', 'LON_MIN', 'LAT_MAX', 'LON_MAX'),
        help='Bounding box [LAT_MIN LON_MIN LAT_MAX LON_MAX], get_tiles_for_bbox を使用'
    )
    parser.add_argument(
        '--tile-size', type=int, default=3,
        help='タイルサイズ（度単位、デフォルト3度）'
    )
    parser.add_argument(
        '--output', '-o', required=True,
        help='Output directory'
    )
    parser.add_argument(
        '--version', '-v',
        choices=['v100/2020/map/', 'v200/2021/map/'],
        default='v100/2020/map/',
        help='S3 prefix (choices: v100/2020/map/, v200/2021/map/)'
    )
    args = parser.parse_args()

    print(f"Country: {args.country}")
    print(f"BBox: {args.bbox}")
    print(f"Tile size: {args.tile_size}")
    print(f"Output directory: {args.output}")
    print(f"S3 version prefix: {args.version}")

    if args.country:
        tiles = get_tiles_for_country(args.country, args.tile_size)
    else:
        tiles = get_tiles_for_bbox(args.bbox, args.tile_size)

    download_worldcover('esa-worldcover', args.version, tiles, args.output)
