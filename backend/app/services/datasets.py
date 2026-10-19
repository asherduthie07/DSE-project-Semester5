"""Checksum-verified Phase I table access with a small, explicit public projection."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.app.core.errors import APIError, missing, unavailable
from backend.app.core.json_safe import clean
from mediscope.eda.runner import FILES, load_prepared


TABLE_KEYS = {
    "uci_cleveland_heart": {"heart": "processed.cleveland.data"},
    "uci_early_diabetes": {"diabetes": "diabetes_data_upload.csv"},
    "kaggle_stroke": {"stroke": "healthcare-dataset-stroke-data.csv"},
    "synthea_csv": {"patients": "csv/patients.csv", "encounters": "csv/encounters.csv"},
}
PUBLIC_FIELDS = {
    "heart": None,
    "diabetes": None,
    "stroke": None,
    "patients": ("RACE", "ETHNICITY", "GENDER", "MARITAL", "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE"),
    "encounters": ("ENCOUNTERCLASS", "CODE", "BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE"),
}
FILTER_FIELDS = {
    "heart": ("heart_disease_binary", "sex", "cp"),
    "diabetes": ("class", "Gender", "Polyuria"),
    "stroke": ("stroke", "gender", "hypertension"),
    "patients": ("GENDER", "RACE"),
    "encounters": ("ENCOUNTERCLASS",),
}


class DatasetService:
    def __init__(self, root: Path) -> None:
        self.root = root
        registry_path = root / "data/metadata/datasets.json"
        try:
            self.registry = {d["id"]: d for d in json.loads(registry_path.read_text(encoding="utf-8"))["datasets"]}
        except (OSError, ValueError, KeyError, TypeError):
            self.registry = {}

    def _check_id(self, dataset_id: str) -> None:
        if dataset_id not in TABLE_KEYS:
            raise missing("dataset")

    @lru_cache(maxsize=4)
    def load(self, dataset_id: str):
        self._check_id(dataset_id)
        if dataset_id not in self.registry:
            raise unavailable("Dataset registry")
        try:
            frames, quality, item = load_prepared(dataset_id, self.root)
            if item["sha256"] != self.registry[dataset_id]["sha256"]:
                raise ValueError("source registry mismatch")
            return frames, quality, item
        except (OSError, ValueError, KeyError, TypeError) as exc:
            raise unavailable("Prepared dataset") from exc

    def table(self, dataset_id: str, table: str | None = None) -> tuple[str, pd.DataFrame]:
        self._check_id(dataset_id)
        choices = TABLE_KEYS[dataset_id]
        if table is None and len(choices) > 1:
            raise APIError(422, "TABLE_REQUIRED", "Choose table=patients or table=encounters for the synthetic dataset.")
        selected = table or next(iter(choices))
        if selected not in choices:
            raise APIError(422, "INVALID_TABLE", "Unknown table for this dataset.")
        frames, _, _ = self.load(dataset_id)
        return selected, frames[choices[selected]]

    def listing(self) -> dict[str, Any]:
        rows = []
        for dataset_id in TABLE_KEYS:
            frames, _, item = self.load(dataset_id)
            rows.append({"id": dataset_id, "name": item["name"], "records": item["records"],
                         "source_url": item["original_url"], "source_sha256": item["sha256"],
                         "tables": {short: len(frames[member]) for short, member in TABLE_KEYS[dataset_id].items()}})
        return {"datasets": rows}

    def schema(self, dataset_id: str) -> dict[str, Any]:
        frames, quality, item = self.load(dataset_id)
        tables = {}
        for short, member in TABLE_KEYS[dataset_id].items():
            frame = frames[member]
            exposed = list(PUBLIC_FIELDS[short] or (c for c in frame.columns if c != "id"))
            tables[short] = {"rows": len(frame), "fields": [
                {"name": c, "dtype": str(frame[c].dtype), "nullable": bool(frame[c].isna().any()),
                 "exposed_in_records": c in exposed} for c in frame.columns], "record_fields": exposed}
        return {"dataset_id": dataset_id, "name": item["name"], "source_sha256": quality["source"]["sha256"], "tables": tables}

    def summary(self, dataset_id: str) -> dict[str, Any]:
        frames, quality, item = self.load(dataset_id)
        return clean({"dataset_id": dataset_id, "name": item["name"], "source_url": item["original_url"],
                      "provenance": item["records"], "source_sha256": quality["source"]["sha256"],
                      "tables": {short: quality["tables"][member]["final"] for short, member in TABLE_KEYS[dataset_id].items()},
                      "rows": {short: len(frames[member]) for short, member in TABLE_KEYS[dataset_id].items()}})

    def quality(self, dataset_id: str) -> dict[str, Any]:
        _, quality, _ = self.load(dataset_id)
        return clean(quality)

    def records(self, dataset_id: str, table: str | None, offset: int, limit: int,
                filter_field: str | None, filter_value: str | None) -> dict[str, Any]:
        short, frame = self.table(dataset_id, table)
        if (filter_field is None) != (filter_value is None):
            raise APIError(422, "INVALID_FILTER", "Provide filter_field and filter_value together.")
        visible = list(PUBLIC_FIELDS[short] or (c for c in frame.columns if c != "id"))
        selected = frame
        if filter_field is not None:
            if filter_field not in FILTER_FIELDS[short]:
                raise APIError(422, "INVALID_FILTER", "Filtering is unavailable for this field.")
            selected = frame.loc[frame[filter_field].astype(str) == filter_value]
        rows = selected.iloc[offset:offset + limit].loc[:, visible].to_dict(orient="records")
        return clean({"dataset_id": dataset_id, "table": short, "source_rows": len(frame),
                      "total": len(selected), "offset": offset, "limit": limit, "items": rows})
