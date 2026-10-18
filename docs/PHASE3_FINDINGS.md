# Phase III presentation findings

## Dataset overview

| Source | Prepared rows | Unit | Primary caution |
|---|---:|---|---|
| UCI Cleveland heart | 303 | source record | 164 no recorded disease, 139 recorded disease; original `num` retained in Phase I |
| UCI early diabetes | 520 | questionnaire row | 269 exact repeated profiles retained; participant identity unknown |
| Healthcare stroke | 5,110 | source record | 249 stroke-positive (4.87%); 201 BMI missing, 1,544 smoking responses unavailable |
| Synthea patients | 1,171 | simulated patient | synthetic identities; not clinical validation |
| Synthea encounters | 53,346 | simulated encounter | repeated visits valid; counts are visit-weighted |

The class distributions, missingness and duplication figures come from `powerbi/exports/v1/` and match Phase I/II evidence. Stroke class imbalance means raw record counts can hide the positive class; within-group shares and explicit denominators are shown. `Unknown` smoking responses are missing rather than a real smoking category. A pie chart is used only for the Cleveland two-part outcome share; cross-dataset parts are not placed in one pie.

The three primary research outcomes are carried through from Phase II without recalculation:

| Test | Statistic and p | Effect and 95% CI | Interpretation |
|---|---|---|---|
| H1 heart age | Welch t = 4.0303, p = 7.0614e-05 | Positive minus negative mean = 4.0405 years; CI [2.0677, 6.0134]; Hedges g = 0.4567 | Recorded heart disease group is older on average in this sample; association is not causal. |
| H2 hypertension/stroke | χ²(1) = 83.5965, p = 6.0681e-20 | Odds ratio = 3.6976; CI [2.7440, 4.9825] | Hypertension and stroke status are associated in these source records. |
| H3 glucose/stroke | Welch t = 6.9824, p = 2.4014e-11 | Positive minus negative mean = 27.7492 source units; CI [19.9237, 35.5747]; Hedges g = 0.6180 | Recorded stroke group has higher mean glucose in this sample; unit was not specified by source. |

These are statistical associations from observational, imperfectly documented datasets. They do not establish clinical utility, causation or population incidence. See [Phase II findings](PHASE2_FINDINGS.md) for assumptions, sensitivity checks and practical-significance discussion. Power BI rendering remains unverified, so the presentation findings above are verified aggregate/report outputs rather than observations from Desktop or Service.
