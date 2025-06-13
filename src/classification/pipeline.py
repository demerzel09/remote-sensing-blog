import argparse
import rasterio

from ..preprocess.cloudmask import cloud_mask
from ..preprocess.stack_bands import stack_bands
from ..preprocess.features import compute_features
from .train_model import train_model
from .predict import predict_model


def main():
    parser = argparse.ArgumentParser(description="Sentinel-2 land use classification pipeline")
    parser.add_argument(
        "--bands",
        nargs=5,
        metavar="BAND",
        help="Paths to Sentinel-2 bands (B02,B03,B04,B08,B11)",
    )
    parser.add_argument("--scl", required=True, help="Path to SCL scene classification band")
    parser.add_argument(
        "--mask",
        help="Optional dataMask band where 0 denotes invalid pixels",
    )
    parser.add_argument("--labels", required=True, help="Raster path with training labels")
    parser.add_argument("--output", default="outputs/prediction.tif", help="Output path for classification result")
    parser.add_argument("--n_estimators", type=int, default=100, help="Number of trees for RandomForest")
    args = parser.parse_args()

    mask = cloud_mask(args.scl, args.mask)
    stack, meta = stack_bands(args.bands, mask)

    # Sentinel-2 indices: provided order is B02, B03, B04, B08, B11
    red_idx = 2
    nir_idx = 3
    swir_idx = 4
    features = compute_features(stack, red_idx=red_idx, nir_idx=nir_idx, swir_idx=swir_idx)

    with rasterio.open(args.labels) as src:
        labels = src.read(1)

    clf = train_model(features, labels, n_estimators=args.n_estimators)

    predict_model(clf, features, meta, args.output)


if __name__ == "__main__":
    main()
