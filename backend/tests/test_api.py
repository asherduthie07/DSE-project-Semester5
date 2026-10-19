"""Phase VI-A contract tests against existing verified research artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.core.errors import unavailable
from backend.app.main import create_app
from mediscope.ml.prediction import predict_case

ROOT = Path(__file__).resolve().parents[2]
BASE = "/api/v1"


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app()) as api:
        yield api


def test_health_readiness_and_powerbi_truth(client):
    assert client.get(BASE + "/health").json() == {"status": "READY", "service": "mediscope-api"}
    response = client.get(BASE + "/system/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["datasets"]["status"] == "READY"
    assert data["components"]["trained_models"]["status"] == "READY"
    assert data["components"]["powerbi"]["status"] == "DEGRADED"
    assert data["components"]["mongodb"]["status"] in {"READY", "UNAVAILABLE", "DEGRADED"}


def test_dataset_metadata_summary_quality_and_schema(client):
    items = client.get(BASE + "/datasets").json()["datasets"]
    assert {item["id"] for item in items} == {"uci_cleveland_heart", "uci_early_diabetes", "kaggle_stroke", "synthea_csv"}
    heart = client.get(BASE + "/datasets/uci_cleveland_heart/summary").json()
    quality = json.loads((ROOT / "reports/quality/uci_cleveland_heart.json").read_text())
    assert heart["rows"]["heart"] == 303
    assert heart["source_sha256"] == quality["source"]["sha256"]
    assert client.get(BASE + "/datasets/uci_cleveland_heart/quality").json()["tables"] == quality["tables"]
    schema = client.get(BASE + "/datasets/synthea_csv/schema").json()
    assert schema["tables"]["encounters"]["rows"] == 53346
    assert "Id" not in schema["tables"]["patients"]["record_fields"]
    assert "PATIENT" not in schema["tables"]["encounters"]["record_fields"]


def test_records_pagination_filter_and_redaction(client):
    url = BASE + "/datasets/uci_early_diabetes/records"
    page = client.get(url, params={"offset": 4, "limit": 3, "filter_field": "class", "filter_value": "Positive"}).json()
    assert page["source_rows"] == 520 and page["total"] == 320 and len(page["items"]) == 3
    assert all(row["class"] == "Positive" for row in page["items"])
    assert client.get(url, params={"limit": 101}).status_code == 422
    assert client.get(url, params={"filter_field": "secret", "filter_value": "x"}).status_code == 422
    assert client.get(BASE + "/datasets/synthea_csv/records").status_code == 422
    synthetic = client.get(BASE + "/datasets/synthea_csv/records", params={"table": "patients", "limit": 2}).json()
    assert synthetic["source_rows"] == 1171
    assert all(not any(k in row for k in ("Id", "FIRST", "LAST", "SSN", "ADDRESS", "BIRTHDATE")) for row in synthetic["items"])
    stroke = client.get(BASE + "/datasets/kaggle_stroke/records", params={"limit": 2}).json()
    assert all("id" not in row for row in stroke["items"])


def test_analytics_tables_and_chart_are_saved_values(client):
    path = BASE + "/analytics/uci_cleveland_heart"
    chart = client.get(path + "/charts").json()["charts"][0]
    assert chart["categories"] == ["0", "1"] and chart["values"] == [164, 139] and chart["sample_size"] == 303
    original = json.loads((ROOT / "reports/eda/uci_cleveland_heart.json").read_text())
    assert client.get(path + "/hypotheses").json()["hypotheses"] == original["hypotheses"]
    correlations = client.get(path + "/correlations").json()["tables"]["correlations"]
    assert correlations[0]["n"] == 303
    assert client.get(BASE + "/analytics/synthea_csv/charts").json()["charts"][0]["sample_size"] == 53346


def test_models_comparison_matrices_curves_and_explanations(client):
    registry = json.loads((ROOT / "ml/registry.json").read_text())["tasks"]
    for task in registry:
        detail = client.get(BASE + f"/models/{task}").json()
        assert detail["selected_model"] == registry[task]["selected_model"]
        comparison = client.get(BASE + f"/models/{task}/comparison").json()
        assert len(comparison["trials"]) == 5
        selected = next(row for row in comparison["trials"] if row["selected"])
        assert selected["cv_mean"] == registry[task]["trials"][detail["selected_model"]]["cv_mean"]
        matrices = client.get(BASE + f"/models/{task}/confusion-matrices").json()["matrices"]
        assert matrices[detail["selected_model"]]["matrix"] == registry[task]["trials"][detail["selected_model"]]["test"]["confusion_matrix"]
        assert client.get(BASE + f"/models/{task}/curves").json()["curves"][detail["selected_model"]]["roc"]
        explanation = client.get(BASE + f"/models/{task}/explanations").json()
        assert "local_development_example" not in explanation["explanation"]


def test_predictions_match_phase4_engine_and_reject_bad_values(client, caplog):
    for task in ("heart", "diabetes", "stroke"):
        case = json.loads((ROOT / "examples" / f"{task}_case.json").read_text())
        result = client.post(BASE + f"/predictions/{task}", json={"features": case})
        assert result.status_code == 200, result.text
        actual = result.json()
        expected = predict_case(task, case)
        for field in ("predicted_class", "predicted_source_label", "estimated_model_score", "decision_threshold", "model_name", "model_version"):
            assert actual[field] == expected[field]
        assert actual["model_sha256"] == json.loads((ROOT / "ml/registry.json").read_text())["tasks"][task]["trials"][actual["model_name"]]["artifact"]["sha256"]
        assert actual["explanation"]["method"] == expected["explanation"]["method"]
        for observed, reference in zip(actual["explanation"]["top_changes"], expected["explanation"]["top_changes"], strict=True):
            assert observed["feature"] == reference["feature"]
            assert observed["score_change"] == pytest.approx(reference["score_change"], abs=1e-12)
        assert "feature_summary" not in actual
        assert len(client.get(BASE + f"/predictions/{task}/schema").json()["features"]) == len(case)
    bad = json.loads((ROOT / "examples/heart_case.json").read_text())
    bad["cp"] = "SECRET_MEDICAL_VALUE"
    invalid = client.post(BASE + "/predictions/heart", json={"features": bad})
    assert invalid.status_code == 422 and invalid.json()["error"]["code"] == "INVALID_FEATURES"
    assert "SECRET_MEDICAL_VALUE" not in invalid.text and "SECRET_MEDICAL_VALUE" not in caplog.text
    bad["age"] = -4
    assert client.post(BASE + "/predictions/heart", json={"features": bad}).status_code == 422
    assert client.post(BASE + "/predictions/heart", json={"features": {"age": 50}}).status_code == 422


def test_bigdata_saved_evidence_is_real_and_live_failure_is_safe(client, monkeypatch):
    evidence = client.get(BASE + "/bigdata/mapreduce/results").json()
    assert evidence["final_state"] == "SUCCEEDED" and evidence["total"] == 53346
    assert evidence["counts"]["ambulatory"] == 18936
    assert evidence["current_services"]["hdfs"]["status"] in {"READY", "DEGRADED", "UNAVAILABLE"}
    services = client.app.state.services
    monkeypatch.setattr(services.bigdata, "_db", lambda: (_ for _ in ()).throw(unavailable("MongoDB")))
    response = client.get(BASE + "/bigdata/collections")
    assert response.status_code == 503 and response.json()["error"]["code"] == "UNAVAILABLE"
    assert client.get(BASE + "/bigdata/aggregations", params={"query": "encounters_by_class"}).status_code == 503
    assert client.get(BASE + "/datasets/uci_cleveland_heart/summary").status_code == 200


def test_saved_job_evidence_missing_does_not_become_a_success(client, monkeypatch, tmp_path):
    from dataclasses import replace

    services = client.app.state.services
    with monkeypatch.context() as patch:
        patch.setattr(services.bigdata, "settings", replace(services.bigdata.settings, project_root=tmp_path))
        response = client.get(BASE + "/bigdata/status").json()
        assert response["saved_mapreduce_evidence"]["status"] == "NOT_VERIFIED"
        assert client.get(BASE + "/bigdata/mapreduce/results").status_code == 503


def test_unavailable_selected_model_does_not_stop_other_routes(client, monkeypatch):
    services = client.app.state.services
    with monkeypatch.context() as patch:
        patch.setattr(services.models, "loaded", {})
        assert client.post(BASE + "/predictions/heart", json={"features": {"age": 55}}).status_code == 503
        assert client.get(BASE + "/health").status_code == 200
        assert client.get(BASE + "/system/readiness").json()["components"]["trained_models"]["status"] == "UNAVAILABLE"


def test_missing_artifact_and_unknown_routes_are_safe(client, monkeypatch, tmp_path):
    services = client.app.state.services
    with monkeypatch.context() as patch:
        patch.setattr(services.analytics, "root", tmp_path)
        services.analytics.report.cache_clear()
        response = client.get(BASE + "/analytics/uci_cleveland_heart/overview")
        assert response.status_code == 503 and "tmp" not in response.text
    services.analytics.report.cache_clear()
    assert client.get(BASE + "/datasets/unknown/summary").status_code == 404
    assert client.get(BASE + "/models/unknown").status_code == 404
    assert client.get(BASE + "/reports/not-approved").status_code == 404
    assert client.get(BASE + "/bigdata/aggregations", params={"query": "$where"}).status_code == 404


def test_missing_project_artifacts_and_invalid_mongo_uri_do_not_block_liveness(tmp_path):
    from dataclasses import replace
    from backend.app.core.config import Settings

    settings = replace(Settings.from_env(), project_root=tmp_path, mongo_uri="://invalid")
    with TestClient(create_app(settings)) as api:
        assert api.get(BASE + "/health").status_code == 200
        readiness = api.get(BASE + "/system/readiness").json()
        assert readiness["status"] == "UNAVAILABLE"
        assert readiness["components"]["datasets"]["status"] == "UNAVAILABLE"
        assert readiness["components"]["mongodb"]["status"] == "UNAVAILABLE"
        assert api.get(BASE + "/datasets").status_code == 503


def test_cors_and_openapi_contract(client):
    permitted = client.options(BASE + "/health", headers={"Origin": "http://localhost:4200", "Access-Control-Request-Method": "GET"})
    assert permitted.headers.get("access-control-allow-origin") == "http://localhost:4200"
    denied = client.options(BASE + "/health", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"})
    assert denied.headers.get("access-control-allow-origin") is None
    paths = client.get("/openapi.json").json()["paths"]
    assert "/api/v1/predictions/{task}" in paths and "/api/v1/bigdata/mapreduce/results" in paths
    assert not any("delete" in methods or "put" in methods for methods in paths.values())
