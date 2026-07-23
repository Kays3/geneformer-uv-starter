# Geneformer + uv starter

Clone this repository, run one setup command, and start Geneformer in
JupyterLab. ASUS Ascent GX10 and Lenovo ThinkStation PGX systems are detected
automatically and use their NVIDIA GB10 GPU. The environment is isolated and reproducible with
[uv](https://docs.astral.sh/uv/).

This is a community setup helper. It is not affiliated with or endorsed by the
Geneformer authors.

## New machine? Start here

If the computer is not set up yet, follow the complete
**[machine setup tutorial](docs/machine-setup.md)**. It covers:

- connecting the monitor, keyboard, mouse, and power, then joining Wi-Fi;
- completing Ubuntu first boot and installing operating-system updates;
- safely verifying or updating NVIDIA GPU drivers;
- special guidance for ASUS Ascent GX10 and Lenovo ThinkStation PGX systems;
- configuring tmux, RustDesk, and Tailscale for approved remote access;
- installing this repository and testing that PyTorch can use the GPU; and
- routine updates and troubleshooting.

If Ubuntu is already current and `nvidia-smi` works, continue with the quick
start below.

## Quick start

### 1. Install the two prerequisites

You need [Git LFS](https://git-lfs.com/) and
[uv](https://docs.astral.sh/uv/getting-started/installation/).

Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs curl
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
dependencies; the operating system Python is not modified. Models, datasets,
notebooks, and results are stored in the visible `geneformer-workspace/`
directory.

### 3. Start Geneformer

```bash
./start.sh
```

JupyterLab will print a local URL and normally open it in your browser. Put
notebooks in the `notebooks` directory shown by JupyterLab. A runnable
`01_stage1_cell_type_tutorial.ipynb` is preloaded; it adapts the nine-class
Stage 1 cell-type model from
[`Kays3/geneformer-nsclc`](https://github.com/Kays3/geneformer-nsclc).

The preloaded `02_lung_allograft_classification_tutorial.ipynb` downloads a
1.18 GB public lung-allograft atlas and compares a frozen Geneformer embedding
classifier with partial Geneformer fine-tuning. It produces donor-held-out
classification reports, normalized confusion-matrix heatmaps, and cell
embedding UMAPs.

To verify the environment without starting JupyterLab:

```bash
./start.sh check
```

If you installed an earlier release, pull and rerun setup. It updates the
environment in place, adds `ipywidgets` to remove the `IProgress not found`
warning, constrains pandas to the Geneformer-compatible 2.x series, and
refreshes the distributed tutorial. If the installed tutorial was changed,
setup first preserves it as
`01_stage1_cell_type_tutorial.user-backup.ipynb`:

```bash
git pull
./setup.sh
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
remove `geneformer-workspace`, and run setup again.

## Choose a model

The optional second setup argument chooses the checkpoint:

```bash
./setup.sh auto v2-104m   # default
./setup.sh auto v2-316m
./setup.sh auto v1-10m
```

Available choices are `v2-104m`, `v2-316m`, `v1-10m`, `none`, and `all`.
The `all` option downloads every upstream Git LFS asset and can be very large.

## Stage 1 tutorial dataset

The preloaded tutorial downloads the original 12.9 GB NSCLC atlas directly
from the public CZ CELLxGENE source used by the archived workflow. It validates
the byte count before using the file and offers an optional SHA-256 pass.

- [CELLxGENE collection](https://cellxgene.cziscience.com/collections/edb893ee-4066-4128-9aec-5eb2b03f8287)
- [Direct H5AD download](https://datasets.cellxgene.cziscience.com/46e0287b-9a33-4e83-99f3-8c044131bfdc.h5ad)
- Expected bytes: `12,897,440,967`
- SHA-256: `141db65b76b1e34f895131e36c74cd829db05fc037f8cd2f422c2960a5a266cd`

The machine-readable record is in
[`datasets/nsclc_integrated.manifest.json`](datasets/nsclc_integrated.manifest.json).
Set `GENEFORMER_DATA_URL` before starting JupyterLab to use a byte-identical
institutional or Google Drive mirror instead.

## Lung allograft tutorial dataset

The second tutorial uses the public CELLxGENE collection **Human Lung
Allografts Experience Persistent Fibrogenic Shift Following Acute Cellular
Rejection**. It validates the 1.18 GB asset size before use and offers an
optional SHA-256 pass.

- [CELLxGENE collection](https://cellxgene.cziscience.com/collections/e276e3e2-197a-4524-abd1-a753a48dc33a)
- [Direct H5AD download](https://datasets.cellxgene.cziscience.com/af6e81be-e65c-4821-987e-e0eb6c8acd59.h5ad)
- Expected bytes: `1,180,621,333`
- SHA-256: `0648ce0268807301b5fe1b92955ed8e9d29c5f67812c6ed9ec3ed7da79e79b4c`

The machine-readable record is in
[`datasets/lung_allograft.manifest.json`](datasets/lung_allograft.manifest.json).
Set `LUNG_ALLOGRAFT_DATA_URL` to use a byte-identical institutional mirror.

See the published **[lung allograft results report](docs/results/lung-allograft/README.md)**
for the completed frozen-versus-fine-tuned comparison, held-out classification
tables, normalized confusion matrices, donor-specific results, embedding UMAPs,
key findings, and limitations.

## Where everything is stored

Setup creates this visible, Git-ignored local workspace:

```text
geneformer-workspace/
├── Geneformer/
│   └── Geneformer-V2-104M/  # downloaded model
└── analysis/
    ├── configs/
    ├── data/                 # downloaded tutorial datasets
    ├── input_data/
    ├── notebooks/
    ├── results/
    ├── scripts/
    ├── pyproject.toml
    └── uv.lock
```

Your data and generated files are not committed to this starter repository.
For durable work, initialize a separate Git repository inside `analysis` or
copy the generated analysis directory to its own project.

Stop JupyterLab before updating. Installations created by older releases are
moved automatically from `.geneformer-workspace/` to `geneformer-workspace/`
the next time `./setup.sh` runs. Existing models and datasets are moved in
place and are not downloaded again.

## Important data notes

- Geneformer expects human transcriptomic data with Ensembl gene identifiers.
- Match the V1 or V2 dictionaries to the selected model.
- Keep donors separated between training and evaluation datasets.
- Try a small tokenization and forward pass before starting a long job.
- GPU resources are recommended for efficient model use and fine-tuning.

### Missing `Python.h`

Older revisions of this starter could select the system Python on some DGX OS
partner images. Those images may omit `python3.12-dev`, causing
`accumulation-tree` to fail with `fatal error: Python.h: No such file or
directory`. Current setup avoids that OS-specific dependency by requiring a
uv-managed Python distribution that includes the headers.

### Tokenizer `KeyError` from `ensembl_id_collapsed`

Geneformer's current tokenizer uses pandas 2.x positional indexing. If an
older starter environment resolved pandas 3, H5AD tokenization can fail with a
`KeyError` mentioning `ensembl_id_collapsed`. Update the environment in place:

```bash
git pull --ff-only
./setup.sh
```

Setup constrains pandas below version 3; the input H5AD does not need to be
recreated or downloaded again.

## Documentation

- [Geneformer getting started](https://geneformer.readthedocs.io/en/latest/getstarted.html)
- [Geneformer model repository](https://huggingface.co/ctheodoris/Geneformer)
- [Geneformer examples](https://huggingface.co/ctheodoris/Geneformer/tree/main/examples)
- [uv project guide](https://docs.astral.sh/uv/guides/projects/)

## License

This setup helper is released under the MIT License. Geneformer and its model
assets are separate upstream works under their own license and terms.
