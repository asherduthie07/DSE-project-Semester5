# Frosted dashboard appearance

Owner-authorized UI follow-up, 2026-11-02. No backend, dataset, model, or research result changes.

## Behavior

- Shared dark glass tint: 50%; backdrop blur: 12px. Cards, shell, controls and report surfaces use the shared appearance settings. Clear layout wrappers and chart canvases preserve the underlying composition.
- Background image: 65% brightness and 12px blur. Original images remain unchanged.
- A separate palette-colored radial-glow layer sits above the image and below the dashboard. Both decorative layers ignore pointer events and are hidden from accessibility tools.
- One page scrollbar drives both layers. Image travel is `progress * min(scrollRange * .15, viewportHeight * .12)` upward; glow travel uses `.30` and `.24`. A clipped fixed wrapper and oversized layers cover the viewport through scrolling and resizing.
- Scroll and resize events schedule a single animation frame outside Angular. A body ResizeObserver handles content changes. Destruction removes observers/listeners; reduced motion disables transforms. No continuous animation loop is added.
- Existing Background Studio units and controls remain. A one-time `mediscope-frosted-v6` migration applies the four new defaults to existing preferences. Later customization persists; reset restores these defaults. Other preferences and selected images remain intact.
- Unsupported backdrop-filter browsers receive a stronger dark translucent fallback.

## Verification

Final verification: Angular unit tests **36/36 passed**; final production build **passed**; sequential Chromium selection **7/7 passed in 4.1 minutes**. The selection covers migration/persistence/reset, parallax/coverage/reduced motion, mobile keyboard and automated WCAG checks, image recovery and frosted alpha, all eight routes, all eight routes at 1440/1280/768/390 px, and Background Studio palette/reset/keyboard close. No browser page errors or horizontal overflow were observed in the route sweep.

Commands (from frontend/): `npm test -- --watch=false`, `npm run build`, and `npx playwright test e2e/appearance.spec.ts e2e/integration.spec.ts e2e/workspace.spec.ts -g 'frosted|slow layers|default background|global background|keyboard dialog|background studio|seven real'`.

Desktop Command Center and mobile Prediction Lab screenshots were visually inspected. Tests used headless Chromium with software WebGL; cross-browser and native GPU performance were not measured. Local API and Angular servers were started for verification and remain available at 127.0.0.1:8000 and 127.0.0.1:4200.

Initial browser checks found a legacy ultra-glass override reducing panel alpha to .3; corrected to use the shared .5 tint. Browser migration, reduced motion/coverage, keyboard/mobile accessibility and Background Studio checks passed individually. A scrolling test initially sampled before its animation frame; it now waits for the computed position. Initial overlapping browser sweeps caused resource contention and conflicting trace outputs; the final sequential run passed. The broad screenshot sweep now pauses 3D animation and captures representative pages rather than a full-page screenshot of every route.

New screenshots belong under docs/screenshots/frosted/ or use a frosted- filename. Historical Phase VI-C screenshots are preserved.
