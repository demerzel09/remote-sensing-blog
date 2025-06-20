import argparse
from pathlib import Path

from ..utils.mosaic import mosaic_sentinel_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mosaic dated Sentinel-2 folders into a single stack"
    )
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing dated scenes"
    )
    parser.add_argument(
        "--method", default="best", choices=["best", "median"],
        help="Pixel compositing strategy"
    )
    args = parser.parse_args()

    mosaic_sentinel_directory(Path(args.input_dir), method=args.method)


if __name__ == "__main__":
    main()
