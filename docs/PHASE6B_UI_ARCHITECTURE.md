# Phase VI-B frontend architecture

The Dark Research Workspace is the only implemented theme. The Angular 20 standalone application is in `frontend/`; seven routes are lazy loaded through Angular Router. `app.ts` owns the shell and API health signal. Each page owns its route-local state and uses `takeUntilDestroyed` for HTTP subscriptions. The Big Data page additionally uses `exhaustMap` for nonoverlapping 15-second polls while the document is visible.

| Route | Page | Verified API contracts |
| --- | --- | --- |
| `/command-center` | Overview | datasets, status, analytics charts, three model comparisons |
| `/datasets` | Dataset Explorer | datasets, schema, summary, Phase I quality, bounded records |
| `/analytics` | Disease Analytics | saved charts, categorical distribution, correlations, hypotheses |
| `/prediction` | Prediction Lab | ordered input schema and POST prediction |
| `/models` | ML Laboratory | model detail, comparison, confusion matrices, ROC/PR curves, explanations |
| `/big-data` | Big Data Monitor | live status and optional live collection counts; saved job evidence inside status |
| `/research` | Research & Reports | curated report registry and approved report content |

`core/api.ts` centralizes typed requests, a 12-second read timeout (20 seconds for predictions), and memoization of stable research artifacts. Prediction values are held only in component memory. The backend supplies prediction validation and saved model identity; the form checks schema bounds before submission. The versioned fictional fixtures in `frontend/public/examples/` are verbatim copies of `examples/` and are labeled as fictional.

`shared/chart.ts` owns ECharts canvas instances, a ResizeObserver, disposal, chart PNG export, zoom reset and fullscreen. Route-level chunking keeps chart code out of the initial shell bundle. The chart library is ECharts Core with only bar, line, heatmap and scatter registered. Charts map the API's saved counts, coefficients, curves, fold scores and permutation importance; no production chart uses mock values. The saved PNGs in `frontend/public/figures/eda/` are verbatim Phase II figure copies and are shown only when referenced by the API's `approved_figures` list.

The API currently does not expose arbitrary numeric distribution bins, filtered statistical calculations, HDFS capacity/usage, a current YARN job list, or complete feature-level descriptive summaries. The UI labels these limits. It does not equate a saved successful Hadoop job with a currently running job. Records use backend pagination at 25 rows. Exact filters use the backend allowlist for each table; search and sorting are clearly limited to the current page.

## Future Clinical Workspace integration

The shell's CSS variables in `src/styles.css` are the theme boundary. A later separately authorized phase can add a new route group and token set, with its own clinical validation, language, and workflow review. No Clinical Workspace, theme toggle, or clinical recommendation flow is implemented in VI-B.
