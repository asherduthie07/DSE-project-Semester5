"""Produce one validated encounter class per source CSV row."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from big_data.mongodb.connection import BigDataError
from big_data.mongodb.import_data import ROOT, read_source


def prepare(output: Path, root: Path = ROOT) -> dict:
    frame, digest = read_source("encounters", root)
    values = frame["ENCOUNTERCLASS"]
    if values.isna().any() or values.astype(str).str.contains(r"[\t\r\n]", regex=True).any():
        raise BigDataError("Missing or unsafe encounter class in source")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        for category in values:
            stream.write(f"{category}\n")
    return {"path": str(output), "rows": len(values), "source_sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(prepare(args.output))
