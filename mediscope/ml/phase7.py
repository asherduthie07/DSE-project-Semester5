"""Supplementary development-only data-quality and reliability experiments."""
from __future__ import annotations

import copy
import hashlib
import json
import platform
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
import sklearn
from scipy.stats import spearmanr
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, brier_score_loss,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from threadpoolctl import threadpool_limits

from ..cli import PROJECT_ROOT, sha256
from ..preparation import load_config
from ..preprocessors import build_preprocessor
from .tasks import TASKS, load_task, profile_groups
from .training import model_factory

SEED = 42
STRATEGIES = ("baseline", "mean", "missing_indicator", "iqr_clip", "minmax", "robust",
              "no_scaling", "categorical_constant", "smoking_explicit", "deduplicated")
METRICS = ("f1", "balanced_accuracy", "roc_auc", "average_precision", "brier")


def read_saved_split(root: Path, task: str, X: pd.DataFrame, y: pd.Series, source_hash: str) -> dict:
    split = json.loads((root / "reports/ml/full" / task / "split.json").read_text())
    if split["prepared_sha256"] != source_hash:
        raise ValueError("Prepared source differs from the frozen Phase IV split")
    saved_hash = split.pop("sha256")
    prepared_hash = split.pop("prepared_sha256")
    actual = hashlib.sha256(json.dumps(split, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    split["sha256"], split["prepared_sha256"] = saved_hash, prepared_hash
    if actual != saved_hash:
        raise ValueError("Phase IV split checksum mismatch")
    dev, held = split["development_indices"], split["test_indices"]
    if len(dev) + len(held) != len(X) or set(dev) & set(held):
        raise ValueError("Invalid saved split partition")
    validation = [i for fold in split["cv_folds"] for i in fold["validation"]]
    if sorted(validation) != list(range(len(dev))):
        raise ValueError("Saved validation folds do not partition development")
    if task == "diabetes":
        groups = profile_groups(X.iloc[dev])
        for fold in split["cv_folds"]:
            if set(groups[fold["train"]]) & set(groups[fold["validation"]]):
                raise ValueError("Profile leakage in saved diabetes folds")
    return split


def strategy_frame(X: pd.DataFrame, task: str, strategy: str) -> pd.DataFrame:
    result = X.copy()
    if task == "stroke" and strategy == "smoking_explicit":
        result["smoking_status"] = result["smoking_status"].fillna("Unknown")
    return result


def pipeline(root: Path, task: str, algorithm: str, params: dict, strategy: str) -> Pipeline:
    config = strategy_config(root, algorithm, strategy)
    prep = build_preprocessor(TASKS[task].dataset_id, config)
    if strategy == "missing_indicator": prep.set_params(numeric__impute__add_indicator=True)
    estimator = Pipeline([("preprocess", prep), ("model", model_factory(algorithm, SEED))])
    estimator.set_params(**params)
    if strategy == "no_scaling" and algorithm == "logistic_regression":
        # Unscaled clinical measures trigger liblinear's loose default stop
        # criterion; tighten optimization so repeated fits agree numerically.
        estimator.set_params(model__tol=1e-9)
    return estimator


def strategy_config(root: Path, algorithm: str, strategy: str) -> dict:
    """Return the exact registered preprocessing knobs for an experiment."""
    config = copy.deepcopy(load_config(root / "data/metadata/preparation_config.json"))
    config["numeric_scaling"] = "standard" if algorithm in ("logistic_regression", "knn") else "none"
    if strategy == "mean": config["numeric_imputation"] = "mean"
    if strategy == "iqr_clip": config["iqr_clip_in_training_pipeline"] = True
    if strategy in ("minmax", "robust"): config["numeric_scaling"] = strategy
    if strategy == "no_scaling": config["numeric_scaling"] = "none"
    if strategy == "categorical_constant":
        config["categorical_imputation"] = "constant"
        config["categorical_fill_value"] = "__MISSING__"
    config["numeric_missing_indicator"] = strategy == "missing_indicator"
    config["stroke_unknown_smoking_as_missing"] = strategy != "smoking_explicit"
    config["deduplicate_training_profiles"] = strategy == "deduplicated"
    config["solver_tolerance"] = 1e-9 if strategy == "no_scaling" and algorithm == "logistic_regression" else 1e-4
    return config


def measure(y: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, float | int]:
    pred = score >= threshold
    return {"n": int(len(y)), "positive_n": int(y.sum()), "negative_n": int(len(y)-y.sum()),
            "f1": float(f1_score(y, pred, zero_division=0)),
            "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
            "precision": float(precision_score(y, pred, zero_division=0)),
            "recall": float(recall_score(y, pred, zero_division=0)),
            "false_positive": int(((y == 0) & pred).sum()),
            "false_negative": int(((y == 1) & ~pred).sum()),
            "roc_auc": float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 else None,
            "average_precision": float(average_precision_score(y, score)) if y.sum() else None,
            "brier": float(brier_score_loss(y, score))}


def wilson(success: int, total: int) -> list[float] | None:
    if total == 0: return None
    z = 1.96
    p = success / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    radius = z*np.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return [float(max(0, center-radius)), float(min(1, center+radius))]


def subgroup_rows(task: str, X: pd.DataFrame, y: np.ndarray, score: np.ndarray, threshold: float) -> list[dict]:
    fields = {"heart": ("sex", "age"), "diabetes": ("Gender", "Age"),
              "stroke": ("gender", "age", "Residence_type", "smoking_status")}[task]
    rows = []
    for field in fields:
        categories = pd.cut(pd.to_numeric(X[field]), [0, 40, 60, 120], labels=["≤40", "41–60", ">60"], include_lowest=True) if field.lower() == "age" else X[field].fillna("Missing")
        for value in sorted(categories.astype(str).unique()):
            mask = (categories.astype(str) == value).to_numpy()
            yt, st = y[mask], score[mask]
            pred = st >= threshold
            tp, fp, fn = int(((yt == 1) & pred).sum()), int(((yt == 0) & pred).sum()), int(((yt == 1) & ~pred).sum())
            precision = tp/(tp+fp) if tp+fp else None
            recall = tp/(tp+fn) if tp+fn else None
            f1 = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None
            rng = np.random.default_rng(SEED)
            bootstrap = []
            for _ in range(400):
                sample = rng.integers(0, len(yt), len(yt))
                bootstrap.append(float(f1_score(yt[sample], pred[sample], zero_division=0)))
            rows.append({"field": field, "group": value, "n": int(mask.sum()), "positive_n": int(yt.sum()),
                         "negative_n": int(len(yt)-yt.sum()), "precision": precision, "recall": recall, "f1": f1,
                         "f1_ci95_bootstrap": [float(v) for v in np.quantile(bootstrap, [0.025, 0.975])],
                         "precision_ci95": wilson(tp, tp+fp), "recall_ci95": wilson(tp, tp+fn),
                         "flag": "small_or_sparse" if len(yt)<30 or min(int(yt.sum()), int(len(yt)-yt.sum()))<10 else "descriptive"})
    return rows


def run_task(root: Path, task: str) -> dict:
    X, y, provenance = load_task(task, root)
    split = read_saved_split(root, task, X, y, provenance["prepared_sha256"])
    dev = np.asarray(split["development_indices"])
    Xd, yd = X.iloc[dev].reset_index(drop=True), y.iloc[dev].to_numpy()
    registry = json.loads((root / "ml/registry.json").read_text())["tasks"][task]
    algorithm = registry["selected_model"]
    params = registry["trials"][algorithm]["best_params"]
    threshold = float(registry["trials"][algorithm]["threshold_selection"]["threshold"])
    strategies = [s for s in STRATEGIES if s != "smoking_explicit" or task == "stroke"]
    strategies = [s for s in strategies if s != "deduplicated" or task == "diabetes"]
    comparisons, importance, baselines, oof_scores = [], [], {}, {}
    folds = split["cv_folds"]
    for strategy in strategies:
        fold_metrics, scores = [], np.full(len(yd), np.nan)
        for fold_index, fold in enumerate(folds):
            train, valid = np.asarray(fold["train"]), np.asarray(fold["validation"])
            if strategy == "deduplicated":
                groups = profile_groups(Xd.iloc[train]); train = train[np.unique(groups, return_index=True)[1]]
            fitted = pipeline(root, task, algorithm, params, strategy)
            fitted.fit(strategy_frame(Xd.iloc[train], task, strategy), yd[train])
            validation = strategy_frame(Xd.iloc[valid], task, strategy)
            score = fitted.predict_proba(validation)[:, 1]
            scores[valid] = score
            fold_metrics.append({"fold": fold_index, **measure(yd[valid], score, threshold), "train_n": int(len(train))})
            # Permutation is always scored on a disjoint validation fold.
            if strategy in ("baseline", "mean", "iqr_clip", "smoking_explicit", "deduplicated"):
                perm = permutation_importance(fitted, validation, yd[valid], n_repeats=3,
                                              random_state=SEED+fold_index, scoring=TASKS[task].selection_score, n_jobs=1)
                for feature, delta in zip(Xd.columns, perm.importances_mean):
                    importance.append({"strategy": strategy, "algorithm": algorithm, "fold": fold_index,
                                       "feature": feature, "score_drop": float(delta)})
        if not np.isfinite(scores).all(): raise ValueError("Incomplete development predictions")
        oof_scores[strategy] = scores
        summary = measure(yd, scores, threshold)
        comparisons.append({"strategy": strategy, "algorithm": algorithm, "model_params": params,
                            "preprocessing_config": strategy_config(root, algorithm, strategy), "threshold": threshold,
                            "folds": fold_metrics, "oof": summary,
                            "fold_mean": {k: float(np.mean([row[k] for row in fold_metrics])) for k in METRICS},
                            "fold_sd": {k: float(np.std([row[k] for row in fold_metrics], ddof=1)) for k in METRICS}})
        if strategy == "baseline": baselines = {"scores": scores, "folds": fold_metrics}
    baseline_scores = baselines["scores"]
    sensitivity = []
    # This evaluates the saved selected model family on the same development folds.
    for family in ("decision_tree", "random_forest", "knn"):
        family_params = registry["trials"][family]["best_params"]
        family_folds = []
        for fold_index, fold in enumerate(folds):
            train, valid = np.asarray(fold["train"]), np.asarray(fold["validation"])
            fitted = pipeline(root, task, family, family_params, "baseline")
            fitted.fit(Xd.iloc[train], yd[train])
            score = fitted.predict_proba(Xd.iloc[valid])[:, 1]
            family_folds.append(measure(yd[valid], score, 0.5))
            perm = permutation_importance(fitted, Xd.iloc[valid], yd[valid], n_repeats=3,
                                          random_state=SEED+fold_index, scoring=TASKS[task].selection_score, n_jobs=1)
            for feature, delta in zip(Xd.columns, perm.importances_mean):
                importance.append({"strategy": "baseline", "algorithm": family, "fold": fold_index,
                                   "feature": feature, "score_drop": float(delta)})
        sensitivity.append({"algorithm": family, "fold_mean": {k: float(np.mean([r[k] for r in family_folds])) for k in METRICS},
                            "fold_sd": {k: float(np.std([r[k] for r in family_folds], ddof=1)) for k in METRICS}})
    thresholds = [0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
    if threshold not in thresholds: thresholds.append(threshold)
    threshold_rows = [{"threshold": t, **measure(yd, baseline_scores, t)} for t in sorted(thresholds)]
    bins = np.linspace(0, 1, 6)
    calibration = []
    for strategy, strategy_scores in oof_scores.items():
        for bin_index in range(5):
            mask = (strategy_scores >= bins[bin_index]) & (strategy_scores < bins[bin_index+1] if bin_index < 4 else strategy_scores <= 1)
            if mask.any(): calibration.append({"strategy": strategy, "lower": float(bins[bin_index]), "upper": float(bins[bin_index+1]),
                                               "n": int(mask.sum()), "mean_score": float(strategy_scores[mask].mean()),
                                               "observed_rate": float(yd[mask].mean())})
    stability = []
    by_key = {(row["strategy"], row["algorithm"], row["fold"], row["feature"]): row["score_drop"] for row in importance}
    for strategy, family in sorted({(row["strategy"], row["algorithm"]) for row in importance}):
        rank_agreements = []
        for first in range(len(folds)):
            for second in range(first+1, len(folds)):
                a = [by_key[(strategy,family,first,feature)] for feature in Xd.columns]
                b = [by_key[(strategy,family,second,feature)] for feature in Xd.columns]
                rho = spearmanr(a,b).statistic
                if np.isfinite(rho): rank_agreements.append(float(rho))
        stability.append({"strategy":strategy,"algorithm":family,"mean_pairwise_spearman":float(np.mean(rank_agreements)) if rank_agreements else None,
                          "fold_pairs":len(rank_agreements)})
    rank_comparisons = []
    rank_vectors = {}
    for strategy, family in sorted({(row["strategy"], row["algorithm"]) for row in importance}):
        rank_vectors[(strategy, family)] = [float(np.mean([by_key[(strategy,family,fold,feature)] for fold in range(len(folds))]))
                                            for feature in Xd.columns]
    reference = rank_vectors[("baseline", algorithm)]
    for (strategy, family), vector in rank_vectors.items():
        rho = spearmanr(reference, vector).statistic
        rank_comparisons.append({"strategy":strategy,"algorithm":family,
                                 "spearman_to_selected_baseline":float(rho) if np.isfinite(rho) else None})
    missing = []
    for fold_index, fold in enumerate(folds):
        train, valid = np.asarray(fold["train"]), np.asarray(fold["validation"])
        fitted = pipeline(root, task, algorithm, params, "baseline").fit(Xd.iloc[train], yd[train])
        base = fitted.predict_proba(Xd.iloc[valid])[:, 1]
        for feature in Xd.columns:
            altered = Xd.iloc[valid].copy(); altered[feature] = np.nan
            changed = fitted.predict_proba(altered)[:, 1]
            missing.append({"fold": fold_index, "feature": feature, "mean_absolute_score_change": float(np.abs(changed-base).mean())})
    result = {"task": task, "dataset_id": TASKS[task].dataset_id, "source": provenance, "split_sha256": split["sha256"],
              "development_n": len(dev), "development_positive_n": int(yd.sum()), "held_out_n_unaccessed": len(split["test_indices"]),
              "selected_phase4_model": algorithm, "phase4_threshold": threshold, "comparisons": comparisons,
              "family_comparisons": sensitivity, "threshold_sensitivity": threshold_rows, "calibration": calibration,
              "subgroups": subgroup_rows(task, Xd, yd, baseline_scores, threshold), "importance": importance,
              "importance_stability": stability,
              "importance_rank_comparisons": rank_comparisons,
              "missing_feature_sensitivity": missing,
              "limitations": ["Development-only OOF comparisons; reused Phase IV hyperparameters and threshold.",
                              "Fold scores share training data and are not independent confidence intervals.",
                              "Subgroups are descriptive, not fairness or clinical validation; row bootstrap and Wilson intervals can be optimistic when diabetes predictor profiles repeat.",
                              "Permutation importance is predictive association, not causation."]}
    return result


def export(root: Path = PROJECT_ROOT) -> dict:
    out = root / "reports/phase7"; out.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=1):
        results = {task: run_task(root, task) for task in TASKS}
    # BLAS/liblinear can differ in the last binary digits across otherwise
    # identical runs. Preserve more precision than the reported measurements
    # support while making serialized tables and chart coordinates stable.
    def rounded(value):
        if isinstance(value, float): return round(value, 10)
        if isinstance(value, dict): return {key: rounded(item) for key, item in value.items()}
        if isinstance(value, list): return [rounded(item) for item in value]
        return value
    results = rounded(results)
    # The unscaled liblinear sensitivity can vary at sub-microprobability
    # levels even with a fixed seed and tighter stopping rule. Its Brier and
    # calibration summaries are serialized to six decimals; other metrics
    # retain ten. Decisions and rankings were computed before this step.
    for result in results.values():
        for comparison in result["comparisons"]:
            if comparison["strategy"] == "no_scaling":
                for row in comparison["folds"]:
                    row["brier"] = round(row["brier"], 6)
                comparison["oof"]["brier"] = round(comparison["oof"]["brier"], 6)
                comparison["fold_mean"]["brier"] = round(comparison["fold_mean"]["brier"], 6)
                comparison["fold_sd"]["brier"] = round(comparison["fold_sd"]["brier"], 6)
        for row in result["calibration"]:
            if row["strategy"] == "no_scaling":
                row["mean_score"] = round(row["mean_score"], 6)
    for task, result in results.items():
        (out/f"{task}.json").write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    comparison = [{"task": task, "strategy": c["strategy"], "algorithm": c["algorithm"],
                   **{f"oof_{m}": c["oof"][m] for m in METRICS},
                   **{f"fold_sd_{m}": c["fold_sd"][m] for m in METRICS}}
                  for task, r in results.items() for c in r["comparisons"]]
    pd.DataFrame(comparison).to_csv(out/"comparisons.csv", index=False)
    pd.DataFrame([{"task": task, **row} for task,r in results.items() for row in r["subgroups"]]).to_csv(out/"subgroups.csv",index=False)
    pd.DataFrame([{"task": task, **row} for task,r in results.items() for row in r["importance"]]).to_csv(out/"importance.csv",index=False)
    pd.DataFrame([{"task": task, **row} for task,r in results.items() for row in r["threshold_sensitivity"]]).to_csv(out/"thresholds.csv",index=False)
    pd.DataFrame([{"task": task, **row} for task,r in results.items() for row in r["importance_rank_comparisons"]]).to_csv(out/"importance_stability.csv",index=False)
    for task, r in results.items():
        primary = TASKS[task].selection_score
        fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
        rows = r["comparisons"]
        ax.errorbar([c["fold_mean"][primary] for c in rows], range(len(rows)),
                    xerr=[c["fold_sd"][primary] for c in rows], fmt="o", capsize=3)
        ax.set_yticks(range(len(rows)), [c["strategy"].replace("_", " ") for c in rows]); ax.invert_yaxis()
        ax.set_xlabel(f"Development fold {primary}: mean ± SD"); ax.set_title(f"{task.title()} preprocessing comparison")
        fig.savefig(out/f"{task}_comparison.png", dpi=200); plt.close(fig)
        fig, ax = plt.subplots(figsize=(7, 5), layout="constrained")
        ax.plot([x["mean_score"] for x in r["calibration"]], [x["observed_rate"] for x in r["calibration"]], "o-")
        ax.plot([0,1],[0,1],"--",color="gray"); ax.set(xlim=(0,1),ylim=(0,1),xlabel="Mean OOF score",ylabel="Observed fraction",title=f"{task.title()} baseline calibration (development)")
        fig.savefig(out/f"{task}_calibration.png",dpi=200); plt.close(fig)
    (out/"run.log").write_text("Phase VII development-only experiment completed.\n"
                               + "Command: .venv/bin/python -m mediscope.ml.phase7\n"
                               + "Thread pool limit: 1\n"
                               + "Tasks: heart, diabetes, stroke\n"
                               + "Frozen split SHA-256: " + json.dumps({task:r["split_sha256"] for task,r in results.items()},sort_keys=True) + "\n"
                               + "Exported comparison rows: " + str(len(comparison)) + "\n")
    manifest = {"version":"phase7-v1", "seed":SEED, "software":{"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,"scipy":scipy.__version__,"scikit_learn":sklearn.__version__},
                "phase4_split_sha256":{task:r["split_sha256"] for task,r in results.items()},
                "source_sha256":{task:r["source"]["raw_sha256"] for task,r in results.items()},
                "artifacts":{str(p.relative_to(root)):sha256(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!="manifest.json"}}
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {"tasks":list(results),"artifacts":len(manifest["artifacts"])}


if __name__ == "__main__":
    print(json.dumps(export(), indent=2))
