#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./start.sh [check]

With no argument, start JupyterLab. Use "check" to validate the environment.
EOF
  exit 0
fi

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
analysis_root="$repository_root/.geneformer-workspace/analysis"

if [[ ! -f "$analysis_root/uv.lock" ]]; then
  echo "Geneformer is not set up yet. Run ./setup.sh first." >&2
  exit 1
fi

cd "$analysis_root"

if [[ "${1:-lab}" == "check" ]]; then
  exec uv run --locked python scripts/smoke_test.py \
    --geneformer-root ../Geneformer
fi

echo "Starting JupyterLab. Stop it with Ctrl+C."
exec uv run --locked jupyter lab
