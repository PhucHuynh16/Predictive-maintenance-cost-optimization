"""Exact threshold/capacity contract; candidate helpers are synthetic-only in G4."""
import math
from numbers import Real
import numpy as np
from .cost_model import binary_vector

PRIMARY = 0.5
SECONDARY = 10 / 510
POLICIES = {"PRIMARY": PRIMARY, "SECONDARY": SECONDARY}


def probabilities(value):
    p = np.asarray(value)
    if (p.ndim != 1 or not p.size or p.dtype.kind not in "iuf"
            or not np.isfinite(p).all() or np.any((p < 0) | (p > 1))):
        raise ValueError("ERROR_INVALID_PROBABILITIES")
    return p.astype(np.float64, copy=False)


def actions_from_probabilities(p, tau):
    p = probabilities(p)
    if (isinstance(tau, (bool, np.bool_)) or not isinstance(tau, Real)
            or not np.isscalar(tau) or not math.isfinite(float(tau)) or not 0 <= tau <= 1):
        raise ValueError("ERROR_INVALID_THRESHOLD")
    return (p >= tau).astype(np.int8)


def capacity_report(actions):
    a = binary_vector(actions, "actions")
    n, m = len(a), int(np.count_nonzero(a))
    k = n // 10
    excess = max(0, m - k)
    return dict(M=m, K=k, maintenance_rate=m / n, excess=excess,
                excess_rate=excess / n, feasible=excess == 0,
                policy_status="FEASIBLE" if not excess else "INFEASIBLE")


def threshold_candidates(p):
    """Contract helper, never called on real Validation by Gate A runner."""
    return np.unique(np.concatenate(([0., 1.], probabilities(p)))).tolist()


def select_candidate(rows, registered_h_order):
    """Synthetic contract: global-min tolerance; registered H before cross-H tie."""
    order = list(registered_h_order)
    if len(set(order)) != len(order):
        raise ValueError("ERROR_H_ORDER")
    for r in rows:
        if (r["h"] not in order or not math.isfinite(r["total_cost"])
                or r["total_cost"] < 0 or r["M"] < 0):
            raise ValueError("ERROR_CANDIDATE")
        actions_from_probabilities([0.], r["threshold"])
    feasible = [r for r in rows if r["feasible"]]
    if not feasible:
        return dict(status="NO_FEASIBLE_CANDIDATE", best=None,
                    candidate_count=len(rows), h_scope=order)
    minimum = min(r["total_cost"] for r in feasible)
    ties = [r for r in feasible if abs(r["total_cost"] - minimum) <= 1e-9]
    best = min(ties, key=lambda r: (r["M"], order.index(r["h"]), -r["threshold"]))
    return dict(status="SELECTED", best=best, candidate_count=len(rows), h_scope=order)
