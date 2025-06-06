import rasterio


def write_raster(path, array, meta):
    """Write a raster array to disk."""
    with rasterio.open(path, 'w', **meta) as dst:
        dst.write(array)
