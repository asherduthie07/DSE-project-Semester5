# Data-quality report: Synthea synthetic patients and encounters

Research and education only. These data and future models are not clinically validated.

Source: https://synthetichealth.github.io/downloads.html
Local raw SHA-256: `4194b18c11eaedcf0d5d5dd448d8ac9661f14381e2ef9f109215dc42266cd38a`

The outputs retain missing feature values. Learned imputation, encoding, scaling, and optional IQR clipping must be fitted inside training folds.

## csv/patients.csv

Initial: **1171 rows × 25 columns**. Final: **1171 rows × 25 columns**.

Exact duplicates: 0 found, 0 removed, 0 retained. Record-key repeated rows: 0.

| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |
|---|---:|---:|---:|---:|---:|
| Id | 0 | 0 | 0 |  |  |
| BIRTHDATE | 0 | 0 | 0 |  |  |
| DEATHDATE | 1000 | 1000 | 0 |  |  |
| SSN | 0 | 0 | 0 |  |  |
| DRIVERS | 213 | 213 | 0 |  |  |
| PASSPORT | 273 | 273 | 0 |  |  |
| PREFIX | 244 | 244 | 0 |  |  |
| FIRST | 0 | 0 | 0 |  |  |
| LAST | 0 | 0 | 0 |  |  |
| SUFFIX | 1159 | 1159 | 0 |  |  |
| MAIDEN | 840 | 840 | 0 |  |  |
| MARITAL | 380 | 380 | 0 |  |  |
| RACE | 0 | 0 | 0 |  |  |
| ETHNICITY | 0 | 0 | 0 |  |  |
| GENDER | 0 | 0 | 0 |  |  |
| BIRTHPLACE | 0 | 0 | 0 |  |  |
| ADDRESS | 0 | 0 | 0 |  |  |
| CITY | 0 | 0 | 0 |  |  |
| STATE | 0 | 0 | 0 |  |  |
| COUNTY | 0 | 0 | 0 |  |  |
| ZIP | 543 | 543 | 0 |  |  |
| LAT | 0 | 0 | 0 | 29 | 29 |
| LON | 0 | 0 | 0 | 163 | 163 |
| HEALTHCARE_EXPENSES | 0 | 0 | 0 | 0 | 0 |
| HEALTHCARE_COVERAGE | 0 | 0 | 0 | 101 | 101 |

### Actions

- `parse_missing_tokens`: Recognize explicit source missing markers without filling values.
- `validate_and_cast_types`: Apply registered numeric, categorical, date, and impossibility rules; retain null features.
- `retain_exact_duplicates`: Identical values can represent distinct people; no proof of duplicate identity; rows=0.
- `retain_iqr_outliers`: IQR flags are descriptive, not proof of erroneous medical measurements.

## csv/encounters.csv

Initial: **53346 rows × 15 columns**. Final: **53346 rows × 15 columns**.

Exact duplicates: 0 found, 0 removed, 0 retained. Record-key repeated rows: 372.

Patient-encounter foreign key: 0 orphan encounters.

| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |
|---|---:|---:|---:|---:|---:|
| Id | 0 | 0 | 0 |  |  |
| START | 0 | 0 | 0 |  |  |
| STOP | 0 | 0 | 0 |  |  |
| PATIENT | 0 | 0 | 0 |  |  |
| ORGANIZATION | 0 | 0 | 0 |  |  |
| PROVIDER | 0 | 0 | 0 |  |  |
| PAYER | 0 | 0 | 0 |  |  |
| ENCOUNTERCLASS | 0 | 0 | 0 |  |  |
| CODE | 0 | 0 | 0 |  |  |
| DESCRIPTION | 0 | 0 | 0 |  |  |
| BASE_ENCOUNTER_COST | 0 | 0 | 0 | 423 | 423 |
| TOTAL_CLAIM_COST | 0 | 0 | 0 | 423 | 423 |
| PAYER_COVERAGE | 0 | 0 | 0 | 0 | 0 |
| REASONCODE | 39569 | 39569 | 0 |  |  |
| REASONDESCRIPTION | 39569 | 39569 | 0 |  |  |

### Actions

- `parse_missing_tokens`: Recognize explicit source missing markers without filling values.
- `validate_and_cast_types`: Apply registered numeric, categorical, date, and impossibility rules; retain null features.
- `retain_exact_duplicates`: Identical values can represent distinct people; no proof of duplicate identity; rows=0.
- `retain_colliding_visit_signatures`: Same patient, time, and code can still have distinct encounter IDs; no rows removed; rows=372.
- `retain_iqr_outliers`: IQR flags are descriptive, not proof of erroneous medical measurements.
- `retain_repeated_patient_visits`: PATIENT is a foreign key; multiple encounter IDs per patient are valid; rows=52175.
