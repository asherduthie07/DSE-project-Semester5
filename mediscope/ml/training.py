"""Fold-local training, preregistered selection and untouched-holdout evaluation."""
from __future__ import annotations

import copy
import json
import platform
import resource
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
import scipy
import sklearn
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, cross_val_predict, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from ..cli import PROJECT_ROOT, sha256
from ..preparation import load_config
from ..preprocessors import build_preprocessor, feature_roles
from .evaluation import binary_metrics, choose_stroke_threshold, positive_scores
from .tasks import MLError, TASKS, cv_pairs, load_task, make_split, profile_groups

CONFIG_PATH = PROJECT_ROOT / "data" / "metadata" / "ml_experiment_config.json"
ALGORITHMS = ("logistic_regression", "decision_tree", "random_forest", "knn")


def select_by_cv(trials: dict[str, Any]) -> str:
    """Select using development scores only; test fields are deliberately ignored."""
    return min(ALGORITHMS, key=lambda algorithm: (-trials[algorithm]["cv_mean"], algorithm))


def read_protocol(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return json.loads((root / "data" / "metadata" / "ml_experiment_config.json").read_text(encoding="utf-8"))


def model_factory(name: str, seed: int) -> Any:
    return {
        "logistic_regression": lambda: LogisticRegression(solver="liblinear", max_iter=2000, random_state=seed),
        "decision_tree": lambda: DecisionTreeClassifier(random_state=seed),
        "random_forest": lambda: RandomForestClassifier(random_state=seed, n_jobs=1),
        "knn": lambda: KNeighborsClassifier(),
    }[name]()


def candidate_pipeline(dataset_id: str, algorithm: str, seed: int, root: Path = PROJECT_ROOT) -> Pipeline:
    prep = copy.deepcopy(load_config(root / "data" / "metadata" / "preparation_config.json"))
    prep["numeric_scaling"] = "standard" if algorithm in ("logistic_regression", "knn") else "none"
    prep["iqr_clip_in_training_pipeline"] = False
    return Pipeline([("preprocess", build_preprocessor(dataset_id, prep)), ("model", model_factory(algorithm, seed))])


def search_grid(algorithm: str, protocol: dict[str, Any], *, quick: bool) -> dict[str, list[Any]]:
    grid = protocol["grids"][algorithm]
    return {key: values[:1] if quick else values for key, values in grid.items()}


def _json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _cv_rows(search: GridSearchCV) -> list[dict[str, Any]]:
    results = search.cv_results_
    rows = []
    split_keys = sorted(key for key in results if key.startswith("split") and key.endswith("_test_score"))
    for index, params in enumerate(results["params"]):
        rows.append({"params": params, "mean": float(results["mean_test_score"][index]),
                     "std": float(results["std_test_score"][index]),
                     "fold_scores": [float(results[key][index]) for key in split_keys],
                     "rank": int(results["rank_test_score"][index])})
    return rows


def _reference(X: pd.DataFrame, name: str) -> dict[str, Any]:
    from ..preprocessors import MODEL_SCHEMAS
    schema = MODEL_SCHEMAS[TASKS[name].dataset_id]
    result: dict[str, Any] = {}
    for column in X.columns:
        values = X[column].dropna()
        if not len(values):
            result[column] = None
        elif column in schema.continuous:
            result[column] = float(pd.to_numeric(values).median())
        else:
            result[column] = str(values.mode().iloc[0])
    return result


def train_task(name: str, *, quick: bool = False, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Tune on development only, select by CV, then evaluate all frozen candidates once."""
    if name not in TASKS:
        raise MLError(f"Unknown task {name!r}")
    started = time.perf_counter()
    task = TASKS[name]
    protocol = read_protocol(root)
    seed = int(protocol["random_seed"])
    X, y, provenance = load_task(name, root)
    profile_audit: dict[str, int] | None = None
    if name == "diabetes":
        all_groups = profile_groups(X)
        profile_labels = pd.DataFrame({"group": all_groups, "label": y}).groupby("group")["label"].nunique()
        profile_audit = {"unique_predictor_profiles": int(len(profile_labels)),
                         "repeated_rows": int(len(X)-len(profile_labels)),
                         "conflicting_label_profiles": int((profile_labels > 1).sum())}
    split = make_split(name, X, y, folds=protocol["quick_folds"] if quick else protocol["full_folds"], seed=seed,
                       holdout_fraction=float(protocol["holdout_fraction"]))
    dev = np.asarray(split["development_indices"], dtype=int)
    held = np.asarray(split["test_indices"], dtype=int)
    X_dev, y_dev = X.iloc[dev], y.iloc[dev]
    folds = cv_pairs(split)
    mode = "quick" if quick else "full"
    report_dir = root / "reports" / "ml" / mode / name
    model_dir = root / "ml" / "models" / mode / name
    report_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    _json(report_dir / "split.json", {**split, "prepared_sha256": provenance["prepared_sha256"]})
    trials: dict[str, Any] = {}
    fitted: dict[str, Any] = {}
    thresholds: dict[str, float] = {}
    # Tuning functions receive only development rows and fold indices. The test
    # subset is not materialized until all hyperparameters and thresholds freeze.
    for algorithm in ALGORITHMS:
        pipeline = candidate_pipeline(task.dataset_id, algorithm, seed, root)
        search = GridSearchCV(pipeline, search_grid(algorithm, protocol, quick=quick), scoring=task.selection_score,
                              cv=folds, n_jobs=1, pre_dispatch=1, refit=True, error_score="raise")
        search.fit(X_dev, y_dev)
        chosen = _cv_rows(search)[int(search.best_index_)]
        thresholds[algorithm] = 0.5
        threshold_info: dict[str, Any] = {"threshold": 0.5, "method": "fixed"}
        if name == "stroke":
            oof = cross_val_predict(clone(search.best_estimator_), X_dev, y_dev, cv=folds,
                                    method="predict_proba", n_jobs=1)[:, 1]
            threshold_info = choose_stroke_threshold(y_dev, oof, protocol["thresholds"]["stroke_min_precision"])
            threshold_info["method"] = "development-only out-of-fold F2"
            thresholds[algorithm] = float(threshold_info["threshold"])
        trials[algorithm] = {"algorithm": algorithm, "search_space": search_grid(algorithm, protocol, quick=quick),
                             "best_params": search.best_params_, "cv_mean": float(search.best_score_),
                             "cv_std": chosen["std"], "cv_fold_scores": chosen["fold_scores"],
                             "cv_candidates": _cv_rows(search), "threshold_selection": threshold_info}
        fitted[algorithm] = search.best_estimator_
        print(f"{name}/{algorithm}: CV {task.selection_score}={search.best_score_:.4f}", flush=True)
    dummy = DummyClassifier(strategy="prior")
    dummy_scores = cross_val_score(dummy, X_dev, y_dev, cv=folds, scoring=task.selection_score, n_jobs=1)
    dummy.fit(X_dev, y_dev)
    trials["dummy_prior"] = {"algorithm": "dummy_prior", "best_params": {"strategy": "prior"},
                              "cv_mean": float(dummy_scores.mean()), "cv_std": float(dummy_scores.std()),
                              "cv_fold_scores": dummy_scores.tolist(), "cv_candidates": [],
                              "threshold_selection": {"threshold": 0.5, "method": "fixed baseline"}}
    fitted["dummy_prior"] = dummy
    thresholds["dummy_prior"] = 0.5
    selected = select_by_cv(trials)
    # Held-out rows and labels are accessed only after selection and all thresholds.
    X_test, y_test = X.iloc[held], y.iloc[held]
    reference = _reference(X_dev, name)
    for algorithm, estimator in fitted.items():
        score = positive_scores(estimator, X_test)
        trials[algorithm]["test"] = binary_metrics(y_test, score, thresholds[algorithm])
        path = model_dir / f"{algorithm}.joblib"
        joblib.dump(estimator, path, compress=3)
        trials[algorithm]["artifact"] = {"path": str(path.relative_to(root)), "sha256": sha256(path)}
    sensitivity: dict[str, Any] = {}
    if name == "diabetes" and not quick:
        if profile_audit and profile_audit["conflicting_label_profiles"]:
            raise MLError("Deduplicated sensitivity requires a reviewed policy for conflicting labels")
        groups = profile_groups(X_dev)
        first = np.unique(groups, return_index=True)[1]
        for algorithm in ALGORITHMS:
            estimator = candidate_pipeline(task.dataset_id, algorithm, seed, root)
            estimator.set_params(**trials[algorithm]["best_params"])
            estimator.fit(X_dev.iloc[first], y_dev.iloc[first])
            sensitivity[algorithm] = binary_metrics(y_test, positive_scores(estimator, X_test), 0.5)
        sensitivity["development_unique_profiles"] = int(len(first))
        sensitivity["development_rows_removed"] = int(len(X_dev)-len(first))
    registry_entry = {"task": name, "dataset_id": task.dataset_id, "artifact_version": protocol["artifact_version"],
                      "prepared_sha256": provenance["prepared_sha256"], "raw_sha256": provenance["raw_sha256"],
                      "feature_columns": list(X.columns), "feature_roles": feature_roles(task.dataset_id),
                      "source_target": task.target, "positive_source": task.positive_source, "positive_encoded": 1,
                      "seed": seed, "split_sha256": split["sha256"], "cv_strategy": split["method"] + f"; {len(folds)} development folds",
                      "selection_score": task.selection_score, "selected_model": selected,
                      "reference_values": reference, "training_timestamp_utc": datetime.now(timezone.utc).isoformat(),
                      "software": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__,
                                   "scipy": scipy.__version__, "scikit_learn": sklearn.__version__},
                      "mode": mode, "trials": trials, "diabetes_dedup_sensitivity": sensitivity,
                      "diabetes_profile_audit": profile_audit,
                      "elapsed_seconds": time.perf_counter()-started,
                      "maxrss_platform_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    _json(report_dir / "experiment.json", registry_entry)
    registry_file = root / "ml" / ("registry_quick.json" if quick else "registry.json")
    registry = json.loads(registry_file.read_text(encoding="utf-8")) if registry_file.is_file() else {"version": protocol["artifact_version"], "tasks": {}}
    registry["tasks"][name] = registry_entry
    _json(registry_file, registry)
    return {"task": name, "mode": mode, "selected": selected, "experiments": len(ALGORITHMS),
            "baseline": "dummy_prior", "split_sha256": split["sha256"], "elapsed_seconds": registry_entry["elapsed_seconds"]}
