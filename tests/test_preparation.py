"""Phase I behavior tests; fixtures are tiny and never treated as study data."""

from __future__ import annotations

import json
import zipfile

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from mediscope.preparation import (
    PreparationError,
    iqr_summary,
    load_config,
    prepare_table,
    read_registered_table,
)
from mediscope.preprocessors import build_preprocessor, feature_roles


@pytest.fixture
def config() -> dict[str, object]:
    return load_config()


def diabetes_rows() -> pd.DataFrame:
    return pd.DataFrame({
        "Age": [45, 45], "Gender": ["Female", "Female"],
        "Polyuria": ["Yes", "Yes"], "Polydipsia": ["No", "No"],
        "sudden weight loss": ["No", "No"], "weakness": ["No", "No"],
        "Polyphagia": ["No", "No"], "Genital thrush": ["No", "No"],
        "visual blurring": ["No", "No"], "Itching": ["No", "No"],
        "Irritability": ["No", "No"], "delayed healing": ["No", "No"],
        "partial paresis": ["No", "No"], "muscle stiffness": ["No", "No"],
        "Alopecia": ["No", "No"], "Obesity": ["No", "No"],
        "class": ["Positive", "Positive"],
    })


def heart_rows() -> pd.DataFrame:
    return pd.DataFrame({
        "age": [63, 54], "sex": ["1.0", "0.0"], "cp": ["1.0", "4.0"],
        "trestbps": [145, 130], "chol": [233, 200], "fbs": ["1.0", "0.0"],
        "restecg": ["2.0", "0.0"], "thalach": [150, 160],
        "exang": ["0.0", "1.0"], "oldpeak": [2.3, 0.0],
        "slope": ["3.0", "1.0"], "ca": [pd.NA, "0.0"],
        "thal": ["6.0", "3.0"], "num": [0, 2],
    })


def test_missing_tokens_and_missing_target_schema(tmp_path) -> None:
    archive = tmp_path / "tiny.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("table.csv", "value,target\n?,Yes\n")
    table = {"member": "table.csv", "header": True, "columns": ["value", "target"], "target": "target"}
    with zipfile.ZipFile(archive) as bundle:
        frame = read_registered_table(bundle, table, ["", "?"])
    assert pd.isna(frame.loc[0, "value"])
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("table.csv", "value,wrong\n1,Yes\n")
    with zipfile.ZipFile(archive) as bundle, pytest.raises(PreparationError, match="Required target column 'target' is missing"):
        read_registered_table(bundle, table, ["", "?"])


def test_incorrect_column_order_rejected(tmp_path) -> None:
    archive = tmp_path / "wrong.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("table.csv", "target,value\nYes,1\n")
    table = {"member": "table.csv", "header": True, "columns": ["value", "target"], "target": "target"}
    with zipfile.ZipFile(archive) as bundle, pytest.raises(PreparationError, match="Schema mismatch"):
        read_registered_table(bundle, table, ["", "?"])


def test_heart_target_preserved_and_binary_derived(config) -> None:
    result = prepare_table(heart_rows(), "uci_cleveland_heart", "processed.cleveland.data", config)
    assert result.data["num"].tolist() == [0, 2]
    assert result.data["heart_disease_binary"].tolist() == [0, 1]
    assert result.data["sex"].tolist() == ["1", "0"]
    assert result.report["initial"]["missing"]["ca"] == 1
    assert result.report["final"]["missing"]["ca"] == 1
    bad = heart_rows()
    bad.loc[0, "num"] = pd.NA
    with pytest.raises(PreparationError, match="target.*imputation is prohibited"):
        prepare_table(bad, "uci_cleveland_heart", "processed.cleveland.data", config)


def test_duplicate_retention_and_justified_removal(config) -> None:
    raw = diabetes_rows()
    retained = prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", config)
    assert len(retained.data) == 2
    assert retained.report["duplicates"]["retained"] == 1
    dropping = dict(config, exact_duplicate_policy="drop", duplicate_removal_justification="Explicit sensitivity run on identical rows")
    removed = prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", dropping)
    assert len(removed.data) == 1
    assert removed.report["duplicates"]["removed"] == 1


def test_invalid_values_are_distinct_from_missing(config) -> None:
    raw = diabetes_rows()
    raw.loc[0, "Age"] = 200
    with pytest.raises(PreparationError, match="Invalid source values"):
        prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", config)
    nullifying = dict(config, invalid_feature_policy="nullify")
    result = prepare_table(raw, "uci_early_diabetes", "diabetes_data_upload.csv", nullifying)
    assert result.report["initial"]["missing"]["Age"] == 0
    assert result.report["invalid_values"]["Age"]["count"] == 1
    assert result.report["final"]["missing"]["Age"] == 1


def test_iqr_is_descriptive_and_extremes_remain() -> None:
    frame = pd.DataFrame({"measurement": [1, 2, 3, 4, 100]})
    summary = iqr_summary(frame, ("measurement",))
    assert summary["measurement"]["count"] == 1
    assert frame.iloc[-1, 0] == 100


