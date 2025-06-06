# remote-sensing-blog

This repository contains a minimal example of a Python pipeline for basic remote sensing analysis. The code is structured for future extensions such as polygon data integration and asset value analysis.

## Structure

```
remote_sensing/
├── __init__.py
├── analysis.py        # NDVI and other analysis routines
├── data_loader.py     # Input/output helpers for raster data
├── pipeline.py        # Command line pipeline
└── polygon.py         # Placeholder for polygon support
```

## Running the pipeline

The `remote_sensing.pipeline` module exposes a `run_pipeline` function and a simple CLI. It expects preprocessed NumPy arrays for the red and near-infrared bands.

```bash
python -m remote_sensing.pipeline path/to/red.npy path/to/nir.npy path/to/out.npy
```

This will produce an NDVI array saved to the provided output path.

## Future work

- Implement real raster loading and saving using libraries such as `rasterio`.
- Integrate polygon data via `remote_sensing.polygon` to mask areas or join with external datasets.
- Extend the analysis for asset value estimation or other domain specific metrics.

Feel free to adapt the modules or add new ones to suit your workflow.
