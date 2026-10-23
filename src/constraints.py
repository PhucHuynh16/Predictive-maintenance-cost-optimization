"""A3 capacity, exact threshold boundaries and deterministic candidate selection.

Candidate helpers are tested on synthetic fixtures only at G4; no threshold
selection is performed for the fixed baselines.
"""

import numpy as np

from src.cost_model import EvaluationInputError, scalar, vector


def capacity(actions):
    actions = vector(actions, "actions", binary=True)
    n, m = len(actions), int(np.count_nonzero(actions))
    k = n // 10  # Exact floor(N/10), locked b=0.10. Never sum sub-batch floors.
    excess = max(0, m - k)
    return {"n": n, "n_maintenance": m, "capacity_k": k,
            "maintenance_rate": m / n, "constraint_excess": excess,
            "constraint_excess_rate": excess / n, "feasible": excess == 0}


def threshold_actions(probabilities, threshold):
    p = vector(probabilities, "p", probability=True)
    threshold = scalar(threshold, "threshold", high=1)
    return (p >= threshold).astype(np.int8)


def candidate_thresholds(probabilities):
    p = vector(probabilities, "p", probability=True)
    return np.unique(np.concatenate(([0.0, 1.0], p)))


def select_candidate(candidates, h_order):
    """Select among already scored Validation candidates using A3-g.

    Caller supplies registered H order, never completion/arrival order. No model
    fit or search here. Return no-feasible explicitly, without a B0 substitution.
    """
    h_order = list(h_order)
    if not h_order or len(set(h_order)) != len(h_order):
        raise EvaluationInputError("h_order: expected nonempty unique registered order")
    candidates = list(candidates)
    feasible = []
    seen = set()
    for row in candidates:
        if row["h"] not in h_order:
            raise EvaluationInputError("candidate h outside registered scope")
        scalar(row["threshold"], "threshold", high=1)
        scalar(row["total_cost"], "total_cost")
        if not isinstance(row["feasible"], (bool, np.bool_)):
            raise EvaluationInputError("candidate feasibility must be boolean")
        m = row["n_maintenance"]
        if isinstance(m, bool) or not isinstance(m, (int, np.integer)) or m < 0:
            raise EvaluationInputError("candidate M must be a nonnegative integer")
        key = (row["h"], row["threshold"])
        if key in seen:
            raise EvaluationInputError("duplicate h/threshold candidate")
        seen.add(key)
        if row["feasible"]:
            feasible.append(row)
    result = {"candidate_count": len(candidates), "h_scope": h_order}
    if not feasible:
        return dict(result, best=None, status="NO_FEASIBLE_CANDIDATE")
    minimum = min(row["total_cost"] for row in feasible)
    tied = [r for r in feasible if abs(r["total_cost"] - minimum) <= 1e-9]
    m = min(r["n_maintenance"] for r in tied)
    tied = [r for r in tied if r["n_maintenance"] == m]
    # Resolve threshold only within the same h, then use registered h order.
    best_h = next(h for h in h_order if any(r["h"] == h for r in tied))
    best = max((r for r in tied if r["h"] == best_h), key=lambda r: r["threshold"])
    return dict(result, best=best.copy(), status="FEASIBLE_CANDIDATE")
