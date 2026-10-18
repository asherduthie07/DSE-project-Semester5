"""Independent, read-only reconciliation of Phase I raw data, exports and reports.

Run from the project root: .venv/bin/python scripts/verify_phase1_outputs.py
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "metadata" / "datasets.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_csv(stream: Any, header: bool, columns: list[str]) -> tuple[list[str], list[list[str]]]:
    reader = csv.reader(stream)
    observed = next(reader) if header else columns
    rows = list(reader)
    if any(len(row) != len(observed) for row in rows):
        raise ValueError("CSV contains a row with the wrong number of columns")
    return observed, rows


def _missing(rows: list[list[str]], columns: list[str], tokens: set[str]) -> dict[str, int]:
    return {column: sum(row[index] in tokens for row in rows) for index, column in enumerate(columns)}


def _outlier_count(rows: list[list[str]], columns: list[str], column: str) -> int:
    index = columns.index(column)
    values = np.asarray([float(row[index]) for row in rows if row[index] != ""], dtype=float)
    if not len(values):
        return 0
    q1, q3 = np.percentile(values, [25, 75])
    spread = q3 - q1
    return int(((values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread)).sum())


def verify(root: Path = ROOT, registry_path: Path = REGISTRY) -> dict[str, Any]:
    """Check every registered input, exported CSV, table, plot and quality report."""
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    result: dict[str, Any] = {"status": "PASS", "datasets": {}, "errors": []}
    for dataset in registry["datasets"]:
        dataset_id = dataset["id"]
        archive = root / "data" / "raw" / dataset["archive"]
        report_path = root / "reports" / "quality" / f"{dataset_id}.json"
        if not archive.is_file() or not report_path.is_file():
            result["errors"].append(f"{dataset_id}: raw archive or JSON report is missing")
            continue
        if not zipfile.is_zipfile(archive):
            result["errors"].append(f"{dataset_id}: raw archive is not a readable ZIP")
            continue
        actual_sha = _sha256(archive)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if actual_sha != dataset["sha256"] or actual_sha != report["source"]["sha256"]:
            result["errors"].append(f"{dataset_id}: raw archive checksum differs from registry/report")
        saved_config = root / "data" / "processed" / f"{dataset_id}_preparation_config.json"
        if not saved_config.is_file():
            result["errors"].append(f"{dataset_id}: saved preparation configuration is missing")
            continue
        if report["config"] != json.loads(saved_config.read_text()):
            result["errors"].append(f"{dataset_id}: saved preparation configuration differs from report")
        missing_tokens = set(report["config"]["missing_tokens"])
        dataset_result: dict[str, Any] = {"raw_sha256": actual_sha, "tables": {}}
        with zipfile.ZipFile(archive) as bundle:
            for table in dataset["tables"]:
                member = table["member"]
                if member not in bundle.namelist() or member not in report["tables"]:
                    result["errors"].append(f"{dataset_id}: missing member or report entry {member}")
                    continue
                try:
                    with bundle.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
                        raw_columns, raw_rows = _read_csv(text, table["header"], table["columns"])
                except (OSError, UnicodeError, ValueError, csv.Error) as error:
                    result["errors"].append(f"{dataset_id}/{member}: unreadable raw CSV: {error}")
                    continue
                quality = report["tables"][member]
                output = report["outputs"][member]
                data_path = root / output["prepared_csv"]
                if not data_path.is_file():
                    result["errors"].append(f"{dataset_id}: prepared CSV missing: {data_path}")
                    continue
                try:
                    with data_path.open(encoding="utf-8-sig", newline="") as source:
                        final_columns, final_rows = _read_csv(source, True, [])
                except (OSError, UnicodeError, ValueError, csv.Error) as error:
                    result["errors"].append(f"{dataset_id}/{member}: unreadable prepared CSV: {error}")
                    continue
                checks = {
                    "raw_schema": raw_columns == table["columns"] == quality["initial"]["columns"],
                    "raw_rows": len(raw_rows) == quality["initial"]["rows"],
                    "raw_missing": _missing(raw_rows, raw_columns, missing_tokens) == quality["initial"]["missing"],
                    "raw_exact_duplicates": len(raw_rows) - len({tuple(row) for row in raw_rows}) == quality["duplicates"]["exact_before"],
                    "row_reconciliation": len(raw_rows) - quality["duplicates"]["removed"] == len(final_rows),
                    "final_schema": final_columns == quality["final"]["columns"],
                    "final_rows": len(final_rows) == quality["final"]["rows"],
                    "final_missing": _missing(final_rows, final_columns, {""}) == quality["final"]["missing"],
                    "prepared_sha256": _sha256(data_path) == output["prepared_sha256"],
                }
                target = table["target"]
                if target:
                    values = {row[final_columns.index(target)] for row in final_rows}
                    allowed = {"0", "1", "2", "3", "4"} if dataset_id == "uci_cleveland_heart" else {"Negative", "Positive"} if dataset_id == "uci_early_diabetes" else {"0", "1"}
                    checks["target_domain"] = bool(values) and values <= allowed
                if dataset_id == "uci_cleveland_heart":
                    original_index = final_columns.index("num")
                    binary_index = final_columns.index("heart_disease_binary")
                    checks["heart_target_rule"] = all(row[binary_index] == str(int(int(row[original_index]) > 0)) for row in final_rows)
                for column, item in quality["outliers_after"].items():
                    checks[f"outliers:{column}"] = _outlier_count(final_rows, final_columns, column) == item["count"]
                table_path = root / output["quality_table"]
                figure_path = root / output["boxplot"]
                checks["quality_table"] = False
                if table_path.is_file():
                    with table_path.open(encoding="utf-8", newline="") as source:
                        table_rows = list(csv.DictReader(source))
                    checks["quality_table"] = len(table_rows) == len(final_columns) and all(
                        item["feature"] == column
                        and int(item["missing_before"]) == quality["initial"]["missing"].get(column, 0)
                        and int(item["missing_after"]) == quality["final"]["missing"].get(column, 0)
                        and int(item["invalid_found"]) == quality["invalid_values"].get(column, {}).get("count", 0)
                        and item["iqr_outliers_after"] == str(quality["outliers_after"][column]["count"] if column in quality["outliers_after"] else "")
                        for item, column in zip(table_rows, final_columns)
                    )
                checks["boxplot_png"] = figure_path.is_file() and figure_path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
                for name, passed in checks.items():
                    if not passed:
                        result["errors"].append(f"{dataset_id}/{member}: {name} failed")
                dataset_result["tables"][member] = {
                    "raw_rows": len(raw_rows), "raw_columns": len(raw_columns),
                    "raw_missing": {key: value for key, value in quality["initial"]["missing"].items() if value},
                    "exact_duplicates": quality["duplicates"]["exact_before"],
                    "removed": quality["duplicates"]["removed"],
                    "final_rows": len(final_rows), "final_columns": len(final_columns),
                    "final_missing": {key: value for key, value in quality["final"]["missing"].items() if value},
                    "invalid_values": {key: value["count"] for key, value in quality["invalid_values"].items() if value["count"]},
                    "target_counts": dict(sorted(Counter(row[final_columns.index(target)] for row in final_rows).items())) if target else {},
                    "outlier_counts": {key: value["count"] for key, value in quality["outliers_after"].items()},
                    "checks_passed": sum(checks.values()), "checks_total": len(checks),
                }
        if dataset_id == "synthea_csv" and all(member in dataset_result["tables"] for member in ("csv/patients.csv", "csv/encounters.csv")):
            with (root / report["outputs"]["csv/patients.csv"]["prepared_csv"]).open(newline="") as source:
                patients = list(csv.DictReader(source))
            with (root / report["outputs"]["csv/encounters.csv"]["prepared_csv"]).open(newline="") as source:
                encounters = list(csv.DictReader(source))
            patient_ids = {row["Id"] for row in patients}
            encounter_ids = [row["Id"] for row in encounters]
            orphans = sum(row["PATIENT"] not in patient_ids for row in encounters)
            if orphans or len(encounter_ids) != len(set(encounter_ids)) or orphans != report["tables"]["csv/encounters.csv"]["relationship"]["orphan_encounters"]:
                result["errors"].append("synthea_csv: patient/encounter relationship or unique encounter ID failed")
            dataset_result["patient_encounter_relationship"] = {"orphan_encounters": orphans, "repeated_patient_rows": len(encounters) - len({row["PATIENT"] for row in encounters})}
        markdown_path = root / "reports" / "quality" / f"{dataset_id}.md"
        if not markdown_path.is_file():
            result["errors"].append(f"{dataset_id}: Markdown report missing")
        result["datasets"][dataset_id] = dataset_result
    if result["errors"]:
        result["status"] = "FAIL"
    return result


if __name__ == "__main__":
    summary = verify()
    print(json.dumps(summary, indent=2))
    raise SystemExit(0 if summary["status"] == "PASS" else 1)
