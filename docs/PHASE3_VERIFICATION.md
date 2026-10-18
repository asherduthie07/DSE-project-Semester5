# Phase III verification record — 2026-10-18

## Scope and environment

Only Phase III was changed. Existing Phase I/II datasets, analysis code and figures were preserved. Host: macOS Darwin 24.5.0, Intel x86_64; Python 3.13.2; Node 22.16.0; Java 17.0.14. Windows PowerShell, Power BI Desktop and an authenticated Power BI Service workspace were unavailable on this machine. Headless Chrome was attempted for visual browser QA and exited 137 without a rendered page; the local preview therefore has HTTP and JavaScript data-wiring evidence, not full visual browser evidence.

The original test suite passed before edits: **33 passed**. After edits, Phase III tests: **13 passed in 6.46s**; complete suite: **46 passed in 9.27s**. `python scripts/verify_phase1_outputs.py` returned **PASS, no errors** including four unchanged raw archive checksums and five processed output contracts. `pip check` returned **No broken requirements found**. No model training, Angular, FastAPI, MongoDB or Hadoop work was started.

## Exact execution commands and observed results

Commands were executed from the repository root unless an absolute path is shown:

| Command | Observed result |
|---|---|
| `.venv/bin/python -m pytest -q` before changes | 33 passed |
| `java -jar /private/tmp/mediscope-synthea-v3.4.0.jar -s 424242 -cs 424242 -p 10 -r 20240101 -e 20240101 --exporter.clinical_note.export=true --exporter.fhir.export=false --exporter.hospital.fhir.export=false --exporter.practitioner.fhir.export=false --exporter.baseDirectory=/private/tmp/mediscope_notes Massachusetts` | Exit 0; ten `.txt` clinical notes in separate synthetic cohort |
| `.venv/bin/python scripts/regenerate_powerbi_exports.py --notes-dir /private/tmp/mediscope_notes/notes` | Built 19 aggregate CSVs; no note text or patient IDs committed |
| `.venv/bin/python scripts/generate_powerbi_project.py` | Generated six PBIR pages, 32 TMDL tables/views |
| `.venv/bin/python scripts/verify_powerbi_exports.py` | PASS, 19 files, no source archives required |
| `.venv/bin/python scripts/verify_powerbi_project.py` | PASS static; six pages, 32 tables, 29 visuals; Desktop NOT TESTED |
| `MPLCONFIGDIR=/private/tmp/mediscope-mpl .venv/bin/python scripts/generate_phase3_figures.py` | Five PNG/SVG pairs generated; sixth pair is note cloud |
| `.venv/bin/python scripts/generate_phase3_tables.py` | Five report tables generated |
| `shasum -a 256 reports/figures/phase3/*.png reports/figures/phase3/*.svg` before/after a second figure run; `diff -u ...` | No differences: byte-identical 12 figures |
| `node --check dashboard/app.js` | Exit 0 |
| `node scripts/smoke_dashboard_js.js` | PASS; overview 3 charts, heart 4, diabetes 3, stroke 6, hospital 4, quality 2 |
| `python3 -m dashboard.app --check` and `bash scripts/run_dashboard_macos.sh --check` | PASS, 19 exports and bundled Plotly.js hash |
| `python3 -m dashboard.app --host 127.0.0.1 --port 8766` with `curl -fsS` GETs | Home, outcomes JSON and note-cloud PNG each returned HTTP 200; server stopped |
| `MPLCONFIGDIR=/private/tmp/mediscope-mpl .venv/bin/python -m pytest tests/test_phase3.py -q` | 13 passed in 6.46s |
| `MPLCONFIGDIR=/private/tmp/mediscope-mpl .venv/bin/python -m pytest -q` | 46 passed in 9.27s |
| `.venv/bin/python scripts/verify_phase1_outputs.py` | PASS, zero errors, zero orphan encounters |
| `.venv/bin/python -m pip check` | No broken requirements |
| Installed Chrome `--headless=new ... --dump-dom http://127.0.0.1:8765/` | Exit 137; visual browser runtime **NOT TESTED** |

Static Microsoft schema validation used temporary `jsonschema` (not a project runtime dependency) and Microsoft's public PBIP/PBIR/PBISM JSON schemas. **38 report JSON files and three project descriptors had zero schema errors.** This checks syntax and published structure only; it cannot prove TMDL import, Desktop chart rendering, theme behavior or Service upload. The one-time schema fetch required network access. The Windows script was not executable on this Mac; no Windows result is claimed.

## Source and aggregate statistics

| Dataset/table | Rows | Outcome or unit | Missing/duplication note |
|---|---:|---|---|
| Cleveland | 303 | 164 binary negative, 139 positive | Six source missing cells; 0 duplicate rows |
| Early diabetes | 520 | 200 Negative, 320 Positive | 269 exact repeated profiles retained |
| Stroke | 5,110 | 4,861 negative, 249 positive | BMI 201 missing; smoking unavailable 1,544 |
| Synthea patients | 1,171 | distinct simulated people | identity fields excluded from exports |
| Synthea encounters | 53,346 | simulated visits | zero orphan encounters; repeated visits valid |

