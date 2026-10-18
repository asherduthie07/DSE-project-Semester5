"""Export compact report-ready Phase III tables from the committed snapshot."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from mediscope.cli import PROJECT_ROOT, sha256
from mediscope.visualization.exports import verify_exports


def copy_columns(source: Path, target: Path, columns: list[str], *, limit: int | None = None) -> int:
    with source.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if limit is not None:
        rows = rows[:limit]
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows({column: row[column] for column in columns} for row in rows)
    return len(rows)


def main() -> int:
    verify_exports()
    source = PROJECT_ROOT / "powerbi" / "exports" / "v1"
    target = PROJECT_ROOT / "reports" / "tables" / "phase3"
    target.mkdir(parents=True, exist_ok=True)
    files = {
        "dataset_overview": ["dataset_id", "table_name", "analysis_unit", "rows", "columns", "exact_duplicates", "missing_cells"],
        "outcomes": ["dataset_id", "category", "count", "all_n", "pct_all"],
        "hypotheses": ["id", "dataset_id", "method", "positive_n", "negative_n", "statistic", "p_value", "effect_size", "effect_name", "ci_low", "ci_high"],
    }
    result = {}
    for name, columns in files.items():
        path = target / f"{name}.csv"
        result[path.name] = copy_columns(source / f"{name}.csv", path, columns)
    path = target / "note_top30.csv"
    result[path.name] = copy_columns(source / "note_terms.csv", path, ["term", "count", "source_id"], limit=30)
    fig_rows = []
    for figure in sorted((PROJECT_ROOT / "reports" / "figures" / "phase3").glob("*.png")):
        fig_rows.append({"figure": figure.name, "sha256": sha256(figure), "bytes": figure.stat().st_size})
    path = target / "figure_inventory.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["figure", "sha256", "bytes"], lineterminator="\n")
        writer.writeheader(); writer.writerows(fig_rows)
    result[path.name] = len(fig_rows)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
