# Project status

Updated: 2026-10-18 (Phase 0)

## Completed in Phase 0

- Inspected macOS 15.5 x86_64 on Intel Core i9-9880H, Python 3.13.2, Git 2.45.2, Node 22.16.0, npm 10.9.2, Java 17.0.14, existing files, and four raw ZIPs.
- Created monorepo directories, Python package/CLI, dependency declaration, engineering rules, source registry, acquisition notes, and assignment evidence map.
- Registered original schemas and SHA-256 fingerprints for the four already present local archives.
- Created `.venv`, installed the editable Phase 0 package and pytest, and ran `mediscope health`, `mediscope audit`, `pytest -q` (2 passed), and `pip check` (no broken requirements).
- Audited ZIP members in place: Cleveland 303 rows, diabetes 520, stroke 5,110, Synthea patients 1,171 and encounters 53,346. All registered archive checksums matched and no registered column-order/width mismatches were found. Diabetes has 269 identical full-row duplicates; raw data was not modified.
- Observed missing tokens: Cleveland `ca` 4 and `thal` 2; stroke `bmi` 201. The diabetes file has no recognized missing tokens despite the UCI page marking the dataset as having missing values. Synthea has many optional blank fields; details are available from the audit command.

## Blocked or unresolved

- Existing archive download dates and exact acquisition links were not recorded. Synthea generator release/seed and stroke patient origin are unverified.
- Power BI Desktop does not run natively on macOS; later Power BI phase needs an approved Windows/VM or web workflow and actual execution evidence.
- Hadoop and MongoDB executables were not found on PATH at Phase 0 inspection. Installation/configuration belongs to later phases.
- The current Git root is the parent `Semester-5` directory, containing unrelated projects. Stage only this project path if making a later commit.

## Upcoming, pending approval

- Data preparation and EDA.
- Statistical visuals and Power BI.
- Leakage-safe model training and experimental evaluation.
- MongoDB, Hadoop/HDFS/MapReduce.
- Angular + FastAPI demonstration.

No later-phase feature is implemented by Phase 0.
