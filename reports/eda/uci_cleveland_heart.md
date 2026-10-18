# Phase II EDA: UCI Cleveland Heart Disease

Source: https://archive.ics.uci.edu/dataset/45/heart+disease
Provenance: real-world; source SHA-256 `b17cd273da9ce1caa4710fce80227ea454d4dbf9fcbc8e6a9121672751563adc`.

Research and education only. Associations do not establish causation or clinical validity.

## Data and methods

- processed.cleveland.data: 303 rows × 15 columns; exact duplicate rows 0.

Continuous summaries use nonmissing denominators and sample variance. Numeric correlations use only registered continuous features and pairwise complete cases. Categorical tests use complete cases; exploratory p-values have within-table Benjamini–Hochberg adjustments. Missing categories remain explicit in frequency tables. No imputation was performed.

- target_rule: heart_disease_binary = 1 when original num > 0; num remains available but is not analyzed as continuous

## Strongest observed associations

- spearman thalach vs oldpeak: r=-0.432, n=303; exploratory association only.
- point_biserial heart_disease_binary vs oldpeak: r=0.425, n=303; exploratory association only.
- point_biserial heart_disease_binary vs thalach: r=-0.417, n=303; exploratory association only.
- thal vs heart_disease_binary: Cramer's V=0.526, n=301, 0 expected cells <5; exploratory association only.
- cp vs heart_disease_binary: Cramer's V=0.520, n=303, 0 expected cells <5; exploratory association only.

## Preregistered hypothesis tests

### H1: Does mean age differ by recorded heart disease?

H0: Population mean ages are equal.
H1: Population mean ages differ.

Method: two-sided Welch unequal-variance t-test; alpha=0.05; Independent observations; numeric measurements; Welch does not require equal variances. Skew and influential values assessed with group summaries and trimmed sensitivity.
Observed statistic=4.03035, p=7.06144e-05; Hedges g (pooled-SD standardization)=0.456687; 95% CI for positive minus negative population mean: [2.06768, 6.01339].

Groups: positive n=139, mean=56.626, SD=7.938; negative n=164, mean=52.585, SD=9.512; trimmed sensitivity p=2.29659e-05.

At alpha=0.05, reject H0. Mean age was 56.63 in the positive group (n=139) and 52.59 in the negative group (n=164); difference 4.04. Consider the original units, effect size, CI and sampling limits for practical importance. The trimmed test is a sensitivity check, not a replacement primary test.

Sampling limitation: Historical, small, nonrandom Cleveland sample; patient independence is assumed, not demonstrable.

## Evidence paths

- reports/tables/eda/uci_cleveland_heart_numeric.csv
- reports/tables/eda/uci_cleveland_heart_categorical.csv
- reports/tables/eda/uci_cleveland_heart_outcome.csv
- reports/tables/eda/uci_cleveland_heart_numeric_by_outcome.csv
- reports/tables/eda/uci_cleveland_heart_categorical_by_outcome.csv
- reports/tables/eda/uci_cleveland_heart_correlations.csv
- reports/tables/eda/uci_cleveland_heart_categorical_associations.csv
- reports/tables/eda/uci_cleveland_heart_original_num.csv
- reports/tables/eda/uci_cleveland_heart_hypotheses.csv
- reports/tables/eda/uci_cleveland_heart_pearson_matrix.csv
- reports/tables/eda/uci_cleveland_heart_spearman_matrix.csv
- reports/figures/eda/uci_cleveland_heart_outcome.png
- reports/figures/eda/uci_cleveland_heart_age_histogram.png
- reports/figures/eda/uci_cleveland_heart_age_boxplot.png
- reports/figures/eda/uci_cleveland_heart_chest_pain_frequency.png
- reports/figures/eda/uci_cleveland_heart_pearson_heatmap.png
- reports/figures/eda/uci_cleveland_heart_spearman_heatmap.png
