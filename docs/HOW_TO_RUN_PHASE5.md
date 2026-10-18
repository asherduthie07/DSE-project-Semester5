# Run Phase V

Prerequisites: Python 3.11–3.13, Docker Desktop with Compose and Linux containers, at least 8 GB allocated to Docker, and the verified Phase I prepared files and quality reports. On this Intel Mac, use `source .venv/bin/activate` and `python -m pip install -e '.[dev,bigdata]'`. On Windows x64, use a Python virtual environment and the equivalent `python -m pip install -e ".[dev,bigdata]"`; Docker Desktop should use its supported WSL2 Linux backend. The Apache Hadoop image is amd64, so ARM Windows hosts are not verified.

macOS:

```bash
bash scripts/setup_bigdata_macos.sh
python -m mediscope bigdata status
python -m mediscope bigdata import --dataset all
python -m mediscope bigdata verify
python -m mediscope bigdata crud
python -m mediscope bigdata aggregate --query encounters_by_class
python -m mediscope bigdata mapreduce --job encounter_counts
python -m mediscope bigdata benchmark
bash scripts/stop_bigdata.sh
```

Windows PowerShell:

```powershell
.\scripts\setup_bigdata_windows.ps1
python -m mediscope bigdata status
python -m mediscope bigdata import --dataset all
python -m mediscope bigdata verify
python -m mediscope bigdata crud
python -m mediscope bigdata aggregate --query encounters_by_class
python -m mediscope bigdata mapreduce --job encounter_counts
python -m mediscope bigdata benchmark
docker compose -f docker/compose.bigdata.yml down
```

For all eight aggregation examples use `--query` with `heart_classes`, `diabetes_outcomes`, `stroke_outcomes`, `glucose_by_stroke`, `patients_by_gender`, `encounters_by_class`, `encounters_per_patient`, or `monthly_encounters`. Query results are saved under `reports/bigdata/mongodb_*.json`. `mediscope bigdata import` can select one dataset; import patients before encounters. The setup scripts stop on Docker failure. Run live tests only with `MEDISCOPE_BIGDATA_INTEGRATION=1 python -m pytest -q tests/test_phase5_integration.py`; skipped tests in a normal suite are not a service pass.

HDFS inspection once started: `docker compose -f docker/compose.bigdata.yml exec namenode hdfs dfs -ls /mediscope/input` and `docker compose -f docker/compose.bigdata.yml exec namenode hdfs dfs -cat /mediscope/output/encounter_counts/part-*`. NameNode UI is `http://127.0.0.1:9870`; YARN UI is `http://127.0.0.1:8088`.
