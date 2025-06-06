import numpy as np
import rasterio


def cloud_mask(qa_path, cloud_bits=(3, 5)):
    """Derive a boolean cloud mask from a QA band.

    Parameters
    ----------
    qa_path : str
        Path to QA band raster.
    cloud_bits : tuple of int
        Bit positions indicating cloud information.

    Returns
    -------
    numpy.ndarray
        Boolean array where True indicates cloud pixels.
    """
    with rasterio.open(qa_path) as src:
        qa = src.read(1)
    mask = np.zeros_like(qa, dtype=bool)
    for bit in cloud_bits:
        mask |= (qa & (1 << bit)) > 0
    return mask
