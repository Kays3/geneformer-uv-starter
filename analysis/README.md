# Geneformer analysis

This is the canonical upstream source for the starter's notebooks, dataset
manifests, dependency profiles, reviewed results, and analysis scripts. Edit
these files here rather than in the generated `geneformer-workspace/`.

During setup, the selected profile and runnable files are copied into
`geneformer-workspace/analysis`. That runtime analysis uses the adjacent
`../Geneformer` checkout as an editable uv dependency, whose exact upstream
revision is recorded in `.geneformer-commit`.

## Generated workspace

```bash
uv sync --frozen --managed-python
uv run --frozen --managed-python python scripts/smoke_test.py --geneformer-root ../Geneformer
uv run --frozen --managed-python jupyter lab
```

Place scripts in `scripts/`, notebooks in `notebooks/`, configuration in
`configs/`, and small reviewed outputs in `results/`. Private or large inputs
and outputs are ignored by default.

The `profiles/` directory is upstream-only. Setup selects one profile and
materializes it as the generated analysis's `pyproject.toml`.
