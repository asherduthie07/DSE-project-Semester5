"""Show Phase I behavior on tiny invented test-only CSV fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import KFold

from mediscope.preparation import iqr_summary, load_config, prepare_table
from mediscope.preprocessors import build_preprocessor

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures"


def read_fixture(name: str) -> pd.DataFrame:
    return pd.read_csv(FIXTURES / name, dtype="string", keep_default_na=False, na_values=["", "?"])


def main() -> None:
    config = load_config()
    diabetes = read_fixture("diabetes_controlled.csv")
    valid_diabetes = prepare_table(diabetes.iloc[:3], "uci_early_diabetes", "diabetes_data_upload.csv", config)
    all_diabetes = prepare_table(diabetes, "uci_early_diabetes", "diabetes_data_upload.csv", dict(config, invalid_feature_policy="nullify"))
    encounters = prepare_table(read_fixture("hospital_encounters_controlled.csv").iloc[:2], "synthea_csv", "csv/encounters.csv", config)
    training = prepare_table(read_fixture("stroke_train_controlled.csv"), "kaggle_stroke", "healthcare-dataset-stroke-data.csv", config).data
    holdout = read_fixture("stroke_holdout_controlled.csv")
    transformer = build_preprocessor("kaggle_stroke", config).fit(training)
    names = transformer.get_feature_names_out().tolist()
    transformed = transformer.transform(holdout)
    fold_means = []
    for train_index, _ in KFold(n_splits=3, shuffle=False).split(training):
        fold_transformer = build_preprocessor("kaggle_stroke", config).fit(training.iloc[train_index])
        fold_means.append(float(fold_transformer.named_transformers_["numeric"].named_steps["scale"].mean_[0]))
    result = {
        "warning": "Invented test fixtures only; never use these counts as research data.",
        "missing_tokens": {"source_missing_age": all_diabetes.report["initial"]["missing"]["Age"], "final_missing_age_after_nullify": all_diabetes.report["final"]["missing"]["Age"]},
        "duplicates": {"exact_found": valid_diabetes.report["duplicates"]["exact_before"], "rows_retained": len(valid_diabetes.data)},
        "valid_extreme_age_retained": 119 in valid_diabetes.data["Age"].tolist(),
        "invalid_values": {"age_200": all_diabetes.report["invalid_values"]["Age"]["count"], "unknown_polyuria": all_diabetes.report["invalid_values"]["Polyuria"]["count"]},
        "iqr": {"values": [1, 2, 3, 4, 100], "outliers": iqr_summary(pd.DataFrame({"measurement": [1, 2, 3, 4, 100]}), ("measurement",))["measurement"]["count"]},
        "hospital_visits": {"rows_retained": len(encounters.data), "unique_patients": int(encounters.data["PATIENT"].nunique()), "unique_visits": int(encounters.data["Id"].nunique())},
        "training_only_preprocessing": {
            "bmi_imputation_median": float(transformer.named_transformers_["numeric"].named_steps["impute"].statistics_[2]),
            "age_scaler_mean": float(transformer.named_transformers_["numeric"].named_steps["scale"].mean_[0]),
            "unseen_binary_code": float(transformed[0, names.index("binary__hypertension")]),
            "unseen_gender_onehot_values": [float(transformed[0, index]) for index, name in enumerate(names) if name.startswith("nominal__gender_")],
            "cross_validation_fold_age_means": fold_means,
        },
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
