"""Binary classification metrics and development-only threshold selection."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, confusion_matrix, f1_score, precision_recall_curve, precision_score,
    recall_score, roc_auc_score, roc_curve)


def positive_scores(pipeline: Any, X: Any) -> np.ndarray:
    classes = list(pipeline.classes_)
    return np.asarray(pipeline.predict_proba(X)[:, classes.index(1)], dtype=float)


def binary_metrics(y_true: Any, score: Any, threshold: float = 0.5) -> dict[str, Any]:
    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(score, dtype=float)
    if (len(truth) != len(scores) or not np.isfinite(scores).all()
            or not np.isin(truth, [0, 1]).all() or not ((0 <= scores) & (scores <= 1)).all()
            or not 0 <= threshold <= 1):
        raise ValueError("Invalid score vector or decision threshold")
    pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(truth, pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if tn + fp else None
    if len(set(truth)) == 2:
        roc_auc = float(roc_auc_score(truth, scores))
        ap = float(average_precision_score(truth, scores))
        brier = float(brier_score_loss(truth, scores))
        frac, mean = calibration_curve(truth, scores, n_bins=5, strategy="quantile")
        fpr, tpr, roc_thresholds = roc_curve(truth, scores)
        pr_precision, pr_recall, pr_thresholds = precision_recall_curve(truth, scores)
    else:
        roc_auc = ap = brier = None
        frac = mean = fpr = tpr = roc_thresholds = pr_precision = pr_recall = pr_thresholds = []
    return {"n": len(truth), "positive_n": int(truth.sum()), "negative_n": int(len(truth)-truth.sum()),
            "threshold": float(threshold), "accuracy": float(accuracy_score(truth, pred)),
            "precision": float(precision_score(truth, pred, zero_division=0)),
            "recall": float(recall_score(truth, pred, zero_division=0)),
            "f1": float(f1_score(truth, pred, zero_division=0)),
            "specificity": float(specificity) if specificity is not None else None,
            "balanced_accuracy": float(balanced_accuracy_score(truth, pred)) if len(set(truth)) == 2 else None,
            "roc_auc": roc_auc, "average_precision": ap, "brier": brier,
            "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]], "false_positive": int(fp), "false_negative": int(fn),
            "calibration": {"mean_predicted": np.asarray(mean).tolist(), "fraction_positive": np.asarray(frac).tolist()},
            "roc_curve": {"fpr": np.asarray(fpr).tolist(), "tpr": np.asarray(tpr).tolist()},
            "precision_recall_curve": {"precision": np.asarray(pr_precision).tolist(), "recall": np.asarray(pr_recall).tolist()},
            "undefined_metrics": [] if len(set(truth)) == 2 else ["roc_auc", "average_precision", "brier", "balanced_accuracy"]}


def choose_stroke_threshold(y: Any, score: Any, min_precision: float = 0.15) -> dict[str, Any]:
    """Select development-OOF threshold by F2 under a precision floor."""
    precision, recall, thresholds = precision_recall_curve(y, score)
    candidates = []
    for threshold, p, r in zip(thresholds, precision[:-1], recall[:-1]):
        if p >= min_precision:
            f2 = 5 * p * r / (4 * p + r) if 4 * p + r else 0.0
            candidates.append((float(f2), float(p), float(r), float(threshold)))
    if not candidates:
        return {"threshold": 0.5, "fallback": "No OOF threshold met minimum precision", "min_precision": min_precision}
    f2, p, r, threshold = max(candidates, key=lambda row: (row[0], row[1], row[3]))
    return {"threshold": threshold, "oof_f2": f2, "oof_precision": p, "oof_recall": r,
            "min_precision": min_precision, "fallback": None}
