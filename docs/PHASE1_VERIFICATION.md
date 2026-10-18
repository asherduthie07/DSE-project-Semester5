# Phase I verification and audit

**Date:** 2026-10-18. **Scope:** data preparation only. **Decision:** Phase I implementation and current-workspace execution **PASS**; external provenance of the existing stroke and Synthea archives remains unresolved. No EDA, disease-model training, clinical validation, Power BI, MongoDB or Hadoop work was performed in this audit.

## 1. Environment and exact commands

Verified on macOS 15.5 (Darwin 24.5.0), Intel Core i9-9880H, x86_64, Python 3.13.2, pip 24.3.1, Git 2.45.2. Installed package versions: pandas 3.0.6, NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.9.1, Matplotlib 3.11.2, pytest 9.1.1. `pip check` returned **No broken requirements found**. The installed versions match all 22 entries in `requirements-phase1.lock.txt`.

The following executable commands were run from the project root (the per-dataset preparation commands were executed by a Python subprocess using these exact argument vectors):

```bash
uname -srm
sw_vers
sysctl -n machdep.cpu.brand_string
.venv/bin/python --version
.venv/bin/pip --version
git --version
.venv/bin/mediscope --help
.venv/bin/mediscope audit --help
.venv/bin/mediscope prepare --help
.venv/bin/mediscope audit --dataset uci_cleveland_heart
.venv/bin/mediscope audit --dataset uci_early_diabetes
.venv/bin/mediscope audit --dataset kaggle_stroke
.venv/bin/mediscope audit --dataset synthea_csv
.venv/bin/mediscope audit
.venv/bin/mediscope prepare --dataset uci_cleveland_heart
.venv/bin/mediscope prepare --dataset uci_early_diabetes
.venv/bin/mediscope prepare --dataset kaggle_stroke
.venv/bin/mediscope prepare --dataset synthea_csv
.venv/bin/mediscope prepare --dataset all
.venv/bin/python scripts/demo_phase1_fixtures.py
.venv/bin/python scripts/verify_phase1_outputs.py
.venv/bin/python -m pytest -vv
.venv/bin/python -m pip check
```

`sysctl` initially failed inside the restricted sandbox; the approved read-only retry returned the Intel CPU model above. The activated form `source .venv/bin/activate; mediscope health; python -m pytest -q` also ran successfully. The audit command now accepts `--dataset` and returns status 2 for missing, mismatched or unreadable sources; this was verified with a controlled missing-directory test.

## 2. Implementation entry points

| Operation | Actual entry point | Behavior |
|---|---|---|
| Registered source/schema validation | `mediscope.cli.audit_dataset`, `mediscope.preparation.read_registered_table`, `prepare_dataset`; rules in `mediscope.schema.SCHEMAS` | Checks ZIP/member, local SHA-256, ordered columns, width, target, types/domains and keys. |
| Missing-value analysis | `mediscope.cli.audit_table`, `mediscope.preparation._missing`, `prepare_table` | Counts source missing tokens; counts stroke `Unknown` separately; retains null features. |
| Duplicate analysis | `mediscope.cli.audit_table`, `mediscope.preparation.prepare_table` | Reports exact rows, unique keys and encounter signatures. Exact removal is opt-in with a written rationale. |
| Outlier detection | `mediscope.preparation.iqr_summary` | Q1/Q3 and 1.5×IQR fences for continuous fields; no default capping/removal. |
| Cleaning and target conversion | `mediscope.preparation.prepare_table` | Parses/validates types, normalizes Cleveland category codes, marks stroke `Unknown` missing, derives and preserves the heart target. |
| Categorical encoding | `mediscope.preprocessors.build_preprocessor`, `feature_roles` | Unfitted binary `OrdinalEncoder` and nominal `OneHotEncoder`; known mappings saved per dataset. |
| Numerical imputation/scaling | `mediscope.preprocessors.build_preprocessor` | Unfitted `SimpleImputer`, optional fold-local `IQRClipper`, Standard/MinMax/Robust scaling. |
| Quality-report generation | `mediscope.reports.export_dataset`, `plot_before_after` | CSV, JSON, Markdown, quality table and PNG artifacts. |
| Independent output reconciliation | `scripts/verify_phase1_outputs.py` | Read-only cross-check of archives, outputs, reports, target domains and Synthea links. |

## 3. Registered sources and observed schemas

Every required raw ZIP exists, and all four local SHA-256 values matched both the registry and the before/after preparation check. Every registered member had the expected ordered columns and row width. `audit` returned `available` for each and for all four together.

