# Geneformer + uv starter

Clone this repository, run one setup command, and start Geneformer in
JupyterLab. ASUS Ascent GX10 and Lenovo ThinkStation PGX systems are detected
automatically and use their NVIDIA GB10 GPU. The environment is isolated and reproducible with
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
environment. It can take several minutes. Setup automatically selects CUDA
13.0 on a GB10 ARM64 appliance and CPU mode on other systems. It also installs
a private uv-managed Python 3.12 with the C headers required by Geneformer's
dependencies; the operating system Python is not modified.

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

## ASUS Ascent GX10 and Lenovo ThinkStation PGX

Both systems use the NVIDIA GB10 Grace Blackwell platform. On either machine,
the normal quick start is all you need:

```bash
./setup.sh
./start.sh
```

Setup checks for an ARM64 CPU and an NVIDIA GPU whose name contains `GB10`,
then selects native CUDA 13.0 PyTorch wheels. Installation only succeeds after
PyTorch detects the GPU and completes a CUDA tensor operation.

Check the result at any time:

```bash
./start.sh check
```

The report should contain values similar to:

```json
{
  "machine": "aarch64",
  "torch_cuda_version": "13.0",
  "cuda_available": true,
  "cuda_self_test": true,
  "gpu": "NVIDIA GB10"
}
```

Keep DGX OS and the NVIDIA driver updated through the vendor-supported update
path. Partner appliance releases may not arrive on exactly the same date.

## Override automatic hardware selection

Automatic detection is recommended. Profiles can also be selected explicitly:

```bash
./setup.sh cu130    # Linux with a CUDA 13-compatible NVIDIA driver
./setup.sh cpu      # CPU-only PyTorch
./setup.sh default  # portable PyPI resolution
```

To change profiles after setup, preserve any notebooks or results you need,
remove `.geneformer-workspace`, and run setup again.

## Choose a model

The optional second setup argument chooses the checkpoint:

```bash
./setup.sh auto v2-104m   # default
./setup.sh auto v2-316m
./setup.sh auto v1-10m
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
`.geneformer-commit` and Python packages are pinned in `uv.lock`. A newly
created analysis is cleaned up if its environment build fails, instead of
appearing complete on the next run. The template also constrains
Transformers to the 4.x API used by the pinned Geneformer source.

### Missing `Python.h`

Older revisions of this starter could select the system Python on some DGX OS
partner images. Those images may omit `python3.12-dev`, causing
`accumulation-tree` to fail with `fatal error: Python.h: No such file or
directory`. Current setup avoids that OS-specific dependency by requiring a
uv-managed Python distribution that includes the headers.

## Documentation

- [Geneformer getting started](https://geneformer.readthedocs.io/en/latest/getstarted.html)
- [Geneformer model repository](https://huggingface.co/ctheodoris/Geneformer)
- [Geneformer examples](https://huggingface.co/ctheodoris/Geneformer/tree/main/examples)
- [uv project guide](https://docs.astral.sh/uv/guides/projects/)

## License

This setup helper is released under the MIT License. Geneformer and its model
assets are separate upstream works under their own license and terms.
