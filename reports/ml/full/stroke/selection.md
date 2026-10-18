# Stroke model-selection report

**Research-only; not clinically validated.** Dataset checksum: `8031625058cfddb391e93633d50b9519775d796c7ad2e1000c813c359be9f1ed`. Split checksum: `76092b3c04ece2503acd83de6d558c5356c9593ff18455f389128e3faf4950fb`.

Selection rule, fixed before test inspection: maximize development five-fold **average_precision**; tie by alphabetical algorithm name. Average precision evaluates positive-case ranking under the observed rare-outcome prevalence; error tradeoffs are reported at a development-only F2 threshold.

Selected **logistic_regression**: CV mean 0.1945, fold SD 0.0436; parameters `{"model__C": 0.3, "model__class_weight": null}`. Threshold 0.0698. Held-out n=1022 (50 positive, 972 negative): accuracy 0.7945, precision 0.1667, recall 0.8000, F1 0.2759, balanced accuracy 0.7971, ROC-AUC 0.8403, average precision 0.2632. False positives 200; false negatives 10.

All four required algorithms and the dummy baseline are in `reports/tables/ml/stroke_comparison.csv`. This test score was **not** used for selection. False negatives may miss recorded outcomes; false positives may create unnecessary follow-up in a real setting, but no clinical use is supported. Cohort origin, sample size, missingness, repeated profiles and calibration limit generalization. Feature importance is descriptive, not causal.
