"""Phase II report and table adapter; never recomputes published statistics."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.errors import APIError, unavailable
from backend.app.core.json_safe import clean
from backend.app.services.datasets import DatasetService


class AnalyticsService:
    def __init__(self, root: Path, datasets: DatasetService) -> None:
        self.root = root
        self.datasets = datasets

    @lru_cache(maxsize=4)
    def report(self, dataset_id: str) -> dict[str, Any]:
        _, quality, _ = self.datasets.load(dataset_id)
        path = self.root / "reports/eda" / f"{dataset_id}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data["dataset_id"] != dataset_id or data["source_sha256"] != quality["source"]["sha256"]:
                raise ValueError("EDA lineage mismatch")
            for member, table in data["tables"].items():
                if table["prepared_sha256"] != quality["outputs"][member]["prepared_sha256"]:
                    raise ValueError("EDA prepared-table hash mismatch")
            return data
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise unavailable("EDA report") from exc

    def table(self, dataset_id: str, name: str) -> list[dict[str, Any]]:
        report = self.report(dataset_id)
        relative = report["table_paths"].get(name)
        if relative is None:
            raise APIError(404, "NOT_FOUND", "Unknown analytics table for this dataset.")
        path = (self.root / relative).resolve()
        allowed = (self.root / "reports/tables/eda").resolve()
        if path.parent != allowed or not path.name.startswith(dataset_id + "_") or path.suffix != ".csv":
            raise unavailable("EDA table")
        try:
            return clean(pd.read_csv(path).to_dict(orient="records"))
        except (OSError, ValueError) as exc:
            raise unavailable("EDA table") from exc

    def overview(self, dataset_id: str) -> dict[str, Any]:
        r = self.report(dataset_id)
        return clean({"dataset_id": dataset_id, "name": r["dataset_name"], "records": r["tables"],
                      "facts": r["facts"], "source_url": r["source_url"], "source_sha256": r["source_sha256"],
                      "caveat": "Research and education only; association does not imply causation or clinical validity."})

    def distributions(self, dataset_id: str, table: str | None) -> dict[str, Any]:
        name = table or ("encounter_class" if dataset_id == "synthea_csv" else "outcome")
        if name not in {"outcome", "categorical", "encounter_class", "monthly_encounters", "age_group_by_stroke", "symptom_yes_by_class"}:
            raise APIError(422, "INVALID_TABLE", "Choose an available distribution table.")
        return {"dataset_id": dataset_id, "table": name, "rows": self.table(dataset_id, name)}

    def correlations(self, dataset_id: str) -> dict[str, Any]:
        r = self.report(dataset_id)
        names = [name for name in r["table_paths"] if name == "correlations" or name.endswith("_correlations")]
        return {"dataset_id": dataset_id, "tables": {name: self.table(dataset_id, name) for name in names},
                "missing_policy": "Pairwise complete cases; see rows for sample size and adjusted exploratory p-values."}

    def hypotheses(self, dataset_id: str) -> dict[str, Any]:
        r = self.report(dataset_id)
        return {"dataset_id": dataset_id, "alpha": r["alpha"], "hypotheses": clean(r["hypotheses"])}

    def charts(self, dataset_id: str) -> dict[str, Any]:
        r = self.report(dataset_id)
        name = "encounter_class" if dataset_id == "synthea_csv" else "outcome"
        rows = self.table(dataset_id, name)
        categories = [str(row["category"]) for row in rows if row.get("group") == "all"]
        values = [int(row["count"]) for row in rows if row.get("group") == "all"]
        n = int(rows[0]["all_n"]) if rows else 0
        figures = [path for path in r["figure_paths"] if path.startswith("reports/figures/eda/") and (self.root / path).is_file()]
        return {"dataset_id": dataset_id, "charts": [{"id": name, "label": "Encounter class" if dataset_id == "synthea_csv" else "Recorded outcome",
                "categories": categories, "values": values, "unit": "encounters" if dataset_id == "synthea_csv" else "records", "sample_size": n,
                "missingness_note": "Counts and denominators are from the saved Phase II frequency table."}],
                "approved_figures": figures, "source_url": r["source_url"],
                "caveat": "Synthea is synthetic; other cohorts are separate. These charts are descriptive, not clinical evidence."}
