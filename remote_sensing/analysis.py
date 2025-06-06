"""Basic analysis routines for remote sensing data."""

import numpy as np


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Compute the Normalized Difference Vegetation Index (NDVI)."""
    red = red.astype(float)
    nir = nir.astype(float)
    ndvi = (nir - red) / (nir + red + 1e-9)
    return ndvi
