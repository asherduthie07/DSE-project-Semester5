# MediScope AI engineering rules

- Work only on the phase explicitly requested by the project owner. Stop after reporting phase results and wait for approval.
- Inspect existing files before editing; preserve raw data, schemas, provenance, and unrelated work.
- Use real, traceable source datasets. Never invent results, citations, or execution logs. Identify uncertain provenance.
- Keep raw files immutable. Document original URLs, terms, checksums, schema, and every derived artifact.
- Fit learned preprocessing within training folds using pipelines. Never leak test information into training or model selection.
- Use reproducible seeds, managed dependencies, meaningful automated tests, and typed modular code.
- Keep design and progress in docs/, including docs/PROJECT_STATUS.md.
- Disease models and predictions are for research and education only. They are not clinically validated or medical advice.
- Do not claim a feature works without running a relevant check.

## Phase boundaries

Phase 0: repository, environment, dataset registry and read-only audit only. No preprocessing, EDA, modeling, frontend, backend API, database ingestion, or Hadoop jobs.
Later phases require explicit authorization before implementation.
