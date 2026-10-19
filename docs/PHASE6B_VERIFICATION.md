# Phase VI-B verification

Date: 2026-10-19, Intel macOS, Node 22.16.0, npm 10.9.2, Angular CLI 20.3.4. Phase VI-B implements only the Dark Research Workspace.

## Executed checks

| Check | Result |
| --- | --- |
| `cd frontend && npm run build` | PASS; production initial bundle 322.36 kB raw / 91.12 kB estimated transfer; seven lazy page chunks; no build warnings after budget adjustment. |
| `cd frontend && ./node_modules/.bin/tsc --noEmit -p tsconfig.app.json` | PASS. |
| `cd frontend && npm test -- --watch=false` | PASS: 8 test files, 13 tests with Angular's experimental jsdom-backed Vitest builder. |
| `.venv/bin/python -m pytest -q` | PASS: 87 passed, 3 Docker-dependent tests skipped, 1 Starlette deprecation warning. |
| Angular proxy / FastAPI smoke | PASS: `GET /health`, `/datasets`, heart analytics charts, heart model comparison, heart prediction schema, `/bigdata/status`, `/reports` returned HTTP 200 through port 4200. |
| Angular route/static HTTP smoke | PASS: all seven deep links served the Angular index; a copied Phase II PNG and fictional JSON fixture returned HTTP 200 with correct content types. This checks routing/asset delivery, not page rendering. |
| Fictional heart prediction via proxy | PASS: saved Logistic Regression returned class 0, model score 0.4453247126343259, threshold 0.5 and local score changes. These are research-only model outputs for `examples/heart_case.json`, not patient data. |
| Copied artifact SHA-256 equality | PASS: all 31 Phase II figure PNGs and all three fictional case JSON files exactly match their repository sources. |
| Dependency audit | `npm uninstall lucide-angular --offline` reported 0 vulnerabilities afterward. No unsupported icon dependency remains. |

The current `GET /bigdata/status` reports MongoDB, HDFS and YARN `UNAVAILABLE`. Independently checked saved MapReduce evidence is `READY`, final state `SUCCEEDED`, total 53,346 synthetic encounters, run `20261018T211007Z`. The UI presents this as historical evidence rather than live job activity.

## Browser and responsive verification

Browser visual inspection could not be performed: the computer-use browser inventory returned no available browsers, and installed ChromeHeadless could not launch for Karma (a direct Chrome headless process exited 137). The production build, jsdom component tests and live proxy checks do not establish pixel-level rendering, console cleanliness, viewport behavior, or chart canvas interactions. No screenshots were captured; `docs/screenshots/` is intentionally empty. Desktop, tablet and mobile layouts have CSS breakpoints at 1100 and 700 px, but must be reviewed in a browser before visual acceptance.

## Implemented interactions and limits

Sidebar collapse, responsive drawer markup, task/dataset selectors, current-page record search/sort, exact supported-field server filtering and 25-row server pagination, chart tooltips, PNG export, fullscreen, zoom reset, prediction form validation, real saved-model submission, debounced what-if re-prediction, model sorting, matrix/model switching, report opening, and nonoverlapping infrastructure polling are implemented. Angular component tests cover shell, routes, API layer, prediction validation, chart data mapping and infrastructure refresh cleanup. No browser-driven interaction test ran.

Several requested views remain limited by existing backend contracts: complete numeric descriptive statistics and arbitrary histogram bins, true filtered Phase II analyses, HDFS capacity/used/remaining, current YARN jobs, and storage statistics are not exposed. The UI gives an explicit unavailable explanation or shows approved static Phase II figures. The API does not provide a report-file download endpoint. Source data is not fabricated to fill these gaps. Before full VI-B acceptance, perform browser QA, capture screenshots at desktop/tablet/mobile widths, inspect console/network failures, and review those API-backed feature gaps.
