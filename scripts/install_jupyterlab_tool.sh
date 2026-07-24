#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: ./scripts/install_jupyterlab_tool.sh

Install JupyterLab as a user-wide uv tool without modifying the operating
system Python. The executable is placed in uv's tool bin directory.
EOF
  exit 0
fi

if [[ $# -ne 0 ]]; then
  echo "This command does not accept arguments." >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required but was not found on PATH." >&2
  exit 1
fi

jupyterlab_spec="${JUPYTERLAB_TOOL_SPEC:-jupyterlab>=4,<5}"
echo "Installing user-wide JupyterLab tool ($jupyterlab_spec)..."
uv tool install "$jupyterlab_spec"

tool_bin="$(uv tool dir --bin)"
if [[ ":${PATH}:" != *":${tool_bin}:"* ]]; then
  uv tool update-shell
  echo "Added $tool_bin to the shell PATH configuration."
  echo "Open a new terminal before running jupyter-lab."
fi

"$tool_bin/jupyter-lab" --version
