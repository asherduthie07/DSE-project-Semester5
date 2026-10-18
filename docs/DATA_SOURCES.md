# Dataset acquisition and provenance

The four ZIP files below were already in `data/raw/` at Phase 0 inspection. Their origin cannot be proven from filenames or matching schemas alone. The registered SHA-256 values fingerprint the **local** archives; they are not claimed as upstream publisher checksums. Do not include raw archives in Git. The CLI audits the files inside each ZIP.

| Dataset | Original page | Local ZIP | Required member | Local SHA-256 |
|---|---|---|---|---|
| UCI Cleveland Heart Disease | https://archive.ics.uci.edu/dataset/45/heart+disease | `data/raw/heart+disease.zip` | `processed.cleveland.data` | `b17cd273da9ce1caa4710fce80227ea454d4dbf9fcbc8e6a9121672751563adc` |
| UCI Early Stage Diabetes | https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction | `data/raw/early+stage+diabetes+risk+prediction+dataset.zip` | `diabetes_data_upload.csv` | `67594c0f11257688b57493798e70737b7156ba37a2e6ac75507ae3a35221a388` |
| Healthcare Stroke Prediction | https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset | `data/raw/archive.zip` | `healthcare-dataset-stroke-data.csv` | `83c150178a7a10439862a66b2703869aadc11f201c359436ae1df77d2b5e7485` |
| Synthea sample CSV | https://synthetichealth.github.io/downloads.html | `data/raw/synthea.zip` | `csv/patients.csv`, `csv/encounters.csv` | `4194b18c11eaedcf0d5d5dd448d8ac9661f14381e2ef9f109215dc42266cd38a` |

## Fresh clone or replacement downloads

1. Use each original page above. For UCI, click **Download** and save the ZIP under the exact local ZIP path in the table. For Kaggle, sign in and click **Download**. For Synthea, choose a **CSV sample** download. Preserve each archive unchanged after acquisition.
2. Confirm the required members by running `python3 -m zipfile -l data/raw/NAME.zip` for each archive. If a publisher changes its archive layout, update the registry after inspecting it; do not silently rename unrelated content.
3. Record the exact download URL, access date, advertised version, original filename, and `shasum -a 256 data/raw/NAME.zip` in a new acquisition record before replacing an archive. The current Synthea ZIP's exact generator version/seed and all original download dates are unknown.

UCI marks both datasets [CC BY 4.0](https://archive.ics.uci.edu/dataset/45/heart+disease) ([diabetes page](https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction)). [Synthea's download page](https://synthetichealth.github.io/downloads.html) permits use of generated data and requests citation. The local stroke ZIP contains no license metadata; check the [publisher's current terms](https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset) before sharing it. Its original patient collection method is unverified, so do not describe it as confirmed clinical patient data. Synthea rows are simulated, never real patients.
