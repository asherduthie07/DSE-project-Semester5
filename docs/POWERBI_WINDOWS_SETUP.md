# Windows: open and validate the Power BI project

**Current gate:** Windows Desktop opening, page rendering, refresh and PBIX export are **NOT TESTED**. The macOS authoring machine cannot run Power BI Desktop. The checked-in PBIP is a reviewable source project, not a verified finished Power BI report.

## From a fresh clone

1. Install [Git](https://git-scm.com/download/win) and [Power BI Desktop for Windows](https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-get-the-desktop). Use a current Windows release. Keep the clone path reasonably short; Microsoft documents a 260-character project path limit.
2. Clone the repository, then open PowerShell in the `DSE-project-Semester5` directory. No raw archives are needed for bundled report data.
3. Validate the bundled 19 CSVs and PBIP source:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_powerbi_windows.ps1 -ValidateOnly
   ```

4. Build an ignored machine-specific project copy and open it:

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\setup_powerbi_windows.ps1
   ```

   The script finds its repository root, checks every bundled CSV checksum, header and row count, and writes `powerbi\.local\MediScopeAI\MediScopeAI.pbip` with the current export directory in the one `DataRoot` parameter. It leaves committed PBIP/TMDL files untouched. If Desktop is not detected, it exits with an error. `-NoOpen` creates the local project without launching it. `-DataRoot C:\some\folder` is accepted only when that folder contains byte-identical versioned exports.

5. In Desktop, approve any local file trust or data-source privacy prompt, refresh if requested, and inspect all six tabs: Executive overview, Heart disease, Diabetes, Stroke, Synthetic hospital, Data quality and research. Confirm charts populate, filters affect the intended fields, measures are valid, and no errors appear. Record any fix in the source project generator, then regenerate the committed PBIP source.
6. Apply `powerbi\theme\mediscope.json` from **View > Themes > Browse for themes**, save, and check colors/legibility. Theme application has not been runtime verified.
7. Use **File > Save As** in Desktop to produce `MediScopeAI.pbix`; reopen it and inspect all six pages and the semantic model. PBIX is ignored by Git until independently validated and a release/LFS distribution decision is made. Record its SHA-256 with `Get-FileHash .\MediScopeAI.pbix -Algorithm SHA256`.

## Desktop acceptance checklist

- [ ] Setup script passes `-ValidateOnly` on Windows.
- [ ] It detects Desktop and opens the generated local PBIP from an arbitrary clone path.
- [ ] All 19 import queries load without privacy/path errors.
- [ ] Six pages and all 29 visuals render with correct captions and aggregation.
- [ ] Slicers and cross filtering work as documented; note that page-specific outcome slicers are currently scoped to their corresponding outcome table and need runtime review.
- [ ] Relationships and DAX measures show no errors.
- [ ] Refresh succeeds using bundled CSVs.
- [ ] The theme is applied and saved.
- [ ] A PBIX is created with Desktop File > Save As, reopened, and checksum recorded.

Capture a screenshot of the setup output, each report page, Model view, query refresh result, and reopened PBIX. Until this checklist is executed, the actual Desktop dashboard and PBIX remain **BLOCKED**.
