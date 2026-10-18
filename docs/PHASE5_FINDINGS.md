# Phase V findings

## Data and database results

The five verified prepared source tables contained heart 303 rows, diabetes 520, stroke 5,110, Synthea patients 1,171 and Synthea encounters 53,346. Live MongoDB collection counts matched all five exactly. Repeated imports retained the same document IDs and field contents. The 269 intentional duplicate diabetes rows remained present, and all encounter patient references resolved to the synthetic patient collection.

MongoDB's heart target counts were 164/139; diabetes outcomes were 200 Negative and 320 Positive; stroke outcomes were 4,861/249. The synthetic patient dataset contained 609 F and 562 M rows. Average glucose was 104.7955 for stroke status 0 (4,861 records) and 132.5447 for status 1 (249 records). These are dataset summaries and do not imply causal or clinical conclusions.

## Cross-engine encounter counts

The six class counts were identical in prepared-source pandas, MongoDB aggregation and Hadoop Streaming: ambulatory 18,936; emergency 2,090; inpatient 1,838; outpatient 9,003; urgentcare 2,373; wellness 19,106. The total is 53,346 encounters. It is an event count, not a unique patient count. The monthly aggregation generated 1,079 month groups, and per-patient encounter aggregation generated 1,171 patient groups; each reconciled to 53,346 encounters.

## Performance observation

For a single live run over the same 53,346 prepared records, pandas aggregation took 0.2900 seconds, MongoDB aggregation took 0.0569 seconds, Hadoop Streaming execution took 19.3230 seconds, and separate Hadoop output validation took 0.2940 seconds. The Hadoop time includes local pseudo-distributed job startup and scheduling overhead. This is a small, one-machine, single-run observation; it cannot establish the benefits or scalability Hadoop may provide on large distributed datasets. Setup cost and differing execution paths also limit direct performance interpretation.

## System and verification

On the Intel Mac, Docker 29.8.2 ran MongoDB 7.0.41 and Apache Hadoop 3.4.3 with one HDFS DataNode and one YARN NodeManager. A real YARN MapReduce application finished SUCCEEDED. Retrieved reducer output matched the six pandas/MongoDB counts. The live opt-in complete suite passed 78 tests with no skips; independent Phase I and Phase IV verifiers and Phase III static verifiers passed. A SHA-256 snapshot found no changes to 286 Phase I–IV files.

The Phase IV tracked artifact manifest still reports eight hash mismatches that predate this final Phase V run. The separate Phase IV output verifier passed, and no prior-phase file was modified during Phase V verification. Windows runtime is not tested because no Windows host was available. Synthea records are synthetic; disease datasets retain their documented source and provenance limits. The ML models remain research and education artifacts, not clinically validated tools.

Full command evidence and the per-requirement decision matrix are in [PHASE5_VERIFICATION.md](PHASE5_VERIFICATION.md). Machine-readable live evidence is in `reports/bigdata/final/20261018T211007Z/`.
