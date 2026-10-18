"""Report figures from actual Phase I prepared data; no random sampling."""

from __future__ import annotations

import os
from pathlib import Path

from ..cli import PROJECT_ROOT

_cache = PROJECT_ROOT / ".cache"
_cache.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_cache))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def save(figure: plt.Figure, path: Path, caption: str, source: str, bottom: float = 0.17) -> None:
    figure.text(0.01, 0.012, f"Source: {source} | {caption}", fontsize=8, va="bottom", wrap=True)
    figure.subplots_adjust(bottom=bottom)
    figure.savefig(path, dpi=200, bbox_inches="tight", metadata={"Software": "MediScope AI Phase II"})
    plt.close(figure)


def outcome_bar(frame: pd.DataFrame, target: str, path: Path, source: str) -> None:
    counts = frame[target].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(counts.index.astype(str), counts.to_numpy(), color="#235789")
    ax.bar_label(bars, labels=[f"{n:,} ({n / len(frame):.1%})" for n in counts])
    ax.set(xlabel=target, ylabel="Records", title=f"{source}: {target} distribution")
    ax.set_ylim(0, max(counts) * 1.15)
    save(fig, path, f"n={len(frame):,}; percentages use all records.", source)


def grouped_hist(frame: pd.DataFrame, feature: str, target: str, unit: str, path: Path, source: str) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for label, part in frame.groupby(target, sort=True):
        values = pd.to_numeric(part[feature], errors="coerce").dropna()
        ax.hist(values, bins=25, density=True, alpha=0.48, label=f"{label} (n={len(values):,})")
    ax.set(xlabel=f"{feature} ({unit})" if unit else feature, ylabel="Density", title=f"{source}: {feature} by {target}")
    ax.legend(title=target)
    save(fig, path, "Within-class density; class sizes are shown in the legend. Nonmissing measurements only.", source)


def grouped_box(frame: pd.DataFrame, feature: str, target: str, unit: str, path: Path, source: str) -> None:
    groups = [(str(label), pd.to_numeric(part[feature], errors="coerce").dropna().to_numpy()) for label, part in frame.groupby(target, sort=True)]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.boxplot([values for _, values in groups], tick_labels=[f"{label}\nn={len(values):,}" for label, values in groups], showfliers=True)
    ax.set(xlabel=target, ylabel=f"{feature} ({unit})" if unit else feature, title=f"{source}: {feature} by {target}")
    save(fig, path, "Box: Q1–Q3; line: median; whiskers: 1.5×IQR; points: retained values.", source)


def category_bar(frame: pd.DataFrame, feature: str, caption: str, path: Path, source: str) -> None:
    counts = frame[feature].astype("string").fillna("<missing>").value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(8, max(4.5, 0.35 * len(counts) + 2)))
    ax.barh(counts.index.astype(str), counts.to_numpy(), color="#218380")
    ax.set(xlabel="Records", ylabel=feature, title=f"{source}: {feature} frequency")
    save(fig, path, f"n={len(frame):,}; {caption}", source)


def heatmap(matrix: pd.DataFrame, method: str, path: Path, source: str) -> None:
    if len(matrix) < 2:
        return
    fig, ax = plt.subplots(figsize=(max(6, len(matrix) + 2), max(5, len(matrix) + 1)))
    image = ax.imshow(matrix.to_numpy(dtype=float), cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(matrix)), labels=matrix.columns, rotation=40, ha="right")
    ax.set_yticks(range(len(matrix)), labels=matrix.index)
    ax.set(xlabel="Continuous features", ylabel="Continuous features", title=f"{source}: {method.title()} correlation")
    for row in range(len(matrix)):
        for col in range(len(matrix)):
            value = matrix.iat[row, col]
            ax.text(col, row, f"{value:.2f}" if np.isfinite(value) else "NA", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, label="Correlation coefficient")
    save(fig, path, "Pairwise complete cases; identifiers and categorical codes excluded. Association is not causation.", source)


def simple_hist(values: pd.Series, label: str, unit: str, path: Path, source: str) -> None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(clean, bins=25, color="#235789", edgecolor="white")
    ax.set(xlabel=f"{label} ({unit})" if unit else label, ylabel="Records", title=f"{source}: {label}")
    save(fig, path, f"n={len(clean):,} nonmissing records.", source)


def temporal_bar(monthly: pd.Series, path: Path, source: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(monthly.index.astype(str), monthly.to_numpy(), color="#235789", linewidth=1.4)
    ax.tick_params(axis="x", rotation=60)
    ax.set(xlabel="Encounter start month", ylabel="Encounters", title=f"{source}: monthly encounters")
    if len(monthly) > 24:
        for i, tick in enumerate(ax.get_xticklabels()):
            tick.set_visible(i % max(1, len(monthly) // 12) == 0)
    save(fig, path, f"{int(monthly.sum()):,} valid-dated simulated encounters; counts are not incidence rates.", source)


def grouped_yes_rates(frame: pd.DataFrame, features: tuple[str, ...], target: str, path: Path, source: str) -> None:
    classes = sorted(frame[target].dropna().unique())
    x = np.arange(len(features))
    width = 0.8 / len(classes)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    for i, label in enumerate(classes):
        part = frame.loc[frame[target] == label]
        rates = [(part[feature] == "Yes").mean() * 100 for feature in features]
        ax.bar(x + (i - (len(classes) - 1) / 2) * width, rates, width, label=f"{label} (n={len(part)})")
    ax.set_xticks(x, labels=features, rotation=55, ha="right")
    ax.set(xlabel="Reported symptom", ylabel="Yes responses within class (%)", ylim=(0, 100), title=f"{source}: symptom frequency by outcome")
    ax.legend(title=target)
    save(fig, path, "Class denominators include all records; identical profiles are retained.", source, bottom=0.34)


def age_group_rates(frame: pd.DataFrame, path: Path, source: str) -> None:
    labels = ["<18", "18–39", "40–59", "60–79", "80+"]
    groups = pd.cut(frame["age"], [-np.inf, 18, 40, 60, 80, np.inf], labels=labels, right=False)
    summary = frame.groupby(groups, observed=False)["stroke"].agg(["size", "sum"])
    rates = 100 * summary["sum"] / summary["size"]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, rates, color="#218380")
    ax.bar_label(bars, labels=[f"{int(p)}/{int(n)}" for p, n in zip(summary["sum"], summary["size"])])
    ax.set(xlabel="Age group (years)", ylabel="Stroke-positive records within group (%)", title=f"{source}: stroke outcome by age group")
    ax.set_ylim(0, max(rates) * 1.2)
    save(fig, path, "Labels show stroke-positive count / age-group count; descriptive proportions only.", source)
