"""Portable Phase III contracts; fixture data never become research findings."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from dashboard.app import check_dashboard
from mediscope.cli import PROJECT_ROOT, sha256
from mediscope.visualization.exports import EXPORT_NAMES, ExportError, verify_exports
from mediscope.visualization.figures import create_figures
from mediscope.visualization.notes import note_terms
from scripts.verify_powerbi_project import verify_project

EXPORT = PROJECT_ROOT / "powerbi" / "exports" / "v1"


def rows(name: str) -> list[dict[str, str]]:
    with (EXPORT / f"{name}.csv").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_portable_files_and_manifest() -> None:
    result = verify_exports()
    assert result["status"] == "PASS" and result["files"] == len(EXPORT_NAMES) == 19
    assert (EXPORT / "manifest.json").is_file()


def test_export_schemas_and_types() -> None:
    manifest = json.loads((EXPORT / "manifest.json").read_text(encoding="utf-8"))
    for name in EXPORT_NAMES:
        entries = rows(name)
        assert all(set(entry) == set(manifest["files"][name + ".csv"]["columns"]) for entry in entries)
        assert len(entries) == manifest["files"][name + ".csv"]["rows"]
    assert all(int(r["count"]) >= 0 for r in rows("outcomes"))
    assert all(0 <= float(r["pct_all"]) <= 100 for r in rows("outcomes"))
    bmi = next(r for r in rows("quality_metrics") if r["dataset_id"] == "kaggle_stroke" and r["feature"] == "bmi")
    assert int(bmi["missing_n"]) == 201
    assert float(bmi["missing_pct"]) == pytest.approx(201 / 5110 * 100)


def test_outcome_counts_and_denominators() -> None:
    overview = {r["dataset_id"]: int(r["rows"]) for r in rows("dataset_overview") if r["dataset_id"] != "synthea_csv"}
    for dataset_id, size in overview.items():
        outcome = [r for r in rows("outcomes") if r["dataset_id"] == dataset_id]
        assert sum(int(r["count"]) for r in outcome) == size
        assert abs(sum(float(r["pct_all"]) for r in outcome) - 100) < 1e-8
        assert {int(r["all_n"]) for r in outcome} == {size}


def test_hypothesis_snapshot_matches_phase2() -> None:
    export = {r["id"]: r for r in rows("hypotheses")}
    assert set(export) == {"H1", "H2", "H3"}
    for dataset in ("uci_cleveland_heart", "kaggle_stroke"):
        source = PROJECT_ROOT / "reports" / "tables" / "eda" / f"{dataset}_hypotheses.csv"
        with source.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                assert float(export[row["id"]]["p_value"]) == pytest.approx(float(row["p_value"]), rel=1e-12)
                assert float(export[row["id"]]["effect_size"]) == pytest.approx(float(row["effect_size"]), rel=1e-12)
                assert float(export[row["id"]]["ci_low"]) == pytest.approx(float(row["ci_low"]), rel=1e-12)
                assert float(export[row["id"]]["ci_high"]) == pytest.approx(float(row["ci_high"]), rel=1e-12)


def test_synthea_denominators_and_note_independence() -> None:
    overview = [r for r in rows("dataset_overview") if r["dataset_id"] == "synthea_csv"]
    assert {r["analysis_unit"]: int(r["rows"]) for r in overview} == {"synthetic patient": 1171, "synthetic encounter": 53346}
    assert sum(int(r["count"]) for r in rows("synthea_encounter_classes")) == 53346
    assert sum(int(r["encounters"]) for r in rows("synthea_monthly_encounters")) == 53346
    assert sum(int(r["patients"]) for r in rows("synthea_encounters_per_patient")) == 1171
    note = json.loads((PROJECT_ROOT / "data" / "metadata" / "synthea_note_source.json").read_text(encoding="utf-8"))
    assert note["note_count"] == 10
    assert note["generator_release"] == "Synthea v3.4.0"
    assert all("patient" not in r for r in rows("note_terms"))


def test_manifest_detects_modified_csv(tmp_path: Path) -> None:
    target = tmp_path / "powerbi" / "exports" / "v1"
    shutil.copytree(EXPORT, target)
    path = target / "outcomes.csv"
    path.write_text(path.read_text(encoding="utf-8") + "tampered\n", encoding="utf-8")
    with pytest.raises(ExportError, match="changed export"):
        verify_exports(tmp_path)


def test_fresh_clone_contract_without_raw_files(tmp_path: Path) -> None:
    shutil.copytree(EXPORT, tmp_path / "powerbi" / "exports" / "v1")
    assert not (tmp_path / "data").exists()
    assert verify_exports(tmp_path)["source_archives_required"] is False
    for relative in ("mediscope/__init__.py", "mediscope/cli.py", "mediscope/visualization/__init__.py",
                     "mediscope/visualization/exports.py"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT_ROOT / relative, target)
    shutil.copytree(PROJECT_ROOT / "dashboard", tmp_path / "dashboard", ignore=shutil.ignore_patterns("__pycache__"))
    result = subprocess.run([sys.executable, "-m", "dashboard.app", "--check"], cwd=tmp_path,
                            text=True, capture_output=True, check=True)
    assert json.loads(result.stdout)["raw_datasets_required"] is False


def test_powerbi_static_project() -> None:
    result = verify_project()
    assert result["pages"] == 6 and result["visuals"] == 29
    assert result["desktop_runtime"] == "NOT TESTED"
    assert not (PROJECT_ROOT / "powerbi" / "MediScopeAI.pbix").exists()
    script = (PROJECT_ROOT / "scripts" / "setup_powerbi_windows.ps1").read_text(encoding="utf-8")
    for required in ("$PSScriptRoot", "Get-FileHash", "Import-Csv", "-ne 19", "__MEDISCOPE_DATA_ROOT__", "[switch]$ValidateOnly", "Start-Process"):
        assert required in script


def test_cross_platform_launcher_and_dashboard_smoke() -> None:
    assert check_dashboard()["status"] == "PASS"
    script = PROJECT_ROOT / "scripts" / "run_dashboard_macos.sh"
    result = subprocess.run(["bash", str(script), "--check"], cwd=PROJECT_ROOT, text=True, capture_output=True, check=True)
    assert '"status": "PASS"' in result.stdout
    assert (PROJECT_ROOT / "scripts" / "run_dashboard_windows.ps1").is_file()
    assert (PROJECT_ROOT / "scripts" / "setup_powerbi_windows.ps1").is_file()


def test_dashboard_javascript_data_wiring() -> None:
    if shutil.which("node") is None:
        pytest.skip("Node.js is optional for running the dashboard; JS runtime smoke unavailable")
    result = subprocess.run(["node", "scripts/smoke_dashboard_js.js"], cwd=PROJECT_ROOT,
                            text=True, capture_output=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS" and len(payload["charts_by_page"]) == 6


def test_note_tokenization_fixture(tmp_path: Path) -> None:
    (tmp_path / "note.txt").write_text("Clinical note: glucose glucose blood pressure. 2024-01-01 Patient A1234.", encoding="utf-8")
    terms, info = note_terms(tmp_path)
    found = {r["term"]: r["count"] for r in terms}
    assert found["glucose"] == 2
    assert info["note_count"] == 1
    assert "2024" not in found and "a1234" not in found


def test_figure_exports_exist() -> None:
    root = PROJECT_ROOT / "reports" / "figures" / "phase3"
    names = ("heart_outcome_pie", "stroke_age_group_share_histogram", "stroke_glucose_aggregate_boxplot", "heart_pearson_heatmap", "diabetes_positive_symptom_frequencies", "synthea_independent_note_wordcloud")
    for name in names:
        for extension in ("png", "svg"):
            path = root / f"{name}.{extension}"
            assert path.is_file() and path.stat().st_size > 1000
    assert len(list((PROJECT_ROOT / "reports" / "figures" / "eda").glob("*.png"))) == 31


def test_figure_regeneration_is_byte_reproducible(tmp_path: Path) -> None:
    shutil.copytree(EXPORT, tmp_path / "powerbi" / "exports" / "v1")
    first = create_figures(tmp_path)
    hashes = {str(p.with_suffix(extension)): sha256(p.with_suffix(extension)) for p in first for extension in (".png", ".svg")}
    create_figures(tmp_path)
    assert hashes == {path: sha256(Path(path)) for path in hashes}
