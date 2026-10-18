"""Actual-result model comparison tables, figures and selection narratives."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from ..cli import PROJECT_ROOT
from .registry import read_registry
from .training import ALGORITHMS

METRICS = ("accuracy", "precision", "recall", "f1")
COLORS = {"logistic_regression": "#16858a", "decision_tree": "#eea36b", "random_forest": "#12304a", "knn": "#3c779b", "dummy_prior": "#8ca3ac"}


def comparison_rows(entry: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for algorithm in (*ALGORITHMS, "dummy_prior"):
        trial, test = entry["trials"][algorithm], entry["trials"][algorithm]["test"]
        rows.append({"dataset": entry["task"], "algorithm": algorithm, "selection_score": entry["selection_score"],
                     "cv_mean": trial["cv_mean"], "cv_std": trial["cv_std"],
                     "threshold": test["threshold"], "test_n": test["n"], "positive_n": test["positive_n"],
                     "negative_n": test["negative_n"], **{metric: test[metric] for metric in (*METRICS, "specificity", "balanced_accuracy", "roc_auc", "average_precision", "brier")},
                     "tn": test["confusion_matrix"][0][0], "fp": test["false_positive"],
                     "fn": test["false_negative"], "tp": test["confusion_matrix"][1][1],
                     "selected_by_cv": int(algorithm == entry["selected_model"])})
    return rows


def create_comparison(name: str, *, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    registry = read_registry(root)
    if name not in registry["tasks"]:
        raise ValueError(f"No full experiment for {name}")
    entry = registry["tasks"][name]
    rows = comparison_rows(entry)
    table_dir = root / "reports" / "tables" / "ml"
    figure_dir = root / "reports" / "figures" / "ml" / "full" / name
    narrative_dir = root / "reports" / "ml" / "full" / name
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    with (table_dir / f"{name}_comparison.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    algorithms = list(ALGORITHMS)
    fig_paths = []
    for metric in METRICS:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.bar(algorithms, [entry["trials"][a]["test"][metric] for a in algorithms], color=[COLORS[a] for a in algorithms])
        ax.set(ylim=(0, 1), ylabel=metric.title(), title=f"{name.title()} — held-out test {metric}")
        ax.tick_params(axis="x", rotation=22)
        fig.subplots_adjust(bottom=0.26)
        fig.text(0.5, 0.01, f"Verified prepared {name} data; test n={rows[0]['test_n']}. Model selected by development CV, not this chart.", ha="center", fontsize=8)
        path = figure_dir / f"test_{metric}.png"; fig.savefig(path, dpi=200, bbox_inches="tight"); plt.close(fig); fig_paths.append(str(path.relative_to(root)))
    fig, ax = plt.subplots(figsize=(9, 5.5))
    means = [entry["trials"][a]["cv_mean"] for a in algorithms]
    stds = [entry["trials"][a]["cv_std"] for a in algorithms]
    ax.bar(algorithms, means, yerr=stds, capsize=4, color=[COLORS[a] for a in algorithms])
    ax.set(ylim=(0, 1), ylabel=f"Development CV {entry['selection_score']}", title=f"{name.title()} — five-fold model selection")
    ax.tick_params(axis="x", rotation=22)
    fig.subplots_adjust(bottom=0.24)
    fig.text(0.5, 0.01, "Mean ± fold SD; shared folds, training-only preprocessing. Error bars are not confidence intervals.", ha="center", fontsize=8)
    path = figure_dir / "cv_performance.png"; fig.savefig(path, dpi=200, bbox_inches="tight"); plt.close(fig); fig_paths.append(str(path.relative_to(root)))
    for kind, xkey, ykey, xlabel, ylabel in (("roc", "fpr", "tpr", "False positive rate", "True positive rate"),
                                              ("precision_recall", "recall", "precision", "Recall", "Precision")):
        fig, ax = plt.subplots(figsize=(7, 6))
        for algorithm in algorithms:
            curve = entry["trials"][algorithm]["test"]["roc_curve" if kind == "roc" else "precision_recall_curve"]
            ax.plot(curve[xkey], curve[ykey], label=algorithm.replace("_", " "), color=COLORS[algorithm])
        if kind == "roc":ax.plot([0, 1], [0, 1], "--", color="#8ca3ac", linewidth=1)
        else:ax.axhline(rows[0]["positive_n"]/rows[0]["test_n"], linestyle="--", color="#8ca3ac", label="test prevalence")
        ax.set(xlim=(0, 1), ylim=(0, 1), xlabel=xlabel, ylabel=ylabel, title=f"{name.title()} — held-out test {kind.replace('_','-')} curves")
        ax.legend(fontsize=8)
        fig.text(0.5, 0.01, "Research-only scores; no clinical calibration or prospective validation.", ha="center", fontsize=8)
        path = figure_dir / f"test_{kind}.png"; fig.savefig(path, dpi=200, bbox_inches="tight"); plt.close(fig); fig_paths.append(str(path.relative_to(root)))
    fig, ax = plt.subplots(figsize=(7, 6))
    for algorithm in algorithms:
        calibration = entry["trials"][algorithm]["test"]["calibration"]
        ax.plot(calibration["mean_predicted"], calibration["fraction_positive"], marker="o", label=algorithm.replace("_", " "), color=COLORS[algorithm])
    ax.plot([0, 1], [0, 1], "--", color="#8ca3ac", label="reference")
    ax.set(xlim=(0, 1), ylim=(0, 1), xlabel="Mean estimated model score", ylabel="Observed positive fraction", title=f"{name.title()} — descriptive test calibration")
    ax.legend(fontsize=8)
    fig.text(0.5, 0.01, "Five quantile bins; small positive counts limit interpretation. Scores are not clinical probabilities.", ha="center", fontsize=8)
    path = figure_dir / "test_calibration.png";fig.savefig(path,dpi=200,bbox_inches="tight");plt.close(fig);fig_paths.append(str(path.relative_to(root)))
    for algorithm in algorithms:
        matrix = np.asarray(entry["trials"][algorithm]["test"]["confusion_matrix"])
        fig, ax = plt.subplots(figsize=(5.5, 5))
        ax.imshow(matrix, cmap="Blues")
        for i in range(2):
            for j in range(2): ax.text(j, i, str(matrix[i,j]), ha="center", va="center", color="black", fontsize=14)
        ax.set(xticks=[0,1], yticks=[0,1], xticklabels=["negative","positive"], yticklabels=["negative","positive"],
               xlabel="Predicted class", ylabel="Observed class", title=f"{name.title()} — {algorithm.replace('_',' ')} test counts")
        fig.text(0.5, 0.01, f"Held-out n={matrix.sum()}; threshold={entry['trials'][algorithm]['test']['threshold']:.3f}. Rows are observed labels.", ha="center", fontsize=8)
        path = figure_dir / f"confusion_{algorithm}.png";fig.savefig(path,dpi=200,bbox_inches="tight");plt.close(fig);fig_paths.append(str(path.relative_to(root)))
    selected = entry["selected_model"]
    trial = entry["trials"][selected]
    test = trial["test"]
    rationale = {"heart": "F1 balances precision and recall in a small two-class historical sample.",
                 "diabetes": "Balanced accuracy gives each questionnaire class equal weight while profile grouping protects the split.",
                 "stroke": "Average precision evaluates positive-case ranking under the observed rare-outcome prevalence; error tradeoffs are reported at a development-only F2 threshold."}[name]
    text = f"""# {name.title()} model-selection report

