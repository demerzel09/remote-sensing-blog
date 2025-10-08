# 目的
 -  Sentinel-2データの土地利用分類。  
    Sentinel-2 はリモートセンシングでもっともよくつかわれるフリーの高品質なデータですが、  
    そのデータを供給しているESA(欧州宇宙機関）の公式のデータと公式のAPIを使って  
    土地利用分類の分類を自前で学習して分類してようという企画です。
    Google Earth ,AWS などを使うと、API一発で取れたりするデータを、自前で加工していきます。
    一度は、やっておきたいリモートセンシングの基礎操作を実習します。
![review](https://storage.googleapis.com/zenn-user-upload/fc63310d6e90-20250606.jpg)

# 概要
  ESA ( Sentinel-Hub )への登録
  実装  
   1. ESAからとってきた雲の少ない日時のL2A(Sentinel-2のプロダクト）のデータを拾う。
   2. 雲のない部分で複数の日時のデータをESA公式のAPI（Sentinel-Hub）でモザイク処理を行い統合。
   3. ESAから WorldCoverという土地利用分類の教師データを集める。
   4. 自前でNDVI(植生/NDWI・水指数）を特徴量として計算
   5. LightGBMで、学習
   6. LightGBMで推論します。
   7. 結果を
     - **QA60**
     - **s2cloudless**
     - **Cloud Score+**  
  ※ プロダクト（＝製品）  

# 基礎用語説明
   - ## Sentinel-2

| 特性        | 内容                         |
| --------- | -------------------------- |
| 衛星数       | Sentinel-2A, 2B            |
| 再訪間隔      | 約5日（2機体制）                  |
| 空間解像度     | 10m / 20m / 60m（バンドにより異なる） |
| スペクトルバンド数 | 13バンド                      |

他の商用衛星の有料データの中には 0.3m/Pixelの解像度や、 同じ地点を 1時間間隔で撮影するものもあります。

   - **L2A（Level 2A）**
     大気補正後の地表反射率(surface reflectance)データ。Sentinel-2 L2Aプロダクトにはシーン分類マップ（Scene Classification Map, SCL） という各ピクセルが何であるかを分類したデータがあります。下記の様な分類があります。
     - 雲（濃い雲、薄い雲など）
     - 巻雲
     - 雲の影
     - 雪/氷
     - 水域
     - 植生
     - 非植生（裸地、市街地など）
     - その他

 - ## 雲がない地表面を得る前処理
    リモートセンシングでは、雲やその影により正しく地表面を観測できないことが問題になります。完全に快晴な画像を得るのは難しいため、GEEでは複数日からの合成（composite）処理で、雲のないピクセルを抽出する方法があります。今回実装する雲除去アルゴリズムは以下になります。
   - **QA60**
     - Sentinel-2 L2A の付属バンド（QA60）を使って、雲マスクを行う
     - 単純かつ高速だが、精度に限界あり
     - ピクセル単位で「cloud bit」がONの箇所を除去
   - **s2cloudless**
     - 大量の教師データセット（MAJAクラウドマスクなどでラベル付けされたSentinel-2のタイル）を用いて学習された機械学習(LightGBM）モデル
     - 0〜1の雲確率を出力 → 一定しきい値でマスク
     - 可視・赤外バンドを活用し、QA60より高精度

   - **雲被覆率**
     - 衛星画像の中で雲が覆っているピクセルの割合（％表示）
     - GEEではフィルタ条件としても活用可能（例：cloud_cover < 20）
 - ## NDVI (植生/NDWI・水指数）

# ESA ( Sentinel-Hub )への登録

source ./set_env_sentinelhub_mine.sh

# 実装

## 1. 衛星データを取得

```bash
python -m src.pipeline.download --output data/example_run2 \
--config "configs/download_fukuoka.yaml" \
--name fukuoka
```

このスクリプトは、設定ファイル（YAML形式）に記載されたパラメータ（緯度・経度・期間など）に基づき、Sentinel-2 衛星データを自動でダウンロードします。  
主な流れは以下の通りです。

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
python -m src.pipeline.cloud_removal --input-dir "data/example_run/Sentinel-2/fukuoka"
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



