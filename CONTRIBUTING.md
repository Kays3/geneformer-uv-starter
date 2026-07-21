# Contributing

Issues and pull requests are welcome. Please keep this repository focused on a
general Geneformer + uv setup and do not add private datasets, pretrained model
weights, generated checkpoints, or experiment-specific results.

Before opening a pull request:

```bash
uv sync --locked
uv run --locked ruff check .
uv run --locked pytest
bash -n scripts/bootstrap_workspace.sh
```

If changing a dependency or PyTorch profile, regenerate the relevant lockfile
and test a fresh bootstrap on the target platform.
