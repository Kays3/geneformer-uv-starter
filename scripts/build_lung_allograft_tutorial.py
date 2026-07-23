#!/usr/bin/env python3
"""Build the distributable lung-allograft classification tutorial notebook."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "02_lung_allograft_classification_tutorial.ipynb"


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
    notebook = json.loads(OUTPUT.read_text(encoding="utf-8"))
    notebook["cells"] = [
        markdown(
            """
# Tutorial: Lung Allograft Cell Classification with Geneformer

This exploratory tutorial uses the CZ CELLxGENE collection **Human Lung
Allografts Experience Persistent Fibrogenic Shift Following Acute Cellular
Rejection** to compare two cell-classification strategies:

1. **Without Geneformer fine-tuning:** frozen pretrained cell embeddings plus
   a logistic-regression probe.
2. **With Geneformer fine-tuning:** a Geneformer cell-classification head and
   partial transformer fine-tuning.

Both methods predict five broad compartments—Endothelium, Epithelium,
Lymphoid, Myeloid, and Stromal—and are evaluated on donors never used for
training or model selection.

**Audience:** researchers with basic Python and single-cell RNA-seq experience.

**Prerequisites:** run `./setup.sh`, launch with `./start.sh`, and use a
CUDA-capable machine for embedding extraction and fine-tuning. Allow at least
15 GB of working space. The source H5AD is about 1.18 GB.

**Learning goals:** inspect CELLxGENE metadata, preserve raw counts, construct
donor-disjoint splits, tokenize cells, assess a frozen-embedding baseline,
fine-tune Geneformer, compare classification reports and confusion matrices,
and visualize pretrained and fine-tuned cell embeddings with UMAP.
"""
        ),
        markdown(
            """
## Data provenance

- Collection: https://cellxgene.cziscience.com/collections/e276e3e2-197a-4524-abd1-a753a48dc33a
- Dataset ID: `10c0c666-bd99-4a5c-b697-f1be835f5427`
- Canonical H5AD: https://datasets.cellxgene.cziscience.com/af6e81be-e65c-4821-987e-e0eb6c8acd59.h5ad
- Expected bytes: `1,180,621,333`
- SHA-256: `0648ce0268807301b5fe1b92955ed8e9d29c5f67812c6ed9ec3ed7da79e79b4c`
- Cells: 56,676; genes: 27,320; donors: 8

CZ CELLxGENE reports raw counts in `raw.X`; the normalized `X` matrix must not
be passed to the Geneformer tokenizer. The download URL can be overridden with
`LUNG_ALLOGRAFT_DATA_URL` when using a byte-identical institutional mirror.
"""
        ),
        markdown(
            """
## Outline

1. Configure reproducible paths and parameters.
2. Download and validate the H5AD.
3. Explore labels, donors, biopsy grades, and class balance.
4. Build a balanced raw-count cohort with donor-disjoint splits.
5. Tokenize cells for Geneformer V2.
6. Evaluate a frozen-embedding classifier without transformer fine-tuning.
7. Fine-tune a Geneformer cell classifier and evaluate the same test donors.
8. Compare classification reports, confusion-matrix heatmaps, and UMAPs.

Fine-tuning is opt-in because it is a substantial GPU job. The earlier cells
still produce the full no-fine-tuning assessment.
"""
        ),
        code(
            """
from __future__ import annotations

import hashlib
import os
import pickle
import urllib.request
from pathlib import Path

import anndata as ad
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import seaborn as sns
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from tqdm.auto import tqdm

SEED = 42
np.random.seed(SEED)
os.environ["WANDB_DISABLED"] = "true"


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
WORK_DIR = PROJECT_DIR / "lung_allograft_classification"
DATA_DIR = WORK_DIR / "data"
INPUT_DIR = WORK_DIR / "input_data"
TOKEN_DIR = WORK_DIR / "tokenized_data"
RUN_DIR = WORK_DIR / "runs"
RESULTS_DIR = WORK_DIR / "results"
FIGURE_DIR = RESULTS_DIR / "figures"
TABLE_DIR = RESULTS_DIR / "tables"
EMBEDDING_DIR = RESULTS_DIR / "embeddings"

for directory in (
    DATA_DIR, INPUT_DIR, TOKEN_DIR, RUN_DIR, FIGURE_DIR, TABLE_DIR, EMBEDDING_DIR
):
    directory.mkdir(parents=True, exist_ok=True)