def test_unknown_categories_and_feature_mappings(config) -> None:
    setup = dict(config, numeric_scaling="none")
    train = pd.DataFrame({
        "age": [10.0, 20.0], "avg_glucose_level": [80.0, 100.0], "bmi": [20.0, 30.0],
        "hypertension": ["0", "1"], "heart_disease": ["0", "0"],
        "ever_married": ["No", "Yes"], "gender": ["Female", "Male"],
        "work_type": ["Private", "Private"], "Residence_type": ["Urban", "Rural"],
        "smoking_status": ["smokes", "never smoked"], "id": [1, 2], "stroke": [0, 1],
    })
    train.loc[0, "bmi"] = pd.NA
    train.loc[0, "smoking_status"] = pd.NA
    transformer = build_preprocessor("kaggle_stroke", setup)
    transformer.fit(train)
    test = train.iloc[[0]].copy()
    test.loc[test.index[0], "age"] = float("nan")
    test.loc[test.index[0], "gender"] = "unseen-category"
    test.loc[test.index[0], "hypertension"] = "unseen-binary"
    transformed = transformer.transform(test)[0]
    names = transformer.get_feature_names_out().tolist()
    assert transformed[names.index("numeric__age")] == 15.0
    assert transformed[names.index("numeric__bmi")] == 30.0
    assert transformed[names.index("binary__hypertension")] == -1
    assert all(transformed[i] == 0 for i, name in enumerate(names) if name.startswith("nominal__gender_"))
    assert feature_roles("kaggle_stroke")["binary_mappings"]["ever_married"] == {"No": 0, "Yes": 1}
    assert "id" not in names and "stroke" not in names


def test_training_only_imputation_and_iqr_fit(config) -> None:
    setup = dict(config, numeric_scaling="none", iqr_clip_in_training_pipeline=True)
    train = pd.DataFrame({
        "Age": [10.0, 20.0, 30.0, 40.0], "Gender": ["Female"] * 4,
        **{column: ["No"] * 4 for column in diabetes_rows().columns if column not in {"Age", "Gender", "class"}},
        "class": ["Negative"] * 4,
    })
    transformer = build_preprocessor("uci_early_diabetes", setup)
    transformer.fit(train)
    holdout = train.iloc[[0]].copy()
    holdout.loc[holdout.index[0], "Age"] = float("nan")
    transformed = transformer.transform(holdout)[0]
    assert transformed[0] == 25.0  # training median, unaffected by holdout
    assert transformer.named_transformers_["numeric"].named_steps["clip"].upper_[0] == 55.0
    scaled = build_preprocessor("uci_early_diabetes", dict(config, numeric_scaling="standard"))
    scaled.fit(train)
    assert scaled.named_transformers_["numeric"].named_steps["scale"].mean_[0] == 25.0


def test_nullable_source_columns_enter_unfitted_pipeline(config) -> None:
    prepared = prepare_table(heart_rows(), "uci_cleveland_heart", "processed.cleveland.data", config).data
    transformer = build_preprocessor("uci_cleveland_heart", config)
    transformed = transformer.fit_transform(prepared)
    assert transformed.shape[0] == 2
    assert transformed.shape[1] == len(transformer.get_feature_names_out())


def test_preparation_reproducibility(config) -> None:
    first = prepare_table(heart_rows(), "uci_cleveland_heart", "processed.cleveland.data", config)
    second = prepare_table(heart_rows(), "uci_cleveland_heart", "processed.cleveland.data", config)
    assert_frame_equal(first.data, second.data)
    assert json.dumps(first.report, sort_keys=True) == json.dumps(second.report, sort_keys=True)


def test_repeated_hospital_visits_are_retained(config) -> None:
    visits = pd.DataFrame({
        "Id": ["visit-1", "visit-2"],
        "START": ["2020-01-01T12:00:00Z", "2020-02-01T12:00:00Z"],
        "STOP": ["2020-01-01T13:00:00Z", "2020-02-01T13:00:00Z"],
        "PATIENT": ["same-patient", "same-patient"],
        "ORGANIZATION": ["org", "org"], "PROVIDER": ["provider", "provider"],
        "PAYER": ["payer", "payer"], "ENCOUNTERCLASS": ["outpatient", "outpatient"],
        "CODE": ["123", "123"], "DESCRIPTION": ["Visit", "Visit"],
        "BASE_ENCOUNTER_COST": [77.49, 77.49],
        "TOTAL_CLAIM_COST": [77.49, 77.49], "PAYER_COVERAGE": [0.0, 0.0],
        "REASONCODE": [pd.NA, pd.NA], "REASONDESCRIPTION": [pd.NA, pd.NA],
    })
    result = prepare_table(visits, "synthea_csv", "csv/encounters.csv", config)
    assert len(result.data) == 2
    assert result.report["duplicates"]["unique_key_repeated_rows"] == 0
    assert result.report["duplicates"]["record_key_repeated_rows"] == 0
