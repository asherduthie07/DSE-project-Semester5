# Background Studio

Open **Background Studio** using the persistent settings button at the lower right of any route. The native modal has an accessible name, Escape dismissal, focus containment and focus restoration.

| Control | Behavior |
| --- | --- |
| Current preview | Displays the selected image |
| Main preset | Uses the supplied `frontend/background-image/3.jpg`, served unchanged as `/backgrounds/3.jpg` |
| Cyan horizon preset | Keeps the previous `main-background-image.jpg` available |
| Spectral preset | Original SVG with violet/amber colors; exercises automatic adaptation |
| Upload | JPEG/PNG/WebP up to 10 MB; local object URL, no remote upload |
| Match colors | Extracts from the selected image; disabling freezes the current palette |
| Brightness | .2–1 CSS brightness |
| Background blur | 0–12 px in 0.1 px steps; default 2.4 px (20% of the control range) |
| Position | 0–100% horizontal crop position, vertical center |
| Glass opacity | 0–.80; default 0 leaves panels, navigation and text areas transparent so the global image shows through |
| Glass blur | 0–20 px |
| Glow | 0–1, controls edge glow/shadow intensity |
| Particles | 0–1, controls decorative point opacity/size and density tier |
| Quality | Adaptive/economy/high pixel ratio; economy defaults new analytical charts to precision mode |
| Restore exact defaults | Main image, auto match enabled, brightness 1, background blur 2.4 px, position 50%, glass 0, glass blur 0 px, glow .35, particles .5, adaptive quality |

Bounded appearance settings are stored under `mediscope-appearance-v1`; only valid bundled preset URLs are stored under `mediscope-background-v1`. Background uploads and prediction feature inputs are never persisted. Uploaded images last for the page session; replacement/reset revokes their object URLs. Refresh restores a selected bundled preset or returns to the main image after an upload. Unsupported/stale URLs and failed preset loads restore the main image; Canvas sampling failures keep a decoded background visible with a readable fallback palette.

Existing browsers with the former main image saved switch to `3.jpg` once (`mediscope-background-v5`). Other preset selections remain in place; the old main image stays selectable.

The clear-dashboard update migrates former default glass values (.72 or .48), default brightness (.75), and default glass blur (10 px) once (`mediscope-transparent-v3`). Other appearance preferences remain stored. The sidebar, header, panels, document/form surfaces, and hover states use the same default zero-alpha tint; the slider can add tint when wanted. Foreground content never receives component-level opacity.

The background blur request sets the default to 2.4 px, which is 20% of the existing 0–12 px control range. Existing saved blur values receive this value once (`mediscope-background-blur-v4`); later user adjustments remain stored.

The supplied background's distribution rights have not been established. User uploads are not sent to an external service. The reference photograph is a style reference, not an application preset.
