# Phase VI-C implementation plan and architecture

Authorized scope: upgrade the existing seven Angular research routes. Preserve all datasets, models and saved experimental results. No Phase VII or Clinical Workspace.

## Inspection and baseline

- Read AGENTS.md, README.md, PROJECT_STATUS.md, Phase VI-A API specification, VI-B architecture, design system, verification and run instructions; inspected Angular shell, routes, typed API, seven pages and reusable ECharts wrapper.
- Baseline: `cd frontend && npm test -- --watch=false`: 13 passed / 8 files. `.venv/bin/python -m pytest -q`: 87 passed, 3 Docker skips, one Starlette warning.
- Images restored by owner: `frontend/background-image/main-background-image.jpg` (735×411 progressive JPEG) and `reference-image.jpg` (455×260 JPEG). Main image is a blue technical grid with cyan horizon; reference is a cyan/amber floating dashboard, not a particle mesh. Both decoded successfully. Source/license is unknown pending owner response; production distribution rights are unverified.
- Computer-use inventory contained no connected browser. Bundled Playwright Chromium was subsequently installed and supplied live application verification at four viewport widths, interaction checks, WCAG automated checks and screenshots. See `PHASE6C_VERIFICATION.md`.

## Ordered implementation

1. Persistent root image, local appearance state, Canvas color quantization, semantic palette and contrast-safe surfaces.
2. Background Studio and shared glass/HUD styling across existing layouts and charts.
3. Dynamically imported Three.js renderer, OrbitControls, resize/disposal/visibility lifecycle, accessible precision alternative.
4. Pure typed geometry mappings: measured scatter axes, categorical bars, empirical histograms/ridgelines and bivariate density; separate decorative wave and conceptual infrastructure graph.
5. Integrate source exploration, model comparisons and prediction score display without modifying analytical values.
6. Test mappings, appearance, lifecycle and integrations; production build and backend regression; record acceptance status and limitations.

## Library decision

Retain ECharts 6 for precise 2D geometry, tooltips, zoom and legends. Use dynamically imported Three.js for explicit 3D geometry and OrbitControls. Avoid an additional full plotting framework. Official lifecycle references: https://threejs.org/docs/pages/WebGLRenderer.html and https://threejs.org/docs/pages/OrbitControls.html.

## Implemented rendering lifecycle

`HolographicChart` loads `renderer.ts` only for a visible 3D view. `HolographicRenderer` owns one scene, renderer, camera, OrbitControls, ResizeObserver, raycaster, event handlers and animation frame. `setMode('2d')` and Angular route destruction dispose geometries/materials/textures, control listeners, renderer and WebGL context. Browser integration checks observe context release on navigation and mode change. The hero is the only continuously animated scene, capped near 25 FPS and paused when hidden, reduced motion is requested or the user presses Pause.

The scene uses instancing for point clouds and columns, a 20×20 surface grid, low-detail spheres and a pixel-ratio cap (1 adaptive on up to four hardware threads, 1.25 otherwise, 2 only when high quality is chosen). No procedural lighting bloom or full-screen fragment shader is required. In 3D, axis lines and labels identify X/Y/Z; the exact visible ranges are in an HTML key below the viewport to avoid occluding observations. Pointer inspection reports source values. The precision chart and paginated data table remain available without a GPU.

The original seven route chunks remain lazy. Three.js contributes a separate ~582 kB raw / ~120 kB estimated transfer renderer chunk; ECharts remains a ~682 kB raw / ~193 kB transfer lazy chart chunk. The latest background/input correction build measured 345.05 kB raw / 97.66 kB estimated initial transfer. The unchanged main JPEG is ~39 kB in `public/backgrounds/`. These are build measurements, not runtime GPU benchmarks.

## Data boundaries

Existing records API permits pages of at most 100 records. A bounded exploration sample must be disclosed, with complete-case exclusions and fetched/source counts. Heart and stroke axes use an explicit continuous-variable allowlist. Diabetes codes remain categorical. Synthea encounter records omit dates: temporal analyses cannot be derived from this projection. Saved research PNGs remain immutable, including their original colors.
