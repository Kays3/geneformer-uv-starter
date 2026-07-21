# Geneformer analysis

This analysis uses the adjacent `../Geneformer` checkout as an editable uv
dependency. Its exact upstream revision is recorded in `.geneformer-commit`.

## Start

```bash
uv sync --frozen
uv run --frozen python scripts/smoke_test.py --geneformer-root ../Geneformer
uv run --frozen jupyter lab
```

Place scripts in `scripts/`, notebooks in `notebooks/`, configuration in
`configs/`, and small reviewed outputs in `results/`. Private or large inputs
and outputs are ignored by default.
