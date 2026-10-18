"""Development-only global explanations and noncausal local score changes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.tree import DecisionTreeClassifier, plot_tree

from ..cli import PROJECT_ROOT
from .evaluation import positive_scores
from .registry import load_model
from .tasks import TASKS, cv_pairs, load_task


def local_score_changes(model: Any, case: pd.DataFrame, reference: dict[str, Any], top: int = 8) -> list[dict[str, Any]]:
    """One-at-a-time deviation from development reference; not additive/causal."""
    original = float(positive_scores(model, case)[0])
    effects = []
    for column in case.columns:
        alternate = case.copy()
        alternate[column] = alternate[column].astype(object)
        alternate.at[alternate.index[0], column] = reference[column]
        score_without = float(positive_scores(model, alternate)[0])
        effects.append({"feature": column, "value": None if pd.isna(case.iloc[0][column]) else str(case.iloc[0][column]),
                        "reference": reference[column], "score_change": original-score_without})
    return sorted(effects, key=lambda row: abs(row["score_change"]), reverse=True)[:top]


def global_explanations(name: str, algorithm: str | None = None, *, root: Path = PROJECT_ROOT, quick: bool = False) -> dict[str, Any]:
    """Permutation importance on a development validation fold, never test labels."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    model, entry, selected = load_model(name, algorithm, root=root, quick=quick)
    X, y, _ = load_task(name, root)
    mode = "quick" if quick else "full"
    split = json.loads((root / "reports" / "ml" / mode / name / "split.json").read_text(encoding="utf-8"))
    dev = np.asarray(split["development_indices"], dtype=int)
    train, valid = cv_pairs(split)[0]
    # The persisted model was fit on all development rows. For permutation scores,
    # refit a clone on this fold's training rows and explain its held-out fold.
    fold_model = clone(model)
    fold_model.fit(X.iloc[dev[train]], y.iloc[dev[train]])
    importance = permutation_importance(fold_model, X.iloc[dev[valid]], y.iloc[dev[valid]],
                                        scoring=TASKS[name].selection_score, n_repeats=5,
                                        random_state=42, n_jobs=1)
    order = np.argsort(importance.importances_mean)[::-1]
    permutation = [{"feature": X.columns[i], "mean_score_drop": float(importance.importances_mean[i]),
                    "std": float(importance.importances_std[i])} for i in order]
    preprocess = model.named_steps["preprocess"]
    feature_names = preprocess.get_feature_names_out().tolist()
    estimator = model.named_steps["model"]
    transformed: list[dict[str, Any]] = []
    if hasattr(estimator, "coef_"):
        transformed = [{"encoded_feature": feature, "coefficient": float(value), "kind": "log_odds_coefficient"}
                       for feature, value in zip(feature_names, estimator.coef_[0])]
    elif hasattr(estimator, "feature_importances_"):
        transformed = [{"encoded_feature": feature, "importance": float(value), "kind": "impurity_importance"}
                       for feature, value in zip(feature_names, estimator.feature_importances_)]
    case = X.iloc[[dev[valid[0]]]].copy()
    local = local_score_changes(model, case, entry["reference_values"])
    result = {"task": name, "algorithm": selected, "selected_by_cv": selected == entry["selected_model"],
              "method": "five-repeat permutation on first development CV validation fold",
              "scoring": TASKS[name].selection_score, "validation_rows": len(valid), "permutation": permutation,
              "encoded_importance": transformed, "local_development_example": local,
              "caveat": "Importance and local score changes are descriptive, noncausal and not clinical explanations; one-hot coefficients refer to encoded levels.",
              "shap": "not performed; optional dependency unavailable"}
    directory = root / "reports" / "ml" / mode / name
    (directory / f"explanations_{selected}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    figure_dir = root / "reports" / "figures" / "ml" / mode / name
    figure_dir.mkdir(parents=True, exist_ok=True)
    top = permutation[:12][::-1]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh([r["feature"] for r in top], [r["mean_score_drop"] for r in top], color="#16858a")
    ax.set(xlabel=f"Mean drop in {TASKS[name].selection_score} after permutation", title=f"{name}: development-fold permutation importance")
    fig.text(0.5, 0.01, "Source: verified prepared data; five seeded repeats on development fold. Association is not causation.", ha="center", fontsize=8)
    fig.savefig(figure_dir / f"permutation_importance_{selected}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    if isinstance(estimator, DecisionTreeClassifier):
        fig, ax = plt.subplots(figsize=(18, 8))
        plot_tree(estimator, feature_names=feature_names, class_names=["negative", "positive"],
                  filled=True, rounded=True, max_depth=3, ax=ax, fontsize=7)
        fig.savefig(figure_dir / "decision_tree_top_levels.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
    return result
