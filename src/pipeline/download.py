import argparse
from pathlib import Path
import shutil
from ..utils import download_sentinel


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--api-url", default=download_sentinel.DEFAULT_API_URL, help="Sentinel API endpoint")
    args = parser.parse_args()

    out_dir = download_sentinel.download_from_config(args.config, args.output, args.api_url)
    shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
