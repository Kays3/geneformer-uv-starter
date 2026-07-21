# Geneformer + uv starter

Clone this repository, run one setup command, and start Geneformer in
JupyterLab. The environment is isolated and reproducible with
[uv](https://docs.astral.sh/uv/).

This is a community setup helper. It is not affiliated with or endorsed by the
Geneformer authors.

## Quick start

### 1. Install the two prerequisites

You need [Git LFS](https://git-lfs.com/) and
[uv](https://docs.astral.sh/uv/getting-started/installation/).

Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs
curl -LsSf https://astral.sh/uv/install.sh | sh
```

macOS with Homebrew:

```bash
brew install git git-lfs uv
```

### 2. Clone and set up

```bash
git clone https://github.com/Kays3/geneformer-uv-starter.git
cd geneformer-uv-starter
./setup.sh
```

The first setup downloads Geneformer V2 104M and installs its Python
environment. It can take several minutes. CPU mode is used by default so the
setup works without an NVIDIA GPU.

### 3. Start Geneformer

```bash
./start.sh
```

JupyterLab will print a local URL and normally open it in your browser. Put
notebooks in the `notebooks` directory shown by JupyterLab.

To verify the environment without starting JupyterLab:

```bash
./start.sh check
```

## GPU setup

If your NVIDIA driver supports CUDA 13.0 PyTorch wheels, select the GPU profile:

```bash
./setup.sh cu130
./start.sh
```

The portable PyPI profile is also available:

```bash
./setup.sh default
```

To change profiles after setup, remove `.geneformer-workspace` and run setup
again. Keep any notebooks or results you want before doing so.

## Choose a model

The optional second setup argument chooses the checkpoint:

```bash
./setup.sh cpu v2-104m   # default
./setup.sh cpu v2-316m
./setup.sh cpu v1-10m
```

Available choices are `v2-104m`, `v2-316m`, `v1-10m`, `none`, and `all`.
The `all` option downloads every upstream Git LFS asset and can be very large.

## Where everything is stored

Setup creates this ignored local workspace:

```text
.geneformer-workspace/
├── Geneformer/     # pinned upstream code, dictionaries, and model
└── analysis/
    ├── configs/
    ├── notebooks/
    ├── results/
    ├── scripts/
    ├── pyproject.toml
    └── uv.lock
```

Your data and generated files are not committed to this starter repository.
For durable work, initialize a separate Git repository inside `analysis` or
copy the generated analysis directory to its own project.

## Use Geneformer from Python

Inside a notebook or script:

```python
from geneformer import EmbExtractor, TranscriptomeTokenizer

print("Geneformer is ready")
```

The model directory is available at:

```python
from pathlib import Path

model_directory = Path("../Geneformer/Geneformer-V2-104M")
```

Refer to the official examples for tokenization, embedding extraction,
fine-tuning, classification, and in silico perturbation.

## Important data notes

- Geneformer expects human transcriptomic data with Ensembl gene identifiers.
- Match the V1 or V2 dictionaries to the selected model.
- Keep donors separated between training and evaluation datasets.
- Try a small tokenization and forward pass before starting a long job.
- GPU resources are recommended for efficient model use and fine-tuning.

## Advanced bootstrap command

The detailed bootstrap remains available when you want a custom workspace or
analysis name:

```bash
./scripts/bootstrap_workspace.sh \
  /path/to/workspace \
  my-analysis \
  cpu \
  04c2b2e84da7c0f385c3f9ad8f3ec24bab6650e5 \
  v2-104m
```

It refuses to overwrite an existing analysis or silently change an existing
Geneformer checkout. The exact upstream revision is saved in
`.geneformer-commit` and Python packages are pinned in `uv.lock`.

## Documentation

- [Geneformer getting started](https://geneformer.readthedocs.io/en/latest/getstarted.html)
- [Geneformer model repository](https://huggingface.co/ctheodoris/Geneformer)
- [Geneformer examples](https://huggingface.co/ctheodoris/Geneformer/tree/main/examples)
- [uv project guide](https://docs.astral.sh/uv/guides/projects/)

## License

This setup helper is released under the MIT License. Geneformer and its model
assets are separate upstream works under their own license and terms.
