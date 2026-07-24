#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./setup.sh [PROFILE] [MODEL]

Profiles: auto (default), cpu, default, cu130
Models:   v2-104m (default), v2-316m, v1-10m, none, all
EOF
  exit 0
fi

requested_profile="${1:-auto}"
model="${2:-v2-104m}"
repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
legacy_workspace_root="$repository_root/.geneformer-workspace"
workspace_root="$repository_root/geneformer-workspace"
analysis_root="$workspace_root/analysis"

if [[ -d "$legacy_workspace_root" ]]; then
  if [[ -e "$workspace_root" ]]; then
    echo "Both legacy and visible Geneformer workspaces exist:" >&2
    echo "  $legacy_workspace_root" >&2
    echo "  $workspace_root" >&2
    echo "Preserve the workspace you need, remove the other, then rerun setup." >&2
    exit 1
  fi
  mv -- "$legacy_workspace_root" "$workspace_root"
  if [[ -d "$analysis_root/.venv" ]]; then
    rm -rf -- "$analysis_root/.venv"
  fi
  echo "Moved the existing workspace to visible directory: $workspace_root"
  echo "Models and datasets were preserved; rebuilding only the Python environment."
fi

case "$requested_profile" in
  auto)
    architecture="$(uname -m)"
    gpu_name="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 || true)"
    if [[ "$architecture" == "aarch64" && "$gpu_name" == *"GB10"* ]]; then
      profile="cu130"
      echo "Detected NVIDIA GB10 on ARM64; using the CUDA 13.0 profile."
    else
      profile="cpu"
      echo "No NVIDIA GB10 appliance detected; using the CPU profile."
    fi
    ;;
  cpu|default|cu130)
    profile="$requested_profile"
    ;;
  *)
    echo "Unknown profile: $requested_profile" >&2
    echo "Choose auto, cpu, default, or cu130." >&2
    exit 2
    ;;
esac

if [[ "$profile" == "cu130" ]]; then
  if [[ "$(uname -s)" != "Linux" ]] || ! command -v nvidia-smi >/dev/null 2>&1; then
    echo "The cu130 profile requires Linux and a working NVIDIA driver." >&2
    exit 1
  fi
  echo "GPU: $(nvidia-smi --query-gpu=name,driver_version --format=csv,noheader | head -1)"
fi

if ! command -v uv >/dev/null 2>&1; then
  cat >&2 <<'EOF'
uv is required but was not found.

Install it, then run ./setup.sh again:
  macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh
  Windows:     use WSL, or follow https://docs.astral.sh/uv/
EOF
  exit 1
fi

"$repository_root/scripts/install_jupyterlab_tool.sh"

if [[ -d "$analysis_root" ]]; then
  echo "Updating the existing Geneformer starter environment..."
  mkdir -p "$analysis_root/notebooks"
  tutorial_source="$repository_root/notebooks/01_stage1_cell_type_tutorial.ipynb"
  tutorial_target="$analysis_root/notebooks/01_stage1_cell_type_tutorial.ipynb"
  tutorial_backup="$analysis_root/notebooks/01_stage1_cell_type_tutorial.user-backup.ipynb"
  if [[ -e "$tutorial_target" ]] && ! cmp -s "$tutorial_source" "$tutorial_target"; then
    cp "$tutorial_target" "$tutorial_backup"
    echo "Preserved the previous tutorial as $(basename "$tutorial_backup")."
  fi
  cp "$tutorial_source" "$tutorial_target"
  allograft_tutorial_source="$repository_root/notebooks/02_lung_allograft_classification_tutorial.ipynb"
  allograft_tutorial_target="$analysis_root/notebooks/02_lung_allograft_classification_tutorial.ipynb"
  allograft_tutorial_backup="$analysis_root/notebooks/02_lung_allograft_classification_tutorial.user-backup.ipynb"
  if [[ -e "$allograft_tutorial_target" ]] \
    && ! cmp -s "$allograft_tutorial_source" "$allograft_tutorial_target"; then
    cp "$allograft_tutorial_target" "$allograft_tutorial_backup"
    echo "Preserved the previous allograft tutorial as $(basename "$allograft_tutorial_backup")."
  fi
  cp "$allograft_tutorial_source" "$allograft_tutorial_target"
  cp "$repository_root/scripts/smoke_test.py" "$analysis_root/scripts/smoke_test.py"
  missing_dependencies=()
  if ! grep -q 'ipywidgets' "$analysis_root/pyproject.toml"; then
    missing_dependencies+=('ipywidgets>=8.1.8')
  fi
  if ! grep -q '"pandas<3"' "$analysis_root/pyproject.toml"; then
    missing_dependencies+=('pandas<3')
  fi
  if ! grep -q 'scikit-learn' "$analysis_root/pyproject.toml"; then
    missing_dependencies+=('scikit-learn>=1.5')
  fi
  if ! grep -q 'seaborn' "$analysis_root/pyproject.toml"; then
    missing_dependencies+=('seaborn>=0.13')
  fi
  if (( ${#missing_dependencies[@]} > 0 )); then
    (
      cd "$analysis_root"
      uv add --managed-python "${missing_dependencies[@]}"
    )
  else
    (
      cd "$analysis_root"
      uv sync --locked --managed-python
    )
  fi
  echo "Geneformer is up to date. Run ./start.sh to open JupyterLab."
  exit 0
fi

if ! command -v git-lfs >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Git LFS is required but was not found.

Install it, then run ./setup.sh again:
  Ubuntu/Debian: sudo apt-get install git-lfs
  macOS:         brew install git-lfs
EOF
  exit 1
fi

echo "Setting up Geneformer (profile=$profile, model=$model, architecture=$(uname -m))..."
"$repository_root/scripts/bootstrap_workspace.sh" \
  "$workspace_root" \
  analysis \
  "$profile" \
  "${GENEFORMER_REF:-04c2b2e84da7c0f385c3f9ad8f3ec24bab6650e5}" \
  "$model"

cat <<'EOF'

Setup complete.

Visible workspace:
  geneformer-workspace/

Next step:
  ./start.sh
EOF
