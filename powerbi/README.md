# MediScope AI Power BI source

`MediScopeAI.pbip` is an editable Power BI Project. Its PBIR report source defines six pages and 29 visual configurations; its TMDL semantic model defines 32 import tables/views, 17 dataset-dimension relationships, explicit aggregate measures and a single `DataRoot` Power Query parameter. The source was structurally checked on macOS, including validation of 38 PBIR JSON files against Microsoft's published schemas. **It has not been opened in Power BI Desktop.** The report and interactions must be reviewed there before calling this a completed Power BI dashboard.

`exports/v1/` contains 19 versioned aggregate CSVs and SHA-256/schema/row-count manifest. It contains no patient IDs or raw patient rows. `note_terms.csv` comes from an independent Synthea run. The source PBIP uses the literal `__MEDISCOPE_DATA_ROOT__` parameter token; the Windows setup script writes an ignored local copy with the clone's export path.

No PBIX or PBIT exists. Microsoft documents Desktop **File > Save As** as the supported PBIP-to-PBIX route. A PBIX is the report/model with data snapshot; a PBIT is a model/report template without imported data. Do not rename or zip the PBIP to pretend it is a PBIX. See [Windows setup](../docs/POWERBI_WINDOWS_SETUP.md), [macOS Service setup](../docs/POWERBI_MACOS_SETUP.md), and [portability notes](../docs/POWERBI_PORTABILITY.md).

The source theme palette is in `theme/mediscope.json`. Apply and save it in Desktop during runtime review; static report files have no verified theme registration.
