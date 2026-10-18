"""Fast Phase V checks; no unavailable Docker service is treated as a pass."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from big_data.hadoop.mapper import map_lines
from big_data.hadoop.prepare_input import prepare
from big_data.hadoop.reducer import reduce_lines
from big_data.hadoop.verify_output import verify
from big_data.mongodb.connection import BigDataError
from big_data.mongodb.import_data import ROOT, read_source, records
from big_data.mongodb.schema import INDEXES


@pytest.mark.parametrize("name,count", [("heart", 303), ("diabetes", 520), ("stroke", 5110), ("patients", 1171), ("encounters", 53346)])
def test_sources_checked(name: str, count: int) -> None:
    frame, digest = read_source(name)
    assert len(frame) == count and len(digest) == 64


def test_duplicate_profiles_keep_distinct_ids() -> None:
    frame, digest = read_source("diabetes")
    docs = records("diabetes", frame, digest)
    assert len({doc["_id"] for doc in docs}) == 520
    assert frame.duplicated().sum() == 269


def test_synthetic_relationships_and_privacy() -> None:
    patients, digest = read_source("patients")
    encounters, _ = read_source("encounters")
    assert set(encounters["PATIENT"]) <= set(patients["Id"])
    sample = records("patients", patients.head(1), digest)[0]
    assert sample["synthetic"] and "SSN" not in sample and "FIRST" not in sample and "ADDRESS" not in sample


def test_mapreduce_local_components_match_pandas(tmp_path: Path) -> None:
    output = tmp_path / "input.txt"
    prepared = prepare(output)
    mapped = list(map_lines(output.open(encoding="utf-8")))
    reduced = list(reduce_lines(sorted(mapped)))
    result_path = tmp_path / "part-00000"
    result_path.write_text("".join(reduced), encoding="utf-8")
    result = verify(result_path)
    assert prepared["rows"] == result["total"] == 53346


def test_mapper_reducer_reject_invalid() -> None:
    with pytest.raises(ValueError):
        list(map_lines(["ENCOUNTERCLASS\n"]))
    with pytest.raises(ValueError):
        list(map_lines(["wellness\tbad\n"]))
    with pytest.raises(ValueError):
        list(reduce_lines(["wellness\t2\n"]))
    with pytest.raises(ValueError):
        list(reduce_lines(["wellness\t1\n", "ambulatory\t1\n"]))


def test_missing_or_tampered_source_fails(tmp_path: Path) -> None:
    with pytest.raises(BigDataError, match="Missing prepared source"):
        read_source("heart", tmp_path)
    destination = tmp_path / "data/processed"
    destination.mkdir(parents=True)
    (destination / "heart.csv").write_bytes((ROOT / "data/processed/heart.csv").read_bytes() + b"\n")
    manifest = tmp_path / "reports/quality"
    manifest.mkdir(parents=True)
    (manifest / "uci_cleveland_heart.json").write_bytes((ROOT / "reports/quality/uci_cleveland_heart.json").read_bytes())
    with pytest.raises(BigDataError, match="checksum mismatch"):
        read_source("heart", tmp_path)


def test_indexes_declared_for_query_keys() -> None:
    assert ("PATIENT", 1) in INDEXES["hospital_encounters"]
    assert ("ENCOUNTERCLASS", 1) in INDEXES["hospital_encounters"]


def test_index_creation_calls_all_declared_keys() -> None:
    from big_data.mongodb.schema import create_indexes
    class Collection:
        def __init__(self):
            self.keys = []
        def create_index(self, key):
            self.keys.append(key)
            return str(key)
    class Database:
        def __init__(self):
            self.collections = {}
        def __getitem__(self, name):
            return self.collections.setdefault(name, Collection())
    db = Database()
    create_indexes(db)
    assert db.collections["hospital_encounters"].keys == [[spec] for spec in INDEXES["hospital_encounters"]]


def test_connection_failure_is_clear(monkeypatch) -> None:
    from pymongo.errors import ServerSelectionTimeoutError
    from big_data.mongodb import connection
    class FakeClient:
        @property
        def admin(self):
            raise ServerSelectionTimeoutError("offline")
    monkeypatch.setattr(connection, "MongoClient", lambda *args, **kwargs: FakeClient())
    with pytest.raises(BigDataError, match="MongoDB unavailable"):
        connection.connect()


def test_cross_platform_launchers_have_prerequisite_checks() -> None:
    mac = (ROOT / "scripts/setup_bigdata_macos.sh").read_text()
    windows = (ROOT / "scripts/setup_bigdata_windows.ps1").read_text()
    assert "docker info" in mac and "docker compose" in mac
    assert "docker info" in windows and "docker compose" in windows
