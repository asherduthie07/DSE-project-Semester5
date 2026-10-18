# Phase II verification

**Date:** 2026-10-18. **Scope:** exploratory data analysis only. **Decision:** Phase II implementation and local execution **PASS** for the current verified Phase I inputs. Source provenance and sampling limits remain; no clinical validation is claimed.

## Environment and commands actually executed

Environment: macOS 15.5 (Darwin 24.5.0) on x86_64, Python 3.13.2. Installed: pandas 3.0.6, NumPy 2.5.4, SciPy 1.18.1, Matplotlib 3.11.2, pytest 9.1.1. The EDA extra is declared in `pyproject.toml`; these dependencies were already installed in the Phase I `.venv`. `pip check` found no broken requirements. A matplotlib cache warning appeared only in a direct version-inspection command that imported Matplotlib outside the EDA cache setup; EDA and tests ran without that warning.

Commands run from the project root, including repeated runs during development:

```bash
uname -srm
sw_vers
.venv/bin/python --version
.venv/bin/mediscope eda --help
.venv/bin/mediscope eda --dataset uci_cleveland_heart
.venv/bin/mediscope eda --dataset uci_early_diabetes
.venv/bin/mediscope eda --dataset kaggle_stroke
.venv/bin/mediscope eda --dataset synthea_csv
.venv/bin/mediscope eda --dataset all
.venv/bin/python -m pytest tests/test_phase2_eda.py -q
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_phase1_outputs.py
.venv/bin/python -m pip check
```

One controlled fixture test initially failed because its invented Synthea encounter frame omitted `ENCOUNTERCLASS`, which the real registered schema requires. The fixture was corrected, then the full tests passed; no production check or requirement was weakened. An early diabetes plot had caption overlap; its layout was adjusted and the regenerated image was visually inspected.

An additional Python subprocess check ran `.venv/bin/mediscope eda --dataset all` twice and compared SHA-256 values of every generated EDA JSON, Markdown, CSV and PNG. **88 artifacts compared, 0 changed**, exit 0, no stderr. This check does not claim byte identity across different Matplotlib, font or operating-system versions.

## Actual input and output checks

| Registered dataset | Verified prepared table size | Nonzero missing fields | Outcomes / relationships | EDA tables | Figures |
|---|---:|---|---|---:|---:|
| UCI Cleveland heart | 303 × 15 | `ca` 4, `thal` 2 | Binary target 164/139; original `num` agrees with `num > 0` | 11 | 6 |
| UCI early diabetes | 520 × 17 | None | Negative 200, Positive 320; 269 identical rows retained | 11 | 6 |
| Kaggle stroke | 5,110 × 12 | BMI 201, smoking 1,544 | Negative 4,861, positive 249 | 14 | 10 |
| Synthea simulated patients | 1,171 × 25 | Optional fields; see JSON | 1,171 unique patient IDs | Combined 13 | Combined 9 |
| Synthea simulated encounters | 53,346 × 15 | Reason fields 39,569 each | 53,346 unique encounter IDs; 0 orphans |  |  |

Each EDA input SHA-256 matched its Phase I quality report; each report's raw archive checksum matched the source registry. `scripts/verify_phase1_outputs.py` returned `"status": "PASS"`, `"errors": []`, checking the four raw archives, five prepared tables, targets, row reconciliation and patient links. The EDA command writes only under `reports/`; it did not change Phase I CSVs or ZIPs. Full suite: **33 passed in 5.37s**. Phase II suite: **13 passed in 4.07s**. The existing Phase I suite remains included in the full run.

## Primary test results (exact values in report JSON)

| Hypothesis | Primary method and groups | Test | Effect and 95% CI | Decision at α=0.05 |
|---|---|---|---|---|
| H1 heart age | Welch; disease n=139 versus absent n=164 | t=4.03035, df=300.934, p=7.06144×10⁻⁵ | Mean difference 4.04053 years, CI [2.06768, 6.01339]; Hedges g=0.45669 | Reject H0 |
| H2 hypertension × stroke | Pearson chi-square; hypertensive n=498 versus nonhypertensive n=4,612; all expected cells ≥5 | χ²=83.59647, df=1, p=6.06812×10⁻²⁰ | OR=3.69756, approximate CI [2.74401, 4.98247]; observed risk difference 9.285 percentage points | Reject H0 |
| H3 stroke glucose | Welch; stroke n=249 versus no stroke n=4,861 | t=6.98241, df=260.894, p=2.40144×10⁻¹¹ | Mean difference 27.74923 source-scale units, CI [19.92371, 35.57474]; Hedges g=0.61804 | Reject H0 |

