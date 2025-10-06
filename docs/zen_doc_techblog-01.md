# 目的
 -  Sentinel-2 (L2A) のデータの扱い方を知る
 -  Google Cloudの **GEE(Google Earth Engine)** を使ってデータを取得
 -  雲のない画像を合成する
![review](https://storage.googleapis.com/zenn-user-upload/fc63310d6e90-20250606.jpg)
# 概要
 - GEE のプロジェクト設置
 - GEE のコードエディタで Sentinel-2 (L2A) を取得し、下記3つの雲マスクアルゴリズムを使用して、東京周辺の雲がないカラー画像を表示し、性能差を比較。
     - **QA60**
     - **s2cloudless**
     - **Cloud Score+**
 - 結果を GeoTIFF（リモートセンシング用の位置情報を含む画像フォーマット）として Google Drive に書き出す
# 衛星データの基本知識
リモートセンシングは幅広く奥深い分野で、衛星ごとのデータ仕様、前処理の段階、空間・時間解像度などを理解するのにある程度の学習が必要です。

- ## 衛星の種類
    - **マルチバンド光学衛星**
      - 可視光〜近赤外（VNIR〜SWIR）を複数のバンドで観測。
      - 主に植生、水域、都市の分類などに利用。
    - **SAR衛星**
      - マイクロ波（レーダー）を使った能動センサー。
      - 雲や夜間でも観測可能（全天候型）
    - **ハイパースペクトル衛星**
      - 数十〜数百の連続したスペクトルバンド。
      - 植生の種類、鉱物識別、水質分析など「物質の識別」に強い
    - **静止気象衛星**
      - 地球の自転と同期 → 常に同じ地域を観測。
      - 空間解像度は低めだが高頻度（10分毎など）


　　今回はマルチバンド光学衛星である Sentinel-2を扱います。

 - ## Sentinel-2

| 特性        | 内容                         |
| --------- | -------------------------- |
| 衛星数       | Sentinel-2A, 2B            |
| 再訪間隔      | 約5日（2機体制）                  |
| 空間解像度     | 10m / 20m / 60m（バンドにより異なる） |
| スペクトルバンド数 | 13バンド                      |

他の商用衛星の有料データの中には 0.3m/Pixelの解像度や、 同じ地点を 1時間間隔で撮影するものもあります。

 - ## 前処理 L1C / L2A　の違い
   衛星データには前処理のレベルが定義されており、Sentinel-2 では以下が代表的です

   - **L1C（Level 1C）**
   幾何補正・放射補正済みのTOA(top of atmosphere)反射率を持つデータ
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

[【図解】衛星データの前処理とは (**宙畑**からの参照）](https://sorabatake.jp/9192/)
![image12-2.png](https://sorabatake.jp/wp-content/uploads/2019/12/image12-2.png)

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
   - **Cloud Score+**
     - Googleが開発した cloudScore アルゴリズムの進化版（Google提供の実験的アルゴリズム）
     - 複数の指数（輝度、NDVI、NDSIなど）を組み合わせてスコア化
     - 雲以外の条件（雪、影、異常値）にも対応
 - ## 他用語 ##
   - **雲被覆率**
     - 衛星画像の中で雲が覆っているピクセルの割合（％表示）
     - GEEではフィルタ条件としても活用可能（例：cloud_cover < 20）
   - **GeoTIFF**
     - 地理参照情報（座標系・解像度など）を持つ画像ファイル形式。GISやQGISなどのソフトでも利用可能。
# Google Cloud の Google Earth Engine (GEE) について
 - 衛星画像、気象データ、地形データなどのパブリックデータがクラウドに保管済み
 - GEEの Code Editorで使える Earth Engine API が用意されており、JavaScript または Python API を使ってブラウザから直接分析・可視化が可能
 - 計算処理は Google のクラウドで実行されるためローカルに負担なし
 - 結果の可視化やダウンロード、Google Drive/Cloud Storageへのエクスポートにも対応

# 実装
## 1. Google Cloud で Earth Engine API を有効化
[Google Cloud](https://cloud.google.com/?hl=ja)  
1. **コンソール メニューへ**
![gcp_start](https://storage.googleapis.com/zenn-user-upload/ad66b440f01e-20250603.jpg)

2. **プロジェクトの作成**
![new_project](https://storage.googleapis.com/zenn-user-upload/a881258ff17f-20250603.jpg)
3. **(Google Cloud タイトル横）三本線ナビゲーションメニュー**  
4. **APIとサービス**     
5. **ライブラリ**   
6. **“Earth Engine API” を検索**   
7. **Google Earth Engine APIを選択し　有効（Enable）をクリック**  
  
## 2. Code Editor にログイン
 1. **Earth Engineのコードエディタにログイン**
[Earth Engine コードエディタ](https://code.earthengine.google.com/)
![GeeCodeEditoror](https://storage.googleapis.com/zenn-user-upload/e144c7a44bdb-20250603.jpg)

2. **I’M AUTHORIZED FOR AN EXISTING CLOUD PROJECT**
3. **先ほどつくった GEEの Google Cloud Projectを選択**
4. **REGISTER PROJECTを選択して先にすすむ**
5. **料金プランを設定する**
社内検証だけなら限定プランで十分です。今回の検証程度であればで課金は発生しません。
EECU（計算量: Earth Engine Compute Units）クォータに達したら処理を分割するか日を改めて実行すれば OK です。
7. **GEE APIを動かす準備が完了しました。**
![CodeEditorAvailable](https://storage.googleapis.com/zenn-user-upload/56f0eafc1ded-20250606.jpg)

## 3 . Sentinel-2を読み込み、雲のない地表面を得る
最初にすべてのコードを示します。
 - 3/15 ～ 5/15 の雲被覆率40%未満のデータをフィルタリングして、元データとする
 - 下記雲除去アルゴリズムを可視化
   - QA60
   - s2cloudless
   - Cloud Score+
 - GeoTIFFとしてGoogle Driveに書き出す
   
```js
// 関心領域（AOI）をポリゴン or Point で定義-------------
var AOI   = ee.Geometry.Point([139.766, 35.681]); // 東京駅
var START = '2024-03-15';
var END   = '2024-05-15';
//var START = '2024-04-01';
//var END   = '2024-04-30';

// Sentinel-2 SR コレクションを呼び出し-------------------------
var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(AOI)
            .filterDate(START, END)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 40)); // 雲被覆率
print('S2_SR 枚数', s2.size());

// (A) QA60 を使ったマスク処理関数-----------------------------
function mask_QA60(img){
  var qa     = img.select('QA60');
  var fill   = 1 << 0;    // データなし フラグ
  var cloud  = 1 << 10;   // 雲 フラグ
  var cirrus = 1 << 11;   // 薄雲 フラグ
  
  var mask = qa.bitwiseAnd(fill).eq(0)             // 有効データ
               .and( qa.bitwiseAnd(cloud ).eq(0) ) // 雲なし
               //.and( qa.bitwiseAnd(cirrus).eq(0) ); // 薄雲 は誤判定が多い水面で外す場合コメントアウト
  return img.updateMask(mask)
            .divide(10000)
            .copyProperties(img, ['system:time_start']);
}
var s2_QA60 = s2.map(mask_QA60);
var comp_QA60 = s2_QA60.median();

// (B) s2cloudless (雲確率 < 40 %) ------------------------------
var clp = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
             .filterBounds(AOI)
             .filterDate(START, END);

function mask_s2cloudless(img){
  // 同じ system:index を持つ確率画像を 1 枚だけ取得
  var prob = clp.filter(ee.Filter.eq('system:index', img.get('system:index')))
                .first()
                .select('probability');
  var mask = prob.lt(40);                         // 確率しきい値
  return img.updateMask(mask)
            .divide(10000)
            .copyProperties(img, ['system:time_start']);
}
var s2_CL = s2.map(mask_s2cloudless);
var comp_CL = s2_CL.median();

// (C) Cloud Score+ (cs ≥ 0.6 がクリア) ---------------------------------
var csCol = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
               .filterBounds(AOI)
               .filterDate(START, END);

function mask_CS(img){
  var cs = csCol.filter(ee.Filter.eq('system:index', img.get('system:index')))
                .first()
                .select('cs');
  var mask = cs.gte(0.6);                         // 0.6 = 60 % 以上クリア
  return img.updateMask(mask)
            .divide(10000)
            .copyProperties(img, ['system:time_start']);
}
var s2_CS = s2.map(mask_CS);
var comp_CS = s2_CS.median();

// 欠損ピクセルをシアンで可視化 (QA60 合成を例) -------------------------------
var nodataMask = comp_QA60.mask()
                  .reduce(ee.Reducer.allNonZero())
                  .not()
                  .selfMask();

// 表示 -----------------------------------------------------------------
Map.centerObject(AOI, 12);
Map.addLayer(nodataMask, {palette:['00FFFF']}, 'nodata (cyan)');
Map.addLayer(comp_QA60, {bands:['B4','B3','B2'], min:0, max:0.3}, 'RGB – QA60');
Map.addLayer(comp_CL ,  {bands:['B4','B3','B2'], min:0, max:0.3}, 'RGB – s2cloudless');
Map.addLayer(comp_CS ,  {bands:['B4','B3','B2'], min:0, max:0.3}, 'RGB – Cloud Score+');

// -----------------------------------------------------------
// 追加：GeoTIFFとしてGoogle Driveに書き出す（Export.image.toDrive）
// -----------------------------------------------------------

// エクスポート範囲を「AOI周辺の矩形領域」に設定
// AOI が点なので、バッファをつけて四角形にしておく
var exportRegion = AOI.buffer(5000).bounds(); // 半径5kmの矩形範囲

// (1) QA60 合成画像をエクスポート
Export.image.toDrive({
  image: comp_QA60.select(['B4','B3','B2']), // 必要なバンドのみ
  description: 'Sentinel2_QA60_composite',    // タスク名（途中で確認可能）
  folder: 'EarthEngineExports',               // Google Drive フォルダ名（任意）
  fileNamePrefix: 'QA60_composite_202404',     // ファイル名プレフィックス
  region: exportRegion,                       // エクスポート範囲
  scale: 10,                                  // 10m 解像度
  crs: 'EPSG:3857',                           // 座標参照系（Web Mercator 例）
  fileFormat: 'GeoTIFF',
  maxPixels: 1e13                             // 大きな画像でもエラー回避
});

// (2) s2cloudless 合成画像をエクスポート
Export.image.toDrive({
  image: comp_CL.select(['B4','B3','B2']),
  description: 'Sentinel2_s2cloudless_composite',
  folder: 'EarthEngineExports',
  fileNamePrefix: 's2cloudless_composite_202404',
  region: exportRegion,
  scale: 10,
  crs: 'EPSG:3857',
  fileFormat: 'GeoTIFF',
  maxPixels: 1e13
});

// (3) Cloud Score+ 合成画像をエクスポート
Export.image.toDrive({
  image: comp_CS.select(['B4','B3','B2']),
  description: 'Sentinel2_CloudScorePlus_composite',
  folder: 'EarthEngineExports',
  fileNamePrefix: 'CloudScorePlus_composite_202404',
  region: exportRegion,
  scale: 10,
  crs: 'EPSG:3857',
  fileFormat: 'GeoTIFF',
  maxPixels: 1e13
});

```
このコードを動かすと、Sentinel-2の過去60日間における 雲被覆率40%以下のデータをフィルタリングして5つのデータを抽出、それぞれ雲を除去して日時が違う5つのデータを合成した画像を表示します。
![RemovedCloud](https://storage.googleapis.com/zenn-user-upload/2c4df294e058-20250604.jpg)*雲のない地表面の合成画像*  

## 4 . 各雲除去アルゴリズムの比較
前項の画像では、３つのアルゴリズムのレイヤーを以下のLayersのチェックボックスで表示/非表示ができます。
 - **QA60**
 - **s2cloudless**
 - **Cloud Score+**
![layer_select](https://storage.googleapis.com/zenn-user-upload/148e7bafb25e-20250604.jpg)*表示レイヤーの切替*

現在のコードの設定では、どれもさほど違いがわかりません。そこで3つのアルゴリズムの性能の違いがわかるように期間と雲被覆率を変更し、1つのデータしか取れないように調整してみました。
・期間：04/01～04/30 （60→30日間）
・雲被覆率：30%（40→30%）


**QA60：**
 - 雲を検出できていない場合が多い。
![QA60](https://storage.googleapis.com/zenn-user-upload/11e08db63e6d-20250604.jpg)

**s2cloudless：**
 - 雲影は除外 (※)
 - 水域を雲と誤検出する場合がある
 - 雲をクリアーとの境界付近で完全にカバーできない場合がある。
  ※ 雲影はアルゴリズム的には検出可能
![s2cloudless](https://storage.googleapis.com/zenn-user-upload/d96e6e3a230f-20250604.jpg)

**Cloud Score+：**
 - 雲影も含んでいる
 - 誤検出が少ない
 - 雲をクリアーとの境界付近もカバーできている
![Cloud ScorePlus](https://storage.googleapis.com/zenn-user-upload/a3cfb80acb86-20250604.jpg)

### s2cloudless vs Cloud Score+ ###
細かくみると、
s2cloudless：
・薄雲の検出できてないところあり
・水域や物体の境界付近の検出がうまくいっていない
Cloud Score+:
・雲検出に対してRecall 重視 (検出漏れをできるだけ排除）
![compare_algo](https://storage.googleapis.com/zenn-user-upload/51c10e8fec33-20250604.jpg)

Cloud Score+は、雲除去の目的にかなっているといえます。

## GeoTIFFとしてGoogle Driveに書き出す
Code EditorでコードのRunを実行したあと、右のウィンドウの Taskタブの、それぞれの 雲除去レイヤーの ”Export.image.toDrive”に対応するタスクを Runすると、アカウントのGoogleDriveのマイドライブに、地理情報がはいった、TIFF ファイルが出力されます。（下図）

![export_google_drive](https://storage.googleapis.com/zenn-user-upload/fbd35bfd0c4f-20250606.jpg)

このTIFFファイルは衛星データ用のビューアーのQGISなど、TIFFファイルを閲覧できるアプリケーションでみることができます。（下図）

![qgis_tiff](https://storage.googleapis.com/zenn-user-upload/bf0862edf83d-20250606.jpg)

# まとめ
本記事では、衛星データの基本を知り、Google Earth Engine を用いて Sentinel-2 (L2A) データの雲除去処理を実装してみました。また、3つのアルゴリズムの性能を比較し、以下の知見を得ました。

 - QA60：処理が簡単で高速だが、精度に限界がある
 - s2cloudless：マシンラーニングベースの高精度手法。水域や薄雲の扱いに注意が必要
 - Cloud Score+：雲影もカバーし、最も網羅的な雲除去が可能（検出漏れが少ない）

結果として、Cloud Score+ は誤検出が少なく、薄雲や雲影にも強いため、地表面の解析において有効な手法であることが確認できました。

今後は、NDVI(植生を表す指標)などの指標計算への応用も検討していきたいと思います。



