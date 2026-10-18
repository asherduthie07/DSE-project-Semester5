# Phase II EDA: Synthea synthetic patients and encounters

Source: https://synthetichealth.github.io/downloads.html
Provenance: synthetic; source SHA-256 `4194b18c11eaedcf0d5d5dd448d8ac9661f14381e2ef9f109215dc42266cd38a`.

Research and education only. Associations do not establish causation or clinical validity.

## Data and methods

- csv/patients.csv: 1,171 rows × 25 columns; exact duplicate rows 0.
- csv/encounters.csv: 53,346 rows × 15 columns; exact duplicate rows 0.

Continuous summaries use nonmissing denominators and sample variance. Numeric correlations use only registered continuous features and pairwise complete cases. Categorical tests use complete cases; exploratory p-values have within-table Benjamini–Hochberg adjustments. Missing categories remain explicit in frequency tables. No imputation was performed.

- distinct_patients: 1171
- encounters: 53346
- patients_with_zero_encounters: 0
- mean_encounters_per_patient: 45.55593509820666
- median_encounters_per_patient: 27.0
- orphan_encounters: 0
- valid_age_at_encounter_n: 53346
- invalid_or_missing_age_at_encounter_n: 0
- valid_start_dates: 53346
- reason_code_nonmissing_n: 13777
- interpretation: All records are simulated. Encounter counts are visits, not distinct people or disease incidence.

## Strongest observed associations

- spearman BASE_ENCOUNTER_COST vs TOTAL_CLAIM_COST: r=1.000, n=53346; exploratory association only.
- pearson BASE_ENCOUNTER_COST vs TOTAL_CLAIM_COST: r=1.000, n=53346; exploratory association only.
- spearman HEALTHCARE_EXPENSES vs HEALTHCARE_COVERAGE: r=0.596, n=1171; exploratory association only.
## Evidence paths

- reports/tables/eda/synthea_csv_synthea_patients_numeric.csv
- reports/tables/eda/synthea_csv_synthea_patients_correlations.csv
- reports/tables/eda/synthea_csv_synthea_encounters_numeric.csv
- reports/tables/eda/synthea_csv_synthea_encounters_correlations.csv
- reports/tables/eda/synthea_csv_encounters_per_patient_distribution.csv
- reports/tables/eda/synthea_csv_encounter_class.csv
- reports/tables/eda/synthea_csv_encounter_age.csv
- reports/tables/eda/synthea_csv_monthly_encounters.csv
- reports/tables/eda/synthea_csv_reason_description_top.csv
- reports/tables/eda/synthea_csv_synthea_patients_pearson_matrix.csv
- reports/tables/eda/synthea_csv_synthea_patients_spearman_matrix.csv
- reports/tables/eda/synthea_csv_synthea_encounters_pearson_matrix.csv
- reports/tables/eda/synthea_csv_synthea_encounters_spearman_matrix.csv
- reports/figures/eda/synthea_csv_patient_gender_frequency.png
- reports/figures/eda/synthea_csv_encounter_class_frequency.png
- reports/figures/eda/synthea_csv_encounters_per_patient.png
- reports/figures/eda/synthea_csv_age_at_encounter.png
- reports/figures/eda/synthea_csv_monthly_encounters.png
- reports/figures/eda/synthea_csv_synthea_patients_pearson_heatmap.png
- reports/figures/eda/synthea_csv_synthea_patients_spearman_heatmap.png
- reports/figures/eda/synthea_csv_synthea_encounters_pearson_heatmap.png
- reports/figures/eda/synthea_csv_synthea_encounters_spearman_heatmap.png
