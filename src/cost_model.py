"""A2 observed, one-period simulated costs. Units are hypothetical cost units."""

from numbers import Real

import numpy as np


class EvaluationInputError(ValueError):
    """ERROR input, distinct from a valid but capacity-infeasible policy."""


def vector(value, name, *, binary=False, probability=False):
    array = np.asarray(value)
    if (array.ndim != 1 or not len(array) or array.dtype.kind not in "biuf"
            or not np.isfinite(array).all()):
        raise EvaluationInputError(f"{name}: expected nonempty finite numeric 1-D input")
    if binary and not np.isin(array, [0, 1]).all():
        raise EvaluationInputError(f"{name}: expected binary values")
    if probability and ((array < 0).any() or (array > 1).any()):
        raise EvaluationInputError(f"{name}: probabilities outside [0,1]")
    return array


def scalar(value, name, low=0, high=None):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, Real)
            or not np.isfinite(value) or value < low
            or (high is not None and value > high)):
        raise EvaluationInputError(f"{name}: invalid finite scalar/domain")
    return float(value)


def paired(y, actions):
    y = vector(y, "y", binary=True)
    actions = vector(actions, "actions", binary=True)
    if y.shape != actions.shape:
        raise EvaluationInputError("y/actions: shape mismatch")
    return y, actions


def observed_cost(y, actions, *, c_pm=1.0, c_f=20.0, eta=0.8):
    y, actions = paired(y, actions)
    c_pm, c_f, eta = (scalar(c_pm, "c_pm"), scalar(c_f, "c_f"),
                        scalar(eta, "eta", high=1))
    with np.errstate(over="ignore", invalid="ignore"):
        total = float(np.sum(c_pm * actions + c_f * y * (1 - eta * actions)))
    if not np.isfinite(total):
        raise EvaluationInputError("cost: nonfinite result")
    return total


def savings(reference_cost, policy_cost):
    reference_cost = scalar(reference_cost, "reference_cost")
    policy_cost = scalar(policy_cost, "policy_cost")
    absolute = reference_cost - policy_cost
    percent = 100 * absolute / reference_cost if reference_cost else None
    if percent is not None and not np.isfinite(percent):
        raise EvaluationInputError("saving_pct: nonfinite result")
    return {"absolute_saving": absolute, "saving_pct": percent,
            "saving_pct_reason": None if reference_cost else "ZERO_REFERENCE_COST"}
