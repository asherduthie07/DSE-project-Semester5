# Data-quality report: UCI Early Stage Diabetes Risk Prediction

Research and education only. These data and future models are not clinically validated.

Source: https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction
Local raw SHA-256: `67594c0f11257688b57493798e70737b7156ba37a2e6ac75507ae3a35221a388`

The outputs retain missing feature values. Learned imputation, encoding, scaling, and optional IQR clipping must be fitted inside training folds.

## diabetes_data_upload.csv

Initial: **520 rows × 17 columns**. Final: **520 rows × 17 columns**.

Exact duplicates: 269 found, 0 removed, 269 retained. Record-key repeated rows: not applicable (no record key).

| Feature | Missing before | Missing after | Invalid | IQR outliers before | IQR outliers after |
|---|---:|---:|---:|---:|---:|
| Age | 0 | 0 | 0 | 4 | 4 |
| Gender | 0 | 0 | 0 |  |  |
| Polyuria | 0 | 0 | 0 |  |  |
| Polydipsia | 0 | 0 | 0 |  |  |
| sudden weight loss | 0 | 0 | 0 |  |  |
| weakness | 0 | 0 | 0 |  |  |
| Polyphagia | 0 | 0 | 0 |  |  |
| Genital thrush | 0 | 0 | 0 |  |  |
| visual blurring | 0 | 0 | 0 |  |  |
| Itching | 0 | 0 | 0 |  |  |
| Irritability | 0 | 0 | 0 |  |  |
| delayed healing | 0 | 0 | 0 |  |  |
| partial paresis | 0 | 0 | 0 |  |  |
| muscle stiffness | 0 | 0 | 0 |  |  |
| Alopecia | 0 | 0 | 0 |  |  |
| Obesity | 0 | 0 | 0 |  |  |
| class | 0 | 0 | 0 |  |  |

### Actions

- `parse_missing_tokens`: Recognize explicit source missing markers without filling values.
- `validate_and_cast_types`: Apply registered numeric, categorical, date, and impossibility rules; retain null features.
- `retain_exact_duplicates`: Identical values can represent distinct people; no proof of duplicate identity; rows=269.
- `retain_iqr_outliers`: IQR flags are descriptive, not proof of erroneous medical measurements.
