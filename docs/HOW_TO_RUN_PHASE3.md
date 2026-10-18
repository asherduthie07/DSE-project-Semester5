# Run Phase III on macOS or Windows

## macOS local analytics preview

1. In Terminal, open this repository: `cd /path/to/DSE-project-Semester5`.
2. Check Python 3.11–3.13: `python3 --version`. The local preview uses standard-library Python and the committed aggregate files; raw ZIPs and `.venv` are not needed for viewing.
3. Validate: `bash scripts/run_dashboard_macos.sh --check`.
4. Start: `bash scripts/run_dashboard_macos.sh`.
5. Open `http://127.0.0.1:8765/` in your browser. Explore the six tabs and page filters. Press Ctrl+C in Terminal to stop.

If port 8765 is already in use, run `python3 -m dashboard.app --port 8766` and open that port. If a checksum error appears, restore the tracked `powerbi/exports/v1/` snapshot. If Python is missing, install a supported Python version. The browser page says **local analytics preview**, not Power BI.

## Windows local preview

Install Python 3.11–3.13. From PowerShell in the clone root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_dashboard_windows.ps1 -ValidateOnly
powershell -ExecutionPolicy Bypass -File .\scripts\run_dashboard_windows.ps1
```

Open `http://127.0.0.1:8765/` and stop with Ctrl+C. The Windows command has not been runtime tested on this Mac.

## Real Power BI

Use [Windows PBIP/Desktop instructions](POWERBI_WINDOWS_SETUP.md). A one-command script validates the exports and creates a local copy, but Desktop may need a trust/permission prompt, refresh and visual review. A PBIX does not yet exist; the macOS [Power BI Service workflow](POWERBI_MACOS_SETUP.md) is pending a verified PBIX from Desktop. Browser Power BI and local preview are different products.

## Rebuild and verify source artifacts

From a Python environment containing the Phase II/III analysis dependencies:

```bash
.venv/bin/python scripts/verify_powerbi_exports.py
.venv/bin/python scripts/verify_powerbi_project.py
.venv/bin/python scripts/regenerate_powerbi_exports.py
.venv/bin/python scripts/generate_powerbi_project.py
MPLCONFIGDIR=/private/tmp/mediscope-mpl .venv/bin/python scripts/generate_phase3_figures.py
.venv/bin/python scripts/generate_phase3_tables.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/verify_phase1_outputs.py
```

`regenerate_powerbi_exports.py` needs the ignored raw/prepared Phase I files and Phase II reports. Do not run it on a fresh clone unless you have reacquired and verified those sources. The already committed exports are enough to view the local dashboard or prepare the PBIP on Windows. To regenerate note terms, run the documented independent official Synthea clinical-note exporter and pass `--notes-dir /path/to/notes`; never invent or substitute notes. Report tables and figures appear under `reports/tables/phase3/` and `reports/figures/phase3/`.
