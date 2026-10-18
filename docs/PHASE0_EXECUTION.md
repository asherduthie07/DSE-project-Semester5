# Phase 0 execution record

Run on 2026-10-18 in the project directory on macOS 15.5, Intel Core i9-9880H (`x86_64`). Commands below are the setup and verification commands executed for this phase. The existing `docs/architecture` and raw ZIP files were preserved.

```bash
uname -srm
sw_vers
sysctl -n machdep.cpu.brand_string
python3 --version
git --version
node --version
npm --version
java -version
git rev-parse --show-toplevel
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/mediscope health
.venv/bin/mediscope audit
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

The first `pip install` attempt in the restricted sandbox failed because DNS/network access to the package index was blocked. The same install command then succeeded with approved network access. The initial sandboxed `sysctl` query was denied; its read-only retry returned the Intel CPU model. No source data was downloaded or modified.

Results: health `ok` on Python 3.13.2 with four registered datasets; pytest **2 passed**; pip check **No broken requirements found**. Audit found all four archives, matching local SHA-256 values, and no column or row-width schema mismatches:

| Member | Rows | Identical full-row duplicates | Target class counts |
|---|---:|---:|---|
| `processed.cleveland.data` | 303 | 0 | 0: 164; 1: 55; 2: 36; 3: 35; 4: 13 |
| `diabetes_data_upload.csv` | 520 | 269 | Negative: 200; Positive: 320 |
| `healthcare-dataset-stroke-data.csv` | 5,110 | 0 | 0: 4,861; 1: 249 |
| `csv/patients.csv` | 1,171 | 0 | No target |
| `csv/encounters.csv` | 53,346 | 0 | No target |

Missing values observed: Cleveland `ca` 4 and `thal` 2; stroke `bmi` 201. Synthea blank optional fields are reported by the CLI. The diabetes file has no recognized missing tokens; UCI's metadata says missing values may exist, so the discrepancy merits later investigation. These are descriptive audit outputs, not modeling results.