COLLECTION_URL = "https://cellxgene.cziscience.com/collections/e276e3e2-197a-4524-abd1-a753a48dc33a"
CANONICAL_URL = "https://datasets.cellxgene.cziscience.com/af6e81be-e65c-4821-987e-e0eb6c8acd59.h5ad"
DATA_URL = os.environ.get("LUNG_ALLOGRAFT_DATA_URL", CANONICAL_URL)
DATA_FILE = DATA_DIR / "lung_allograft_biopsy.h5ad"
EXPECTED_BYTES = 1_180_621_333
EXPECTED_SHA256 = "0648ce0268807301b5fe1b92955ed8e9d29c5f67812c6ed9ec3ed7da79e79b4c"

CLASSES = ["Endothelium", "Epithelium", "Lymphoid", "Myeloid", "Stromal"]
TRAIN_DONORS = ["LTx_pt_01", "LTx_pt_02", "LTx_pt_03", "LTx_pt_05", "LTx_pt_07"]
EVAL_DONORS = ["LTx_pt_04"]
TEST_DONORS = ["LTx_pt_06", "LTx_pt_08"]
MAX_CELLS_PER_DONOR_CLASS = 500
TOKENIZED_DATASET = TOKEN_DIR / "lung_allograft_compartments.dataset"

print("Project:", PROJECT_DIR)
print("Base model:", MODEL_DIR)
print("Compute:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU")
assert MODEL_DIR.is_dir(), "Run ./setup.sh before opening this notebook."
"""
        ),
        markdown(
            """
## 1. Download and verify the source dataset

The download is written to a `.part` file and renamed only after its byte count
matches the CELLxGENE asset record. Rerunning the cell reuses a complete file.
Set `VERIFY_SHA256=True` for full byte-level verification.
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

    request = urllib.request.Request(url, headers={"User-Agent": "geneformer-uv-starter"})
    with urllib.request.urlopen(request) as response, temporary.open("wb") as output:
        total = int(response.headers.get("Content-Length", expected_bytes))
        with tqdm(total=total, unit="B", unit_scale=True, desc="Lung allograft") as progress:
            while chunk := response.read(8 * 1024 * 1024):
                output.write(chunk)
                progress.update(len(chunk))

    actual_bytes = temporary.stat().st_size
    if actual_bytes != expected_bytes:
        raise RuntimeError(f"Expected {expected_bytes} bytes, downloaded {actual_bytes}")
    temporary.replace(destination)
    print("Downloaded:", destination)


download_with_progress(DATA_URL, DATA_FILE, EXPECTED_BYTES)

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
    print("Size verified. Set VERIFY_SHA256=True for the full checksum pass.")
"""
        ),
        markdown(
            """
## 2. Explore the atlas

Start in backed mode so metadata can be inspected without loading the full
expression matrix. We use the curated broad `compartment` label as the target.
The finer `cell_type` and `author_cell_type` labels remain available for later
extensions.
"""
        ),
        code(
            """
atlas = sc.read_h5ad(DATA_FILE, backed="r")
print(atlas)

required_obs = {"donor_id", "compartment", "Biopsy", "Grade", "cell_type"}
missing_obs = required_obs.difference(atlas.obs.columns)
assert not missing_obs, f"Missing metadata columns: {sorted(missing_obs)}"
assert atlas.raw is not None, "CELLxGENE raw counts are required in raw.X."
assert atlas.n_obs == 56_676 and atlas.n_vars == 27_320

display(atlas.obs["compartment"].value_counts().rename("cells").to_frame())
display(pd.crosstab(atlas.obs["donor_id"], atlas.obs["compartment"]))
display(pd.crosstab(atlas.obs["Biopsy"], atlas.obs["Grade"]))
"""
        ),
        code(
            """
fig, axes = plt.subplots(1, 2, figsize=(15, 5))
sns.countplot(
    data=atlas.obs,
    y="compartment",
    order=CLASSES,
    color="#4c78a8",
    ax=axes[0],
)
axes[0].set_title("All source cells")
axes[0].set_xlabel("Cells")

