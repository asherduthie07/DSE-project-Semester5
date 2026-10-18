# Phase IV verification record

Date: 2026-10-18. Scope: Phase IV only. The preregistered protocol in `docs/PHASE4_METHODOLOGY.md` and `data/metadata/ml_experiment_config.json` was written before any model comparison. All metrics below come from actual saved models and prepared source-label datasets; no clinical performance is claimed.

## Environment and baseline

- macOS 15.5, Darwin 24.5.0, x86_64 Intel MacBook Pro; Python 3.13.2.
- NumPy 2.5.4, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, joblib 1.6.0.
- `pip check`: “No broken requirements found.” CPU model command `sysctl -n machdep.cpu.brand_string` was denied in this sandbox; the existing Phase 0 inventory recorded Intel Core i9-9880H.
- Before Phase IV edits: `.venv/bin/python -m pytest -q` → **46 passed in 24.12s**.
- Source data verified: heart 303×15, diabetes 520×17, stroke 5,110×12. Phase I output verifier confirmed raw SHA-256s and prepared schemas unchanged.

## Commands actually executed

Run from the repository root; `.venv/bin/` was used where shown. The full model runs were single worker with BLAS threads limited:

```bash
.venv/bin/python -m pytest -q
.venv/bin/mediscope ml --help
LOKY_MAX_CPU_COUNT=8 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/mediscope ml train --dataset heart
LOKY_MAX_CPU_COUNT=8 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/mediscope ml train --dataset diabetes
LOKY_MAX_CPU_COUNT=8 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/mediscope ml train --dataset stroke
LOKY_MAX_CPU_COUNT=8 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/mediscope ml train --dataset all
.venv/bin/mediscope ml train --dataset heart --quick
.venv/bin/mediscope ml train --dataset diabetes --quick
.venv/bin/mediscope ml train --dataset stroke --quick
MPLCONFIGDIR=/private/tmp/mediscope-mpl OPENBLAS_NUM_THREADS=1 .venv/bin/mediscope ml compare --dataset all
MPLCONFIGDIR=/private/tmp/mediscope-mpl OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/mediscope ml explain --dataset all
.venv/bin/mediscope ml evaluate --dataset all
.venv/bin/mediscope ml predict --dataset heart --input examples/heart_case.json
.venv/bin/mediscope ml predict --dataset diabetes --input examples/diabetes_case.json
.venv/bin/mediscope ml predict --dataset stroke --input examples/stroke_case.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python scripts/verify_phase4_outputs.py
.venv/bin/python scripts/build_phase4_manifest.py
.venv/bin/python scripts/build_phase4_manifest.py --check
.venv/bin/python -m pytest -q tests/test_phase4_ml.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_powerbi_exports.py
.venv/bin/python scripts/verify_powerbi_project.py
.venv/bin/python scripts/verify_phase1_outputs.py
.venv/bin/python -m pip check
PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -e '.[dev,prep,eda,ml]'
```

The separate `train --dataset all` was a reproducibility rerun. Its split hashes, selected models, best hyperparameters, thresholds, CV means and checked held-out metrics matched the first full run exactly. Initial full task durations were 27.57, 36.24 and 64.72 seconds; the second full run recorded 25.00, 25.99 and 59.88 seconds for heart, diabetes and stroke. Maximum resident set reported by macOS for the second runs was approximately 183, 188 and 212 MB respectively (the `resource` values are platform-specific). No GPU, parallel search, SHAP or resampling was used.

The first `ml explain --dataset all` run failed because a reference float was inserted into a pandas integer column during local explanation. The source was corrected to use an object-typed alternate column; the complete second run succeeded for all 12 models. An initial Phase III export verification invoked system `python3` and failed to import the editable package; rerunning with `.venv/bin/python` passed. These failures were environmental/implementation corrections, not hidden research results.

The Phase IV editable-install command **could not complete in this sandbox**: pip's isolated build needed `setuptools>=75`, and the network could not reach the package index. A separate `--no-index --no-build-isolation` attempt also failed because the existing `.venv` does not contain `setuptools`. The pre-existing editable environment already contains the required scientific libraries, and `pip check`, all CLI commands and all tests passed. A fresh virtual-environment install remains **NOT TESTED here**; with normal package-index access, the documented command is the intended setup path.

## Split, leakage and source checks

| Task | Development | Untouched test | Test positives | CV strategy | Leakage check |
|---|---:|---:|---:|---|---|
| Heart | 242 | 61 | 28 | 5 stratified folds | `num` and derived target excluded; train/test disjoint |
| Diabetes | 416 | 104 | 64 | 5 stratified group folds | 251 raw predictor profiles; zero group overlap in holdout and every CV fold |
| Stroke | 4,088 | 1,022 | 50 | 5 stratified folds | `id` and target excluded; natural test imbalance preserved |

The independent verifier `scripts/verify_phase4_outputs.py` loaded all **15 saved estimators** (12 complete preprocessing pipelines and three dummy baselines), checked artifact SHA-256s, verified all five folds and group isolation, recomputed nine scalar metrics and each confusion matrix from saved models and untouched test rows, and found no mismatches. Tests mutate held-out or validation values and confirm fitted preprocessing parameters stay unchanged. Each primary pipeline contains imputation, encoding and optional scaling; no sampler is present, so no sampling leakage can occur. Hyperparameter search, chosen threshold and model selection use only development data. The selected algorithm is invariant to modified test-score fields in a controlled test.

