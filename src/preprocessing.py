"""Feature-only sklearn pipelines, cloned/fitted inside train folds in later stages."""

from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.data import DataGateError, FEATURES, NUMERIC_FEATURES, validate_features


class FeatureValidator(TransformerMixin, BaseEstimator):
    """Stateless check on both fit and transform; never impute or drop rows."""

    def fit(self, X, y=None):
        validate_features(X)
        self.n_features_in_ = len(FEATURES)
        return self

    def transform(self, X):
        validate_features(X)
        return X

    def get_feature_names_out(self, input_features=None):
        return list(FEATURES)


def build_preprocessor(kind: str) -> Pipeline:
    if kind not in {"lr", "rf"}:
        raise DataGateError("Preprocessor kind must be lr or rf")
    columns = ColumnTransformer(
        [("type", OneHotEncoder(handle_unknown="ignore", sparse_output=False), ["Type"]),
         ("numeric", StandardScaler() if kind == "lr" else "passthrough", list(NUMERIC_FEATURES))],
        remainder="drop", sparse_threshold=0, verbose_feature_names_out=True,
    )
    return Pipeline([("validate", FeatureValidator()), ("columns", columns)])


def prepare_development(X_train, X_validation):
    """No test input or labels accepted. Fit each preprocessor only on X_train."""
    result = {}
    for kind in ("lr", "rf"):
        preprocessor = build_preprocessor(kind)
        train = preprocessor.fit_transform(X_train)
        validation = preprocessor.transform(X_validation)
        result[kind] = (preprocessor, train, validation)
    return result
