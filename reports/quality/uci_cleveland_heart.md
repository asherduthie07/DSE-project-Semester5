# Data-quality report: UCI Cleveland Heart Disease

Research and education only. These data and future models are not clinically validated.

Source: https://archive.ics.uci.edu/dataset/45/heart+disease
Local raw SHA-256: `b17cd273da9ce1caa4710fce80227ea454d4dbf9fcbc8e6a9121672751563adc`

The outputs retain missing feature values. Learned imputation, encoding, scaling, and optional IQR clipping must be fitted inside training folds.

## processed.cleveland.data

Initial: **303 rows × 14 columns**. Final: **303 rows × 15 columns**.

Exact duplicates: 0 found, 0 removed, 0 retained. Record-key repeated rows: not applicable (no record key).

| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |
|---|---:|---:|---:|---:|---:|
| age | 0 | 0 | 0 | 0 | 0 |
| sex | 0 | 0 | 0 |  |  |
| cp | 0 | 0 | 0 |  |  |
| trestbps | 0 | 0 | 0 | 9 | 9 |
| chol | 0 | 0 | 0 | 5 | 5 |
| fbs | 0 | 0 | 0 |  |  |
| restecg | 0 | 0 | 0 |  |  |
| thalach | 0 | 0 | 0 | 1 | 1 |
| exang | 0 | 0 | 0 |  |  |
| oldpeak | 0 | 0 | 0 | 5 | 5 |
| slope | 0 | 0 | 0 |  |  |
| ca | 4 | 4 | 0 |  |  |
| thal | 2 | 2 | 0 |  |  |
| num | 0 | 0 | 0 |  |  |
| heart_disease_binary | 0 | 0 | 0 |  |  |

### Actions

- `parse_missing_tokens`: Recognize explicit source missing markers without filling values.
- `validate_and_cast_types`: Apply registered numeric, categorical, date, and impossibility rules; retain null features.
- `canonicalize_cleveland_codes`: Integral codes such as 1.0 are represented as category string 1.
- `derive_target`: 1 if num > 0, else 0; preserve num.
- `retain_exact_duplicates`: Identical values can represent distinct people; no proof of duplicate identity; rows=0.
- `retain_iqr_outliers`: IQR flags are descriptive, not proof of erroneous medical measurements.
