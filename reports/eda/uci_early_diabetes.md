# Phase II EDA: UCI Early Stage Diabetes Risk Prediction

Source: https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction
Provenance: real-world; source SHA-256 `67594c0f11257688b57493798e70737b7156ba37a2e6ac75507ae3a35221a388`.

Research and education only. Associations do not establish causation or clinical validity.

## Data and methods

- diabetes_data_upload.csv: 520 rows × 17 columns; exact duplicate rows 269.

Continuous summaries use nonmissing denominators and sample variance. Numeric correlations use only registered continuous features and pairwise complete cases. Categorical tests use complete cases; exploratory p-values have within-table Benjamini–Hochberg adjustments. Missing categories remain explicit in frequency tables. No imputation was performed.

- identical_profiles: 269
- distinct_profiles: 251
- independence_warning: No participant identifier: identical profiles may be distinct people or repeat records. Retained; inferential independence cannot be verified.

## Strongest observed associations

- point_biserial class_binary vs Age: r=0.109, n=520; exploratory association only.
- Polyuria vs class: Cramer's V=0.666, n=520, 0 expected cells <5; exploratory association only.
- Polydipsia vs class: Cramer's V=0.649, n=520, 0 expected cells <5; exploratory association only.
## Evidence paths

- reports/tables/eda/uci_early_diabetes_numeric.csv
- reports/tables/eda/uci_early_diabetes_categorical.csv
- reports/tables/eda/uci_early_diabetes_outcome.csv
- reports/tables/eda/uci_early_diabetes_numeric_by_outcome.csv
- reports/tables/eda/uci_early_diabetes_categorical_by_outcome.csv
- reports/tables/eda/uci_early_diabetes_correlations.csv
- reports/tables/eda/uci_early_diabetes_categorical_associations.csv
- reports/tables/eda/uci_early_diabetes_symptom_yes_by_class.csv
- reports/tables/eda/uci_early_diabetes_unique_profile_class_counts.csv
- reports/tables/eda/uci_early_diabetes_pearson_matrix.csv
- reports/tables/eda/uci_early_diabetes_spearman_matrix.csv
- reports/figures/eda/uci_early_diabetes_outcome.png
- reports/figures/eda/uci_early_diabetes_age_histogram.png
- reports/figures/eda/uci_early_diabetes_age_boxplot.png
- reports/figures/eda/uci_early_diabetes_gender_frequency.png
- reports/figures/eda/uci_early_diabetes_polyuria_frequency.png
- reports/figures/eda/uci_early_diabetes_symptom_yes_by_class.png
