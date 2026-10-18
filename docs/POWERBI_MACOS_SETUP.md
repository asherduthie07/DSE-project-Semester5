# macOS: Power BI Service browser workflow

Power BI Desktop is a Windows application. A PBIP cannot be opened natively in Power BI Desktop on macOS. The official browser route is [Power BI Service](https://app.powerbi.com/), but **this repository currently has no verified PBIX**. The upload/view gate is therefore **BLOCKED** until a Windows Desktop session completes the [PBIX procedure](POWERBI_WINDOWS_SETUP.md).

Once a verified `MediScopeAI.pbix` release artifact exists:

1. Clone this repository. Obtain the **versioned verified PBIX** from its documented release or LFS location and compare its published SHA-256. Do not use an unverified file named `.pbix`.
2. Open [app.powerbi.com](https://app.powerbi.com/) in a supported browser and sign in with an eligible Microsoft work/school account. Check that your tenant permits Power BI and that you can use an accessible workspace. Free use may permit personal exploration, while sharing and collaboration can require Pro/PPU or capacity-based licensing. Confirm your institution's permissions.
3. In the workspace, choose **Upload > Browse**, select the verified PBIX, then open the imported report. Verify six pages, slicers, the semantic model and dataset snapshot.
4. Capture screenshots of the workspace item list, each page and a filter interaction. Record the upload date, account/license context (without secrets), and artifact checksum.

A local PBIX upload gives a **snapshot**. The Service cannot refresh `C:\...` or a Mac's repository CSV path by itself. For subsequent data updates, either rebuild and reupload a verified PBIX, connect the model to a supported OneDrive for work/school or SharePoint source and configure credentials, or configure an approved on-premises data gateway and refresh schedule. These are separate workflows; none was tested here. Browser editing depends on tenant permissions and report/model capabilities, and full PBIP/TMDL authoring and Desktop File > Save As remain Windows Desktop steps.

## Service acceptance checklist

- [ ] Verified PBIX with checksum is available.
- [ ] Eligible account and writable workspace are available.
- [ ] PBIX upload succeeds.
- [ ] Imported semantic model is visible; six pages render.
- [ ] Slicers and page interactions work.
- [ ] Snapshot versus refresh behavior is documented for the chosen source.

Official references: [upload Desktop files](https://learn.microsoft.com/en-us/power-bi/connect-data/service-desktop-files), [Power BI project formats](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-overview), [Power BI licensing](https://learn.microsoft.com/en-us/power-bi/fundamentals/service-features-license-type).
