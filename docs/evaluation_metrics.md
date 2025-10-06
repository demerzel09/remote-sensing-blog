# Land Cover Classification Evaluation Metrics

Remote sensing land cover classification models are commonly evaluated with categorical metrics derived from comparisons between model predictions and ground-truth labels (e.g., GT GeoTIFFs). The following indicators are widely used when assessing pixel-level predictions.

## Confusion Matrix
- **Definition:** A contingency table that compares predicted classes versus ground-truth classes for every pixel.
- **Use:** Serves as the basis for most other metrics and allows visual inspection of systematic confusion between classes.

## Overall Accuracy (OA)
- **Definition:** The proportion of correctly classified pixels across all classes.
- **Interpretation:** Easy to understand but can be dominated by large or majority classes.

## Producer's Accuracy and User's Accuracy
- **Producer's Accuracy (PA):** For a given class, PA = correctly predicted pixels of that class / total ground-truth pixels of that class. It measures omission errors (how often true class pixels are missed).
- **User's Accuracy (UA):** For a given class, UA = correctly predicted pixels of that class / total predicted pixels of that class. It measures commission errors (how often predicted class pixels are incorrect).

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

