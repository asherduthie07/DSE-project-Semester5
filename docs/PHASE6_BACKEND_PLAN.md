# Phase VI-A backend implementation plan

Status: design recorded before backend implementation, 2026-10-19.

## Reuse and trust boundaries

- Read the Phase I prepared CSVs through `mediscope.eda.runner.load_prepared`, which checks source lineage, SHA-256, ordered columns, row counts, targets and Synthea relationships. Cache verified tables in the application process. Expose explicit safe columns only; require a Synthea table choice.
- Read Phase II EDA JSON and named CSV tables without recomputing statistics. Read Phase III approved figure metadata and Power BI static verification status. Power BI Desktop and Service remain unverified.
- Read Phase IV `ml/registry.json`; load only the three selected full-model artifacts through `mediscope.ml.registry.load_model`, which validates registry path and checksum before joblib deserialization. Keep the loaded pipelines in lifespan state. Reuse Phase IV input validation, scoring and local explanation helpers. No training or changes to split, threshold or model bytes.
- Use a PyMongo client managed by lifespan. Test availability on read requests; only named Phase V collection and aggregation reads are available. Read Hadoop evidence from the final Phase V bundle only after verifying its success marker, application status, reducer counts and prepared-source checksum. Probe current HDFS/YARN HTTP endpoints separately; evidence of an earlier successful job does not prove present availability.

## Architecture

`backend/app/main.py` creates the versioned FastAPI app and lifespan. `core` owns configuration and safe errors. `services` own dataset, analytics, models, prediction, big-data, readiness and artifact logic. `routers` contain only request validation and service calls. `schemas` provide response and request models. `dependencies` reads services from application state. `middleware` records method, path template, status and duration without request bodies, query values or medical features.

## Availability and security

The API starts with optional MongoDB/Hadoop unavailable. Readiness uses READY, DEGRADED, UNAVAILABLE and NOT_VERIFIED per component. Static data/model failures yield clear 503 responses; invalid task/dataset/input yields 404/422. Error bodies contain a stable code and safe message. No arbitrary filesystem path, command, MongoDB write or unregistered artifact can be selected by a caller. CORS defaults to local development origins. The application binds to loopback by default; access control is required before any nonlocal deployment.

## Verification sequence

1. Confirm baseline tests (75 passed, 3 default skips on this Mac).
2. Implement services and thin routers from the specification in `PHASE6_API_SPEC.md`.
3. Add API tests against Phase I–V saved source artifacts, with MongoDB/Hadoop availability simulated in unit tests and a separate live request smoke test.
4. Run the complete prior suite plus new API tests, generate OpenAPI JSON, and verify actual HTTP responses using a local server.
5. Record live and unavailable states precisely in `PHASE6A_VERIFICATION.md`, update project status, then stop at Phase VI-A.
