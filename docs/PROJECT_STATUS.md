# Project status

Updated: 2026-10-19 (Phase VI-A FastAPI backend)

## Phase VI-A: FastAPI research backend

- Added a versioned, modular, read-only FastAPI application under `backend/app/` with lifespan loading of three checksum-verified selected Phase IV models, a managed optional PyMongo client, bounded records, local CORS, safe structured errors and access logs that omit request bodies and feature values. The generated machine-readable schema contains 27 paths in `backend/openapi.json`.
- Added dataset, Phase II analytics/chart, model comparison/curve/explanation, research prediction, Phase V status/evidence, and curated report routes. The Phase V evidence adapter independently checks the saved successful Hadoop job against prepared Synthea encounters; current service availability is reported separately. Power BI Desktop/Service remains unverified.
- Baseline suite before editing: 75 passed, 3 Docker tests skipped. Phase VI-A full suite: 87 passed, 3 Docker tests skipped because the Docker daemon socket is absent in this session. A live Uvicorn server returned health, readiness, Big Data status and a prediction for the repository's fictional heart example. All three example predictions matched the Phase IV engine for class, score, model and threshold. `pip check` passed. The current MongoDB/HDFS/YARN services are UNAVAILABLE; their live API routes were not claimed as verified in this session. See `PHASE6A_VERIFICATION.md`, `PHASE6_API_SPEC.md` and `HOW_TO_RUN_BACKEND.md`.
- **Phase VI-A local backend PASS.** Windows backend runtime and Angular integration have not been tested or started. No Phase I–IV data/model outputs or Phase V persistent state were changed.

## Phase V: MongoDB and Hadoop/MapReduce

- Added PyMongo source-validated, SHA-256-checked, idempotent import code for five prepared tables, dataset metadata, quality summaries and Phase IV experiment metadata. Synthea patient/encounter keys are preserved; synthetic names and identity/address fields are excluded. Added eight aggregation queries, controlled CRUD, source/database reconciliation, and CLI commands.
- Added a pinned local Compose configuration for MongoDB 7.0.41 and Apache Hadoop 3.4.3, cross-platform setup/verification tools, sanitized encounter-class input preparation, Hadoop Streaming mapper/reducer, HDFS job driver and output verification. Added source reference tables, a chart, architecture diagrams and run instructions. A guarded one-shot initializer formats only an empty NameNode volume and preserves existing HDFS data.
- **Final live Intel Mac verification passed:** Docker 29.8.2 x86_64, MongoDB 7.0.41, HDFS (one live DataNode), and YARN (one RUNNING NodeManager). Imported all five prepared source tables; live counts were heart 303, diabetes 520, stroke 5,110, patients 1,171, encounters 53,346, plus 9 metadata, 4 quality reports and 3 model experiments. Document-level reconciliation and repeat import confirmed stable IDs/content; 269 intentional diabetes duplicate rows were retained and there were zero orphan encounters. CRUD passed; all eight MongoDB aggregation pipelines and indexes verified against pandas.
- A genuine Hadoop Streaming encounter-class job completed on YARN as `application_1792354467390_0007` / `job_1792354467390_0007`, final state SUCCEEDED. All six reducer counts and total 53,346 matched pandas and MongoDB. One measured run: pandas 0.2900 s; MongoDB 0.0569 s; Hadoop job 19.3230 s; Hadoop output validation 0.2940 s. This single-node pseudo-distributed run and small dataset cannot establish Hadoop scalability.
- Opt-in live integration and complete regression suite at Phase V acceptance: **78 passed, 0 skipped**. Phase I independent verifier, Phase III static output verifiers, and Phase IV independent 15-estimator verifier passed. A before/after hash snapshot showed all 286 earlier-phase files unchanged. Separate Phase IV artifact-manifest check still fails on eight pre-existing hash mismatches; none was changed. macOS runtime PASS; Windows PowerShell runtime NOT TESTED. Full evidence, logs, status and matrix: `reports/bigdata/final/20261018T211007Z/` and `PHASE5_VERIFICATION.md`. **Phase V PASS at its live verification; the Docker daemon socket was absent during Phase VI-A verification.**

## Phase IV: machine learning and research-only prediction

