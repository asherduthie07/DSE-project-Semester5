"""Three preregistered Phase II tests; group direction is positive minus negative."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from .stats import finite


def welch_test(frame: pd.DataFrame, target: str, feature: str, positive: Any, negative: Any, alpha: float, hypothesis_id: str) -> dict[str, Any]:
    """Welch test, mean-difference CI, and descriptive Hedges g."""
    a = pd.to_numeric(frame.loc[frame[target] == positive, feature], errors="coerce").dropna().to_numpy(dtype=float)
    b = pd.to_numeric(frame.loc[frame[target] == negative, feature], errors="coerce").dropna().to_numpy(dtype=float)
    if min(len(a), len(b)) < 2:
        raise ValueError(f"{hypothesis_id}: each group requires at least two nonmissing observations")
    n1, n0 = len(a), len(b)
    m1, m0 = float(a.mean()), float(b.mean())
    v1, v0 = float(a.var(ddof=1)), float(b.var(ddof=1))
    se2 = v1 / n1 + v0 / n0
    if se2 <= 0:
        raise ValueError(f"{hypothesis_id}: mean difference has zero standard error")
    df = se2 ** 2 / ((v1 / n1) ** 2 / (n1 - 1) + (v0 / n0) ** 2 / (n0 - 1))
    difference = m1 - m0
    critical = float(stats.t.ppf(1 - alpha / 2, df))
    result = stats.ttest_ind(a, b, equal_var=False)
    pooled = math.sqrt(((n1 - 1) * v1 + (n0 - 1) * v0) / (n1 + n0 - 2))
    hedges_g = (difference / pooled) * (1 - 3 / (4 * (n1 + n0 - 2) - 1)) if pooled > 0 else None
    trimmed = stats.ttest_ind(a, b, equal_var=False, trim=0.1) if min(n1, n0) >= 10 else None
    return {"id": hypothesis_id, "method": "two-sided Welch unequal-variance t-test", "feature": feature, "target": target,
            "positive_label": str(positive), "negative_label": str(negative), "positive_n": n1, "negative_n": n0,
            "positive_mean": m1, "negative_mean": m0, "positive_sd": math.sqrt(v1), "negative_sd": math.sqrt(v0),
            "positive_median": float(np.median(a)), "negative_median": float(np.median(b)),
            "positive_skew": finite(stats.skew(a, bias=False)) if n1 > 2 and len(np.unique(a)) > 1 else None,
            "negative_skew": finite(stats.skew(b, bias=False)) if n0 > 2 and len(np.unique(b)) > 1 else None,
            "mean_difference": difference, "statistic": finite(result.statistic), "df": df, "p_value": finite(result.pvalue),
            "effect_size": finite(hedges_g) if hedges_g is not None else None, "effect_name": "Hedges g (pooled-SD standardization)",
            "ci_low": difference - critical * math.sqrt(se2), "ci_high": difference + critical * math.sqrt(se2),
            "ci_parameter": "positive minus negative population mean", "alpha": alpha,
            "sensitivity_method": "two-sided 10% trimmed Welch/Yuen test" if trimmed is not None else None,
            "sensitivity_p_value": finite(trimmed.pvalue) if trimmed is not None else None,
            "missing_policy": "complete cases for feature and target", "assumptions": "Independent observations; numeric measurements; Welch does not require equal variances. Skew and influential values assessed with group summaries and trimmed sensitivity."}


def hypertension_test(frame: pd.DataFrame, alpha: float) -> dict[str, Any]:
    """Select Fisher for a 2x2 table when chi-square expected cells are small."""
    table = pd.crosstab(frame["hypertension"], frame["stroke"]).reindex(index=[0, 1], columns=[0, 1], fill_value=0)
    if table.to_numpy().sum() == 0 or (table.sum(axis=0) == 0).any() or (table.sum(axis=1) == 0).any():
        raise ValueError("H2 requires both hypertension and stroke classes")
    chi2, chi_p, _, expected = stats.chi2_contingency(table, correction=False)
    observed = table.to_numpy(dtype=float)
    fisher = bool((expected < 5).any())
    if fisher:
        odds, pvalue = stats.fisher_exact(observed, alternative="two-sided")
        statistic = float(odds)
        method = "two-sided Fisher exact test (minimum expected cell <5)"
    else:
        pvalue = chi_p
        statistic = chi2
        method = "Pearson chi-square test, 1 df, no continuity correction (all expected cells >=5)"
    # Exposed versus unexposed odds of stroke; half-cell correction only if zero observed.
    a, b, c, d = observed[1, 1], observed[1, 0], observed[0, 1], observed[0, 0]
    adjusted = [x + 0.5 for x in (a, b, c, d)] if min(a, b, c, d) == 0 else [a, b, c, d]
    aa, bb, cc, dd = adjusted
    odds_ratio = aa * dd / (bb * cc)
    se = math.sqrt(sum(1 / x for x in adjusted))
    z = float(stats.norm.ppf(1 - alpha / 2))
    risk1, risk0 = a / (a + b), c / (c + d)
    return {"id": "H2", "method": method, "feature": "hypertension", "target": "stroke",
            "table": {"no_hypertension_no_stroke": int(d), "no_hypertension_stroke": int(c), "hypertension_no_stroke": int(b), "hypertension_stroke": int(a)},
            "positive_n": int(a + b), "negative_n": int(c + d), "stroke_positive_n": int(a + c), "stroke_negative_n": int(b + d),
            "stroke_risk_hypertension": risk1, "stroke_risk_no_hypertension": risk0, "risk_difference": risk1 - risk0,
            "statistic": finite(statistic), "p_value": finite(pvalue), "effect_name": "odds ratio, hypertension versus no hypertension",
            "effect_size": odds_ratio, "ci_low": math.exp(math.log(odds_ratio) - z * se), "ci_high": math.exp(math.log(odds_ratio) + z * se),
            "ci_parameter": "odds ratio (approximate log-Wald interval)", "minimum_expected": finite(expected.min()),
            "phi": math.sqrt(chi2 / observed.sum()), "alpha": alpha, "missing_policy": "complete cases; no target imputation",
            "assumptions": "Independent records and mutually exclusive categories; expected-cell rule selects Fisher where needed. Odds-ratio interval is approximate."}
