import numpy as np
from ..utils import io_raster


def predict_model(clf, features, meta, output_path):
    """Generate a classification raster using a trained model."""
    X = features.reshape(features.shape[0], -1).T
    nodata = np.isnan(X).any(axis=1)
    preds = np.zeros(X.shape[0], dtype=np.uint8)
    valid_idx = ~nodata
    preds[valid_idx] = clf.predict(X[valid_idx])
    pred_raster = preds.reshape(features.shape[1:])
    meta = meta.copy()
    meta.update(count=1, dtype='uint8', nodata=0)
    io_raster.write_raster(output_path, pred_raster[np.newaxis, ...], meta)
    return pred_raster
