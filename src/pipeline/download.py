import argparse
from pathlib import Path
import shutil
from ..utils.download_sentinel import download_from_config, SH_BASE_URL, SH_TOKEN_URL


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=True, help="Output directory")
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

    out_dir = download_from_config(
        args.config,
        args.output,
        sh_base_url=args.sh_base_url,
        sh_token_url=args.sh_token_url,
    )
    shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
