"""Reproducible Phase I data preparation without learned full-data transforms."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .cli import PROJECT_ROOT, REGISTRY, load_registry, sha256
from .schema import SCHEMAS, TableSchema

DEFAULT_CONFIG = PROJECT_ROOT / "data" / "metadata" / "preparation_config.json"
OUTPUT_NAMES = {
    "processed.cleveland.data": "heart.csv",
    "diabetes_data_upload.csv": "diabetes.csv",
    "healthcare-dataset-stroke-data.csv": "stroke.csv",
    "csv/patients.csv": "synthea_patients.csv",
    "csv/encounters.csv": "synthea_encounters.csv",
}
STRICT_POSITIVE = {"trestbps", "chol", "thalach", "id", "avg_glucose_level", "bmi"}


class PreparationError(ValueError):
    """A source file or preparation rule violates its registered contract."""


@dataclass
class PreparedTable:
    """Prepared data plus its machine-readable quality comparison."""

    data: pd.DataFrame
    report: dict[str, Any]
    before: pd.DataFrame
    schema: TableSchema


def load_config(path: Path = DEFAULT_CONFIG) -> dict[str, Any]:
    """Read and validate the reproducible preparation configuration."""
    config = json.loads(path.read_text(encoding="utf-8"))
    choices = {
        "invalid_feature_policy": {"error", "nullify"},
        "exact_duplicate_policy": {"retain", "drop"},
        "outlier_policy": {"report_only"},
        "numeric_imputation": {"median", "mean", "most_frequent"},
        "categorical_imputation": {"most_frequent", "constant"},
        "numeric_scaling": {"standard", "minmax", "robust", "none"},
    }
    for key, accepted in choices.items():
        if config.get(key) not in accepted:
            raise PreparationError(f"Config {key} must be one of {sorted(accepted)}")
    if config["exact_duplicate_policy"] == "drop" and not config.get("duplicate_removal_justification", "").strip():
        raise PreparationError("Dropping exact duplicates requires duplicate_removal_justification")
    return config


def _source_dataset(dataset_id: str, registry_path: Path = REGISTRY) -> dict[str, Any]:
    for dataset in load_registry(registry_path)["datasets"]:
        if dataset["id"] == dataset_id:
            return dataset
    raise PreparationError(f"Unknown dataset {dataset_id!r}; use an ID from the registry")


def read_registered_table(bundle: zipfile.ZipFile, table: dict[str, Any], missing_tokens: list[str]) -> pd.DataFrame:
    """Validate ZIP member, required target, ordered header, and CSV row width."""
    member = table["member"]
    if member not in bundle.namelist():
        raise PreparationError(f"Required source member {member!r} is missing")
    expected = table["columns"]
    with bundle.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        observed = next(reader, []) if table["header"] else expected
        target = table.get("target")
        if target and target not in observed:
            raise PreparationError(f"Required target column {target!r} is missing from {member}")
        if observed != expected:
            raise PreparationError(f"Schema mismatch in {member}: expected columns {expected}, found {observed}")
        for line_number, row in enumerate(reader, start=2 if table["header"] else 1):
            if len(row) != len(expected):
                if target and expected.index(target) >= len(row):
                    raise PreparationError(f"Required target column {target!r} is missing at data line {line_number} in {member}")
                raise PreparationError(f"Schema mismatch in {member} at data line {line_number}: expected {len(expected)} fields, found {len(row)}")
    with bundle.open(member) as binary:
        frame = pd.read_csv(
            binary, header=0 if table["header"] else None,
            names=None if table["header"] else expected,
            dtype="string", keep_default_na=False, na_values=missing_tokens,
        )
    if frame.empty:
        raise PreparationError(f"Registered table {member} contains no records")
    return frame


def _canonical_category(series: pd.Series, column: str) -> pd.Series:
    """Normalize UCI Cleveland's integral codes from `1.0` to `1`."""
    if column not in {"sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"}:
        return series

    def canonical(value: Any) -> Any:
        if pd.isna(value):
            return pd.NA
        try:
            numeric = float(value)
            return str(int(numeric)) if numeric.is_integer() else str(value)
        except ValueError:
            return str(value)

    return series.map(canonical).astype("string")


