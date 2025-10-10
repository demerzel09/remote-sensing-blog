
# `download_aws.py::download_from_config` 仕様プロンプト（現行コード準拠）

> **目的**: 既存の `src/utils/download_aws.py` および `configs/download_oita.yaml` の挙動を**そのまま**仕様化し、将来の再実装/差し替えに使える「プロンプト（仕様書）」として固定する。  
> **対象**: `python -m src.pipeline.download --output <DIR> --config <YAML> --name <NAME>` 実行時に、YAMLの `provider: aws_cog` が選ばれた経路。

---

## 1. YAML（`configs/download_*.yaml`）の仕様

### 1.1 最低限のキー（サンプル: `download_oita.yaml`）
```yaml
provider: aws_cog        # ← これで AWS COG + STAC ルートに分岐

# 空間範囲の指定（以下のいずれかで AOI を作る）
lat: 33.380              # 単点中心（WGS84）
lon: 131.468
# buffer: 0.1            # 度単位のバッファ（任意）
buffer_m: 10000          # メートル単位バッファ（任意、優先）

# 期間
start: '2024-01-01'
end:   '2024-02-27'

# 事前フィルタ
max_cloud: 40            # STACの eo:cloud_cover < 40 で検索

# 事後フィルタ（最終判定）
min_valid: 30            # 出力画像の NoData 以外の割合(%) がこれ未満ならフォルダ削除

# 付帯情報
satellite: 'Sentinel-2'  # 出力ディレクトリ名に使用

# 取得アセット（= バンド）
bands:
  - B02
  - B03
  - B04
  - B08
  - B11
  - SCL
  - dataMask            # ← 要求時は内部でSCLからMASK.tifを作成
```

### 1.2 受理されるキーと正規化規則（コード準拠）
- `provider: aws_cog` … パイプラインが AWS ルートへ迂回（`src/pipeline/download.py`）。
- 空間範囲の与え方（優先順位）
  - `aoi`（GeoJSON）→ そのまま使用
  - `bbox: [xmin, ymin, xmax, ymax]`（WGS84, 度）
  - `center: {lon, lat}` もしくは `lon` + `lat`
    - `buffer`（度）または `buffer_m`（メートル）で矩形/バッファを生成（`buffer_m` があれば UTM 変換して正確にバッファ）
    - どちらも無ければ buffer_m = 10000 をデフォルトとする
- 期間
  - `datetime` は `start` + `end` から `"start/end"` を生成
- 雲量
  - `cloud_cover_lt` は `max_cloud` を適用
- バンド/アセット
  - `assets` は `bands` からコピー（例: `["B02","B03","B04","B08","B11","SCL","dataMask"]`）
- 追加オプション（すべて**任意**、デフォルトを併記）
  - `target_res_m: 10` …… 共通グリッドの解像度（m）
  - `max_items: 50` …… STAC 取得上限
  - `min_valid: <percent>` …… 事後チェック（NoData以外の割合）
  - `make_bands_tif: true` …… `BANDS.tif` を作るか

> **補足:** `download.py` が YAML を先読みして `provider` を見てから `download_aws.py` の `download_from_config()` を呼び出します。

---

## 2. 関数インターフェース（現行）

```python
def download_from_config(
    config_path: str | Path,
    output_dir: str | Path | None = None,
    *,
    name: str | None = None,
    skip_existing: bool = False,
) -> Path:
    # YAML を読み込み、AWS STAC (earth-search) から指定アセットを取得。
    # AOI で切り出し後、単一の「共通グリッド」に揃えて GeoTIFF を保存する。
    # 戻り値は出力ルートディレクトリ: <output_dir>/<satellite>/<name or cfg.name or aws_stac>
```

### 2.1 引数
- `config_path` … YAML ファイルパス
- `output_dir` … 出力ルート（未指定なら既定 `"data"`）
- `name` … サブフォルダ名（`<satellite>/<name>`）。未指定時は YAML の `name`、なければ `"aws_stac"`
- `skip_existing` … 既存ファイルが共通グリッドに合致していれば再投影のみ or スキップ

### 2.2 返り値
- `Path` … 出力ルート `<output_dir>/<satellite>/<name>`

### 2.3 例外・終了条件（抜粋）
- `datetime` が YAML 内で解決できない場合 `ValueError`
- 要求バンドが STAC item に存在しない場合 `KeyError`
- STAC 検索でヒット 0、または `min_valid` 事後判定で全除外の場合も**エラーにはせず**空ディレクトリを返す

---

## 3. 出力仕様（ファイル/ディレクトリ & グリッド）

