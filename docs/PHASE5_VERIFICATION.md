# Phase V live verification — 2026-10-19 (Asia/Kolkata)

## Final decision

**Phase V PASS for the live local Intel Mac demonstration.** MongoDB imports, CRUD and aggregation succeeded; a genuine Hadoop Streaming MapReduce job ran through YARN and its reducer output matched both pandas and MongoDB. This is a single-node pseudo-distributed development cluster. Windows runtime testing remains **NOT TESTED**.

The complete evidence bundle for this final run is `reports/bigdata/final/20261018T211007Z/`; `reports/bigdata/final/latest.json` points to it. It includes service and CLI status, first/repeat import logs, all actual aggregation outputs, document-by-document reconciliation, HDFS listings and reducer output, YARN status and task logs, benchmark measurements, test JUnit XML, and previous-phase integrity checks.

## Services and machine

On the Intel Mac (`x86_64`), Docker Engine 29.8.2 reported about 8.2 GB available to containers. The existing Compose stack was used without deleting or resetting volumes. `docker compose -f docker/compose.bigdata.yml ps -a` showed MongoDB 7.0.41, Hadoop NameNode, DataNode, ResourceManager and NodeManager running; MongoDB, NameNode, DataNode and ResourceManager were healthy. `mediscope bigdata status` returned PASS for Docker, MongoDB, HDFS and YARN. HDFS reported one live DataNode; YARN reported one RUNNING NodeManager. Local published endpoints were MongoDB `127.0.0.1:27017`, NameNode UI `127.0.0.1:9870`, and ResourceManager UI `127.0.0.1:8088`.

Evidence: `service_status.json`, `services.log`, `status.log`.

### Startup configuration diagnosis

The earlier startup attempt exposed two Hadoop image issues and two HDFS volume issues. The Hadoop 3.4.2 base was CentOS 7; `apt-get` was unavailable, and switching to `yum` failed against retired CentOS mirrors with no Python 3 package. The pinned image was moved to Apache Hadoop 3.4.3, whose inspected Ubuntu 22.04 image includes Python 3. The NameNode volume had been mounted at a path different from Hadoop's configured NameNode directory, and the DataNode volume ownership prevented Hadoop from opening it. `docker/init_hdfs.sh` now corrects ownership and permissions, formats only a confirmed-empty NameNode directory, and refuses a nonempty unformatted directory. Before initial formatting, both HDFS volumes were checked and empty. No existing Docker volume was deleted or reset; the live setup logs confirm the formatted NameNode volume was preserved.

## MongoDB import, reconciliation, CRUD and aggregations

The import command was run twice. All five prepared source tables matched their MongoDB document counts and SHA-256 lineage. Every imported field was compared with the prepared source; repeated import preserved the same IDs and contents. The diabetes source's 269 intentional duplicate rows were retained; all 53,346 synthetic encounters reference existing synthetic patients (zero orphans). The CRUD demonstration created, read, updated and deleted its controlled `phase5_demo` record.

| Collection | Documents |
|---|---:|
| `heart_disease_records` | 303 |
| `diabetes_records` | 520 |
| `stroke_records` | 5,110 |
| `hospital_patients` | 1,171 |
| `hospital_encounters` | 53,346 |
| `dataset_metadata` | 9 |
| `data_quality_reports` | 4 |
| `model_experiments` | 3 |

The live aggregations returned:

| Aggregation | Actual result |
|---|---|
| Heart classes | 0: 164; 1: 139 (303 records) |
| Diabetes outcomes | Negative: 200; Positive: 320 (520 records) |
| Stroke outcomes | 0: 4,861; 1: 249 (5,110 records) |
| Average glucose by stroke status | status 0: 104.7955 over 4,861 rows; status 1: 132.5447 over 249 rows |
| Synthetic patients by gender | F: 609; M: 562 (1,171 patients) |
| Encounters by class | ambulatory: 18,936; emergency: 2,090; inpatient: 1,838; outpatient: 9,003; urgentcare: 2,373; wellness: 19,106 (53,346 encounters) |
| Encounters per synthetic patient | 1,171 patient groups; 53,346 encounters total |
| Monthly synthetic encounters | 1,079 month groups; 53,346 encounters total |

