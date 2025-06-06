import numpy as np


def ndvi(nir, red):
    """Compute NDVI."""
    return (nir - red) / (nir + red)


def ndwi(nir, swir):
    """Compute NDWI."""
    return (nir - swir) / (nir + swir)


def compute_features(stack, red_idx, nir_idx, swir_idx):
    """Compute NDVI and NDWI from a band stack."""
    red = stack[red_idx]
    nir = stack[nir_idx]
    swir = stack[swir_idx]
    features = np.stack([ndvi(nir, red), ndwi(nir, swir)])
    return features.astype('float32')
