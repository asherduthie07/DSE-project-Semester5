# Phase VII research contribution

This phase adds a controlled, reproducible sensitivity study of data-quality decisions across three heterogeneous healthcare datasets. Its contribution is the *comparison protocol and measured sensitivity*, not a new classifier or a clinical claim.

The study holds original development folds, Phase IV model parameters and operating thresholds fixed while varying numeric imputation, missingness signals, outlier handling, scaling, categorical missingness and diabetes training-profile duplication. It adds OOF probability reliability, threshold/error tradeoffs, recorded subgroup descriptions, validation-fold permutation importance and rank stability across model families. The outputs expose where conclusions depend on preprocessing and where small or repeated samples weaken interpretation.

The work extends the read-only research API and the Holographic Dark Research Workspace with saved results. Probability calibration and threshold relationships remain 2D because their axes have precise statistical meanings. The existing 3D visualization system remains available in the other research pages; Phase VII does not invent a third measurement axis for these comparisons.

No claim of a novel scientific discovery, causal relation, demographic fairness or clinical readiness is made. Source sampling, outcome adjudication, external generalization and clinical impact are unresolved. See [findings](PHASE7_FINDINGS.md) and [verification](PHASE7_VERIFICATION.md) for actual measurements and tested scope.
