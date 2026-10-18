"""Fast Phase 0 checks using only standard library and pytest."""

from io import StringIO

from mediscope.cli import audit_table, health, load_registry


def test_health_reads_all_registered_datasets() -> None:
    assert health()["status"] == "ok"
    assert len(load_registry()["datasets"]) == 4


def test_audit_reports_schema_and_missing_tokens() -> None:
    table = {"columns": ["feature", "target"], "header": True, "target": "target"}
    report = audit_table(StringIO("feature,target\n1,Yes\n?,No\n1,Yes\n"), table)
    assert report["rows"] == 3
    assert report["missing_values"]["feature"] == 1
    assert report["target_class_counts"] == {"No": 1, "Yes": 2}
    assert report["duplicate_rows"] == 1
    assert report["schema_mismatches"]["column_order"] is False
