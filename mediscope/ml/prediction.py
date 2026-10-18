"""Validated research-only prediction from a trusted saved full pipeline."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

from ..cli import PROJECT_ROOT
from ..preparation import STRICT_POSITIVE
from ..preprocessors import MODEL_SCHEMAS
from .evaluation import positive_scores
from .explainability import local_score_changes
from .registry import load_model
from .tasks import MLError, TASKS

ALLOW_NULL = {"heart": {"ca", "thal"}, "diabetes": set(), "stroke": {"bmi", "smoking_status"}}


def validate_case(name: str, case: dict[str, Any]) -> pd.DataFrame:
    if name not in TASKS:
        raise MLError(f"Unknown prediction task {name!r}")
    schema = MODEL_SCHEMAS[TASKS[name].dataset_id]
    required = set(schema.continuous) | set(schema.binary) | set(schema.nominal) | set(schema.ordinal)
    missing = required-set(case)
    extra = set(case)-required
    if missing or extra:
        raise MLError(f"Feature schema mismatch: missing={sorted(missing)}, unexpected={sorted(extra)}")
    clean = {}
    for column, value in case.items():
        if value == "Unknown" and name == "stroke" and column == "smoking_status":
            value = None
        if value is None:
            if column not in ALLOW_NULL[name]:
                raise MLError(f"{column} is required and may not be null")
            clean[column] = None
            continue
        if column in schema.continuous:
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise MLError(f"{column} must be a finite JSON number")
            low, high = schema.numeric[column]
            if (low is not None and (value <= low if column in STRICT_POSITIVE else value < low)) or (high is not None and value > high):
                raise MLError(f"{column} violates the registered domain range")
            if column in schema.integer and not float(value).is_integer():
                raise MLError(f"{column} must be an integer")
            clean[column] = value
        else:
            if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                raise MLError(f"{column} must be a registered category")
            label = str(int(value)) if isinstance(value, (int, float)) and float(value).is_integer() else str(value)
            allowed = schema.binary.get(column) or schema.categories.get(column) or schema.ordinal.get(column)
            if allowed is None or label not in allowed:
                raise MLError(f"Unknown {column} category {label!r}; allowed={list(allowed or [])}")
            clean[column] = label
    return pd.DataFrame([{column: clean[column] for column in (list(schema.continuous)+list(schema.binary)+list(schema.nominal)+list(schema.ordinal))}])


def predict_case(name: str, case: dict[str, Any], *, root: Path = PROJECT_ROOT, quick: bool = False) -> dict[str, Any]:
    model, entry, algorithm = load_model(name, root=root, quick=quick)
    frame = validate_case(name, case)
    if list(frame.columns) != entry["feature_columns"]:
        raise MLError("Saved model feature order does not match current schema")
    score = float(positive_scores(model, frame)[0])
    threshold = float(entry["trials"][algorithm]["threshold_selection"]["threshold"])
    encoded = int(score >= threshold)
    return {"task": name, "model_name": algorithm, "model_version": entry["artifact_version"],
            "predicted_class": encoded, "predicted_source_label": entry["positive_source"] if encoded else ("Negative" if name == "diabetes" else 0),
            "estimated_model_score": score, "decision_threshold": threshold,
            "feature_summary": {key: None if pd.isna(value) else value for key, value in frame.iloc[0].to_dict().items()},
            "explanation": {"method": "one-feature-at-a-time score change versus development median/mode reference",
                            "top_changes": local_score_changes(model, frame, entry["reference_values"]),
                            "caveat": "Changes are nonadditive associations, not causes."},
            "warning": "Research and educational use only. Not a clinically validated diagnostic tool or medical advice."}
