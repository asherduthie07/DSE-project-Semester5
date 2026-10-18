# Data-quality report: Healthcare Stroke Prediction

Research and education only. These data and future models are not clinically validated.

Source: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset
Local raw SHA-256: `83c150178a7a10439862a66b2703869aadc11f201c359436ae1df77d2b5e7485`

The outputs retain missing feature values. Learned imputation, encoding, scaling, and optional IQR clipping must be fitted inside training folds.

## healthcare-dataset-stroke-data.csv

Initial: **5110 rows × 12 columns**. Final: **5110 rows × 12 columns**.

Exact duplicates: 0 found, 0 removed, 0 retained. Record-key repeated rows: 0.

| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |
|---|---:|---:|---:|---:|---:|
| id | 0 | 0 | 0 |  |  |
| gender | 0 | 0 | 0 |  |  |
| age | 0 | 0 | 0 | 0 | 0 |
| hypertension | 0 | 0 | 0 |  |  |
| heart_disease | 0 | 0 | 0 |  |  |
| ever_married | 0 | 0 | 0 |  |  |
| work_type | 0 | 0 | 0 |  |  |
| Residence_type | 0 | 0 | 0 |  |  |
| avg_glucose_level | 0 | 0 | 0 | 627 | 627 |
| bmi | 201 | 201 | 0 | 110 | 110 |
| smoking_status | 0 | 1544 | 0 |  |  |
| stroke | 0 | 0 | 0 |  |  |

### Actions

- `parse_missing_tokens`: Recognize explicit source missing markers without filling values.
- `validate_and_cast_types`: Apply registered numeric, categorical, date, and impossibility rules; retain null features.
- `missing_response`: Source 'Unknown' denotes unavailable smoking history; rows=1544.
- `retain_exact_duplicates`: Identical values can represent distinct people; no proof of duplicate identity; rows=0.
- `retain_iqr_outliers`: IQR flags are descriptive, not proof of erroneous medical measurements.
