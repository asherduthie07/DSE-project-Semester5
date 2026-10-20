# MediScope AI — Holographic Research Workspace

Phase VI-C extends the existing Angular research frontend. All seven routes retain their original API-backed workflows. Shared styles live in `frontend/src/holographic.css`; scoped shell/page styles use the same semantic tokens.

## Supplied images

| File | Actual format / size | Observed content | SHA-256 |
| --- | --- | --- | --- |
| `frontend/background-image/main-background-image.jpg` | Progressive JPEG, 735×411, 39,316 bytes | Blue technical grid, cyan horizon, dark blue foreground | `3b7def1d14d4c3369be83cfcd2d2722d635c38e8a89e50455e56fcf8005cac17` |
| `frontend/background-image/reference-image.jpg` | JPEG, 455×260, 25,589 bytes | Floating translucent dashboards, cyan and amber lighting | `badf1a575c618a5bf44454265185b09046d795a1d82c7fed77a2552736775e80` |

Both files were decoded and visually inspected. Contrary to the initial description, the supplied reference does not depict flowing particle meshes. Its floating panels and fine light edges inform the interface; the requested particle wave is implemented separately as abstract decoration. The reference image is not copied into application assets. An unchanged copy of the main image lives at `frontend/public/backgrounds/main-background-image.jpg`, served through Angular's standard public asset path. See `BACKGROUND_AND_INPUT_FIX_VERIFICATION.md` for the serving and input correction.

No source URL, author or license was supplied. Permission to redistribute is **unverified**, and production distribution remains blocked pending that evidence. No obvious watermark was identified, which does not establish permission. The main image's small resolution becomes visibly soft on larger screens; no artificial detail or replacement image was introduced. `spectral-field.svg` is an original code-generated bundled alternate, not a substitute for the default.

## Background and palette

A fixed root layer uses `background-size: cover`, configurable horizontal position, brightness and blur. It sits at z-index 0; the transparent app shell sits at 1. It survives route navigation and ignores pointer events. Its image is decoded asynchronously and sampled through a 64×64 local Canvas. Four-bit RGB buckets rank dominant chromatic colors; a separated hue supplies the secondary color. Adjusted HSL lightness/saturation produce readable highlights and five distinct chart colors. Black/white/transparent and failed images use a deterministic fallback. This is perceptually informed RGB/HSL adjustment, not an OKLCH implementation.

Tokens: `--holo-primary`, `--holo-secondary`, `--holo-accent`, `--holo-highlight`, `--holo-glow`, `--holo-border`, `--holo-surface`, `--holo-surface-shell`, `--holo-surface-readable`, `--holo-surface-hover`, `--holo-text`, `--holo-text-muted`, `--holo-grid`, and `--holo-chart-1` through `--holo-chart-5`. Default panel glass is .48 alpha and sidebar/header glass is .38 alpha, so the image remains visible across every route. Forms and report content use a still-translucent readable surface of at least .72 alpha; muted text contrast on this surface is tested against a worst-case white background and generated dark palette. Decorative ultra glass is confined to the hero; it is not intended for dense data tables. Meaningful warning/error/success indicators preserve their semantic colors. The user slider spans .32–.80, and prior stored default .72 settings migrate once to .48.

## Reuse and interaction

- `.panel` / `.holo-panel`: shared glass panel, fine top edge marker, border, shadow and hover response.
- `.metric`, `.tag`, `.data-note`, `.control`, `.btn`, `.glass-ultra`, `.glass-readable`: shared metric, status, explanation and control surfaces.
- `BackgroundStudio`: native modal dialog with Escape, focus handling, local controls and preview.
- `HolographicChart`: shared chart frame, mode buttons, camera actions, fullscreen, PNG export, hover/pinned inspection, legend and paginated data table.
- `DataExplorer`, `ModelStudio`, `InfrastructureStudio`, `ScoreDisplay`: domain-specific, typed data adapters and controls.
- Existing `ChartComponent`: precise ECharts geometry with palette adaptation, zoom reset, legend behavior, PNG export and fullscreen. Palette-only changes preserve zoom/legend selection. Unchanged options avoid repeated updates on unrelated UI events.

Analytical plots do not continuously animate. The hero runs at a capped ~25 FPS and pauses on document/viewport invisibility or a user pause. Reduced-motion preferences pause it by default. Unsupported backdrop blur falls back to a readable dark surface. The native dialog and keyboard controls supplement pointer interaction; precision views and HTML tables expose data without WebGL.

Saved Phase II PNGs retain their original colors and pixels. Altering verified figure images to match the theme would break their role as immutable evidence.
