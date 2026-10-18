"""Deterministic Phase II orchestration and evidence exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..cli import PROJECT_ROOT, load_registry, sha256
from ..schema import DIABETES, DIABETES_SYMPTOMS, ENCOUNTERS, HEART, PATIENTS, STROKE, TableSchema
from . import figures
from .hypotheses import hypertension_test, welch_test
from .stats import categorical_associations, categorical_summary, numeric_associations, numeric_summary


class EDAError(ValueError):
    """Prepared-data provenance or schema is insufficient for EDA."""


FILES = {
    "uci_cleveland_heart": {"processed.cleveland.data": ("heart.csv", HEART)},
    "uci_early_diabetes": {"diabetes_data_upload.csv": ("diabetes.csv", DIABETES)},
    "kaggle_stroke": {"healthcare-dataset-stroke-data.csv": ("stroke.csv", STROKE)},
    "synthea_csv": {"csv/patients.csv": ("synthea_patients.csv", PATIENTS), "csv/encounters.csv": ("synthea_encounters.csv", ENCOUNTERS)},
}
TARGETS = {"uci_cleveland_heart": "heart_disease_binary", "uci_early_diabetes": "class", "kaggle_stroke": "stroke"}
POSITIVE = {"uci_cleveland_heart": 1, "uci_early_diabetes": "Positive", "kaggle_stroke": 1}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _write_table(path: Path, rows: list[dict[str, Any]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, lineterminator="\n")


def load_prepared(dataset_id: str, root: Path = PROJECT_ROOT) -> tuple[dict[str, pd.DataFrame], dict[str, Any], dict[str, Any]]:
    """Verify each CSV against Phase I quality SHA and ordered output schema."""
    registry = {item["id"]: item for item in load_registry()["datasets"]}
    if dataset_id not in FILES:
        raise EDAError(f"Unknown dataset {dataset_id!r}; choose {list(FILES)} or all")
    item = registry[dataset_id]
    quality_path = root / "reports" / "quality" / f"{dataset_id}.json"
    if not quality_path.is_file():
        raise EDAError(f"Missing Phase I quality report: {quality_path}; run mediscope prepare first")
    quality = json.loads(quality_path.read_text(encoding="utf-8"))
    if quality["source"]["sha256"] != item["sha256"]:
        raise EDAError(f"Phase I source checksum disagrees with registry for {dataset_id}")
    frames = {}
    for member, (filename, _) in FILES[dataset_id].items():
        path = root / "data" / "processed" / filename
        if not path.is_file():
            raise EDAError(f"Missing prepared table: {path}; run mediscope prepare --dataset {dataset_id}")
        expected = quality["outputs"][member]["prepared_sha256"]
        if sha256(path) != expected:
            raise EDAError(f"Prepared table checksum mismatch: {path}; rerun Phase I verification")
        frame = pd.read_csv(path)
        if list(frame.columns) != quality["tables"][member]["final"]["columns"] or len(frame) != quality["tables"][member]["final"]["rows"]:
            raise EDAError(f"Prepared table schema or row count mismatch: {path}")
        frames[member] = frame
    if dataset_id == "uci_cleveland_heart" and not (frames["processed.cleveland.data"]["heart_disease_binary"] == frames["processed.cleveland.data"]["num"].gt(0).astype(int)).all():
        raise EDAError("Cleveland derived target disagrees with original num")
    if dataset_id in TARGETS:
        target = TARGETS[dataset_id]
        frame = next(iter(frames.values()))
        allowed = {"Negative", "Positive"} if dataset_id == "uci_early_diabetes" else {0, 1}
        if frame[target].isna().any() or set(frame[target].unique()) != allowed:
            raise EDAError(f"Target {target} is missing or outside its required two classes")
    if dataset_id == "synthea_csv":
        patients, encounters = frames.values()
        if patients["Id"].duplicated().any() or encounters["Id"].duplicated().any() or (~encounters["PATIENT"].isin(patients["Id"])).any():
            raise EDAError("Synthea patient/encounter keys are invalid")
    return frames, quality, item


def _save_tables(dataset_id: str, tables: dict[str, list[dict[str, Any]]], root: Path) -> dict[str, str]:
    directory = root / "reports" / "tables" / "eda"
    directory.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, rows in tables.items():
        if rows:
            path = directory / f"{dataset_id}_{name}.csv"
            _write_table(path, rows)
            paths[name] = str(path.relative_to(root))
    return paths


def _standard_tables(frame: pd.DataFrame, schema: TableSchema, target: str | None) -> tuple[dict[str, list[dict[str, Any]]], dict[str, pd.DataFrame], dict[str, Any]]:
    numeric = tuple(schema.continuous)
    categorical = tuple(schema.binary) + schema.nominal + tuple(schema.ordinal)
    tables = {"numeric": numeric_summary(frame, numeric), "categorical": categorical_summary(frame, categorical)}
    if target:
        tables["outcome"] = categorical_summary(frame, (target,))
        tables["numeric_by_outcome"] = numeric_summary(frame, numeric, target)
        tables["categorical_by_outcome"] = categorical_summary(frame, categorical, target)
    association_numeric = tuple(c for c in numeric if c not in ("LAT", "LON"))
    correlation_frame = frame.assign(class_binary=(frame["class"] == "Positive").astype(int)) if target == "class" else frame
    correlation_target = "class_binary" if target == "class" else target
    correlation, matrices, skipped_numeric = numeric_associations(correlation_frame, association_numeric, correlation_target)
    tables["correlations"] = correlation
    if target:
        association, skipped_cat = categorical_associations(frame, categorical, target)
        tables["categorical_associations"] = association
    else:
        skipped_cat = []
    return tables, matrices, {"constant_numeric": skipped_numeric, "constant_categorical": skipped_cat,
                               "numeric_policy": "registered continuous features only; pairwise complete cases; exploratory p-values BH-adjusted within table",
                               "categorical_policy": "registered binary/nominal features only; complete cases; exploratory p-values BH-adjusted within table; small expected cells flagged"}


def _disease_extra(dataset_id: str, frame: pd.DataFrame, quality: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    extra: dict[str, list[dict[str, Any]]] = {}
    facts: dict[str, Any] = {}
    if dataset_id == "uci_cleveland_heart":
        extra["original_num"] = categorical_summary(frame, ("num",))
        facts["target_rule"] = "heart_disease_binary = 1 when original num > 0; num remains available but is not analyzed as continuous"
    elif dataset_id == "uci_early_diabetes":
        extra["symptom_yes_by_class"] = [{"symptom": c, "class": label, "yes_n": int((part[c] == "Yes").sum()), "class_n": len(part), "yes_pct": 100 * (part[c] == "Yes").mean()}
                                         for c in DIABETES_SYMPTOMS for label, part in frame.groupby("class", sort=True)]
        duplicates = int(frame.duplicated().sum())
        unique = frame.drop_duplicates()
        facts["identical_profiles"] = duplicates
        facts["distinct_profiles"] = len(unique)
        facts["independence_warning"] = "No participant identifier: identical profiles may be distinct people or repeat records. Retained; inferential independence cannot be verified."
        extra["unique_profile_class_counts"] = categorical_summary(unique, ("class",))
    elif dataset_id == "kaggle_stroke":
        bins = [-np.inf, 18, 40, 60, 80, np.inf]
        labels = ["<18", "18–39", "40–59", "60–79", "80+"]
        grouped = frame.assign(age_group=pd.cut(frame["age"], bins=bins, labels=labels, right=False))
        extra["age_group_by_stroke"] = categorical_summary(grouped, ("age_group",), "stroke")
        extra["hypertension_by_stroke"] = categorical_summary(frame, ("hypertension",), "stroke")
        extra["heart_disease_by_stroke"] = categorical_summary(frame, ("heart_disease",), "stroke")
        extra["smoking_by_stroke"] = categorical_summary(frame, ("smoking_status",), "stroke")
        facts["stroke_positive_pct"] = 100 * (frame["stroke"] == 1).mean()
        facts["smoking_unknown_recast_missing"] = quality["tables"]["healthcare-dataset-stroke-data.csv"]["final"]["missing"]["smoking_status"]
        facts["imbalance_warning"] = "Class imbalance makes accuracy alone misleading in later modeling; no model is trained in Phase II."
    return extra, facts


def synthea_relationships(patients: pd.DataFrame, encounters: pd.DataFrame) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Count people by patient ID and visits by encounter ID without fanout."""
    count = encounters.groupby("PATIENT").size().reindex(patients["Id"], fill_value=0)
    birth = pd.to_datetime(patients.set_index("Id")["BIRTHDATE"], errors="coerce", utc=True)
    start = pd.to_datetime(encounters["START"], errors="coerce", utc=True)
    age = (start.reset_index(drop=True) - encounters["PATIENT"].map(birth).reset_index(drop=True)).dt.total_seconds() / (365.2425 * 86400)
    valid_age = age.where(age.between(0, 120))
    monthly = start.dt.tz_localize(None).dt.to_period("M").value_counts().sort_index()
    reason = encounters["REASONDESCRIPTION"].fillna("<missing>").value_counts()
    tables = {
        "encounters_per_patient_distribution": [{"encounters": int(k), "patients": int(v)} for k, v in count.value_counts().sort_index().items()],
        "encounter_class": categorical_summary(encounters, ("ENCOUNTERCLASS",)),
        "encounter_age": numeric_summary(pd.DataFrame({"age_at_encounter": valid_age}), ("age_at_encounter",)),
        "monthly_encounters": [{"month": str(k), "encounters": int(v)} for k, v in monthly.items()],
        "reason_description_top": [{"description": str(k), "encounters": int(v)} for k, v in reason.head(15).items()],
    }
    facts = {"distinct_patients": int(patients["Id"].nunique()), "encounters": int(encounters["Id"].nunique()),
             "patients_with_zero_encounters": int((count == 0).sum()), "mean_encounters_per_patient": float(count.mean()),
             "median_encounters_per_patient": float(count.median()), "orphan_encounters": int((~encounters["PATIENT"].isin(patients["Id"])).sum()),
             "valid_age_at_encounter_n": int(valid_age.notna().sum()), "invalid_or_missing_age_at_encounter_n": int(valid_age.isna().sum()),
             "valid_start_dates": int(start.notna().sum()), "reason_code_nonmissing_n": int(encounters["REASONCODE"].notna().sum()),
             "interpretation": "All records are simulated. Encounter counts are visits, not distinct people or disease incidence."}
    return tables, {**facts, "_age_series": valid_age, "_encounters_series": count, "_monthly_series": monthly}


