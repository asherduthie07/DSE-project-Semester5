# Phase I: data preparation policy

These datasets support academic analysis only. Neither the datasets nor future models establish clinical validity. Source archives are immutable and identified by the [registry](../data/metadata/datasets.json) SHA-256 values. The local ZIPs' original acquisition dates remain unknown.

## Deterministic source transformations

| Source | Import and validation | Preparation action | Target and identifiers |
|---|---|---|---|
| UCI Cleveland | Headerless `processed.cleveland.data`; 14 ordered fields; `?` becomes missing; numeric and code domains checked | Normalize integral category codes (`1.0` → `1`); retain missing `ca`/`thal` and all rows | Keep original `num` (0–4); add `heart_disease_binary = 1` when `num > 0`; both are excluded from model features |
| UCI early diabetes | `diabetes_data_upload.csv`; 520 rows in current source; 17 ordered fields; Yes/No symptoms and Positive/Negative target checked | Keep identical rows by default because source lacks a participant ID | `class` is never imputed; no source-derived identifier exists |
| Kaggle stroke | Registered CSV; 12 ordered fields; numeric ranges, codes, and target checked | Treat `smoking_status=Unknown` as an unavailable response; retain 201 missing BMI values and class imbalance | Keep `id` for traceability but exclude it from model features; `stroke` stays 0/1 and is never imputed |
| Synthea | Read `csv/patients.csv` and `csv/encounters.csv`; validate dates, costs, unique `Id`s, and patient foreign keys | Keep all encounters, including repeated patients and colliding patient/time/code signatures; retain optional blank fields | No disease target; simulated patients and visits stay in separate linked tables |

No whole-dataset imputation, normalization, encoding, deduplication, outlier capping, or outlier removal is applied by default. Analysis-ready CSVs are typed and validated but still contain missing features. This is intentional: learned transforms must fit on training folds within the unfitted [factory](../mediscope/preprocessors.py). No model is trained in Phase I.

## Rules and policies

- Missing tokens are `""`, `?`, `NA`, `N/A`, `NULL`, and `null`; the stroke `Unknown` response is separately counted before being set missing. Missing values and malformed or impossible values have separate report fields.
- Default invalid-value policy is `error`. An explicit `nullify` setting converts invalid **features** to missing with an audit entry; invalid or absent targets and required identifiers still fail. Domain bounds in `mediscope/schema.py` are broad impossibility checks, not diagnostic cutoffs.
- Exact duplicates are reported and retained. `exact_duplicate_policy=drop` requires a nonempty written `duplicate_removal_justification`. Unique record keys must not repeat. For Synthea, repeated `PATIENT` is valid because `Id` identifies each encounter.
- The IQR rule uses Q1 − 1.5×IQR and Q3 + 1.5×IQR on continuous measurements only. It flags extremes; it does not prove error. The default `outlier_policy=report_only` never changes values. Optional IQR clipping exists only as a transformer that learns its fences when a later training pipeline fits; it is off by default.
- `numeric_imputation` supports median, mean, or most frequent; `categorical_imputation` supports most frequent or a constant; `numeric_scaling` supports standard, min-max, robust, or none. These settings configure **unfitted** scikit-learn pipelines, not the exported whole dataset.
- Binary attributes have explicit 0/1 mappings in each dataset's `*_feature_roles.json`. Nominal attributes use one-hot encoding with ignored unseen categories. Unseen binary values encode as −1 for monitoring. None of the current source codes has a defensible ordinal ordering; Cleveland chest pain, slope, and thal codes are treated as nominal.

Use the default [configuration](../data/metadata/preparation_config.json), or copy it to another path and pass `--config`. Do not edit raw data to make validation pass. A checksum mismatch means the registry must be reviewed and updated after documenting the replacement download.

## Outputs and interpretation

`mediscope prepare --dataset all` writes `heart.csv`, `diabetes.csv`, `stroke.csv`, `synthea_patients.csv`, and `synthea_encounters.csv` under `data/processed/`; a config snapshot and three feature-role mapping files sit beside them. Each source has a JSON and Markdown report in `reports/quality/`, a per-feature CSV table in `reports/tables/`, and paired before/after boxplots in `reports/figures/`. The JSON contains source fingerprint, initial/final dimensions, missing values, invalid findings, duplicate decisions, IQR fences/counts, actions, and output CSV fingerprints. The before/after plots will generally match because valid extreme values are retained.

The prepared CSVs are excluded from Git because source data redistribution terms may differ, especially for the stroke archive. Reports, tables, and figures remain in the workspace for review. Re-running with unchanged source files, package versions, and configuration should reproduce the prepared CSV bytes; the current execution confirmed matching hashes on two runs.

## Limitations for later phases

- Diabetes has 269 identical full rows with no participant IDs. Retaining them avoids an unsupported claim that they represent duplicate people. Later experimental splits should evaluate repeated-profile leakage and report sensitivity to a justified deduplication policy.
- Stroke source provenance is unverified; `Unknown` smoking history and the strong class imbalance need explicit modeling treatment. Resampling, if used, must happen within training folds only.
- Synthea represents simulated people; its generated encounters cannot validate a clinical disease predictor. Optional blanks and repeated visits are expected.
- IQR flags, including very high BMI or glucose values, are not automatic errors. Default exports keep them. The chosen broad invalid-value bounds must be reviewed for any new dataset version.
- No future model performance, clinical interpretation, or Power BI/Hadoop result is implied by this phase.
