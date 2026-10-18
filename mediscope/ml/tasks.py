"""Checksum-verified classification tasks and immutable split definitions."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, train_test_split

from ..cli import PROJECT_ROOT
from ..eda.runner import load_prepared
from ..preprocessors import MODEL_SCHEMAS


@dataclass(frozen=True)
class Task:
    name: str
    dataset_id: str
    target: str
    positive_source: str | int
    filename: str
    selection_score: str


TASKS = {
    "heart": Task("heart", "uci_cleveland_heart", "heart_disease_binary", 1, "heart.csv", "f1"),
    "diabetes": Task("diabetes", "uci_early_diabetes", "class", "Positive", "diabetes.csv", "balanced_accuracy"),
    "stroke": Task("stroke", "kaggle_stroke", "stroke", 1, "stroke.csv", "average_precision"),
}


class MLError(ValueError):
    """Invalid task, schema, split, model artifact, or research input."""


def predictors(task: Task) -> list[str]:
    schema = MODEL_SCHEMAS[task.dataset_id]
    columns = list(schema.continuous) + list(schema.binary) + list(schema.nominal) + list(schema.ordinal)
    if set(columns).intersection(schema.excluded_from_model) or task.target in columns:
        raise MLError("Outcome or excluded field appears in predictors")
    return columns


def load_task(name: str, root: Path = PROJECT_ROOT) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    """Reuse Phase I/II checksum, target and schema validation."""
    if name not in TASKS:
        raise MLError(f"Unknown ML dataset {name!r}; choose {list(TASKS)}")
    task = TASKS[name]
    frames, quality, _ = load_prepared(task.dataset_id, root)
    frame = next(iter(frames.values()))
    features = predictors(task)
    if not set(features).issubset(frame.columns) or task.target not in frame:
        raise MLError(f"Prepared {name} schema is missing required predictive fields")
    X = frame.loc[:, features].copy()
    source_target = frame[task.target]
    allowed = {task.positive_source, "Negative" if name == "diabetes" else 0}
    if source_target.isna().any() or not set(source_target.unique()).issubset(allowed):
        raise MLError(f"{name} target contains null or unknown source labels")
    y = (source_target == task.positive_source).astype(int)
    if set(y.unique()) != {0, 1}:
        raise MLError(f"{name} target must contain both classes without nulls")
    member = next(iter(quality["outputs"]))
    provenance = {"prepared_sha256": quality["outputs"][member]["prepared_sha256"],
                  "raw_sha256": quality["source"]["sha256"], "rows": len(frame), "features": features,
                  "source_target": task.target, "positive_source": task.positive_source}
    return X, y, provenance


def profile_groups(X: pd.DataFrame) -> np.ndarray:
    """Assign one group to every identical raw predictor tuple, never using y."""
    def key(row: tuple[Any, ...]) -> tuple[str, ...]:
        return tuple("<MISSING>" if pd.isna(value) else str(value) for value in row)
    ids: dict[tuple[str, ...], int] = {}
    return np.asarray([ids.setdefault(key(row), len(ids)) for row in X.itertuples(index=False, name=None)], dtype=int)


def make_split(name: str, X: pd.DataFrame, y: pd.Series, *, folds: int = 5, seed: int = 42,
               holdout_fraction: float = 0.2) -> dict[str, Any]:
    """Create one untouched holdout and fixed, shared development CV folds."""
    if not 0 < holdout_fraction < 1:
        raise MLError("Holdout fraction must be between zero and one")
    indices = np.arange(len(y))
    if name == "diabetes":
        outer_folds = round(1 / holdout_fraction)
        if outer_folds < 2 or not np.isclose(1 / outer_folds, holdout_fraction):
            raise MLError("Diabetes holdout fraction must be the reciprocal of an integer >= 2")
        groups = profile_groups(X)
        splitter = StratifiedGroupKFold(n_splits=outer_folds, shuffle=True, random_state=seed)
        dev_idx, test_idx = next(splitter.split(X, y, groups))
        dev_groups = groups[dev_idx]
        if set(dev_groups).intersection(groups[test_idx]):
            raise MLError("Diabetes profile overlap across holdout boundary")
        inner = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
        cv = list(inner.split(X.iloc[dev_idx], y.iloc[dev_idx], dev_groups))
    else:
        groups = None
        dev_idx, test_idx = train_test_split(indices, test_size=holdout_fraction, stratify=y, random_state=seed)
        inner = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
        cv = list(inner.split(X.iloc[dev_idx], y.iloc[dev_idx]))
    for train, validation in cv:
        if set(y.iloc[dev_idx[train]]) != {0, 1} or set(y.iloc[dev_idx[validation]]) != {0, 1}:
            raise MLError("A CV fold lacks one outcome class")
        if groups is not None and set(groups[dev_idx[train]]).intersection(groups[dev_idx[validation]]):
            raise MLError("Diabetes profile overlap in CV")
    if set(y.iloc[dev_idx]) != {0, 1} or set(y.iloc[test_idx]) != {0, 1}:
        raise MLError("Holdout lacks one outcome class")
    split = {"seed": seed, "method": "StratifiedGroupKFold fold 0" if name == "diabetes" else "stratified train_test_split",
             "development_indices": dev_idx.tolist(), "test_indices": test_idx.tolist(),
             "cv_folds": [{"train": tr.tolist(), "validation": va.tolist()} for tr, va in cv],
             "development_counts": {str(c): int((y.iloc[dev_idx] == c).sum()) for c in (0, 1)},
             "test_counts": {str(c): int((y.iloc[test_idx] == c).sum()) for c in (0, 1)},
             "profile_count": int(len(set(groups))) if groups is not None else None,
             "profile_overlap": 0 if groups is not None else None}
    canonical = json.dumps(split, sort_keys=True, separators=(",", ":")).encode()
    split["sha256"] = hashlib.sha256(canonical).hexdigest()
    return split


def cv_pairs(split: dict[str, Any]) -> list[tuple[np.ndarray, np.ndarray]]:
    return [(np.asarray(fold["train"], dtype=int), np.asarray(fold["validation"], dtype=int)) for fold in split["cv_folds"]]
