"""Checksummed, idempotent Phase I table import; original CSVs are never modified."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from pymongo import UpdateOne
from pymongo.errors import PyMongoError

from .connection import BigDataError
from .schema import COLLECTIONS, ENCOUNTER_FIELDS, PATIENT_FIELDS, create_indexes

ROOT = Path(__file__).resolve().parents[2]
LOG = logging.getLogger(__name__)
EXPECTED = {
    "heart": ("age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num", "heart_disease_binary"),
    "diabetes": ("Age", "Gender", "Polyuria", "Polydipsia", "sudden weight loss", "weakness", "Polyphagia", "Genital thrush", "visual blurring", "Itching", "Irritability", "delayed healing", "partial paresis", "muscle stiffness", "Alopecia", "Obesity", "class"),
    "stroke": ("id", "gender", "age", "hypertension", "heart_disease", "ever_married", "work_type", "Residence_type", "avg_glucose_level", "bmi", "smoking_status", "stroke"),
    "patients": ("Id", "BIRTHDATE", "DEATHDATE", "SSN", "DRIVERS", "PASSPORT", "PREFIX", "FIRST", "LAST", "SUFFIX", "MAIDEN", "MARITAL", "RACE", "ETHNICITY", "GENDER", "BIRTHPLACE", "ADDRESS", "CITY", "STATE", "COUNTY", "ZIP", "LAT", "LON", "HEALTHCARE_EXPENSES", "HEALTHCARE_COVERAGE"),
    "encounters": ("Id", "START", "STOP", "PATIENT", "ORGANIZATION", "PROVIDER", "PAYER", "ENCOUNTERCLASS", "CODE", "DESCRIPTION", "BASE_ENCOUNTER_COST", "TOTAL_CLAIM_COST", "PAYER_COVERAGE", "REASONCODE", "REASONDESCRIPTION"),
}
TARGETS = {"heart": {0: 164, 1: 139}, "diabetes": {"Negative": 200, "Positive": 320}, "stroke": {0: 4861, 1: 249}}


def fingerprint(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_source(name: str, root: Path = ROOT) -> tuple[pd.DataFrame, str]:
    if name not in COLLECTIONS:
        raise BigDataError(f"Unknown dataset: {name}")
    _, filename, count, target = COLLECTIONS[name]
    path = root / "data" / "processed" / filename
    if not path.is_file():
        raise BigDataError(f"Missing prepared source: {path}; run Phase I preparation and verification")
    digest = fingerprint(path)
    quality_name = {"heart": ("uci_cleveland_heart", "processed.cleveland.data"),
                    "diabetes": ("uci_early_diabetes", "diabetes_data_upload.csv"),
                    "stroke": ("kaggle_stroke", "healthcare-dataset-stroke-data.csv"),
                    "patients": ("synthea_csv", "csv/patients.csv"),
                    "encounters": ("synthea_csv", "csv/encounters.csv")}[name]
    quality_path = root / "reports" / "quality" / f"{quality_name[0]}.json"
    try:
        expected_digest = json.loads(quality_path.read_text(encoding="utf-8"))["outputs"][quality_name[1]]["prepared_sha256"]
    except (OSError, ValueError, KeyError) as exc:
        raise BigDataError(f"Missing or invalid Phase I quality manifest: {quality_path}") from exc
    if digest != expected_digest:
        raise BigDataError(f"Prepared CSV checksum mismatch: {path}")
    frame = pd.read_csv(path, low_memory=False)
    if tuple(frame.columns) != EXPECTED[name] or len(frame) != count:
        raise BigDataError(f"Schema or row count mismatch in {path}: observed {len(frame)} rows, {list(frame.columns)}")
    if target and frame[target].value_counts(dropna=False).to_dict() != TARGETS[name]:
        raise BigDataError(f"Target distribution mismatch in {path}")
    if name in ("patients", "encounters") and (frame["Id"].isna().any() or frame["Id"].duplicated().any()):
        raise BigDataError(f"Missing or duplicate synthetic IDs in {path}")
    return frame, digest


def records(name: str, frame: pd.DataFrame, digest: str) -> list[dict]:
    if name == "patients":
        frame = frame[list(PATIENT_FIELDS)]
    elif name == "encounters":
        frame = frame[list(ENCOUNTER_FIELDS)]
    clean = frame.astype(object).where(pd.notna(frame), None)
    docs = []
    for position, row in enumerate(clean.to_dict("records"), start=1):
        row = {key: value.item() if hasattr(value, "item") else value for key, value in row.items()}
        source_id = row.get("Id", position)
        row.update({"_id": f"{name}:{source_id}", "source_dataset": name, "source_sha256": digest,
                    "source_row": position, "synthetic": name in ("patients", "encounters")})
        docs.append(row)
    return docs


def _import_dataset(db, name: str, root: Path = ROOT) -> dict:
    frame, digest = read_source(name, root)
    if name == "encounters":
        patients, _ = read_source("patients", root)
        missing = set(frame["PATIENT"]) - set(patients["Id"])
        if missing:
            raise BigDataError(f"Encounter source contains {len(missing)} orphan patient IDs")
        db_ids = {doc["Id"] for doc in db.hospital_patients.find({"source_dataset": "patients"}, {"Id": 1})}
        if not set(frame["PATIENT"]).issubset(db_ids):
            raise BigDataError("Import patients before encounters; database lacks referenced patient IDs")
    collection_name = COLLECTIONS[name][0]
    collection = db[collection_name]
    existing = collection.find_one({"source_dataset": name, "source_sha256": {"$ne": digest}}, {"_id": 1})
    if existing:
        raise BigDataError(f"{collection_name} holds another source revision; review before importing")
    docs = records(name, frame, digest)
    try:
        for offset in range(0, len(docs), 1000):
            collection.bulk_write([UpdateOne({"_id": doc["_id"]}, {"$setOnInsert": doc}, upsert=True)
                                   for doc in docs[offset:offset + 1000]], ordered=True)
        count = collection.count_documents({"source_dataset": name, "source_sha256": digest})
        if count != len(docs):
            raise BigDataError(f"{collection_name}: database has {count} source rows; expected {len(docs)}")
        db.dataset_metadata.update_one({"_id": name}, {"$set": {"collection": collection_name, "source_path": f"data/processed/{COLLECTIONS[name][1]}", "sha256": digest, "rows": len(docs), "synthetic": name in ("patients", "encounters")}}, upsert=True)
        LOG.info("Imported %s: %d rows, SHA-256 %s", name, count, digest)
    except (PyMongoError, BigDataError) as exc:
        LOG.exception("Import failed for %s", name)
        raise BigDataError(f"Import failed for {name}: {exc}") from exc
    return {"dataset": name, "collection": collection_name, "rows": count, "sha256": digest}


def import_dataset(db, name: str, root: Path = ROOT) -> dict:
    """Import one source and append a minimal success/failure audit event."""
    try:
        result = _import_dataset(db, name, root)
    except Exception as exc:
        status, detail = "FAIL", f"{type(exc).__name__}: {exc}"
        LOG.error("Import %s failed: %s", name, detail)
        raise
    else:
        status, detail = "PASS", f"{result['rows']} rows; SHA-256 {result['sha256']}"
    finally:
        events = root / "reports/bigdata/import_events.jsonl"
        events.parent.mkdir(parents=True, exist_ok=True)
        with events.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"time_utc": datetime.now(timezone.utc).isoformat(), "dataset": name,
                                     "status": status, "detail": detail}) + "\n")
    return result


def import_summaries(db, root: Path = ROOT) -> dict:
    for item in json.loads((root / "data/metadata/datasets.json").read_text())["datasets"]:
        db.dataset_metadata.update_one({"_id": item["id"]}, {"$set": {"original_url": item["original_url"], "archive_sha256": item["sha256"], "license": item["license"], "provenance": item["records"]}}, upsert=True)
        path = root / "reports" / "quality" / f"{item['id']}.json"
        report = json.loads(path.read_text())
        db.data_quality_reports.update_one({"_id": item["id"]}, {"$set": {"source_dataset": item["id"], "report": report}}, upsert=True)
    model = root / "ml" / "registry.json"
    registry = json.loads(model.read_text())
    digest = fingerprint(model)
    for task, value in registry["tasks"].items():
        db.model_experiments.update_one({"_id": task}, {"$set": {"source_dataset": value["dataset_id"], "registry_sha256": digest, "selected_model": value["selected_model"], "experiment_count": len(value["trials"]), "research_only": True}}, upsert=True)
    return {"quality_reports": db.data_quality_reports.count_documents({}), "model_experiments": db.model_experiments.count_documents({})}


def import_all(db, root: Path = ROOT) -> list[dict]:
    create_indexes(db)
    results = [import_dataset(db, name, root) for name in ("heart", "diabetes", "stroke", "patients", "encounters")]
    results.append(import_summaries(db, root))
    return results