def _markdown(report: dict[str, Any]) -> str:
    lines = [f"# Phase II EDA: {report['dataset_name']}", "", f"Source: {report['source_url']}",
             f"Provenance: {report['records']}; source SHA-256 `{report['source_sha256']}`.", "",
             "Research and education only. Associations do not establish causation or clinical validity.", "",
             "## Data and methods", ""]
    for name, item in report["tables"].items():
        lines.append(f"- {name}: {item['rows']:,} rows × {item['columns']} columns; exact duplicate rows {item['exact_duplicates']:,}.")
    lines += ["", "Continuous summaries use nonmissing denominators and sample variance. Numeric correlations use only registered continuous features and pairwise complete cases. Categorical tests use complete cases; exploratory p-values have within-table Benjamini–Hochberg adjustments. Missing categories remain explicit in frequency tables. No imputation was performed.", ""]
    for key, value in report["facts"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Strongest observed associations", ""]
    if report["strongest_associations"]:
        for row in report["strongest_associations"]:
            lines.append(f"- {row['description']}")
    else:
        lines.append("- No eligible nonconstant pair was available.")
    if report["hypotheses"]:
        lines += ["", "## Preregistered hypothesis tests", ""]
        for h in report["hypotheses"]:
            lines += [f"### {h['id']}: {h['question']}", "", f"H0: {h['null']}", f"H1: {h['alternative']}", "",
                      f"Method: {h['method']}; alpha={h['alpha']}; {h['assumptions']}",
                      f"Observed statistic={h['statistic']:.6g}, p={h['p_value']:.6g}; {h['effect_name']}={h['effect_size']:.6g}; {100 * (1 - h['alpha']):g}% CI for {h['ci_parameter']}: [{h['ci_low']:.6g}, {h['ci_high']:.6g}].", "",
                      (f"Groups: positive n={h['positive_n']}, mean={h['positive_mean']:.3f}, SD={h['positive_sd']:.3f}; negative n={h['negative_n']}, mean={h['negative_mean']:.3f}, SD={h['negative_sd']:.3f}; trimmed sensitivity p={h['sensitivity_p_value']:.6g}." if h['id'] != 'H2' else f"Contingency cells (hypertension × stroke): {h['table']}; expected minimum={h['minimum_expected']:.3f}; phi={h['phi']:.3f}."), "",
                      h["interpretation"], "", f"Sampling limitation: {h['limitation']}", ""]
    lines += ["## Evidence paths", ""]
    lines += [f"- {path}" for path in list(report["table_paths"].values()) + report["figure_paths"]]
    return "\n".join(lines) + "\n"


def _annotate_hypothesis(h: dict[str, Any], item: dict[str, Any]) -> None:
    questions = {
        "H1": ("Does mean age differ by recorded heart disease?", "Population mean ages are equal.", "Population mean ages differ.", "Historical, small, nonrandom Cleveland sample; patient independence is assumed, not demonstrable."),
        "H2": ("Is hypertension associated with stroke status?", "Hypertension and stroke are independent.", "Hypertension and stroke are associated.", "Stroke source collection is unverified; cross-sectional association cannot establish temporal or causal direction."),
        "H3": ("Does mean average glucose differ by stroke status?", "Population mean glucose levels are equal.", "Population mean glucose levels differ.", "Stroke source collection is unverified; skew, outliers and nonrandom sampling limit population inference.")}
    question, null, alternative, limitation = questions[h["id"]]
    h.update(question=question, null=null, alternative=alternative, limitation=limitation)
    decision = "reject H0" if h["p_value"] < h["alpha"] else "do not reject H0"
    if h["id"] == "H2":
        h["interpretation"] = f"At alpha={h['alpha']}, {decision}. Observed stroke proportions were {h['stroke_risk_hypertension']:.2%} with hypertension and {h['stroke_risk_no_hypertension']:.2%} without (difference {h['risk_difference']:.2%}). The odds ratio and its interval describe magnitude; statistical significance alone does not establish clinical importance or causation."
    else:
        h["interpretation"] = f"At alpha={h['alpha']}, {decision}. Mean {h['feature']} was {h['positive_mean']:.2f} in the positive group (n={h['positive_n']}) and {h['negative_mean']:.2f} in the negative group (n={h['negative_n']}); difference {h['mean_difference']:.2f}. Consider the original units, effect size, CI and sampling limits for practical importance. The trimmed test is a sensitivity check, not a replacement primary test."


def run_dataset(dataset_id: str, alpha: float = 0.05, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    frames, quality, item = load_prepared(dataset_id, root)
    source = item["name"] + (" (synthetic)" if dataset_id == "synthea_csv" else "")
    table_rows: dict[str, list[dict[str, Any]]] = {}
    matrices: dict[str, pd.DataFrame] = {}
    skipped: dict[str, Any] = {}
    hypotheses: list[dict[str, Any]] = []
    facts: dict[str, Any] = {}
    fig_dir = root / "reports" / "figures" / "eda"
    fig_dir.mkdir(parents=True, exist_ok=True)
    figures_out: list[str] = []

    def make(name: str, function: Any, *args: Any) -> None:
        path = fig_dir / f"{dataset_id}_{name}.png"
        function(*args, path=path, source=source)
        figures_out.append(str(path.relative_to(root)))

    for member, frame in frames.items():
        filename, schema = FILES[dataset_id][member]
        prefix = Path(filename).stem if dataset_id == "synthea_csv" else ""
        target = TARGETS.get(dataset_id)
        standard, corr_matrices, note = _standard_tables(frame, schema, target)
        for name, rows in standard.items():
            table_rows[f"{prefix}_{name}".strip("_")] = rows
        skipped[prefix or dataset_id] = note
        for method, matrix in corr_matrices.items():
            if len(matrix):
                matrices[f"{prefix}_{method}".strip("_")] = matrix
        if target:
            extra, extra_facts = _disease_extra(dataset_id, frame, quality)
            table_rows.update(extra)
            facts.update(extra_facts)
            make("outcome", figures.outcome_bar, frame, target)
            age_feature = "Age" if dataset_id == "uci_early_diabetes" else "age"
            make("age_histogram", figures.grouped_hist, frame, age_feature, target, "years")
            make("age_boxplot", figures.grouped_box, frame, age_feature, target, "years")
            if dataset_id == "uci_cleveland_heart":
                make("chest_pain_frequency", figures.category_bar, frame, "cp", "Source chest-pain codes; no ordinal interpretation.")
                hypotheses.append(welch_test(frame, target, "age", 1, 0, alpha, "H1"))
            elif dataset_id == "uci_early_diabetes":
                make("gender_frequency", figures.category_bar, frame, "Gender", "Questionnaire gender labels.")
                make("polyuria_frequency", figures.category_bar, frame, "Polyuria", "Questionnaire symptom responses.")
                make("symptom_yes_by_class", figures.grouped_yes_rates, frame, DIABETES_SYMPTOMS, target)
            else:
                make("glucose_histogram", figures.grouped_hist, frame, "avg_glucose_level", target, "source unit unspecified")
                make("glucose_boxplot", figures.grouped_box, frame, "avg_glucose_level", target, "source unit unspecified")
                make("bmi_boxplot", figures.grouped_box, frame, "bmi", target, "kg/m²")
                make("smoking_frequency", figures.category_bar, frame, "smoking_status", "Unknown source responses appear as <missing>.")
                make("stroke_by_age_group", figures.age_group_rates, frame)
                hypotheses.extend((hypertension_test(frame, alpha), welch_test(frame, target, "avg_glucose_level", 1, 0, alpha, "H3")))
        else:
            if member.endswith("patients.csv"):
                make("patient_gender_frequency", figures.category_bar, frame, "GENDER", "Simulated patients; one row per patient.")
            else:
                make("encounter_class_frequency", figures.category_bar, frame, "ENCOUNTERCLASS", "Simulated visits; patients can repeat.")
    if dataset_id == "synthea_csv":
        patients, encounters = frames.values()
        extra, relationship = synthea_relationships(patients, encounters)
        table_rows.update(extra)
        make("encounters_per_patient", figures.simple_hist, relationship.pop("_encounters_series"), "encounters per patient", "visits")
        make("age_at_encounter", figures.simple_hist, relationship.pop("_age_series"), "age at encounter", "years")
        make("monthly_encounters", figures.temporal_bar, relationship.pop("_monthly_series"))
        facts.update(relationship)
    for key, matrix in matrices.items():
        path = root / "reports" / "tables" / "eda" / f"{dataset_id}_{key}_matrix.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        matrix.to_csv(path, lineterminator="\n")
        if len(matrix) >= 2:
            make(f"{key}_heatmap", figures.heatmap, matrix, key)
    for h in hypotheses:
        _annotate_hypothesis(h, item)
    if hypotheses:
        table_rows["hypotheses"] = [{key: value for key, value in h.items() if not isinstance(value, dict)} for h in hypotheses]
    paths = _save_tables(dataset_id, table_rows, root)
    for key in matrices:
        paths[f"{key}_matrix"] = str((root / "reports" / "tables" / "eda" / f"{dataset_id}_{key}_matrix.csv").relative_to(root))
    strongest: list[dict[str, str]] = []
    corrs = [r for name, rows in table_rows.items() if name.endswith("correlations") for r in rows if r.get("coefficient") is not None and r["left"] != r["right"]]
    for row in sorted(corrs, key=lambda r: abs(r["coefficient"]), reverse=True)[:3]:
        strongest.append({"description": f"{row['method']} {row['left']} vs {row['right']}: r={row['coefficient']:.3f}, n={row['n']}; exploratory association only."})
    assocs = [r for name, rows in table_rows.items() if name.endswith("categorical_associations") for r in rows if r.get("cramers_v") is not None]
    for row in sorted(assocs, key=lambda r: r["cramers_v"], reverse=True)[:2]:
        strongest.append({"description": f"{row['feature']} vs {row['target']}: Cramer's V={row['cramers_v']:.3f}, n={row['n']}, {row['expected_below_5']} expected cells <5; exploratory association only."})
    report = {"dataset_id": dataset_id, "dataset_name": item["name"], "source_url": item["original_url"], "records": item["records"],
              "source_sha256": quality["source"]["sha256"], "alpha": alpha,
              "tables": {member: {"rows": len(frame), "columns": len(frame.columns), "dtypes": {c: str(t) for c, t in frame.dtypes.items()},
                                  "missing": {c: int(n) for c, n in frame.isna().sum().items() if n}, "exact_duplicates": int(frame.duplicated().sum()),
                                  "prepared_sha256": quality["outputs"][member]["prepared_sha256"]} for member, frame in frames.items()},
              "facts": facts, "skipped_features_and_policies": skipped, "strongest_associations": strongest,
              "hypotheses": hypotheses, "table_paths": paths, "figure_paths": figures_out}
    report_dir = root / "reports" / "eda"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path, markdown_path = report_dir / f"{dataset_id}.json", report_dir / f"{dataset_id}.md"
    _write_json(json_path, report)
    markdown_path.write_text(_markdown(report), encoding="utf-8")
    return {"dataset_id": dataset_id, "report_json": str(json_path.relative_to(root)), "report_markdown": str(markdown_path.relative_to(root)),
            "tables": len(paths), "figures": len(figures_out), "hypotheses": [h["id"] for h in hypotheses]}


def run_eda(dataset_id: str = "all", alpha: float = 0.05, root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    """Run one registered dataset or all four without changing Phase I data."""
    if dataset_id != "all" and dataset_id not in FILES:
        raise EDAError(f"Unknown dataset {dataset_id!r}; choose {list(FILES)} or all")
    chosen = list(FILES) if dataset_id == "all" else [dataset_id]
    return [run_dataset(value, alpha, root) for value in chosen]
