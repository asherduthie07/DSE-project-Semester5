"""Hadoop Streaming mapper for sanitized one-class-per-line input."""
from __future__ import annotations

import sys


def map_lines(lines):
    for line in lines:
        category = line.rstrip("\r\n")
        if not category or category == "ENCOUNTERCLASS" or "\t" in category:
            raise ValueError(f"Invalid prepared encounter class: {category!r}")
        yield f"{category}\t1\n"


if __name__ == "__main__":
    try:
        sys.stdout.writelines(map_lines(sys.stdin))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(2) from exc
