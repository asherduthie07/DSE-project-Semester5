"""Controlled test values only; none are used as research observations."""

from __future__ import annotations

import hashlib
import json
import shutil

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from mediscope.cli import main
from mediscope.eda.hypotheses import hypertension_test, welch_test
from mediscope.eda.runner import EDAError, _standard_tables, load_prepared, synthea_relationships
from mediscope.schema import TableSchema
from mediscope.eda.stats import bh_adjust, categorical_associations, categorical_summary, numeric_associations, numeric_summary


def test_numeric_sample_formulas_and_missing() -> None:
    frame = pd.DataFrame({"measure": [1.0, 2.0, 4.0, np.nan]})
    row = numeric_summary(frame, ("measure",))[0]
    assert row["n"] == 3 and row["missing_n"] == 1 and row["missing_pct"] == 25
    assert row["mean"] == pytest.approx(7 / 3)
    assert row["median"] == 2 and row["min"] == 1 and row["max"] == 4 and row["range"] == 3
    assert row["q1"] == 1.5 and row["q3"] == 3 and row["iqr"] == 1.5
    assert row["variance"] == pytest.approx(7 / 3)
    assert row["std"] == pytest.approx(np.sqrt(7 / 3))


def test_categorical_group_denominators() -> None:
    frame = pd.DataFrame({"class": [0, 0, 1], "symptom": ["Yes", None, "No"]})
    rows = categorical_summary(frame, ("symptom",), "class")
    yes = next(row for row in rows if row["group"] == "0" and row["category"] == "Yes")
    missing = next(row for row in rows if row["group"] == "0" and row["category"] == "<missing>")
    assert yes["count"] == 1 and yes["pct_all"] == 50 and yes["pct_nonmissing"] == 100
    assert missing["pct_nonmissing"] is None


def test_numeric_associations_exclude_ids_codes_and_constant() -> None:
    frame = pd.DataFrame({"id": [10, 20, 30, 40], "code": [1, 2, 1, 2], "x": [1, 2, 3, 4], "y": [4, 3, 2, 1], "constant": [2] * 4, "target": [0, 0, 1, 1]})
    rows, matrices, skipped = numeric_associations(frame, ("x", "y", "constant"), "target")
    assert skipped == ["constant"]
    assert list(matrices["pearson"]) == ["x", "y"]
    assert all("id" not in (row["left"], row["right"]) and "code" not in (row["left"], row["right"]) for row in rows)
    assert next(row for row in rows if row["method"] == "pearson")["coefficient"] == pytest.approx(-1)
    assert sum(row["method"] == "point_biserial" for row in rows) == 2


def test_diabetes_string_target_point_biserial_is_analysis_only() -> None:
    frame = pd.DataFrame({"Age": [20, 30, 40, 50], "class": ["Negative", "Negative", "Positive", "Positive"]})
    schema = TableSchema(continuous=("Age",))
    tables, _, _ = _standard_tables(frame, schema, "class")
    row = next(row for row in tables["correlations"] if row["method"] == "point_biserial")
    assert row["left"] == "class_binary" and row["n"] == 4 and row["coefficient"] > 0
    assert "class_binary" not in frame


def test_categorical_association_and_bh() -> None:
    frame = pd.DataFrame({"category": ["a"] * 5 + ["b"] * 5, "constant": ["same"] * 10, "target": [0] * 4 + [1] + [0] + [1] * 4})
    rows, skipped = categorical_associations(frame, ("category", "constant"), "target")
    assert skipped == ["constant"] and len(rows) == 1
    assert rows[0]["cramers_v"] == pytest.approx(0.6)
    assert rows[0]["n"] == 10 and rows[0]["expected_below_5"] == 4
    assert bh_adjust([0.01, 0.03, 0.9]) == pytest.approx([0.03, 0.045, 0.9])


def test_welch_reference_effect_and_ci() -> None:
    frame = pd.DataFrame({"outcome": [1] * 4 + [0] * 5, "measurement": [4, 5, 6, 7, 1, 2, 2, 3, 4]})
    result = welch_test(frame, "outcome", "measurement", 1, 0, 0.05, "fixture")
    reference = stats.ttest_ind([4, 5, 6, 7], [1, 2, 2, 3, 4], equal_var=False)
    assert result["statistic"] == pytest.approx(reference.statistic)
    assert result["p_value"] == pytest.approx(reference.pvalue)
    assert result["mean_difference"] == pytest.approx(3.1)
    assert result["ci_low"] < 3.1 < result["ci_high"]
    pooled = np.sqrt((3 * np.var([4, 5, 6, 7], ddof=1) + 4 * np.var([1, 2, 2, 3, 4], ddof=1)) / 7)
    expected_g = (3.1 / pooled) * (1 - 3 / (4 * 7 - 1))
    assert result["effect_size"] == pytest.approx(expected_g)


