import argparse
from pathlib import Path
import shutil
from ..utils.download_sentinel import (
    download_from_config,
    SH_BASE_URL,
    SH_TOKEN_URL,
)



def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--name",
        help="Optional subfolder name created under the output directory",
    )
    parser.add_argument(
        "--sh-base-url",
        default=SH_BASE_URL,
        type=str,
        help="Sentinel Hub service URL",
    )
    parser.add_argument(
        "--sh-token-url",
        default=SH_TOKEN_URL,
        type=str,
        help="Sentinel Hub auth URL",
    )
    args = parser.parse_args()

    base_dir = Path(args.output)
    if args.name:
        base_dir = base_dir / args.name

    out_dir = download_from_config(
        args.config,
        base_dir,
        sh_base_url=args.sh_base_url,
        sh_token_url=args.sh_token_url,
    )
    # Later pipeline stages expect the config file to be named
    # ``download.yaml`` inside the download directory.
    shutil.copy(args.config, Path(out_dir) / "download.yaml")


if __name__ == "__main__":
    main()
