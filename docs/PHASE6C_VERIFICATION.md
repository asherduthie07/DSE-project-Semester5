# Phase VI-C verification and acceptance

Date: 2026-10-20. Scope: only the existing seven-page Angular research workspace. The source datasets, prepared tables, backend, selected model artifacts, thresholds, evaluation reports and Phase V persistent state were not modified.

## Executed checks

| Command | Actual result |
| --- | --- |
| `cd frontend && npm test -- --watch=false` | PASS: 9 files, 28 tests. Baseline was 8 files, 13 tests. One jsdom Canvas warning is emitted because jsdom has no native Canvas; the browser integration suite covers real Canvas. |
| `cd frontend && npm run build` | PASS: initial 344.40 kB raw / 97.48 kB estimated transfer; ECharts lazy chunk 682.14 kB raw / 193.02 kB transfer, Three renderer lazy chunk 582.15 kB raw / 120.04 kB transfer. No production budget warning. |
| `.venv/bin/python -m pytest -q` | PASS: 87 passed, 3 Docker-dependent skipped, one existing Starlette deprecation warning. |
| `cd frontend && npm run test:e2e` | PASS: 9 live Chromium tests, 28 route/width screenshots plus interaction screenshots. Tested live API on localhost. |
| `cd frontend && npm audit --omit=dev --json` | PASS: zero production dependency advisories. Full audit reports seven development-tool advisories (Angular build/Karma/Vitest and transitives); available automatic fixes require major upgrades, outside the visual integration scope. |

The frontend and backend were started with these exact commands: `.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log` and `cd frontend && npm start -- --host 127.0.0.1`. The browser was installed using `cd frontend && npx playwright install chromium`. New packages were installed using `npm install three`, `npm install --save-dev @types/three`, `npm install --save-dev @playwright/test`, and `npm install --save-dev @axe-core/playwright`. Image fingerprints were measured with `shasum -a 256 frontend/background-image/*.jpg`; dimensions/formats with `file` and `sips -g pixelWidth -g pixelHeight`.

## Acceptance matrix

| Requested item | Status | Evidence or limit |
| --- | --- | --- |
| Main image used by default | PASS | Asset mapping, root layer, browser screenshot |
| Reference informs holographic graph style | PASS | Floating panel/edge style inspected; separate code-generated particle wave |
| Background visible throughout application | PASS | Seven routes and 28 viewport screenshots |
| Seven pages use transparent holographic components | PASS | Shared glass styling and live route screenshots |
| Dynamic palette matches selected background | PASS | Canvas quantization tests and live preset/browser token change |
| Background Studio works | PASS | Local upload, preset, sliders, reset, keyboard dialog tests |
| Reusable WebGL/3D system exists | PASS | Lazy Three renderer, single scene per studio, cleanup test |
| Real 3D scatter plots work | PASS | Heart/stroke data, camera screenshot comparison, measured axes |
| Meaningful surfaces/ridgelines work | PASS | Gaussian KDE unit tests, Synthea monthly browser view, outcome histogram reconciliation |
| Particle-wave visuals work | PASS | Decorative hero browser screenshot and pause test |
| 3D chart camera interactions work | PASS | Rotation, zoom, reset and fullscreen controls; rotation screenshot difference. Trackpad pan and fit across every geometry type were not individually tested. |
| Holographic 2D charts remain statistically correct | PASS | Existing ECharts curves/tables preserved; pure theming test confirms numerical values unchanged |
| 3D/2D visualization modes work | PASS | Browser switch and forced WebGL fallback |
| ML Laboratory fully functional | PASS | All three tasks matched live selected-model/matrix API; four required algorithms visible; existing ROC/PR/CV/importance views retained |
| Prediction Lab uses actual saved models | PASS | Live fictional heart POST result/class/score, threshold/model/version from API |
| Big Data Monitor reports actual statuses | PASS | Browser/API comparison; optional MongoDB/HDFS/YARN currently unavailable |
| Historical research data not presented as live | PASS | Saved job evidence and conceptual topology labeled; no invented activity |
| Interactive charts adapt to background palette | PASS | ECharts theme mapping test, Three palette binding and browser preset switch; immutable saved PNGs retain source colors |
| Application remains responsive | PASS | Route/interaction sweep with no critical errors, lazy chunks, measured browser timing. Native Intel GPU throughput remains NOT TESTED. |
| Fallbacks and accessibility work | PASS | Forced WebGL failure, precision table, contrast tests, keyboard/mobile/axe checks. Manual screen-reader testing NOT TESTED. |
| Angular production build passes | PASS | Build above |
| Frontend tests pass | PASS | 28/28 above |
| Existing backend tests pass | PASS | 87 passed, 3 skipped above |
| Real browser inspection completed where possible | PASS | Chromium screenshots and inspected representative pages; native Safari/Windows NOT TESTED |
| Important changes documented | PASS | This file and five named VI-C architecture/design/studio/mapping/verification files; PROJECT_STATUS updated |
| Production rights for supplied image | BLOCKED | Owner source/license or permission record not supplied |
| Native Intel GPU and long-run memory acceptance | NOT TESTED | Bundled Chromium used SwiftShader software WebGL; no native Intel GPU benchmark or long-session profile |
| Safari, Windows and manual screen-reader acceptance | NOT TESTED | Those environments and a human assistive-technology review were not available |

## Remaining Phase VI-C integration issues

The API has no arbitrary prepared-feature summary endpoint, live HDFS capacity/current YARN job list, or patient-specific timestamp projection. The UI uses the verified aggregates that do exist and labels these limits. Static approved Phase II figures remain unchanged, including their fixed colors. The main 735×411 JPEG needs a verified redistribution license and, for high-resolution screens, a higher-resolution authorized source if the owner wants a crisp production background. Native Intel GPU, long-run memory, Safari/Windows and manual screen-reader acceptance are open. The full npm audit's seven development-tool advisories have not been addressed by a potentially breaking Angular/Vitest upgrade.
