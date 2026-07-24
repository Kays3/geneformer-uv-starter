# NVIDIA GPU setup for Geneformer

This tutorial starts with a working Linux machine and ends with a tested
Geneformer CUDA environment. It is intended for NVIDIA GB10 systems such as
the ASUS Ascent GX10 and Lenovo ThinkStation PGX, as well as supported Ubuntu
workstations with a discrete NVIDIA GPU.

## Scope

You do **not** need to install or reimage Ubuntu, run `apt full-upgrade`, install
a system-wide CUDA Toolkit, or replace a working NVIDIA driver to use this
starter.

The required starting state is:

- Ubuntu or the vendor-supplied DGX OS is already running;
- the machine has internet access and at least 50 GB free;
- you have `sudo` access for installing Git packages; and
- `nvidia-smi` can communicate with the NVIDIA GPU.

New GB10 appliances ship with a supported DGX OS and NVIDIA software stack.
Keep that supplied image. Reimaging and platform upgrades are recovery or
maintenance operations outside this Geneformer tutorial.

## 1. Verify the NVIDIA GPU

Open a terminal and run:

```bash
uname -m
nvidia-smi
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
```

An ASUS Ascent GX10 or Lenovo ThinkStation PGX should normally report
`aarch64` and a GPU name containing `GB10`. A conventional Intel or AMD
workstation normally reports `x86_64`.

Continue when `nvidia-smi` displays the GPU and driver without an error. The
CUDA version displayed by `nvidia-smi` is the maximum runtime supported by the
driver; it does not mean a CUDA Toolkit is installed. This starter installs
the required PyTorch CUDA runtime inside its UV-managed environment.

### If `nvidia-smi` fails

Do not replace a GB10 appliance driver with a generic NVIDIA `.run` installer
or run `ubuntu-drivers install` merely to obtain a newer version. The vendor
tests DGX OS, the kernel, firmware, and NVIDIA components as a platform stack.

- NVIDIA recommends its DGX Dashboard for DGX Spark system updates:
  [NVIDIA OS and Component Update Guide](https://docs.nvidia.com/dgx/dgx-spark/os-and-component-update.html).
- Lenovo PGX owners should use the
  [ThinkStation PGX user guide](https://support.lenovo.com/us/en/documentation/sg10462)
  and [PGX driver support](https://pcsupport.lenovo.com/us/en/products/workstations/thinkstation-p-series-workstations/thinkstation-pgx/downloads).
- Other partner appliances should use that manufacturer's support and
  recovery instructions.

For a standard Ubuntu workstation, follow the workstation vendor or
organization administrator's supported NVIDIA-driver procedure. Stop here
until this command succeeds:

```bash
nvidia-smi
```

Useful diagnostics to send to the vendor or administrator are:

```bash
lspci | grep -i nvidia
uname -r
dkms status
journalctl -k -b | grep -iE 'nvidia|nouveau|secure boot'
```

## 2. Install the repository prerequisites

The only Ubuntu packages required by the starter are Git, Git LFS, and `curl`.
Refreshing the package index is not a full operating-system upgrade:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs curl
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Open a new terminal so its `PATH` includes UV, then verify:

```bash
git --version
git-lfs version
git lfs install
uv --version
```

UV installs a private Python distribution and isolated environments. It does
not modify Ubuntu's system Python.

## 3. Clone and configure Geneformer

Choose a project directory, clone the starter, and run setup:

```bash
mkdir -p "$HOME/projects"
cd "$HOME/projects"
git clone https://github.com/Kays3/geneformer-uv-starter.git
cd geneformer-uv-starter
./setup.sh
```

On an ARM64 machine whose GPU name contains `GB10`, setup automatically uses
the CUDA 13.0 profile. It downloads the default Geneformer V2 104M checkpoint,
creates `geneformer-workspace/analysis/`, installs a UV-managed Python 3.12,
and validates a CUDA tensor operation.

For another Linux workstation with a compatible NVIDIA driver, explicitly
request the CUDA profile:

```bash
./setup.sh cu130
```

The command fails rather than silently accepting a broken CUDA environment.
Do not proceed to analysis until setup completes successfully.

## 4. Verify CUDA

Run the starter's smoke test:

```bash
./start.sh check
```

A working GPU result includes:

```json
{
  "torch_cuda_version": "13.0",
  "cuda_available": true,
  "cuda_self_test": true,
  "gpu": "NVIDIA GB10"
}
```

The exact GPU name can differ on a standard workstation. Both CUDA fields must
be `true`.

You can also inspect the locked environment:

```bash
cd geneformer-workspace/analysis
uv lock --check
cd ../..
```

No output from `uv lock --check` means the lockfile matches the project.

## 5. Start JupyterLab

Start JupyterLab with the locked Geneformer environment:

```bash
./start.sh
```

Open the local URL printed in the terminal. Stop the server with `Ctrl`+`C`.
Keep its access token private.

Setup also installs JupyterLab as an isolated user-wide UV tool. To install or
repair only that command:

```bash
./scripts/install_jupyterlab_tool.sh
jupyter-lab --version
```

## Updating the starter

Updating this repository does not require upgrading Ubuntu:

```bash
cd "$HOME/projects/geneformer-uv-starter"
git pull --ff-only
./setup.sh
./start.sh check
```

Manage DGX OS, firmware, and NVIDIA-driver updates separately through the
machine vendor. If `nvidia-smi` works and organizational policy does not
require a platform update, no operating-system upgrade is needed for this
Geneformer setup.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| `nvidia-smi` is missing or fails | Stop and use the machine vendor's supported driver/recovery procedure |
| Setup selects CPU on a GB10 | Confirm `uname -m` is `aarch64` and the GPU name from `nvidia-smi` contains `GB10` |
| CUDA smoke test fails | Confirm `nvidia-smi`; do not install random CUDA or driver packages |
| `uv: command not found` | Open a new terminal or follow the PATH message from the UV installer |
| Git LFS is missing | Run `sudo apt-get install -y git-lfs` and `git lfs install` |
| Model download stops | Confirm internet access and free disk space, then rerun `./setup.sh` |
| JupyterLab does not start | Run `./start.sh check`, then rerun `./setup.sh` |

For profile and model options, workspace layout, datasets, and
application-level troubleshooting, see the [main README](../README.md).