donor_counts = pd.crosstab(atlas.obs["donor_id"], atlas.obs["compartment"])[CLASSES]
sns.heatmap(donor_counts, annot=True, fmt="d", cmap="Blues", ax=axes[1])
axes[1].set_title("Cells by donor and compartment")
plt.tight_layout()
plt.show()
"""
        ),
        markdown(
            """
## 3. Create a balanced, donor-disjoint cohort

The fixed split holds out `LTx_pt_06` and `LTx_pt_08` for the final test and
uses `LTx_pt_04` only for model selection. No donor appears in more than one
split. Within each donor and compartment, at most 500 cells are sampled so the
largest donor cannot dominate.

This cell deliberately copies `raw.X`. The source `X` is normalized and is not
valid Geneformer tokenizer input.
"""
        ),
        code(
            """
split_for_donor = {
    **{donor: "train" for donor in TRAIN_DONORS},
    **{donor: "eval" for donor in EVAL_DONORS},
    **{donor: "test" for donor in TEST_DONORS},
}
assert set(split_for_donor) == set(atlas.obs["donor_id"].unique())

eligible = atlas.obs.loc[
    atlas.obs["donor_id"].isin(split_for_donor)
    & atlas.obs["compartment"].isin(CLASSES)
].copy()

selected_parts = []
for _, group in eligible.groupby(["donor_id", "compartment"], observed=True):
    selected_parts.append(
        group.sample(
            n=min(MAX_CELLS_PER_DONOR_CLASS, len(group)),
            random_state=SEED,
        )
    )
selected_obs = pd.concat(selected_parts).sort_index()
selected_obs["split"] = selected_obs["donor_id"].map(split_for_donor)

split_summary = (
    selected_obs.groupby(["split", "compartment"], observed=True)
    .agg(cells=("donor_id", "size"), donors=("donor_id", "nunique"))
    .reset_index()
)
display(split_summary)

leakage = selected_obs.groupby("donor_id")["split"].nunique()
assert leakage.max() == 1, "Donor leakage detected."
assert set(CLASSES).issubset(set(selected_obs.loc[selected_obs["split"] == "test", "compartment"]))
print("Donor leakage check: PASS")
"""
        ),
        code(
            """
GENEFORMER_H5AD = INPUT_DIR / "lung_allograft_compartments.h5ad"

if not GENEFORMER_H5AD.exists():
    atlas.file.close()
    source = sc.read_h5ad(DATA_FILE)
    assert source.raw is not None
    cohort = source[selected_obs.index].raw.to_adata()
    cohort.obs = selected_obs.loc[cohort.obs_names].copy()
    cohort.obs["cell_id"] = cohort.obs_names.astype(str)
    cohort.obs["individual"] = cohort.obs["donor_id"].astype(str)
    cohort.obs["celltype"] = cohort.obs["compartment"].astype(str)
    cohort.obs["biopsy"] = cohort.obs["Biopsy"].astype(str)
    cohort.obs["grade"] = cohort.obs["Grade"].astype(str)
    cohort.obs["filter_pass"] = 1
    cohort.obs["n_counts"] = np.asarray(cohort.X.sum(axis=1)).ravel().astype(float)
    cohort.var["ensembl_id"] = cohort.var_names.astype(str).str.split(".").str[0]

    keep_obs = [
        "cell_id", "individual", "celltype", "biopsy", "grade", "disease",
        "split", "n_counts", "filter_pass",
    ]
    cohort.obs = cohort.obs[keep_obs].copy()
    cohort.var = cohort.var[["ensembl_id"]].copy()
    cohort.layers.clear()
    cohort.obsm = {}
    cohort.obsp = {}
    cohort.uns = {}
    cohort.varm = {}

    raw_sample = cohort.X[: min(200, cohort.n_obs), : min(200, cohort.n_vars)]
    raw_values = raw_sample.data if hasattr(raw_sample, "data") else np.asarray(raw_sample)
    assert np.allclose(raw_values, np.rint(raw_values)), "Expected integer-like raw counts."
    cohort.write_h5ad(GENEFORMER_H5AD)
    print("Saved:", GENEFORMER_H5AD, cohort)
else:
    atlas.file.close()
    print("Prepared H5AD already exists:", GENEFORMER_H5AD)
"""
        ),
        markdown(
            """
## 4. Tokenize for Geneformer V2

