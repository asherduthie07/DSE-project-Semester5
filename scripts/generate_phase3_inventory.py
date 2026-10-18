"""Snapshot every changed Phase III file before the Phase III commit."""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

from mediscope.cli import PROJECT_ROOT, sha256


def main() -> int:
    lines = subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=PROJECT_ROOT, text=True).splitlines()
    target = PROJECT_ROOT / "reports" / "tables" / "phase3" / "artifact_inventory.csv"
    listed = {line[3:] for line in lines if len(line) > 3}
    listed.add(str(target.relative_to(PROJECT_ROOT)))
    with target.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["path", "sha256", "bytes"], lineterminator="\n")
        writer.writeheader()
        for name in sorted(listed):
            path = PROJECT_ROOT / name
            if not path.is_file():
                continue
            writer.writerow({"path": name, "sha256": "self" if path == target else sha256(path),
                             "bytes": "self" if path == target else path.stat().st_size})
    print(f"{target}: {len(listed)} paths including self")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
