import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_stage1_cell_type_tutorial.ipynb"
MANIFEST = ROOT / "datasets" / "nsclc_integrated.manifest.json"


def test_tutorial_notebook_is_valid_and_all_code_compiles() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

    assert notebook["nbformat"] == 4
    assert notebook["cells"][0]["cell_type"] == "markdown"
    assert "Stage 1 Cell-Type Classifier" in "".join(notebook["cells"][0]["source"])

    for index, cell in enumerate(notebook["cells"]):
        if cell["cell_type"] == "code":
            compile("".join(cell["source"]), f"{NOTEBOOK}:cell-{index}", "exec")


def test_tutorial_and_manifest_use_the_verified_original_dataset() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    notebook_text = NOTEBOOK.read_text(encoding="utf-8")

    assert manifest["bytes"] == 12_897_440_967
    assert manifest["sha256"] == (
        "141db65b76b1e34f895131e36c74cd829db05fc037f8cd2f422c2960a5a266cd"
    )
    assert manifest["canonical_download_url"] in notebook_text
    assert manifest["sha256"] in notebook_text
