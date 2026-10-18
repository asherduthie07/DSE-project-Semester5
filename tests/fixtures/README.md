# Controlled Phase I test fixtures

These tiny CSVs are invented **only to test code behavior**. They are never research data and must not appear in academic dataset statistics or model evaluation.

- `diabetes_controlled.csv`: one exact duplicate; one valid but extreme age (119); one impossible age (200); one `?` missing age; one unknown symptom answer (`Maybe`). Rows follow the registered diabetes schema.
- `hospital_encounters_controlled.csv`: two distinct visits for one synthetic patient and one exact duplicate of the first visit. Tests select the first two for valid repeated visits; the third checks unique-key rejection.
- `stroke_train_controlled.csv`: six training examples with numeric missingness and several categories, used solely to inspect fitted preprocessing parameters.
- `stroke_holdout_controlled.csv`: two held-out examples with extreme values and unseen categories, used solely to test transform behavior and leakage isolation.
