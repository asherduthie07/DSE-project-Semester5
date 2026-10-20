# Project status

## Background image selection — 2026-10-20

- The owner selected `frontend/background-image/3.jpg` as the dashboard background. The original JPEG (735×414, 79,924 bytes, SHA-256 `b70d86c3f8957b6f10d67bfbf71297dc71b9ff9e7d04e3968952fb7606b55e99`) is unchanged; an identical copy is served from `frontend/public/backgrounds/3.jpg`. Supplied-file provenance beyond its local path is unverified; embedded EXIF credits Graphic in Motion / stock.adobe.com, and redistribution rights are unverified.
- The default preset and pre-bootstrap background point to `/backgrounds/3.jpg`. The previous image remains an optional preset, while browsers holding it as the old default migrate once. The 2.4 px blur and transparent dashboard surfaces remain.
- Verification: Angular unit suite **36/36 passed** and production build **passed**. Headless Chromium at the live `http://localhost:4200/command-center` displayed `3.jpg` with the existing 2.4 px blur and transparent panel, even when initialized with the former saved default. The image returned `200 image/jpeg`, 79,924 bytes; the source and public copy SHA-256 hashes matched.

## Local runtime restart — 2026-10-20

- Stopped the running Angular development server, confirmed ports 4200 and 8000 were free, then started FastAPI on `127.0.0.1:8000` and Angular on `localhost:4200`. Docker services were unavailable and are optional for the research frontend.
- Verified HTTP 200 for the frontend, supplied JPEG, direct API health, and proxied API health. Headless Chromium loaded Command Center with the supplied background and `brightness(1) blur(2.4px)`.

## Background blur adjustment — 2026-10-20

- Set the global image blur default to 2.4 px, defined as 20% of Background Studio's existing 0–12 px range. The fixed image layer expands 8 px past the viewport to avoid blurred edges. A one-time saved-setting migration applies the new default to existing browsers; later slider changes persist.
- Verification: Angular unit suite **35/35 passed**, production build **passed**, and headless Chromium at the active `http://localhost:4200/command-center` confirmed `brightness(1) blur(2.4px)` with a zero-alpha panel. A browser initialized with the former saved zero-blur setting migrated and stored `2.4`.

## Clear dashboard background — 2026-10-20

- Follow-up runtime fix: two Angular development servers were bound to port 4200 on different loopback addresses. `localhost:4200` (IPv6) was still serving a pre-change stylesheet without `holographic.css`, while `127.0.0.1:4200` (IPv4) served the transparent dashboard. Restarted the stale `localhost:4200` server with the current Angular configuration. Headless Chromium then showed the supplied JPEG through the sidebar, header, and panels at that exact URL; computed surface alpha was zero and the background filter was `brightness(1) blur(0px)`.
- The owner requested the supplied `frontend/background-image/main-background-image.jpg` as the visible global background. Its unchanged public copy already serves at `/backgrounds/main-background-image.jpg` and remains the fixed, cover-sized layer on all seven routes.
- Changed default background brightness to 1 and glass opacity/blur to 0. Shared surface tokens and remaining opaque dashboard sections now leave the image visible through the sidebar, topbar, panels, forms, and report areas. Background Studio still allows a user-selected tint and blur. Former default appearance values migrate once; other saved preferences remain.
- Verification: Angular unit suite **34/34 passed** and production build **passed**. A local Chromium check loaded all seven routes and confirmed the fixed JPEG, full brightness, and zero-alpha sidebar, header, and panels; the JPEG returned `200 image/jpeg` with 39,316 bytes. A mobile check at 390 px confirmed former saved defaults migrate to clear surfaces. A scrolled viewport screenshot confirmed the fixed image remains visible behind lower dashboard panels. This visual check used headless Chromium, not a manual cross-browser review.

## Background and human-readable input correction — 2026-10-20

