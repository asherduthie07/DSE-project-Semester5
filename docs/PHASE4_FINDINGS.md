# Phase IV findings and report interpretation

## Study design

Three separate binary source-label tasks were trained on verified Phase I prepared data: Cleveland heart (303 records), early-stage diabetes symptoms (520 records), and stroke (5,110 records). The positive labels are respectively `heart_disease_binary=1`, `class=Positive` and `stroke=1`. The original heart `num`, stroke `id`, and every target column are absent from predictors. Synthea remains an analytics cohort, not a disease-label task.

One reproducible untouched holdout per task was defined before tuning. Heart and stroke use stratified 80/20 splits. Diabetes uses predictor-profile groups for a group-disjoint 416/104 split. Five identical development CV folds are shared by all algorithms for each task. Every model is a Phase I preprocessing and estimator pipeline; imputation, category encoding and scaling fit within the training fold. No resampling was used. Search spaces and selection rules were registered in `docs/PHASE4_METHODOLOGY.md` and `data/metadata/ml_experiment_config.json` before comparisons.

## Model results

The complete 12-model plus three-dummy table, including all compulsory metrics and confusion matrices, is in [MODEL_COMPARISON.md](MODEL_COMPARISON.md). Logistic Regression was selected on development CV for each task: heart F1 **0.8473**, diabetes balanced accuracy **0.9348**, stroke average precision **0.1945**. Test performance for these selected models was:

| Task | Test n (positive) | Accuracy | Precision | Recall | F1 | Balanced accuracy | ROC-AUC | Average precision | False positives | False negatives |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Heart | 61 (28) | .8689 | .8125 | .9286 | .8667 | .8734 | .9697 | .9683 | 6 | 2 |
| Diabetes | 104 (64) | .8462 | .8243 | .9531 | .8841 | .8141 | .9570 | .9767 | 13 | 3 |
| Stroke | 1,022 (50) | .7945 | .1667 | .8000 | .2759 | .7971 | .8403 | .2632 | 200 | 10 |

Exact values are in `ml/registry.json`; the rounded ROC-AUC and balanced accuracy values in this table should be checked against that file if quoted to more precision. Confusion matrices for the selected models, in `[[TN,FP],[FN,TP]]` order, are heart `[[27,6],[2,26]]`, diabetes `[[27,13],[3,61]]`, stroke `[[772,200],[10,40]]`. A test score is not a clinically validated probability of disease.

## Error patterns and model choice

Heart Logistic Regression missed two of 28 test positives and falsely flagged six of 33 negatives. The heart test set is small enough that single observations materially change rates. Diabetes Logistic Regression missed three of 64 positives and falsely flagged 13 of 40 negatives. Although Random Forest had a higher test F1 on both tasks, the prespecified validation criterion favored Logistic Regression; switching after reading test performance would compromise the held-out evaluation.

Stroke has 249 positive cases in 5,110 rows, about 4.87%. The selected development-only operating threshold near 0.0698 produced test recall .80 but precision .1667. It flagged 200 negatives to identify 40 positives. The prior-only dummy scored .9511 accuracy by predicting all negative, while its positive recall was zero. Average precision and explicit error counts are more informative here than accuracy. None of these operating points is a medical screening recommendation.

## Repeated profiles and sensitivity

Diabetes has **251 unique predictor profiles**, **269 repeated rows**, and **zero conflicting-label profiles** in the verified prepared table. Repeated profiles are never split between development/test or inner folds. The sensitivity experiment kept only 202 distinct development profiles (removing 214 repeated development rows), refit each CV-selected hyperparameter configuration, and evaluated on the same untouched group-disjoint test. For example, deduplicated Logistic Regression had test F1 **.8507**, versus **.8841** in the primary analysis. This is sensitivity evidence only; without participant identifiers, neither the repeats nor the unique profiles prove independent persons.

## Explanation findings

Five-repeat permutation on the first development validation fold of selected Logistic Regression identified the largest score drops for heart as `thal` (.107), `ca` (.093) and `thalach` (.061); for diabetes as `Polyuria` (.108), `Irritability` (.086) and `Polydipsia` (.084); for stroke as `age` (.125), `work_type` (.008) and `bmi` (.003). These are fold-specific importance values in the respective selection metric, not effect sizes or causes. JSON files also list encoded Logistic Regression coefficients, tree/forest importances, and local score-change examples from development rows. The CLI returns a local score-change explanation for a validated hypothetical input.

## Limitations and report language

The source cohorts have unclear sampling and outcome adjudication, and there is no external validation. The stroke holdout contains only 50 positives. Diabetes profile repeats limit independence; no patient identity is available. Calibration plots are descriptive. The chosen stroke threshold reflects an exploratory development-only tradeoff, not clinical utility. Correlated predictors complicate importance interpretation, and individual score changes are not causal. SHAP and sampling-strategy sensitivity were not performed. Phase III Power BI runtime blockers remain separate. See [MODEL_LIMITATIONS.md](MODEL_LIMITATIONS.md) for the full caveat set.

Suggested report wording: “In a reproducible, group-aware comparison of four classifiers on three distinct source datasets, Logistic Regression had the highest prespecified development validation score for each task. Held-out results showed strong source-label separation for heart and diabetes but a substantial false-positive burden for the rare stroke outcome. These findings concern retrospective source labels and do not establish clinical diagnostic performance.”