All eight pipelines matched pandas. Encounter totals are event counts, not unique patient counts. Full actual output is preserved in `mongodb_aggregation_results.json`; validation and index evidence is in `mongodb_reconciliation.json`. Import and CRUD logs are `import_first.log`, `import_repeat.log`, and `crud.log`.

## HDFS and genuine Hadoop Streaming job

The prepared input contains one sanitized encounter-class category per row (53,346 rows, source SHA-256 `c38b5c2f8a9440a00cd8470c397e47a44d4cc0dee3880c9906a0165932bbbd3f`). It was uploaded to `/mediscope/input/encounter_classes.txt` (544,666 bytes). Hadoop Streaming submitted mapper and reducer tasks through YARN. Application `application_1792354467390_0007` and job `job_1792354467390_0007` finished with `Final-State: SUCCEEDED`; map/reduce progress reached 100%. YARN's configured log aggregation is DISABLED, so `yarn logs` reported unavailable aggregated logs. The NodeManager task logs were collected directly and saved as `nodemanager_task_logs.log`.

HDFS listed the input and the output directory containing `_SUCCESS` and `part-00000` (94 bytes). Retrieved reducer output:

| Encounter class | Hadoop | Pandas | MongoDB |
|---|---:|---:|---:|
| ambulatory | 18,936 | 18,936 | 18,936 |
| emergency | 2,090 | 2,090 | 2,090 |
| inpatient | 1,838 | 1,838 | 1,838 |
| outpatient | 9,003 | 9,003 | 9,003 |
| urgentcare | 2,373 | 2,373 | 2,373 |
| wellness | 19,106 | 19,106 | 19,106 |
| **Total encounters** | **53,346** | **53,346** | **53,346** |

Evidence: `mapreduce_cli.log`, `hadoop_job.log`, `yarn_application_status.log`, `yarn_application_logs.log`, `nodemanager_task_logs.log`, `hdfs_listing.log`, `hdfs_reducer_read.log`, `hadoop_encounter_counts.tsv`, `hadoop_verification.json`, and `mapreduce_results.json`.

## Processing times

The CLI measured one local run on the same 53,346 source records: pandas aggregation **0.2900 s**, MongoDB aggregation **0.0569 s**, Hadoop Streaming job **19.3230 s**, and Hadoop output validation **0.2940 s**. These are single wall-clock observations, not repeated controlled benchmarks. The Hadoop time includes local job startup, scheduling, container/task startup and processing; this single-node pseudo-distributed run has no distributed scale-out benefit. Approximately 53,000 rows cannot establish Hadoop's performance or scalability on large distributed workloads.

Raw measurements and source hash are in `processing_comparison.json`; `benchmark_cli.log` records the command output.

## Tests and earlier-phase preservation

`pytest -v` with `MEDISCOPE_BIGDATA_INTEGRATION=1` ran all **78 tests: 78 passed, 0 failures, 0 skips** in 55.53 seconds. This includes the three Docker-dependent live integration tests. The Phase I independent verifier passed with zero errors; Phase III Power BI export and static project verifiers passed; the Phase IV independent model-output verifier reloaded and verified all 15 estimators. A before/after SHA-256 snapshot of 286 Phase I–IV files reported no changes.

An optional `scripts/build_phase4_manifest.py --check` returned FAIL because eight Phase IV logistic-regression model, experiment and comparison-table hashes already differed from the tracked manifest before this run. The Phase IV independent output verifier passed, and the final run's earlier-artifact snapshot confirms Phase V did not change those files. No Phase IV artifacts or manifest were rewritten.

