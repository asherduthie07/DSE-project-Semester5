# Run the Phase VI-A FastAPI backend

Run commands from the MediScope AI project root. Python 3.11–3.13 is supported. The API reads the verified prepared CSVs, Phase II reports, Phase IV registry/models and Phase V evidence already in this workspace. On a fresh clone, complete the documented Phase I preparation and Phase IV artifact setup first; ignored prepared data are not bundled in Git.

## macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[api,dev]'
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

The last line is the verified startup command. Add `--reload` during local code editing if desired. Stop with Ctrl+C.

## Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[api,dev]"
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Windows runtime was not tested in Phase VI-A; these commands use the same Python application entry point. Stop with Ctrl+C. Use Docker Desktop's supported Linux backend only if you want the optional live Phase V routes.

## Configuration

Defaults bind the server to loopback, allow local Angular/Vite development origins, and contact MongoDB at `mongodb://127.0.0.1:27017`, NameNode at `http://127.0.0.1:9870`, and YARN at `http://127.0.0.1:8088`. See `.env.example` for optional process environment variables. The application does not read `.env` automatically; export variables in your shell or use your preferred local environment manager. Do not put credentials in source control.

MongoDB, HDFS and YARN can be stopped while the core API runs. `/api/v1/system/readiness` reports DEGRADED and `/api/v1/bigdata/status` shows current availability separately from the saved successful Phase V job evidence. Start Phase V services using [HOW_TO_RUN_PHASE5.md](HOW_TO_RUN_PHASE5.md) if live database routes are required. The API never starts or resets Docker containers.

`--no-access-log` disables Uvicorn's default URL logging. The application's own access log records only HTTP method, route template, status and duration; it omits query values and prediction bodies.

## Explore and check endpoints

Open `http://127.0.0.1:8000/docs` for Swagger UI or `http://127.0.0.1:8000/openapi.json` for the live machine-readable schema. The checked-in snapshot is `backend/openapi.json`.

On macOS, read-only examples:

```bash
curl http://127.0.0.1:8000/api/v1/health
curl http://127.0.0.1:8000/api/v1/system/readiness
curl http://127.0.0.1:8000/api/v1/datasets
curl 'http://127.0.0.1:8000/api/v1/datasets/synthea_csv/records?table=encounters&limit=5&filter_field=ENCOUNTERCLASS&filter_value=wellness'
curl http://127.0.0.1:8000/api/v1/analytics/uci_cleveland_heart/charts
curl http://127.0.0.1:8000/api/v1/analytics/kaggle_stroke/hypotheses
curl http://127.0.0.1:8000/api/v1/models/heart/comparison
curl http://127.0.0.1:8000/api/v1/predictions/heart/schema
curl http://127.0.0.1:8000/api/v1/bigdata/status
curl http://127.0.0.1:8000/api/v1/bigdata/mapreduce/results
curl http://127.0.0.1:8000/api/v1/reports
```

To submit the repository's fictional heart example without storing request values in a log file:

```bash
.venv/bin/python -c "import json,pathlib; print(json.dumps({'features':json.loads(pathlib.Path('examples/heart_case.json').read_text())}))" | curl -sS -X POST -H 'Content-Type: application/json' --data-binary @- http://127.0.0.1:8000/api/v1/predictions/heart
```

On PowerShell, use `Invoke-RestMethod` for GET endpoints. For the same fictional example:

```powershell
$features = Get-Content examples/heart_case.json -Raw | ConvertFrom-Json
$body = @{ features = $features } | ConvertTo-Json -Depth 10
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/predictions/heart -Method Post -ContentType application/json -Body $body
```

Predictions are research scores, not clinical probabilities or diagnoses. The API does not persist submitted features. It only returns registered selected-model classes, scores, thresholds and noncausal local explanations.

## Tests and troubleshooting

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
```

The three Docker integration tests are skipped unless `MEDISCOPE_BIGDATA_INTEGRATION=1` and the Phase V services are actually running. If datasets or models show UNAVAILABLE, check `data/processed/`, `reports/quality/`, `reports/eda/`, `ml/registry.json`, and `ml/models/full/`, then run the corresponding Phase I or Phase IV read-only verifier. Do not substitute new artifacts under old checksums. If port 8000 is occupied, use another loopback port and update the URLs above. For MongoDB/HDFS/YARN failures, inspect Docker Desktop and run `python -m mediscope bigdata status`; the API's other routes remain available.
