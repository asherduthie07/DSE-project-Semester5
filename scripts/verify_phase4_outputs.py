"""Independently recompute stored holdout metrics from trusted Phase IV pipelines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mediscope.ml.evaluation import binary_metrics, positive_scores  # noqa: E402
from mediscope.ml.registry import load_model, read_registry  # noqa: E402
from mediscope.ml.tasks import TASKS, cv_pairs, load_task, profile_groups  # noqa: E402


def verify() -> dict[str, object]:
    registry = read_registry(ROOT)
    if set(registry["tasks"]) != set(TASKS):
        raise AssertionError("Registry does not contain exactly three classification tasks")
    result = {}
    for name in TASKS:
        entry = registry["tasks"][name]
        X, y, source = load_task(name, ROOT)
        if source["prepared_sha256"] != entry["prepared_sha256"]:
            raise AssertionError(f"{name}: prepared checksum changed")
        split = json.loads((ROOT / "reports" / "ml" / "full" / name / "split.json").read_text())
        dev, held = np.asarray(split["development_indices"]), np.asarray(split["test_indices"])
        if len(dev) + len(held) != len(X) or set(dev) & set(held):
            raise AssertionError(f"{name}: holdout indices invalid")
        if split["sha256"] != entry["split_sha256"]:
            raise AssertionError(f"{name}: split checksum mismatch")
        if len(cv_pairs(split)) != 5:
            raise AssertionError(f"{name}: expected five development folds")
        for train, valid in cv_pairs(split):
            if set(train) & set(valid) or set(y.iloc[dev[train]]) != {0, 1} or set(y.iloc[dev[valid]]) != {0, 1}:
                raise AssertionError(f"{name}: invalid development CV fold")
        if name == "diabetes":
            groups = profile_groups(X)
            if set(groups[dev]) & set(groups[held]):
                raise AssertionError("Diabetes profile overlap in holdout")
            for train, valid in cv_pairs(split):
                if set(groups[dev[train]]) & set(groups[dev[valid]]):
                    raise AssertionError("Diabetes profile overlap in CV")
        if len(entry["trials"]) != 5:
            raise AssertionError(f"{name}: expected four algorithms and dummy")
        verified = []
        for algorithm, trial in entry["trials"].items():
            model, _, _ = load_model(name, algorithm, root=ROOT)
            threshold = trial["threshold_selection"]["threshold"]
            actual = binary_metrics(y.iloc[held], positive_scores(model, X.iloc[held]), threshold)
            expected = trial["test"]
            for key in ("accuracy", "precision", "recall", "f1", "specificity", "balanced_accuracy",
                        "roc_auc", "average_precision", "brier"):
                if not np.isclose(actual[key], expected[key], atol=1e-10):
                    raise AssertionError(f"{name}/{algorithm}: {key} differs")
            if actual["confusion_matrix"] != expected["confusion_matrix"]:
                raise AssertionError(f"{name}/{algorithm}: confusion matrix differs")
            verified.append(algorithm)
        table = ROOT / "reports" / "tables" / "ml" / f"{name}_comparison.csv"
        if not table.is_file():
            raise AssertionError(f"{name}: comparison table missing")
        figure_dir = ROOT / "reports" / "figures" / "ml" / "full" / name
        if not figure_dir.is_dir() or len(list(figure_dir.glob("*.png"))) < 12:
            raise AssertionError(f"{name}: required comparison/explanation figures missing")
        result[name] = {"rows": len(X), "development": len(dev), "test": len(held),
                        "test_positive": int(y.iloc[held].sum()), "verified_models": verified,
                        "selected_by_cv": entry["selected_model"]}
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
