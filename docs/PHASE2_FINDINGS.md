# Phase II findings: report draft

**Scope:** exploratory analysis of the five Phase I prepared tables on 2026-10-18. These are observations from the current checksummed local archives, not clinical evidence or causal estimates. Exact counts, denominators, p-values and figures are in `reports/eda/` and `reports/tables/eda/`.

## Dataset overview and descriptive patterns

| Source and analysis unit | Prepared size | Outcome distribution | Missingness and dependence |
|---|---:|---|---|
| UCI Cleveland heart, record | 303 × 15 | `heart_disease_binary`: 164 absent, 139 present (45.9% present); original `num` retained | `ca` 4 and `thal` 2 missing; no exact rows repeated; historical nonrandom sample |
| UCI early diabetes, questionnaire row | 520 × 17 | 200 Negative, 320 Positive (61.5% Positive) | 269 exact rows duplicate another profile; no participant ID to verify independence |
| Kaggle stroke, record | 5,110 × 12 | 4,861 negative, 249 positive (4.87% positive) | BMI missing 201; source `Unknown` smoking recoded to missing 1,544; source patient origin unverified |
| Synthea patients, simulated person | 1,171 × 25 | No disease target | Optional demographic fields are frequently blank; simulated, not observed people |
| Synthea encounters, simulated visit | 53,346 × 15 | No disease target | 39,569 missing reason codes/descriptions; 0 orphan visits; multiple visits per person valid |

Heart-positive records had mean age **56.63** years versus **52.59** in the negative group. Mean maximum heart rate was **139.26** versus **158.38**, and mean ST depression (`oldpeak`) was **1.57** versus **0.59**, respectively. These are unadjusted group descriptions; they do not isolate one feature's effect.

In the diabetes questionnaire, mean age was **49.07** for Positive and **46.36** for Negative rows. The recorded polyuria Yes frequency was **75.94%** among Positive rows versus **7.50%** among Negative rows; polydipsia was **70.31%** versus **4.00%**. Identical rows may amplify descriptive and inferential patterns. Counting unique profiles yields **251 distinct response patterns**, but treating those as unique people would be unjustified, so the main tables retain all 520 rows.

Stroke-positive records averaged **67.73** years versus **41.97** years among negative records. Mean BMI was **30.47** among 209 positive records with BMI and **28.82** among 4,700 negative records with BMI. The 201 missing BMI values have different target-group denominators. Stroke-positive proportions increased from **2/856** for ages under 18 to **40/186** for ages 80 and above in the observed table; this is a sample pattern, not an age-specific population incidence rate. The severe 4.87% outcome imbalance makes plain accuracy an inadequate later modeling metric; Phase II trains no model.

Synthea has **1,171 distinct simulated patients** and **53,346 distinct simulated encounters**, averaging **45.56** encounters per patient (median **27**). There are no patients with zero listed encounters in these files and no orphan encounters. Age at encounter was valid for all 53,346 visits; the **encounter-weighted** mean was **43.85** years. Wellness (**19,106**) and ambulatory (**18,936**) were the largest encounter classes. Valid start dates permit monthly encounter counts, and 13,777 encounters have nonmissing reason codes. None of these figures can be read as real clinical incidence.

## Correlation and association findings

Among registered continuous heart features, the strongest displayed pair was Spearman `thalach` versus `oldpeak`, **ρ = −0.432** (n=303). Point-biserial correlations with binary outcome included `oldpeak` **r = 0.425** and `thalach` **r = −0.417** (n=303). These are exploratory, unadjusted associations.

For diabetes, the larger categorical effect-size estimates against class included polyuria **Cramér V = 0.666** and polydipsia **V = 0.649** (n=520). The age versus Positive-class point-biserial coefficient was **r = 0.109** (n=520), using an analysis-only Positive=1 indicator. Repeated profiles and selection bias restrict inference. With only one registered continuous variable (`Age`), no numeric pairwise heatmap is meaningful.

For stroke, Spearman age versus BMI was **ρ = 0.376** using 4,909 complete pairs; Pearson age versus BMI was **r = 0.333**. Point-biserial stroke versus age was **r = 0.245** (n=5,110). Smoking-status association analyses omit the 1,544 unavailable responses, while frequency tables show them explicitly. Chi-square expected-cell flags and within-table Benjamini–Hochberg adjusted exploratory p-values are in the CSV tables. Synthea cost variables have near-perfect correlation in this sample, likely reflecting how simulated claims were generated; no causal or clinical interpretation is warranted. Latitude/longitude and all IDs are excluded from correlation matrices.

## Preregistered hypothesis tests

All tests were specified before inspecting Phase II results. Alpha was 0.05. Confidence intervals are 95%. Tests are two-sided. The H1/H3 confidence intervals and Hedges g compare positive minus negative groups. H2's odds ratio compares hypertension versus no hypertension.

| Question | Data and primary method | Statistic and p-value | Effect size and 95% CI | Interpretation |
|---|---|---|---|---|
| H1: equal mean age by heart status? | Heart present n=139, mean 56.626, SD 7.938; absent n=164, mean 52.585, SD 9.512. Welch t | t=4.030, df=300.934, p=7.061×10⁻⁵ | Mean difference **4.041 years**, CI **[2.068, 6.013]**; Hedges g **0.457** | Reject equal means in this sample. A roughly four-year contrast may matter descriptively, but recruitment and confounding prevent a causal or population claim. |
| H2: independent hypertension and stroke? | Hypertension: 66 stroke / 432 no stroke; no hypertension: 183 stroke / 4,429 no stroke. All expected cells ≥5; Pearson χ² | χ²=83.596, df=1, p=6.068×10⁻²⁰ | OR **3.698**, approximate CI **[2.744, 4.982]**; observed stroke fractions **13.25%** vs **3.97%** (difference **9.29 percentage points**) | Reject independence in this table. The risk difference describes sample magnitude; causation or temporal order cannot be inferred. |
| H3: equal mean glucose by stroke status? | Positive n=249, mean 132.545, SD 61.921; negative n=4,861, mean 104.796, SD 43.846. Welch t | t=6.982, df=260.894, p=2.401×10⁻¹¹ | Mean difference **27.749 source-scale units**, CI **[19.924, 35.575]**; Hedges g **0.618** | Reject equal means in this sample. The source unit is not verified in the registry; practical/clinical interpretation requires measurement provenance and context. |

The 10% trimmed Welch sensitivity p-values were **2.297×10⁻⁵** for H1 and **8.264×10⁻¹¹** for H3. They point in the same direction as the primary tests, but do not fix nonrandom sampling, duplicate-independence concerns or confounding. The H2 chi-square minimum expected cell and phi are recorded in the JSON and CSV. Even a conservative 0.05/3 threshold would not change these three observed decisions; that is a sensitivity observation, not a retroactive protocol change.

## Limitations and report use

The Cleveland dataset is small and historical. Diabetes has repeated profiles without IDs, so independence cannot be verified. Stroke collection provenance, measurement units, and sampling frame are unclear; smoking history is unavailable for 1,544 rows and BMI for 201. Synthea is simulated and repeated encounter rows are expected. All findings are unadjusted, mostly cross-sectional descriptions; **association does not prove causation**. The analyses cannot support clinical decision-making.

For a university report, use the outcome-frequency tables, grouped numeric summaries, three hypothesis rows, correlation matrices, category association tables, the diabetes symptom chart, stroke age-group chart, heart age boxplot, stroke glucose boxplot, and Synthea encounter trends. Cite the original source URLs from `data/metadata/datasets.json` and explain the local archive provenance caveats. The full Phase III dashboard and predictive experiments remain outside Phase II.