def test_welch_missing_and_ci_width() -> None:
    frame = pd.DataFrame({"y": [1, 1, 1, 0, 0, 0], "x": [4, 5, np.nan, 1, 2, 3]})
    wide = welch_test(frame, "y", "x", 1, 0, 0.01, "fixture")
    narrow = welch_test(frame, "y", "x", 1, 0, 0.10, "fixture")
    assert wide["positive_n"] == 2 and wide["negative_n"] == 3
    assert wide["ci_high"] - wide["ci_low"] > narrow["ci_high"] - narrow["ci_low"]


def test_chi_square_and_fisher_selection() -> None:
    dense = pd.DataFrame({"hypertension": [0] * 50 + [1] * 50, "stroke": [0] * 30 + [1] * 20 + [0] * 20 + [1] * 30})
    chi = hypertension_test(dense, 0.05)
    assert "chi-square" in chi["method"] and chi["minimum_expected"] >= 5
    assert chi["effect_size"] == pytest.approx(2.25)
    assert chi["ci_low"] < chi["effect_size"] < chi["ci_high"]
    sparse = pd.DataFrame({"hypertension": [0] * 9 + [1] * 3, "stroke": [0] * 8 + [1] + [0] + [1] * 2})
    fisher = hypertension_test(sparse, 0.05)
    assert "Fisher" in fisher["method"] and fisher["minimum_expected"] < 5
    assert fisher["p_value"] == pytest.approx(stats.fisher_exact([[8, 1], [1, 2]]).pvalue)


def test_synthea_patient_encounter_levels() -> None:
    patients = pd.DataFrame({"Id": ["p1", "p2"], "BIRTHDATE": ["2000-01-01", "2001-01-01"]})
    encounters = pd.DataFrame({"Id": ["e1", "e2", "e3"], "PATIENT": ["p1", "p1", "p2"], "START": ["2020-01-01T00:00:00Z"] * 3, "ENCOUNTERCLASS": ["wellness"] * 3, "REASONDESCRIPTION": [None] * 3, "REASONCODE": [None] * 3})
    _, facts = synthea_relationships(patients, encounters)
    assert facts["distinct_patients"] == 2 and facts["encounters"] == 3
    assert facts["mean_encounters_per_patient"] == 1.5 and facts["orphan_encounters"] == 0
    assert facts["valid_age_at_encounter_n"] == 3


def test_missing_prepared_file_and_invalid_schema(tmp_path) -> None:
    with pytest.raises(EDAError, match="Missing Phase I quality report"):
        load_prepared("uci_cleveland_heart", tmp_path)
    with pytest.raises(EDAError, match="Unknown dataset"):
        load_prepared("not_registered", tmp_path)


def test_prepared_checksum_and_schema_rejected(tmp_path) -> None:
    from mediscope.cli import PROJECT_ROOT
    quality_src = PROJECT_ROOT / "reports" / "quality" / "uci_cleveland_heart.json"
    data_src = PROJECT_ROOT / "data" / "processed" / "heart.csv"
    quality_dir = tmp_path / "reports" / "quality"
    data_dir = tmp_path / "data" / "processed"
    quality_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)
    quality_path = quality_dir / quality_src.name
    data_path = data_dir / data_src.name
    shutil.copyfile(quality_src, quality_path)
    shutil.copyfile(data_src, data_path)
    data_path.write_text(data_path.read_text().replace("age,sex", "wrong_age,sex", 1))
    with pytest.raises(EDAError, match="checksum mismatch"):
        load_prepared("uci_cleveland_heart", tmp_path)
    quality = json.loads(quality_path.read_text())
    quality["outputs"]["processed.cleveland.data"]["prepared_sha256"] = hashlib.sha256(data_path.read_bytes()).hexdigest()
    quality_path.write_text(json.dumps(quality))
    with pytest.raises(EDAError, match="schema or row count mismatch"):
        load_prepared("uci_cleveland_heart", tmp_path)


def test_report_reproducibility_and_phase1_immutable() -> None:
    from mediscope.cli import PROJECT_ROOT
    from mediscope.eda.runner import run_dataset
    paths = [PROJECT_ROOT / "reports" / "eda" / "uci_cleveland_heart.json", PROJECT_ROOT / "reports" / "tables" / "eda" / "uci_cleveland_heart_numeric.csv"]
    raw = PROJECT_ROOT / "data" / "raw" / "heart+disease.zip"
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths, raw]]
    run_dataset("uci_cleveland_heart")
    after = [hashlib.sha256(p.read_bytes()).hexdigest() for p in [*paths, raw]]
    assert after == before
    report = json.loads(paths[0].read_text())
    assert report["hypotheses"][0]["id"] == "H1"


def test_eda_cli_help_and_unknown(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["eda", "--dataset", "unknown"])
    assert exc.value.code == 2
