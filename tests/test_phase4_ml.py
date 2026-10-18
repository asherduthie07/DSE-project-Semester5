"""Controlled Phase IV fixtures; no research metric is derived from these rows."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV

from mediscope.ml.evaluation import binary_metrics, choose_stroke_threshold, positive_scores
from mediscope.ml.explainability import local_score_changes
from mediscope.ml.prediction import validate_case
from mediscope.ml.registry import load_model, read_registry
from mediscope.ml.tasks import TASKS, cv_pairs, load_task, make_split, predictors, profile_groups
from mediscope.ml.training import ALGORITHMS, candidate_pipeline, read_protocol, search_grid, select_by_cv
from mediscope.preprocessors import build_preprocessor

ROOT = Path(__file__).resolve().parents[1]


def test_task_targets_and_excluded_predictors() -> None:
    assert TASKS["heart"].target == "heart_disease_binary"
    assert TASKS["diabetes"].positive_source == "Positive"
    assert TASKS["stroke"].positive_source == 1
    assert not {"num", "heart_disease_binary"}.intersection(predictors(TASKS["heart"]))
    assert "id" not in predictors(TASKS["stroke"])


def test_profile_groups_use_predictors_and_keep_repeats_together() -> None:
    X = pd.DataFrame({"Age": [40, 40, 60, 60, 30, 30], "Polyuria": ["Yes", "Yes", "No", "No", "Yes", "Yes"]})
    groups = profile_groups(X)
    assert groups.tolist() == [0, 0, 1, 1, 2, 2]
    # Even conflicting labels do not change the predictor-defined grouping.
    labels = pd.Series([0, 1, 0, 0, 1, 1])
    assert profile_groups(X).tolist() == groups.tolist()
    assert labels.iloc[0] != labels.iloc[1]


def test_diabetes_holdout_and_cv_group_isolation_reproducible() -> None:
    # 50 distinct profiles, each repeated twice, with balanced labels.
    X = pd.DataFrame({"Age": np.repeat(np.arange(20, 70), 2), "Polyuria": np.repeat(["Yes", "No"] * 25, 2)})
    y = pd.Series(np.repeat([0, 1] * 25, 2))
    first = make_split("diabetes", X, y, folds=3)
    assert first == make_split("diabetes", X, y, folds=3)
    groups = profile_groups(X)
    dev, held = first["development_indices"], first["test_indices"]
    assert not set(groups[dev]) & set(groups[held])
    assert not set(dev) & set(held)
    for train, valid in cv_pairs(first):
        assert not set(groups[np.asarray(dev)[train]]) & set(groups[np.asarray(dev)[valid]])


def test_stratified_split_reproducible_and_balanced() -> None:
    X = pd.DataFrame({"x": np.arange(100)})
    y = pd.Series([0, 1] * 50)
    for task in ("heart", "stroke"):
        split = make_split(task, X, y, folds=5)
        assert split == make_split(task, X, y, folds=5)
        assert split["development_counts"] == {"0": 40, "1": 40}
        assert split["test_counts"] == {"0": 10, "1": 10}


def test_fold_local_imputation_scaling_and_encoding() -> None:
    protocol = read_protocol(ROOT)
    X = pd.DataFrame({
        "age": [40, 50, 60, 999], "trestbps": [120, 130, 140, 150],
        "chol": [200, 210, 220, 230], "thalach": [150, 160, 170, 180],
        "oldpeak": [0.0, 1.0, 2.0, 3.0], "sex": [0, 1, 0, 1],
        "fbs": [0, 1, 0, 1], "exang": [0, 1, 0, 1],
        "cp": ["1", "2", "1", "unseen"], "restecg": ["0", "1", "0", "2"],
        "slope": ["1", "2", "1", "3"], "ca": ["0", None, "1", "2"],
        "thal": ["3", "6", "3", "7"],
    })
    pipeline = candidate_pipeline(TASKS["heart"].dataset_id, "logistic_regression", 42, ROOT)
    y = pd.Series([0, 1, 0, 1])
    first = clone(pipeline).fit(X.iloc[:3], y.iloc[:3])
    changed = X.copy()
    changed.loc[3, "age"] = 1_000_000
    changed.loc[3, "cp"] = "another unseen"
    second = clone(pipeline).fit(changed.iloc[:3], y.iloc[:3])
    a = first.named_steps["preprocess"]
    b = second.named_steps["preprocess"]
    np.testing.assert_allclose(a.named_transformers_["numeric"].named_steps["scale"].mean_,
                               b.named_transformers_["numeric"].named_steps["scale"].mean_)
    assert list(a.get_feature_names_out()) == list(b.get_feature_names_out())
    assert "nominal__cp_unseen" not in a.get_feature_names_out()
    assert a.transform(X.iloc[[3]]).shape[1] == a.transform(changed.iloc[[3]]).shape[1]
    # Numeric source codes must encode to registered 0/1, never unknown -1.
    assert set(a.transform(X.iloc[:3])[:, 5].tolist()) == {0.0, 1.0}
    assert protocol["resource_policy"]["search_n_jobs"] == 1


def test_no_resampling_or_data_preparation_outside_pipeline() -> None:
    for algorithm in ALGORITHMS:
        pipe = candidate_pipeline(TASKS["stroke"].dataset_id, algorithm, 42, ROOT)
        assert [step for step, _ in pipe.steps] == ["preprocess", "model"]
        assert pipe.named_steps["preprocess"].transformers[0][1].steps[1][0] == "impute"


def test_known_metrics_confusion_and_threshold() -> None:
    result = binary_metrics([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9])
    assert result["confusion_matrix"] == [[1, 1], [1, 1]]
    assert result["accuracy"] == result["precision"] == result["recall"] == result["f1"] == 0.5
    assert result["specificity"] == result["balanced_accuracy"] == 0.5
    assert result["false_positive"] == result["false_negative"] == 1
    assert binary_metrics([0, 1], [0.4, 0.6], 0.7)["recall"] == 0
    with pytest.raises(ValueError):
        binary_metrics([0, 1], [0.2, 1.2])


def test_threshold_is_selected_from_supplied_development_scores() -> None:
    y = [0, 0, 0, 1, 1]
    scores = [0.1, 0.2, 0.3, 0.7, 0.9]
    chosen = choose_stroke_threshold(y, scores, min_precision=0.5)
    assert chosen["threshold"] == pytest.approx(0.7)
    assert chosen["oof_recall"] == 1


def test_model_selection_never_reads_test_fields() -> None:
    trials = {key: {"cv_mean": float(i), "test": {"accuracy": 1.0 - i / 10}}
              for i, key in enumerate(ALGORITHMS)}
    winner = select_by_cv(trials)
    assert winner == ALGORITHMS[-1]
    for trial in trials.values():
        trial["test"] = {"accuracy": 0}
    assert select_by_cv(trials) == winner


def test_hyperparameter_search_on_small_fixture_and_save_reload(tmp_path: Path) -> None:
    example = json.loads((ROOT / "examples" / "diabetes_case.json").read_text())
    rows = []
    labels = []
    for index in range(24):
        row = example.copy()
        row["Age"] = 25 + index
        row["Polyuria"] = "Yes" if index % 2 else "No"
        rows.append(row)
        labels.append(index % 2)
    X, y = pd.DataFrame(rows), pd.Series(labels)
    split = make_split("heart", X, y, folds=3)
    dev = split["development_indices"]
    search = GridSearchCV(candidate_pipeline(TASKS["diabetes"].dataset_id, "logistic_regression", 42, ROOT),
                          search_grid("logistic_regression", read_protocol(ROOT), quick=True),
                          cv=cv_pairs(split), scoring="f1", n_jobs=1, error_score="raise")
    search.fit(X.iloc[dev], y.iloc[dev])
    assert search.best_estimator_.named_steps["preprocess"].transform(X.iloc[dev]).shape[0] == len(dev)
    path = tmp_path / "controlled.joblib"
    joblib.dump(search.best_estimator_, path)
    restored = joblib.load(path)
    np.testing.assert_allclose(positive_scores(search.best_estimator_, X.iloc[:3]), positive_scores(restored, X.iloc[:3]))
    assert local_score_changes(restored, X.iloc[[0]], {key: value for key, value in example.items()})


def test_prediction_schema_validation_and_unknown_categories() -> None:
    for task in ("heart", "diabetes", "stroke"):
        case = json.loads((ROOT / "examples" / f"{task}_case.json").read_text())
        assert len(validate_case(task, case)) == 1
        bad = case.copy()
        bad.pop(next(iter(bad)))
        with pytest.raises(ValueError, match="schema mismatch"):
            validate_case(task, bad)
        bad = case.copy()
        bad[next(iter(bad))] = -999
        with pytest.raises(ValueError):
            validate_case(task, bad)
    stroke = json.loads((ROOT / "examples" / "stroke_case.json").read_text())
    stroke["smoking_status"] = "Unknown"
    assert pd.isna(validate_case("stroke", stroke)["smoking_status"].iloc[0])
    stroke["smoking_status"] = "unregistered"
    with pytest.raises(ValueError, match="Unknown"):
        validate_case("stroke", stroke)


def test_preprocessor_factory_is_unfitted() -> None:
    config = json.loads((ROOT / "data" / "metadata" / "preparation_config.json").read_text())
    transformer = build_preprocessor(TASKS["stroke"].dataset_id, config)
    assert not hasattr(transformer, "transformers_")


def test_missing_prepared_dataset_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises((ValueError, FileNotFoundError), match="[Mm]issing|[Nn]ot found|[Nn]o such|[Rr]eport"):
        load_task("heart", tmp_path)


def test_registry_rejects_missing_and_escaped_artifacts(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="registry missing"):
        read_registry(tmp_path)
    registry = {"tasks": {"heart": {"selected_model": "logistic_regression", "trials": {
        "logistic_regression": {"artifact": {"path": "../../outside.joblib", "sha256": "0" * 64}}
    }}}}
    (tmp_path / "ml").mkdir()
    (tmp_path / "ml" / "registry.json").write_text(json.dumps(registry))
    with pytest.raises(ValueError, match="escapes trusted"):
        load_model("heart", root=tmp_path)


def test_inner_cv_preprocessing_ignores_validation_extreme() -> None:
    example = json.loads((ROOT / "examples" / "diabetes_case.json").read_text())
    rows = []
    for index in range(30):
        row = example.copy()
        row["Age"] = 20 + index
        rows.append(row)
    X = pd.DataFrame(rows)
    y = pd.Series([0, 1] * 15)
    split = make_split("heart", X, y, folds=3)
    dev = np.asarray(split["development_indices"])
    train, valid = cv_pairs(split)[0]
    base = candidate_pipeline(TASKS["diabetes"].dataset_id, "logistic_regression", 42, ROOT)
    fitted = clone(base).fit(X.iloc[dev[train]], y.iloc[dev[train]])
    changed = X.copy()
    changed.loc[dev[valid], "Age"] = 9999
    fitted_changed = clone(base).fit(changed.iloc[dev[train]], y.iloc[dev[train]])
    a = fitted.named_steps["preprocess"].named_transformers_["numeric"].named_steps["scale"].mean_
    b = fitted_changed.named_steps["preprocess"].named_transformers_["numeric"].named_steps["scale"].mean_
    np.testing.assert_allclose(a, b)
