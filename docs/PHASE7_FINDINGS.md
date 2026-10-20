# Phase VII findings — measured development data

## Research objective and data

This supplementary study asks how preprocessing affects classifier performance, reliability and explanation rankings. It uses the three original Phase IV **development** partitions only: Cleveland heart 242 rows / 111 positives, early diabetes 416 / 256, and stroke 4,088 / 199 (prevalence 4.87%). The frozen five folds, source/split hashes, configurations and full precision values are in [`reports/phase7/`](../reports/phase7/) and [methodology](PHASE7_METHODOLOGY.md). The Phase IV held-out test findings remain in [Phase IV findings](PHASE4_FINDINGS.md); no Phase VII comparison uses them for configuration choice.

## Preprocessing comparisons

All values below are out-of-fold (OOF) on development rows, using the same selected Phase IV Logistic Regression hyperparameters and frozen thresholds. Fold standard deviations quantify observed variation, not independent-sample confidence intervals.

| Task and configuration | F1 | Balanced accuracy | Average precision | Brier | False positives / negatives |
| --- | ---: | ---: | ---: | ---: | ---: |
| Heart baseline | .8479 | .8610 | .8948 | .1215 | 14 / 19 |
| Heart IQR clipping | .8426 | .8565 | .8947 | .1215 | 14 / 20 |
| Heart MinMax scaling | .8161 | .8298 | .9005 | .1201 | 21 / 20 |
| Heart categorical constant | .8519 | .8648 | .8956 | .1206 | 13 / 19 |
| Diabetes baseline | .9442 | .9348 | .9835 | .0707 | 9 / 19 |
| Diabetes no scaling | .9315 | .9230 | .9830 | .0710 | 9 / 25 |
| Diabetes training-fold deduplication | .9131 | .9008 | .9806 | .0798 | 13 / 30 |
| Stroke baseline | .2480 | .7550 | .1721 | .0428 | 811 / 56 |
| Stroke missing indicators | .2570 | .7602 | .2124 | .0418 | 771 / 56 |
| Stroke `Unknown` smoking explicit | .2467 | .7526 | .1720 | .0428 | 810 / 57 |

All remaining strategies and their exact fold metrics are in [`comparisons.csv`](../reports/phase7/comparisons.csv). Mean imputation made almost no difference in this run. For heart and diabetes, missing indicators left the baseline metrics unchanged. The stroke indicator configuration had higher OOF average precision (.2124 versus .1721), but this is one development-fold sensitivity comparison with fixed Phase IV parameters, not proof of improvement on unseen populations. Diabetes training-fold deduplication reduced OOF balanced accuracy from .9348 to .9008. Since repeated profiles may represent repeated questionnaires or different people, deduplication is a sensitivity study, not a corrected cohort.

## Robustness, thresholds and calibration

Baseline primary-metric fold SD was .0341 for heart F1, .0664 for diabetes balanced accuracy and .0487 for stroke average precision. At the saved threshold, stroke OOF precision was .1499 and recall .7186; the 811 false positives greatly exceed the 143 true positives. This reflects the 4.87% development prevalence and shows why accuracy alone would mislead. Threshold curves and exact error counts are in [`thresholds.csv`](../reports/phase7/thresholds.csv). No new operating point is selected.

Baseline Brier scores were .1215 (heart), .0707 (diabetes) and .0428 (stroke). Five-bin OOF calibration is stored for **every** preprocessing strategy in each task JSON and can be compared in the UI. Stroke baseline had 3 nonempty bins: 3,905 rows with mean score .040 and observed rate .041; 181 rows with mean .261 and observed .210; only 2 rows in the .4–.6 bin, so that last fraction cannot support a conclusion. The diabetes .6–.8 bin had 44 rows, mean score .700 and observed rate .932, suggesting local miscalibration in that band. These are descriptive internal estimates; no probability is clinically calibrated or externally validated.

Missing-feature sensitivity measures the mean absolute change in score when one validation field is replaced with missing and transformed by a model fitted on the other fold rows. On fold 0, the largest changes were heart `ca` .092, diabetes `Polyuria` .087, and stroke `age` .045. This perturbation does not model realistic patterns of missingness or clinical consequences.

## Subgroups and uncertainty

Descriptive OOF results by recorded category include:

| Task / recorded group | n | Positive | Precision | Recall | F1 (95% row-bootstrap percentile interval) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Heart sex code 0 | 77 | 18 | .857 | .667 | .750 [.545, .903] |
| Heart sex code 1 | 165 | 93 | .870 | .860 | .865 [.811, .915] |
| Diabetes Female | 149 | 134 | .978 | .985 | .981 [.960, .996] |
| Diabetes Male | 267 | 122 | .946 | .861 | .901 [.861, .940] |
| Stroke Female | 2,395 | 112 | .139 | .670 | .230 [.187, .274] |
| Stroke Male | 1,692 | 87 | .165 | .782 | .272 [.218, .320] |

The full [`subgroups.csv`](../reports/phase7/subgroups.csv) includes age, stroke residence and smoking categories, denominators, precision/recall Wilson intervals and F1 bootstrap intervals. Heart age ≤40 has 13 rows/5 positives; stroke age ≤40 has only 3 positives and stroke `Other` gender has one negative row. These are flagged small/sparse. The intervals condition on OOF model predictions and do not include training variability; diabetes repeats make row-bootstrap intervals potentially too narrow. Differences may reflect sampling, prevalence, outcome recording or model behavior. They cannot establish fairness or discrimination.

## Explainability stability

Validation-fold permutation importance ranked `ca` and `thal` highly for heart, `Polyuria` and `Gender` for diabetes, and `age` clearly highest for stroke on fold 0. Across five folds, mean pairwise Spearman rank agreement for the selected baseline was only .287 (heart), .551 (diabetes) and .184 (stroke). The selected baseline's mean ranking correlated with decision tree at .64/.71/.58 and KNN at .58/.73/−.04 for heart/diabetes/stroke, respectively. Diabetes deduplicated versus baseline Logistic Regression rank correlation was .51. Full fold-level scores and correlations are in [`importance.csv`](../reports/phase7/importance.csv) and [`importance_stability.csv`](../reports/phase7/importance_stability.csv). These rankings measure predictive score dependence under permutation. They do not identify causal risk factors.

## Discussion and conclusion

Some preprocessing changes barely affected these development predictions, while scaling, stroke missingness indicators and diabetes profile weighting had measurable effects. The effects are task-specific and cannot justify replacing the frozen Phase IV results or selecting a newly deployed configuration without a separately designed validation study. Stroke's rare outcome and false-positive burden, diabetes profile repetition, sparse subgroups, uncertain source sampling and lack of external validation are the main reliability limits. This study provides controlled internal sensitivity evidence, not a clinically usable diagnostic model or a novel scientific discovery.
