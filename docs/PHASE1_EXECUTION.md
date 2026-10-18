# Phase I execution record

Executed on 2026-10-18 in the project directory with Python 3.13.2 on macOS 15.5 (Intel x86_64). The [preparation policy](PHASE1_DATA_PREPARATION.md) explains what each command produces.

```bash
cat AGENTS.md README.md docs/PROJECT_STATUS.md pyproject.toml
cat data/metadata/datasets.json
.venv/bin/mediscope audit
.venv/bin/pip install -e '.[dev,prep]'
.venv/bin/mediscope prepare --dataset all
.venv/bin/mediscope prepare --dataset uci_cleveland_heart
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
.venv/bin/pip freeze --exclude-editable
```

The raw ZIPs were also inspected in place with Python's `zipfile` and `csv` modules to check observed categories, ranges, and keys before implementing the domain rules. The first test run found a wrong expected IQR fence in a test assertion (85 versus the calculated 55); that assertion was corrected. A direct fit/transform smoke check then found pandas nullable `pd.NA` needed conversion to NumPy missing values inside the pipeline; this was fixed and covered by a regression test. Final results: **13 passed in 2.24s**, `pip check` reported **No broken requirements found**, all four datasets prepared, the single-dataset command succeeded, and the three classification preprocessing factories fit/transformed table samples without errors. The factories were exercised for preprocessing verification only; no model training was performed.

Reproducibility was checked by calculating SHA-256 for each prepared CSV, rerunning `prepare --dataset all`, and comparing SHA-256 again. All five hashes matched:

| Prepared CSV | SHA-256 |
|---|---|
| `heart.csv` | `36b51c189bc5e5edf72f83152e9243f0b0801494951c73af290c44a68a3a1b53` |
| `diabetes.csv` | `fba09cdce359ada29bf87d8def1a7a32d956f793e2176c9fdcf7d004aba2f76e` |
| `stroke.csv` | `8031625058cfddb391e93633d50b9519775d796c7ad2e1000c813c359be9f1ed` |
| `synthea_patients.csv` | `f9506feaf8eed0725d99d3421122424dbc5ed692cebb3cad6ef4eafa97f090d5` |
| `synthea_encounters.csv` | `c38b5c2f8a9440a00cd8470c397e47a44d4cc0dee3880c9906a0165932bbbd3f` |

All current archives passed schema, checksum, and domain validation; no source files were changed. More detailed observed counts and actions are in the machine-readable reports under `reports/quality/`.
