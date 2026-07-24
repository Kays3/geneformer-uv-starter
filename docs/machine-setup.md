# Geneformer setup on a preinstalled NVIDIA GB10 machine

This tutorial is for ASUS Ascent GX10 and Lenovo ThinkStation PGX machines.
They arrive with Ubuntu-based DGX OS, the NVIDIA driver, and the GB10 software
stack preinstalled. This guide does **not** reinstall Ubuntu.

The setup sequence is:

1. update the supported NVIDIA driver and platform stack;
2. verify the GPU with `nvidia-smi`;
3. install Tailscale, tmux, Git LFS, and UV;
4. connect both computers to the same Tailscale network;
5. install JupyterLab user-wide through UV;
6. install and test Geneformer; and
7. run JupyterLab persistently in tmux over Tailscale.

## Before you start

You need:

- an ASUS Ascent GX10 or Lenovo ThinkStation PGX already booted into its
  supplied operating system;
- a stable internet connection and power source;
- administrator (`sudo`) access;
- a second computer with a browser, signed in to the same Tailscale network;
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

## 3. Install Tailscale, tmux, Git LFS, and UV

Ubuntu is already installed. The following `apt-get update` refreshes package
metadata; it does not reinstall or upgrade the operating system:

```bash
sudo apt-get update
sudo apt-get install -y git git-lfs curl tmux
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
```

`sudo tailscale up` prints an authentication URL. Open it and add the machine
to your tailnet. Install Tailscale on the client computer as well and sign in
to the same tailnet. Then verify on the Geneformer machine:

```bash
git --version
git-lfs version
git lfs install
tmux -V
tailscale status
tailscale ip -4
uv --version
```

The last Tailscale command should print this machine's stable tailnet IPv4
address. The remote launcher binds JupyterLab only to that address—not to
`0.0.0.0`—so it is not exposed on every network interface. Tailnet access
rules still determine which Tailscale users and devices can connect.

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

## 7. Start JupyterLab persistently over Tailscale

Start JupyterLab in a detached tmux session, bound to the machine's Tailscale
IPv4 address:

```bash
./start.sh remote
./start.sh remote-status
```

The status output contains a URL such as
`http://100.x.y.z:8888/lab?token=...`. Open that complete URL on the client
computer. Keep the token private. Both computers must be connected to
Tailscale, but they do not need to be on the same physical network.

The process survives a dropped SSH connection because it runs inside tmux.
Use these lifecycle commands from the repository:

```bash
./start.sh remote-status  # show the token URL and recent output
./start.sh remote-attach  # interact with Jupyter; detach with Ctrl-b, then d
./start.sh remote-stop    # stop JupyterLab when finished
```

Inside an attached tmux session, press `Ctrl-b` and then `d` to detach without
stopping JupyterLab. Do not press `Ctrl-c` unless you intend to stop the
server. The starter notebooks are under
`geneformer-workspace/analysis/notebooks/`.

The launcher automatically loads the repository's
[`config/tmux.conf`](../config/tmux.conf) on an isolated tmux socket, so it
does not replace your personal `~/.tmux.conf` or alter unrelated tmux
sessions. Mouse scrolling, pane selection, and a 100,000-line history are
enabled. Copy and paste work as follows:

- Drag with the mouse to copy a selection to tmux's buffer. When the SSH
  terminal supports OSC 52, tmux also sends it to the client clipboard.
- Press `Ctrl-b`, then `[` to enter keyboard copy mode. Move to the desired
  text, press `v` to begin selecting, and press `y` to copy.
- Press `Ctrl-b`, then `]` to paste the latest tmux buffer.
- Hold `Shift` while dragging if you want the terminal application's native
  selection instead of tmux mouse handling, then use the client's normal copy
  shortcut.

Clipboard forwarding depends on the SSH terminal's OSC 52 policy. The tmux
buffer shortcuts continue to work even when client clipboard forwarding is
disabled.

To reconnect after logging out, SSH to the machine over its Tailscale IP (or
use its MagicDNS name), enter the repository, and run:

```bash
cd "$HOME/projects/geneformer-uv-starter"
./start.sh remote-status
./start.sh remote-attach
```

Tailscale SSH is optional. Standard OpenSSH over the Tailscale network works
without enabling it. If your tailnet administrator permits Tailscale SSH, it
can be enabled separately with `sudo tailscale set --ssh`.

For local desktop-only use, the original foreground command remains available:

```bash
./start.sh
```

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
| `Tailscale is not connected` | Run `sudo tailscale up`, authenticate, and check `tailscale status` |
| Remote URL does not open | Connect the client to the same tailnet and verify `tailscale ping <server-IP>` |
| tmux session already exists | Use `./start.sh remote-status` or `./start.sh remote-attach` |
| Port 8888 is occupied | Check `./start.sh remote-status`; Jupyter retries on the next available port |
| Model download stops | Check internet access and free disk space, then rerun `./setup.sh` |

For model choices, profiles, workspace layout, datasets, and application-level
troubleshooting, see the [main README](../README.md).
