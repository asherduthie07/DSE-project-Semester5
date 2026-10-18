# How to run Phase I on this MacBook

These instructions run data preparation only. The data and any future disease model are for research and education, not clinical use.

## 1. Open the project

Open **Terminal** on macOS (Spotlight → Terminal). Enter:

```bash
cd "/Users/asherduthie/KARUNYA/Semester-5/DSE/DSE-project-Semester5"
pwd
```

`pwd` should print that same project directory. Run every command below from there.

## 2. Use the Python environment

The existing `.venv` was verified with Python 3.13.2 on this Intel Mac. Activate it:

```bash
source .venv/bin/activate
python --version
mediscope health
```

You should see `Python 3.13.2` and a JSON health result with `"status": "ok"` and four registered datasets. After activation, the Terminal prompt usually begins with `(.venv)`. If `.venv` is missing, create and install it:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,prep]'
```

For the exact dependency versions used in verification on this Intel Mac/Python 3.13, you can install `requirements-phase1.lock.txt` into a fresh environment, then `python -m pip install --no-deps -e .`. The regular extra above is simpler and uses the supported version ranges.

## 3. Audit the raw ZIPs

The current workspace already contains the four raw ZIPs in `data/raw/`. To see command options and audit one source:

```bash
mediscope --help
mediscope audit --help
mediscope audit --dataset uci_cleveland_heart
mediscope audit --dataset uci_early_diabetes
mediscope audit --dataset kaggle_stroke
mediscope audit --dataset synthea_csv
```

Run `mediscope audit` to inspect all four in one JSON result. Look for `"status": "available"` and `"checksum_matches_registry": true` for each. The audit shows column names, token types, missing values, class counts, exact duplicates and schema mismatches. It reads files inside ZIPs and never edits them. A missing archive or schema/checksum mismatch gives a nonzero exit status; follow [DATA_SOURCES.md](DATA_SOURCES.md) to obtain the exact source archive rather than substituting another dataset.

## 4. Prepare one dataset or all datasets

```bash
mediscope prepare --help
mediscope prepare --dataset uci_cleveland_heart
mediscope prepare --dataset uci_early_diabetes
mediscope prepare --dataset kaggle_stroke
mediscope prepare --dataset synthea_csv
mediscope prepare --dataset all
```

Each command prints the output paths as JSON. `all` creates five CSVs because Synthea has separate patient and encounter tables. Re-running with the unchanged archives and default configuration gives the same outputs. The preparation config is `data/metadata/preparation_config.json`; copy it and pass `--config PATH` only if you intend to test a different documented policy.

## 5. Find and inspect the results

- `data/processed/heart.csv`, `diabetes.csv`, `stroke.csv`, `synthea_patients.csv`, `synthea_encounters.csv`: typed, validated tables. Missing feature values remain blank so a later training pipeline can impute within each training fold.
- `data/processed/*_preparation_config.json` and `*_feature_roles.json`: saved settings and categorical mappings.
- `reports/quality/<dataset ID>.json` and `.md`: detailed counts, decisions, and before/after comparison.
- `reports/tables/*_quality.csv`: per-feature rows ready for the academic report.
- `reports/figures/*_boxplot.png`: before/after IQR inspection plots.

For example, view a report in Terminal:

```bash
python -m json.tool reports/quality/kaggle_stroke.json | less
cat reports/quality/uci_cleveland_heart.md
```

Press `q` to leave `less`. In Finder, open the project folder and navigate to `reports/figures/` to view PNGs. The plots are usually identical before and after because Phase I retains valid extreme measurements.

## 6. Run tests and an independent output check

```bash
python -m pytest -q
python scripts/demo_phase1_fixtures.py
python scripts/verify_phase1_outputs.py
python -m pip check
```

On the verified workspace, pytest returned **20 passed**, the output verifier returned `"status": "PASS"` with an empty `errors` list, and `pip check` found no broken requirements. The fixture demo prints results from tiny invented CSVs in `tests/fixtures/`; never use their counts as research results. The verifier rereads raw archives and prepared CSVs to check fingerprints, schemas, row counts, missing values, target domains, reports, plots and patient/encounter links.

## Common errors

| Message or symptom | What to do |
|---|---|
| `mediscope: command not found` | Run `source .venv/bin/activate` from the project root, or use `.venv/bin/mediscope`. |
| `.venv` or package missing | Create the virtual environment and install `'.[dev,prep]'` as in step 2. |
| Raw archive missing | Check `data/raw/` and use the exact download path in [DATA_SOURCES.md](DATA_SOURCES.md). Do not rename an unrelated dataset to satisfy the CLI. |
| Checksum or schema mismatch | Inspect the archive and its source. Keep the changed file separate; update the registry only after documenting the actual acquisition and schema. |
| Required target missing or invalid | The preparation command intentionally stops. Recheck the source file; never fill a missing disease label automatically. |
| Output verifier says `FAIL` | Read its `errors` list, rerun `mediscope prepare --dataset all`, then rerun the verifier. If it still fails, inspect the specified file. |
| Matplotlib cache warning | The project writes its cache under `.cache/`; make sure the project directory is writable. |

You can end the activated session with `deactivate`. [PHASE1_VERIFICATION.md](PHASE1_VERIFICATION.md) records the full audit and known limitations.
