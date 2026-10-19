"""Read Phase IV registry and use trusted, preloaded selected pipelines."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.errors import APIError, missing, unavailable
from backend.app.core.json_safe import clean
from mediscope.ml.evaluation import positive_scores
from mediscope.ml.explainability import local_score_changes
from mediscope.ml.prediction import ALLOW_NULL, validate_case
from mediscope.ml.registry import load_model, read_registry
from mediscope.ml.tasks import MLError, TASKS
from mediscope.preprocessors import MODEL_SCHEMAS
from mediscope.preparation import STRICT_POSITIVE

logger = logging.getLogger("mediscope.api.models")
WARNING = "Research and educational use only. Not a clinically validated diagnostic tool or medical advice."


class ModelService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.registry: dict[str, Any] = {}
        self.loaded: dict[str, Any] = {}
        self.load_errors: set[str] = set()

    def initialize(self) -> None:
        try:
            self.registry = read_registry(self.root)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            logger.warning("Trusted model registry unavailable: %s", type(exc).__name__)
            self.registry = {}
            self.load_errors = set(TASKS)
            return
        for task in TASKS:
            try:
                model, entry, algorithm = load_model(task, root=self.root)
                self.loaded[task] = (model, entry, algorithm)
            except (OSError, ValueError, KeyError, TypeError) as exc:
                logger.warning("Selected %s model unavailable: %s", task, type(exc).__name__)
                self.load_errors.add(task)

    def _entry(self, task: str) -> dict[str, Any]:
        if task not in TASKS:
            raise missing("model task")
        try:
            return self.registry["tasks"][task]
        except (KeyError, TypeError) as exc:
            raise unavailable("Model registry") from exc

    def listing(self) -> dict[str, Any]:
        return {"tasks": [{"task": task, "selected_model": self._entry(task)["selected_model"],
                           "artifact_version": self._entry(task)["artifact_version"],
                           "available_for_prediction": task in self.loaded} for task in TASKS],
                "warning": WARNING}

    def detail(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        return {"task": task, "selected_model": e["selected_model"], "artifact_version": e["artifact_version"],
                "artifact_sha256": e["trials"][e["selected_model"]]["artifact"]["sha256"],
                "dataset_id": e["dataset_id"], "feature_columns": e["feature_columns"],
                "cv_strategy": e["cv_strategy"], "selection_score": e["selection_score"],
                "selection_reason": "Highest registered development cross-validation selection score; holdout was not used to select the model.",
                "split_sha256": e["split_sha256"], "prepared_sha256": e["prepared_sha256"],
                "available_for_prediction": task in self.loaded, "warning": WARNING}

    def comparison(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        trials = []
        for name, t in e["trials"].items():
            trials.append(clean({"algorithm": name, "best_params": t["best_params"], "cv_mean": t["cv_mean"],
                                 "cv_std": t["cv_std"], "cv_fold_scores": t["cv_fold_scores"],
                                 "test_metrics": {k: v for k, v in t["test"].items() if k not in {"roc_curve", "precision_recall_curve", "calibration"}},
                                 "decision_threshold": t["threshold_selection"]["threshold"],
                                 "selected": name == e["selected_model"]}))
        return {"task": task, "cv_strategy": e["cv_strategy"], "selection_score": e["selection_score"],
                "selected_model": e["selected_model"], "trials": trials, "warning": WARNING}

    def matrices(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        return {"task": task, "matrices": {name: {"matrix": t["test"]["confusion_matrix"],
                "test_n": t["test"]["n"], "positive_n": t["test"]["positive_n"], "negative_n": t["test"]["negative_n"]}
                for name, t in e["trials"].items()}, "warning": WARNING}

    def curves(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        return clean({"task": task, "curves": {name: {"roc": t["test"].get("roc_curve"),
                      "precision_recall": t["test"].get("precision_recall_curve"),
                      "roc_auc": t["test"].get("roc_auc"), "average_precision": t["test"].get("average_precision")}
                      for name, t in e["trials"].items()}, "warning": WARNING})

    def explanations(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        path = self.root / "reports/ml/full" / task / f"explanations_{e['selected_model']}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["task"] != task or data["algorithm"] != e["selected_model"]:
                raise ValueError("explanation identity mismatch")
        except (OSError, ValueError, KeyError) as exc:
            raise unavailable("Model explanation") from exc
        data.pop("local_development_example", None)
        return clean({"task": task, "selected_model": e["selected_model"], "explanation": data,
                      "warning": WARNING})

    def input_schema(self, task: str) -> dict[str, Any]:
        e = self._entry(task)
        schema = MODEL_SCHEMAS[TASKS[task].dataset_id]
        fields = []
        for name in e["feature_columns"]:
            if name in schema.continuous:
                low, high = schema.numeric[name]
                fields.append({"name": name, "type": "number", "integer": name in schema.integer,
                               "minimum": low, "maximum": high, "exclusive_minimum": name in STRICT_POSITIVE,
                               "nullable": name in ALLOW_NULL[task]})
            else:
                allowed = schema.binary.get(name) or schema.categories.get(name) or schema.ordinal.get(name)
                fields.append({"name": name, "type": "category", "allowed": list(allowed or ()),
                               "nullable": name in ALLOW_NULL[task]})
        return {"task": task, "features": fields, "artifact_version": e["artifact_version"],
                "selected_model": e["selected_model"], "warning": WARNING}

    def predict(self, task: str, features: dict[str, Any]) -> dict[str, Any]:
        self._entry(task)
        if task not in self.loaded:
            raise unavailable("Selected model")
        model, entry, algorithm = self.loaded[task]
        try:
            frame = validate_case(task, features)
            if list(frame.columns) != entry["feature_columns"]:
                raise MLError("Feature order differs from saved pipeline")
            score = float(positive_scores(model, frame)[0])
            threshold = float(entry["trials"][algorithm]["threshold_selection"]["threshold"])
            encoded = int(score >= threshold)
            explanation = {"method": "one-feature-at-a-time score change versus development median/mode reference",
                           "top_changes": local_score_changes(model, frame, entry["reference_values"]),
                           "caveat": "Changes are nonadditive associations, not causes."}
        except MLError as exc:
            raise APIError(422, "INVALID_FEATURES", "Invalid prediction features; consult the task schema.") from exc
        except (ValueError, KeyError, TypeError) as exc:
            raise unavailable("Selected model") from exc
        return clean({"task": task, "model_name": algorithm, "model_version": entry["artifact_version"],
                      "model_sha256": entry["trials"][algorithm]["artifact"]["sha256"],
                      "predicted_class": encoded,
                      "predicted_source_label": entry["positive_source"] if encoded else ("Negative" if task == "diabetes" else 0),
                      "estimated_model_score": score, "decision_threshold": threshold,
                      "explanation": explanation, "warning": WARNING})