| Dataset / required ZIP member | Raw rows × columns | Final rows × columns | Raw missing values (nonzero only) | Exact duplicate rows |
|---|---:|---:|---|---:|
| Cleveland / `processed.cleveland.data` | 303 × 14 | 303 × 15 | `ca` 4; `thal` 2 | 0 |
| Diabetes / `diabetes_data_upload.csv` | 520 × 17 | 520 × 17 | None recognized | 269 retained |
| Stroke / `healthcare-dataset-stroke-data.csv` | 5,110 × 12 | 5,110 × 12 | `bmi` 201 | 0 |
| Synthea / `csv/patients.csv` | 1,171 × 25 | 1,171 × 25 | `DEATHDATE` 1,000; `DRIVERS` 213; `PASSPORT` 273; `PREFIX` 244; `SUFFIX` 1,159; `MAIDEN` 840; `MARITAL` 380; `ZIP` 543 | 0 |
| Synthea / `csv/encounters.csv` | 53,346 × 15 | 53,346 × 15 | `REASONCODE` 39,569; `REASONDESCRIPTION` 39,569 | 0 |

Registered ordered columns were verified against source headers or, for headerless Cleveland, against all 14 field positions:

- Cleveland: `age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal, num`.
- Diabetes: `Age, Gender, Polyuria, Polydipsia, sudden weight loss, weakness, Polyphagia, Genital thrush, visual blurring, Itching, Irritability, delayed healing, partial paresis, muscle stiffness, Alopecia, Obesity, class`.
- Stroke: `id, gender, age, hypertension, heart_disease, ever_married, work_type, Residence_type, avg_glucose_level, bmi, smoking_status, stroke`.
- Synthea patients: `Id, BIRTHDATE, DEATHDATE, SSN, DRIVERS, PASSPORT, PREFIX, FIRST, LAST, SUFFIX, MAIDEN, MARITAL, RACE, ETHNICITY, GENDER, BIRTHPLACE, ADDRESS, CITY, STATE, COUNTY, ZIP, LAT, LON, HEALTHCARE_EXPENSES, HEALTHCARE_COVERAGE`.
- Synthea encounters: `Id, START, STOP, PATIENT, ORGANIZATION, PROVIDER, PAYER, ENCOUNTERCLASS, CODE, DESCRIPTION, BASE_ENCOUNTER_COST, TOTAL_CLAIM_COST, PAYER_COVERAGE, REASONCODE, REASONDESCRIPTION`.

## 4. Targets, keys and suspicious values

| Dataset | Verified target | Key and relationship result | Extreme/quality observations |
|---|---|---|---|
| Cleveland | `num`: 0=164, 1=55, 2=36, 3=35, 4=13. Derived `heart_disease_binary`: 0=164, 1=139; every derived value equals `int(num > 0)`. | No patient ID in this table. | Cholesterol 126–564; resting BP 94–200; `oldpeak` 0–6.2. IQR flags: `trestbps` 9, `chol` 5, `thalach` 1, `oldpeak` 5. |
| Diabetes | `class`: Negative=200, Positive=320; no missing target. | No participant ID; 269 identical full-row profiles retained. | Age 16–90; IQR age flags 4. |
| Stroke | `stroke`: 0=4,861, 1=249; no missing target. | `id` unique (0 duplicates), retained in CSV and excluded from model features. | BMI 10.3–97.6 (201 missing); glucose 55.12–271.74. IQR flags: glucose 627, BMI 110. `Unknown` smoking was marked missing in 1,544 rows. |
| Synthea | No disease target. | Patient and encounter `Id`s unique; 0 orphan encounters; 52,175 encounter rows repeat a `PATIENT`; 372 share patient/start/code while keeping distinct encounter IDs. | Simulated costs and locations are not clinical observations. IQR flags include 423 encounter base-cost values and 101 patient coverage values. |

All current source values passed the implemented broad numeric/category/date impossibility rules: **zero domain-invalid values**. An IQR flag is not an invalid-value finding. Reported high measurements were preserved. Broad bounds cannot establish whether an unusual observation is clinically plausible. Synthea optional blanks are expected. The source page's generic missing-value flag for diabetes differs from the current 520-row CSV's zero recognized missing tokens; the file itself was audited.

## 5. Operations performed and controlled test-fixture demonstrations

