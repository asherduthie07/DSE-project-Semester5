"""Opt-in live tests; skipped tests are never evidence of live success."""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("MEDISCOPE_BIGDATA_INTEGRATION") != "1", reason="Live Docker integration not requested")


def test_live_services() -> None:
    from big_data.status import main
    assert main() == 0


def test_live_import_idempotency_and_aggregation() -> None:
    from big_data.mongodb.connection import connect
    from big_data.mongodb.import_data import import_all
    from big_data.mongodb.aggregations import aggregate
    from big_data.mongodb.schema import INDEXES
    client = connect()
    db = client.mediscope_healthcare
    first = import_all(db)
    second = import_all(db)
    assert first == second
    counts = {row["_id"]: row["encounters"] for row in aggregate(db, "encounters_by_class")}
    assert sum(counts.values()) == 53346
    assert all(db[name].index_information() for name in INDEXES)
    client.close()


def test_live_hadoop_job() -> None:
    from big_data.hadoop.run_job import run
    assert run()["total"] == 53346
