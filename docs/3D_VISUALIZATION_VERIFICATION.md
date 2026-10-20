# Phase VI-C 3D visualization verification

Verified with the running FastAPI + Angular application in bundled Playwright Chromium using SwiftShader software WebGL. No connected computer-use browser was available, so Playwright supplied independent browser automation and actual screenshots. The test suite is `frontend/e2e/` and screenshot evidence is in `docs/screenshots/phase6c/`.

## Visual and interaction evidence

The browser sweep navigated all seven deep links at 1440, 1280, 768 and 390 px. It asserted the persistent `cover` background, absence of horizontal document overflow, expected page headings, 3D canvases where present, and no uncaught JavaScript page errors. Actual full-page PNGs were captured for every route/width combination. Selected images were opened and inspected for the background, transparency, text, chart visibility, layout, 3D depth and form readability. The screenshot file names identify each route and width. The main image is visible behind panels across routes. On very long full-page captures, the fixed background occupies the first viewport in the stitched image; it remains fixed during real scrolling.

The interaction test compared the 3D canvas before and after camera rotation, exercised zoom and reset, switched to precision 2D and back, changed the cohort to stroke, confirmed 5,110 fetched rows and 201 missing-BMI exclusions, displayed the estimated density, then switched to diabetes categorical symptoms. It also confirmed the real heart prediction response of `0.4453247126343259` for the repository's fictional heart example. A forced WebGL failure exposed the precision plot and accessible 50-row table. A separate integration test compared all three model tasks' selected models and confusion-matrix counts against live API responses, and checked all four required algorithms.

The browser test validated actual saved Synthea monthly encounter ridges and live service statuses; it did not equate historical Hadoop job evidence with current YARN activity. Dialog focus/Escape, mobile drawer navigation and an axe WCAG 2 A/AA and 2.1 AA scan passed on mobile Research & Reports with Background Studio open. HTML data tables and precision mode provide non-pointer alternatives. The scene cleanup test observed WebGL context release after route navigation and after switching to 2D. Animation pause produced byte-identical canvas captures across a 200 ms interval. Uploading the supplied reference into Background Studio temporarily produced a local blob URL and a newly extracted palette; the test reset to the main default.

## Browser timing and limits

`browser-timing.json` stores one measured 60-frame requestAnimationFrame sample and JS heap reading. It used software rendering and is **not** a native Intel GPU frame-rate or long-session memory benchmark. No native Intel GPU profile, long-run memory leak assessment, Windows browser run, Safari run or manual screen-reader test was performed. A browser screenshot establishes visual rendering at the captured state, not a guarantee for every dynamic state.

No fabricated science or infrastructure output was needed. Full source axes, exclusions, estimation method, denominators and conceptual/decorative views are documented in `3D_VISUALIZATION_DATA_MAPPING.md`. Two remaining external acceptance conditions are the unknown rights to distribute the supplied main image and a native Intel GPU performance review. The 735×411 main image visibly softens at large display sizes.

## Test commands

From `frontend/`: `npm test -- --watch=false`, `npm run build`, and `npm run test:e2e`. From the project root: `.venv/bin/python -m pytest -q`. Start FastAPI and Angular as described in `HOW_TO_RUN_FRONTEND.md` before the browser test. The browser tests require `npx playwright install chromium` once. The Playwright configuration uses bundled Chromium and SwiftShader; it is reproducible without a globally installed browser.
