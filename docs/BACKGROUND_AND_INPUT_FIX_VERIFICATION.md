# Background and input corrections — verification

Date: 2026-10-20. Scope: the existing Phase VI-C Angular research workspace only. No raw or prepared data, model artifact, threshold, registry metric, or backend contract was edited.

## Background diagnosis and correction

The supplied files are `frontend/background-image/main-background-image.jpg` (39,316 bytes, progressive JPEG, 735 × 411) and `reference-image.jpg` (25,589 bytes, JPEG, 455 × 260). The latter remains a style reference, not a bundled default. Before this correction, `angular.json` copied the default JPEG from a source-only `background-image` directory through a custom asset rule; that path was not part of the normal `public/` asset tree. The image could be served in a local development run, so a universal 404 or a z-index defect could **not** be reproduced from the available evidence. Prior Chromium screenshots did show it. However, delivery depended on that separate, previously untracked source asset being present, and the app had no CSS image until Angular initialized. Background Studio stored settings but not the selected bundled preset; failed image decoding left the selected URL in CSS, so a stale/missing selection could leave a blank background.

The unchanged source JPEG is now also copied to `frontend/public/backgrounds/main-background-image.jpg`; Angular's ordinary `public/` copying serves it at `/backgrounds/main-background-image.jpg` in development and production. The custom `angular.json` rule was removed. A CSS fallback shows this URL before app initialization; the persistent fixed root layer remains outside the route outlet with `cover`, no pointer interception and z-index below the shell. Shared panels, header and sidebar use translucent surface colors with backdrop blur, not component opacity. A valid bundled preset is saved locally; stale/unsupported saved URLs and failed preset loads return to the default. Session-only uploads are checked for JPEG/PNG/WebP MIME, nonzero size, maximum 10 MB and browser decode, without remote upload. Palette extraction uses same-origin image decoding and local Canvas sampling. A sampling failure retains a decoded image and applies the readable fallback palette.

## Verified display/value contract

The live prediction schema constrains the options shown by the form. Metadata only changes display text; `<option value>` remains the exact string accepted by the saved model API. Unsupported categories are never added. Numeric measurements retain numeric controls and range checks; nullable values remain null.

| Dataset | Field | UI labels → exact submitted/source values |
| --- | --- | --- |
| Cleveland heart | Recorded Sex | Female → `0`; Male → `1` |
| Cleveland heart | Chest pain type | Typical angina → `1`; atypical angina → `2`; non-anginal pain → `3`; asymptomatic → `4` |
| Cleveland heart | Fasting blood sugar >120 mg/dL, exercise-induced angina | No → `0`; Yes → `1` |
| Cleveland heart | Resting ECG | Normal → `0`; ST–T wave abnormality → `1`; probable/definite left ventricular hypertrophy → `2` |
| Cleveland heart | Peak exercise ST slope | Upsloping → `1`; flat → `2`; downsloping → `3` |
| Cleveland heart | Major vessels shown | 0–3 vessels → corresponding string codes `0`–`3` |
| Cleveland heart | Thalassemia test result | Normal → `3`; fixed defect → `6`; reversible defect → `7` |
| Cleveland heart | Derived recorded outcome | Not recorded as present → `0`; recorded as present → `1` |
| Diabetes | Gender | Female → `Female`; Male → `Male` |
| Diabetes | Polyuria, Polydipsia, sudden weight loss, weakness, Polyphagia, Genital thrush, visual blurring, Itching, Irritability, delayed healing, partial paresis, muscle stiffness, Alopecia, Obesity | No → `No`; Yes → `Yes` for each source questionnaire field |
| Stroke | Gender | Female → `Female`; Male → `Male`; Other → `Other` only if returned by the task schema |
| Stroke | Hypertension and heart-disease history | No → `0`; Yes → `1` |
| Stroke | Ever married | No → `No`; Yes → `Yes` |
| Stroke | Work type | Government job → `Govt_job`; Never worked → `Never_worked`; Private → `Private`; Self-employed → `Self-employed`; Children → `children` |
| Stroke | Residence type | Rural → `Rural`; Urban → `Urban` |
| Stroke | Smoking status | Formerly smoked → `formerly smoked`; Never smoked → `never smoked`; Smokes → `smokes`; missing → `null` |
| Stroke | Recorded outcome | No recorded stroke → `0`; recorded stroke → `1` |
| Synthea patient preview | Gender and marital status | Male → `M`; Female → `F`; Married → `M`; Single → `S` (field-specific mappings) |

