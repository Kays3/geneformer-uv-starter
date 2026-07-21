# Geneformer + uv starter

A small, reproducible starter for running [Geneformer](https://huggingface.co/ctheodoris/Geneformer)
with [uv](https://docs.astral.sh/uv/). It creates an independent analysis project,
pins the Geneformer source revision, selects a CPU or PyTorch profile, and checks
the resulting environment.

This repository is a community setup helper. It is not affiliated with or
endorsed by the Geneformer authors.

## Quick start

Install the system prerequisites:

- Git and [Git LFS](https://git-lfs.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- an NVIDIA driver if you want GPU acceleration

On Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y build-essential git git-lfs libhdf5-dev pkg-config
git lfs install
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then clone this repository and create an analysis:

```bash
git clone https://github.com/Kays3/geneformer-uv-starter.git
cd geneformer-uv-starter

./scripts/bootstrap_workspace.sh \
  "$HOME/geneformer-workspace" \
  my-analysis \
  default
```

The default downloads the Geneformer V2 104M checkpoint and matching V2 gene
dictionaries. It does not download every checkpoint in the upstream repository.

Start working:

```bash
cd "$HOME/geneformer-workspace/my-analysis"
uv run --locked python scripts/smoke_test.py --geneformer-root ../Geneformer
uv run --locked jupyter lab
```

## Bootstrap options

```text
bootstrap_workspace.sh WORKSPACE_ROOT ANALYSIS_NAME PROFILE [GENEFORMER_REF] [MODEL]
```

Profiles:

| Profile | PyTorch source | Intended use |
|---|---|---|
| `default` | PyPI | Portable default; lets uv choose compatible wheels |
| `cpu` | PyTorch CPU index | Machines without an NVIDIA GPU |
| `cu130` | PyTorch CUDA 13.0 index | Systems whose driver supports CUDA 13 wheels |

Model choices:

| Model | Downloaded LFS assets |
|---|---|
| `v2-104m` | V2 dictionaries and Geneformer V2 104M (default) |
| `v2-316m` | V2 dictionaries and Geneformer V2 316M |
| `v1-10m` | V1 dictionaries and Geneformer V1 10M |
| `none` | Source only; useful for environment development |
| `all` | Every upstream Git LFS asset; potentially very large |

The default source revision is pinned in the bootstrap script. Override it with
a branch, tag, or commit:

```bash
./scripts/bootstrap_workspace.sh \
  "$HOME/geneformer-workspace" \
  cpu-analysis \
  cpu \
  04c2b2e84da7c0f385c3f9ad8f3ec24bab6650e5 \
  v2-104m
```

The command refuses to overwrite an analysis or change an existing Geneformer
checkout. This protects research code and makes the recorded revision meaningful.

## Created layout

```text
geneformer-workspace/
├── Geneformer/                 # clean, pinned upstream checkout
└── my-analysis/                # your independent Git-ready project
    ├── .geneformer-commit
    ├── .python-version
    ├── pyproject.toml
    ├── uv.lock
    ├── configs/
    ├── notebooks/
    ├── results/
    └── scripts/
```

Geneformer is installed as an editable relative dependency. Keep the two
directories adjacent, or update the source path in `pyproject.toml`.

## Before a real analysis

- Use raw counts with human Ensembl gene identifiers and document whether they
  are stored in `X` or a layer.
- Keep donor-level train/evaluation/test splits disjoint for supervised tasks.
- Match V1/V2 dictionaries, vocabulary, input size, and model checkpoint.
- Keep private data, credentials, and large generated checkpoints out of Git.
- Run a tiny tokenization and forward-pass test before a long job.
- Tune fine-tuning hyperparameters for the downstream task; there is no universal
  Geneformer configuration.

Efficient Geneformer use generally requires a GPU. CPU mode is still useful for
installation checks, data preparation, and small experiments.

## Reproduce an existing analysis

Clone the analysis next to Geneformer checked out at the SHA stored in
`.geneformer-commit`, then run:

```bash
uv sync --frozen
uv run --frozen python scripts/smoke_test.py --geneformer-root ../Geneformer
```

Commit `uv.lock`; uv uses it to recreate the exact resolved Python environment.

## Upstream documentation

- [Geneformer getting started](https://geneformer.readthedocs.io/en/latest/getstarted.html)
- [Geneformer model repository](https://huggingface.co/ctheodoris/Geneformer)
- [uv project guide](https://docs.astral.sh/uv/guides/projects/)
- [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)

## License

The setup helper is released under the MIT License. Geneformer and its model
assets are separate upstream works under their own license and terms.
