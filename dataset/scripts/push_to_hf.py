#!/usr/bin/env python3
"""
Push the prepared FMG-Bench v1 open dataset benchmark to Hugging Face.

Prerequisites:
  1. huggingface-cli login   (or set HF_TOKEN env var)
  2. Create the FideAI org on huggingface.co
  3. Confirm these release files are present:
     - README.md
     - data/fmg_bench_v1.jsonl
     - data/manifest.json
     - examples/public_sample.jsonl

Usage:
  python scripts/push_to_hf.py
  python scripts/push_to_hf.py --repo FideAI/fmg-bench --private  # dry run as private first
"""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import HfApi, upload_file, upload_folder


REPO_ID = "FideAI/fmg-bench"
REPO_TYPE = "dataset"
REQUIRED_FILES = (
    "README.md",
    "data/fmg_bench_v1.jsonl",
    "data/manifest.json",
    "examples/public_sample.jsonl",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Push FMG-Bench to Hugging Face")
    parser.add_argument("--repo", default=REPO_ID, help=f"HF repo id (default: {REPO_ID})")
    parser.add_argument("--private", action="store_true", help="Create/keep repo private")
    parser.add_argument("--create-repo", action="store_true", help="Create the repo if it does not exist")
    args = parser.parse_args()

    dataset_root = Path(__file__).parent.parent
    data_dir = dataset_root / "data"
    examples_dir = dataset_root / "examples"
    readme_path = dataset_root / "README.md"

    missing = [item for item in REQUIRED_FILES if not (dataset_root / item).exists()]
    if missing:
        print("ERROR: required Hugging Face release files are missing:")
        for item in missing:
            print(f"  - {item}")
        raise SystemExit(1)

    api = HfApi()

    if args.create_repo:
        api.create_repo(
            repo_id=args.repo,
            repo_type=REPO_TYPE,
            private=args.private,
            exist_ok=True,
        )
        print(f"Repo ready: https://huggingface.co/datasets/{args.repo}")

    # Upload dataset card
    if readme_path.exists():
        upload_file(
            path_or_fileobj=str(readme_path),
            path_in_repo="README.md",
            repo_id=args.repo,
            repo_type=REPO_TYPE,
            commit_message="Update dataset card",
        )
        print("Uploaded README.md (dataset card)")

    # Upload data files
    upload_folder(
        folder_path=str(data_dir),
        path_in_repo="data",
        repo_id=args.repo,
        repo_type=REPO_TYPE,
        commit_message="Upload FMG-Bench v1 open benchmark dataset",
        ignore_patterns=["*.pyc", "__pycache__"],
    )
    print(f"Uploaded data/ to https://huggingface.co/datasets/{args.repo}")

    if examples_dir.exists():
        upload_folder(
            folder_path=str(examples_dir),
            path_in_repo="examples",
            repo_id=args.repo,
            repo_type=REPO_TYPE,
            commit_message="Upload FMG-Bench v1 example sample",
            ignore_patterns=["*.pyc", "__pycache__"],
        )
        print(f"Uploaded examples/ to https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
