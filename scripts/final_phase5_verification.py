"""Execute Phase V against existing services and retain timestamped evidence."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from big_data.mongodb.import_data import ROOT, COLLECTIONS, read_source, records
from big_data.mongodb.connection import connect
from big_data.mongodb.aggregations import QUERIES, aggregate


def snapshot() -> dict[str, str]:
    """Fingerprint earlier phase outputs without changing them."""
    result = {}
    for directory in ("data", "ml", "reports", "powerbi/exports"):
        for path in sorted((ROOT / directory).rglob("*")):
            relative = path.relative_to(ROOT)
            if path.is_file() and "bigdata" not in relative.parts and "__pycache__" not in relative.parts:
                result[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> None:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "reports/bigdata/final" / run_id
    out.mkdir(parents=True, exist_ok=False)
    env = {**os.environ, "MEDISCOPE_BIGDATA_INTEGRATION": "1", "MPLCONFIGDIR": "/private/tmp/mediscope-mpl"}
    transcript = []

    def save(name: str, value: object) -> None:
        (out / f"{name}.json").write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")

    def execute(name: str, args: list[str], timeout: int = 1800, required: bool = True) -> str:
        print(f"RUN {name}", flush=True)
        started = time.perf_counter()
        result = subprocess.run(args, cwd=ROOT, env=env, text=True, capture_output=True, timeout=timeout)
        entry = {"name": name, "argv": args, "returncode": result.returncode,
                 "seconds": time.perf_counter() - started, "stdout": result.stdout, "stderr": result.stderr}
        transcript.append(entry)
        save("commands", transcript)
        (out / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        if required and result.returncode:
            raise RuntimeError(f"{name} failed; see {out / (name + '.log')}")
        return result.stdout

    before = snapshot()
    save("earlier_artifacts_before", before)
    py = sys.executable
    cli = [py, "-m", "mediscope", "bigdata"]
    compose = ["docker", "compose", "-f", "docker/compose.bigdata.yml"]
    execute("services", compose + ["ps", "-a"])
    execute("status", cli + ["status"])
    first = json.loads(execute("import_first", cli + ["import", "--dataset", "all"]))
    execute("database_verify", cli + ["verify"])
    execute("crud", cli + ["crud"])
    for query in QUERIES:
        execute(f"aggregation_{query}", cli + ["aggregate", "--query", query])

    with connect() as client:
        db = client.mediscope_healthcare
        counts = {name: db[name].count_documents({}) for name in
                  [spec[0] for spec in COLLECTIONS.values()] + ["dataset_metadata", "data_quality_reports", "model_experiments"]}
        save("collection_counts", counts)
        before_docs = {}
        checks = {}
        for name, (collection, _, _, _) in COLLECTIONS.items():
            frame, digest = read_source(name)
            expected = {doc["_id"]: doc for doc in records(name, frame, digest)}
            actual = {doc["_id"]: doc for doc in db[collection].find({"source_dataset": name})}
            assert actual == expected, f"Document content mismatch: {name}"
            before_docs[name] = actual
            checks[name] = {"rows": len(actual), "every_imported_field_matches": True, "sha256": digest}
        checks["diabetes_duplicates_retained"] = int(read_source("diabetes")[0].duplicated().sum())
        assert checks["diabetes_duplicates_retained"] == 269
        patient_ids = {doc["Id"] for doc in before_docs["patients"].values()}
        assert all(doc["PATIENT"] in patient_ids for doc in before_docs["encounters"].values())
        checks["orphan_encounters"] = 0
        second = json.loads(execute("import_repeat", cli + ["import", "--dataset", "all"]))
        assert first == second
        for name, (collection, _, _, _) in COLLECTIONS.items():
            assert before_docs[name] == {doc["_id"]: doc for doc in db[collection].find({"source_dataset": name})}
        checks["repeat_import_same_ids_and_contents"] = True
        save("document_reconciliation", checks)

    execute("mapreduce_cli", cli + ["mapreduce", "--job", "encounter_counts"])
    # Run the full suite with the three live tests enabled, rather than counting skips as passes.
    execute("complete_tests_with_live_integration", [py, "-m", "pytest", "-v", "--junitxml=" + str(out / "tests.xml")])
    job = json.loads((ROOT / "reports/bigdata/hadoop_verification.json").read_text())
    log = (ROOT / "reports/bigdata/hadoop_job.log").read_text()
    app_id = re.findall(r"application_\d+_\d+", log)[-1]
    job_id = re.findall(r"job_\d+_\d+", log)[-1]
    assert "completed successfully" in log
    status = execute("yarn_application_status", compose + ["exec", "-T", "resourcemanager", "yarn", "application", "-status", app_id])
    assert re.search(r"Final-State\s*:\s*SUCCEEDED", status), status
    execute("yarn_application_logs", compose + ["exec", "-T", "resourcemanager", "yarn", "logs", "-applicationId", app_id], required=False)
    execute("nodemanager_task_logs", compose + ["exec", "-T", "nodemanager", "sh", "-c",
             f"find /var/log/hadoop/userlogs/{app_id} -type f \\( -name stdout -o -name stderr -o -name syslog \\) -print -exec cat {{}} \\;"])
    execute("hdfs_listing", compose + ["exec", "-T", "namenode", "hdfs", "dfs", "-ls", "/mediscope/input", "/mediscope/output/encounter_counts"])
    execute("hdfs_reducer_read", compose + ["exec", "-T", "namenode", "hdfs", "dfs", "-cat", "/mediscope/output/encounter_counts/part-00000"])
    execute("benchmark_cli", cli + ["benchmark"])
    with connect() as client:
        frame, digest = read_source("encounters")
        trials = []
        for _ in range(5):
            started = time.perf_counter()
            reference = frame.ENCOUNTERCLASS.value_counts().to_dict()
            pandas_seconds = time.perf_counter() - started
            started = time.perf_counter()
            actual = {row["_id"]: row["encounters"] for row in aggregate(client.mediscope_healthcare, "encounters_by_class")}
            mongo_seconds = time.perf_counter() - started
            assert reference == actual == job["counts"]
            trials.append({"pandas_in_memory_aggregation_seconds": pandas_seconds, "mongodb_query_seconds": mongo_seconds})
        save("aggregation_timings", {"trials": trials, "hadoop_submission_to_completion_seconds": job["job_seconds"],
                                     "rows": len(frame), "source_sha256": digest, "environment": platform.platform(),
                                     "scope": "Pandas excludes CSV loading; Mongo includes client roundtrip; Hadoop includes YARN scheduling. Warm local runs, not a scalability experiment."})
    for name, args in (
        ("phase1_integrity", [py, "scripts/verify_phase1_outputs.py"]),
        ("phase3_exports", [py, "scripts/verify_powerbi_exports.py"]),
        ("phase3_project", [py, "scripts/verify_powerbi_project.py"]),
        ("phase4_models", [py, "scripts/verify_phase4_outputs.py"]),
        ("phase4_manifest", [py, "scripts/build_phase4_manifest.py", "--check"]),
    ):
        execute(name, args, required=name != "phase4_manifest")
    after = snapshot()
    assert before == after, "An earlier phase artifact changed"
    save("earlier_artifacts_unchanged", {"status": "PASS", "files": len(before), "sha256": before})
    manifest_event = next(event for event in transcript if event["name"] == "phase4_manifest")
    from scripts.build_phase4_manifest import inventory, MANIFEST
    expected_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    actual_manifest = inventory()
    changed_manifest_paths = [path for path, digest in actual_manifest["files"].items()
                               if expected_manifest.get("files", {}).get(path) != digest]
    (out / "phase4_manifest_preexisting_mismatch.json").write_text(
        json.dumps({"status": "FAIL_PREEXISTING", "returncode": manifest_event["returncode"],
                    "phase4_independent_output_verifier": "PASS", "prior_phase_artifacts_changed_during_run": False,
                    "manifest_artifacts_changed_before_this_run": changed_manifest_paths,
                    "note": "The current Phase IV artifact hashes already differ from their tracked manifest; the live Phase V run did not change any earlier-phase files."}, indent=2) + "\n",
        encoding="utf-8")
    for filename in ("hadoop_job.log", "hadoop_verification.json", "hadoop_encounter_counts.tsv", "processing_comparison.json",
                     "service_status.json", "mongodb_reconciliation.json", "mongodb_encounters_by_class.json",
                     "import_events.jsonl", "yarn_application_0005_local_logs.txt"):
        if filename == "yarn_application_0005_local_logs.txt":
            continue  # App-specific file is saved by nodemanager_task_logs.log for the current run.
        if not (ROOT / "reports/bigdata" / filename).is_file():
            continue
        (out / filename).write_bytes((ROOT / "reports/bigdata" / filename).read_bytes())
    save("result", {"status": "PASS", "run_id": run_id, "application_id": app_id, "job_id": job_id,
                    "counts": job["counts"], "total": job["total"], "phase4_manifest": "FAIL_PREEXISTING",
                    "earlier_phase_files_changed": False, "windows_runtime": "NOT TESTED: no Windows host available"})
    (ROOT / "reports/bigdata/final/latest.json").write_text(json.dumps({"run_id": run_id, "path": str(out.relative_to(ROOT))}, indent=2) + "\n")
    print(f"PASS: {out}", flush=True)


if __name__ == "__main__":
    main()
