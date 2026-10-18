"""Reconcile actual Hadoop reducer output with the Phase I source table."""
from __future__ import annotations

from pathlib import Path

from big_data.mongodb.connection import BigDataError
from big_data.mongodb.import_data import ROOT, read_source


def verify(path: Path, root: Path = ROOT) -> dict:
    if not path.is_file():
        raise BigDataError(f"Hadoop output missing: {path}")
    actual = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) != 2 or not parts[0] or parts[0] in actual:
            raise BigDataError(f"Malformed or duplicate reducer row: {line!r}")
        try:
            actual[parts[0]] = int(parts[1])
        except ValueError as exc:
            raise BigDataError(f"Noninteger reducer count: {line!r}") from exc
    source, digest = read_source("encounters", root)
    expected = source["ENCOUNTERCLASS"].value_counts().to_dict()
    if actual != expected:
        raise BigDataError(f"MapReduce mismatch: actual={actual}, expected={expected}")
    return {"status": "PASS", "counts": dict(sorted(actual.items())), "total": sum(actual.values()), "source_sha256": digest}
