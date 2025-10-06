from typing import Mapping, Optional, Tuple

import rasterio


def write_raster(
    path,
    array,
    meta,
    colormap: Optional[Mapping[int, Mapping[int, Tuple[int, int, int, int]]]] = None,
):
    """Write a raster array to disk."""
    with rasterio.open(path, 'w', **meta) as dst:
        dst.write(array)
        if colormap:
            for band, cmap in colormap.items():
                dst.write_colormap(band, dict(cmap))