Nineteen portable CSVs are in `powerbi/exports/v1/`, with a checksum/schema/row-count manifest. The note term export has 513 displayed terms from ten separate seeded clinical notes; term aggregation does not imply any link to the existing Synthea cohort. Five analytic report tables plus the artifact inventory are in `reports/tables/phase3/`. The three hypothesis rows exactly match Phase II CSV values within round-trip floating-point precision; see [findings](PHASE3_FINDINGS.md) and Phase II methodology for test assumptions.

The complete created/modified file list, including all generated PBIR visual JSON and TMDL table files, is [artifact_inventory.csv](../reports/tables/phase3/artifact_inventory.csv). Its own hash is marked `self` to avoid a recursive checksum.

## Figure review

All **31** existing `reports/figures/eda/*.png` were opened in four contact sheets and checked for nonempty dimensions, data-grounded titles, source labels, units/denominators, captions and legibility. They remain unchanged. The compact heatmap axis labels/captions, dense Synthea monthly timeline and long-tailed encounters-per-patient axis were flagged as readability limitations; none was interpreted as an invalid statistic. Larger Phase III heatmap, within-group stroke histogram, aggregate box plot, heart pie and symptom frequency chart were generated to improve report use. The Phase III box whiskers show observed min/max by design. All figures are research-only, and correlation is not causation.

## Requirement decision matrix

| Phase III requirement | Entry point / evidence | Decision |
|---|---|---|
| Histograms | `mediscope/visualization/figures.py`; stroke age PNG/SVG; Phase II histograms | **PASS** |
| Box plots | Same module; stroke glucose PNG/SVG; Phase II box plots | **PASS** |
| Correlation heatmaps | Same module; heart Pearson PNG/SVG; Phase II matrices | **PASS** |
| Pie charts | Same module; Cleveland two-class part-to-whole PNG/SVG; local Plotly pie | **PASS** |
| Word cloud from authentic synthetic notes | Official Synthea v3.4.0 generation record; `notes.py`; note cloud and term table | **PASS** |
| Portable Power BI inputs | 19 aggregate CSVs, manifest, checksum/schema/row tests; fresh-clone test without raw files | **PASS** |
| Source-controlled PBIP | PBIP/PBIR/TMDL, six page definitions, 32 tables/views, 29 visuals; static schema and cross-reference checks | **PASS — static source only** |
| Actual six-page Power BI dashboard | Requires Desktop import, refresh, chart/filter/theme review | **BLOCKED** |
| Windows one-command setup automation | `scripts/setup_powerbi_windows.ps1`; source inspection only | **NOT TESTED on Windows** |
| Windows Desktop runtime verification | [Windows checklist](POWERBI_WINDOWS_SETUP.md) | **BLOCKED** |
| PBIX/PBIT through supported workflow | No Desktop session; no PBIX/PBIT file generated | **BLOCKED** |
| macOS Power BI Service workflow documented | [Service guide](POWERBI_MACOS_SETUP.md) and official links | **PASS (documentation)** |
| macOS Service upload/view | Requires verified PBIX, eligible account/workspace | **BLOCKED** |
| Cross-platform local dashboard | Six sections, bundled JS/data, macOS HTTP and Node data-wiring checks | **PASS on macOS data path; Windows runtime and visual browser QA NOT TESTED** |
| No mandatory raw-file dependency for viewing | Fresh-clone test and `--check` | **PASS** |
| Existing Phase I/II regression tests | Full suite 46 passed; independent Phase I verifier PASS | **PASS** |
| Documentation/reproducibility evidence | This record, methods, findings, run guides, manifests, deterministic figures | **PASS** |

## Remaining work before academic Power BI acceptance

1. Execute the Windows Desktop checklist, repair any import/render/slicer/theme issues found, and record screenshots and refresh outcome. Static PBIR validity is insufficient evidence of a working report.
2. Save and reopen a real PBIX with Desktop, record checksum and distribute it via a versioned GitHub Release or Git LFS if its size warrants. Optionally export PBIT from Desktop; no template file is fabricated here.
3. Upload the verified PBIX to Power BI Service from an eligible account/workspace, inspect all six pages and record screenshots. A local CSV path cannot refresh in the Service without a supported cloud source or gateway.
4. Perform visual browser QA of the local preview on a Mac and Windows. The Mac HTTP and Node checks support its data wiring, but Chrome headless could not render in this environment.
5. Review PBIR page-level slicer behavior in Desktop. Some outcome slicers currently bind one disease outcome table and may not cross-filter other scoped aggregate views. Add relationships or page controls if broader coordinated filtering is required.
6. Apply and verify the source theme in Desktop; the palette file exists but theme registration/rendering is unverified.

No result above claims that an actual Power BI Desktop report or Service dashboard was viewed.
