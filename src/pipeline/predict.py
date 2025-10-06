import argparse
import json
import joblib
import shutil
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import rasterio
import yaml

from ..classification.predict import predict_model
from ..preprocess.cloudmask import cloud_mask
from ..preprocess.stack_bands import stack_bands
from ..preprocess.features import compute_features
from .preprocess import split_band_stack
from ..utils.io_raster import write_raster


def _safe_divide(numerator: float, denominator: float) -> Optional[float]:
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


def _compute_core_metrics(
    predictions: np.ndarray, labels: np.ndarray
) -> Optional[Dict[str, object]]:
    # Treat label value 0 as background / nodata and exclude it from evaluation.
    valid_mask = labels > 0
    if not np.any(valid_mask):
        return None

    pred_flat = predictions[valid_mask].ravel()
    label_flat = labels[valid_mask].ravel()

    positive_labels = {int(c) for c in np.unique(label_flat) if c > 0}
    positive_preds = {int(c) for c in np.unique(pred_flat) if c > 0}
    class_id_set = positive_labels | positive_preds
    has_unclassified = np.any(pred_flat <= 0)
    if has_unclassified:
        class_id_set.add(0)

    if not class_id_set:
        return None

    class_ids = sorted(class_id_set)
    class_to_index = {cls: idx for idx, cls in enumerate(class_ids)}
    matrix = np.zeros((len(class_ids), len(class_ids)), dtype=int)

    for true_val, pred_val in zip(label_flat, pred_flat):
        true_cls = int(true_val)
        if true_cls <= 0:
            continue
        pred_cls = int(pred_val) if int(pred_val) > 0 else 0 if has_unclassified else int(pred_val)
        matrix[class_to_index[true_cls], class_to_index[pred_cls]] += 1

    totals = label_flat.size
    if totals == 0:
        return None

    diagonal = np.diag(matrix)
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)

    producer_accuracy: Dict[str, Optional[float]] = {}
    user_accuracy: Dict[str, Optional[float]] = {}
    f1_per_class: Dict[str, Optional[float]] = {}

    eval_indices = [i for i, cls in enumerate(class_ids) if cls > 0]

    for idx in eval_indices:
        cls = class_ids[idx]
        recall = _safe_divide(diagonal[idx], row_sums[idx])
        precision = _safe_divide(diagonal[idx], col_sums[idx])

        producer_accuracy[str(cls)] = recall
        user_accuracy[str(cls)] = precision

        if recall is None or precision is None:
            f1_per_class[str(cls)] = None
        elif recall == 0 and precision == 0:
            f1_per_class[str(cls)] = 0.0
        else:
            f1_per_class[str(cls)] = 2 * precision * recall / (precision + recall)

    f1_values = [v for v in f1_per_class.values() if v is not None]
    macro_f1 = _safe_divide(sum(f1_values), len(f1_values)) if f1_values else None

    correct = sum(int(diagonal[idx]) for idx in eval_indices)
    overall_accuracy = _safe_divide(correct, totals)

    producer_accuracy = {
        cls: (float(val) if val is not None else None)
        for cls, val in producer_accuracy.items()
    }
    user_accuracy = {
        cls: (float(val) if val is not None else None)
        for cls, val in user_accuracy.items()
    }
    f1_per_class = {
        cls: (float(val) if val is not None else None)
        for cls, val in f1_per_class.items()
    }

    classes = [int(cls) for cls in class_ids]
    overall_accuracy = overall_accuracy if overall_accuracy is None else float(overall_accuracy)
    macro_f1 = macro_f1 if macro_f1 is None else float(macro_f1)

    return {
        "classes": classes,
        "confusion_matrix": matrix.tolist(),
        "overall_accuracy": overall_accuracy,
        "producer_accuracy": producer_accuracy,
        "user_accuracy": user_accuracy,
        "f1_per_class": f1_per_class,
        "macro_f1": macro_f1,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run model inference")
    parser.add_argument("--config", required=True, help="YAML config file")
    parser.add_argument("--input-dir", required=True, help="Directory containing the dataset")
    parser.add_argument("--model-dir", required=True, help="Directory with trained model")
    parser.add_argument("--output-dir", required=True, help="Directory for prediction result")
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    input_dir = Path(args.input_dir)
    model_dir = Path(args.model_dir)
    output_dir = Path(args.output_dir)

    features_path = input_dir / "preprocess" / cfg["features"]
    if features_path.exists():
        data = np.load(features_path)["features"]
        meta_path = (
            input_dir
            / "preprocess"
            / Path(cfg.get("meta", Path(cfg["features"]).with_suffix(".meta.json"))).name
        )
        with open(meta_path) as f:
            meta = json.load(f)
    else:
        dl_cfg_path = input_dir / "download.yaml"
        if dl_cfg_path.exists():
            dl_cfg = yaml.safe_load(dl_cfg_path.read_text())
            spectral = [b for b in dl_cfg.get("bands", []) if b not in {"SCL", "dataMask"}]
            stack = input_dir / "BANDS.tif"
            if stack.exists():
                missing = [b for b in spectral if not (input_dir / f"{b}.tif").exists()]
                if missing:
                    split_band_stack(stack, spectral)
            else:
                raise ValueError("BANDS.tif not found in input directory")

            bands = [input_dir / f"{b}.tif" for b in spectral]
            scl_path = input_dir / "SCL.tif" if "SCL" in dl_cfg.get("bands", []) else input_dir / Path(cfg["scl"]).name
            mask_path = (
                input_dir / "MASK.tif"
                if "dataMask" in dl_cfg.get("bands", [])
                else input_dir / Path(cfg.get("mask", "")).name
                if cfg.get("mask")
                else None
            )
        else:
            bands = [input_dir / Path(p).name for p in cfg["bands"]]
            scl_path = input_dir / Path(cfg["scl"]).name
            mask_path = input_dir / Path(cfg.get("mask", "")).name if cfg.get("mask") else None

        mask = cloud_mask(scl_path, mask_path)
        stack, meta = stack_bands(bands, mask)
        data = compute_features(stack, red_idx=2, nir_idx=3, swir_idx=4)

    clf = joblib.load(model_dir / cfg["model"])
    out_path = output_dir / "prediction.tif"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    predictions = predict_model(clf, data, meta, out_path)

    labels_path = input_dir / cfg.get("labels", "labels.tif")
    if labels_path.exists():
        with rasterio.open(labels_path) as src:
            labels = src.read(1)

        if labels.shape != predictions.shape:
            raise ValueError(
                "Shape mismatch between predictions and labels: "
                f"{predictions.shape} vs {labels.shape}"
            )

        metrics = _compute_core_metrics(predictions, labels)

        # Export a difference heatmap (absolute class gap) for visual inspection.
        difference_path = out_path.parent / "difference.tif"
        visual_difference = np.full(predictions.shape, 255, dtype=np.uint8)
        valid_diff_mask = labels > 0
        if np.any(valid_diff_mask):
            label_vals = labels[valid_diff_mask].astype(np.int32)
            pred_vals = predictions[valid_diff_mask].astype(np.int32)
            abs_diff = np.abs(label_vals - pred_vals)

            max_gap = int(abs_diff.max()) if abs_diff.size else 0
            mismatch_pixels = int(np.count_nonzero(abs_diff))
            total_pixels = int(abs_diff.size)
            mean_gap = float(abs_diff.mean()) if abs_diff.size else 0.0

            if max_gap == 0:
                scaled = np.zeros_like(abs_diff, dtype=np.uint8)
            else:
                scaled = np.rint((abs_diff / max_gap) * 254).astype(np.uint8)

            visual_difference[valid_diff_mask] = scaled

            diff_meta = meta.copy()
            diff_meta.update(count=1, dtype="uint8", nodata=255)
            write_raster(
                difference_path,
                visual_difference[np.newaxis, ...],
                diff_meta,
            )

            if metrics is not None:
                metrics["difference_summary"] = {
                    "max_gap": max_gap,
                    "mean_gap": mean_gap,
                    "mismatch_rate": _safe_divide(mismatch_pixels, total_pixels),
                    "scaling": {
                        "nodata": 255,
                        "max_gap_encoded_as": 254,
                    },
                }

        if metrics is not None:
            metrics_path = out_path.parent / "metrics.json"
            with open(metrics_path, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

    shutil.copy(args.config, out_path.parent / Path(args.config).name)


if __name__ == "__main__":
    main()