- Registered a prereviewed three-task, five-fold experiment protocol with seed 42, separate untouched test splits, and diabetes predictor-profile grouping. Original heart `num`, derived heart target, stroke `id`, and all targets are excluded from predictors.
- Reused Phase I fold-local preprocessing in complete scikit-learn pipelines. Corrected numeric-coded binary category canonicalization so registered 0/1 values are encoded as 0/1 rather than unknown `-1`. Added controlled leakage and encoding tests.
- Completed **12/12 compulsory full model experiments** (Logistic Regression, Decision Tree, Random Forest and KNN on each task), **3/3 dummy baselines**, modest GridSearchCV, and separately isolated quick smoke runs. Saved 12 complete fitted preprocessing pipelines and three dummy estimators with checksums, a structured registry, split definitions, full metric/curve records, 3 comparison CSVs and 51 PNG figures.
- Selected Logistic Regression on development CV for heart (F1 .8473), diabetes (balanced accuracy .9348), and stroke (average precision .1945). Held-out test confusion matrices are respectively `[[27,6],[2,26]]`, `[[27,13],[3,61]]` and `[[772,200],[10,40]]`. The rare stroke outcome has a substantial false-positive burden; these are research results, not clinical diagnostic claims.
- Confirmed diabetes has 251 predictor profiles, 269 repeated rows and zero conflicting-label profiles. The group-disjoint split and five CV folds had zero profile overlap. A development-only deduplicated sensitivity analysis removed 214 repeated development rows without changing the primary test split or selection.
- Added research-only validation and prediction CLI, global development-fold permutation importance, transformed coefficients/importance, tree visualizations and local score-change explanations. SHAP and resampling sensitivity were not performed. Full results and limitations are in `PHASE4_FINDINGS.md`, `MODEL_COMPARISON.md`, `MODEL_LIMITATIONS.md` and `PHASE4_VERIFICATION.md`.
- Repeated the full training run: split hashes, selected models, parameters, thresholds, CV and test metrics were identical. Independent verifier reloaded all 15 estimators and recomputed held-out metrics. Phase I and Phase III static regression checks passed. Final full suite: **61 passed in 31.04s**.
- Phase III Power BI Desktop runtime, PBIX and Service upload gates remain open; Phase IV did not change Power BI deliverables.
- Fresh virtual-environment installation of the new `ml` extra is **BLOCKED/NOT TESTED in this sandbox** because pip could not reach its package index for build-time `setuptools`. The existing environment resolved dependencies, passed `pip check`, and executed training, prediction and tests.

## Phase III: visualization and Power BI portability

- Added six high-resolution PNG and six SVG Phase III visuals, including a part-to-whole heart pie and a word cloud from ten authentic notes generated by a separate, seeded official Synthea v3.4.0 run. The notes are not linked to the existing hospital cohort. Audited all 31 Phase II PNGs and preserved them.
- Produced 19 aggregate-only committed-ready Power BI CSVs and a checksum/schema manifest. A fresh-clone test with no raw data passed. Added five report-ready CSV tables.
- Created a six-section local Plotly browser preview with vendored Plotly.js, macOS/Windows launchers, export checks, HTTP smoke checks and six-page JavaScript data-wiring smoke.
- Generated PBIP/PBIR/TMDL source with six pages, 29 visual definitions, 32 tables/views, explicit DAX aggregates and a single data-root parameter. Static structural checks and official Microsoft JSON-schema validation passed. The Windows script writes an ignored local copy after checksum/header/row validation; it has not run on Windows.
- Phase III tests: **13 passed**; full suite: **46 passed**; Phase I independent output verifier: **PASS**, zero errors; `pip check`: no broken requirements. Figure regeneration produced byte-identical PNG/SVG hashes on two consecutive runs.
- **Open gates:** Power BI Desktop runtime import, visual/filter/theme review, PBIX export/reopen and Power BI Service browser upload/view are **BLOCKED** pending Windows Desktop and eligible account access. Local dashboard HTTP and JS data wiring passed, but actual browser visual rendering was **NOT TESTED** after headless Chrome exited 137 on this Mac. Full matrix: [PHASE3_VERIFICATION.md](PHASE3_VERIFICATION.md).

## Completed in Phase II

- Added reproducible semantics-aware descriptive statistics, Pearson/Spearman/point-biserial correlations, categorical chi-square/Cramér V, Benjamini–Hochberg adjustment for exploratory association tables, and three preregistered primary hypothesis tests with effects, confidence intervals, assumptions and trimmed Welch sensitivity checks.
- Added checksummed Phase I CSV loading, CLI `mediscope eda --dataset ...|all`, dataset-specific heart/diabetes/stroke/Synthea analyses, and 200 dpi supporting figures. Synthea patient and encounter denominators remain distinct; `Unknown` stroke smoking responses remain missing.
- Generated 4 JSON and 4 Markdown EDA reports, 49 CSV tables and 31 PNG figures; created a teaching notebook and Phase II methodology, findings, verification and macOS run guide.
- Phase II suite: **13 passed**; complete suite: **33 passed**; independent Phase I output verifier: **PASS, 0 errors**; `pip check`: no broken requirements. Repeated all-dataset analysis produced **88 byte-identical artifacts** in this environment.
- Actual findings and caveats are recorded in `docs/PHASE2_FINDINGS.md` and `docs/PHASE2_VERIFICATION.md`. This analysis is research-only and not clinically validated.

## Completed in Phase 0

