# Land Cover Classification Evaluation Metrics

Remote sensing land cover classification models are commonly evaluated with categorical metrics derived from comparisons between model predictions and ground-truth labels (e.g., GT GeoTIFFs).

## Recommended Core Metrics

多クラス土地被覆分類の実務評価では、以下の組み合わせを用いるのが一般的です。

1. **混同行列** – まず全クラスの混同行列を作成し、誤分類の傾向を把握します。
2. **全体精度 (Overall Accuracy)** – 全体の達成度を一目で把握する指標として併記します。
3. **クラス別のプロデューサズ精度 (PA) とユーザーズ精度 (UA)** – 欠落誤差・過剰誤差を定量化し、どのクラスが課題かを診断します。
4. **F1 スコア（マクロ平均）** または **IoU / mIoU** – クラス不均衡に強い代表的な統合指標として、多クラス平均値を報告します。ピクセル単位のセマンティックセグメンテーションでは mIoU がよく採用されます。

このセットをベースに、必要に応じて下記の補助指標を追加すると、報告内容に厚みが出ます。

## Confusion Matrix
- **Definition:** A contingency table that compares predicted classes versus ground-truth classes for every pixel.
- **Use:** Serves as the basis for most other metrics and allows visual inspection of systematic confusion between classes.

## Overall Accuracy (OA)
- **Definition:** The proportion of correctly classified pixels across all classes.
- **Interpretation:** Easy to understand but can be dominated by large or majority classes.

## Producer's Accuracy and User's Accuracy
- **Producer's Accuracy (PA):** For a given class, PA = correctly predicted pixels of that class / total ground-truth pixels of that class. It measures omission errors (how often true class pixels are missed).
- **User's Accuracy (UA):** For a given class, UA = correctly predicted pixels of that class / total predicted pixels of that class. It measures commission errors (how often predicted class pixels are incorrect).

### Visualizing differences between `prediction.tif` and `labels.tif`

- **Difference heatmap (`difference.tif`):** Exporting the per-pixel absolute class gap (|prediction − label|) as a GeoTIFF produces a heatmap-style layer where 0 denotes perfect agreement and larger values highlight pixels with greater disagreement. Pixels without GT labels remain nodata. 予測とGTが一致した画素は 0、もっとも差が大きかった画素は 254 として 8bit スケーリングされ、さらに小さな差でも視認できるよう平方根（γ=0.5）でコントラストを強調し、最低でも 32 以上の輝度に持ち上げています（255 は nodata）。K→B→C→Y→R の順で滑らかに変化するカラーマップを埋め込んでいるため、そのままGISに読み込んでもヒートマップとして可視化できます。`metrics.json` には元のギャップ統計値（最大値、平均値、ミスマッチ率）が保存され、数値的な確認にも利用できます。
- **Use UA when overestimation matters:** UA drops when many predicted pixels for a class are false positives, so it is the better scalar indicator of "over-mapping" a class relative to the ground truth.
- **Use PA when underestimation matters:** PA decreases when ground-truth pixels are missed (false negatives), making it the preferred metric when you care about areas where the model fails to map existing class extents.
- **Pair the map with PA/UA:** The heatmap shows *where* large discrepancies occur, while UA pinpoints classes responsible for commission errors and PA highlights classes suffering omission errors. Reviewing both gives a balanced explanation for the intensity patterns in the difference layer.

## F1 Score
- **Definition:** Harmonic mean of precision (UA) and recall (PA) per class, i.e., F1 = 2 × (Precision × Recall) / (Precision + Recall).
- **Variants:** Macro-averaged F1 treats each class equally, while weighted F1 scales by class prevalence.

## Intersection over Union (IoU)
- **Definition:** IoU = True Positives / (True Positives + False Positives + False Negatives) for each class.
- **Mean IoU (mIoU):** Average IoU across classes; robust to class imbalance compared to OA.

## Cohen's Kappa Coefficient
- **Definition:** Measures agreement between predictions and ground truth after accounting for agreement expected by chance.
- **Interpretation:** Useful when class imbalance is present; values range from -1 (complete disagreement) to 1 (perfect agreement).

## Balanced Accuracy
- **Definition:** Average of per-class recall (PA). Equivalent to the mean of the diagonal of the normalized confusion matrix by ground-truth counts.
- **Use:** Mitigates bias towards majority classes.

## Area-Adjusted Accuracy Metrics
- **Context:** When validation data come from stratified sampling, accuracy estimates can be adjusted to account for unequal area representation per class, providing unbiased regional accuracy estimates.

## Spatially Aware Metrics (Optional)
- **Examples:** Boundary F1 scores, structural similarity, or clump-based accuracies that consider neighborhood coherence.
- **Use:** Helpful when map smoothness or spatial patterns are critical, though they are more complex to compute.

## Practical Considerations
- **Cross-Validation:** Split labeled data spatially to avoid spatial autocorrelation bias when estimating metrics.
- **Confidence Intervals:** Bootstrap resampling over tiles or polygons provides uncertainty ranges for reported metrics.

