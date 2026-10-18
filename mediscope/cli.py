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
    eda = subcommands.add_parser("eda", help="Run Phase II exploratory analysis on prepared CSVs")
    eda.add_argument("--dataset", default="all", help="Registry dataset ID or 'all' (default)")
    eda.add_argument("--alpha", type=float, default=0.05, help="Preregistered significance level (default: 0.05)")
    eda.add_argument("--output-root", type=Path, default=PROJECT_ROOT)
    ml = subcommands.add_parser("ml", help="Run Phase IV research-only classification experiments")
    ml_actions = ml.add_subparsers(dest="ml_action", required=True)
    for action in ("train", "evaluate", "compare", "explain", "predict"):
        command = ml_actions.add_parser(action, help=f"ML {action} action")
        command.add_argument("--dataset", default="all" if action != "predict" else None,
                             help="heart, diabetes, stroke, or all (except predict)")
        if action in ("train", "evaluate", "compare", "explain"):
            command.add_argument("--quick", action="store_true", help="Use separate three-fold pipeline smoke artifacts")
        if action == "predict":
            command.add_argument("--input", type=Path, required=True, help="JSON feature dictionary")
    args = parser.parse_args(argv)
    if args.command == "health":
        report: Any = health()
    elif args.command == "audit":
        datasets = load_registry()["datasets"]
        selected = datasets if args.dataset == "all" else [item for item in datasets if item["id"] == args.dataset]
        if not selected:
            parser.exit(2, f"Unknown dataset {args.dataset!r}; choose one of {[item['id'] for item in datasets]}\n")
        report = [audit_dataset(dataset, args.raw_dir) for dataset in selected]
    elif args.command == "eda":
        from .eda import EDAError, run_eda

        try:
            if not 0 < args.alpha < 1:
                raise EDAError("alpha must be strictly between 0 and 1")
            report = run_eda(args.dataset, args.alpha, args.output_root)
        except (EDAError, OSError, ValueError) as error:
            parser.exit(2, f"EDA failed: {error}\n")
    elif args.command == "ml":
        from .ml.tasks import MLError, TASKS

        try:
            selected = list(TASKS) if args.dataset == "all" else [args.dataset]
            if any(name not in TASKS for name in selected):
                raise MLError(f"Unknown ML dataset {args.dataset!r}; choose {list(TASKS)} or all")
            if args.ml_action == "predict":
                if len(selected) != 1:
                    raise MLError("Predict requires --dataset heart, diabetes, or stroke")
                from .ml.prediction import predict_case

                case = json.loads(args.input.read_text(encoding="utf-8"))
                if not isinstance(case, dict):
                    raise MLError("Prediction input must be a JSON feature dictionary")
                report = predict_case(selected[0], case)
            elif args.ml_action == "train":
                from .ml.training import train_task

                report = [train_task(name, quick=args.quick) for name in selected]
            elif args.ml_action == "evaluate":
                from .ml.registry import load_model, read_registry

                registry = read_registry(quick=args.quick)
                for name in selected:
                    for algorithm in registry["tasks"][name]["trials"]:
                        load_model(name, algorithm, quick=args.quick)
                summary_keys = ("accuracy", "precision", "recall", "f1", "specificity", "balanced_accuracy",
                                "roc_auc", "average_precision", "brier", "confusion_matrix")
                report = {name: {"selected_by_cv": registry["tasks"][name]["selected_model"],
                                 "selection_score": registry["tasks"][name]["selection_score"],
                                 "experiments": {key: {"cv_mean": value["cv_mean"], "cv_std": value["cv_std"],
                                                        "threshold": value["threshold_selection"]["threshold"],
                                                        "test": {metric: value["test"][metric] for metric in summary_keys}}
                                                 for key, value in registry["tasks"][name]["trials"].items()}}
                          for name in selected}
            elif args.ml_action == "compare":
                if args.quick:
                    raise MLError("Comparison figures require full five-fold experiments")
                from .ml.reporting import create_comparison

                report = [create_comparison(name) for name in selected]
            else:
                if args.quick:
                    raise MLError("Explanations require full five-fold experiments")
                from .ml.explainability import global_explanations
                from .ml.training import ALGORITHMS

                report = [{"task": name, "algorithms": [global_explanations(name, algorithm)["algorithm"] for algorithm in ALGORITHMS]}
                          for name in selected]
        except (MLError, OSError, ValueError, KeyError) as error:
            parser.exit(2, f"ML failed: {error}\n")
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