Tokenization retains the donor, target label, split, biopsy, and grade. Rerun
this cell safely: an existing tokenized dataset is reused.
"""
        ),
        code(
            """
from geneformer import TranscriptomeTokenizer

if not TOKENIZED_DATASET.exists():
    tokenizer = TranscriptomeTokenizer(
        custom_attr_name_dict={
            "cell_id": "cell_id",
            "individual": "individual",
            "celltype": "celltype",
            "biopsy": "biopsy",
            "grade": "grade",
            "disease": "disease",
            "split": "split",
        },
        nproc=4,
        chunk_size=512,
        model_version="V2",
    )
    tokenizer.tokenize_data(
        data_directory=str(INPUT_DIR),
        output_directory=str(TOKEN_DIR),
        output_prefix="lung_allograft_compartments",
        file_format="h5ad",
    )
else:
    print("Tokenized dataset already exists:", TOKENIZED_DATASET)

from datasets import load_from_disk

tokens = load_from_disk(str(TOKENIZED_DATASET))
print(tokens)
print(pd.Series(tokens["split"]).value_counts())
assert {"cell_id", "individual", "celltype", "split"}.issubset(tokens.column_names)
"""
        ),
        markdown(
            """
## 5. Without fine-tuning: frozen Geneformer embeddings

The pretrained checkpoint does not contain a trained compartment classifier,
so a direct “zero-shot” classification score would be undefined. Instead, we
freeze Geneformer, extract one vector per cell, and fit a small
logistic-regression probe. Only the probe learns; transformer weights never
change.
"""
        ),
        code(
            """
from geneformer import EmbExtractor

BASE_EMBEDDING_FILE = EMBEDDING_DIR / "pretrained_cell_embeddings.csv"
LABEL_COLUMNS = ["cell_id", "individual", "celltype", "split"]

if BASE_EMBEDDING_FILE.exists():
    base_embeddings = pd.read_csv(BASE_EMBEDDING_FILE, index_col=0)
else:
    assert torch.cuda.is_available(), "Geneformer embedding extraction requires CUDA."
    base_extractor = EmbExtractor(
        model_type="Pretrained",
        num_classes=0,
        emb_mode="cell",
        max_ncells=None,
        emb_layer=-1,
        emb_label=LABEL_COLUMNS,
        labels_to_plot=["celltype", "split"],
        forward_batch_size=16,
        nproc=4,
        model_version="V2",
    )
    base_embeddings = base_extractor.extract_embs(
        model_directory=str(MODEL_DIR),
        input_data_file=str(TOKENIZED_DATASET),
        output_directory=str(EMBEDDING_DIR),
        output_prefix="pretrained_cell_embeddings",
    )

embedding_columns = [column for column in base_embeddings.columns if column not in LABEL_COLUMNS]
print("Embedding table:", base_embeddings.shape)
display(base_embeddings[LABEL_COLUMNS].head())
"""
        ),
        code(
            """
train_mask = base_embeddings["split"].eq("train")
test_mask = base_embeddings["split"].eq("test")

probe = make_pipeline(
    StandardScaler(),
    LogisticRegression(
        max_iter=2_000,
        class_weight="balanced",
        random_state=SEED,
    ),
)
probe.fit(
    base_embeddings.loc[train_mask, embedding_columns],
    base_embeddings.loc[train_mask, "celltype"],
)
baseline_true = base_embeddings.loc[test_mask, "celltype"].to_numpy()
baseline_pred = probe.predict(base_embeddings.loc[test_mask, embedding_columns])

baseline_report = pd.DataFrame(
    classification_report(
        baseline_true,
        baseline_pred,
        labels=CLASSES,
        output_dict=True,
        zero_division=0,
    )
).T
baseline_report.to_csv(TABLE_DIR / "baseline_classification_report.csv")
display(baseline_report.round(3))
"""
        ),
        code(
            """
def plot_confusion_heatmap(y_true, y_pred, title: str, output_name: str) -> None:
    matrix = confusion_matrix(y_true, y_pred, labels=CLASSES, normalize="true")
    frame = pd.DataFrame(matrix, index=CLASSES, columns=CLASSES)
    frame.to_csv(TABLE_DIR / f"{output_name}.csv")
    plt.figure(figsize=(8, 6))
    sns.heatmap(frame, annot=True, fmt=".2f", cmap="Blues", vmin=0, vmax=1)
    plt.title(title)
    plt.xlabel("Predicted compartment")
    plt.ylabel("True compartment")
    plt.tight_layout()
    plt.savefig(FIGURE_DIR / f"{output_name}.png", dpi=180, bbox_inches="tight")
    plt.show()


