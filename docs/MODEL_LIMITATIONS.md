# Phase IV model limitations

These are research and teaching classifiers. None is clinically validated, externally validated, calibrated for patient counseling, or suitable for medical advice.

- The Cleveland sample has 303 rows; its 61-row holdout yields wide unreported performance uncertainty. The original ordinal `num` is a direct source of the binary target and is excluded from predictors.
- The early-stage diabetes symptom survey has 520 rows but only 251 distinct predictor profiles and no participant identifiers. The group-disjoint split avoids profile leakage, yet cannot establish that profiles correspond to independent people. Deduplication sensitivity uses development profiles only and is not a new prospective validation.
- Stroke has 249 positive labels among 5,110 rows. The 1,022-row holdout has only 50 positives. High overall accuracy can coexist with zero positive recall. The dataset's collection context and patient representativeness are unverified. `Unknown` smoking responses are missing and imputed within folds; 201 BMI values are missing.
- All outcomes are source labels, not independently adjudicated diagnoses. Source population, sampling, outcome timing and deployment prevalence are uncertain. No external cohort was tested.
- Hyperparameter grids are intentionally modest for an Intel MacBook. Model selection by development CV is sensitive to fold variation. The held-out test is evaluated once per frozen candidate; comparisons of test scores must not be used to reselect a model.
- Stroke class weights and a development-only threshold were explored, without a sampler. Sampling-method sensitivity and external calibration remain open. The stroke threshold's OOF precision floor of 0.15 is a research operating rule, not a clinical tradeoff.
- Calibration curves and Brier scores are descriptive. They do not turn model scores into clinical disease probabilities, especially for small heart/diabetes samples and rare stroke positives.
- Permutation importance measures score sensitivity on one development validation fold and can understate correlated features. Tree impurity importance is biased toward features with more split opportunities. Logistic coefficients refer to transformed and scaled/encoded columns. Local one-at-a-time changes are nonadditive, may represent implausible feature combinations and do not establish causality.
- SHAP was not run because it would add a heavy optional dependency and is unnecessary to establish the required global and local explanation baseline. Model artifact checksums detect accidental alteration; they do not make untrusted pickle/joblib safe to load.
- Phase III Power BI Desktop runtime, PBIX export and Service browser upload remain separate blocked gates. Phase IV did not change those deliverables.
