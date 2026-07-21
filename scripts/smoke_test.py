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
    def has_downloaded_weights(model_directory: Path) -> bool:
        weight_names = ("model.safetensors", "pytorch_model.bin")
        return any(
            weight.is_file() and weight.stat().st_size > 1024
            for name in weight_names
            if (weight := model_directory / name)
        )

    return sorted(
        path.name
        for path in geneformer_root.glob("Geneformer-*")
        if path.is_dir()
        and (path / "config.json").is_file()
        and has_downloaded_weights(path)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--geneformer-root", type=Path, required=True)
    parser.add_argument("--json", type=Path, help="Optional environment report output")
    parser.add_argument(
        "--require-cuda",
        action="store_true",
        help="Fail unless PyTorch can execute a basic CUDA operation",
    )
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

    cuda_available = torch.cuda.is_available()
    cuda_self_test = None
    if cuda_available:
        cuda_self_test = (torch.ones(1, device="cuda") * 2).item() == 2
    if args.require_cuda and not cuda_available:
        raise SystemExit("CUDA profile installed, but PyTorch cannot access the NVIDIA GPU.")
    if args.require_cuda and not cuda_self_test:
        raise SystemExit("CUDA profile installed, but the CUDA tensor self-test failed.")

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
        "cuda_available": cuda_available,
        "cuda_self_test": cuda_self_test,
        "gpu": torch.cuda.get_device_name(0) if cuda_available else None,
    }
    rendered = json.dumps(report, indent=2)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")

    if not model_dirs:
        print("WARNING: no Geneformer model directory with downloaded weights was found.")
    print("Geneformer environment smoke test passed")


if __name__ == "__main__":
    main()
