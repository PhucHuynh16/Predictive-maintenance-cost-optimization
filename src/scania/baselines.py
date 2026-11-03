"""Fixed constructors. Gate A fits only small, explicitly synthetic fixtures."""
import time
import warnings
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from .constraints import POLICIES, actions_from_probabilities, probabilities
from .cost_model import binary_vector
from .evaluation import evaluate_aps_policy

STUMP_PARAMS = dict(criterion="gini", splitter="best", max_depth=1,
                    min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0,
                    max_features=None, random_state=42, max_leaf_nodes=None,
                    min_impurity_decrease=0.0, class_weight=None, ccp_alpha=0.0,
                    monotonic_cst=None)
LR_PARAMS = dict(C=1.0, l1_ratio=0.0, solver="lbfgs", dual=False, fit_intercept=True,
                 tol=0.0001, max_iter=2000, class_weight=None, random_state=42,
                 warm_start=False, verbose=0)


class BaselineFailure(RuntimeError):
    def __init__(self, reason, recorded_warnings=()):
        super().__init__(reason)
        self.warnings = [dict(category=w.category.__name__, message=str(w.message)) for w in recorded_warnings]


def build_baseline(name):
    if name == "B0": return None
    if name == "B1": return DecisionTreeClassifier(**STUMP_PARAMS)
    if name == "B2": return LogisticRegression(**LR_PARAMS)
    raise ValueError("ERROR_BASELINE_ID")


def synthetic_fixture():
    """Deterministic fabricated observations, unrelated to either real dataset."""
    t = np.arange(60, dtype=float)
    x = np.column_stack((np.sin(t), np.cos(t / 2), (t % 7) / 7))
    y = (np.arange(60) % 5 == 0).astype(np.int8)
    return x[:40], y[:40], x[40:], y[40:]


def fit_predict_synthetic(name, x, y, validation, *, mode):
    """No real-data fit API in Gate A. CLI accepts only built-in fixture fits."""
    if mode != "SYNTHETIC_FIXTURE":
        raise PermissionError("GATE_B_NOT_AUTHORIZED")
    x, v = np.asarray(x), np.asarray(validation)
    y = binary_vector(y, "labels")
    if (x.ndim != 2 or v.ndim != 2 or x.shape[1] != v.shape[1]
            or not 1 <= len(x) <= 200 or not 1 <= len(v) <= 200
            or not 1 <= x.shape[1] <= 8 or len(y) != len(x)
            or x.dtype.kind not in "iuf" or v.dtype.kind not in "iuf"
            or not np.isfinite(x).all() or not np.isfinite(v).all()):
        raise ValueError("ERROR_SYNTHETIC_FIXTURE_LIMITS")
    model = build_baseline(name)
    if model is None: raise ValueError("B0_HAS_NO_ESTIMATOR")
    start = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x, y)
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise BaselineFailure("FAILED_CONVERGENCE_WARNING: " + "; ".join(str(w.message) for w in caught), caught)
    fitted = time.perf_counter() - start
    labels = list(model.classes_)
    if labels != [0, 1]: raise BaselineFailure("FAILED_CLASS_MAPPING", caught)
    start = time.perf_counter()
    proba = np.asarray(model.predict_proba(v))
    if proba.shape != (len(v), 2) or not np.isfinite(proba).all() or not np.allclose(proba.sum(1), 1):
        raise BaselineFailure("FAILED_INVALID_PROBABILITY_MATRIX", caught)
    try: p = probabilities(proba[:, labels.index(1)])
    except ValueError as exc: raise BaselineFailure("FAILED_INVALID_PROBABILITIES", caught) from exc
    return p, dict(fit_seconds=fitted, predict_seconds=time.perf_counter() - start,
                   warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught],
                   parameters=model.get_params(deep=False), classes=[int(label) for label in labels])


def fixed_policy_rows(y, scores):
    rows = [evaluate_aps_policy(y, np.zeros(len(y), dtype=np.int8),
                               baseline_id="B0", role="REFERENCE")]
    for role, threshold in POLICIES.items():
        for name in ("B1", "B2"):
            p = scores[name]
            rows.append(evaluate_aps_policy(y, actions_from_probabilities(p, threshold), p,
                        baseline_id=name, role=role, threshold=threshold))
    return rows
