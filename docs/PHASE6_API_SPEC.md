# MediScope AI Phase VI-A API specification

Base path: `/api/v1`. Responses use JSON. The backend is a local research application, not a clinical service. Generated machine-readable OpenAPI is `backend/openapi.json`.

## Common contract

- Error: `{ "error": { "code": string, "message": string } }`. Validation errors are HTTP 422, unknown dataset/task/report names HTTP 404, unavailable verified artifact or optional live dependency HTTP 503. Internal details and credentials are never returned.
- Component state: `READY`, `DEGRADED`, `UNAVAILABLE`, `NOT_VERIFIED`; each state has a short evidence-based message. Overall readiness is `READY` when core datasets, EDA and models are ready and optional dependencies are ready; `DEGRADED` when optional dependencies are unavailable/unverified; `UNAVAILABLE` when required core artifacts cannot be used.
- Pagination: `offset` 0–100000 and `limit` 1–100 (default 20). Records return `total`, `source_rows`, `offset`, `limit`, and `items`. Exact `filter_field` plus `filter_value` is allowed only for explicit safe fields. The Synthea dataset requires `table=patients` or `table=encounters`; no mixed cohort response exists.
- Every prediction is a research-only score and class. No endpoint interprets it as clinical risk, diagnosis or treatment guidance.

## Endpoints

| Method and path | Response / source |
|---|---|
| `GET /health` | Liveness: API service only. |
| `GET /system/readiness` | Current component states plus saved Hadoop evidence state; no invented live result. |
| `GET /datasets` | Four registered datasets, source provenance and verified prepared row counts. |
| `GET /datasets/{id}/schema` | Prepared field names/types and safe exposed fields by table. |
| `GET /datasets/{id}/summary` | Phase I quality table counts, source checksum and target facts. |
| `GET /datasets/{id}/quality` | Full Phase I quality report with no local absolute paths. |
| `GET /datasets/{id}/records` | Bounded, filtered safe records from a checksummed prepared table. |
| `GET /analytics/{dataset}/overview` | Phase II report metadata, facts, provenance and caveats. |
| `GET /analytics/{dataset}/distributions` | Named Phase II frequency/outcome table rows. |
| `GET /analytics/{dataset}/correlations` | Existing Phase II correlation rows, sample sizes and missing policy. |
| `GET /analytics/{dataset}/hypotheses` | Existing preregistered results (empty when none). |
| `GET /analytics/{dataset}/charts` | Frontend chart series from Phase II tables; approved figure references. |
| `GET /models` | Three tasks and selected models from the full registry. |
| `GET /models/{task}` | Selection, version, selected artifact SHA-256, feature list and CV methodology. |
| `GET /models/{task}/comparison` | All five actual trials: parameters, CV score, threshold and held-out metrics. |
| `GET /models/{task}/confusion-matrices` | Held-out matrices and denominators from Phase IV. |
| `GET /models/{task}/curves` | Saved ROC and PR arrays when available. |
| `GET /models/{task}/explanations` | Saved selected-model explanation and limitations. |
| `GET /predictions/{task}/schema` | Exact ordered selected-pipeline feature schema, registered numeric bounds and categories. |
| `POST /predictions/{task}` | Body `{ "features": { ... } }`; class, model score, selected model, version, verified artifact SHA-256, threshold, explanation and warning. No feature summary echo. |
| `GET /bigdata/status` | Live MongoDB/HDFS/YARN availability and independently checked saved MapReduce evidence. |
| `GET /bigdata/collections` | Live allowed MongoDB document counts, or 503 if unavailable. |
| `GET /bigdata/aggregations?query=...` | One named live Phase V read-only pipeline, or 503. |
| `GET /bigdata/mapreduce/jobs` | Saved verified application/job ID, execution status and source checksum, alongside current HDFS/YARN availability. |
| `GET /bigdata/mapreduce/results` | Saved verified reducer counts plus evidence timestamp and separate current HDFS/YARN availability. |
| `GET /reports` | Curated report, methodology, chart and Power BI instruction registry. |
| `GET /reports/{key}` | Approved report metadata and text content only; no user-supplied paths. |

Dataset IDs are the registered `uci_cleveland_heart`, `uci_early_diabetes`, `kaggle_stroke` and `synthea_csv`. Model task IDs are `heart`, `diabetes` and `stroke`. Named aggregation IDs are the eight keys in `big_data.mongodb.aggregations.QUERIES`. No mutating HTTP endpoint exists.
