# MediScope AI

Research-only Smart Healthcare Analytics and Disease Prediction System. Any later model output is for academic demonstration and is not clinically validated or medical advice.

## Phase 0: Mac setup

Run from this directory. Python 3.11–3.13 is supported; Phase 0 only needs the standard library and pytest. Analysis, API, frontend, database, and Hadoop dependencies are deferred until their approved phases.

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

`mediscope/` holds Phase 0 CLI code; `data/metadata/` holds source contracts. `frontend/`, `backend/`, `notebooks/`, `pipelines/`, `ml/`, `visualizations/`, `big_data/`, `powerbi/`, `reports/`, and `tests/` are reserved for approved later phases. See [project plan](docs/PROJECT_PLAN.md) and [status](docs/PROJECT_STATUS.md).