The actual exports keep feature nulls and all rows by default. Stroke's 1,544 `Unknown` smoking responses change from a source category to missing; Cleveland receives one derived target column. No targets were imputed, no exact rows were removed, no IQR extremes were capped, and no whole-dataset normalization or one-hot encoding was performed. Unfitted pipeline factories are available for later fold-local use.

`python scripts/demo_phase1_fixtures.py` ran on **invented test-only** CSVs in `tests/fixtures/` and produced the following observed results. These are behavioral checks, not research statistics:

| Controlled input / expected behavior | Actual behavior |
|---|---|
| `?` age is missing; age 200 is invalid and separate | Source missing age=1; invalid age=1; with explicit `nullify`, final missing age=2. |
| Two identical diabetes rows remain by default | Exact duplicate count=1; all 3 valid demonstration rows retained. |
| Age 119 is extreme but within the documented domain | Retained (`true`). |
| Unknown symptom value `Maybe` is invalid | Invalid `Polyuria` count=1; explicit `nullify` turns it missing. |
| `[1,2,3,4,100]` has one IQR outlier | Outlier count=1; original 100 remains unchanged. |
| Two encounters for one patient have distinct visit IDs | 2 visits retained; 1 patient and 2 unique visits. A duplicated encounter `Id` is rejected in a separate test. |
| Unseen holdout categories must not change the fitted map | Binary `hypertension` encoded −1; unseen `gender` has `[0,0]` one-hot values. |

Default `invalid_feature_policy=error` rejects age 200 and `Maybe`; the fixture demo uses an **explicit** `nullify` configuration to show the alternative. The fixture rows are never written to `data/raw/` or included in dataset reports.

## 6. Training/test and cross-validation leakage checks

The production `build_preprocessor` returns a new, unfitted `ColumnTransformer`. Its `SimpleImputer`, encoders, scaler and optional IQR clipper are nested within pipelines. The tests fit only their controlled training rows, then transform held-out rows.

- Controlled stroke training rows produced BMI median **30.0** and age scaler mean **35.0**. The held-out file contains ages 99/missing and BMI 140/missing. Replacing its age and BMI with 9,999 and −9,999 and changing its categories did **not** alter the stored imputer, scaler or one-hot category parameters.
- With `KFold(n_splits=3)`, a fresh factory was fitted on each training subset. The fold-local age means were **45.0, 35.0, 25.0**. Transforming original and modified validation rows did not change each fold's fitted parameters. This checks preprocessing isolation during cross-validation without training a disease model.
- The default exported CSVs retain null features. Later modeling must put this factory inside each train/test or CV training procedure; Phase I does not itself run a predictive evaluation.

## 7. Automated tests and output reconciliation

Final command `.venv/bin/python -m pytest -vv` collected **20 tests; all 20 PASSED in 2.29s**. The passing test names were:

```text
test_controlled_diabetes_missing_duplicate_extreme_and_invalid
test_controlled_repeated_encounters_and_duplicate_unique_key
test_audit_dataset_selection_and_missing_archive
test_audit_marks_mismatched_schema_invalid
test_holdout_values_cannot_change_fitted_preprocessing
test_each_cv_fold_fits_only_its_training_subset
test_output_verifier_reports_tampered_csv
test_missing_tokens_and_missing_target_schema
test_incorrect_column_order_rejected
test_heart_target_preserved_and_binary_derived
test_duplicate_retention_and_justified_removal
test_invalid_values_are_distinct_from_missing
test_iqr_is_descriptive_and_extremes_remain
test_unknown_categories_and_feature_mappings
test_training_only_imputation_and_iqr_fit
test_nullable_source_columns_enter_unfitted_pipeline
test_preparation_reproducibility
test_repeated_hospital_visits_are_retained
test_health_reads_all_registered_datasets
test_audit_reports_schema_and_missing_tokens
```

The independent `scripts/verify_phase1_outputs.py` run returned **PASS, 0 errors**. It reconciled raw and final columns/rows, source missing and exact duplicate counts, documented removals (all zero), final missing counts, output SHA-256 values, target domains, heart target conversion, IQR counts, quality-table values, PNG files, saved configuration, unique encounter IDs and the Synthea patient foreign key. Its per-table check counts passed were 18/18 heart, 13/13 diabetes, 15/15 stroke, 15/15 Synthea patients and 14/14 Synthea encounters.

