import argparse
from pathlib import Path
import shutil
import yaml

from ..utils import download_sentinel


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    args = parser.parse_args()

    out_dir = download_sentinel.download_from_config(args.config)
    shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
