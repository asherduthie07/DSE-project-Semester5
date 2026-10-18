"""Phase I preparation exports and report-ready quality evidence."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from .cli import PROJECT_ROOT, sha256

# Keep Matplotlib and font caches inside this writable project on macOS.
_cache = PROJECT_ROOT / ".cache"
_cache.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_cache / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_cache))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .preparation import OUTPUT_NAMES, PreparedTable


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _quality_rows(table: PreparedTable) -> list[dict[str, Any]]:
    before = table.report["initial"]["missing"]
    after = table.report["final"]["missing"]
    invalid = table.report["invalid_values"]
    out_before = table.report["outliers_before"]
    out_after = table.report["outliers_after"]
    return [
        {
            "feature": column,
            "missing_before": before.get(column, 0),
            "missing_after": after.get(column, 0),
            "invalid_found": invalid.get(column, {}).get("count", 0),
            "iqr_outliers_before": out_before.get(column, {}).get("count", ""),
            "iqr_outliers_after": out_after.get(column, {}).get("count", ""),
        }
        for column in table.report["final"]["columns"]
    ]


def plot_before_after(table: PreparedTable, path: Path, title: str) -> None:
    """Draw paired raw-typed and prepared boxplots for continuous attributes."""
    columns = table.schema.continuous
    figure, axes = plt.subplots(len(columns), 2, figsize=(11, max(3, 2.5 * len(columns))), squeeze=False)
    for row, column in enumerate(columns):
        for col, (frame, label) in enumerate(((table.before, "Before"), (table.data, "After"))):
            values = pd.to_numeric(frame[column], errors="coerce").dropna().to_numpy(dtype=float)
            if len(values):
                axes[row, col].boxplot(values, vert=False)
            axes[row, col].set_title(f"{label}: {column} (n={len(values)})")
            axes[row, col].set_xlabel(column)
            axes[row, col].set_yticks([])
    figure.suptitle(f"{title}: IQR inspection (extremes retained)")
    figure.tight_layout()
    figure.savefig(path, dpi=130, metadata={"Software": "MediScope AI"})
    plt.close(figure)


def _markdown(report: dict[str, Any], quality: dict[str, list[dict[str, Any]]]) -> str:
    lines = [
        f"# Data-quality report: {report['dataset_name']}", "",
        "Research and education only. These data and future models are not clinically validated.", "",
        f"Source: {report['source']['original_url']}",
        f"Local raw SHA-256: `{report['source']['sha256']}`", "",
        "The outputs retain missing feature values. Learned imputation, encoding, scaling, and optional IQR clipping must be fitted inside training folds.", "",
    ]
    for member, table in report["tables"].items():
        lines += [f"## {member}", "", f"Initial: **{table['initial']['rows']} rows × {len(table['initial']['columns'])} columns**. Final: **{table['final']['rows']} rows × {len(table['final']['columns'])} columns**.", ""]
        duplicates = table["duplicates"]
        repeated = duplicates["record_key_repeated_rows"]
        repeated_text = str(repeated) if repeated is not None else "not applicable (no record key)"
        lines += [f"Exact duplicates: {duplicates['exact_before']} found, {duplicates['removed']} removed, {duplicates['retained']} retained. Record-key repeated rows: {repeated_text}.", ""]
        if "relationship" in table:
            lines += [f"Patient-encounter foreign key: {table['relationship']['orphan_encounters']} orphan encounters.", ""]
        lines += ["| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |", "|---|---:|---:|---:|---:|---:|"]
        for row in quality[member]:
            lines.append("| " + " | ".join(str(row[key]) for key in ("feature", "missing_before", "missing_after", "invalid_found", "iqr_outliers_before", "iqr_outliers_after")) + " |")
        lines += ["", "### Actions", ""]
        for action in table["actions"]:
            rows = f"; rows={action['rows']}" if "rows" in action else ""
            lines.append(f"- `{action['operation']}`: {action.get('rationale', action.get('rule', 'Deterministic source transformation'))}{rows}.")
        lines.append("")
    return "\n".join(lines)


def export_dataset(
    dataset_id: str,
    dataset_name: str,
    prepared: dict[str, PreparedTable],
    config: dict[str, Any],
    root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Export typed CSVs, config, JSON/Markdown reports, tables, and figures."""
    processed = root / "data" / "processed"
    quality_dir = root / "reports" / "quality"
    tables_dir = root / "reports" / "tables"
    figures_dir = root / "reports" / "figures"
    for directory in (processed, quality_dir, tables_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)
    config_path = processed / f"{dataset_id}_preparation_config.json"
    _write_json(config_path, config)
    if dataset_id != "synthea_csv":
        from .preprocessors import feature_roles

        _write_json(processed / f"{dataset_id}_feature_roles.json", feature_roles(dataset_id))
    report: dict[str, Any] = {
        "dataset_id": dataset_id, "dataset_name": dataset_name,
        "source": next(iter(prepared.values())).report["source"],
        "config": config,
        "tables": {},
        "outputs": {},
    }
    quality_rows: dict[str, list[dict[str, Any]]] = {}
    for member, result in prepared.items():
        stem = Path(OUTPUT_NAMES[member]).stem
        data_path = processed / OUTPUT_NAMES[member]
        table_path = tables_dir / f"{dataset_id}_{stem}_quality.csv"
        figure_path = figures_dir / f"{dataset_id}_{stem}_boxplot.png"
        result.data.to_csv(data_path, index=False, na_rep="", lineterminator="\n")
        rows = _quality_rows(result)
        with table_path.open("w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        plot_before_after(result, figure_path, f"{dataset_name} — {stem}")
        quality_rows[member] = rows
        report["tables"][member] = result.report
        report["outputs"][member] = {
            "prepared_csv": str(data_path.relative_to(root)), "prepared_sha256": sha256(data_path),
            "quality_table": str(table_path.relative_to(root)),
            "boxplot": str(figure_path.relative_to(root)),
        }
    report_path = quality_dir / f"{dataset_id}.json"
    markdown_path = quality_dir / f"{dataset_id}.md"
    _write_json(report_path, report)
    markdown_path.write_text(_markdown(report, quality_rows), encoding="utf-8")
    return {"dataset_id": dataset_id, "report_json": str(report_path), "report_markdown": str(markdown_path), "tables": report["outputs"]}
