from pathlib import Path

import pytest

from analysis.scripts.smoke_test import find_models


ROOT = Path(__file__).resolve().parents[1]


def test_find_models_returns_only_configured_geneformer_directories(tmp_path: Path) -> None:
    configured = tmp_path / "Geneformer-V2-104M"
    configured.mkdir()
    (configured / "config.json").write_text("{}", encoding="utf-8")
    (configured / "model.safetensors").write_bytes(b"0" * 2048)

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
    (model / "model.safetensors").write_bytes(b"0" * 2048)

    assert find_models(tmp_path) == [directory]


def test_find_models_ignores_git_lfs_pointer(tmp_path: Path) -> None:
    model = tmp_path / "Geneformer-V2-104M"
    model.mkdir()
    (model / "config.json").write_text("{}", encoding="utf-8")
    (model / "model.safetensors").write_text(
        "version https://git-lfs.github.com/spec/v1\n",
        encoding="utf-8",
    )

    assert find_models(tmp_path) == []


@pytest.mark.parametrize("profile", ["cpu", "cu130", "default"])
def test_analysis_profiles_constrain_pandas_below_version_three(profile: str) -> None:
    template = ROOT / "analysis" / "profiles" / f"pyproject.{profile}.toml"

    assert '"pandas<3"' in template.read_text(encoding="utf-8")


@pytest.mark.parametrize("profile", ["cpu", "cu130", "default"])
def test_analysis_profiles_include_allograft_tutorial_dependencies(profile: str) -> None:
    template = ROOT / "analysis" / "profiles" / f"pyproject.{profile}.toml"
    template_text = template.read_text(encoding="utf-8")

    assert '"scikit-learn>=1.5"' in template_text
    assert '"seaborn>=0.13"' in template_text
