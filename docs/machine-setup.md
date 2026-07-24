# Geneformer setup on a preinstalled NVIDIA GB10 machine

This tutorial is for ASUS Ascent GX10 and Lenovo ThinkStation PGX machines.
They arrive with Ubuntu-based DGX OS, the NVIDIA driver, and the GB10 software
stack preinstalled. This guide does **not** reinstall Ubuntu.

The setup sequence is:

1. update the supported NVIDIA driver and platform stack;
2. verify the GPU with `nvidia-smi`;
3. install Git LFS and UV;
4. install JupyterLab user-wide through UV; and
5. install and test Geneformer.

## Before you start

You need:

- an ASUS Ascent GX10 or Lenovo ThinkStation PGX already booted into its
  supplied operating system;
- a stable internet connection and power source;
- administrator (`sudo`) access;
- at least 50 GB free for the default model and environment; and
- a maintenance window for the NVIDIA update and reboot.

Back up important notebooks and results before updating the platform.

## 1. Update the NVIDIA driver and platform stack

The NVIDIA driver is part of the tested GB10 platform stack. Update it through
the machine's supported graphical updater rather than installing an isolated
driver package.

### NVIDIA DGX Dashboard

NVIDIA recommends the DGX Dashboard for system, firmware, and NVIDIA-driver
updates on DGX Spark. From the desktop:

1. Open **Show Apps**.
2. Open **DGX Dashboard**.
3. Review the available update and its release notes.
4. Close running applications and save your work.
5. Apply the update while the machine remains connected to stable power.
6. Reboot when requested.

Official references:

- [NVIDIA DGX Dashboard](https://docs.nvidia.com/dgx/dgx-spark/dgx-dashboard.html)
- [NVIDIA OS and Component Update Guide](https://docs.nvidia.com/dgx/dgx-spark/os-and-component-update.html)
- [NVIDIA DGX Spark release notes](https://docs.nvidia.com/dgx/dgx-spark/release-notes.html)

### ASUS and Lenovo partner machines

Partner releases may arrive on a different schedule from NVIDIA's Founders
Edition. If the machine vendor supplies its own update tool or release
instructions, use that supported path:

- [ASUS Ascent GX10 drivers, BIOS, and firmware](https://www.asus.com/us/supportonly/gx10/helpdesk_download/)
- [Lenovo ThinkStation PGX user guide](https://support.lenovo.com/us/en/documentation/sg10462)
- [Lenovo ThinkStation PGX drivers and software](https://pcsupport.lenovo.com/us/en/products/workstations/thinkstation-p-series-workstations/thinkstation-pgx/downloads)

Do not replace the supplied GB10 driver with a generic NVIDIA `.run` installer
or run `ubuntu-drivers install` merely to obtain a higher version number. The
kernel, firmware, driver, and CUDA components are validated together.

## 2. Verify the updated GPU

After the reboot, open a terminal and run:

```bash
uname -m
nvidia-smi
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader
```

The expected architecture is `aarch64`, and the GPU name should contain
`GB10`. Continue only when `nvidia-smi` displays the GPU and driver without an
error.

The CUDA version shown by `nvidia-smi` is the newest CUDA runtime supported by
the driver. It does not mean you need to install a separate system-wide CUDA
Toolkit; the starter installs the required PyTorch CUDA packages in its locked
environment.

If `nvidia-smi` fails, stop here and use the ASUS or Lenovo support path above.
Useful diagnostics to provide to support are:

```bash
lspci | grep -i nvidia
uname -r
dkms status
journalctl -k -b | grep -iE 'nvidia|nouveau|secure boot'
```

## 3. Install Git LFS and UV

Ubuntu is already installed. The following `apt-get update` refreshes package
metadata; it does not reinstall or upgrade the operating system:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

Open a new terminal and verify:

```bash
git --version
git-lfs version
git lfs install
uv --version
```

UV manages its own Python installations and isolated environments without
modifying Ubuntu's system Python.

## 4. Install JupyterLab user-wide with UV

Install JupyterLab as a UV tool:

```bash
uv tool install 'jupyterlab>=4,<5'
uv tool update-shell
```

Open a new terminal after `uv tool update-shell`, then verify:

```bash
command -v jupyter-lab
jupyter-lab --version
uv tool list
```

This is global for the current user: `jupyter-lab` is available across that
user's projects. UV keeps it in an isolated tool environment; it is not
installed into the root account or Ubuntu's system Python.

The repository also provides an idempotent installer for the same operation:

```bash
./scripts/install_jupyterlab_tool.sh
```

Run that helper after cloning the repository, or use it later to repair the
user-wide command.

## 5. Clone and install Geneformer

Choose a directory for projects, clone this repository, and run setup:

```bash
mkdir -p "$HOME/projects"
cd "$HOME/projects"
git clone https://github.com/Kays3/geneformer-uv-starter.git
cd geneformer-uv-starter
./setup.sh
```

On an ARM64 system whose GPU name contains `GB10`, setup automatically selects
the CUDA 13.0 profile. It:

- installs or verifies user-wide JupyterLab;
- downloads the selected Geneformer checkpoint;
- creates `geneformer-workspace/analysis/`;
- installs a UV-managed Python 3.12 and locked dependencies; and
- requires PyTorch to complete a CUDA tensor operation.

The default checkpoint is Geneformer V2 104M. Setup may take several minutes
depending on the network connection.

## 6. Verify Geneformer and CUDA

Run:

```bash
./start.sh check
```

A successful GB10 report includes values similar to:

```json
{
  "machine": "aarch64",
  "torch_cuda_version": "13.0",
  "cuda_available": true,
  "cuda_self_test": true,
  "gpu": "NVIDIA GB10"
}
```

Both CUDA fields must be `true`.

The analysis lockfile can also be checked directly:

```bash
cd geneformer-workspace/analysis
uv lock --check
cd ../..
```

No output from `uv lock --check` means the lockfile matches the project.

## 7. Start JupyterLab

Start JupyterLab with the locked Geneformer environment:

```bash
./start.sh
```

Open the local URL printed in the terminal. The starter notebooks are under
`geneformer-workspace/analysis/notebooks/`. Stop JupyterLab with `Ctrl`+`C`
and keep its access token private.

For a general JupyterLab session outside Geneformer, use the user-wide command:

```bash
jupyter-lab
```

## Updating later

Check the ASUS or Lenovo update channel periodically for supported NVIDIA
driver and platform updates. Apply those updates before rerunning the CUDA
check:

```bash
nvidia-smi
cd "$HOME/projects/geneformer-uv-starter"
git pull --ff-only
./setup.sh
./start.sh check
```

Do not substitute a generic driver-install command for the vendor update path.

## Troubleshooting

| Symptom | First action |
| --- | --- |
| `nvidia-smi` fails | Stop and use the ASUS or Lenovo supported update/recovery path |
| Setup selects CPU on a GB10 machine | Confirm `uname -m` is `aarch64` and the GPU name contains `GB10` |
| CUDA smoke test fails | Verify the vendor NVIDIA update completed and rerun `nvidia-smi` |
| `uv: command not found` | Open a new terminal or follow the PATH message printed by the UV installer |
| `jupyter-lab: command not found` | Run `uv tool update-shell`, open a new terminal, and check `uv tool list` |
| Git LFS is missing | Run `sudo apt-get install -y git-lfs` and `git lfs install` |
| Model download stops | Check internet access and free disk space, then rerun `./setup.sh` |

For model choices, profiles, workspace layout, datasets, and application-level
troubleshooting, see the [main README](../README.md).