SHA-256 was calculated for all four raw ZIPs before and after the sequence of single-dataset preparation commands and the all-dataset command. **All four were unchanged and matched the registry.** After another `prepare --dataset all`, hash comparisons found all **5 prepared CSVs, 4 JSON reports, 4 Markdown reports, 5 quality tables and 5 PNG figures byte-identical** to the preceding run. Row counts reconcile with the reports: every source has 0 documented removals and equal initial/final row counts. The reports contain source-derived data-quality counts and no fabricated model-performance metrics. A controlled tamper test confirmed the verifier returns **FAIL** when a prepared CSV is damaged.

## 8. Generated output paths

- Prepared CSVs: `data/processed/heart.csv`, `diabetes.csv`, `stroke.csv`, `synthea_patients.csv`, `synthea_encounters.csv`.
- Saved settings: `data/processed/<dataset ID>_preparation_config.json` for all four; `<dataset ID>_feature_roles.json` for heart, diabetes and stroke.
- Reports: `reports/quality/uci_cleveland_heart.{json,md}`, `uci_early_diabetes.{json,md}`, `kaggle_stroke.{json,md}`, `synthea_csv.{json,md}`.
- Tables: `reports/tables/uci_cleveland_heart_heart_quality.csv`, `uci_early_diabetes_diabetes_quality.csv`, `kaggle_stroke_stroke_quality.csv`, `synthea_csv_synthea_patients_quality.csv`, `synthea_csv_synthea_encounters_quality.csv`.
- Figures: matching `reports/figures/<dataset ID>_<table>_boxplot.png` paths for the five tables.
- Verification tools and controlled fixtures: `scripts/verify_phase1_outputs.py`, `scripts/demo_phase1_fixtures.py`, `tests/fixtures/*.csv`.

Prepared CSVs are ignored by Git and exist in this workspace; reports, tables and figures are reviewable files. The raw archives remain ignored by Git and unchanged.

## 9. Known issues and unfinished work

- The local ZIP checksums prove file identity here, but original download dates and exact acquisition links were not recorded. Stroke patient collection provenance is unverified. The Synthea archive's generator release and seed are unknown. These are **provenance limitations**, not reasons to label simulated data as real patients.
- Diabetes has 269 identical rows without participant IDs. They are retained; later train/test design must assess repeated-profile leakage and sensitivity to a justified deduplication choice.
- Stroke classes are imbalanced (249 positive of 5,110). Phase I does not rebalance, because any resampling belongs inside later training folds.
- The current broad domain bounds identify obvious impossibilities, not every medically implausible value. IQR outliers are not automatically errors.
- There is no clinically validated disease prediction, model score, EDA result, Power BI dashboard, MongoDB ingestion or Hadoop job in Phase I. Those are outside this audit's scope and require later phase approval.

No compulsory **Phase I preparation operation** remains unfinished on the current available files. Source provenance questions above remain unresolved and must be disclosed in the academic report.

## 10. Compulsory Phase I decision matrix

| Requirement | Decision | Evidence / limit |
|---|---|---|
| 1. Data import and schema/target validation | **PASS** | Four registered archives and five tables audited; missing file, target and schema tests pass. |
| 2. Missing values and invalid-value separation | **PASS** | Per-feature counts, explicit source tokens, configurable fold-local imputation; target never imputed. |
| 3. Exact/key duplicates and repeated encounters | **PASS** | 269 identical diabetes rows retained; unique IDs and Synthea links checked; justified removal path tested. |
| 4. IQR outliers and impossible-value rules | **PASS** | All five tables summarized and plotted; domain-invalid counts zero; extremes retained by default. |
| 5. Categorical encoding and mappings | **PASS** | Binary/nominal roles, saved mapping files, unseen-category tests; no defensible ordinal fields in current sources. |
| 6. Numerical scaling and leakage prevention | **PASS** | Unfitted factories; holdout mutation and fold-local parameter tests pass. |
| 7. Dataset-specific heart/diabetes/stroke/Synthea logic | **PASS** | Target conversion, 520-row dataset check, stroke ID/missingness, patient foreign key verified. |
| 8. JSON/Markdown quality reports and comparisons | **PASS** | Four report pairs, five tables and five before/after figures generated and reconciled. |
| 9. Reproducible outputs, config and CLI | **PASS** | Per-dataset/all CLI runs, unchanged raw hashes, repeated output hashes identical, config snapshots saved. |
| 10. Automated and controlled-fixture tests | **PASS** | 20 passing tests, fixture demonstration and independent output verifier PASS. |
| External source acquisition provenance | **BLOCKED** | Existing archives lack original download timestamps/exact links; stroke collection origin and Synthea seed/version cannot be reconstructed from these ZIPs. This does not block running Phase I, but limits source claims. |