- Phase VI-C follow-up only: copied the supplied main JPEG unchanged into Angular's supported `public/backgrounds/` path, removed the custom source asset rule, added a pre-bootstrap CSS fallback, persisted valid bundled preset selection, and made failed/stale images restore the default without hiding a successfully decoded image on palette failure. The live `/backgrounds/main-background-image.jpg` response was `200 image/jpeg 39316`; source, served and built SHA-256 hashes matched.
- Phase VI-C transparency follow-up: the same fixed main image remains the global background. Default dashboard panel alpha is now .48, navigation shell alpha .38, and text-dense glass remains translucent at .72 or higher. Updated shared tokens cover all seven routes; older stored default opacity migrates once. Frontend tests 34/34, production build PASS, and seven-route Chromium transparency check PASS. Viewport screenshots: `docs/screenshots/phase6c/transparent-command-center.png` and `transparent-research.png`.
- Added a centralized, verified presentation vocabulary for Cleveland, diabetes and stroke categories. Prediction options are intersected with the live schema and retain exact submitted values. Dataset preview, filters, charts and explanation labels use the same mappings; numeric measurements and saved research artifacts are unchanged. Three fictional form POST bodies matched their original fixture JSON and saved CLI/API results.
- Verification: Angular 33/33, production build PASS, Python 87 passed/3 Docker skips, clean 11-test Chromium suite PASS plus focused dataset-table test PASS. The seven-route/four-width sweep and background recovery/scroll tests passed. Full evidence, exact values, screenshots and remaining limits: `docs/BACKGROUND_AND_INPUT_FIX_VERIFICATION.md`. Image redistribution rights and native Intel GPU acceptance remain open. No Phase VII or Clinical Workspace work began.

Updated: 2026-10-20 (Phase VI-C Holographic Research Workspace)

## Phase VI-C: holographic visual transformation

- Integrated the restored default background through a persistent root layer, extracted a palette locally in Canvas, added bounded glass and glow tokens, and built Background Studio. The reference image informed panel lighting; a separate particle wave is explicitly decorative. Exact image names, dimensions and SHA-256 are in `HOLOGRAPHIC_DESIGN_SYSTEM.md`. Distribution rights for the supplied images are unverified.
- Added a lazy Three.js renderer with OrbitControls, actual measured scatter plots, categorical/model columns, Gaussian density surface, histogram/temporal ridgelines, conceptual infrastructure topology and a model-score arc. The shared visualization frame offers a precise ECharts 2D view, camera controls, PNG export, fallback, hover/click inspection and accessible tables. All seven existing routes retain their API workflows; no backend/data/model or Clinical Workspace changes.
- Final regression: Angular **28 passed / 9 files**; production build **PASS** (344.40 kB raw / 97.48 kB estimated transfer initial); Python **87 passed, 3 Docker skips**; Playwright Chromium **9 passed** with all seven routes at 1440/1280/768/390 and screenshots. Zero production dependency audit advisories; seven development-tool advisories remain. Full evidence and PASS/FAIL/BLOCKED/NOT TESTED matrix: `PHASE6C_VERIFICATION.md`, `3D_VISUALIZATION_VERIFICATION.md`, screenshots in `docs/screenshots/phase6c/`.
- Open gates: supplied image rights, a higher-resolution authorized background for crisp large-display production, native Intel GPU performance and long-run memory review, Safari/Windows and manual screen-reader acceptance. Phase VI-C implementation stops here pending owner acceptance; Phase VII has not begun.

## Phase VI-B: Angular research frontend

- Added a standalone Angular 20 dark research frontend with seven lazy routes, a typed FastAPI client, ECharts analytical views, schema-driven saved-model predictions, historical MapReduce evidence separated from live infrastructure status, responsive design tokens, and curated reports. No Clinical Workspace or Phase VI-C work was started.
- Production build and strict TypeScript check passed. Angular jsdom suite: **13 passed across 8 files**. Existing Python suite: **87 passed, 3 Docker skips**. Live Angular proxy reached the relevant FastAPI routes and executed a fictional heart prediction. All 31 copied Phase II figures and three fictional cases match original repository SHA-256 hashes.
- **Visual browser acceptance remains open:** no computer-use browser was available and installed ChromeHeadless could not launch. No screenshots or viewport inspection were possible. Backend gaps for arbitrary numeric distributions, full feature summaries, HDFS capacity, current YARN jobs and downloads are documented in `PHASE6B_VERIFICATION.md`. Phase VI-B implementation is reviewable but is not declared fully accepted.
- Guides: `FRONTEND_DESIGN_SYSTEM.md`, `HOW_TO_RUN_FRONTEND.md`, `PHASE6B_UI_ARCHITECTURE.md`, `PHASE6B_VERIFICATION.md`.

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
