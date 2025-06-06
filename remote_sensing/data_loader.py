"""Utility functions for loading remote sensing datasets."""

from pathlib import Path
from typing import Any

import numpy as np


def load_raster(path: str | Path) -> np.ndarray:
    """Load a raster image from disk into a NumPy array."""
    path = Path(path)
    # Placeholder for actual raster reading logic.
    return np.load(path)


def save_raster(array: np.ndarray, path: str | Path) -> None:
    """Save a NumPy array as a raster image."""
    path = Path(path)
    # Placeholder for actual raster writing logic.
    np.save(path, array)
