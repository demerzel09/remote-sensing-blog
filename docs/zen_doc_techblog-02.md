# 目的
 -  Sentinel-2データの土地利用分類。  
    Sentinel-2 は、ESA(欧州宇宙機関）が提供する リモートセンシングでもっともよくつかわれるフリーの高品質なデータです。  
    土地利用分類の分類を自前で学習して分類してようという企画です。
    Google Earth などを使うと可視化・データ加工までの処理をAPI一発で取れたりするデータを、できるだけ自前で加工していきます。
    一度は、やっておきたいリモートセンシングの基礎操作を自習します。
![review](https://storage.googleapis.com/zenn-user-upload/fc63310d6e90-20250606.jpg)

  ## 参考  
   - ### Sentinel-2 などの用語説明について  
        https://zenn.dev/fusic/articles/d21ac63d8d3c69#sentinel-2  

   - ### NDVI (植生/NDWI・水指数）について  

     NDVI（正規化植生指数）は、衛星画像の赤色バンドと近赤外バンドを用いて植生の活性度を評価する 標です。
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
- ただしHPを操作して手動で zip ファイルを持ってくるなどの制限がある。

### ② Sentinel Hub（Commercial API／無料枠あり）
$\quad$ESA公式APIのデータを高速アクセス。
- PythonなどからAPI経由で取得可能。
- [Sentinel Hub](https://www.sentinel-hub.com/)
- 30日間の無料枠あり。それ以降は 300 EURO/月～

### ③ Google Earth Engine（GEE）
$\quad$クラウド上でSentinel-2データを直接処理できるプラットフォーム。

- ダウンロードせず、解析・可視化・雲除去などをスクリプトで実行可能。
- [Google Earth Engine](https://earthengine.google.com/)

### ④ AWS Open Data Registry（Amazon S3）
$\quad$Amazonがホストしているオープンデータセット。

- Sentinel-2のL1C/L2Aデータを HTTP または S3 API 経由で取得可能。
- 登録などは不要
- [AWS Open Data Registry: Sentinel-2](https://registry.opendata.aws/sentinel-2/)

---

今回は④ AWS Open Data Registryを利用します。
②のSentinel Hub APIを使った自動ダウンロード例は、
`src/utils/download_sentinel.py` および `configs/sentinel-hub/` で実装しています。興味がある方はそちらもご参照ください。


# 実装

## 1. 衛星データを取得

```bash
# 個別に処理
python -m src.pipeline.download --output data/example_run2 \
--config "configs/download_fukuoka.yaml" \
--name fukuoka
# まとめて処理
./scripts/download_sentinel2.sh
```

このスクリプトは、設定ファイル（YAML形式）に記載されたパラメータ（緯度・経度・期間など）に
基づき、Sentinel-2 衛星データを自動でダウンロードします。主な流れは以下の通りです。  

- コマンドライン引数で設定ファイルと出力先ディレクトリを指定
- 設定ファイルからダウンロード条件（座標・期間・バンドなど）を読み込み
- Sentinel Hub API を使って、指定範囲・期間の衛星画像を検索・取得
- 画像データ（GeoTIFF形式）を自動でディレクトリに保存
- 取得した画像をバンドごとに分割し、必要に応じて雲量や有効画素率でフィルタリング
- 設定ファイルもダウンロードディレクトリにコピーし、後続処理で再利用可能に

この自動化により、煩雑な衛星データ取得作業をシンプルに再現性高く実行できます。
ESA公式のAPI（Sentinel-Hub）で雲の少ない日時のL2A(Sentinel-2のプロダクト）のデータを集めます。


## 2. 雲除去処理の実行

```bash
# 個別に処理
python -m src.pipeline.cloud_removal --input-dir "data/example_run/Sentinel-2/fukuoka"
# まとめて処理
./scripts/cloud_removal_sentinel2.sh
```

このスクリプトは、ダウンロード済みのSentinel-2 L2Aデータに対して雲除去を行います。
`src/pipeline/cloud_removal.py` は、指定ディレクトリ内の各日付シーンごとに雲マスクを適用し、雲や影の影響を受けたピクセルを自動的にマスク（無効化）します。

主な処理内容は以下の通りです。

- コマンドライン引数（--input-dir）で入力ディレクトリを指定
- ディレクトリ内の各日付サブフォルダに対し、SCLバンドやdataMaskバンドを用いて雲・影領域を判定
- 雲・影と判定されたピクセルを、全バンド画像で無効値（例：-9999）に置換
- 雲除去済みの画像を上書き保存

この処理により、後続の解析やモザイク処理で雲の影響を大幅に低減できます。


## 3. 複数の日時の雲除去された部分でモザイク処理を行い(複数日時のデータからなる）統合データを作る。
# 3. Integrate multiple cloud-removed datasets
bash scripts/mosaic_sentinel2.sh

## 4. ESAから WorldCoverという土地利用分類の教師データを集める。
# 4. Download the original training data (ESA WorldCover)
#    Obtain all tiles covering the Kyushu region.　　　
bash scripts/download_worldcover_for_label.sh

## 5. 自前でNDVI(植生/NDWI・水指数）を特徴量として計算
# 5. Extract features (NDVI/NDWI)
bash scripts/preprocess_sentinel2.sh

## 6. 教師データを作成
# 6. Create training labels
bash scripts/create_labels_of_bbox.sh

## 7. LightGBMで、学習
# 7. Train a model using LightGBM with NDVI/NDWI features (Regions: Ōita / Kitakyushu)
bash scripts/train_model.sh

## 8. LightGBMで推論します。
# 8.Run inference using LightGBM
bash scripts/predict_sentinel2.sh


# まとめ
本記事では、衛星データの基本を知り、Google Earth Engine を用いて Sentinel-2 (L2A) データの雲除去処理を実装してみました。また、3つのアルゴリズムの性能を比較し、以下の知見を得ました。

 - QA60：処理が簡単で高速だが、精度に限界がある
 - s2cloudless：マシンラーニングベースの高精度手法。水域や薄雲の扱いに注意が必要
 - Cloud Score+：雲影もカバーし、最も網羅的な雲除去が可能（検出漏れが少ない）

結果として、Cloud Score+ は誤検出が少なく、薄雲や雲影にも強いため、地表面の解析において有効な手法であることが確認できました。

今後は、NDVI(植生を表す指標)などの指標計算への応用も検討していきたいと思います。



