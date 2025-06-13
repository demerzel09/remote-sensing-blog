import numpy as np
import rasterio


def cloud_mask(scl_path, mask_path=None, cloudy_values=(3, 7, 8, 9, 10, 11)):
    """Return a boolean cloud mask from Sentinel‑2 ``SCL``/``dataMask`` bands.

    Parameters
    ----------
    scl_path : str
        Path to the ``SCL`` scene classification band.
    mask_path : str, optional
        Optional ``dataMask`` band where 0 denotes invalid pixels.
    cloudy_values : tuple of int
        ``SCL`` values treated as cloudy. Defaults to shadow and cloud classes.

    Returns
    -------
    numpy.ndarray
        Boolean array where ``True`` indicates cloud or invalid pixels.
    """
    with rasterio.open(scl_path) as src:
        scl = src.read(1)
    mask = np.isin(scl, cloudy_values)
    if mask_path:
        with rasterio.open(mask_path) as src:
            data_mask = src.read(1)
        mask |= data_mask == 0
    return mask
