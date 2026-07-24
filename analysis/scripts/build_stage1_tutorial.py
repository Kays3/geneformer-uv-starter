#!/usr/bin/env python3
"""Build the distributable Stage 1 cell-type classifier tutorial notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "01_stage1_cell_type_tutorial.ipynb"


def markdown(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.strip().splitlines(keepends=True),
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.strip().splitlines(keepends=True),
    }


def main() -> None:
    cells = [
        markdown(
            """
# Tutorial: Geneformer Stage 1 Cell-Type Classifier

This tutorial adapts the **Stage 1: cell-type model** from
[`Kays3/geneformer-nsclc`](https://github.com/Kays3/geneformer-nsclc) into a
clean, reproducible workflow for the ASUS Ascent GX10, Lenovo ThinkStation PGX,
and other supported machines.

**Audience:** researchers with basic Python and single-cell RNA-seq experience.

**Prerequisites:** run `./setup.sh`, then launch this notebook with `./start.sh`.
The full source atlas is 12.9 GB, and preprocessing plus fine-tuning requires
substantial additional disk space. A GB10 GPU is strongly recommended.

**Learning goals:** download and verify the source atlas, construct the original
nine-class 27k-cell cohort, tokenize it for Geneformer V2, create donor-disjoint
splits, fine-tune a cell classifier, and evaluate the held-out donors.
"""
        ),
        markdown(
            """
## Data provenance

The original notebook downloaded the core NSCLC atlas from the CZ CELLxGENE
collection **A single-cell lung cancer atlas of tumor and immune cells**:

- Collection: https://cellxgene.cziscience.com/collections/edb893ee-4066-4128-9aec-5eb2b03f8287
- Canonical H5AD: https://datasets.cellxgene.cziscience.com/46e0287b-9a33-4e83-99f3-8c044131bfdc.h5ad
- Expected bytes: `12,897,440,967`
- SHA-256: `141db65b76b1e34f895131e36c74cd829db05fc037f8cd2f422c2960a5a266cd`

The URL can be overridden with the `GENEFORMER_DATA_URL` environment variable,
for example if your team mirrors the exact file in Google Drive or object
storage. Keep the checksum unchanged when using a byte-identical mirror.
"""
        ),
        markdown(
            """
## Outline

1. Configure paths and verify the Geneformer environment.
2. Download and optionally checksum the source atlas.
3. Select the nine Stage 1 cell types with donor caps.
4. write a Geneformer-ready raw-count H5AD.
5. Tokenize with the Geneformer V2 vocabulary.
6. Create donor-disjoint train, evaluation, and test splits.
7. Fine-tune and evaluate the Stage 1 classifier.
8. Review pitfalls and try an exercise.
"""
        ),
        code(
            """
from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path

import pandas as pd
import scanpy as sc
import torch
from tqdm.auto import tqdm

SEED = 42


def find_project_directory(start: Path) -> Path:
    for candidate in (start.resolve(), *start.resolve().parents):
        has_project = (candidate / "pyproject.toml").is_file()
        has_geneformer = (candidate.parent / "Geneformer").is_dir()
        if has_project and has_geneformer:
            return candidate
    raise FileNotFoundError(
        "Could not locate the generated analysis. Start JupyterLab with ./start.sh."
    )


PROJECT_DIR = find_project_directory(Path.cwd())
GENEFORMER_ROOT = (PROJECT_DIR.parent / "Geneformer").resolve()
MODEL_DIR = GENEFORMER_ROOT / "Geneformer-V2-104M"
DATA_DIR = PROJECT_DIR / "data" / "nsclc"
DATA_FILE = DATA_DIR / "nsclc_integrated.h5ad"
INPUT_DIR = PROJECT_DIR / "input_data" / "01_primary_celltype"
TOKEN_DIR = PROJECT_DIR / "tokenized_data" / "01_primary_celltype"
RUN_DIR = PROJECT_DIR / "runs_geneformer_v2" / "01_primary_celltype"

CELLXGENE_URL = "https://datasets.cellxgene.cziscience.com/46e0287b-9a33-4e83-99f3-8c044131bfdc.h5ad"
DATA_URL = os.environ.get("GENEFORMER_DATA_URL", CELLXGENE_URL)
EXPECTED_BYTES = 12_897_440_967
EXPECTED_SHA256 = "141db65b76b1e34f895131e36c74cd829db05fc037f8cd2f422c2960a5a266cd"

for directory in (DATA_DIR, INPUT_DIR, TOKEN_DIR, RUN_DIR):
    directory.mkdir(parents=True, exist_ok=True)

sc.set_figure_params(dpi=100, dpi_save=100)
os.environ["WANDB_DISABLED"] = "true"

print("Project:", PROJECT_DIR)
print("Model:", MODEL_DIR)
print("GPU:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
assert MODEL_DIR.is_dir(), "Run ./setup.sh before opening this notebook."
"""
        ),
        markdown(
            """
## 1. Download the original atlas

The download resumes only at the file level: an existing file with the expected
size is reused; an incomplete file is downloaded again to a `.part` path and
renamed only after completion. Expect approximately 13 GB of network transfer.
"""
        ),
        code(
            """
def download_with_progress(url: str, destination: Path, expected_bytes: int) -> None:
    if destination.exists() and destination.stat().st_size == expected_bytes:
        print("Dataset already present:", destination)
        return

    temporary = destination.with_suffix(destination.suffix + ".part")
    if temporary.exists():
        temporary.unlink()

    with urllib.request.urlopen(url) as response, temporary.open("wb") as output:
        total = int(response.headers.get("Content-Length", expected_bytes))
        with tqdm(total=total, unit="B", unit_scale=True, desc="NSCLC atlas") as progress:
            while chunk := response.read(8 * 1024 * 1024):
                output.write(chunk)
                progress.update(len(chunk))

    actual_bytes = temporary.stat().st_size
    if actual_bytes != expected_bytes:
        raise RuntimeError(f"Expected {expected_bytes} bytes, downloaded {actual_bytes}")
    temporary.replace(destination)
    print("Downloaded:", destination)


download_with_progress(DATA_URL, DATA_FILE, EXPECTED_BYTES)
"""
        ),
        markdown(
            """
### Optional full checksum

Size validation catches incomplete transfers. Enable the SHA-256 pass when you
need byte-level provenance; hashing a 12.9 GB file takes additional time.
"""
        ),
        code(
            """
VERIFY_SHA256 = False

if VERIFY_SHA256:
    digest = hashlib.sha256()
    with DATA_FILE.open("rb") as stream:
        while chunk := stream.read(16 * 1024 * 1024):
            digest.update(chunk)
    actual_sha256 = digest.hexdigest()
    print("SHA-256:", actual_sha256)
    assert actual_sha256 == EXPECTED_SHA256
else:
    print("Checksum skipped. Set VERIFY_SHA256=True for full verification.")
"""
        ),
        markdown(
            """
## 2. Select the original Stage 1 cohort

The archived workflow selected nine major cell types, capped each donor at 300
cells per class, then capped each class at 3,000 cells. This produces up to
27,000 cells while limiting dominance by a single donor.
"""
        ),
        code(
            """
KEEP_CELL_TYPES = [
    "Macrophage alveolar",
    "Macrophage",
    "Monocyte",
    "T cell CD4",
    "T cell CD8",
    "NK cell",
    "B cell",
    "Endothelial cell",
    "cDC2",
]
MAX_PER_CLASS = 3_000
MAX_PER_DONOR_PER_CLASS = 300

adata_backed = sc.read_h5ad(DATA_FILE, backed="r")
required_obs = {"cell_type_major", "donor_id", "disease", "total_counts"}
missing_obs = required_obs.difference(adata_backed.obs.columns)
assert not missing_obs, f"Missing atlas metadata columns: {sorted(missing_obs)}"
assert "count" in adata_backed.layers, "Expected raw counts in layers['count']."

obs = adata_backed.obs.copy()
mask = (
    obs["cell_type_major"].isin(KEEP_CELL_TYPES)
    & obs["donor_id"].notna()
    & obs["total_counts"].notna()
)
if "doublet_status" in obs.columns:
    mask &= obs["doublet_status"].astype(str).str.lower().eq("singlet")
obs_selected = obs.loc[mask].copy()

selected_cells = []
for cell_type, cell_type_frame in obs_selected.groupby("cell_type_major", observed=True):
    donor_parts = [
        donor_frame.sample(
            n=min(MAX_PER_DONOR_PER_CLASS, len(donor_frame)),
            random_state=SEED,
        )
        for _, donor_frame in cell_type_frame.groupby("donor_id", observed=True)
    ]
    donor_capped = pd.concat(donor_parts)
    class_sample = donor_capped.sample(
        n=min(MAX_PER_CLASS, len(donor_capped)),
        random_state=SEED,
    )
    selected_cells.extend(class_sample.index.tolist())

selected_cells = pd.Index(selected_cells)
selected_obs = obs_selected.loc[selected_cells]
print("Selected cells:", len(selected_cells))
display(selected_obs["cell_type_major"].value_counts())
"""
        ),
        markdown(
            """
## 3. Create the Geneformer-ready H5AD

Geneformer must receive raw counts, not normalized `X`. The source atlas stores
raw counts in `layers['count']`; the next cell explicitly promotes that layer to
`X`, removes unused matrices, and adds Geneformer's required metadata.
"""
        ),
        code(
            """
stage1 = adata_backed[selected_cells, :].to_memory()
adata_backed.file.close()

stage1.X = stage1.layers["count"].copy()
stage1.layers.clear()
stage1.obs["celltype"] = stage1.obs["cell_type_major"].astype(str)
stage1.obs["disease"] = stage1.obs["disease"].astype(str)
stage1.obs["individual"] = stage1.obs["donor_id"].astype(str)
stage1.obs["cell_id"] = stage1.obs_names.astype(str)
stage1.obs["filter_pass"] = 1
stage1.obs["n_counts"] = stage1.obs["total_counts"].astype(float)
stage1.var["ensembl_id"] = stage1.var_names.astype(str)

stage1.obs = stage1.obs[
    ["cell_id", "individual", "celltype", "disease", "n_counts", "filter_pass"]
].copy()
stage1.obsm = {}
stage1.obsp = {}
stage1.uns = {}
stage1.varm = {}

stage1_file = INPUT_DIR / "01_primary_celltype.h5ad"
stage1.write_h5ad(stage1_file)
print(stage1)
print(f"Saved {stage1_file} ({stage1_file.stat().st_size / 1e9:.2f} GB)")
"""
        ),
        markdown(
            """
## 4. Tokenize for Geneformer V2

V2 uses its matching 104M-corpus dictionaries, special tokens, and input length.
`model_version='V2'` selects the matching defaults; the explicit input size is
4096, not the 2048-token V1 length used in an early archived notebook.
"""
        ),
        code(
            """
from geneformer import TranscriptomeTokenizer

tokenizer = TranscriptomeTokenizer(
    custom_attr_name_dict={
        "cell_id": "cell_id",
        "individual": "individual",
        "celltype": "celltype",
        "disease": "disease",
    },
    chunk_size=512,
    model_input_size=4096,
    nproc=min(8, os.cpu_count() or 1),
    model_version="V2",
)
tokenizer.tokenize_data(
    data_directory=str(INPUT_DIR),
    output_directory=str(TOKEN_DIR),
    output_prefix="01_primary_celltype",
    file_format="h5ad",
)

TOKENIZED_DATASET = TOKEN_DIR / "01_primary_celltype.dataset"
print("Tokenized dataset:", TOKENIZED_DATASET)
"""
        ),
        code(
            """
from datasets import load_from_disk

dataset = load_from_disk(str(TOKENIZED_DATASET))
print(dataset)
print("Columns:", dataset.column_names)
print("First record keys:", dataset[0].keys())
"""
        ),
        markdown(
            """
## 5. Create donor-disjoint splits

Cells from one donor must never cross train, evaluation, and test boundaries.
The split below is deterministic and asserts that all donor sets are disjoint.
"""
        ),
        code(
            """
from sklearn.model_selection import train_test_split

metadata = sc.read_h5ad(stage1_file, backed="r")
donors = sorted(metadata.obs["individual"].astype(str).unique())
metadata.file.close()

train_eval_ids, test_ids = train_test_split(donors, test_size=0.20, random_state=SEED)
train_ids, eval_ids = train_test_split(
    train_eval_ids,
    test_size=0.20,
    random_state=SEED,
)

assert set(train_ids).isdisjoint(eval_ids)
assert set(train_ids).isdisjoint(test_ids)
assert set(eval_ids).isdisjoint(test_ids)
print({"train_donors": len(train_ids), "eval_donors": len(eval_ids), "test_donors": len(test_ids)})
"""
        ),
        markdown(
            """
## 6. Configure and prepare the cell classifier

One epoch reproduces the archived tutorial's smoke-scale configuration. Treat
these values as a starting point: tune hyperparameters and assess class/donor
balance before using a model for scientific conclusions.
"""
        ),
        code(
            """
from geneformer import Classifier

classifier = Classifier(
    classifier="cell",
    cell_state_dict={"state_key": "celltype", "states": "all"},
    filter_data=None,
    training_args={
        "num_train_epochs": 1,
        "learning_rate": 1e-4,
        "per_device_train_batch_size": 8,
        "seed": SEED,
    },
    max_ncells=None,
    freeze_layers=6,
    num_crossval_splits=1,
    forward_batch_size=16,
    nproc=4,
    model_version="V2",
)

classifier.prepare_data(
    input_data_file=str(TOKENIZED_DATASET),
    output_directory=str(RUN_DIR),
    output_prefix="01_primary_celltype",
    split_id_dict={
        "attr_key": "individual",
        "train": train_ids + eval_ids,
        "test": test_ids,
    },
)
print("Prepared train and held-out test datasets in", RUN_DIR)
"""
        ),
        markdown(
            """
## 7. Fine-tune and evaluate

Training is opt-in so opening or running the tutorial does not accidentally
launch a long GPU job. Set `RUN_TRAINING=True` after inspecting the cohort and
available disk space. The corrected split key is `attr_key`.
"""
        ),
        code(
            """
RUN_TRAINING = False

if RUN_TRAINING:
    metrics = classifier.validate(
        model_directory=str(MODEL_DIR),
        prepared_input_data_file=str(RUN_DIR / "01_primary_celltype_labeled_train.dataset"),
        id_class_dict_file=str(RUN_DIR / "01_primary_celltype_id_class_dict.pkl"),
        output_directory=str(RUN_DIR),
        output_prefix="01_primary_celltype",
        split_id_dict={
            "attr_key": "individual",
            "train": train_ids,
            "eval": eval_ids,
        },
        n_hyperopt_trials=0,
    )
    display(metrics)
else:
    print("Training skipped. Review the preceding checks, then set RUN_TRAINING=True.")
"""
        ),
        code(
            """
if RUN_TRAINING:
    saved_models = sorted(RUN_DIR.glob("*geneformer_cellClassifier*/ksplit1"))
    if not saved_models:
        raise FileNotFoundError("No trained Stage 1 checkpoint found.")
    stage1_model = saved_models[-1]
    test_metrics = classifier.evaluate_saved_model(
        model_directory=str(stage1_model),
        id_class_dict_file=str(RUN_DIR / "01_primary_celltype_id_class_dict.pkl"),
        test_data_file=str(RUN_DIR / "01_primary_celltype_labeled_test.dataset"),
        output_directory=str(RUN_DIR),
        output_prefix="01_primary_celltype_test",
    )
    (RUN_DIR / "MODEL_STAGE1_PATH.txt").write_text(str(stage1_model), encoding="utf-8")
    display(test_metrics)
else:
    print("Evaluation will run after training.")
"""
        ),
        markdown(
            """
## Common pitfalls and extensions

- **`IProgress not found`:** rerun `./setup.sh`; the starter installs
  `ipywidgets`, `jupyterlab_widgets`, and the notebook integration.
- **Normalized expression used as counts:** this tutorial explicitly copies
  `layers['count']` into `X` before tokenization.
- **V1/V2 mismatch:** keep the V2 model, 104M dictionaries, special tokens, and
  4096-token input configuration together.
- **Donor leakage:** retain donor-disjoint splits and report per-class support.
- **Extension:** compare embeddings from the base V2 model and the fine-tuned
  Stage 1 model, following the archived `Step5-Stage1-embeddings.ipynb`.
"""
        ),
        markdown(
            """
## Exercise

Before training, quantify whether each cell type appears in every split and
whether any donor contributes more than 10% of a split. What would you change
if a class is absent from evaluation or test?
"""
        ),
        code(
            """
# Exercise answer scaffold
split_by_donor = {
    "train": set(train_ids),
    "eval": set(eval_ids),
    "test": set(test_ids),
}

stage1_obs = stage1.obs[["individual", "celltype"]].copy()
for split_name, split_donors in split_by_donor.items():
    split_obs = stage1_obs[stage1_obs["individual"].isin(split_donors)]
    class_counts = split_obs["celltype"].value_counts()
    donor_fraction = split_obs["individual"].value_counts(normalize=True).max()
    print(f"\\n{split_name}: {len(split_obs):,} cells; max donor fraction={donor_fraction:.3f}")
    display(class_counts.to_frame("cells"))

# If a class is absent, redesign the donor assignment with a documented,
# donor-level stratification strategy; never split cells from the same donor.
"""
        ),
    ]

    notebook = {
        "cells": cells,
        "metadata": {
            "geneformer_uv_starter": {"tutorial_version": "1.1"},
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
