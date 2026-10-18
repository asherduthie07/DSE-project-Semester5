# Phase II EDA: Healthcare Stroke Prediction

Source: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset
Provenance: unverified; do not assert real-world patient origin; source SHA-256 `83c150178a7a10439862a66b2703869aadc11f201c359436ae1df77d2b5e7485`.

Research and education only. Associations do not establish causation or clinical validity.

## Data and methods

- healthcare-dataset-stroke-data.csv: 5,110 rows × 12 columns; exact duplicate rows 0.

Continuous summaries use nonmissing denominators and sample variance. Numeric correlations use only registered continuous features and pairwise complete cases. Categorical tests use complete cases; exploratory p-values have within-table Benjamini–Hochberg adjustments. Missing categories remain explicit in frequency tables. No imputation was performed.

- stroke_positive_pct: 4.87279843444227
- smoking_unknown_recast_missing: 1544
- imbalance_warning: Class imbalance makes accuracy alone misleading in later modeling; no model is trained in Phase II.

## Strongest observed associations

- spearman age vs bmi: r=0.376, n=4909; exploratory association only.
- pearson age vs bmi: r=0.333, n=4909; exploratory association only.
- point_biserial stroke vs age: r=0.245, n=5110; exploratory association only.
- heart_disease vs stroke: Cramer's V=0.135, n=5110, 0 expected cells <5; exploratory association only.
- hypertension vs stroke: Cramer's V=0.128, n=5110, 0 expected cells <5; exploratory association only.

## Preregistered hypothesis tests

### H2: Is hypertension associated with stroke status?

H0: Hypertension and stroke are independent.
H1: Hypertension and stroke are associated.

Method: Pearson chi-square test, 1 df, no continuity correction (all expected cells >=5); alpha=0.05; Independent records and mutually exclusive categories; expected-cell rule selects Fisher where needed. Odds-ratio interval is approximate.
Observed statistic=83.5965, p=6.06812e-20; odds ratio, hypertension versus no hypertension=3.69756; 95% CI for odds ratio (approximate log-Wald interval): [2.74401, 4.98247].

Contingency cells (hypertension × stroke): {'no_hypertension_no_stroke': 4429, 'no_hypertension_stroke': 183, 'hypertension_no_stroke': 432, 'hypertension_stroke': 66}; expected minimum=24.267; phi=0.128.

At alpha=0.05, reject H0. Observed stroke proportions were 13.25% with hypertension and 3.97% without (difference 9.29%). The odds ratio and its interval describe magnitude; statistical significance alone does not establish clinical importance or causation.

Sampling limitation: Stroke source collection is unverified; cross-sectional association cannot establish temporal or causal direction.

### H3: Does mean average glucose differ by stroke status?

H0: Population mean glucose levels are equal.
H1: Population mean glucose levels differ.

Method: two-sided Welch unequal-variance t-test; alpha=0.05; Independent observations; numeric measurements; Welch does not require equal variances. Skew and influential values assessed with group summaries and trimmed sensitivity.
Observed statistic=6.98241, p=2.40144e-11; Hedges g (pooled-SD standardization)=0.618042; 95% CI for positive minus negative population mean: [19.9237, 35.5747].

Groups: positive n=249, mean=132.545, SD=61.921; negative n=4861, mean=104.796, SD=43.846; trimmed sensitivity p=8.26351e-11.

At alpha=0.05, reject H0. Mean avg_glucose_level was 132.54 in the positive group (n=249) and 104.80 in the negative group (n=4861); difference 27.75. Consider the original units, effect size, CI and sampling limits for practical importance. The trimmed test is a sensitivity check, not a replacement primary test.

Sampling limitation: Stroke source collection is unverified; skew, outliers and nonrandom sampling limit population inference.

## Evidence paths

- reports/tables/eda/kaggle_stroke_numeric.csv
- reports/tables/eda/kaggle_stroke_categorical.csv
- reports/tables/eda/kaggle_stroke_outcome.csv
- reports/tables/eda/kaggle_stroke_numeric_by_outcome.csv
- reports/tables/eda/kaggle_stroke_categorical_by_outcome.csv
- reports/tables/eda/kaggle_stroke_correlations.csv
- reports/tables/eda/kaggle_stroke_categorical_associations.csv
- reports/tables/eda/kaggle_stroke_age_group_by_stroke.csv
- reports/tables/eda/kaggle_stroke_hypertension_by_stroke.csv
- reports/tables/eda/kaggle_stroke_heart_disease_by_stroke.csv
- reports/tables/eda/kaggle_stroke_smoking_by_stroke.csv
- reports/tables/eda/kaggle_stroke_hypotheses.csv
- reports/tables/eda/kaggle_stroke_pearson_matrix.csv
- reports/tables/eda/kaggle_stroke_spearman_matrix.csv
- reports/figures/eda/kaggle_stroke_outcome.png
- reports/figures/eda/kaggle_stroke_age_histogram.png
- reports/figures/eda/kaggle_stroke_age_boxplot.png
- reports/figures/eda/kaggle_stroke_glucose_histogram.png
- reports/figures/eda/kaggle_stroke_glucose_boxplot.png
- reports/figures/eda/kaggle_stroke_bmi_boxplot.png
- reports/figures/eda/kaggle_stroke_smoking_frequency.png
- reports/figures/eda/kaggle_stroke_stroke_by_age_group.png
- reports/figures/eda/kaggle_stroke_pearson_heatmap.png
- reports/figures/eda/kaggle_stroke_spearman_heatmap.png
