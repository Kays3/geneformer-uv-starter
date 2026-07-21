from pathlib import Path

import pytest

from scripts.smoke_test import find_models


def test_find_models_returns_only_configured_geneformer_directories(tmp_path: Path) -> None:
    configured = tmp_path / "Geneformer-V2-104M"
    configured.mkdir()
    (configured / "config.json").write_text("{}", encoding="utf-8")

    (tmp_path / "Geneformer-V2-316M").mkdir()
    other = tmp_path / "unrelated"
    other.mkdir()
    (other / "config.json").write_text("{}", encoding="utf-8")

    assert find_models(tmp_path) == ["Geneformer-V2-104M"]


@pytest.mark.parametrize("directory", ["Geneformer-V1-10M", "Geneformer-V2-316M"])
def test_find_models_sorts_supported_directory_names(tmp_path: Path, directory: str) -> None:
    model = tmp_path / directory
    model.mkdir()
    (model / "config.json").write_text("{}", encoding="utf-8")

    assert find_models(tmp_path) == [directory]
