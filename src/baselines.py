"""Fixed B0/B1/B2. No calibration, tuning, Test interface or Train+Val refit."""

import time
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from src.constraints import threshold_actions
from src.cost_model import EvaluationInputError, vector
from src.data import validate_features
from src.preprocessing import build_preprocessor

LR_PARAMS = {"C": 1.0, "l1_ratio": 0.0, "solver": "lbfgs", "dual": False,
             "fit_intercept": True, "tol": 1e-4, "max_iter": 2000,
             "class_weight": None, "random_state": 42, "warm_start": False,
             "verbose": 0, "n_jobs": None, "intercept_scaling": 1}


class BaselineFailure(RuntimeError):
    def __init__(self, reason, warning_records):
        self.warning_records = warning_records
        super().__init__(reason)


def reactive_actions(n):
    if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n <= 0:
        raise EvaluationInputError("B0: N must be a positive integer")
    return np.zeros(n, dtype=np.int8)


def fixed_wear_actions(features):
    validate_features(features)
    return (features["Tool wear [min]"].to_numpy() >= 200).astype(np.int8)


def build_b2():
    # l1_ratio=0 encodes L2 in the approved sklearn 1.9.1 API; omit penalty.
    return Pipeline([("preprocess", build_preprocessor("lr")),
                     ("model", LogisticRegression(**LR_PARAMS))])


def fit_b2_development(X_train, y_train, X_validation):
    """Fit exactly once on Train. Validation labels cannot enter this function."""
    validate_features(X_train)
    validate_features(X_validation)
    y_train = vector(y_train, "y_train", binary=True)
    if len(y_train) != len(X_train) or len(np.unique(y_train)) != 2:
        raise EvaluationInputError("B2 Train requires matching rows and two classes")
    model = build_b2()
    start = time.perf_counter()
    captured = []
    try:
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            model.fit(X_train, y_train)
            fit_seconds = time.perf_counter() - start
            if any(issubclass(w.category, ConvergenceWarning) for w in captured):
                raise EvaluationInputError("B2 ConvergenceWarning; no automatic retry authorized")
            prediction_start = time.perf_counter()
            index = np.flatnonzero(model.classes_ == 1)
            if len(index) != 1:
                raise EvaluationInputError("B2 missing probability class 1")
            output = np.asarray(model.predict_proba(X_validation))
            if output.shape != (len(X_validation), 2):
                raise EvaluationInputError("B2 invalid probability matrix shape")
            for column in output.T:
                vector(column, "B2 probability", probability=True)
            if not np.allclose(output.sum(axis=1), 1, rtol=0, atol=1e-12):
                raise EvaluationInputError("B2 probability rows do not sum to 1")
            p = output[:, index[0]]
            actions = threshold_actions(p, 0.5)
            if any(issubclass(w.category, ConvergenceWarning) for w in captured):
                raise EvaluationInputError("B2 ConvergenceWarning; no automatic retry authorized")
            prediction_seconds = time.perf_counter() - prediction_start
    except Exception as exc:
        warning_records = [{"category": w.category.__name__, "message": str(w.message)} for w in captured]
        raise BaselineFailure(str(exc), warning_records) from exc
    return {"model": model, "probabilities": p, "actions": actions,
            "fit_seconds": fit_seconds, "prediction_seconds": prediction_seconds,
            "warnings": [{"category": w.category.__name__, "message": str(w.message)} for w in captured]}
