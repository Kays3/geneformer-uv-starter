from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"


def test_analysis_has_one_canonical_tracked_structure() -> None:
    expected = {
        "datasets",
        "notebooks",
        "profiles",
        "results",
        "scripts",
    }

    assert expected.issubset({path.name for path in ANALYSIS.iterdir() if path.is_dir()})
    for retired_duplicate in ("datasets", "notebooks", "templates"):
        assert not (ROOT / retired_duplicate).exists()


def test_bootstrap_reads_only_from_canonical_analysis_source() -> None:
    bootstrap = (ROOT / "scripts" / "bootstrap_workspace.sh").read_text(encoding="utf-8")

    assert 'analysis_source="$setup_root/analysis"' in bootstrap
    assert "$setup_root/templates" not in bootstrap
    assert "$setup_root/notebooks" not in bootstrap
    assert "$setup_root/scripts/smoke_test.py" not in bootstrap
