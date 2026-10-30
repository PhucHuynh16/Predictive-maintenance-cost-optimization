"""Cloneable P05 pipelines; fitting them is not predictive model training."""
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.validation import check_is_fitted

from .contracts import FEATURES, GateError


class FeatureContract(TransformerMixin, BaseEstimator):
    def __init__(self, features=FEATURES, require_finite=False):
        self.features = features
        self.require_finite = require_finite

    def _validate(self, X):
        if hasattr(X, "columns") and tuple(X.columns) != tuple(self.features):
            raise GateError("SCHEMA_MISMATCH: feature order/target/IDs")
        a = np.asarray(X)
        if (a.ndim != 2 or a.shape[0] == 0 or a.shape[1] != len(self.features)
                or a.dtype.kind not in "fiu"):
            raise GateError("INVALID_FEATURE_ARRAY")
        a = np.asarray(a, dtype=np.float64)
        if np.isinf(a).any() or (self.require_finite and not np.isfinite(a).all()):
            raise GateError("NONFINITE_FEATURES")
        return a

    def fit(self, X, y=None):
        self._validate(X)
        self.n_features_in_ = len(self.features)
        return self

    def transform(self, X):
        check_is_fitted(self, "n_features_in_")
        return self._validate(X)


def build_preprocessor(kind, features=FEATURES):
    if kind not in ("tree", "lr"):
        raise GateError("PREPROCESSOR_KIND must be tree or lr")
    steps = [("schema", FeatureContract(features=features)),
             ("imputer", SimpleImputer(strategy="median", keep_empty_features=True,
                                       add_indicator=False, copy=True))]
    if kind == "lr":
        steps.append(("scaler", StandardScaler(copy=True, with_mean=True, with_std=True)))
    steps.append(("output", FeatureContract(features=features, require_finite=True)))
    return Pipeline(steps)
