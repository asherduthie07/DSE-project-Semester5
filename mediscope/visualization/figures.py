"""Phase III publication figures from versioned Phase II aggregate exports."""
from __future__ import annotations

import csv
from pathlib import Path

from mediscope.cli import PROJECT_ROOT
from .exports import verify_exports

NAVY = "#13324b"
TEAL = "#168b8b"
ORANGE = "#e39a45"


def _rows(name: str, root: Path) -> list[dict[str, str]]:
    with (root / "powerbi" / "exports" / "v1" / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _save(fig: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path.with_suffix(".png"), dpi=220, bbox_inches="tight", facecolor="white")
    fig.savefig(path.with_suffix(".svg"), bbox_inches="tight", facecolor="white", metadata={"Date": None})


def create_figures(root: Path = PROJECT_ROOT) -> list[Path]:
    """Create static figures without recomputing Phase II statistical findings."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    verify_exports(root)
    output = root / "reports" / "figures" / "phase3"
    made: list[Path] = []
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "svg.hashsalt": "mediscope-phase3"})

    outcomes = [r for r in _rows("outcomes", root) if r["dataset_id"] == "uci_cleveland_heart"]
    values = [int(r["count"]) for r in outcomes]
    labels = ["No recorded disease", "Recorded disease"]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(values, labels=labels, autopct=lambda pct: f"{pct:.1f}%", startangle=90,
           colors=[TEAL, ORANGE], wedgeprops={"width": 0.42, "edgecolor": "white"},
           textprops={"color": NAVY})
    ax.set_title("UCI Cleveland Heart Disease — recorded outcome", color=NAVY, pad=18)
    fig.text(0.5, 0.02, f"Source: UCI Cleveland | n={sum(values):,}; shares use all prepared records. Descriptive only.", ha="center", fontsize=9)
    path = output / "heart_outcome_pie"; _save(fig, path); plt.close(fig); made.append(path)

    bins = [r for r in _rows("histogram_bins", root) if r["dataset_id"] == "kaggle_stroke" and r["feature"] == "age"]
    fig, ax = plt.subplots(figsize=(10, 6))
    for label, color in [("0", TEAL), ("1", ORANGE)]:
        rows = [r for r in bins if r["outcome"] == label]
        centers = [(float(r["bin_start"]) + float(r["bin_end"])) / 2 for r in rows]
        widths = [float(r["bin_end"]) - float(r["bin_start"]) for r in rows]
        denominator = int(rows[0]["nonmissing_group_n"])
        ax.bar(centers, [int(r["count"]) / denominator for r in rows], width=widths, alpha=0.55,
               color=color, edgecolor="white", label=f"Stroke {label} (n={denominator:,})")
    ax.set(title="Healthcare Stroke Prediction — age distribution by outcome", xlabel="Age (years)", ylabel="Share within outcome group")
    ax.legend(frameon=False)
    fig.subplots_adjust(bottom=0.23)
    fig.text(0.5, 0.025, "Source: Healthcare Stroke Prediction | Five-year bins; within-group shares account for class imbalance.", ha="center", fontsize=9)
    path = output / "stroke_age_group_share_histogram"; _save(fig, path); plt.close(fig); made.append(path)

    boxes = [r for r in _rows("boxplot_stats", root) if r["dataset_id"] == "kaggle_stroke" and r["feature"] == "avg_glucose_level"]
    boxes = sorted(boxes, key=lambda r: r["group"])
    stats = [{"label": f"Stroke {r['group']}\n(n={r['n']})", "whislo": float(r["min"]), "q1": float(r["q1"]),
              "med": float(r["median"]), "q3": float(r["q3"]), "whishi": float(r["max"]), "fliers": []} for r in boxes]
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bxp(stats, showfliers=False, patch_artist=True, boxprops={"facecolor": TEAL, "alpha": 0.4}, medianprops={"color": NAVY})
    ax.set(title="Healthcare Stroke Prediction — glucose summaries", ylabel="Average glucose level (source unit unspecified)")
    fig.subplots_adjust(bottom=0.23)
    fig.text(0.5, 0.025, "Source: Healthcare Stroke Prediction | Boxes: Q1–Q3, median; whiskers: observed min–max. Aggregated source data.", ha="center", fontsize=9)
    path = output / "stroke_glucose_aggregate_boxplot"; _save(fig, path); plt.close(fig); made.append(path)

    correlations = [r for r in _rows("correlations", root) if r["dataset_id"] == "uci_cleveland_heart" and r["method"] == "pearson"]
    features = sorted(set(r["left"] for r in correlations) | set(r["right"] for r in correlations))
    matrix = np.full((len(features), len(features)), np.nan)
    for r in correlations:
        i, j = features.index(r["left"]), features.index(r["right"])
        matrix[i, j] = matrix[j, i] = float(r["coefficient"])
    np.fill_diagonal(matrix, 1)
    fig, ax = plt.subplots(figsize=(8, 7))
    image = ax.imshow(matrix, cmap="BrBG", vmin=-1, vmax=1)
    ax.set_xticks(range(len(features)), features, rotation=30, ha="right")
    ax.set_yticks(range(len(features)), features)
    for i in range(len(features)):
        for j in range(len(features)):
            if np.isfinite(matrix[i, j]): ax.text(j, i, f"{matrix[i,j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(image, ax=ax, shrink=0.8, label="Pearson correlation coefficient")
    ax.set_title("UCI Cleveland Heart Disease — continuous-feature correlation", pad=18)
    fig.subplots_adjust(bottom=0.24, left=0.15)
    fig.text(0.5, 0.025, "Source: UCI Cleveland | Pairwise non-missing observations; ID and nominal codes excluded. Association is not causation.", ha="center", fontsize=9)
    path = output / "heart_pearson_heatmap"; _save(fig, path); plt.close(fig); made.append(path)

    frequency = [r for r in _rows("diabetes_symptoms", root) if r["class"] == "Positive"]
    frequency.sort(key=lambda r: float(r["yes_pct"]))
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh([r["symptom"] for r in frequency], [float(r["yes_pct"]) for r in frequency], color=TEAL)
    ax.set(xlabel="Share reporting symptom within positive class (%)", xlim=(0, 100),
           title="UCI Early Stage Diabetes — symptom frequency among positive records")
    fig.subplots_adjust(left=0.27, bottom=0.17)
    fig.text(0.5, 0.025, "Source: UCI Early Stage Diabetes | Denominator: 320 positive records; repeated profiles may affect independence.", ha="center", fontsize=9)
    path = output / "diabetes_positive_symptom_frequencies"; _save(fig, path); plt.close(fig); made.append(path)
    return made