plot_confusion_heatmap(
    baseline_true,
    baseline_pred,
    "Frozen Geneformer embeddings + logistic regression",
    "baseline_confusion_matrix_normalized",
)
"""
        ),
        code(
            """
def plot_embedding_umap(
    embedding_frame: pd.DataFrame,
    title: str,
    output_name: str,
    prediction: np.ndarray | None = None,
) -> ad.AnnData:
    feature_columns = [c for c in embedding_frame.columns if c not in LABEL_COLUMNS]
    view = ad.AnnData(embedding_frame[feature_columns].to_numpy(dtype=np.float32))
    view.obs = embedding_frame[LABEL_COLUMNS].reset_index(drop=True).copy()
    if prediction is not None:
        view.obs["prediction"] = prediction
    sc.pp.neighbors(view, n_neighbors=15, use_rep="X", random_state=SEED)
    sc.tl.umap(view, random_state=SEED)
    colors = ["celltype", "prediction"] if prediction is not None else ["celltype", "split"]
    sc.pl.umap(view, color=colors, wspace=0.35, show=False)
    plt.suptitle(title, y=1.02)
    plt.savefig(FIGURE_DIR / f"{output_name}.png", dpi=180, bbox_inches="tight")
    plt.show()
    return view


baseline_test_embeddings = base_embeddings.loc[test_mask].reset_index(drop=True)
baseline_umap = plot_embedding_umap(
    baseline_test_embeddings,
    "Pretrained Geneformer embeddings: held-out donors",
    "baseline_test_embedding_umap",
    baseline_pred,
)
"""
        ),
        markdown(
            """
## 6. With fine-tuning: Geneformer cell classifier

Set `RUN_FINE_TUNING=True` only after the baseline completes and the split
summary looks correct. This trains for one epoch, freezes the first six
transformer layers, selects on the evaluation donor, and assesses the same two
held-out test donors used by the baseline.

An existing checkpoint can be reused by assigning its directory to
`TRAINED_MODEL_DIR` and leaving `RUN_FINE_TUNING=False`.
"""
        ),
        code(
            """
from geneformer import Classifier

RUN_FINE_TUNING = False
TRAINED_MODEL_DIR: Path | None = None
OUTPUT_PREFIX = "lung_allograft_compartments"

classifier = Classifier(
    classifier="cell",
    cell_state_dict={"state_key": "celltype", "states": CLASSES},
    filter_data=None,
    training_args={
        "num_train_epochs": 1,
        "learning_rate": 5e-5,
        "per_device_train_batch_size": 8,
        "per_device_eval_batch_size": 16,
        "seed": SEED,
        "save_strategy": "epoch",
        "logging_steps": 25,
        "report_to": "none",
    },
    max_ncells=None,
    freeze_layers=6,
    num_crossval_splits=1,
    forward_batch_size=16,
    nproc=4,
    model_version="V2",
)

prepared_train = RUN_DIR / f"{OUTPUT_PREFIX}_labeled_train.dataset"
prepared_test = RUN_DIR / f"{OUTPUT_PREFIX}_labeled_test.dataset"
id_class_file = RUN_DIR / f"{OUTPUT_PREFIX}_id_class_dict.pkl"

if RUN_FINE_TUNING:
    assert torch.cuda.is_available(), "Fine-tuning requires CUDA."
    if not (prepared_train.exists() and prepared_test.exists() and id_class_file.exists()):
        classifier.prepare_data(
            input_data_file=str(TOKENIZED_DATASET),
            output_directory=str(RUN_DIR),
            output_prefix=OUTPUT_PREFIX,
            split_id_dict={
                "attr_key": "individual",
                "train": TRAIN_DONORS + EVAL_DONORS,
                "test": TEST_DONORS,
            },
        )

    classifier.validate(
        model_directory=str(MODEL_DIR),
        prepared_input_data_file=str(prepared_train),
        id_class_dict_file=str(id_class_file),
        output_directory=str(RUN_DIR),
        output_prefix=OUTPUT_PREFIX,
        split_id_dict={
            "attr_key": "individual",
            "train": TRAIN_DONORS,
            "eval": EVAL_DONORS,
        },
        n_hyperopt_trials=0,
    )
    saved_models = sorted(RUN_DIR.glob(f"*geneformer_cellClassifier_{OUTPUT_PREFIX}/ksplit1"))
    assert saved_models, "Fine-tuning finished without a saved ksplit1 checkpoint."
    TRAINED_MODEL_DIR = saved_models[-1]
    (RUN_DIR / "TRAINED_MODEL_PATH.txt").write_text(str(TRAINED_MODEL_DIR), encoding="utf-8")

