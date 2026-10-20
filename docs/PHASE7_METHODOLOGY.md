# Phase VII methodology — development-only research

## Question and scope

How do preprocessing choices change predictive performance, stability and feature rankings for the three previously registered MediScope AI classification tasks? These are supplementary experiments. The Phase IV benchmark, selected models, thresholds and held-out results remain frozen. This work has no clinical validation or claim of diagnostic utility.

The source registry is [`data/metadata/datasets.json`](../data/metadata/datasets.json): [UCI Cleveland](https://archive.ics.uci.edu/dataset/45/heart+disease), [UCI early diabetes](https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction), and [Kaggle stroke](https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset). Archive origin/version limits, terms, checksums and schemas are recorded there. Prepared-file checksums are checked by `load_task`; raw archives and prepared data are never modified here. Synthea is not a Phase VII classifier.

## Fixed design

The runner verifies and reuses `reports/ml/full/{task}/split.json`, including the SHA-256, original development indices and five validation folds. Heart and stroke use stratified folds; diabetes uses predictor-profile group folds. Diabetes profiles are formed without outcomes; each training and validation side remains group-disjoint. Only development rows enter Phase VII fitting, selection comparisons, OOF metrics, threshold curves, subgroup descriptions or permutation importance. The held-out index list is checked for separation and counted, never used to materialize test features or labels in the Phase VII runner.

The selected Phase IV algorithm, tuned hyperparameters and operating threshold are read from `ml/registry.json` and held fixed for each task. All learned imputers, optional IQR bounds, scalers, encoders and estimators are fitted in a new `Pipeline` on each training fold. Validation rows are transformed only after fitting. This design isolates preprocessing impact from hyperparameter retuning. Each task uses the same five saved folds for every strategy. No output here selects a new deployed model.

| Strategy | Change from Phase IV baseline |
| --- | --- |
| `baseline` | Median numeric, most-frequent categorical, preserved extremes, standard scaling for Logistic Regression/KNN and no scaling for trees |
| `mean` | Numeric mean imputation |
| `missing_indicator` | Fold-fitted numeric missingness indicators |
| `iqr_clip` | Fold-fitted 1.5-IQR clipping after numeric imputation |
| `minmax`, `robust`, `no_scaling` | Alternative numeric scaling; unscaled Logistic Regression uses a tighter `liblinear` tolerance (`1e-9`) to stabilize numerical convergence, recorded in each configuration |
| `categorical_constant` | Explicit constant for missing categorical fields; unknown binary codes are handled by existing encoder policy |
| `smoking_explicit` | Stroke only: prepared missing smoking status is supplied as literal `Unknown` before fold-local encoding; baseline treats it as missing |
| `deduplicated` | Diabetes only: retain one raw predictor profile within each **training fold**; never deduplicate validation folds or cross the original holdout boundary |

The deduplication analysis tests sensitivity to repeated predictor profiles, not patient independence; no participant IDs exist. Stroke `Unknown` is a questionnaire response of uncertain meaning, so both treatments are plausible sensitivity choices. Clipping is exploratory because extremes can be genuine observations.

## Evaluation and uncertainty

Each configuration generates one probability per development row through out-of-fold prediction. Saved outputs include F1, balanced accuracy, ROC-AUC, average precision, Brier score, precision, recall, false positives, false negatives, per-fold metrics, mean and sample SD. Stroke interpretation emphasizes average precision, prevalence, recall, precision and false-positive burden. The fixed Phase IV threshold is applied for comparable binary classifications; a development-only threshold sweep is descriptive and does not choose a replacement threshold. Calibration uses five fixed bins of OOF scores, observed positive fractions and Brier score; sparse/empty bins limit inference.

Recorded sex/gender, age bands (≤40, 41–60, >60) and available stroke residence/smoking categories are reported with counts, outcome distribution, precision, recall and F1. Precision and recall have 95% Wilson intervals; F1 has seeded 400-resample row-bootstrap percentile intervals. Groups with fewer than 30 rows or fewer than 10 in either outcome are flagged. The intervals condition on fitted OOF predictions and omit model-training uncertainty; repeated diabetes profiles can make row-level intervals optimistic. These are descriptive evaluations, not discrimination or fairness tests. No unavailable protected attribute is inferred.

Permutation importance uses three seeded repeats on each held-out validation fold, scored with each task's Phase IV selection metric. Feature-ranking stability is summarized by pairwise Spearman correlation across folds and correlation to the selected baseline across strategies/model families. Correlation among predictors, class imbalance and small validation subsets can make rankings unstable. Importance and missing-feature score changes are predictive associations, not causal effects. SHAP was not used because permutation importance directly supports the planned fold/model comparisons without adding another explanation convention.

`reports/phase7/manifest.json` records input raw hashes, saved split hashes, seed, library versions and SHA-256 for every generated artifact. The runner does not write to `data/`, `ml/models/`, Phase IV reports or the Phase IV registry.
Serialized floating-point summaries are rounded to ten decimal places after all metric and decision calculations, to avoid meaningless last-bit differences in output hashes.
The unscaled Logistic Regression sensitivity has measurable sub-microprobability solver variation despite fixed seeds and a tighter stopping rule. Its Brier and calibration summaries are stored to six decimals; no decision or metric computation is performed on rounded probabilities.
