"""Example pipeline orchestrating remote sensing operations."""

from pathlib import Path

import numpy as np

from . import analysis, data_loader


def run_pipeline(red_path: str | Path, nir_path: str | Path, out_path: str | Path) -> None:
    """Run a simple NDVI computation pipeline."""
    red = data_loader.load_raster(red_path)
    nir = data_loader.load_raster(nir_path)
    ndvi = analysis.compute_ndvi(red, nir)
    data_loader.save_raster(ndvi, out_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Remote sensing NDVI pipeline")
    parser.add_argument("red", help="Path to red band raster")
    parser.add_argument("nir", help="Path to near-infrared band raster")
    parser.add_argument("output", help="Output path for NDVI result")
    args = parser.parse_args()
    run_pipeline(args.red, args.nir, args.output)
