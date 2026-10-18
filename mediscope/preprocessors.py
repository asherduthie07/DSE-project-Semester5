"""Unfitted, leakage-safe scikit-learn preprocessing factories for later ML phases."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, MinMaxScaler, OneHotEncoder, OrdinalEncoder, RobustScaler, StandardScaler

from .preparation import PreparationError
from .schema import HEART, DIABETES, STROKE, TableSchema

MODEL_SCHEMAS: dict[str, TableSchema] = {
    "uci_cleveland_heart": HEART,
    "uci_early_diabetes": DIABETES,
    "kaggle_stroke": STROKE,
}


def _numeric_array(X: Any) -> np.ndarray:
    """Convert nullable pandas numerics to scikit-learn's NumPy NaN format."""
    return pd.DataFrame(X).to_numpy(dtype=float, na_value=np.nan)


def _categorical_array(X: Any) -> np.ndarray:
    """Convert pandas NA in categoricals to NumPy NaN without learning values."""
    frame = pd.DataFrame(X).astype(object)
    return frame.where(pd.notna(frame), np.nan).to_numpy(dtype=object)


class IQRClipper(TransformerMixin, BaseEstimator):
    """Optional IQR clipper fitted only on the training portion of a pipeline."""

    def fit(self, X: Any, y: Any = None) -> IQRClipper:
        values = np.asarray(X, dtype=float)
        q1, q3 = np.percentile(values, [25, 75], axis=0)
        spread = q3 - q1
        self.lower_ = q1 - 1.5 * spread
        self.upper_ = q3 + 1.5 * spread
        self.n_features_in_ = values.shape[1]
        return self

    def transform(self, X: Any) -> np.ndarray:
        return np.clip(np.asarray(X, dtype=float), self.lower_, self.upper_)

    def get_feature_names_out(self, input_features: Any = None) -> np.ndarray:
        return np.asarray(input_features, dtype=object)


def feature_roles(dataset_id: str) -> dict[str, Any]:
    """Document binary mappings, nominal columns, and defensible ordinal choices."""
    if dataset_id not in MODEL_SCHEMAS:
        raise PreparationError(f"No classification feature schema for {dataset_id!r}")
    schema = MODEL_SCHEMAS[dataset_id]
    return {
        "continuous": list(schema.continuous),
        "binary_mappings": {name: {values[0]: 0, values[1]: 1} for name, values in schema.binary.items()},
        "nominal": {name: list(schema.categories[name]) for name in schema.nominal},
        "ordinal": {name: list(values) for name, values in schema.ordinal.items()},
        "excluded": list(schema.excluded_from_model),
        "unknown_category_policy": "Unseen nominal categories produce all-zero one-hot columns; unseen binary categories encode as -1 and require monitoring.",
    }


def build_preprocessor(dataset_id: str, config: dict[str, Any]) -> ColumnTransformer:
    """Return an unfitted transform; fit it inside each train/CV fold only.

    Clinical codes such as Cleveland chest pain type or ST-slope are nominal here;
    none of the current source attributes has a defensible explicit ordinal order.
    """
    if dataset_id not in MODEL_SCHEMAS:
        raise PreparationError(f"No classification feature schema for {dataset_id!r}")
    schema = MODEL_SCHEMAS[dataset_id]
    numeric_steps: list[tuple[str, Any]] = [
        ("as_array", FunctionTransformer(_numeric_array, feature_names_out="one-to-one")),
        ("impute", SimpleImputer(strategy=config["numeric_imputation"], keep_empty_features=True)),
    ]
    if config["iqr_clip_in_training_pipeline"]:
        numeric_steps.append(("clip", IQRClipper()))
    scaler = {"standard": StandardScaler, "minmax": MinMaxScaler, "robust": RobustScaler}.get(config["numeric_scaling"])
    if scaler is not None:
        numeric_steps.append(("scale", scaler()))
    category_kwargs = {"strategy": config["categorical_imputation"], "keep_empty_features": True}
    if config["categorical_imputation"] == "constant":
        category_kwargs["fill_value"] = config["categorical_fill_value"]
    binary = Pipeline([
        ("as_array", FunctionTransformer(_categorical_array, feature_names_out="one-to-one")),
        ("impute", SimpleImputer(**category_kwargs)),
        ("encode", OrdinalEncoder(categories=list(schema.binary.values()), handle_unknown="use_encoded_value", unknown_value=-1)),
    ])
    nominal = Pipeline([
        ("as_array", FunctionTransformer(_categorical_array, feature_names_out="one-to-one")),
        ("impute", SimpleImputer(**category_kwargs)),
        ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    transformers: list[tuple[str, Any, list[str]]] = [
        ("numeric", Pipeline(numeric_steps), list(schema.continuous)),
        ("binary", binary, list(schema.binary)),
        ("nominal", nominal, list(schema.nominal)),
    ]
    if schema.ordinal:
        transformers.append(("ordinal", Pipeline([
            ("as_array", FunctionTransformer(_categorical_array, feature_names_out="one-to-one")),
            ("impute", SimpleImputer(**category_kwargs)),
            ("encode", OrdinalEncoder(categories=list(schema.ordinal.values()), handle_unknown="use_encoded_value", unknown_value=-1)),
        ]), list(schema.ordinal)))
    return ColumnTransformer(transformers=transformers, remainder="drop", verbose_feature_names_out=True)
