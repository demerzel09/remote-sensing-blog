#!/usr/bin/env python3
import os
import argparse
import boto3
from botocore import UNSIGNED
from botocore.client import Config

def download_worldcover(bucket: str, prefix: str, output_dir: str):
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)

    # 署名なしの S3 クライアントを作成
    s3 = boto3.client(
        "s3",
        config=Config(signature_version=UNSIGNED),
        region_name="eu-central-1",  # 必要に応じて変更
    )

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # ローカルにサブフォルダ構造を再現して保存
            rel_path = key[len(prefix):]
            local_path = os.path.join(output_dir, rel_path)
            local_dir = os.path.dirname(local_path)
            os.makedirs(local_dir, exist_ok=True)

            print(f"Downloading s3://{bucket}/{key} → {local_path}")
            s3.download_file(bucket, key, local_path)

    print("Download complete!")

def main():
    parser = argparse.ArgumentParser(
        description="Download ESA WorldCover tiles from public S3 bucket"
    )
    parser.add_argument(
        "--country", "-c",
        required=True,
        help="Country name (e.g. Japan). (現在はスクリプト内フィルタ未実装)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="出力ディレクトリ (例: data/wc_japan)"
    )
    parser.add_argument(
        "--version", "-v",
        default="v100/2020/map/",
        help="WorldCover バージョンとパスプレフィクス (デフォルト: v100/2020/map/)"
    )
    args = parser.parse_args()

    bucket = "esa-worldcover"
    prefix = args.version

    # （必要であれば country に応じたフィルタ処理をここに追加）
    print(f"Country: {args.country}")
    print(f"Output directory: {args.output}")
    print(f"S3 prefix: {prefix}")

    download_worldcover(bucket, prefix, args.output)

if __name__ == "__main__":
    main()