def _invalid_findings(frame: pd.DataFrame, schema: TableSchema) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Return typed columns and masks for malformed or impossible values."""
    typed = frame.copy()
    findings: dict[str, Any] = {}
    for column, (low, high) in schema.numeric.items():
        original = frame[column]
        converted = pd.to_numeric(original, errors="coerce")
        malformed = original.notna() & converted.isna()
        impossible = pd.Series(False, index=frame.index)
        if low is not None:
            impossible |= converted.le(low) if column in STRICT_POSITIVE else converted.lt(low)
        if high is not None:
            impossible |= converted.gt(high)
        if column in schema.integer:
            impossible |= converted.notna() & converted.ne(converted.round())
        invalid = (malformed | impossible).fillna(False)
        left = "(" if low is None or column in STRICT_POSITIVE else "["
        right = ")" if high is None else "]"
        low_label = "−∞" if low is None else str(low)
        high_label = "+∞" if high is None else str(high)
        findings[column] = {"count": int(invalid.sum()), "rule": f"numeric in {left}{low_label}, {high_label}{right}" + (" and integer" if column in schema.integer else "")}
        typed[column] = converted.mask(invalid)
        if column in schema.integer:
            typed[column] = typed[column].astype("Int64")
    for column, allowed in schema.categories.items():
        values = _canonical_category(frame[column], column)
        invalid = (values.notna() & ~values.isin(allowed)).fillna(False)
        findings[column] = {"count": int(invalid.sum()), "rule": f"one of {list(allowed)}"}
        typed[column] = values.mask(invalid)
    for column in schema.dates:
        converted = pd.to_datetime(frame[column], errors="coerce", utc=True)
        invalid = (frame[column].notna() & converted.isna()).fillna(False)
        findings[column] = {"count": int(invalid.sum()), "rule": "parseable date/time"}
        typed[column] = frame[column].mask(invalid)
    return typed, findings


def _missing(frame: pd.DataFrame) -> dict[str, int]:
    return {column: int(count) for column, count in frame.isna().sum().items()}


def iqr_summary(frame: pd.DataFrame, columns: tuple[str, ...]) -> dict[str, dict[str, float | int | None]]:
    """Count IQR outliers on continuous columns; never classify codes or labels."""
    result: dict[str, dict[str, float | int | None]] = {}
    for column in columns:
        values = pd.to_numeric(frame[column], errors="coerce").dropna()
        if values.empty:
            result[column] = {"q1": None, "q3": None, "lower": None, "upper": None, "count": 0}
            continue
        q1, q3 = (float(values.quantile(q)) for q in (0.25, 0.75))
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        result[column] = {"q1": q1, "q3": q3, "lower": lower, "upper": upper, "count": int(((values < lower) | (values > upper)).sum())}
    return result


def prepare_table(frame: pd.DataFrame, dataset_id: str, member: str, config: dict[str, Any]) -> PreparedTable:
    """Apply deterministic validation, typing, and optional justified exact-row removal."""
    schema = SCHEMAS[dataset_id][member]
    initial = frame.copy()
    initial_missing = _missing(initial)
    actions: list[dict[str, Any]] = [
        {"operation": "parse_missing_tokens", "tokens": config["missing_tokens"], "rationale": "Recognize explicit source missing markers without filling values"},
        {"operation": "validate_and_cast_types", "rationale": "Apply registered numeric, categorical, date, and impossibility rules; retain null features"},
    ]
    if dataset_id == "kaggle_stroke" and config["stroke_unknown_smoking_as_missing"]:
        count = int((frame["smoking_status"] == "Unknown").sum())
        frame = frame.copy()
        frame.loc[frame["smoking_status"] == "Unknown", "smoking_status"] = pd.NA
        actions.append({"operation": "missing_response", "column": "smoking_status", "rows": count, "rationale": "Source 'Unknown' denotes unavailable smoking history"})
    normalized_missing = _missing(frame)
    typed, invalid = _invalid_findings(frame, schema)
    target = "num" if dataset_id == "uci_cleveland_heart" else "class" if dataset_id == "uci_early_diabetes" else "stroke" if dataset_id == "kaggle_stroke" else None
    if target and typed[target].isna().any():
        raise PreparationError(f"Required target {target!r} has missing or invalid values; target imputation is prohibited")
    for column in schema.required_text:
        if typed[column].isna().any():
            raise PreparationError(f"Required identifier/date {column!r} has missing or invalid values")
    invalid_columns = {column: item["count"] for column, item in invalid.items() if item["count"]}
    if invalid_columns and config["invalid_feature_policy"] == "error":
        raise PreparationError(f"Invalid source values in {member}: {invalid_columns}; use a justified nullify policy to retain rows")
    if invalid_columns:
        actions.append({"operation": "nullify_invalid_features", "counts": invalid_columns, "rationale": "Invalid feature values become missing; target and identifiers remain protected"})
    before = typed.copy()
    if dataset_id == "uci_cleveland_heart":
        actions.append({"operation": "canonicalize_cleveland_codes", "rationale": "Integral codes such as 1.0 are represented as category string 1"})
        typed["heart_disease_binary"] = typed["num"].gt(0).astype("Int64")
        actions.append({"operation": "derive_target", "source": "num", "destination": "heart_disease_binary", "rule": "1 if num > 0, else 0; preserve num"})
    exact = int(typed.duplicated().sum())
    key_duplicates = int(typed.duplicated(subset=list(schema.record_key)).sum()) if schema.record_key else None
    unique_duplicates = int(typed.duplicated(subset=list(schema.unique_key)).sum()) if schema.unique_key else 0
    if unique_duplicates:
        raise PreparationError(f"Unique record key {schema.unique_key} repeats {unique_duplicates} times in {member}")
    removed = 0
    if config["exact_duplicate_policy"] == "drop":
        removed = exact
        typed = typed.drop_duplicates().reset_index(drop=True)
        actions.append({"operation": "drop_exact_duplicates", "rows": removed, "rationale": config["duplicate_removal_justification"]})
    else:
        actions.append({"operation": "retain_exact_duplicates", "rows": exact, "rationale": "Identical values can represent distinct people; no proof of duplicate identity"})
    if dataset_id == "synthea_csv" and member == "csv/encounters.csv":
        actions.append({"operation": "retain_colliding_visit_signatures", "rows": key_duplicates, "rationale": "Same patient, time, and code can still have distinct encounter IDs; no rows removed"})
    actions.append({"operation": "retain_iqr_outliers", "rationale": "IQR flags are descriptive, not proof of erroneous medical measurements"})
    report = {
        "dataset_id": dataset_id, "member": member,
        "initial": {"rows": len(initial), "columns": list(initial.columns), "missing": initial_missing},
        "missing_after_token_normalization": normalized_missing,
        "duplicates": {"exact_before": exact, "record_key": list(schema.record_key), "record_key_repeated_rows": key_duplicates, "unique_key": list(schema.unique_key), "unique_key_repeated_rows": unique_duplicates, "removed": removed, "retained": exact - removed},
        "invalid_values": invalid,
        "outliers_before": iqr_summary(before, schema.continuous),
        "outliers_after": iqr_summary(typed, schema.continuous),
        "actions": actions,
        "final": {"rows": len(typed), "columns": list(typed.columns), "missing": _missing(typed)},
    }
    return PreparedTable(data=typed, report=report, before=before, schema=schema)


def prepare_dataset(dataset_id: str, config: dict[str, Any], raw_dir: Path = PROJECT_ROOT / "data" / "raw", registry_path: Path = REGISTRY) -> dict[str, PreparedTable]:
    """Prepare all registered members of one archive and validate relationships."""
    dataset = _source_dataset(dataset_id, registry_path)
    archive = raw_dir / dataset["archive"]
    if not archive.is_file():
        raise PreparationError(f"Raw archive is missing: {archive}; see dataset registry download instructions")
    actual_sha = sha256(archive)
    if actual_sha != dataset["sha256"]:
        raise PreparationError(f"Archive checksum mismatch for {archive}: registry {dataset['sha256']}, actual {actual_sha}")
    prepared: dict[str, PreparedTable] = {}
    with zipfile.ZipFile(archive) as bundle:
        for table in dataset["tables"]:
            member = table["member"]
            raw = read_registered_table(bundle, table, config["missing_tokens"])
            prepared[member] = prepare_table(raw, dataset_id, member, config)
    if dataset_id == "synthea_csv":
        patients = prepared["csv/patients.csv"].data
        encounters = prepared["csv/encounters.csv"].data
        orphan_count = int((~encounters["PATIENT"].isin(patients["Id"])).sum())
        prepared["csv/encounters.csv"].report["relationship"] = {"foreign_key": "encounters.PATIENT -> patients.Id", "orphan_encounters": orphan_count}
        prepared["csv/encounters.csv"].report["relationship"]["repeated_patient_rows"] = int(encounters.duplicated(subset=["PATIENT"]).sum())
        prepared["csv/encounters.csv"].report["actions"].append({"operation": "retain_repeated_patient_visits", "rows": int(encounters.duplicated(subset=["PATIENT"]).sum()), "rationale": "PATIENT is a foreign key; multiple encounter IDs per patient are valid"})
        if orphan_count:
            raise PreparationError(f"Synthea contains {orphan_count} encounters without a patient record")
    for result in prepared.values():
        result.report["source"] = {"original_url": dataset["original_url"], "archive": dataset["archive"], "sha256": actual_sha, "records": dataset["records"], "version": dataset["version"]}
    return prepared
