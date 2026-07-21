#!/usr/bin/env python3
"""Validate a Geneformer analysis environment and report its versions."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


PACKAGES = (
    "anndata",
    "datasets",
    "geneformer",
    "numpy",
    "pandas",
    "scanpy",
    "torch",
    "transformers",
)


def package_versions() -> dict[str, str]:
    result = {}
    for package in PACKAGES:
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not-installed-as-distribution"
    return result


def geneformer_commit(geneformer_root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(geneformer_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def find_models(geneformer_root: Path) -> list[str]:
    return sorted(
        path.name
        for path in geneformer_root.glob("Geneformer-*")
        if path.is_dir() and (path / "config.json").is_file()
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geneformer-root", type=Path, required=True)
    parser.add_argument("--json", type=Path, help="Optional environment report output")
    args = parser.parse_args()

    geneformer_root = args.geneformer_root.resolve()
    if not (geneformer_root / ".git").is_dir():
        raise SystemExit(f"Not a Geneformer checkout: {geneformer_root}")

    import anndata  # noqa: F401
    import datasets  # noqa: F401
    import geneformer  # noqa: F401
    import scanpy  # noqa: F401
    import torch
    import transformers  # noqa: F401

    model_dirs = find_models(geneformer_root)
    report = {
        "python": sys.version.replace("\n", " "),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "geneformer_root": str(geneformer_root),
        "geneformer_commit": geneformer_commit(geneformer_root),
        "model_directories": model_dirs,
        "packages": package_versions(),
        "torch_cuda_version": torch.version.cuda,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    if not model_dirs:
        print("WARNING: no Geneformer model directory with config.json was found.")
    print("Geneformer environment smoke test passed")


if __name__ == "__main__":
    main()
