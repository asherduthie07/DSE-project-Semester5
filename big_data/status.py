"""Live Phase V service checks; unavailable services are BLOCKED."""
from __future__ import annotations

import json
import subprocess

from big_data.mongodb.import_data import ROOT


def check(command: list[str]) -> dict:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status": "BLOCKED", "detail": str(exc)}
    return {"status": "PASS" if result.returncode == 0 else "FAIL", "detail": (result.stdout + result.stderr)[-5000:]}


def main() -> int:
    docker = check(["docker", "info", "--format", "{{.ServerVersion}} {{.Architecture}} {{.MemTotal}}"])
    if docker["status"] != "PASS":
        print(json.dumps({"docker": docker, "mongodb": {"status": "BLOCKED"}, "hdfs": {"status": "BLOCKED"}, "yarn": {"status": "BLOCKED"}}, indent=2))
        return 2
    from big_data.mongodb.connection import BigDataError, connect
    try:
        client = connect()
        mongo = {"status": "PASS", "version": client.server_info()["version"]}
        client.close()
    except BigDataError as exc:
        mongo = {"status": "FAIL", "detail": str(exc)}
    base = ["docker", "compose", "-f", str(ROOT / "docker/compose.bigdata.yml"), "exec", "-T"]
    hdfs = check(base + ["namenode", "hdfs", "dfsadmin", "-report"])
    yarn = check(base + ["resourcemanager", "yarn", "node", "-list"])
    if hdfs["status"] == "PASS" and "Live datanodes (1)" not in hdfs["detail"]:
        hdfs["status"] = "FAIL"
    if yarn["status"] == "PASS" and not any("TotalNodes:1" in line.replace(" ", "") for line in yarn["detail"].splitlines()):
        yarn["status"] = "FAIL"
    print(json.dumps({"docker": docker, "mongodb": mongo, "hdfs": hdfs, "yarn": yarn}, indent=2))
    return 0 if all(x["status"] == "PASS" for x in (mongo, hdfs, yarn)) else 2
