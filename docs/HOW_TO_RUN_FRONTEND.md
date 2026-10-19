# Run the Phase VI-B frontend

Prerequisites: Node.js 22 (verified: 22.16.0), npm 10 (verified: 10.9.2), Angular CLI 20.3.4 via project dependencies, Python environment from `docs/HOW_TO_RUN_BACKEND.md`. Angular dependencies are locked in `frontend/package-lock.json`. Power BI Desktop, MongoDB and Hadoop are not needed for the disease analytics pages; unavailable optional services show their actual state.

From the repository root, start FastAPI in one terminal:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

On Windows, use `.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log` instead. In another terminal:

```bash
cd frontend
npm ci
npm start -- --host 127.0.0.1
```

Open `http://127.0.0.1:4200/`. The Angular dev proxy forwards `/api` to `127.0.0.1:8000`; edit `frontend/proxy.conf.json` if the backend uses another local address. For production, run `npm run build`; static files appear under `frontend/dist/mediscope-frontend/browser/`. A production web server must proxy `/api/v1` to FastAPI and serve the Angular index for client routes.

Verification commands from `frontend/`:

```bash
npm run build
./node_modules/.bin/tsc --noEmit -p tsconfig.app.json
npm test -- --watch=false
```

Common issues: an unavailable API makes research panels show error states; start FastAPI and verify `/api/v1/health`. MongoDB/HDFS/YARN may remain unavailable without blocking analytics. If port 4200 is occupied, pass `--port 4201` and configure `MEDISCOPE_CORS_ORIGINS` for that origin if bypassing the proxy. A missing prepared dataset or selected model is a backend artifact issue; consult Phase VI-A documentation. This UI does not create or retrain artifacts.