- Inspected macOS 15.5 x86_64 on Intel Core i9-9880H, Python 3.13.2, Git 2.45.2, Node 22.16.0, npm 10.9.2, Java 17.0.14, existing files, and four raw ZIPs.
- Created monorepo directories, Python package/CLI, dependency declaration, engineering rules, source registry, acquisition notes, and assignment evidence map.
- Registered original schemas and SHA-256 fingerprints for the four already present local archives.
- Created `.venv`, installed the editable Phase 0 package and pytest, and ran `mediscope health`, `mediscope audit`, `pytest -q` (2 passed), and `pip check` (no broken requirements).
- Audited ZIP members in place: Cleveland 303 rows, diabetes 520, stroke 5,110, Synthea patients 1,171 and encounters 53,346. All registered archive checksums matched and no registered column-order/width mismatches were found. Diabetes has 269 identical full-row duplicates; raw data was not modified.
- Observed missing tokens: Cleveland `ca` 4 and `thal` 2; stroke `bmi` 201. The diabetes file has no recognized missing tokens despite the UCI page marking the dataset as having missing values. Synthea has many optional blank fields; details are available from the audit command.

## Completed in Phase I

- Added registered CSV import, strict ordered-schema and checksum validation, explicit target/identifier checks, missing-token handling, typed/domain validation, duplicate and patient-encounter relationship checks, IQR summaries, and immutable-source preparation in `mediscope/`.
- Added an unfitted scikit-learn `ColumnTransformer` factory with fold-local imputers, binary/nominal encoders, numerical scalers, and optional fold-local IQR clipping. No model was trained and no full-data imputation/scaling/encoding was exported.
- Captured the verified Python environment in `requirements-phase1.lock.txt` for the current Intel Mac/Python 3.13 setup.
- Exported five typed analysis-ready CSVs under `data/processed/`, four JSON and four Markdown quality reports under `reports/quality/`, five per-feature CSV tables under `reports/tables/`, and five paired boxplot PNGs under `reports/figures/`. Saved config snapshots and three feature-role mappings beside the prepared CSVs.
- Current sources: heart 303→303 rows and 14→15 columns (`num` preserved, binary target 164 absent/139 present); diabetes 520→520 rows with 269 identical rows retained; stroke 5,110→5,110 rows, 201 missing BMI and 1,544 `Unknown` smoking responses set missing; Synthea 1,171 patients and 53,346 encounters retained with zero orphan encounters. All domain-invalid counts were zero.
- Initial Phase I implementation suite: **13 passed**. `pip check` found no broken requirements. All five prepared CSV SHA-256 hashes matched across consecutive `prepare --dataset all` runs. The three model-feature factories also successfully transformed samples of the prepared tables in a smoke check.

## Phase I verification audit (2026-10-18)

- Re-read Phase I source, tests, registry, config, reports and docs. Added per-dataset CLI audit selection and nonzero status for missing/mismatched sources; updated README with exact commands and created a beginner-friendly macOS run guide.
- Added controlled test-only CSV fixtures, holdout and cross-validation isolation tests, missing-file/schema CLI tests, an executable fixture demonstration, and an independent read-only output verifier.
- Controlled fixture tests found and fixed a stroke ID domain boundary error: ID 1 is valid; positive IDs are now accepted.
- Final verbose suite: **20 passed in 2.29s**; `pip check` reported no broken requirements. All four per-dataset audits and all four per-dataset preparation commands succeeded; all-dataset preparation succeeded. A controlled tamper test confirmed the independent verifier returns FAIL for damaged output.
- Independent verifier: **PASS, 0 errors** across all five tables. Raw ZIP hashes remained unchanged. Consecutive runs produced identical hashes for all 5 prepared CSVs, 4 JSON reports, 4 Markdown reports, 5 quality tables and 5 PNG figures.
- Full commands, observed data counts, leakage proof, requirement decisions and limitations are in `docs/PHASE1_VERIFICATION.md`; user steps are in `docs/HOW_TO_RUN_PHASE1.md`.

## Blocked or unresolved

- Existing archive download dates and exact acquisition links were not recorded. Synthea generator release/seed and stroke patient origin are unverified.
- Power BI Desktop does not run natively on macOS; Phase III PBIP needs Windows Desktop runtime evidence, a real PBIX export and Service upload evidence.
- Hadoop and MongoDB executables were not found on PATH at Phase 0 inspection. Installation/configuration belongs to later phases.
- The current Git root is the parent `Semester-5` directory, containing unrelated projects. Stage only this project path if making a later commit.
- Diabetes has no participant ID to resolve identical profiles; stroke collection provenance remains unverified; Synthea is simulated. These limit interpretation of later experiments. The CLI retains source measurements, including IQR-flagged extremes.

## Upcoming, pending approval

- Angular frontend integration and any later phase.

No EDA, model training, frontend, MongoDB, Power BI, or Hadoop implementation was started in Phase I.