Two-sided 10% trimmed Welch sensitivity p-values: H1 2.29659×10⁻⁵; H3 8.26351×10⁻¹¹. These are sensitivity checks. The findings document discusses practical meaning and limits; none of the tests establishes causation.

## Verification matrix

| Phase II requirement | Implementation entry point | Evidence | Result |
|---|---|---|---|
| Read verified prepared inputs and preserve Phase I | `eda.runner.load_prepared` | SHA/schema/target checks; Phase I verifier PASS | PASS |
| Descriptive shape, types, numerical moments, quantiles, missingness and group summaries | `eda.stats.numeric_summary`; `runner._standard_tables` | `reports/eda/*.json`; `reports/tables/eda/*numeric*.csv`; formula tests | PASS |
| Categorical, outcome and denominator-aware frequencies | `eda.stats.categorical_summary` | `*categorical*.csv`, `*outcome.csv`; controlled denominator test | PASS |
| Pearson, Spearman, point-biserial, matrices and heatmaps | `eda.stats.numeric_associations`; `eda.figures.heatmap` | `*correlations.csv`, `*matrix.csv`, heatmap PNG; selection/constant tests | PASS |
| Chi-square and Cramér V with assumption flags and exploratory correction | `eda.stats.categorical_associations`; `bh_adjust` | `*categorical_associations.csv`; controlled effect/FDR test | PASS |
| H1 Welch, effects, CI and sensitivity | `eda.hypotheses.welch_test` | Heart JSON/Markdown and hypothesis CSV; reference-value test | PASS |
| H2 chi-square/Fisher selection, effect and CI | `eda.hypotheses.hypertension_test` | Stroke JSON/Markdown and hypothesis CSV; dense/sparse 2×2 tests | PASS |
| H3 Welch, effects, CI and sensitivity | `eda.hypotheses.welch_test` | Stroke JSON/Markdown and hypothesis CSV; reference-value test | PASS |
| Heart, diabetes, stroke disease distributions and repeated profiles | `runner._disease_extra` | Dataset-specific CSVs, report facts and figures | PASS |
| Synthetic patient versus encounter analyses, age and trends | `runner.synthea_relationships` | Synthea JSON/CSV/figures; controlled relationship test | PASS |
| High-resolution supporting figures and captions | `eda.figures` | 31 PNGs at 200 dpi; representative images opened and visually checked | PASS |
| CLI, reproducibility, report outputs and teaching notebook | `mediscope.cli.main`, `eda.runner.run_eda` | CLI per dataset/all exit 0; 88 stable artifact hashes; notebook file | PASS |
| Phase II tests and Phase I regression checks | `tests/test_phase2_eda.py`, existing tests, independent verifier | 13 Phase II passed; 33 full passed; verifier PASS | PASS |

## Evidence paths

- Four JSON and four Markdown reports: `reports/eda/`.
- **49 CSV files** including summaries, grouped tables, associations, matrices and primary hypothesis tables: `reports/tables/eda/`.
- **31 PNG files** including distributions, grouped boxplots, category charts, temporal trend and correlation heatmaps: `reports/figures/eda/`.
- Narrative: `docs/PHASE2_METHODOLOGY.md`, `docs/PHASE2_FINDINGS.md`, and `docs/HOW_TO_RUN_PHASE2.md`.
- Teaching notebook: `notebooks/phase2_eda_teaching.ipynb` (created; not executed as an independent validation path).

## Remaining limitations

The existing archives' exact acquisition dates were not recorded. Stroke patient origin and glucose measurement unit remain unverified. Diabetes rows have no participant ID, so identical profiles cannot be interpreted as unique or repeated people. The Cleveland sample is historical and small. Synthea is simulated; repeated encounters are expected. Chi-square exploratory tables with low expected cells have flagged assumptions and should not be interpreted as confirmatory tests. All contrasts are unadjusted and may be confounded. Figure pixel equality across different systems is not guaranteed. No Phase III dashboard or predictive model was implemented.
