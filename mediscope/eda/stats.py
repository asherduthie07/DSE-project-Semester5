"""Semantics-aware descriptive and association statistics for prepared tables."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


def finite(value: Any) -> float | None:
    """Turn undefined NumPy/scipy statistics into JSON nulls."""
    value = float(value)
    return value if math.isfinite(value) else None


def numeric_summary(frame: pd.DataFrame, columns: tuple[str, ...], group: str | None = None) -> list[dict[str, Any]]:
    """Use nonmissing denominators and sample variance (ddof=1)."""
    groups = [("all", frame)] if group is None else list(frame.groupby(group, dropna=False, sort=True))
    rows: list[dict[str, Any]] = []
    for label, part in groups:
        for column in columns:
            values = pd.to_numeric(part[column], errors="coerce").dropna().astype(float)
            n = len(values)
            q1, median, q3 = (finite(values.quantile(q)) if n else None for q in (0.25, 0.5, 0.75))
            modes = values.mode() if n else pd.Series(dtype=float)
            rows.append({"group": str(label), "feature": column, "rows": len(part), "n": n,
                         "missing_n": len(part) - n, "missing_pct": 100 * (len(part) - n) / len(part) if len(part) else None,
                         "mean": finite(values.mean()) if n else None, "median": median,
                         "mode": finite(modes.iloc[0]) if n and values.nunique() <= 20 and len(modes) == 1 else None,
                         "min": finite(values.min()) if n else None, "max": finite(values.max()) if n else None,
                         "range": finite(values.max() - values.min()) if n else None,
                         "q1": q1, "q3": q3, "iqr": q3 - q1 if n else None,
                         "variance": finite(values.var(ddof=1)) if n > 1 else None,
                         "std": finite(values.std(ddof=1)) if n > 1 else None,
                         "skewness": finite(stats.skew(values, bias=False)) if n > 2 and values.nunique() > 1 else None})
    return rows


def categorical_summary(frame: pd.DataFrame, columns: tuple[str, ...], group: str | None = None) -> list[dict[str, Any]]:
    groups = [("all", frame)] if group is None else list(frame.groupby(group, dropna=False, sort=True))
    rows: list[dict[str, Any]] = []
    for label, part in groups:
        for column in columns:
            counts = part[column].astype("string").fillna("<missing>").value_counts(dropna=False, sort=False).sort_index()
            present = int(part[column].notna().sum())
            for category, count in counts.items():
                rows.append({"group": str(label), "feature": column, "category": str(category), "count": int(count),
                             "nonmissing_n": present, "all_n": len(part), "pct_all": 100 * count / len(part) if len(part) else None,
                             "pct_nonmissing": 100 * count / present if present and category != "<missing>" else None})
    return rows


def bh_adjust(pvalues: list[float]) -> list[float]:
    """Benjamini-Hochberg adjusted exploratory p values, preserving input order."""
    if not pvalues:
        return []
    n = len(pvalues)
    order = sorted(range(n), key=lambda i: pvalues[i])
    adjusted = [1.0] * n
    ceiling = 1.0
    for rank in range(n, 0, -1):
        i = order[rank - 1]
        ceiling = min(ceiling, pvalues[i] * n / rank)
        adjusted[i] = ceiling
    return adjusted


def numeric_associations(frame: pd.DataFrame, columns: tuple[str, ...], target: str | None = None) -> tuple[list[dict[str, Any]], dict[str, pd.DataFrame], list[str]]:
    """Pairwise complete-case correlations; never infer semantic roles from dtype."""
    usable = [c for c in columns if frame[c].dropna().nunique() > 1]
    skipped = [c for c in columns if c not in usable]
    matrices = {method: pd.DataFrame(np.nan, index=usable, columns=usable) for method in ("pearson", "spearman")}
    rows: list[dict[str, Any]] = []
    for i, left in enumerate(usable):
        for method in matrices:
            matrices[method].loc[left, left] = 1.0
        for right in usable[i + 1:]:
            pair = frame[[left, right]].dropna()
            for method, function in (("pearson", stats.pearsonr), ("spearman", stats.spearmanr)):
                result = function(pair[left], pair[right]) if len(pair) >= 3 and pair[left].nunique() > 1 and pair[right].nunique() > 1 else None
                coefficient = finite(result.statistic) if result is not None else None
                pvalue = finite(result.pvalue) if result is not None else None
                matrices[method].loc[left, right] = matrices[method].loc[right, left] = coefficient
                rows.append({"method": method, "left": left, "right": right, "n": len(pair), "coefficient": coefficient, "p_value": pvalue, "missing_policy": "pairwise complete case"})
    if target is not None:
        for column in usable:
            pair = frame[[column, target]].dropna()
            if len(pair) >= 3 and pair[target].nunique() == 2 and pair[column].nunique() > 1:
                result = stats.pointbiserialr(pair[target].astype(float), pair[column].astype(float))
                rows.append({"method": "point_biserial", "left": target, "right": column, "n": len(pair), "coefficient": finite(result.statistic), "p_value": finite(result.pvalue), "missing_policy": "pairwise complete case"})
    valid = [i for i, row in enumerate(rows) if row["p_value"] is not None]
    for index, q in zip(valid, bh_adjust([rows[i]["p_value"] for i in valid])):
        rows[index]["bh_q_value"] = q
    return rows, matrices, skipped


def categorical_associations(frame: pd.DataFrame, columns: tuple[str, ...], target: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Chi-square and Cramer's V for nominal/binary predictors, with small-cell flags."""
    rows: list[dict[str, Any]] = []
    skipped: list[str] = []
    for column in columns:
        pair = frame[[column, target]].dropna()
        table = pd.crosstab(pair[column], pair[target])
        if min(table.shape, default=0) < 2:
            skipped.append(column)
            continue
        chi2, pvalue, dof, expected = stats.chi2_contingency(table, correction=False)
        n = int(table.to_numpy().sum())
        rows.append({"feature": column, "target": target, "n": n, "levels": table.shape[0], "target_levels": table.shape[1],
                     "chi2": finite(chi2), "dof": int(dof), "p_value": finite(pvalue),
                     "cramers_v": finite(math.sqrt(chi2 / (n * min(table.shape[0] - 1, table.shape[1] - 1)))),
                     "minimum_expected": finite(expected.min()), "expected_below_5": int((expected < 5).sum()),
                     "missing_policy": "complete case; missing/Unknown responses excluded"})
    valid = [i for i, row in enumerate(rows) if row["p_value"] is not None]
    for index, q in zip(valid, bh_adjust([rows[i]["p_value"] for i in valid])):
        rows[index]["bh_q_value"] = q
    return rows, skipped