print("Fine-tuned checkpoint:", TRAINED_MODEL_DIR or "not selected")
"""
        ),
        code(
            """
if TRAINED_MODEL_DIR is not None:
    fine_metrics = classifier.evaluate_saved_model(
        model_directory=str(TRAINED_MODEL_DIR),
        id_class_dict_file=str(id_class_file),
        test_data_file=str(prepared_test),
        output_directory=str(RUN_DIR),
        output_prefix=f"{OUTPUT_PREFIX}_heldout",
        predict=True,
        predict_metadata=["cell_id", "individual", "celltype"],
    )

    with id_class_file.open("rb") as stream:
        id_to_class = pickle.load(stream)
    prediction_file = RUN_DIR / f"{OUTPUT_PREFIX}_heldout_pred_dict.pkl"
    with prediction_file.open("rb") as stream:
        prediction_payload = pickle.load(stream)

    fine_true = np.array([id_to_class[index] for index in prediction_payload["label_ids"]])
    fine_pred = np.array([id_to_class[index] for index in prediction_payload["pred_ids"]])
    fine_report = pd.DataFrame(
        classification_report(
            fine_true,
            fine_pred,
            labels=CLASSES,
            output_dict=True,
            zero_division=0,
        )
    ).T
    fine_report.to_csv(TABLE_DIR / "finetuned_classification_report.csv")
    display(fine_report.round(3))
    plot_confusion_heatmap(
        fine_true,
        fine_pred,
        "Fine-tuned Geneformer classifier",
        "finetuned_confusion_matrix_normalized",
    )
else:
    print("Fine-tuned evaluation skipped. Set RUN_FINE_TUNING=True or provide a checkpoint.")
"""
        ),
        markdown(
            """
## 7. Fine-tuned embedding UMAP

The next cell extracts held-out donor embeddings from the trained classifier.
The UMAP is fitted separately from the baseline UMAP, so compare neighborhood
separation—not absolute coordinates or axis directions.
"""
        ),
        code(
            """
if TRAINED_MODEL_DIR is not None:
    fine_embedding_file = EMBEDDING_DIR / "finetuned_test_cell_embeddings.csv"
    if fine_embedding_file.exists():
        fine_embeddings = pd.read_csv(fine_embedding_file, index_col=0)
    else:
        fine_extractor = EmbExtractor(
            model_type="CellClassifier",
            num_classes=len(CLASSES),
            emb_mode="cell",
            filter_data={"split": ["test"]},
            max_ncells=None,
            emb_layer=-1,
            emb_label=LABEL_COLUMNS,
            labels_to_plot=["celltype"],
            forward_batch_size=16,
            nproc=4,
            model_version="V2",
        )
        fine_embeddings = fine_extractor.extract_embs(
            model_directory=str(TRAINED_MODEL_DIR),
            input_data_file=str(TOKENIZED_DATASET),
            output_directory=str(EMBEDDING_DIR),
            output_prefix="finetuned_test_cell_embeddings",
        )

    fine_prediction_by_cell = dict(
        zip(
            prediction_payload["prediction_metadata"]["cell_id"],
            fine_pred,
            strict=True,
        )
    )
    fine_embedding_pred = fine_embeddings["cell_id"].map(fine_prediction_by_cell).to_numpy()
    assert pd.notna(fine_embedding_pred).all()
    finetuned_umap = plot_embedding_umap(
        fine_embeddings.reset_index(drop=True),
        "Fine-tuned Geneformer embeddings: held-out donors",
        "finetuned_test_embedding_umap",
        fine_embedding_pred,
    )
else:
    print("Fine-tuned UMAP skipped until a trained checkpoint is selected.")
