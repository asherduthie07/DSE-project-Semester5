# Dark Research Workspace design system

The visual system uses deep navy layers and restrained teal, blue and violet accents. Tokens are in `frontend/src/styles.css`: background `#080D19`, sidebar `#0B1220`, surface `#101A2B`, card `#131F32`, hover `#19283D`, border `#26354A`; text `#F1F6FC`, secondary `#9AAEC5`, muted `#71869F`; teal `#39D9D0`, blue `#60A5FA`, violet `#A78BFA`, positive `#34D399`, warning `#FBBF24`, error `#FB7185`.

Space Grotesk is used for display numerals and headings, DM Sans for interface text, with system fallbacks. Remote font loading is optional; the UI remains usable without it. Metrics use tabular numerals. The shell has a 256 px sidebar, 72 px collapsed rail, 70 px top bar, and responsive drawer below 700 px. Four-, three- and two-column grids collapse progressively at 1100 and 700 px. Panels have subtle borders, rounded corners and hover feedback. Focus rings, explicit form labels, chart accessible names and reduced-motion support are included.

Components: App shell (brand, nav, API connection, status), page heads, metric cards, panels, tags, controls, tables, notices, and the reusable chart wrapper. Navigation icons are thin inline SVG paths. Empty and error states describe absent artifacts/services. Research-use notices appear in prediction and model contexts. No theme switch is present.