**Research-only; not clinically validated.** Dataset checksum: `{entry['prepared_sha256']}`. Split checksum: `{entry['split_sha256']}`.

Selection rule, fixed before test inspection: maximize development five-fold **{entry['selection_score']}**; tie by alphabetical algorithm name. {rationale}

Selected **{selected}**: CV mean {trial['cv_mean']:.4f}, fold SD {trial['cv_std']:.4f}; parameters `{json.dumps(trial['best_params'], sort_keys=True)}`. Threshold {test['threshold']:.4f}. Held-out n={test['n']} ({test['positive_n']} positive, {test['negative_n']} negative): accuracy {test['accuracy']:.4f}, precision {test['precision']:.4f}, recall {test['recall']:.4f}, F1 {test['f1']:.4f}, balanced accuracy {test['balanced_accuracy']:.4f}, ROC-AUC {test['roc_auc']:.4f}, average precision {test['average_precision']:.4f}. False positives {test['false_positive']}; false negatives {test['false_negative']}.

All four required algorithms and the dummy baseline are in `reports/tables/ml/{name}_comparison.csv`. This test score was **not** used for selection. False negatives may miss recorded outcomes; false positives may create unnecessary follow-up in a real setting, but no clinical use is supported. Cohort origin, sample size, missingness, repeated profiles and calibration limit generalization. Feature importance is descriptive, not causal.
"""
    (narrative_dir / "selection.md").write_text(text, encoding="utf-8")
    return {"task": name, "selected": selected, "table": str((table_dir / f"{name}_comparison.csv").relative_to(root)), "figures": fig_paths}
