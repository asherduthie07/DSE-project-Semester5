# How to run Phase II on macOS

1. Open Terminal and enter the MediScope project folder:

   ```bash
   cd /Users/asherduthie/KARUNYA/Semester-5/DSE/DSE-project-Semester5
   source .venv/bin/activate
   ```

   Your prompt should show `(.venv)`. If `.venv` does not exist, run `python3 -m venv .venv` and `python -m pip install -e '.[dev,prep,eda]'`. If the five files in `data/processed/` are missing, follow `docs/HOW_TO_RUN_PHASE1.md` first.

2. Inspect the CLI and analyze any dataset:

   ```bash
   mediscope eda --help
   mediscope eda --dataset uci_cleveland_heart
   mediscope eda --dataset uci_early_diabetes
   mediscope eda --dataset kaggle_stroke
   mediscope eda --dataset synthea_csv
   mediscope eda --dataset all
   ```

   A successful command exits with code 0 and prints JSON listing report paths and counts. `--dataset all` runs all four registrations, including both Synthea tables. Use `mediscope eda --dataset all --alpha 0.01` only if you want to explicitly change the test threshold and confidence level; record that choice in your report.

3. Open the evidence. Read `reports/eda/uci_cleveland_heart.md`, `uci_early_diabetes.md`, `kaggle_stroke.md`, and `synthea_csv.md` in a text editor. Open the matching `.json` files for exact machine-readable numbers. Open CSV files in `reports/tables/eda/` with a spreadsheet viewer. Preview PNG plots in `reports/figures/eda/` with macOS Preview. `docs/PHASE2_FINDINGS.md` gives the report narrative.

4. Verify the environment and both phases:

   ```bash
   python -m pip check
   python -m pytest tests/test_phase2_eda.py -q
   python -m pytest -q
   python scripts/verify_phase1_outputs.py
   ```

   The last command should print `"status": "PASS"` and `"errors": []`. A test failure or nonzero exit code needs investigation. Phase II reads prepared CSVs but does not modify them.

## Common errors

- `command not found: mediscope`: activate `.venv` or run `.venv/bin/mediscope` directly from the project root.
- `No module named scipy` or `matplotlib`: with `.venv` active, run `python -m pip install -e '.[dev,prep,eda]'`.
- `Missing Phase I quality report` or `Missing prepared table`: run `mediscope prepare --dataset all`, then `python scripts/verify_phase1_outputs.py`.
- `checksum mismatch` or target/schema failure: do not edit a CSV manually. Re-run and verify Phase I; check raw archive checksums in the registry.
- Plots are large: each is 200 dpi for report use. PNGs are supporting Phase II figures, not a Phase III dashboard.
