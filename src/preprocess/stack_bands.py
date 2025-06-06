import numpy as np
import rasterio


def stack_bands(band_paths, mask):
    """Stack multiple bands applying a cloud mask."""
    arrays = []
    meta = None
    for path in band_paths:
        with rasterio.open(path) as src:
            band = src.read(1)
            if meta is None:
                meta = src.meta.copy()
            band = np.where(mask, np.nan, band)
            arrays.append(band)
    stack = np.stack(arrays)
    meta.update(count=len(band_paths), dtype='float32')
    return stack.astype('float32'), meta
