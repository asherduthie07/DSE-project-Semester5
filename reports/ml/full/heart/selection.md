# Heart model-selection report

**Research-only; not clinically validated.** Dataset checksum: `36b51c189bc5e5edf72f83152e9243f0b0801494951c73af290c44a68a3a1b53`. Split checksum: `6f758a9456d0319a911509625ae30d8cd462710c4a582a047d7c600da5eb9724`.

Selection rule, fixed before test inspection: maximize development five-fold **f1**; tie by alphabetical algorithm name. F1 balances precision and recall in a small two-class historical sample.

Selected **logistic_regression**: CV mean 0.8473, fold SD 0.0305; parameters `{"model__C": 0.3, "model__class_weight": "balanced"}`. Threshold 0.5000. Held-out n=61 (28 positive, 33 negative): accuracy 0.8689, precision 0.8125, recall 0.9286, F1 0.8667, balanced accuracy 0.8734, ROC-AUC 0.9697, average precision 0.9683. False positives 6; false negatives 2.

All four required algorithms and the dummy baseline are in `reports/tables/ml/heart_comparison.csv`. This test score was **not** used for selection. False negatives may miss recorded outcomes; false positives may create unnecessary follow-up in a real setting, but no clinical use is supported. Cohort origin, sample size, missingness, repeated profiles and calibration limit generalization. Feature importance is descriptive, not causal.
