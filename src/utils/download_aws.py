#!/usr/bin/env python
"""Download Sentinel-2 L2A imagery from AWS STAC (earth-search) with AOI clipping.

機能:
- YAML は download_sentinel.py と互換（lat/lon, buffer, start/end, max_cloud, min_valid など）
- STAC geometry×AOI 重なり率で事前 min_valid フィルタ（無駄なダウンロードを削減）
- ダウンロード後は AOI にクリップし、全バンドを同一格子に再投影
- SCL から MASK.tif を生成 (SCL==0→0, それ以外→1)
- min_valid (最終判定) は「NoData 以外のピクセル率」で評価（雲も有効）
- 出力は GeoTIFF（QGISでそのまま使用可）
"""

from __future__ import annotations
import os, json, time, shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
import requests
from tqdm import tqdm

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import transform_bounds, reproject, Resampling

from shapely.geometry import shape as shp_shape, box as shp_box, mapping as shp_mapping, Point as shp_Point
from shapely.ops import transform as shp_transform

from pystac_client import Client
from pyproj import CRS, Transformer

DEFAULT_STAC = "https://earth-search.aws.element84.com/v1"
DEFAULT_COLLECTION = "sentinel-2-l2a"


# ---------------------------------------------------------------------
# 基本ヘルパー
# ---------------------------------------------------------------------
def _ensure_dir(path: str | Path):
    Path(path).mkdir(parents=True, exist_ok=True)


def _safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-._" else "_" for c in s)


