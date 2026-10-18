"""Cross-platform driver for a genuine Hadoop Streaming job."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from big_data.hadoop.prepare_input import prepare
from big_data.hadoop.verify_output import verify
from big_data.mongodb.connection import BigDataError
from big_data.mongodb.import_data import ROOT

COMPOSE = ["docker", "compose", "-f", "docker/compose.bigdata.yml"]


def command(args: list[str], root: Path = ROOT, timeout: int = 600, include_stderr: bool = False) -> str:
    try:
        result = subprocess.run(args, cwd=root, text=True, capture_output=True, timeout=timeout, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise BigDataError(f"Command unavailable or timed out: {args}: {exc}") from exc
    if result.returncode:
        raise BigDataError(f"Command failed ({result.returncode}): {args}\n{result.stderr[-3000:]}")
    return result.stdout + result.stderr if include_stderr else result.stdout


def run(root: Path = ROOT) -> dict:
    evidence = root / "reports/bigdata"
    evidence.mkdir(parents=True, exist_ok=True)
    prepared = prepare(evidence / "encounter_classes.txt", root)
    log = []
    base = COMPOSE + ["exec", "-T", "namenode"]
    try:
        log.append(command(base + ["hdfs", "dfs", "-mkdir", "-p", "/mediscope/input"], root))
        log.append(command(base + ["hdfs", "dfs", "-put", "-f", "/workspace/reports/bigdata/encounter_classes.txt", "/mediscope/input/encounter_classes.txt"], root))
        log.append(command(base + ["hdfs", "dfs", "-ls", "/mediscope/input"], root))
        # A previous successful output cannot be mistaken for this run.
        command(base + ["hdfs", "dfs", "-rm", "-r", "-f", "/mediscope/output/encounter_counts"], root)
        script = 'hadoop jar "$(find /opt/hadoop/share/hadoop/tools/lib -name "hadoop-streaming*.jar" | head -1)" -D mapreduce.job.name=mediscope-encounter-counts -files /workspace/big_data/hadoop/mapper.py,/workspace/big_data/hadoop/reducer.py -mapper "python3 mapper.py" -reducer "python3 reducer.py" -input /mediscope/input/encounter_classes.txt -output /mediscope/output/encounter_counts'
        start = time.perf_counter()
        log.append(command(base + ["bash", "-lc", script], root, timeout=1800, include_stderr=True))
        job_seconds = time.perf_counter() - start
        output = command(base + ["bash", "-lc", "hdfs dfs -cat /mediscope/output/encounter_counts/part-*"], root)
    except BigDataError as exc:
        (evidence / "hadoop_job.log").write_text("\n".join(log) + f"\nFAIL: {exc}\n", encoding="utf-8")
        raise
    (evidence / "hadoop_job.log").write_text("\n".join(log), encoding="utf-8")
    output_path = evidence / "hadoop_encounter_counts.tsv"
    output_path.write_text(output, encoding="utf-8")
    result = verify(output_path, root)
    result.update({"job_seconds": job_seconds, "prepared": prepared, "execution": "Hadoop Streaming via YARN"})
    (evidence / "hadoop_verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result
