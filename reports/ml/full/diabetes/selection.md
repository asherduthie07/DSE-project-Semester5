# Diabetes model-selection report

**Research-only; not clinically validated.** Dataset checksum: `fba09cdce359ada29bf87d8def1a7a32d956f793e2176c9fdcf7d004aba2f76e`. Split checksum: `b9e14a20d31b46fbbcdbc1a6ab93e35cf91e81216ec39411e99b10b5729db6cd`.

Selection rule, fixed before test inspection: maximize development five-fold **balanced_accuracy**; tie by alphabetical algorithm name. Balanced accuracy gives each questionnaire class equal weight while profile grouping protects the split.

Selected **logistic_regression**: CV mean 0.9348, fold SD 0.0594; parameters `{"model__C": 0.3, "model__class_weight": "balanced"}`. Threshold 0.5000. Held-out n=104 (64 positive, 40 negative): accuracy 0.8462, precision 0.8243, recall 0.9531, F1 0.8841, balanced accuracy 0.8141, ROC-AUC 0.9570, average precision 0.9767. False positives 13; false negatives 3.

All four required algorithms and the dummy baseline are in `reports/tables/ml/diabetes_comparison.csv`. This test score was **not** used for selection. False negatives may miss recorded outcomes; false positives may create unnecessary follow-up in a real setting, but no clinical use is supported. Cohort origin, sample size, missingness, repeated profiles and calibration limit generalization. Feature importance is descriptive, not causal.