def _utm_crs_for_lonlat(lon: float, lat: float) -> CRS:
    zone = int((lon + 180) // 6) + 1
    south = lat < 0
    return CRS.from_dict({"proj": "utm", "zone": zone, "south": south})

# --- add: HTTP downloader ---------------------------------------------
def _download_file(url: str, dst: Path, retries: int = 3, chunk: int = 1 << 20):
    """
    URL からファイルをストリーム保存するユーティリティ。
    - retries: エラー時のリトライ回数
    - chunk:   ダウンロード時のチャンクサイズ（既定 1MB）
    """
    dst = Path(dst)
    tmp = dst.with_suffix(dst.suffix + ".part")

    for attempt in range(retries):
        try:
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                with open(tmp, "wb") as f:
                    pbar = tqdm(
                        total=total or None, unit="B", unit_scale=True,
                        desc=dst.name, leave=False
                    )
                    for part in r.iter_content(chunk_size=chunk):
                        if part:
                            f.write(part)
                            if total:
                                pbar.update(len(part))
                    pbar.close()
            tmp.replace(dst)  # 原子的にリネーム
            return
        except Exception as e:
            if attempt + 1 == retries:
                raise
            time.sleep(2 * (attempt + 1))

# ---------------------------------------------------------------------
# Config 正規化 & AOI生成
# ---------------------------------------------------------------------
def _pick_assets(item, requested: List[str]) -> Dict[str, str]:
    """
    Sentinel-2 band名 (B02,B03,B04,B08,B11,SCL,dataMaskなど)
    を AWS STAC のアセットキー（blue, green, red, nir, swir16, scl...）に解決。
    """
    assets = item.assets or {}
    keys = set(assets.keys())

    def first_available(candidates: List[str]):
        for k in candidates:
            if k in keys:
                return k
        return None

    # S2 band → STACアセット名対応表
    resolver = {
        "b01": ["coastal"],
        "b02": ["blue"],
        "b03": ["green"],
        "b04": ["red"],
        "b08": ["nir", "nir08"],
        "b11": ["swir16"],
        "b12": ["swir22"],
        "scl": ["scl"],
        "aot": ["aot"],
        "wvp": ["wvp"],
        "visual": ["visual"],
        "datamask": ["scl"],  # SCLからMASK生成
    }

    out = {}
    for name in requested:
        key = name.lower()
        candidates = resolver.get(key, [key])
        found = first_available(candidates)
        if found:
            out[name] = assets[found].href
        else:
            raise KeyError(f"[warn] asset for '{name}' not found in item {item.id} (candidates={candidates})")
    return out

def _normalize_config(cfg: dict) -> dict:
    out = dict(cfg)
    if "lat" in out and "lon" in out and "center" not in out:
        out["center"] = {"lat": float(out["lat"]), "lon": float(out["lon"])}
    if "start" in out and "end" in out and "datetime" not in out:
        out["datetime"] = f"{out['start']}/{out['end']}"
    if "max_cloud" in out and "cloud_cover_lt" not in out:
        out["cloud_cover_lt"] = out["max_cloud"]
    if "bands" in out and "assets" not in out:
        out["assets"] = out["bands"]
    return out


def _to_geojson_aoi(cfg: dict) -> dict:
    if "aoi" in cfg and cfg["aoi"]:
        return shp_mapping(shp_shape(cfg["aoi"]))
    if "bbox" in cfg and cfg["bbox"]:
        xmin, ymin, xmax, ymax = cfg["bbox"]
        return shp_mapping(shp_box(xmin, ymin, xmax, ymax))
    if "center" not in cfg or not cfg["center"]:
        raise ValueError("center not found.")
    lon, lat = float(cfg["center"]["lon"]), float(cfg["center"]["lat"])
    if "buffer" in cfg and cfg["buffer"]:
        buf = float(cfg["buffer"])
        return shp_mapping(shp_box(lon - buf, lat - buf, lon + buf, lat + buf))
    if "buffer_m" in cfg and cfg["buffer_m"]:
        meters = float(cfg["buffer_m"])
        pt = shp_Point(lon, lat)
        wgs84 = CRS.from_epsg(4326)
        utm = _utm_crs_for_lonlat(lon, lat)
        fwd = Transformer.from_crs(wgs84, utm, always_xy=True).transform
        inv = Transformer.from_crs(utm, wgs84, always_xy=True).transform
        g_utm = shp_transform(fwd, pt)
        g_buf = g_utm.buffer(meters)
        g_back = shp_transform(inv, g_buf)
        return shp_mapping(g_back)
    tiny = 1e-4
    return shp_mapping(shp_box(lon - tiny, lat - tiny, lon + tiny, lat + tiny))


def _aoi_bbox_lonlat(cfg: dict) -> Tuple[float, float, float, float]:
    g = shp_shape(_to_geojson_aoi(cfg))
    return g.bounds


# ---------------------------------------------------------------------
# STAC 検索と事前min_validフィルタ
# ---------------------------------------------------------------------
def search_items(stac_endpoint: str, collection: str, aoi_geojson: dict, datetime_rng: str,
                 cloud_cover_lt: Optional[float], max_items: int) -> List:
    client = Client.open(stac_endpoint)
    query = {}
    if cloud_cover_lt is not None:
        query["eo:cloud_cover"] = {"lt": float(cloud_cover_lt)}
    search = client.search(
        collections=[collection],
        intersects=aoi_geojson,
        datetime=datetime_rng,
        query=query or None,
        max_items=max_items or 100,
    )
    return list(search.get_items())


def _estimate_valid_ratio_from_stac_item(item, aoi_geojson: dict) -> float:
    """STACアイテムのgeometryとAOIの重なり率(%)を算出"""
    g_item = shp_shape(item.geometry)
    g_aoi = shp_shape(aoi_geojson)
    if not g_item.is_valid or not g_aoi.is_valid:
        return 0.0
    inter_area = g_item.intersection(g_aoi).area
    if inter_area == 0:
        return 0.0
    return (inter_area / g_aoi.area) * 100.0


# ---------------------------------------------------------------------
# Raster操作
# ---------------------------------------------------------------------
def _clip_read(src_path: Path, bbox_lonlat, *, resampling=Resampling.bilinear):
    with rasterio.open(src_path) as src:
        xmin, ymin, xmax, ymax = transform_bounds(CRS.from_epsg(4326), src.crs, *bbox_lonlat, densify_pts=21)
        win = from_bounds(xmin, ymin, xmax, ymax, transform=src.transform).round_offsets().round_lengths()
        data = src.read(window=win)
        transform = src.window_transform(win)
        profile = src.profile.copy()
        mask = src.read_masks(1, window=win)
        return data, transform, src.crs, profile, mask


def _reproject_to_grid(data, src_transform, src_crs, dst_transform, dst_crs, dst_shape, *, nearest=False):
    dst = np.zeros((data.shape[0], dst_shape[0], dst_shape[1]), dtype=data.dtype)
    for b in range(data.shape[0]):
        reproject(
            source=data[b], destination=dst[b],
            src_transform=src_transform, src_crs=src_crs,
            dst_transform=dst_transform, dst_crs=dst_crs,
            resampling=(Resampling.nearest if nearest else Resampling.bilinear),
        )
    return dst


def _reproject_mask_to_grid(mask_src, src_transform, src_crs, dst_transform, dst_crs, dst_shape):
    dst = np.zeros(dst_shape, dtype=np.uint8)
    reproject(
        source=mask_src, destination=dst,
        src_transform=src_transform, src_crs=src_crs,
        dst_transform=dst_transform, dst_crs=dst_crs,
        resampling=Resampling.nearest,
    )
    return np.where(dst > 0, 255, 0).astype(np.uint8)


def _save_geotiff(path: Path, array, crs, transform, base_profile, *, mask=None, dtype=None):
    prof = base_profile.copy()
    prof.update({
        "driver": "GTiff",
        "count": array.shape[0],
        "height": array.shape[1],
        "width": array.shape[2],
        "transform": transform,
        "crs": crs,
        "dtype": (dtype or array.dtype),
        "tiled": True,
        "compress": "deflate",
        "predictor": 2,
    })
    prof.pop("nodata", None)
    with rasterio.open(path, "w", **prof) as dst:
        dst.write(array)
        if mask is not None:
            dst.write_mask(mask)

def _generate_MASK_from_SCL(scl_path: Path, out_path: Path) -> Path:
    with rasterio.open(scl_path) as src:
        scl = src.read(1)
        meta = src.meta.copy()
        mask = np.where(scl == 0, 0, 1).astype(np.uint8)
        meta.update(dtype=rasterio.uint8, count=1)
        with rasterio.open(out_path, "w", **meta) as dst:
            dst.write(mask, 1)
    print(f"[info] MASK created from SCL → {out_path.name}")
    return out_path

def _write_preview_masked(date_dir: Path):
    rgb_paths = [date_dir/"B04.tif", date_dir/"B03.tif", date_dir/"B02.tif"]
    mask_path = date_dir/"MASK.tif"
    if not all(p.exists() for p in rgb_paths) or not mask_path.exists():
        return
    with rasterio.open(rgb_paths[0]) as r4, \
         rasterio.open(rgb_paths[1]) as r3, \
         rasterio.open(rgb_paths[2]) as r2, \
         rasterio.open(mask_path) as rm:
        R = r4.read(1).astype(np.float32)
        G = r3.read(1).astype(np.float32)
        B = r2.read(1).astype(np.float32)
        M = rm.read(1).astype(np.float32)

    def stretch(x, m):
        v = m > 0
        lo, hi = (np.nanpercentile(x[v], [2,98]) if np.any(v) else (np.nanmin(x), np.nanmax(x)))
        return np.clip((x-lo)/(hi-lo+1e-6), 0, 1)

    img = np.dstack([stretch(R,M)*M, stretch(G,M)*M, stretch(B,M)*M])
    from PIL import Image
    Image.fromarray((img*255).astype(np.uint8)).save(date_dir / "preview_masked.png")

# ---------------------------------------------------------------------
# メイン処理
# ---------------------------------------------------------------------
def download_from_config(config_path: str | Path, output_dir: str | Path | None = None, *, name: str | None = None) -> Path:
    cfg = yaml.safe_load(Path(config_path).read_text()) or {}
    cfg = _normalize_config(cfg)

    if "datetime" not in cfg:
        raise ValueError("Config must include date range.")
    aoi_geojson = _to_geojson_aoi(cfg)
    bbox_deg = _aoi_bbox_lonlat(cfg)

    stac, col = DEFAULT_STAC, DEFAULT_COLLECTION
    dt, cloud = cfg["datetime"], cfg.get("cloud_cover_lt")
    assets_req = cfg.get("assets", ["visual"])
    satellite = cfg.get("satellite", "Sentinel-2")
    min_valid = cfg.get("min_valid")
    max_items = cfg.get("max_items", 100)

    need_mask = any(a.lower() == "datamask" for a in assets_req)
    assets_internal = list(assets_req)
    if need_mask and not any(a.lower() == "scl" for a in assets_internal):
        assets_internal.append("SCL")

    base_dir = Path(output_dir or "data")
    sub_dir = Path(satellite) / (name or cfg.get("name", "aws_stac"))
    out_root = base_dir / sub_dir
    _ensure_dir(out_root)
    print(f"📦 Output base: {out_root}")

    # --- STAC検索 & 事前フィルタ ---
    items = search_items(stac, col, aoi_geojson, dt, cloud, max_items)
    if not items:
        print("⚠️  シーンが見つかりません。")
        return out_root

    if min_valid is not None:
        before = len(items)
        items = [it for it in items if _estimate_valid_ratio_from_stac_item(it, aoi_geojson) >= float(min_valid)]
        after = len(items)
        print(f"[info] pre-filtered by AOI overlap: {after}/{before} items remain (min_valid={min_valid}%)")
        if not items:
            print("⚠️  min_valid フィルタで全て除外されました。")
            return out_root

    # ---- ダウンロード＆保存 ----
    for it in items:
        date_dir = out_root / _safe_filename(it.id)
        _ensure_dir(date_dir)

        asset_map = _pick_assets(it, assets_internal)
        if not asset_map:
            print(f"[warn] no matching assets found for item {it.id}")
            continue

        # --- 修正: 基準バンドの決め方（大小無視で安全に選ぶ） ---
        prefer_ci = ["b04", "b03", "b02", "b08", "b11", "visual", "scl", "datamask"]
        lower2orig = {k.lower(): k for k in asset_map.keys()}

        base_key = next((lower2orig[c] for c in prefer_ci if c in lower2orig), next(iter(asset_map.keys())))
        # ここで base_key は 'B04' など元のキー（大文字）のままになります

        # --- 修正: lower() をやめる ---
        base_href = asset_map[base_key]

        # 基準バンドのダウンロード＆格子確定はこのまま
        tmp_base = date_dir / f"__tmp__{base_key}.tif"
        _download_file(base_href, tmp_base)
        base_data, base_transform, base_crs, base_prof, base_mask = _clip_read(tmp_base, bbox_deg)
        tmp_base.unlink(missing_ok=True)
        base_out = date_dir / f"{base_key}.tif"
        _save_geotiff(base_out, base_data, base_crs, base_transform, base_prof, mask=base_mask)

        # --- 修正: 残りのバンド処理（大小無視でスキップ判定） ---
        for req_name, href in asset_map.items():
            if req_name.lower() == base_key.lower():
                continue
            tmp = date_dir / f"__tmp__{req_name}.tif"
            _download_file(href, tmp)
            data, src_transform, src_crs, prof, mask_src = _clip_read(
                tmp, bbox_deg,
                resampling=(Resampling.nearest if req_name.lower() in ("scl","datamask") else Resampling.bilinear)
            )
            aligned = _reproject_to_grid(
                data, src_transform, src_crs,
                base_transform, base_crs,
                (base_data.shape[1], base_data.shape[2]),
                nearest=(req_name.lower() in ("scl","datamask")),
            )
            mask_aligned = _reproject_mask_to_grid(
                mask_src, src_transform, src_crs,
                base_transform, base_crs,
                (base_data.shape[1], base_data.shape[2]),
            )
            out_name = "MASK" if req_name.lower()=="datamask" else req_name
            dst = date_dir / f"{out_name}.tif"
            _save_geotiff(
                dst, aligned, base_crs, base_transform, base_prof,
                mask=mask_aligned,
                dtype=(rasterio.uint8 if req_name.lower() in ("scl","datamask") else None)
            )
            tmp.unlink(missing_ok=True)


        # 3) dataMask 生成
        if need_mask:
            scl_path = date_dir / "SCL.tif"
            mask_path = date_dir / "MASK.tif"
            if scl_path.exists() and not mask_path.exists():
                _generate_MASK_from_SCL(scl_path, mask_path)

        # 4) min_valid (NoData除外率) 判定
        if min_valid is not None:
            with rasterio.open(base_out) as src:
                m = src.dataset_mask()
            valid_pct = float((m > 0).sum()) * 100.0 / m.size
            if valid_pct < float(min_valid):
                print(f"[info] Skip {it.id}: valid {valid_pct:.1f}% < min_valid {min_valid}% → remove folder")
                shutil.rmtree(date_dir)
                continue
        
        _write_preview_masked(date_dir)
        print(f"✅  Saved to {date_dir}")

    shutil.copy(config_path, out_root / "download.yaml")
    print(f"✅  Saved GeoTIFFs to {out_root}")
    return out_root


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--output", default="data")
    p.add_argument("--name", default=None)
    args = p.parse_args()
    download_from_config(args.config, args.output, name=args.name)
