# MediScope AI

Research-only Smart Healthcare Analytics and Disease Prediction System. Any later model output is for academic demonstration and is not clinically validated or medical advice.

## Phase V: MongoDB and Hadoop

Phase V adds checksummed, idempotent PyMongo ingestion, documented aggregations, a local Docker Compose topology and a Python Hadoop Streaming encounter-count job. The local Intel Mac stack has been run: MongoDB, one HDFS DataNode and one YARN NodeManager are healthy, and a real Streaming job counted all 53,346 synthetic encounters with exact pandas reconciliation. Windows runtime remains untested. Start with the [Phase V run guide](docs/HOW_TO_RUN_PHASE5.md), [live verification matrix](docs/PHASE5_VERIFICATION.md), [database schema](docs/MONGODB_SCHEMA.md) and [Hadoop architecture](docs/HADOOP_ARCHITECTURE.md). Phase VI integration has not started.

## Phase IV: research-only disease classification

Three separate tasks use the verified Phase I prepared CSVs. Four compulsory algorithms and a dummy baseline run on each task. The final comparison uses five development folds and untouched test partitions; diabetes keeps identical predictor profiles together. Models are research artifacts, **not clinically validated diagnostic tools**.

On macOS, from the project root:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev,prep,eda,ml]'
mediscope ml --help
mediscope ml train --dataset all
mediscope ml evaluate --dataset all
mediscope ml compare --dataset all
mediscope ml explain --dataset all
mediscope ml predict --dataset heart --input examples/heart_case.json
python scripts/verify_phase4_outputs.py
python scripts/build_phase4_manifest.py --check
python -m pytest -q
```

Use `--dataset heart`, `diabetes`, or `stroke` for one task. `mediscope ml train --dataset all --quick` runs a separate three-fold smoke mode with minimal grids; it does not replace full results. Prediction examples for each task are fictional input fixtures, not clinical cases. Full results are in `ml/registry.json`, `reports/ml/full/`, `reports/tables/ml/`, and `reports/figures/ml/full/`. Read the [macOS Phase IV guide](docs/HOW_TO_RUN_PHASE4.md), [methods](docs/PHASE4_METHODOLOGY.md), [findings](docs/PHASE4_FINDINGS.md), [verification](docs/PHASE4_VERIFICATION.md), and [limitations](docs/MODEL_LIMITATIONS.md). Fresh clones require the verified Phase I prepared data or the registered raw archives and a Phase I preparation run; ignored data files are not bundled.

## Phase III: portable visualization snapshot and dashboard

Phase III bundles 19 aggregate-only CSV exports with ordered schemas and SHA-256 checksums. A fresh clone can run the local six-section analytics preview without the ignored raw ZIPs:

```bash
python3 scripts/verify_powerbi_exports.py
bash scripts/run_dashboard_macos.sh --check
bash scripts/run_dashboard_macos.sh
```

Open `http://127.0.0.1:8765/` and stop with Ctrl+C. On Windows, run `powershell -ExecutionPolicy Bypass -File .\scripts\run_dashboard_windows.ps1`. For a Power BI Desktop review on Windows, run `powershell -ExecutionPolicy Bypass -File .\scripts\setup_powerbi_windows.ps1 -ValidateOnly` and then the same command without `-ValidateOnly`. The script builds an ignored clone-local PBIP copy. **Desktop rendering, PBIX creation, and Power BI Service upload have not been tested; no PBIX/PBIT is present.** The source PBIP and all six page definitions are version-controlled, but an actual Power BI acceptance check is still required on Windows. macOS Power BI access requires a verified PBIX uploaded to the official Service. See the [Phase III run guide](docs/HOW_TO_RUN_PHASE3.md), [Windows setup](docs/POWERBI_WINDOWS_SETUP.md), [macOS Service setup](docs/POWERBI_MACOS_SETUP.md), [methods](docs/PHASE3_METHODOLOGY.md), and [verification](docs/PHASE3_VERIFICATION.md).

Static exports and figures can be verified with:

```bash
python3 -m dashboard.app --check
.venv/bin/python scripts/verify_powerbi_project.py
.venv/bin/python -m pytest -q
```

High-resolution PNG/SVG evidence is in `reports/figures/phase3/`; report tables are in `reports/tables/phase3/`. All disease analytics are research-only and have not been clinically validated.

## Phase II: exploratory data analysis

Phase II reads the five verified Phase I prepared CSVs. It does not alter raw or prepared data. From the project root on macOS:

```bash
source .venv/bin/activate
python -m pip install -e '.[dev,prep,eda]'
mediscope eda --help
mediscope eda --dataset uci_cleveland_heart
mediscope eda --dataset uci_early_diabetes
mediscope eda --dataset kaggle_stroke
mediscope eda --dataset synthea_csv
mediscope eda --dataset all
python -m pytest -q
python scripts/verify_phase1_outputs.py
```

