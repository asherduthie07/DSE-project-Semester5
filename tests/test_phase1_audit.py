"""Controlled fixtures for Phase I verification; no fixture is research data."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import zipfile

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import KFold

from mediscope.cli import audit_dataset, main
from mediscope.preparation import PreparationError, load_config, prepare_dataset, prepare_table
from mediscope.preprocessors import build_preprocessor
from scripts.verify_phase1_outputs import verify

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / name, dtype="string", keep_default_na=False, na_values=["", "?"])


def _fitted_parameters(transformer) -> dict[str, object]:
    numeric = transformer.named_transformers_["numeric"]
    nominal = transformer.named_transformers_["nominal"]
    return {
        "imputer": numeric.named_steps["impute"].statistics_.copy(),
        "scaler_mean": numeric.named_steps["scale"].mean_.copy(),
        "nominal_categories": [values.copy() for values in nominal.named_steps["encode"].categories_],
    }


def _same_parameters(left: dict[str, object], right: dict[str, object]) -> None:
    np.testing.assert_array_equal(left["imputer"], right["imputer"])
    np.testing.assert_array_equal(left["scaler_mean"], right["scaler_mean"])
    for left_values, right_values in zip(left["nominal_categories"], right["nominal_categories"]):
        np.testing.assert_array_equal(left_values, right_values)


def test_controlled_diabetes_missing_duplicate_extreme_and_invalid() -> None:
    raw = _fixture("diabetes_controlled.csv")
    config = load_config()
    valid = prepare_table(raw.iloc[:3].copy(), "uci_early_diabetes", "diabetes_data_upload.csv", config)
    assert valid.report["duplicates"]["exact_before"] == 1
    assert valid.report["duplicates"]["retained"] == 1
    assert 119 in valid.data["Age"].tolist()  # extreme but within documented 0–120 rule
    with pytest.raises(PreparationError, match="Invalid source values"):
        prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", config)
    nullified = prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", dict(config, invalid_feature_policy="nullify"))
    assert nullified.report["initial"]["missing"]["Age"] == 1  # source '?'
    assert nullified.report["invalid_values"]["Age"]["count"] == 1  # impossible 200
    assert nullified.report["invalid_values"]["Polyuria"]["count"] == 1  # unknown Maybe
    assert nullified.report["final"]["missing"]["Age"] == 2
    assert nullified.report["final"]["missing"]["Polyuria"] == 1
    assert len(nullified.data) == 6


def test_controlled_repeated_encounters_and_duplicate_unique_key() -> None:
    raw = _fixture("hospital_encounters_controlled.csv")
    config = load_config()
    visits = prepare_table(raw.iloc[:2].copy(), "synthea_csv", "csv/encounters.csv", config)
    assert len(visits.data) == 2
    assert visits.data["PATIENT"].nunique() == 1
    assert visits.data["Id"].nunique() == 2
    with pytest.raises(PreparationError, match="Unique record key"):
        prepare_table(raw, "synthea_csv", "csv/encounters.csv", config)


def test_audit_dataset_selection_and_missing_archive(tmp_path: Path, capsys) -> None:
    code = main(["audit", "--dataset", "uci_cleveland_heart", "--raw-dir", str(tmp_path)])
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert len(result) == 1
    assert result[0]["status"] == "missing"
    with pytest.raises(PreparationError, match="Raw archive is missing"):
        prepare_dataset("uci_cleveland_heart", load_config(), raw_dir=tmp_path)


def test_audit_marks_mismatched_schema_invalid(tmp_path: Path) -> None:
    archive = tmp_path / "controlled.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("table.csv", "target,feature\nYes,1\n")
    dataset = {
        "name": "controlled test only", "archive": archive.name,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "tables": [{"member": "table.csv", "header": True, "columns": ["feature", "target"], "target": "target"}],
    }
    report = audit_dataset(dataset, tmp_path)
    assert report["checksum_matches_registry"] is True
    assert report["status"] == "invalid"
    assert report["tables"]["table.csv"]["schema_mismatches"]["column_order"] is True


def test_holdout_values_cannot_change_fitted_preprocessing() -> None:
    config = load_config()
    training = prepare_table(_fixture("stroke_train_controlled.csv"), "kaggle_stroke", "healthcare-dataset-stroke-data.csv", config).data
    holdout = _fixture("stroke_holdout_controlled.csv")
    transformer = build_preprocessor("kaggle_stroke", config)
    transformer.fit(training)
    before = _fitted_parameters(transformer)
    assert before["imputer"][2] == 30.0  # BMI training median
    assert before["scaler_mean"][0] == 35.0  # age training mean
    output = transformer.transform(holdout)
    names = transformer.get_feature_names_out().tolist()
    assert output[0, names.index("binary__hypertension")] == -1
    assert all(output[0, index] == 0 for index, name in enumerate(names) if name.startswith("nominal__gender_"))
    changed = holdout.copy()
    changed["age"] = [9999, -9999]
    changed["bmi"] = [9999, -9999]
    changed["gender"] = ["Another-unseen", "Yet-another-unseen"]
    transformer.transform(changed)
    _same_parameters(before, _fitted_parameters(transformer))


def test_each_cv_fold_fits_only_its_training_subset() -> None:
    config = load_config()
    frame = prepare_table(_fixture("stroke_train_controlled.csv"), "kaggle_stroke", "healthcare-dataset-stroke-data.csv", config).data
    fold_means: list[float] = []
    for train_index, test_index in KFold(n_splits=3, shuffle=False).split(frame):
        train = frame.iloc[train_index]
        validation = frame.iloc[test_index]
        transformer = build_preprocessor("kaggle_stroke", config).fit(train)
        before = _fitted_parameters(transformer)
        fold_means.append(float(before["scaler_mean"][0]))
        mutated = validation.copy()
        mutated["age"] = 9999.0
        mutated["gender"] = "unseen-in-fold"
        transformer.transform(validation)
        transformer.transform(mutated)
        _same_parameters(before, _fitted_parameters(transformer))
    assert len(set(fold_means)) == 3  # fold-local statistics differ, not one global fit


def test_output_verifier_reports_tampered_csv(tmp_path: Path) -> None:
    """The independent verifier must return FAIL, not crash, on corrupt output."""
    archive = tmp_path / "data" / "raw" / "controlled.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("table.csv", "feature,target\n1,0\n")
    raw_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"datasets": [{
        "id": "controlled", "archive": "controlled.zip", "sha256": raw_sha,
        "tables": [{"member": "table.csv", "header": True, "columns": ["feature", "target"], "target": "target"}],
    }]}))
    prepared = tmp_path / "data" / "processed" / "controlled.csv"
    prepared.parent.mkdir(parents=True)
    prepared.write_text("feature,target\n1,0\n")
    config = {"missing_tokens": ["", "?"]}
    (prepared.parent / "controlled_preparation_config.json").write_text(json.dumps(config))
    table = tmp_path / "reports" / "tables" / "controlled_quality.csv"
    table.parent.mkdir(parents=True)
    table.write_text("feature,missing_before,missing_after,invalid_found,iqr_outliers_before,iqr_outliers_after\nfeature,0,0,0,,\ntarget,0,0,0,,\n")
    figure = tmp_path / "reports" / "figures" / "controlled.png"
    figure.parent.mkdir(parents=True)
    figure.write_bytes(b"\x89PNG\r\n\x1a\n")
    report = tmp_path / "reports" / "quality" / "controlled.json"
    report.parent.mkdir(parents=True)
    report.write_text(json.dumps({
        "source": {"sha256": raw_sha}, "config": config,
        "tables": {"table.csv": {
            "initial": {"rows": 1, "columns": ["feature", "target"], "missing": {"feature": 0, "target": 0}},
            "duplicates": {"exact_before": 0, "removed": 0},
            "final": {"rows": 1, "columns": ["feature", "target"], "missing": {"feature": 0, "target": 0}},
            "invalid_values": {}, "outliers_after": {},
        }},
        "outputs": {"table.csv": {
            "prepared_csv": "data/processed/controlled.csv",
            "prepared_sha256": hashlib.sha256(prepared.read_bytes()).hexdigest(),
            "quality_table": "reports/tables/controlled_quality.csv",
            "boxplot": "reports/figures/controlled.png",
        }},
    }))
    (report.parent / "controlled.md").write_text("# Controlled test only\n")
    assert verify(tmp_path, registry)["status"] == "PASS"
    prepared.write_bytes(prepared.read_bytes() + b"\n")
    failed = verify(tmp_path, registry)
    assert failed["status"] == "FAIL"
    assert any("unreadable prepared CSV" in error for error in failed["errors"])
