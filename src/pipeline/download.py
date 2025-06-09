import argparse
from pathlib import Path
import shutil
from ..utils import download_sentinel


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--sh-base-url",
        help="Sentinel Hub service URL (default: env SH_BASE_URL or Copernicus)",
    )
    parser.add_argument(
        "--sh-auth-base-url",
        help="Sentinel Hub auth URL (default: env SH_AUTH_BASE_URL or Copernicus)",
    )
    args = parser.parse_args()

    out_dir = download_sentinel.download_from_config(
        args.config,
        args.output,
        sh_base_url=args.sh_base_url,
        sh_auth_base_url=args.sh_auth_base_url,
    )
    shutil.copy(args.config, Path(out_dir) / Path(args.config).name)


if __name__ == "__main__":
    main()