Analysis summaries are in `reports/eda/`, CSV evidence tables in `reports/tables/eda/`, and 200 dpi figures in `reports/figures/eda/`. The three preregistered tests use alpha 0.05 by default; `--alpha 0.01` changes the reported confidence level and decision threshold. See [Phase II run guide](docs/HOW_TO_RUN_PHASE2.md), [methods](docs/PHASE2_METHODOLOGY.md), [findings](docs/PHASE2_FINDINGS.md), and [verification](docs/PHASE2_VERIFICATION.md).

## Phase I: data preparation

Phase I uses the existing raw ZIPs. Install the preparation dependencies and create all five typed CSV tables, data-quality reports, tables, and paired boxplots:

```bash
.venv/bin/pip install -e '.[dev,prep]'
.venv/bin/mediscope prepare --dataset all
.venv/bin/python -m pytest -q
```

For the exact dependency versions verified on this Intel Mac and Python 3.13, use [requirements-phase1.lock.txt](requirements-phase1.lock.txt) in a fresh virtual environment: `.venv/bin/pip install -r requirements-phase1.lock.txt` followed by `.venv/bin/pip install --no-deps -e .`. The `pyproject.toml` extras remain the supported version ranges for other compatible machines.

Run one source using `--dataset uci_cleveland_heart`, `uci_early_diabetes`, `kaggle_stroke`, or `synthea_csv`. The default configuration is [data/metadata/preparation_config.json](data/metadata/preparation_config.json); supply a reviewed variant with `--config PATH`. Prepared CSVs are in `data/processed/`, quality JSON/Markdown in `reports/quality/`, table CSVs in `reports/tables/`, and figures in `reports/figures/`. Raw ZIPs are never modified. See [Phase I preparation guide](docs/PHASE1_DATA_PREPARATION.md) for policy, limitations, and exact output semantics.

### Verified Phase I commands

Run these from the project root after activating the environment with `source .venv/bin/activate` (or prefix each command with `.venv/bin/`):

```bash
mediscope --help
mediscope audit --help
mediscope prepare --help
mediscope audit --dataset uci_cleveland_heart
mediscope audit --dataset uci_early_diabetes
mediscope audit --dataset kaggle_stroke
mediscope audit --dataset synthea_csv
mediscope audit
mediscope prepare --dataset uci_cleveland_heart
mediscope prepare --dataset uci_early_diabetes
mediscope prepare --dataset kaggle_stroke
mediscope prepare --dataset synthea_csv
mediscope prepare --dataset all
python scripts/verify_phase1_outputs.py
python scripts/demo_phase1_fixtures.py
python -m pytest -q
```

The `audit` command reads ZIPs without changing them and exits with status 2 if a selected source is missing or mismatched. The fixture demo uses invented test data only. See [HOW_TO_RUN_PHASE1.md](docs/HOW_TO_RUN_PHASE1.md) for a beginner-friendly macOS walkthrough and [PHASE1_VERIFICATION.md](docs/PHASE1_VERIFICATION.md) for the actual audit results.

## Phase 0: Mac setup

Run from this directory. Python 3.11–3.13 is supported. The initial Phase 0 environment needs only the standard library and pytest; the Phase I installation above adds NumPy, pandas, scikit-learn, Matplotlib, and transitive dependencies. API, frontend, database, and Hadoop dependencies are deferred until their approved phases.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/mediscope health
.venv/bin/mediscope audit
.venv/bin/python -m pytest -q
```

Use `.venv/bin/python` and `.venv/bin/mediscope` directly, or activate with `source .venv/bin/activate`. The audit reads registered ZIP members in place and prints JSON. It does not preprocess or extract data. `observed_types` are token-level integer/float/text observations, not inferred pandas dtypes. Missing tokens recognized: empty, `?`, `NA`, `N/A`, `NULL`, `null`. Duplicate counts refer to identical full rows, and bad-width rows are excluded from column statistics. The audit reports schema mismatches and checksum comparison; it does not attest dataset origin.

## Raw datasets

See [dataset registry](data/metadata/datasets.json) and [acquisition notes](docs/DATA_SOURCES.md). Existing local archives are kept in `data/raw/` and ignored by Git. The four registered archives are present in the current workspace, so no manual download is needed to verify Phase 0 here. On a fresh clone, obtain the exact source archives using the registry instructions. Record download dates, source links, and new checksums before using replacement files. Never substitute a different dataset under an expected filename.

## Layout

`mediscope/` holds the CLI and reusable preparation code; `data/metadata/` holds source contracts and configuration. `frontend/`, `backend/`, `notebooks/`, `pipelines/`, `ml/`, `visualizations/`, `big_data/`, and `powerbi/` remain reserved for approved later phases. `reports/` and `tests/` contain Phase I evidence. See [project plan](docs/PROJECT_PLAN.md) and [status](docs/PROJECT_STATUS.md).
