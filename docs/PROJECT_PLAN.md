# Project plan and assignment evidence map

All model work is research-only and requires a later explicit phase request. Evidence must come from executed code and identified source data.

| Compulsory requirement | Planned implementation location | Required proof | Expected report section |
|---|---|---|---|
| Healthcare data preparation | `mediscope/preparation.py`, `mediscope/schema.py`, `mediscope/preprocessors.py`, `data/metadata/`, `data/processed/` | Source inventory, schema audit, missing/duplicate/outlier treatment, transformation log, tests, quality reports | Data sources and preparation |
| Exploratory data analysis | `notebooks/`, `reports/tables/` | Reproducible descriptive tables and distributions from source data | Exploratory analysis |
| Statistical visualization | `visualizations/`, `reports/figures/` | Labeled generated figures with sample sizes and methods | Statistical visualization |
| Power BI | `powerbi/exports/`, report documentation | `.pbix` or documented report, screenshots, refresh source mapping | Power BI dashboard |
| Logistic Regression | `ml/` | Leakage-safe pipeline, seeded split/CV, held-out metrics | Models and evaluation |
| Decision Tree | `ml/` | Same protocol and comparable metrics | Models and evaluation |
| Random Forest | `ml/` | Same protocol and comparable metrics | Models and evaluation |
| KNN | `ml/` | Same protocol and comparable metrics | Models and evaluation |
| MongoDB | `backend/` or `pipelines/` | Collection schema, ingestion counts, representative query output | Database design and MongoDB |
| Hadoop architecture | `big_data/`, `docs/` | Cluster/component diagram, version and runtime evidence | Hadoop architecture |
| HDFS | `big_data/` | File upload/listing commands and actual outputs | HDFS workflow |
| MapReduce | `big_data/` | Job source, input/output, execution logs and result validation | MapReduce analysis |

Additional demonstration: Angular UI in `frontend/`, FastAPI in `backend/`, and rigorous evaluation in `ml/` and `reports/`. These are planned, not Phase 0 deliverables. Each later phase must document reproducibility, leakage controls, limitations, and nonclinical use.
