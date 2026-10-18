"""Aggregate-only, source-verified exports shared by Power BI and local dashboard."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from ..cli import PROJECT_ROOT, sha256

EXPORT_VERSION = "v1"
EXPORT_NAMES = (
    "dataset_dimension", "dataset_overview", "outcomes", "numeric_summary", "categorical_frequencies",
    "histogram_bins", "boxplot_stats", "correlations", "categorical_associations",
    "hypotheses", "quality_metrics", "age_groups", "diabetes_symptoms",
    "stroke_risk_factors", "synthea_encounter_classes", "synthea_monthly_encounters",
    "synthea_encounters_per_patient", "synthea_age_at_encounter", "note_terms",
)
COUNT_COLUMNS = {"count", "rows", "n", "nonmissing_n", "all_n", "group_n", "yes_n", "class_n", "missing_n", "missing_cells", "exact_duplicates", "exact_duplicates_retained", "records", "stroke_positive", "positive_n", "negative_n", "encounters", "patients", "stroke_positive_n", "stroke_negative_n"}
PERCENT_COLUMNS = {"pct_all", "pct_nonmissing", "pct_within_age_group", "yes_pct", "stroke_pct", "missing_pct"}


class ExportError(ValueError):
    """Portable export contract failed validation."""


def _read_csv(path: Path) -> Any:
    import pandas as pd

    return pd.read_csv(path)


def _clean(value: Any) -> Any:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return value.item() if hasattr(value, "item") else value


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _clean(row.get(column, "")) for column in columns})


def _histogram(frame: Any, dataset_id: str, feature: str, outcome: str, edges: list[float]) -> list[dict[str, Any]]:
    import numpy as np
    import pandas as pd

    rows: list[dict[str, Any]] = []
    for label, part in frame.groupby(outcome, sort=True):
        values = pd.to_numeric(part[feature], errors="coerce").dropna().to_numpy()
        counts, boundaries = np.histogram(values, bins=edges)
        for i, count in enumerate(counts):
            rows.append({"dataset_id": dataset_id, "feature": feature, "outcome": str(label), "bin_start": float(boundaries[i]),
                         "bin_end": float(boundaries[i + 1]), "bin_label": f"{boundaries[i]:g}–{boundaries[i+1]:g}", "count": int(count),
                         "nonmissing_group_n": len(values)})
    return rows


def _quality_rows(dataset_id: str, quality: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for member, table in quality["tables"].items():
        for feature in table["final"]["columns"]:
            rows.append({"dataset_id": dataset_id, "table_name": Path(member).stem, "feature": feature,
                         "rows": table["final"]["rows"], "missing_n": table["final"]["missing"].get(feature, 0),
                         "missing_pct": 100 * table["final"]["missing"].get(feature, 0) / table["final"]["rows"],
                         "iqr_outliers_n": table["outliers_after"].get(feature, {}).get("count", ""),
                         "exact_duplicates_retained": table["duplicates"]["retained"]})
    return rows


def build_exports(root: Path = PROJECT_ROOT, notes_dir: Path | None = None) -> dict[str, Any]:
    """Write safe aggregates after checking all Phase I and II evidence."""
    import pandas as pd
    from ..eda.runner import load_prepared
    export_dir = root / "powerbi" / "exports" / EXPORT_VERSION
    export_dir.mkdir(parents=True, exist_ok=True)
    eda_tables = root / "reports" / "tables" / "eda"
    sources: dict[str, Any] = {}
    collections: dict[str, list[dict[str, Any]]] = {name: [] for name in EXPORT_NAMES}
    for dataset_id in ("uci_cleveland_heart", "uci_early_diabetes", "kaggle_stroke", "synthea_csv"):
        frames, quality, item = load_prepared(dataset_id, root)
        eda_path = root / "reports" / "eda" / f"{dataset_id}.json"
        if not eda_path.is_file():
            raise ExportError(f"Phase II report missing: {eda_path}")
        report = json.loads(eda_path.read_text(encoding="utf-8"))
        if report["source_sha256"] != quality["source"]["sha256"]:
            raise ExportError(f"Phase II provenance differs from Phase I for {dataset_id}")
        sources[dataset_id] = {"raw_sha256": quality["source"]["sha256"], "eda_sha256": sha256(eda_path),
                               "prepared_sha256": {member: info["prepared_sha256"] for member, info in quality["outputs"].items()},
                               "source_url": item["original_url"], "records": item["records"]}
        collections["dataset_dimension"].append({"dataset_id": dataset_id, "display_name": item["name"],
                "source_url": item["original_url"], "provenance": item["records"], "synthetic": int(item["records"] == "synthetic")})
        for member, frame in frames.items():
            collections["dataset_overview"].append({"dataset_id": dataset_id, "table_name": Path(member).stem,
                 "display_name": item["name"], "analysis_unit": "synthetic patient" if member.endswith("patients.csv") else "synthetic encounter" if member.endswith("encounters.csv") else "source record",
                 "rows": len(frame), "columns": len(frame.columns), "synthetic": int(item["records"] == "synthetic"),
                 "exact_duplicates": int(frame.duplicated().sum()), "missing_cells": int(frame.isna().sum().sum())})
        collections["quality_metrics"].extend(_quality_rows(dataset_id, quality))
        for export_name, suffix in (("outcomes", "outcome"), ("numeric_summary", "numeric_by_outcome"),
                                    ("categorical_frequencies", "categorical_by_outcome"),
                                    ("correlations", "correlations"), ("categorical_associations", "categorical_associations"),
                                    ("hypotheses", "hypotheses")):
            path = eda_tables / f"{dataset_id}_{suffix}.csv"
            if path.is_file():
                for row in _read_csv(path).to_dict("records"):
                    collections[export_name].append({"dataset_id": dataset_id, **row})
        if dataset_id == "uci_cleveland_heart":
            heart = next(iter(frames.values()))
            collections["histogram_bins"].extend(_histogram(heart, dataset_id, "age", "heart_disease_binary", list(range(20, 91, 5))))
            collections["age_groups"].extend(_age_groups(heart, dataset_id, "age", "heart_disease_binary", [0, 40, 60, 80, 121], ["<40", "40–59", "60–79", "80+"]))
        elif dataset_id == "uci_early_diabetes":
            diabetes = next(iter(frames.values()))
            collections["histogram_bins"].extend(_histogram(diabetes, dataset_id, "Age", "class", list(range(10, 101, 5))))
            collections["age_groups"].extend(_age_groups(diabetes, dataset_id, "Age", "class", [0, 40, 60, 80, 121], ["<40", "40–59", "60–79", "80+"]))
            collections["diabetes_symptoms"].extend({"dataset_id": dataset_id, **row} for row in _read_csv(eda_tables / f"{dataset_id}_symptom_yes_by_class.csv").to_dict("records"))
        elif dataset_id == "kaggle_stroke":
            stroke = next(iter(frames.values()))
            collections["histogram_bins"].extend(_histogram(stroke, dataset_id, "age", "stroke", list(range(0, 91, 5))))
            collections["histogram_bins"].extend(_histogram(stroke, dataset_id, "avg_glucose_level", "stroke", list(range(50, 301, 10))))
            collections["histogram_bins"].extend(_histogram(stroke, dataset_id, "bmi", "stroke", list(range(0, 111, 5))))
            collections["age_groups"].extend(_age_groups(stroke, dataset_id, "age", "stroke", [0, 18, 40, 60, 80, 121], ["<18", "18–39", "40–59", "60–79", "80+"]))
            for factor in ("hypertension", "heart_disease"):
                for value, part in stroke.groupby(factor, sort=True):
                    collections["stroke_risk_factors"].append({"dataset_id": dataset_id, "factor": factor, "value": int(value),
                        "records": len(part), "stroke_positive": int(part["stroke"].sum()), "stroke_pct": 100 * part["stroke"].mean()})
        else:
            for name, suffix in (("synthea_encounter_classes", "encounter_class"),
                                 ("synthea_monthly_encounters", "monthly_encounters"),
                                 ("synthea_encounters_per_patient", "encounters_per_patient_distribution")):
                collections[name].extend({"dataset_id": dataset_id, **row} for row in _read_csv(eda_tables / f"{dataset_id}_{suffix}.csv").to_dict("records"))
            encounters = frames["csv/encounters.csv"]
            patients = frames["csv/patients.csv"]
            birth = pd.to_datetime(patients.set_index("Id")["BIRTHDATE"], utc=True)
            age = (pd.to_datetime(encounters["START"], utc=True).reset_index(drop=True) - encounters["PATIENT"].map(birth).reset_index(drop=True)).dt.days / 365.2425
            valid = age.where(age.between(0, 120)).dropna()
            counts = pd.cut(valid, [0, 18, 40, 60, 80, 121], labels=["<18", "18–39", "40–59", "60–79", "80+"], right=False).value_counts().sort_index()
            collections["synthea_age_at_encounter"].extend({"dataset_id": dataset_id, "age_group": str(group), "encounters": int(count)} for group, count in counts.items())
    for row in collections["numeric_summary"]:
        collections["boxplot_stats"].append({key: row.get(key, "") for key in ("dataset_id", "group", "feature", "n", "min", "q1", "median", "q3", "max", "iqr")})
    if notes_dir is not None:
        from .notes import note_terms, write_wordcloud

        collections["note_terms"], note_info = note_terms(notes_dir)
        note_info.update({"generator_release": "Synthea v3.4.0", "generator_jar_sha256": "38678aab1e667d26671163824aad60ee5e30fa366f3d59d5ea5765ebb5702432",
                          "seed": 424242, "clinician_seed": 424242, "population_size": 10, "reference_date": "2024-01-01", "end_date": "2024-01-01",
                          "generator_reported_version": "v3.3.0-96-g17dd17e93", "state": "Massachusetts",
                          "generator_url": "https://github.com/synthetichealth/synthea/releases/tag/v3.4.0"})
        (root / "data" / "metadata" / "synthea_note_source.json").write_text(json.dumps(note_info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cloud_dir = root / "reports" / "figures" / "phase3"
        cloud_dir.mkdir(parents=True, exist_ok=True)
        write_wordcloud(collections["note_terms"], cloud_dir / "synthea_independent_note_wordcloud")
    else:
        existing = export_dir / "note_terms.csv"
        if existing.is_file():
            collections["note_terms"] = _read_csv(existing).to_dict("records")
    schemas = _export_schemas()
    files = {}
    for name in EXPORT_NAMES:
        path = export_dir / f"{name}.csv"
        _write_csv(path, collections[name], schemas[name])
        files[path.name] = {"sha256": sha256(path), "rows": len(collections[name]), "columns": schemas[name]}
    manifest = {"schema_version": 1, "export_version": EXPORT_VERSION, "description": "Aggregate-only Phase III visualization snapshot; no raw records or identifiers",
                "sources": sources, "files": files, "notes_status": "independent Synthea v3.4.0 run; see data/metadata/synthea_note_source.json" if collections["note_terms"] else "unavailable"}
    (export_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    return {"directory": str(export_dir), "files": len(files), "rows": {name: len(rows) for name, rows in collections.items()}}


def _age_groups(frame: Any, dataset_id: str, age: str, outcome: str, bins: list[int], labels: list[str]) -> list[dict[str, Any]]:
    import pandas as pd
    groups = pd.cut(frame[age], bins=bins, labels=labels, right=False)
    result = []
    for label, part in frame.groupby(groups, observed=False):
        counts = part[outcome].value_counts()
        for outcome_value, count in counts.items():
            result.append({"dataset_id": dataset_id, "age_group": str(label), "outcome": str(outcome_value),
                           "count": int(count), "group_n": len(part), "pct_within_age_group": 100 * count / len(part) if len(part) else 0})
    return result


def _export_schemas() -> dict[str, list[str]]:
    return {
        "dataset_dimension": ["dataset_id", "display_name", "source_url", "provenance", "synthetic"],
        "dataset_overview": ["dataset_id", "table_name", "display_name", "analysis_unit", "rows", "columns", "synthetic", "exact_duplicates", "missing_cells"],
        "outcomes": ["dataset_id", "group", "feature", "category", "count", "nonmissing_n", "all_n", "pct_all", "pct_nonmissing"],
        "numeric_summary": ["dataset_id", "group", "feature", "rows", "n", "missing_n", "missing_pct", "mean", "median", "mode", "min", "max", "range", "q1", "q3", "iqr", "variance", "std", "skewness"],
        "categorical_frequencies": ["dataset_id", "group", "feature", "category", "count", "nonmissing_n", "all_n", "pct_all", "pct_nonmissing"],
        "histogram_bins": ["dataset_id", "feature", "outcome", "bin_start", "bin_end", "bin_label", "count", "nonmissing_group_n"],
        "boxplot_stats": ["dataset_id", "group", "feature", "n", "min", "q1", "median", "q3", "max", "iqr"],
        "correlations": ["dataset_id", "method", "left", "right", "n", "coefficient", "p_value", "missing_policy", "bh_q_value"],
        "categorical_associations": ["dataset_id", "feature", "target", "n", "levels", "target_levels", "chi2", "dof", "p_value", "cramers_v", "minimum_expected", "expected_below_5", "missing_policy", "bh_q_value"],
        "hypotheses": ["dataset_id", "id", "method", "feature", "target", "positive_label", "negative_label", "positive_n", "negative_n", "positive_mean", "negative_mean", "positive_sd", "negative_sd", "positive_median", "negative_median", "positive_skew", "negative_skew", "mean_difference", "statistic", "df", "p_value", "effect_size", "effect_name", "ci_low", "ci_high", "ci_parameter", "alpha", "sensitivity_method", "sensitivity_p_value", "missing_policy", "assumptions", "stroke_positive_n", "stroke_negative_n", "stroke_risk_hypertension", "stroke_risk_no_hypertension", "risk_difference", "minimum_expected", "phi"],
        "quality_metrics": ["dataset_id", "table_name", "feature", "rows", "missing_n", "missing_pct", "iqr_outliers_n", "exact_duplicates_retained"],
        "age_groups": ["dataset_id", "age_group", "outcome", "count", "group_n", "pct_within_age_group"],
        "diabetes_symptoms": ["dataset_id", "symptom", "class", "yes_n", "class_n", "yes_pct"],
        "stroke_risk_factors": ["dataset_id", "factor", "value", "records", "stroke_positive", "stroke_pct"],
        "synthea_encounter_classes": ["dataset_id", "group", "feature", "category", "count", "nonmissing_n", "all_n", "pct_all", "pct_nonmissing"],
        "synthea_monthly_encounters": ["dataset_id", "month", "encounters"],
        "synthea_encounters_per_patient": ["dataset_id", "encounters", "patients"],
        "synthea_age_at_encounter": ["dataset_id", "age_group", "encounters"],
        "note_terms": ["term", "count", "source_id"],
    }


def verify_exports(root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Check tracked snapshot without requiring raw archives or prepared rows."""
    export_dir = root / "powerbi" / "exports" / EXPORT_VERSION
    manifest_path = export_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ExportError(f"Missing export manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("export_version") != EXPORT_VERSION or set(manifest.get("files", {})) != {f"{name}.csv" for name in EXPORT_NAMES}:
        raise ExportError("Export manifest version or file set mismatch")
    schemas = _export_schemas()
    for name in EXPORT_NAMES:
        path = export_dir / f"{name}.csv"
        info = manifest["files"][path.name]
        if not path.is_file() or sha256(path) != info["sha256"]:
            raise ExportError(f"Missing or changed export: {path}")
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != schemas[name]:
                raise ExportError(f"Export schema mismatch: {path}")
            rows = list(reader)
        if len(rows) != info["rows"]:
            raise ExportError(f"Export row count mismatch: {path}")
        for row in rows:
            for column in COUNT_COLUMNS.intersection(row):
                if row[column]:
                    try:
                        parsed = float(row[column])
                    except ValueError as exc:
                        raise ExportError(f"Non-integer count in {path}: {column}") from exc
                    if not math.isfinite(parsed) or not parsed.is_integer():
                        raise ExportError(f"Non-integer count in {path}: {column}")
                    value = int(parsed)
                    if value < 0:
                        raise ExportError(f"Negative count in {path}: {column}")
            for column in PERCENT_COLUMNS.intersection(row):
                if row[column]:
                    try:
                        value = float(row[column])
                    except ValueError as exc:
                        raise ExportError(f"Non-numeric percentage in {path}: {column}") from exc
                    if not math.isfinite(value) or not 0 <= value <= 100:
                        raise ExportError(f"Invalid percentage in {path}: {column}")
    return {"status": "PASS", "version": EXPORT_VERSION, "files": len(EXPORT_NAMES), "source_archives_required": False}