### 3.1 ディレクトリ構成
```
<output_dir>/<satellite>/<name>/
  ├─ <item-id-sanitized-1>/
  │    ├─ B02.tif, B03.tif, B04.tif, B08.tif, B11.tif, SCL.tif, MASK.tif
  │    ├─ BANDS.tif                 # make_bands_tif=true のとき
  │    └─ preview_masked.png        # B04/B03/B02 + MASK による簡易プレビュー
  ├─ <item-id-sanitized-2>/
  │    └─ （同上）
  └─ download.yaml                  # 実行時の YAML をコピー
```

### 3.2 共通グリッド（空間統一のルール）
- **全ファイルが同一の** `CRS / transform / width / height / pixel size` を持つ
- CRS 決定:
  - UTM を自動決定（南北半球も自動）
- 解像度: `target_res_m`（デフォルト 10 m）
- AOI（WGS84）の bbox を `grid_crs` に投影 →
  - 左上原点に**スナップ**（`xmin= floor(xmin/res)*res`, `ymax= ceil(ymax/res)*res`）
  - `from_origin(xmin_s, ymax_s, res, res)` を採用（上が北、行方向に負のスケール）
- クリップ→再投影の**後**に保存するため、**有効領域の大小に関係なく**出力格子は固定（上端合わせ等はしない）

### 3.3 画像の内容・型
- 連続値（B02, B03, B04, B08, B11 など）: オリジナル dtype を維持（一般に `uint16`）
- 離散値（`SCL`, `dataMask→MASK`）: `uint8`
- マスク
  - 読み込み時の dataset mask をリプロジェクションして AND 結合
  - 追加で `dataMask` を要求した場合は、内部で `SCL` から `MASK.tif` を生成（`SCL==0 → 0`, それ以外→ `1`）
- `BANDS.tif` の順序
  - `bands_stack` があればその順
  - 無ければ、`["B02","B03","B04","B08","B11","dataMask"]` から存在ファイルだけを抽出（最低限 `"B02","B03","B04","dataMask"` を想定）
- `preview_masked.png`
  - B04/B03/B02 の 2–98% ストレッチ後、MASK で乗算した簡易可視化

---

## 4. 取得フロー & フィルタ

1. **STAC 検索**
   - エンドポイント: `https://earth-search.aws.element84.com/v1`
   - コレクション: `sentinel-2-l2a`
   - パラメータ: `intersects=AOI`, `datetime`, `eo:cloud_cover < cloud_cover_lt`（任意）
   - `max_items` まで取得（既定 100）
2. **事前フィルタ（任意）**
   - `min_valid` が設定されている場合、**STAC Item の geometry と AOI の重なり率(%)** でフィルタ（AOI面積に対する割合）。
3. **ダウンロード & クリップ**
   - 要求アセットごとに URL を解決（例: `B04→red`, `B08→nir`, `dataMask→SCL`）
   - まず基準バンド（優先順: `B04,B03,B02,B08,B11,visual,SCL,dataMask`）を保存し、以降のバンドも同じ**共通グリッド**へ再投影して保存
4. **事後フィルタ（任意）**
   - `min_valid` が設定されている場合、**保存済み基準バンドの dataset mask** の有効画素率(%)が閾値未満なら、その Item のフォルダを削除

> **注意:** `min_valid` は **NoData 以外の割合**で判定し、**雲ピクセルは有効扱い**。雲除去は別工程。

---

## 5. 既知のユースケースと注意点

- **解像度/サイズ不一致の回避**: `target_res_m` と「格子スナップ」規則により、全出力は同サイズ・同 transform で固定。  
- **有効領域が小さい/位置ズレ問題**: AOI→投影→スナップで**地理座標基準**の格子を固定し、各アセットをその格子に再投影して保存するため、**上端合わせ等のズレは発生しない**。  
- **`dataMask` の意味**: 入力として `SCL` を読み、`SCL==0` を 0（無効）、それ以外を 1 として `MASK.tif` を出力。雲は別扱い。

---

## 6. 再実装時の受け入れ条件（ミニマム）

- 同一 YAML → **同一 CRS / transform / width / height** の GeoTIFF を生成すること  
- `download.yaml` を出力ルート直下にコピーすること  
- `bands_stack` 指定があれば `BANDS.tif` の順が一致すること  
- `min_valid` の事前/事後フィルタ仕様が一致すること（AOI重なり率 / NoData 率）

---

## 7. 将来変更しやすいパラメータ一覧（明示）
- 空間: `target_res_m`, `target_crs_epsg`
- 検索: `max_items`, `cloud_cover_lt`
- 事前/事後フィルタ: `min_valid`
- 合成: `make_bands_tif`, `bands_stack`

---

## 付録: コマンド実行例

```bash
python -m src.pipeline.download   --output data/example_run   --config "configs/download_oita.yaml"   --name oita
```
