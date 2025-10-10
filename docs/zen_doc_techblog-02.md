# 目的
 -  Sentinel-2データの土地利用分類。  
    Sentinel-2 は、ESA(欧州宇宙機関）が提供する リモートセンシングでもっともよくつかわれるフリーの高品質なデータです。  
    土地利用分類の分類を自前で学習して分類してみようという企画です。
    リモートセンシングのデータの基礎操作を一通りやってみます。
![review](https://storage.googleapis.com/zenn-user-upload/fc63310d6e90-20250606.jpg)

  ## 参考  
   - ### Sentinel-2 などの用語説明について  
        https://zenn.dev/fusic/articles/d21ac63d8d3c69#sentinel-2  

   - ### NDVI (植生/NDWI・水指数）について  

     NDVI（正規化植生指数）は、衛星画像の赤色バンドと近赤外バンドを用いて植生の活性度を評価する 指標です。
     値は -1〜1 の範囲をとり、値が高いほど植生が活発であることを示します。

     NDWI（水域指数）は、近赤外バンドと短波赤外バンドを使って水域の分布を抽出する指標です。
     どちらもリモートセンシングで土地被覆分類や環境モニタリングに広く利用されています。

     **計算式とバンド**
     - NDVI = (B08 - B04) / (B08 + B04)
        - B08: 近赤外バンド（NIR, 10m解像度）
        - B04: 赤色バンド（Red, 10m解像度）

     - NDWI = (B08 - B11) / (B08 + B11)
        - B08: 近赤外バンド（NIR, 10m解像度）
        - B11: 短波赤外バンド（SWIR, 20m解像度）
  
# Sentinel-2 のデータ取得方法

   Sentinel-2 データの主な取得方法は以下の通りです。

### ① Copernicus Open Access Hub（旧：SciHub）  
$\quad$ESA公式の基本ポータル。  
- Sentinel-1～5シリーズのデータがすべてダウンロード可能。
- [Copernicus Open Access Hub](https://dataspace.copernicus.eu/)
- アカウント登録（無料）が必要。
- Webブラウザ上でエリア・期間・雲量などを指定して検索・ダウンロード可能。
- ただしHPを操作して手動で zip ファイルを持ってくる必要があるという制限がある。

### ② Sentinel Hub（Commercial API／無料枠あり）
$\quad$ESA公式APIのデータを高速アクセス。
- PythonなどからAPI経由で取得可能。
- [Sentinel Hub](https://www.sentinel-hub.com/)
- 30日間の無料枠あり。それ以降は 300 EURO/月～

### ③ Google Earth Engine（GEE）
$\quad$クラウド上でSentinel-2データを直接処理できるプラットフォーム。

- ダウンロードせず、解析・可視化・雲除去などをスクリプトで実行可能。
- [Google Earth Engine](https://earthengine.google.com/)
- 登録が必要
- 前回の Tech-Blogのお題  
  https://zenn.dev/fusic/articles/d21ac63d8d3c69
  
### ④ AWS Open Data Registry（Amazon S3）
$\quad$Amazonがホストしているオープンデータセット。

- Sentinel-2のL1C/L2Aデータを HTTP または S3 API 経由で取得可能。
- 登録などは不要
- [AWS Open Data Registry: Sentinel-2](https://registry.opendata.aws/sentinel-2/)

---

今回は④ AWS Open Data Registryを利用します。
②のSentinel Hub APIを使った自動ダウンロード例は、  
`src/utils/download_sentinel.py` および `configs/sentinel-hub/` で実装しています。  
興味がある方はそちらをご参照ください。


# 実装

## 1. 衛星データを取得

```bash
# 個別に処理
python -m src.pipeline.download \
--output data/example_run2 \
--config "configs/download_fukuoka.yaml" \
--name fukuoka

# まとめて処理
bash scripts/download_sentinel2.sh
```

設定ファイル（YAML形式）に記載されたパラメータ（緯度・経度・期間など）に基づき、Sentinel-2 衛星データを自動でダウンロードします。

- 設定ファイルからダウンロード条件（座標・期間・バンドなど）を読み込み
- AWSから、指定範囲・期間・雲被覆率の衛星画像を検索・ダウンロード
- クラスデータが入っているSCLから、有効領域の MASK.tifを作成
- MASK.tif から、有効画素率でフィルタリング
  
AWS COG + STAC のデータを、ESA公式のAPI（Sentinel-Hub）で雲の少ない日時のL2A(Sentinel-2のプロダクト）と同等のデータに加工します。


## 2. 雲除去処理の実行

```bash
# 個別に処理
python -m src.pipeline.cloud_removal \
--input-dir "data/example_run/Sentinel-2/fukuoka"

# まとめて処理
bash scripts/cloud_removal_sentinel2.sh
```

ダウンロード済みのSentinel-2 L2Aデータに対して雲除去を行います。
`src/pipeline/cloud_removal.py` は、指定ディレクトリ内の各日付シーンごとに雲マスクを適用し、雲や影の影響を受けたピクセルを自動的にマスク（無効化）します。

- SCLバンドやdataMaskバンドを用いて雲・影領域を判定
- 雲・影と判定されたピクセルを、全バンド画像で無効値（例：-9999）に置換
- 雲除去済みの画像を上書き保存

この処理により、後続の解析やモザイク処理で雲の影響を大幅に低減できます。


## 3. 複数の日時の雲除去された部分でモザイク処理（統合処理）を行う

```bash
# 個別に処理
python -m src.pipeline.mosaic \
--input-dir "data/example_run/Sentinel-2/fukuoka" \
--method best

# まとめて処理
bash scripts/mosaic_sentinel2.sh
```

複数日時の雲除去済みSentinel-2データ（各日付サブフォルダ内のBANDS.tif等）を統合し、雲の少ないピクセルを優先的に選択して1枚のモザイク画像を作成します。

- 複数の日付サブフォルダのBANDS.tif（およびSCL.tif, MASK.tif）を収集
- SCL（シーン分類）情報を活用し、雲や影の少ないピクセルを優先して統合
   - `best`：各ピクセル位置で最も良好な（雲のない）値を選択
   - `median`：雲のないピクセルの中央値を合成
- SCL.tifやMASK.tifも同様にモザイク処理  

この処理により、複数日時のデータから雲の影響を最小限に抑えた高品質な合成画像を得ることができます。


## 4. ESA WorldCoverという土地利用分類の教師データを集める

```bash
# 個別に処理
python -m src.utils.download_worldcover_datasets \
--bbox 30 129 34 132 \
--output "data/wc2021_kyusyu_bbox" \
--version v200/2021/map/

# まとめて処理
bash scripts/download_worldcover_for_label.sh
```

ESA WorldCover（2021年版など）の土地利用分類データを、指定した範囲（国名またはバウンディングボックス）で自動的にダウンロードします。

 - 指定範囲に重なる3度×3度タイルのリストを自動で計算
 - 各タイルのGeoTIFF（例: ESA_WorldCover_10m_2021_v200_N33E130_Map.tif）をS3から取得
 - 国名指定（--country）もしくは緯度経度範囲（--bbox）で取得範囲を指定できます。

取得したデータは後続のラベル生成や機械学習にそのまま活用できます。


## 5. NDVI(植生/NDWI・水指数）を特徴量として計算  

```bash
# 個別に処理
python -m src.pipeline.preprocess \

# まとめて処理
bash scripts/preprocess_sentinel2.sh
```

Sentinel-2データに対してNDVIやNDWIなどの植生・水域指標を計算し、特徴量として保存します。

- 設定ファイル（YAML）から計算対象のバンドやパラメータを読み込み
- 各シーンのBANDS.tif等から必要なバンド（例：B04, B08, B11）を抽出
- NDVI, NDWIなどの指標をピクセルごとに計算

この処理により、後続の機械学習や解析のための特徴量データセットが作成されます。

## 6. 教師データを作成

```bash
# 個別に処理
python -m src.utils.worldcover_to_label \

# まとめて処理
bash scripts/create_labels_of_bbox.sh
```

WorldCoverの土地利用分類データ（ラベル画像）と、Sentinel-2の観測データを重ね合わせて、機械学習用の教師データ（ラベル画像）を作成します。

- WorldCoverディレクトリからラベル画像（GeoTIFF）を読み込み
- Sentinel-2ディレクトリ内の各シーンと空間的に重なる範囲を抽出
- 必要に応じてリサンプリングや座標系変換を行い、ラベル画像と観測データのピクセルを対応させ、土地利用クラス（例：森林、農地、水域など）のラベルを割り当て

この処理により、衛星画像と正解ラベルが対応した教師データセットを生成、土地利用分類などの機械学習タスクに活用できます。

## 7. LightGBMで、学習
```bash
# 個別に処理
python -m src.pipeline.train \
--config configs/train.yaml \
--output-dir data/outputs/model_example \
--verbose 1

# まとめて処理
bash scripts/train_model.sh
```

前処理済みの特徴量データと教師データ（ラベル画像）を用いて、LightGBMによる土地利用分類モデルの学習を行います。

- 設定ファイル（train.yaml）から学習パラメータや入力データのパスを読み込み  
  $\quad$train.yaml では後の推論データと重ならなように、2つの地域を教師データとしている。  
  - data/example_run/Sentinel-2/kitakyusyu
  - data/example_run/Sentinel-2/oita
  - data/example_run/Sentinel-2/karatzu

- NDVIやバンド値などの特徴量と、対応するラベル画像を読み込んで学習用データセットを作成
- LightGBMの分類モデルを訓練データで学習
- 学習過程や評価指標（例：精度、損失、混同行列など）を出力

この処理により、衛星画像から土地利用を分類するための機械学習モデルが作成されます。

## 8. LightGBMで推論します

```bash
# 個別に処理
python -m src.pipeline.predict \
--config configs/predict.yaml \
--model-dir data/outputs/model_example \
--input-dir "data/example_run/Sentinel-2/fukuoka" \
--output-dir "data/outputs/prediction_example/fukuoka"

# まとめて処理
bash scripts/predict_sentinel2.sh
```

学習済みのLightGBMモデルを用いて、Sentinel-2データに対する土地利用分類の推論（予測）を行います。

- 設定ファイル（predict.yaml）から推論パラメータや入力データのパスを読み込み
- 特徴量データ（NDVIやバンド値など）を読み込み
- 学習済みモデルをロードし、各ピクセルごとに土地利用クラスを予測
- 予測結果をラスタ画像（GeoTIFF等）として保存

この処理により、未知の地域や時期の衛星画像に対して土地利用分類結果を得ることができます。

# 結果の検証


# まとめ