The Phase I independent output verifier returned `PASS`, with no errors across five prepared tables and raw archive fingerprints. Phase III aggregate export check returned `PASS` for 19 files; PBIP structural check returned `PASS` for six pages, 32 tables and 29 visuals, **static only**. Desktop rendering and Service upload remain **NOT TESTED/BLOCKED** from Phase III. No Phase III deliverable was changed by Phase IV.

## Results and saved evidence

- **12/12 compulsory full experiments completed**: four algorithms on each of three datasets. **3/3 dummy baselines completed**. Five development folds per task; search grids, fold scores and chosen parameters are in `ml/registry.json`.
- Development-selected model: Logistic Regression for all three tasks. Selected test confusion matrices: heart `[[27,6],[2,26]]`; diabetes `[[27,13],[3,61]]`; stroke `[[772,200],[10,40]]`. Complete numbers appear in `docs/MODEL_COMPARISON.md` and `reports/tables/ml/`.
- Diabetes primary data retained all 520 records and 269 repeated rows; predictor-profile analysis found zero conflicting-label profiles. Development-only deduplication retained 202 unique profiles, dropping 214 repeated development rows. Same untouched test was used for sensitivity evaluation; it did not affect model choice.
- Stroke Logistic Regression used a development OOF threshold of 0.0698182314216704. Test recall .80 and precision .1667 expose a substantial false-positive burden; prior dummy accuracy .9511 came with zero positive recall.
- Artifacts: `ml/models/full/<task>/*.joblib` (12 complete pipelines and three dummy estimators, checksums listed in registry), `reports/ml/full/<task>/{split,experiment,explanations_*}.json`, three CSV comparison tables, and **51 PNG figures** under `reports/figures/ml/full/` (including ROC/PR, calibration, confusion matrices, model metrics, permutation importance, and tree graphics). All **90** full output paths and SHA-256s are listed in `reports/ml/artifact_manifest.json`; `--check` passed. A representative stroke PR figure was visually inspected and showed readable axes, legend and prevalence line.
- Three prediction CLI example commands returned class, score, threshold and local score-change output from reloaded models. The inputs in `examples/` are fictional test fixtures. Scores are not clinical probabilities.

## Automated tests

`tests/test_phase4_ml.py`: **15 passed in 8.09s**. It covers targets and exclusions, profile grouping including conflicting labels, group-disjoint/reproducible splits, fold-local imputation/scaling/encoding, known numeric-code encoding, no sampler, metrics and confusion matrices, threshold selection, selection without test access, small-fixture grid search, save/load equality, local explanation, input schema/range/unknown categories, unfitted factory, missing prepared data, escaped or absent artifacts, and inner-fold preprocessing isolation.

The full suite before the three final essential tests was **58 passed in 25.17s**. Final full suite after the configurable split and reporting refinements: **61 passed in 31.04s**. No existing test was removed or weakened.

## Requirement decision matrix

| Phase IV requirement | Entry point / evidence | Decision |
|---|---|
| Three separate source-label tasks, exclusions and provenance | `mediscope/ml/tasks.py`, registry, split JSON | PASS |
| 80/20 reproducible splits, diabetes profile isolation | `make_split`, controlled tests and verifier | PASS |
| Fold-local Phase I preprocessing, encoding, scaling | `candidate_pipeline`, leakage tests | PASS |
| Four compulsory models × three datasets | `training.py`, 12 full registry trials | PASS |
| Three dummy baselines | registry trials, verifier | PASS |
| Five-fold shared CV, modest tuning, quick mode | protocol JSON, CV candidate rows, quick registry | PASS |
| Natural class distributions, class weights and development threshold | stroke registry and split | PASS |
| Sampling-method comparison | no sampler installed or used | NOT TESTED |
| All compulsory metrics, ranking and calibration data | `evaluation.py`, test results and verifier | PASS |
| Development-only model selection and test isolation | `select_by_cv`, protocol, tests | PASS |
| Comparison tables and charts | CSV tables, 51 PNG figures | PASS |
| Global and local explanations, transformed feature names | `explainability.py`, 12 explanation JSONs | PASS |
| SHAP optional feasibility | documented as not performed | NOT TESTED |
| Input validation, saved-pipeline prediction and reload | `prediction.py`, examples, tests, CLI | PASS |
| Registry with hashes, versions, split, metrics, threshold | `ml/registry.json` | PASS |
| Fresh environment dependency installation in this sandbox | pip could not obtain build-time setuptools due network restriction | BLOCKED |
| Phase I/II and Phase III regression checks | full suite, Phase I and Phase III static verifiers | PASS |
| External validation and clinical usefulness | no external or prospective cohort | BLOCKED |
| Phase III Power BI Desktop/Service runtime | separate Phase III gate | BLOCKED |

**Phase IV research implementation is ready for academic code/report review.** Clinical use, external validation, resampling sensitivity and optional SHAP remain outside the demonstrated evidence. The Phase III Power BI runtime gates are still unresolved and are not claimed as Phase IV accomplishments.
