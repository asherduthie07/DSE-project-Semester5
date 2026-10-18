"""Time equivalent encounter-class counts without manufacturing benchmark results."""
from __future__ import annotations

import json
import time
from pathlib import Path

from big_data.hadoop.verify_output import verify
from big_data.mongodb.aggregations import aggregate
from big_data.mongodb.connection import BigDataError
from big_data.mongodb.import_data import ROOT, read_source


def compare(db, hadoop_output: Path, root: Path = ROOT) -> dict:
    start = time.perf_counter()
    frame, digest = read_source("encounters", root)
    pandas_counts = frame["ENCOUNTERCLASS"].value_counts().to_dict()
    pandas_seconds = time.perf_counter() - start
    start = time.perf_counter()
    mongo_counts = {item["_id"]: item["encounters"] for item in aggregate(db, "encounters_by_class")}
    mongo_seconds = time.perf_counter() - start
    if mongo_counts != pandas_counts:
        raise BigDataError("MongoDB counts do not match pandas source counts")
    start = time.perf_counter()
    hadoop = verify(hadoop_output, root)
    retrieval_seconds = time.perf_counter() - start
    job_evidence = hadoop_output.with_name("hadoop_verification.json")
    if not job_evidence.is_file():
        raise BigDataError(f"Missing live Hadoop job timing evidence: {job_evidence}")
    evidence = json.loads(job_evidence.read_text(encoding="utf-8"))
    if evidence.get("source_sha256") != digest or evidence.get("counts") != hadoop["counts"] or evidence.get("execution") != "Hadoop Streaming via YARN":
        raise BigDataError("Hadoop job evidence does not match retrieved output/source")
    return {"records": len(frame), "source_sha256": digest, "counts": dict(sorted(pandas_counts.items())),
            "pandas_seconds": pandas_seconds, "mongodb_aggregation_seconds": mongo_seconds,
            "hadoop_output_validation_seconds": retrieval_seconds,
            "hadoop_job_seconds": evidence["job_seconds"],
            "note": "Single local wall-clock observations, including distinct Hadoop execution and validation times; no distributed scaling conclusion."}


def save(result: dict, path: Path = ROOT / "reports/bigdata/processing_comparison.json") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
