# Phase IV model comparison

Full five-fold experiments, random seed 42. The table reports development cross-validation (CV) selection score and untouched test metrics. Every candidate's test metrics were evaluated after hyperparameter, threshold and final model selection had been frozen. The chosen model is the highest **development CV** score, not the highest test score.

| Task | Algorithm | CV selection mean | Test accuracy | Precision | Recall | F1 | Test AP | Test confusion matrix `[[TN,FP],[FN,TP]]` |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Heart | Logistic Regression **selected** | F1 .8473 | .8689 | .8125 | .9286 | .8667 | .9683 | `[[27,6],[2,26]]` |
| Heart | Decision Tree | F1 .7284 | .7705 | .7188 | .8214 | .7667 | .8285 | `[[24,9],[5,23]]` |
| Heart | Random Forest | F1 .8031 | .9016 | .8438 | .9643 | .9000 | .9235 | `[[28,5],[1,27]]` |
| Heart | KNN | F1 .8303 | .9016 | .8667 | .9286 | .8966 | .9079 | `[[29,4],[2,26]]` |
| Heart | Dummy prior | F1 .0000 | .5410 | .0000 | .0000 | .0000 | .4590 | `[[33,0],[28,0]]` |
| Diabetes | Logistic Regression **selected** | Balanced accuracy .9348 | .8462 | .8243 | .9531 | .8841 | .9767 | `[[27,13],[3,61]]` |
| Diabetes | Decision Tree | Balanced accuracy .9301 | .8269 | .8485 | .8750 | .8615 | .8723 | `[[30,10],[8,56]]` |
| Diabetes | Random Forest | Balanced accuracy .9298 | .9135 | .8986 | .9688 | .9323 | .9839 | `[[33,7],[2,62]]` |
| Diabetes | KNN | Balanced accuracy .9167 | .8846 | .9194 | .8906 | .9048 | .9634 | `[[35,5],[7,57]]` |
| Diabetes | Dummy prior | Balanced accuracy .5000 | .6154 | .6154 | 1.0000 | .7619 | .6154 | `[[0,40],[0,64]]` |
| Stroke | Logistic Regression **selected** | AP .1945 | .7945 | .1667 | .8000 | .2759 | .2632 | `[[772,200],[10,40]]` |
| Stroke | Decision Tree | AP .1568 | .8141 | .1729 | .7400 | .2803 | .1822 | `[[795,177],[13,37]]` |
| Stroke | Random Forest | AP .1926 | .8170 | .1722 | .7200 | .2780 | .2046 | `[[799,173],[14,36]]` |
| Stroke | KNN | AP .1232 | .9364 | .1429 | .0600 | .0845 | .1117 | `[[954,18],[47,3]]` |
| Stroke | Dummy prior | AP .0487 | .9511 | .0000 | .0000 | .0000 | .0489 | `[[972,0],[50,0]]` |

Heart has 242 development and 61 test rows (28 test positives). Diabetes has 416 development and 104 test rows (64 test positives). Stroke has 4,088 development and 1,022 test rows (50 test positives). These are dataset-specific experiments and are never pooled.

The stroke selected threshold is **0.069818** (rounded) from development-only out-of-fold F2 subject to 0.15 precision. Other tasks use 0.5. Stroke Logistic Regression identified 40 of 50 test positives while flagging 200 of 972 negatives. The dummy model's 95.1% stroke accuracy while identifying no positives illustrates why accuracy alone is unsuitable. The apparent test advantage of Random Forest on heart/diabetes does not overturn the preregistered CV selections.

Machine-readable exact values, CV standard deviations, grids, chosen parameters, ROC/PR points and calibration bins are in `ml/registry.json` and `reports/ml/full/<task>/experiment.json`. Report-ready tables are in `reports/tables/ml/`. Interpretation limitations are in `docs/MODEL_LIMITATIONS.md`.
