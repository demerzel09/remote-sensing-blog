import argparse
from pathlib import Path
import shutil

import yaml
from ..utils.download_sentinel import (
    SH_BASE_URL,
    SH_TOKEN_URL,
)

def main() -> None:
    parser = argparse.ArgumentParser(description="Download Sentinel data using a config file")
    parser.add_argument("--config", required=True, help="Path to YAML config")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument(
        "--name",
        help="Optional folder name placed under the satellite directory",
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
    print(f"config file = {args.config}")
    # out_dir = download_from_config(
    #     args.config,
    #     base_dir,
    #     sh_base_url=args.sh_base_url,
    #     sh_token_url=args.sh_token_url,
    #     name=args.name,
    # )
    
    # ここで一度だけ YAML を読み、provider を判定
    with open(args.config, "r", encoding="utf-8") as f:
        _cfg = yaml.safe_load(f) or {}
    provider = _cfg.get("provider", "sentinel_hub")

    if provider == "aws_cog":
        # AWS ルート（新規）
        from ..utils.download_aws import download_from_config as aws_download_from_config
        out_dir = aws_download_from_config(
            args.config,
            base_dir,
            name=args.name,
        )
    else:
        from ..utils.download_sentinel import download_from_config as sh_download_from_config
        # 既存 Sentinel Hub ルート（後方互換）
        out_dir = sh_download_from_config(
            args.config,
            base_dir,
            sh_base_url=args.sh_base_url,
            sh_token_url=args.sh_token_url,
            name=args.name,
        )
    
    # Later pipeline stages expect the config file to be named
    # ``download.yaml`` inside the download directory.
    shutil.copy(args.config, Path(out_dir) / "download.yaml")


if __name__ == "__main__":
    main()