Evidence: `tests.xml`, `complete_tests_with_live_integration.log`, `phase1_integrity.log`, `phase3_exports.log`, `phase3_project.log`, `phase4_models.log`, `phase4_manifest.log`, `phase4_manifest_preexisting_mismatch.json`, and `earlier_artifacts_unchanged.json`.

## Commands executed

The final evidence runner was invoked as:

```sh
.venv/bin/python -m scripts.final_phase5_verification
```

It executed `docker compose -f docker/compose.bigdata.yml ps -a`; `python -m mediscope bigdata status`; `import --dataset all` twice; `verify`; `crud`; each of the eight `aggregate --query ...` commands; `mapreduce --job encounter_counts`; and `benchmark`. It ran the complete suite with the live integration opt-in and JUnit capture:

```sh
MEDISCOPE_BIGDATA_INTEGRATION=1 .venv/bin/python -m pytest -v --junitxml=reports/bigdata/final/20261018T211007Z/tests.xml
```

It also ran the independent Phase I verifier, Phase III static verifiers, Phase IV output verifier and the read-only Phase IV manifest check. Exact argument vectors, exit codes, durations and captured stdout/stderr are recorded in `commands.json`.

## Requirement decision matrix

| Requirement | Decision | Evidence / scope |
|---|---|---|
| Docker engine running | PASS | Docker 29.8.2 x86_64; `service_status.json` |
| MongoDB service and host port | PASS | MongoDB 7.0.41; loopback `127.0.0.1:27017` |
| Five prepared tables imported and counted | PASS | `collection_counts.json`, `document_reconciliation.json` |
| Repeat import is idempotent | PASS | Stable IDs and contents in `document_reconciliation.json` |
| Synthetic patient/encounter links and duplicates | PASS | Zero orphan encounters; 269 diabetes duplicate rows retained |
| Safe CRUD demonstration | PASS | `crud.log` |
| MongoDB aggregations, indexes and pandas reconciliation | PASS | Eight queries matched; `mongodb_aggregation_results.json`, `mongodb_reconciliation.json` |
| NameNode and DataNode operational | PASS | HDFS status and one live DataNode in `status.log` |
| ResourceManager and NodeManager operational | PASS | YARN reports one RUNNING NodeManager |
| HDFS upload, listing and read-back | PASS | `hdfs_listing.log`, `hdfs_reducer_read.log` |
| Hadoop architecture and local pseudo-distributed limitation documented | PASS | `HADOOP_ARCHITECTURE.md`, `MAPREDUCE_WORKFLOW.md` |
| Genuine Hadoop Streaming job executed | PASS | YARN application/job IDs, `Final-State: SUCCEEDED` |
| Reducer output matches pandas and MongoDB | PASS | All six categories and total 53,346 match exactly |
| Actual processing times recorded | PASS | `processing_comparison.json` |
| Three Docker integration tests | PASS | Opt-in full run: 78 passed, 0 skipped |
| Complete regression suite | PASS | Same 78-test run; earlier-phase checks below |
| Phase I integrity | PASS | Independent verifier: zero errors |
| Phase III static outputs | PASS | Export and project structural verifiers passed |
| Phase IV model outputs | PASS | Independent output verifier passed for all 15 estimators |
| Earlier Phase I–IV files changed by final run | PASS | 286-file before/after SHA-256 snapshot unchanged |
| Existing Phase IV artifact manifest | FAIL (pre-existing) | Eight previously mismatched hashes; no changes made in this run |
| macOS live setup | PASS | Actual Intel Mac Docker stack and setup CLI verified |
| Windows runtime and PowerShell execution | NOT TESTED | No Windows host available; runtime portability not demonstrated |
| Report-ready Phase V evidence | PASS | Run bundle linked above |

The Phase V gate is **PASS** because real MongoDB operations and a real successful Hadoop MapReduce execution were both verified. Windows remains untested and the pre-existing Phase IV manifest discrepancy is recorded separately.
