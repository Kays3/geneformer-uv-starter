#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./setup.sh [PROFILE] [MODEL]

Profiles: cpu (default), default, cu130
Models:   v2-104m (default), v2-316m, v1-10m, none, all
EOF
  exit 0
fi

profile="${1:-cpu}"
model="${2:-v2-104m}"
repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace_root="$repository_root/.geneformer-workspace"
analysis_root="$workspace_root/analysis"

if [[ -d "$analysis_root" ]]; then
  echo "Geneformer is already set up."
  echo "Run ./start.sh to open JupyterLab."
  exit 0
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

if ! command -v git-lfs >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Git LFS is required but was not found.

Install it, then run ./setup.sh again:
  Ubuntu/Debian: sudo apt-get install git-lfs
  macOS:         brew install git-lfs
EOF
  exit 1
fi

echo "Setting up Geneformer (profile=$profile, model=$model)..."
"$repository_root/scripts/bootstrap_workspace.sh" \
  "$workspace_root" \
  analysis \
  "$profile" \
  "${GENEFORMER_REF:-04c2b2e84da7c0f385c3f9ad8f3ec24bab6650e5}" \
  "$model"

cat <<'EOF'

Setup complete.

Next step:
  ./start.sh
EOF