Cleveland meanings were checked against the [UCI Heart Disease data dictionary](https://archive.ics.uci.edu/dataset/45/heart+disease), with local accepted codes in `mediscope/schema.py`. Diabetes and stroke category domains are from that verified Phase I schema and the live Phase IV prediction schema. Synthea patient gender/marital codes were checked against the [official Synthea CSV dictionary](https://github.com/synthetichealth/synthea/wiki/CSV-File-Data-Dictionary). The original Cleveland `num` code 1–4 is **not** given an invented severity description. Synthea fields without a verified display dictionary remain as source values. Dataset tables, available filters, chart categories, legends, plot hover groups, model feature-importance labels and prediction explanations use the same presentation vocabulary; approved saved research figures and reports are not rewritten.

## Checks and evidence

Changed files for this correction: `frontend/angular.json`, `frontend/public/backgrounds/main-background-image.jpg`, `frontend/src/holographic.css`, `frontend/src/app/visualization/appearance.service.ts`, `frontend/src/app/visualization/background-studio.ts`, `frontend/src/app/shared/field-metadata.ts`, and the presentation integrations in `pages/{prediction,datasets,analytics,models,overview}.ts` and `visualization/{data-explorer,geometry}.ts`. Tests changed in `frontend/src/app/shared/field-metadata.spec.ts`, `frontend/src/app/visualization/visualization.spec.ts`, `frontend/e2e/{workspace,integration}.spec.ts`. The supplied source files in `frontend/background-image/` were not altered. The original, public and built JPEGs have the identical SHA-256 `3b7def1d14d4c3369be83cfcd2d2722d635c38e8a89e50455e56fcf8005cac17`.

Executed checks:

| Check | Result |
| --- | --- |
| `cd frontend && npm test -- --watch=false` | PASS: 33 tests across 10 files. jsdom emits its expected Canvas-not-implemented warning; real Canvas is exercised in Chromium. |
| `cd frontend && npm run build` | PASS: initial 345.05 kB raw / 97.65 kB estimated transfer. Built JPEG exists at `dist/mediscope-frontend/browser/backgrounds/main-background-image.jpg` with the source SHA-256. |
| `.venv/bin/python -m pytest -q` | PASS: 87 passed, 3 Docker-dependent skipped, one existing Starlette deprecation warning. |
| `curl -fsS -o /dev/null -w '%{http_code} %{content_type} %{size_download}' http://127.0.0.1:4200/backgrounds/main-background-image.jpg` | PASS: `200 image/jpeg 39316`. |
| `cd frontend && npm run test:e2e` | PASS: clean run of 11 tests, including seven routes at 1440/1280/768/390 px, browser console/page-error sweep, background preset/upload/reset, all three prediction fixtures, 3D/2D fallback and accessibility. Earlier test-only assertions were corrected before this clean run. |
| `cd frontend && npx playwright test e2e/integration.spec.ts -g 'default background survives'` | PASS: image response, stale preference recovery, all seven routes, panel translucency, fixed image after scrolling. |
| `cd frontend && npx playwright test e2e/integration.spec.ts -g 'dataset preview and server filters'` | PASS: readable Cleveland, diabetes, stroke and Synthea patient cells; heart Recorded Sex filter displayed “Male” while the server request retained `filter_value=1`. This test was added after the clean full-suite run. |

The browser suite also passed existing background preset/reset, local upload, palette extraction, keyboard/axe, four-width route sweep, 3D/2D and WebGL fallback tests. The actual screenshot evidence includes [default background](screenshots/phase6c/background-fixed.png), [scrolled viewport](screenshots/phase6c/background-scroll.png), [Background Studio](screenshots/phase6c/background-studio.png), and [heart](screenshots/phase6c/readable-heart-prediction.png), [diabetes](screenshots/phase6c/readable-diabetes-prediction.png) and [stroke](screenshots/phase6c/readable-stroke-prediction.png) human-readable prediction forms. The browser console had no uncaught page errors in the route sweep. The screenshots visibly show the background behind panels and the category labels, including after scrolling. Full-page stitched captures render a fixed layer only in the first captured viewport; the separate scrolled screenshot confirms continued viewport coverage.

Prediction equivalence uses the repository's fictional `examples/{heart,diabetes,stroke}_case.json` fixtures. The browser test loaded each fixture into the human-readable Angular controls and compared the outgoing POST `features` object **exactly** with the original JSON. The same fixture was submitted directly to FastAPI; model class and displayed score agreed. Independent `.venv/bin/mediscope ml predict --dataset <task> --input examples/<task>_case.json` commands gave:

| Task | CLI / API / form class | CLI / API score | Saved threshold | Exact category examples in request |
| --- | --- | --- | --- | --- |
| Heart | `0` | `0.4453247126343259` | `0.5` | `sex: "1"`, `fbs: "0"`, `cp: "4"` |
| Diabetes | `1` | `0.9176253132070262` | `0.5` | `Gender: "Female"`, `Polyuria: "Yes"` |
| Stroke | `1` | `0.07491816847377022` | `0.06981823142169408` | `gender: "Female"`, `hypertension: "1"`, `smoking_status: null` |

The form test also asserted that “Other” appears only in the stroke gender control and that the Yes/No hypertension selection preserves its string code. No model preprocessing or encoder was changed.

Limits: the supplied image's redistribution rights remain unverified; its 735 × 411 resolution softens on large screens. Manual Safari/Windows/assistive-technology and native Intel GPU performance checks are outside this run. Historical static figures retain their original labels/colors as immutable evidence.
