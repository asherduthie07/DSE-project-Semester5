# Portable snapshot and platform boundaries

## Tracked inputs

`powerbi/exports/v1/manifest.json` pins names, ordered schemas, row counts, source checksums and SHA-256 for 19 aggregate CSVs. Only aggregated analysis data are included. There are no source identifiers or patient-level rows. Synthea note frequencies come from an independent 10-patient generator run, so they must not be joined to the 1,171-patient hospital cohort. `dataset_dimension.csv` links only aggregates from the same registered source. Disease sources remain separate.

`python3 scripts/verify_powerbi_exports.py` uses only the Python standard library and succeeds without the ignored raw ZIPs, processed CSVs or EDA reports. The local Plotly.js bundle is vendored from official Plotly distribution and checked by SHA-256. `python3 -m dashboard.app --check` verifies the browser app input contract. Regeneration from local verified Phase I/II artifacts uses `.venv/bin/python scripts/regenerate_powerbi_exports.py`; supply `--notes-dir PATH` only when recreating the separate Synthea note export. Regeneration will change checksums when inputs or library behavior change; review scientific provenance before committing the new snapshot.

## Power BI source

The PBIP, PBIR and TMDL files are text and version-controlled. Windows setup validates the snapshot and substitutes the single `DataRoot` token into an ignored local copy. The committed source never contains a personal filesystem path. Microsoft documents that PBIP/PBIR source files are for Desktop authoring and that converting to PBIX uses Desktop File > Save As. The 29 PBIR visuals passed static JSON-schema validation against Microsoft's published schemas, but static validity does **not** prove successful Power BI rendering or interactivity. Windows and Service runtime acceptance remain open.

The local browser dashboard works from committed exports without raw data or cloud accounts. Its served HTTP endpoints and JavaScript syntax passed checks on macOS; an actual visual browser session was unavailable for this verification. It is an analytics preview and does not replace the mandatory Power BI gate.

References: [PBIP overview](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [PBIR format](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report), [TMDL overview](https://learn.microsoft.com/en-us/analysis-services/tmdl/tmdl-overview), [Service file upload](https://learn.microsoft.com/en-us/power-bi/connect-data/service-desktop-files).
