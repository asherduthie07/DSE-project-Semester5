# Phase V methodology

Phase I prepared CSVs and quality manifests are the only clinical and encounter data inputs. Imports validate exact ordered columns, fixed source row counts, target frequencies and SHA-256 before writing. Synthea IDs are checked for uniqueness; encounter patient references are checked against both source patients and imported patients. Source-row `_id` values preserve duplicate observations. `UpdateOne(..., $setOnInsert, upsert=True)` does not overwrite existing imported documents. A changed digest is rejected for review. Source URL, raw checksum, terms and uncertain provenance come from `data/metadata/datasets.json`.

```mermaid
flowchart LR
 A[Registered raw archive] --> B[Verified Phase I prepared CSV]
 B --> C[SHA-256, schema, count and target checks]
 C --> D[Field minimization and null conversion]
 D --> E[Stable source-row IDs]
 E --> F[MongoDB insert-only upserts]
 F --> G[Count and pandas reconciliation]
```

MongoDB aggregations use explicit `source_dataset` filters so demonstration records cannot enter denominators. Patient demographic counts use one patient document per person; encounter class and monthly counts use encounter documents. `encounters_per_patient` counts visits for each synthetic patient. Stroke average glucose uses all nonmissing glucose values for each stroke class. The controlled CRUD example uses an isolated `phase5_demo` collection.

The cross-system comparison requires the same 53,346 encounter rows and class grouping. It records pandas and MongoDB aggregation wall time, plus Hadoop output validation time. Hadoop execution duration is recorded separately by the actual job driver. Local tests of mapper/reducer establish logic but do not establish Hadoop runtime success. No scaling inference is drawn from a single laptop or this dataset size.
