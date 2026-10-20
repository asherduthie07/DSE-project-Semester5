# Phase VI-C data-to-geometry mappings

All analytical geometry originates from the existing `/api/v1` API. No model, prepared/raw dataset or saved statistical result is modified. Pure mapping functions live in `visualization/geometry.ts`, with domain adapters alongside them.

| View | Source and encoding | Denominator and limitations |
| --- | --- | --- |
| Heart scatter | `/datasets/uci_cleveland_heart/records`; default X age, Y thalach, Z chol, color heart_disease_binary | All 303 current source records; selected-axis complete cases only. Numeric allowlist also includes trestbps and oldpeak; categorical codes such as cp are excluded. Labels retain source field names; undocumented units are not invented. |
| Stroke scatter | `/datasets/kaggle_stroke/records`; X age, Y bmi, Z avg_glucose_level, color stroke | All 5,110 current records fetched; default complete-case plot has 4,909 points and 201 missing-BMI exclusions. Class filtering changes the displayed denominator. |
| Diabetes columns | `/datasets/uci_early_diabetes/records`; symptom category × recorded class, height count | All 520 records including retained duplicates. Yes/No are categories, not continuous physiological measurements. |
| KDE surface/wireframe | Complete cases of chosen X/Z from heart/stroke; height product Gaussian joint density | 20×20 grid; bandwidth per axis = sample SD × n^(-1/6), floored at range/100 and 1e-6. No boundary correction. Triangles interpolate estimated grid values; not a new observed variable. At least 3 observations required. |
| Outcome ridgelines | Selected continuous X feature grouped by recorded outcome | 12 shared equal-width bins; last bin includes maximum. No smoothing; lines join bin centers. Each observed complete X value contributes to exactly one bin. |
| Synthea encounter columns | `/analytics/synthea_csv/charts`; category index × saved cohort, height saved count | 53,346 encounters, not 1,171 unique patients. Category spacing is arbitrary. |
| Synthea temporal ridges | `/analytics/synthea_csv/distributions?table=monthly_encounters`; calendar month × year, height encounters | Latest ten recorded years, with their actual summed denominator displayed. Missing months are omitted. Lines are a visual connection, not invented monthly observations. |
| Model landscape | `/models/{task}/comparison`; algorithm × evaluation metric, height held-out score | All four compulsory models plus dummy baseline for selected task. Fixed score axis 0–1. Missing metrics omitted, never zero-filled. |
| Development landscape | Same endpoint; algorithm × fold, height saved fold score | Five actual development folds, selection metric labeled. Never used to reorder model selection using held-out scores. |
| Confusion columns | `/models/{task}/confusion-matrices`; predicted class × actual class, height count | Same TN/FP/FN/TP and test denominator as conventional matrix retained below. |
| ROC/PR/importance | Existing saved curves/explanation endpoints through ECharts | ROC and PR stay 2D; PR prevalence reference retained; importance remains association/model explanation, not causality. |
| Prediction ring | `POST /predictions/{task}` response score determines arc angle 2π × score | Actual class, threshold, selected model and version retained. Ring is a score encoding, not clinical certainty. What-if changes make fresh requests; edits/reset/task changes invalidate older requests. |
| Infrastructure topology | `/bigdata/status` plus documented Phase V master/worker relationships | Node positions are conceptual, not measurements. Only service-level reachability is known. Child nodes are explicitly labeled as documented, with individual health unexposed. Failed refresh marks topology stale. Historical job evidence remains separate. |
| Hero wave | Analytic sine/cosine decoration, no API values | Explicitly decorative; no sample size, medical labels or scientific measurements. |

## Paging and state

Disease record requests use the existing 100-row maximum, with at most four requests in flight. Pages are sorted by offset before combining. A 6,000-row guard currently accommodates all three cohorts; if exceeded, the UI explicitly labels the first 6,000 as a nonrandom prefix. A failed page prevents plotting a partial collection. Dataset changes unsubscribe prior loads. Mode switching reuses the same data and selected filters.

The renderer normalizes each numeric axis to [-4,4] for display, retains original values for inspection and tables, and labels bounds. Bar axes begin at zero. Categorical axes use explicit labels and do not imply numeric distance. Precision scatter is an X/Y projection; Z remains in the table. Density precision view is a heatmap. Model/categorical precision views are grouped bars and temporal precision views are lines. Conceptual topology has a conventional point/table alternative.

Hover inspection and click-to-pin use Three.js raycasting against rendered geometry. Tables expose every plotted point in 50-row pages. The conventional existing model table and confusion matrix remain available independently of the spatial view.
