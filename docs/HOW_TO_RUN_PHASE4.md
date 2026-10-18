# Run Phase IV on macOS

## 1. Open the project and environment

In Terminal, change to the cloned MediScope AI project directory. Run `pwd` and confirm it contains `AGENTS.md`, `pyproject.toml`, and `mediscope/`. Then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,prep,eda,ml]'
mediscope ml --help
```

If you already have the project's `.venv`, activate it instead of recreating it. `python -m pip check` should report no broken requirements.

The editable install requires access to a Python package index for build dependencies such as `setuptools`. This development sandbox had no package-index access, so a **fresh** environment install was not retested here; the existing `.venv` ran all Phase IV commands successfully.

## 2. Supply and verify data

The three prepared CSVs in `data/processed/` and their Phase I quality reports are ignored by Git. On this development Mac they exist. On a fresh clone, follow `docs/DATA_SOURCES.md` for the exact registered raw sources, put the archives in `data/raw/`, then run:

```bash
mediscope audit --dataset all
mediscope prepare --dataset all
python scripts/verify_phase1_outputs.py
```

`mediscope ml train` will stop with a clear error when the prepared file, schema or recorded checksum is missing or changed. Do not substitute a different source file under a registered filename. Phase III aggregate exports are separate and cannot replace the patient-level Phase IV inputs.

## 3. Run the experiments

From the project root with the environment active:

```bash
mediscope ml train --dataset heart
mediscope ml train --dataset diabetes
mediscope ml train --dataset stroke
mediscope ml evaluate --dataset all
mediscope ml compare --dataset all
mediscope ml explain --dataset all
python scripts/verify_phase4_outputs.py
python scripts/build_phase4_manifest.py --check
```

`mediscope ml train --dataset all` is equivalent to the three full train commands. On this Intel Mac, the three full tasks took roughly 28, 36 and 65 seconds respectively with single-worker search. For a quick functional check first, run `mediscope ml train --dataset all --quick`; its separate outputs must never be cited as the final five-fold results. You can use `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LOKY_MAX_CPU_COUNT=8` before a command to limit thread oversubscription.

## 4. Read outputs

- `ml/registry.json`: software versions, source hashes, selected model, parameters, fold scores, held-out metrics, thresholds, artifact checksums.
- `ml/models/full/<task>/`: saved trusted joblib pipelines for the four algorithms and a separate dummy estimator.
- `reports/ml/full/<task>/split.json`: immutable index definitions and class counts.
- `reports/ml/full/<task>/experiment.json`: detailed experiment record.
- `reports/ml/full/<task>/explanations_*.json`: permutation and local explanation data.
- `reports/tables/ml/<task>_comparison.csv`: report-ready comparison table.
- `reports/figures/ml/full/<task>/`: comparison, ROC/PR, calibration, confusion and explanation plots.
- `reports/ml/artifact_manifest.json`: all 90 full output paths and SHA-256 checksums; regenerate with `python scripts/build_phase4_manifest.py` after a deliberate full rerun.

The selected algorithm is based on development CV scores, even when a different candidate has a higher held-out test score. Do not treat estimated scores as medical risk probabilities.

## 5. Run a hypothetical prediction and tests

```bash
mediscope ml predict --dataset heart --input examples/heart_case.json
mediscope ml predict --dataset diabetes --input examples/diabetes_case.json
mediscope ml predict --dataset stroke --input examples/stroke_case.json
python -m pytest -q tests/test_phase4_ml.py
python -m pytest -q
```

Only load joblib files produced by a trusted copy of this repository. Joblib uses Python pickle. Prediction inputs are validated and are not stored by the CLI. The `examples/` records are invented software fixtures.

## Common errors

- **`command not found: mediscope`**: activate `.venv` or use `.venv/bin/mediscope`.
- **pip cannot download `setuptools`**: connect to a package index or provide approved local wheels, then repeat the install. This sandbox's network restriction blocked a fresh reinstall; do not treat it as a model failure.
- **Missing prepared file or checksum mismatch**: rerun the registered Phase I audit and preparation; inspect `reports/quality/` and `data/metadata/datasets.json`.
- **No trained model registry**: run the relevant full `train` command before `evaluate`, `compare`, `explain` or `predict`.
- **Unknown category or invalid numeric range**: use the Phase I feature schema and the example JSON keys/allowed values; do not force an arbitrary category.
- **Slow experiment or high CPU**: set the thread limits shown above. Full training is intentionally single worker to preserve predictable laptop resource use.
- **Artifact checksum mismatch**: do not bypass the check; regenerate models from verified data or restore a trusted version.

Successful execution means the three full tasks, 12 compulsory model trials, three dummy trials, independent output verifier and full test suite all pass. Inspect the limitations in `docs/MODEL_LIMITATIONS.md` before using any result in a report.
