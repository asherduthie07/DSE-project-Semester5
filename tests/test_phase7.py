"""Phase VII split, pipeline, metric and saved-artifact regression checks."""
from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from backend.app.main import create_app
from mediscope.cli import PROJECT_ROOT
from mediscope.ml.phase7 import measure, pipeline, read_saved_split, strategy_frame, wilson
from mediscope.ml.tasks import load_task, profile_groups
from mediscope.preprocessors import IQRClipper


def test_saved_development_folds_remain_group_disjoint():
    for task in ("heart", "diabetes", "stroke"):
        X, y, provenance = load_task(task)
        split = read_saved_split(PROJECT_ROOT, task, X, y, provenance["prepared_sha256"])
        dev, held = split["development_indices"], split["test_indices"]
        assert not set(dev) & set(held)
        assert len(split["cv_folds"]) == 5
        if task == "diabetes":
            groups = profile_groups(X)
            assert not set(groups[dev]) & set(groups[held])
            for fold in split["cv_folds"]:
                assert not set(groups[np.asarray(dev)[fold["train"]]]) & set(groups[np.asarray(dev)[fold["validation"]]])


def test_preprocessing_fits_on_training_only_and_smoking_policy():
    X, y, provenance = load_task("stroke")
    split = read_saved_split(PROJECT_ROOT, "stroke", X, y, provenance["prepared_sha256"])
    dev = np.asarray(split["development_indices"])
    fold = split["cv_folds"][0]
    train, valid = dev[fold["train"]], dev[fold["validation"]]
    params = json.loads((PROJECT_ROOT/"ml/registry.json").read_text())["tasks"]["stroke"]["trials"]["logistic_regression"]["best_params"]
    model = pipeline(PROJECT_ROOT, "stroke", "logistic_regression", params, "baseline").fit(X.iloc[train],y.iloc[train])
    before = model.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"].statistics_.copy()
    changed = X.iloc[valid].copy(); changed.loc[:, "age"] = 120
    model.predict_proba(changed)
    after = model.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"].statistics_
    np.testing.assert_array_equal(before, after)
    assert strategy_frame(X.iloc[valid], "stroke", "smoking_explicit")["smoking_status"].isna().sum() == 0
    assert X.iloc[valid]["smoking_status"].isna().sum() > 0


def test_metrics_intervals_and_duplicate_policy():
    result = measure(np.array([0,0,1,1]),np.array([.1,.8,.2,.9]),.5)
    assert (result["false_positive"],result["false_negative"]) == (1,1)
    assert result["f1"] == .5 and result["brier"] > 0
    assert wilson(0,0) is None
    assert 0 < wilson(1,2)[0] < .5 < wilson(1,2)[1] < 1
    X, _, _ = load_task("diabetes")
    assert len(np.unique(profile_groups(X))) == 251


def test_iqr_policy_is_fitted_only_on_training_values():
    clipper = IQRClipper().fit(np.array([[1.], [2.], [3.], [4.], [5.]]))
    before = clipper.upper_.copy()
    transformed = clipper.transform(np.array([[1000.]]))
    np.testing.assert_array_equal(before, clipper.upper_)
    assert transformed[0, 0] == before[0]


def test_outputs_and_api_are_checksum_verified():
    manifest = json.loads((PROJECT_ROOT/"reports/phase7/manifest.json").read_text())
    for relative, digest in manifest["artifacts"].items():
        assert hashlib.sha256((PROJECT_ROOT/relative).read_bytes()).hexdigest() == digest
    with TestClient(create_app()) as client:
        overview = client.get("/api/v1/research-lab")
        assert overview.status_code == 200
        assert len(overview.json()["tasks"]) == 3
        for task in ("heart", "diabetes", "stroke"):
            response = client.get(f"/api/v1/research-lab/{task}")
            assert response.status_code == 200
            data = response.json()
            assert data["split_sha256"] == manifest["phase4_split_sha256"][task]
            assert len(data["calibration"]) > 0 and len(data["subgroups"]) > 0
            assert all(row["n"] == row["positive_n"]+row["negative_n"] for row in data["subgroups"])
            baseline = data["comparisons"][0]
            assert baseline["strategy"] == "baseline"
            assert baseline["preprocessing_config"]["numeric_imputation"] == "median"
            assert baseline["model_params"]
            assert len(baseline["folds"]) == 5
            assert sum(row["n"] for row in baseline["folds"]) == data["development_n"]
            bins = [row for row in data["calibration"] if row["strategy"] == "baseline"]
            assert sum(row["n"] for row in bins) == data["development_n"]
            assert np.isclose(sum(row["n"]*row["observed_rate"] for row in bins), data["development_positive_n"])
            thresholds = data["threshold_sensitivity"]
            assert all(a["false_positive"] >= b["false_positive"] for a,b in zip(thresholds,thresholds[1:]))
            assert all(-1 <= row["spearman_to_selected_baseline"] <= 1 for row in data["importance_rank_comparisons"] if row["spearman_to_selected_baseline"] is not None)
            assert all(len(row["f1_ci95_bootstrap"]) == 2 for row in data["subgroups"])
        assert client.get("/api/v1/research-lab/exports/comparisons.csv").status_code == 200
        assert client.get("/api/v1/research-lab/unknown").status_code == 404
