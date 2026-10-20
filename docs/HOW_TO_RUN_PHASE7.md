# Run Phase VII

From the repository root with the managed `.venv` and existing prepared datasets:

```sh
.venv/bin/python -m mediscope.ml.phase7
.venv/bin/python -m pytest -q
cd frontend && npm test -- --watch=false && npm run build
```

The runner checks the frozen Phase IV split and source hashes, then writes `reports/phase7/` (JSON, CSV, 200-dpi PNG, execution summary and SHA-256 manifest). It does not touch original datasets or trained Phase IV artifacts. Re-running replaces only Phase VII derived outputs. The output manifest can be verified by `tests/test_phase7.py` or by comparing its listed SHA-256 digests to files.

To serve the saved results, use the existing [backend](HOW_TO_RUN_BACKEND.md) and [frontend](HOW_TO_RUN_FRONTEND.md) startup instructions. Open `/research-lab`. API routes are `GET /api/v1/research-lab`, `GET /api/v1/research-lab/{heart|diabetes|stroke}` and `GET /api/v1/research-lab/exports/{registered-filename}`. They load verified saved outputs and never fit a model during HTTP requests.

For a browser regression check with the local FastAPI and Angular servers running on the configured ports:

```sh
cd frontend && npx playwright test e2e/phase7.spec.ts
```

The generated PNG and CSV exports are report-ready. PDF export is not implemented or claimed; the Phase VII pipeline has no verified PDF export workflow.
