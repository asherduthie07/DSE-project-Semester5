"""CLI for environment health, raw-data audit, and Phase I preparation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import platform
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, TextIO

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = PROJECT_ROOT / "data" / "metadata" / "datasets.json"
MISSING = {"", "?", "NA", "N/A", "NULL", "null"}


def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    """Load the tracked dataset contract without modifying raw files."""
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def value_type(value: str) -> str:
    """Classify an observed nonmissing CSV token without coercing source data."""
    if value.strip() in MISSING:
        return "missing"
    try:
        number = float(value)
    except ValueError:
        return "text"
    return "integer" if number.is_integer() else "float"


def audit_table(stream: TextIO, table: dict[str, Any]) -> dict[str, Any]:
    """Stream a CSV and compare its ordered columns with the registry."""
    reader = csv.reader(stream)
    expected = table["columns"]
    observed = next(reader, []) if table["header"] else expected
    missing = Counter()
    types: dict[str, set[str]] = {column: set() for column in observed}
    targets = Counter()
    seen: set[tuple[str, ...]] = set()
    rows = duplicates = bad_width = 0
    target_index = observed.index(table["target"]) if table.get("target") in observed else None
    for row in reader:
        rows += 1
        if len(row) != len(observed):
            bad_width += 1
            continue
        key = tuple(row)
        duplicates += key in seen
        seen.add(key)
        for column, value in zip(observed, row):
            kind = value_type(value)
            if kind == "missing":
                missing[column] += 1
            else:
                types[column].add(kind)
        if target_index is not None:
            targets[row[target_index]] += 1
    return {
        "rows": rows,
        "columns": observed,
        "observed_types": {key: sorted(value) or ["all missing"] for key, value in types.items()},
        "missing_values": {key: missing[key] for key in observed},
        "target_class_counts": dict(sorted(targets.items())),
        "duplicate_rows": duplicates,
        "schema_mismatches": {
            "missing_columns": [c for c in expected if c not in observed],
            "unexpected_columns": [c for c in observed if c not in expected],
            "column_order": observed != expected,
            "rows_with_wrong_width": bad_width,
        },
    }


def audit_dataset(dataset: dict[str, Any], raw_dir: Path) -> dict[str, Any]:
    """Audit registered ZIP members; report unavailable or corrupt inputs."""
    archive = raw_dir / dataset["archive"]
    result: dict[str, Any] = {"name": dataset["name"], "archive": str(archive)}
    if not archive.is_file():
        return {**result, "status": "missing", "tables": {}}
    result["sha256"] = sha256(archive)
    result["checksum_matches_registry"] = result["sha256"] == dataset["sha256"]
    tables: dict[str, Any] = {}
    try:
        with zipfile.ZipFile(archive) as bundle:
            for table in dataset["tables"]:
                member = table["member"]
                if member not in bundle.namelist():
                    tables[member] = {"status": "missing member"}
                    continue
                with bundle.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
                    tables[member] = audit_table(stream, table)
    except (OSError, zipfile.BadZipFile, UnicodeError, csv.Error) as error:
        return {**result, "status": "unreadable", "error": str(error), "tables": tables}
    result["tables"] = tables
    mismatches = any(
        table.get("status") == "missing member"
        or any(table.get("schema_mismatches", {}).values())
        for table in tables.values()
    )
    result["status"] = "invalid" if mismatches or not result["checksum_matches_registry"] else "available"
    return result


def health() -> dict[str, Any]:
    """Return a minimal executable and registry health report."""
    registry = load_registry()
    return {
        "status": "ok",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "registry_datasets": len(registry["datasets"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MediScope AI project tools")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("health", help="Check Python and registry availability")
    audit = subcommands.add_parser("audit", help="Read-only audit of registered raw ZIPs")
    audit.add_argument("--raw-dir", type=Path, default=PROJECT_ROOT / "data" / "raw")
    audit.add_argument("--dataset", default="all", help="Registry dataset ID or 'all' (default)")
    prepare = subcommands.add_parser("prepare", help="Run Phase I data preparation")
    prepare.add_argument("--dataset", default="all", help="Registry dataset ID or 'all' (default)")
    prepare.add_argument("--config", type=Path, default=PROJECT_ROOT / "data" / "metadata" / "preparation_config.json")
    prepare.add_argument("--raw-dir", type=Path, default=PROJECT_ROOT / "data" / "raw")
    prepare.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)
    if args.command == "health":
        report: Any = health()
    elif args.command == "audit":
        datasets = load_registry()["datasets"]
        selected = datasets if args.dataset == "all" else [item for item in datasets if item["id"] == args.dataset]
        if not selected:
            parser.exit(2, f"Unknown dataset {args.dataset!r}; choose one of {[item['id'] for item in datasets]}\n")
        report = [audit_dataset(dataset, args.raw_dir) for dataset in selected]
    else:
        from .preparation import PreparationError, load_config, prepare_dataset
        from .reports import export_dataset

        try:
            config = load_config(args.config)
            datasets = load_registry()["datasets"]
            selected = datasets if args.dataset == "all" else [item for item in datasets if item["id"] == args.dataset]
            if not selected:
                raise PreparationError(f"Unknown dataset {args.dataset!r}; choose one of {[item['id'] for item in datasets]}")
            report = [
                export_dataset(item["id"], item["name"], prepare_dataset(item["id"], config, args.raw_dir), config, args.output_root)
                for item in selected
            ]
        except (PreparationError, OSError, zipfile.BadZipFile) as error:
            parser.exit(2, f"Preparation failed: {error}\n")
    print(json.dumps(report, indent=2))
    return 2 if args.command == "audit" and any(item["status"] != "available" for item in report) else 0
