#!/usr/bin/env bash
set -euo pipefail

DEFAULT_GENEFORMER_REF="04c2b2e84da7c0f385c3f9ad8f3ec24bab6650e5"

usage() {
  cat >&2 <<'EOF'
Usage: bootstrap_workspace.sh WORKSPACE_ROOT ANALYSIS_NAME PROFILE [GENEFORMER_REF] [MODEL]

Profiles: default, cpu, cu130
Models:   v2-104m (default), v2-316m, v1-10m, none, all
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 3 || $# -gt 5 ]]; then
  usage
  exit 2
fi

workspace_input="$1"
analysis_name="$2"
profile="$3"
geneformer_ref="${4:-$DEFAULT_GENEFORMER_REF}"
model="${5:-v2-104m}"

case "$profile" in
  default|cpu|cu130) ;;
  *) usage; exit 2 ;;
esac

case "$model" in
  v2-104m|v2-316m|v1-10m|none|all) ;;
  *) usage; exit 2 ;;
esac

if [[ -z "$analysis_name" || "$analysis_name" == */* \
  || "$analysis_name" == "." || "$analysis_name" == ".." ]]; then
  echo "ANALYSIS_NAME must be one non-empty directory name without slashes." >&2
  exit 2
fi

for required_command in git git-lfs uv; do
  command -v "$required_command" >/dev/null 2>&1 || {
    echo "Missing required command: $required_command" >&2
    exit 1
  }
done

# Some DGX OS partner images include the Python runtime without development
# headers. Geneformer's tdigest dependency builds a small C extension, so use a
# uv-managed CPython distribution that includes Python.h on every platform.
uv python install 3.12 --no-bin

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
setup_root="$(cd "$script_dir/.." && pwd)"
template_dir="$setup_root/templates"

mkdir -p "$workspace_input"
workspace_root="$(realpath "$workspace_input")"
geneformer_root="$workspace_root/Geneformer"
analysis_root="$workspace_root/$analysis_name"

git lfs install --skip-repo

fresh_clone=false
if [[ ! -e "$geneformer_root" ]]; then
  GIT_LFS_SKIP_SMUDGE=1 git clone \
    https://huggingface.co/ctheodoris/Geneformer \
    "$geneformer_root"
  git -C "$geneformer_root" checkout --detach "$geneformer_ref"
  fresh_clone=true
elif [[ ! -d "$geneformer_root/.git" ]]; then
  echo "Existing path is not a Git checkout: $geneformer_root" >&2
  exit 1
else
  actual_ref="$(git -C "$geneformer_root" rev-parse HEAD)"
  requested_ref="$(git -C "$geneformer_root" rev-parse "$geneformer_ref^{commit}")"
  if [[ "$actual_ref" != "$requested_ref" ]]; then
    echo "Existing Geneformer checkout does not match $geneformer_ref." >&2
    echo "Use a separate workspace or resolve the checkout intentionally." >&2
    exit 1
  fi
fi

if ! git -C "$geneformer_root" diff --quiet \
  || ! git -C "$geneformer_root" diff --cached --quiet; then
  echo "Existing Geneformer checkout has tracked modifications." >&2
  echo "Use a clean checkout so the recorded commit fully describes the source." >&2
  exit 1
fi

case "$model" in
  v2-104m)
    lfs_include="geneformer/*.pkl,Geneformer-V2-104M/*"
    ;;
  v2-316m)
    lfs_include="geneformer/*.pkl,Geneformer-V2-316M/*"
    ;;
  v1-10m)
    lfs_include="geneformer/gene_dictionaries_30m/*.pkl,Geneformer-V1-10M/*"
    ;;
  none)
    lfs_include=""
    ;;
  all)
    lfs_include="*"
    ;;
esac

if [[ -n "$lfs_include" ]]; then
  git -C "$geneformer_root" lfs pull --include="$lfs_include" --exclude=""
elif [[ "$fresh_clone" == true ]]; then
  echo "Skipping Geneformer model and dictionary downloads (MODEL=none)."
fi

if [[ -e "$analysis_root" ]]; then
  echo "Refusing to overwrite existing analysis path: $analysis_root" >&2
  exit 1
fi

analysis_created=true
cleanup_failed_analysis() {
  if [[ "$analysis_created" == true && -d "$analysis_root" ]]; then
    rm -rf -- "$analysis_root"
  fi
}
trap cleanup_failed_analysis EXIT

mkdir -p \
  "$analysis_root/scripts" \
  "$analysis_root/notebooks" \
  "$analysis_root/configs" \
  "$analysis_root/results"
cp "$template_dir/.python-version" "$analysis_root/.python-version"
cp "$template_dir/.gitignore" "$analysis_root/.gitignore"
cp "$template_dir/README.md" "$analysis_root/README.md"
cp "$template_dir/pyproject.$profile.toml" "$analysis_root/pyproject.toml"
cp "$template_dir/analysis.py" "$analysis_root/scripts/analysis.py"
cp "$setup_root/scripts/smoke_test.py" "$analysis_root/scripts/smoke_test.py"
cp -R "$setup_root/notebooks/." "$analysis_root/notebooks/"
chmod +x "$analysis_root/scripts/analysis.py" "$analysis_root/scripts/smoke_test.py"

git -C "$geneformer_root" rev-parse HEAD > "$analysis_root/.geneformer-commit"

cd "$analysis_root"
uv lock --managed-python
uv sync --locked --managed-python
smoke_arguments=(--geneformer-root "$geneformer_root")
if [[ "$profile" == "cu130" ]]; then
  smoke_arguments+=(--require-cuda)
fi
uv run --locked --managed-python python scripts/smoke_test.py "${smoke_arguments[@]}"

analysis_created=false
trap - EXIT

echo "Created Geneformer analysis at $analysis_root"
echo "Commit pyproject.toml, uv.lock, .python-version, and .geneformer-commit."
