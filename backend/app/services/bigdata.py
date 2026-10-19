"""Live read-only MongoDB access and independently checked saved Hadoop evidence."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from pymongo import MongoClient
from pymongo.errors import ConfigurationError, InvalidURI, PyMongoError

from backend.app.core.config import Settings
from backend.app.core.errors import unavailable
from backend.app.core.json_safe import clean
from backend.app.services.datasets import DatasetService
from big_data.mongodb.aggregations import QUERIES, aggregate, reconcile
from big_data.mongodb.connection import DATABASE
from big_data.mongodb.schema import COLLECTIONS

EXTRA_COLLECTIONS = ("dataset_metadata", "data_quality_reports", "model_experiments")


class BigDataService:
    def __init__(self, settings: Settings, datasets: DatasetService) -> None:
        self.settings = settings
        self.datasets = datasets
        try:
            self.client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=1200, connectTimeoutMS=1200)
        except (ConfigurationError, InvalidURI, ValueError):
            self.client = None

    def close(self) -> None:
        if self.client is not None:
            self.client.close()

    def _db(self):
        if self.client is None:
            raise unavailable("MongoDB")
        try:
            self.client.admin.command("ping")
            return self.client[DATABASE]
        except PyMongoError as exc:
            raise unavailable("MongoDB") from exc

    def _expected(self) -> dict[str, int]:
        mapping = {"heart": ("uci_cleveland_heart", "heart"), "diabetes": ("uci_early_diabetes", "diabetes"),
                   "stroke": ("kaggle_stroke", "stroke"), "patients": ("synthea_csv", "patients"),
                   "encounters": ("synthea_csv", "encounters")}
        return {COLLECTIONS[name][0]: len(self.datasets.table(dataset_id, table)[1]) for name, (dataset_id, table) in mapping.items()}

    def collections(self) -> dict[str, Any]:
        db = self._db()
        names = [item[0] for item in COLLECTIONS.values()] + list(EXTRA_COLLECTIONS)
        try:
            counts = {name: db[name].count_documents({}) for name in names}
        except PyMongoError as exc:
            raise unavailable("MongoDB") from exc
        expected = self._expected()
        matches = all(counts[k] == v for k, v in expected.items())
        return {"status": "READY" if matches else "DEGRADED",
                "database": DATABASE, "counts": counts,
                "source_counts_match": matches}

    def aggregation(self, query: str) -> dict[str, Any]:
        if query not in QUERIES:
            from backend.app.core.errors import missing
            raise missing("aggregation")
        if not self.collections()["source_counts_match"]:
            raise unavailable("Verified MongoDB import")
        try:
            db = self._db()
            reconcile(db)
            rows = aggregate(db, query)
        except (PyMongoError, RuntimeError, OSError, ValueError) as exc:
            raise unavailable("MongoDB aggregation") from exc
        return clean({"query": query, "collection": QUERIES[query][0], "rows": rows,
                      "denominator": "patients" if query == "patients_by_gender" else "encounters" if "encounter" in query else "records"})

    @staticmethod
    def _get_json(url: str) -> Any:
        with urlopen(url, timeout=1.5) as response:
            return json.load(response)

    def live_status(self) -> dict[str, Any]:
        try:
            self._db()
        except Exception:
            mongo = {"status": "UNAVAILABLE", "message": "MongoDB is not reachable."}
        else:
            try:
                reconciled = self.collections()["source_counts_match"]
                mongo = {"status": "READY" if reconciled else "DEGRADED",
                         "message": "MongoDB import counts match prepared tables." if reconciled else "MongoDB is reachable but imported table counts do not match prepared data."}
            except Exception:
                mongo = {"status": "NOT_VERIFIED", "message": "MongoDB is reachable but import counts could not be verified."}
        try:
            data = self._get_json(self.settings.hdfs_url + "/jmx?qry=Hadoop:service=NameNode,name=FSNamesystemState")
            beans = data.get("beans", [])
            live = int(beans[0].get("NumLiveDataNodes", 0)) if beans else 0
            hdfs = {"status": "READY" if live > 0 else "DEGRADED", "message": f"NameNode reports {live} live DataNode(s)."}
        except (OSError, HTTPError, URLError, ValueError, KeyError, TypeError):
            hdfs = {"status": "UNAVAILABLE", "message": "NameNode status endpoint is not reachable."}
        try:
            data = self._get_json(self.settings.yarn_url + "/ws/v1/cluster/nodes")
            nodes = data.get("nodes", {}).get("node") or []
            running = sum(node.get("state") == "RUNNING" for node in nodes)
            yarn = {"status": "READY" if running > 0 else "DEGRADED", "message": f"YARN reports {running} running NodeManager(s)."}
        except (OSError, HTTPError, URLError, ValueError, KeyError, TypeError):
            yarn = {"status": "UNAVAILABLE", "message": "YARN status endpoint is not reachable."}
        return {"mongodb": mongo, "hdfs": hdfs, "yarn": yarn}

    def evidence(self) -> dict[str, Any]:
        root = self.settings.project_root
        try:
            marker = json.loads((root / "reports/bigdata/final/latest.json").read_text(encoding="utf-8"))
            relative = Path(marker["path"])
            folder = (root / relative).resolve()
            if folder.parent != (root / "reports/bigdata/final").resolve():
                raise ValueError("evidence path outside final bundle")
            result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
            verified = json.loads((folder / "hadoop_verification.json").read_text(encoding="utf-8"))
            reducer = json.loads((folder / "mapreduce_results.json").read_text(encoding="utf-8"))
            status = (folder / "yarn_application_status.log").read_text(encoding="utf-8")
            listing = (folder / "hdfs_listing.log").read_text(encoding="utf-8")
            _, frame = self.datasets.table("synthea_csv", "encounters")
            expected = {str(k): int(v) for k, v in frame["ENCOUNTERCLASS"].value_counts().items()}
            checks = (result["status"] == "PASS" and verified["status"] == "PASS" and
                      verified["execution"] == "Hadoop Streaming via YARN" and
                      reducer["final_state"] == "SUCCEEDED" and
                      reducer["application_id"] == result["application_id"] and
                      reducer["counts"] == result["counts"] == verified["counts"] == expected and
                      reducer["source_sha256"] == verified["source_sha256"] and
                      "Final-State : SUCCEEDED" in status and result["application_id"] in status and
                      "/mediscope/output/encounter_counts/_SUCCESS" in listing)
            if not checks:
                raise ValueError("saved job evidence does not reconcile")
            return {"status": "READY", "run_id": marker["run_id"], "application_id": result["application_id"],
                    "job_id": result["job_id"], "final_state": "SUCCEEDED", "counts": expected,
                    "total": sum(expected.values()), "source_sha256": verified["source_sha256"],
                    "evidence_path": str(relative), "note": "Saved verified execution evidence; current HDFS/YARN availability is reported separately."}
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return {"status": "NOT_VERIFIED", "message": "A reconciled Hadoop execution evidence bundle is unavailable."}

    def jobs(self) -> dict[str, Any]:
        evidence = self.evidence()
        if evidence["status"] != "READY":
            raise unavailable("Verified Hadoop job evidence")
        result = {k: evidence[k] for k in ("status", "run_id", "application_id", "job_id", "final_state", "source_sha256", "evidence_path", "note")}
        current = self.live_status()
        result["current_services"] = {key: current[key] for key in ("hdfs", "yarn")}
        return result

    def results(self) -> dict[str, Any]:
        evidence = self.evidence()
        if evidence["status"] != "READY":
            raise unavailable("Verified Hadoop results")
        current = self.live_status()
        return {**evidence, "current_services": {key: current[key] for key in ("hdfs", "yarn")}}
