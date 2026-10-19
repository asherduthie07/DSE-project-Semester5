# Phase VI-A FastAPI backend verification

Date: 2026-10-19, Intel Mac (`x86_64`). Scope: backend only. **Decision: PASS for the local research API; live Phase V services are currently unavailable.** Angular and Phase VII were not started.

## Files delivered

New: `backend/app/` (core, schemas, services, dependencies, middleware, routers and main entry point), `backend/tests/test_api.py`, `backend/openapi.json`, `docs/PHASE6_BACKEND_PLAN.md`, `docs/PHASE6_API_SPEC.md`, `docs/HOW_TO_RUN_BACKEND.md`, this verification file, and `reports/backend/` live responses/test output. Updated: `pyproject.toml`, `.env.example`, `README.md`, and `docs/PROJECT_STATUS.md`. No Phase I–IV artifact or Phase V Docker volume was modified.

## Reused artifacts and contracts

- Phase I: `mediscope.eda.runner.load_prepared` verified the four registered datasets and five prepared tables against quality report checksums, ordered columns, row counts, targets and Synthea relationships. Record routes expose only safe columns and bounded pages; Synthea patients and encounters require separate table selection.
- Phase II/III: the API reads saved EDA JSON/CSV tables and approved chart paths; it does not recompute inferential statistics. Power BI static export artifacts exist, while Desktop/Service runtime remains NOT VERIFIED.
- Phase IV: lifespan loaded the three selected full pipelines through `load_model`, which checked trusted registry paths and artifact SHA-256 values. Prediction responses matched `mediscope.ml.prediction.predict_case` on the three fictional example fixtures for class, score, model and threshold; local explanation score changes matched within `1e-12` floating-point tolerance. No model training, threshold change or artifact mutation occurred.
- Phase V: `reports/bigdata/final/20261018T211007Z/` independently reconciled saved reducer counts and source SHA-256 against the prepared Synthea encounters, checked `Final-State: SUCCEEDED` and HDFS `_SUCCESS`. The saved job is `application_1792354467390_0007` / `job_1792354467390_0007`, total 53,346. This is past execution evidence, not a claim of current service availability.

## Actual execution and requests

Before implementation, the existing suite returned **75 passed, 3 skipped** in 12.61 seconds. After adding backend tests, the full suite returned **87 passed, 3 skipped** in 19.59 seconds. `pip check` reported no broken requirements. FastAPI 0.146.0, Pydantic 2.14.1, Uvicorn 0.54.0, HTTPX 0.28.1 and PyMongo 4.19.0 were installed in `.venv`.

The server started using:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

A live HTTP `GET /api/v1/health` returned `{"status":"READY","service":"mediscope-api"}`. A live heart prediction using the repository's fictional example returned class `0`, model `logistic_regression`, version `phase4-v1`, score `0.4453247126343259` and threshold `0.5`; the response included the Phase IV local explanation and research-only warning. Live responses were saved in `reports/backend/live_readiness.json`, `live_bigdata_status.json`, and `live_heart_prediction.json`. `backend/openapi.json` is the generated machine-readable OpenAPI snapshot (27 paths).

Current live readiness was **DEGRADED**: datasets, EDA and all three selected models READY; MongoDB, HDFS and YARN UNAVAILABLE; saved MapReduce job evidence READY; Power BI DEGRADED because Desktop/Service runtime is unverified. The Docker command `docker compose -f docker/compose.bigdata.yml ps -a` failed to connect to the daemon socket (`no such file or directory`) in this session. The three Docker-dependent tests were therefore not enabled; they were not reported as passing. Phase V's earlier live import/job evidence remains preserved in its own verification bundle.

## API test coverage

The 12 backend tests cover liveness/readiness, true dataset counts and checksums, redacted synthetic records, bounded pagination and filtering, EDA chart and hypothesis agreement, model comparison/matrix/curve/explanation agreement, exact schema, prediction equivalence and invalid inputs, safe error messages and access logs, optional MongoDB failure, missing Hadoop evidence, missing EDA/project artifacts, invalid MongoDB configuration, report allowlists, CORS and OpenAPI routes. No previous test was removed or weakened.

## Gate matrix

| Requirement | Decision | Evidence |
|---|---|---|
| Modular FastAPI app and lifespan resources | PASS | `backend/app/`, server startup/shutdown |
| Versioned OpenAPI and local CORS | PASS | 27 paths in `backend/openapi.json`; CORS test |
| Health and component readiness | PASS | Live responses and tests |
| Verified dataset metadata, quality and safe records | PASS | Phase I checksum loader and API tests |
| Phase II analytics and Phase III chart data | PASS | Saved report/table comparisons |
| Phase IV model comparison and prediction | PASS | Registry/artifact SHA load and three-example equivalence |
| Invalid prediction and safe errors | PASS | API tests; no submitted feature value in logs/errors |
| Live MongoDB API reads in this session | BLOCKED | Docker daemon socket absent; routes report UNAVAILABLE |
| Past genuine Hadoop execution evidence | PASS | Saved YARN/HDFS proof independently reconciled |
| Current HDFS/YARN availability in this session | BLOCKED | Docker daemon absent; status reports UNAVAILABLE |
| Power BI static artifact registry | PASS | Curated allowlist and runtime caveat |
| Power BI Desktop/Service runtime | NOT VERIFIED | Prior Phase III runtime gate remains open |
| Complete project regression tests | PASS | 87 passed; 3 Docker tests skipped |
| Windows backend runtime | NOT TESTED | Windows instructions documented; no Windows host run |
| Angular integration readiness | READY WITH DEPENDENCIES | Versioned API and OpenAPI ready; live Big Data routes require Docker |

## Limitations

The server is intended for local development and academic demonstration. It has no authentication or deployment hardening for a public network. Model scores and explanations are research outputs, not clinical diagnoses, calibrated clinical risk or treatment advice. The Phase IV artifact manifest has eight pre-existing hash mismatches noted in Phase V verification; the selected registry-listed model artifacts passed their own SHA-256 checks and direct prediction equivalence here. The backend did not modify prior-phase data, reports, models, test splits or thresholds.
