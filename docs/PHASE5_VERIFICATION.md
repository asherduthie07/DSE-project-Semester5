# Phase V live verification — 2026-10-19 (Asia/Kolkata)

## Startup diagnosis and fixes

Docker Desktop 29.8.2 was running on this Intel Mac (`x86_64`, 8,217,882,624 bytes allocated). No Phase V containers existed initially. The first `docker compose ... up` build failed at `sudo apt-get: command not found`: Apache Hadoop 3.4.2 was based on CentOS 7. Replacing `apt-get` with `yum` failed because the CentOS 7.6.1810 mirror URLs returned 404 and `No package python3 available`.

The pinned Apache Hadoop image was updated to **3.4.3**, whose inspected Ubuntu 22.04 image already contains Python 3; the unnecessary derived Dockerfile was removed. With that image, MongoDB and YARN started, but NameNode reported `Directory /tmp/hadoop-hadoop/dfs/name ... does not exist or is not accessible`, followed by `NameNode is not formatted`. Compose had mounted the NameNode volume at `/tmp/hadoop-root/dfs/name`. DataNode reported `EPERM: Operation not permitted` and `Too many failed volumes` on its root-owned named volume.

The NameNode mount now matches Hadoop's configured path. `docker/init_hdfs.sh` sets the Hadoop volume ownership and permissions, formats a **confirmed-empty** NameNode volume on first use, and refuses a nonempty unformatted volume. Before the one-time live format, both named HDFS volumes were inspected and contained no files. No Docker volume was deleted or reset. A later setup run logged `Existing formatted NameNode volume preserved.` The initializer was also tested on an ephemeral container with no persistent volume. The original MongoDB volume was retained.

## Live services and data

`bash scripts/setup_bigdata_macos.sh` completed successfully. `docker compose ... ps -a` showed MongoDB 7.0.41, NameNode, DataNode and ResourceManager healthy; NodeManager was running. The one-shot volume initializer exited 0. `mediscope bigdata status` reported PASS for Docker, MongoDB, HDFS (`Live datanodes (1)`), and YARN (`Total Nodes:1`, NodeManager `RUNNING`). Host bindings were `127.0.0.1:27017`, `127.0.0.1:9870`, and `127.0.0.1:8088`. Machine-readable status is in `reports/bigdata/service_status.json`.

`mediscope bigdata import --dataset all` imported the verified Phase I tables. `mediscope bigdata verify` matched all five source row counts, all eight MongoDB aggregations and all required indexes against pandas. A controlled CRUD record was created, read, updated and deleted in `phase5_demo` without touching imported rows. Repeat import in the live integration test returned identical counts.

| Required collection | Live documents |
|---|---:|
| `dataset_metadata` | 9 |
| `heart_disease_records` | 303 |
| `diabetes_records` | 520 |
| `stroke_records` | 5,110 |
| `hospital_patients` | 1,171 |
| `hospital_encounters` | 53,346 |
| `data_quality_reports` | 4 |
| `model_experiments` | 3 |

The live MongoDB encounter-class aggregation returned ambulatory 18,936; emergency 2,090; inpatient 1,838; outpatient 9,003; urgentcare 2,373; wellness 19,106. These are **encounter counts**, totaling 53,346, not distinct-patient counts. Results and all-query reconciliation are in `reports/bigdata/mongodb_encounters_by_class.json` and `mongodb_reconciliation.json`.

## Genuine HDFS and MapReduce evidence

`mediscope bigdata mapreduce --job encounter_counts` uploaded `/mediscope/input/encounter_classes.txt` (544,666 bytes), listed it in HDFS, submitted Hadoop Streaming through YARN, retrieved the reducer part file, and checked every count against pandas. A second real run passed in the integration test. The final job log records application `application_1792354467390_0002`, map 100%, reduce 100%, and `completed successfully`. HDFS contained `/mediscope/output/encounter_counts/_SUCCESS` and `part-00000` (94 bytes). The six reducer counts exactly matched the MongoDB counts above and the source pandas table. The final job's measured execution time was **20.0007 s**.

Evidence: `reports/bigdata/hadoop_job.log`, `hadoop_encounter_counts.tsv`, and `hadoop_verification.json`. The source SHA-256 reconciled across preparation and output verification: `c38b5c2f8a9440a00cd8470c397e47a44d4cc0dee3880c9906a0165932bbbd3f`.

## Timings, tests, and limits

One local wall-clock observation from `mediscope bigdata benchmark`: pandas aggregation **0.2696 s**, MongoDB aggregation **0.0569 s**, Hadoop Streaming job **20.0007 s**, and separate Hadoop output validation **0.2917 s**. These timings are not controlled repetitions, exclude different setup costs, and cannot establish distributed scalability with about 53,000 encounters. The measured record is `reports/bigdata/processing_comparison.json`.

The fast full suite reported **75 passed, 3 skipped** (the skipped tests are explicitly Docker-dependent). With `MEDISCOPE_BIGDATA_INTEGRATION=1`, the live integration suite reported **3 passed**, including idempotent import and a real job. The independent Phase I verifier reported **PASS, zero errors**. Phase I–IV data and models were not changed. Shell syntax, Compose configuration and the macOS setup script were checked. The PowerShell setup remains **NOT TESTED on Windows**.

## Requirement decision matrix

| Gate | Decision | Evidence |
|---|---|---|
| MongoDB running and port reachable | PASS | PyMongo ping, Compose health, loopback port |
| Required records imported | PASS | Eight live collection counts above |
| CRUD and database queries | PASS | Controlled CRUD; saved aggregation result |
| Aggregations match source | PASS | Eight live comparisons in `mongodb_reconciliation.json` |
| HDFS operational | PASS | One live DataNode; input/output HDFS listings |
| Hadoop architecture documented | PASS | `HADOOP_ARCHITECTURE.md` and Compose |
| Genuine MapReduce executed | PASS | YARN application/job log and `_SUCCESS` |
| Reducer outputs verified | PASS | Exact six-class pandas reconciliation |
| Windows setup documented and checked | NOT TESTED | Script documented; no Windows runtime available |
| macOS setup documented and checked | PASS | Actual setup script completed successfully |
| Previous phases functional | PASS | 75-pass full suite, Phase I verifier PASS |
| Report-ready evidence generated | PASS | Live status, DB reconciliation, job log, reducer output, timing JSON |

**Decision:** Phase V passes its live local Intel Mac demonstration gates. Windows runtime portability is still unverified. This is a one-laptop development cluster and the disease models remain research-only, not clinical tools.
