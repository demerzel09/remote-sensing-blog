import argparse
from pathlib import Path

from ..utils.cloud_removal_sentinel import apply_cloud_mask_to_directory


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove cloudy pixels from each dated Sentinel-2 folder"
    )
    parser.add_argument(
        "--input-dir", required=True, help="Directory containing dated scenes"
    )
    args = parser.parse_args()

    apply_cloud_mask_to_directory(Path(args.input_dir))


if __name__ == "__main__":
    main()
