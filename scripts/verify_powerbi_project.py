"""Offline structural checks for the source PBIP (not Desktop runtime validation)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from mediscope.cli import PROJECT_ROOT
from mediscope.visualization.exports import EXPORT_NAMES, verify_exports

EXPECTED_PAGES = ["overview", "heart", "diabetes", "stroke", "hospital", "quality"]


def verify_project(root: Path = PROJECT_ROOT) -> dict[str, object]:
    verify_exports(root)
    base = root / "powerbi"
    pbip = json.loads((base / "MediScopeAI.pbip").read_text(encoding="utf-8"))
    assert pbip["artifacts"] == [{"report": {"path": "MediScopeAI.Report"}}]
    report = base / "MediScopeAI.Report"
    model = base / "MediScopeAI.SemanticModel"
    descriptor = json.loads((report / "definition.pbir").read_text(encoding="utf-8"))
    assert descriptor["datasetReference"]["byPath"]["path"] == "../MediScopeAI.SemanticModel"
    assert json.loads((model / "definition.pbism").read_text(encoding="utf-8"))["version"] == "4.2"
    pages_dir = report / "definition" / "pages"
    metadata = json.loads((pages_dir / "pages.json").read_text(encoding="utf-8"))
    assert metadata["pageOrder"] == EXPECTED_PAGES
    tables_dir = model / "definition" / "tables"
    table_files = {p.stem: p for p in tables_dir.glob("*.tmdl")}
    assert set(EXPORT_NAMES).issubset(table_files)
    definitions: dict[str, dict[str, set[str]]] = {}
    for name, path in table_files.items():
        body = path.read_text(encoding="utf-8")
        assert body.startswith(f"table {name}\n")
        assert 'File.Contents(DataRoot & "\\' in body
        assert "C:\\Users\\" not in body and "/Users/" not in body
        definitions[name] = {"columns": set(re.findall(r"^\tcolumn (.+)$", body, re.M)),
                             "measures": set(re.findall(r"^\tmeasure '([^']+)'", body, re.M))}
    parameter = (model / "definition" / "expressions.tmdl").read_text(encoding="utf-8")
    assert "__MEDISCOPE_DATA_ROOT__" in parameter
    relationships = (model / "definition" / "relationships.tmdl").read_text(encoding="utf-8")
    assert relationships.count("fromColumn:") >= 10
    visuals = 0
    for page_name in EXPECTED_PAGES:
        page = pages_dir / page_name
        spec = json.loads((page / "page.json").read_text(encoding="utf-8"))
        assert spec["name"] == page_name and spec["displayName"]
        files = sorted(page.glob("visuals/*/visual.json"))
        assert len(files) >= 4, page_name
        for path in files:
            visual = json.loads(path.read_text(encoding="utf-8"))
            assert visual["name"] == path.parent.name
            pos = visual["position"]
            assert 0 <= pos["x"] and 0 <= pos["y"] and pos["x"] + pos["width"] <= 1280 and pos["y"] + pos["height"] <= 720
            for role in visual["visual"]["query"]["queryState"].values():
                for projection in role["projections"]:
                    field = projection["field"]
                    kind = next(iter(field))
                    table = field[kind]["Expression"]["SourceRef"]["Entity"]
                    column = field[kind]["Property"]
                    assert table in definitions and column in definitions[table]["measures" if kind == "Measure" else "columns"], (path, table, column)
            visuals += 1
    return {"status": "PASS", "scope": "static only", "pages": 6, "tables": len(table_files), "visuals": visuals,
            "desktop_runtime": "NOT TESTED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(verify_project(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