"""
        ),
        markdown(
            """
## 8. Compare held-out performance

Macro F1 weights all compartments equally; accuracy weights every cell
equally. Report both, and inspect per-class recall and the normalized confusion
matrices. With only eight donors, uncertainty is substantial—these values are
an exploratory assessment, not a clinical performance claim.
"""
        ),
        code(
            """
comparison_rows = [
    {
        "method": "Frozen embeddings + logistic regression",
        "accuracy": accuracy_score(baseline_true, baseline_pred),
        "macro_f1": f1_score(baseline_true, baseline_pred, average="macro"),
        "test_donors": ", ".join(TEST_DONORS),
    }
]
if TRAINED_MODEL_DIR is not None:
    comparison_rows.append(
        {
            "method": "Fine-tuned Geneformer classifier",
            "accuracy": accuracy_score(fine_true, fine_pred),
            "macro_f1": f1_score(fine_true, fine_pred, average="macro"),
            "test_donors": ", ".join(TEST_DONORS),
        }
    )

comparison = pd.DataFrame(comparison_rows)
comparison.to_csv(TABLE_DIR / "model_comparison.csv", index=False)
display(comparison.round(3))
"""
        ),
        markdown(
            """
## Interpretation checklist and pitfalls

- **No donor leakage:** train, evaluation, and test donor sets must be disjoint.
- **Raw counts only:** tokenize `raw.X`, never the normalized source `X`.
- **No zero-shot claim:** the frozen-embedding probe trains a downstream linear
  model; it is “without transformer fine-tuning,” not a label-free classifier.
- **Class balance:** normalized confusion matrices and macro F1 expose failures
  on smaller compartments that accuracy can hide.
- **UMAP is qualitative:** cluster separation does not establish classification
  validity, and separate UMAP coordinate systems are not directly aligned.
- **Small donor count:** repeat with alternate donor-level folds before drawing
  biological conclusions.

Outputs are saved under
`lung_allograft_classification/results/{tables,figures,embeddings}` in the
generated analysis workspace.
"""
        ),
        markdown(
            """
## Exercise

Replace the five-compartment target with a carefully selected set of finer
`cell_type` labels. Before training, answer:

1. Does every selected class occur in every split?
2. Does each split contain multiple donors per class where possible?
3. How will you cap abundant macrophage and endothelial populations?
4. Which metric will you prioritize when rare classes matter?

Use the scaffold below; do not start fine-tuning until all assertions pass.
"""
        ),
        code(
            """
# Exercise answer scaffold (intentionally not executed by the main workflow)
FINE_LABELS = [
    # "macrophage",
    # "classical monocyte",
    # "natural killer cell",
]

if FINE_LABELS:
    exercise_obs = selected_obs[selected_obs["cell_type"].isin(FINE_LABELS)].copy()
    coverage = pd.crosstab(exercise_obs["split"], exercise_obs["cell_type"])
    display(coverage)
    assert (coverage > 0).all().all(), "At least one label is absent from a split."
    exercise_leakage = exercise_obs.groupby("donor_id")["split"].nunique()
    assert exercise_leakage.max() == 1
else:
    print("Choose FINE_LABELS after reviewing atlas.obs['cell_type'].value_counts().")
"""
        ),
        markdown(
            """
## Next steps

- Repeat the comparison across donor-level cross-validation folds.
- Add bootstrap confidence intervals where the resampling unit is the donor,
  not the cell.
- Compare compartment performance across biopsy grades without using grade as
  an input feature.
- Fine-tune on an external lung reference and treat this allograft atlas as a
  completely external validation cohort.
"""
        ),
    ]

    for index, cell in enumerate(notebook["cells"]):
        cell["id"] = f"lung-allograft-{index:02d}"

    notebook.setdefault("metadata", {})["geneformer_uv_starter"] = {
        "tutorial_version": "1.0",
        "dataset_id": "10c0c666-bd99-4a5c-b697-f1be835f5427",
        "collection_id": "e276e3e2-197a-4524-abd1-a753a48dc33a",
        "classification_target": "compartment",
    }
    notebook["nbformat"] = 4
    notebook["nbformat_minor"] = max(5, notebook.get("nbformat_minor", 5))
    OUTPUT.write_text(json.dumps(notebook, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
