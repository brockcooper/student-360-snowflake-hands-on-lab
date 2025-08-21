#!/usr/bin/env python3
"""
Upload local synthetic data to S3 using the AWS CLI.

Actions:
 1) Verify AWS CLI and credentials
 2) Create S3 bucket (handles us-east-1 vs other regions)
 3) Upload contents of local data directory (not the top-level folder itself)

Usage:
  python3 scripts/upload_to_s3.py \
    --bucket snowflake_student_360_hol \
    --data-dir ./data [--region us-west-2]

Notes:
 - If the bucket already exists and is owned by you, creation is skipped.
 - If the bucket exists but is not owned by you, the script aborts.
 - The upload uses: aws s3 cp --recursive <data_dir>/ s3://<bucket>/
"""

import argparse
import os
import shlex
import subprocess
import sys


def run(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    print(f"$ {cmd}")
    result = subprocess.run(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed ({result.returncode}): {cmd}\n{result.stdout}")
    return result


def aws_cli_available() -> None:
    try:
        run("aws --version", check=True)
    except Exception as exc:
        raise SystemExit(f"AWS CLI not found. Please install and configure it: https://aws.amazon.com/cli/\n{exc}")


def get_region(cli_region_arg: str | None) -> str:
    if cli_region_arg:
        return cli_region_arg
    # Prefer env, then AWS config, else default to us-east-1
    env_region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
    if env_region:
        return env_region
    result = run("aws configure get region", check=False)
    region = (result.stdout or "").strip() or "us-east-1"
    return region


def ensure_bucket(bucket: str, region: str) -> None:
    # Check access/ownership
    head = run(f"aws s3api head-bucket --bucket {shlex.quote(bucket)}", check=False)
    if head.returncode == 0:
        print(f"Bucket '{bucket}' exists and is accessible. Skipping creation.")
        return
    # Create bucket. Special-case us-east-1 (no LocationConstraint allowed)
    if region == "us-east-1":
        run(f"aws s3api create-bucket --bucket {shlex.quote(bucket)} --region {region}", check=True)
    else:
        run(
            f"aws s3api create-bucket --bucket {shlex.quote(bucket)} --region {region} "
            f"--create-bucket-configuration LocationConstraint={region}",
            check=True,
        )
    print(f"Created bucket '{bucket}' in region '{region}'.")


def upload_data(bucket: str, data_dir: str) -> None:
    # Ensure we upload the CONTENTS of data_dir (trailing slash matters) to the bucket root
    local = os.path.abspath(data_dir)
    if not os.path.isdir(local):
        raise SystemExit(f"Data directory not found: {local}")
    # Quick sanity check that expected subfolders exist
    expected = ["sis", "lms", "admissions", "financials", "student_advising"]
    missing = [d for d in expected if not os.path.isdir(os.path.join(local, d))]
    if missing:
        print(f"Warning: expected subfolders missing under {local}: {', '.join(missing)}")

    # Perform upload; omit top-level folder by using trailing slash on source
    run(f"aws s3 cp --recursive {shlex.quote(local)}/ s3://{shlex.quote(bucket)}/", check=True)


def main():
    parser = argparse.ArgumentParser(description="Create S3 bucket and upload demo data using AWS CLI")
    parser.add_argument("--bucket", required=True, help="S3 bucket name (must be globally unique)")
    parser.add_argument("--data-dir", default="data", help="Path to local data directory (containing schema subfolders)")
    parser.add_argument("--region", default=None, help="AWS region for bucket (defaults to env/config or us-east-1)")
    args = parser.parse_args()

    aws_cli_available()
    region = get_region(args.region)

    # Validate credentials by calling STS (optional but helpful)
    run("aws sts get-caller-identity", check=True)

    ensure_bucket(args.bucket, region)
    upload_data(args.bucket, args.data_dir)
    print("Upload complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(str(e))
        sys.exit(1)


