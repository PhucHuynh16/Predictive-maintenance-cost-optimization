"""Observed APS benchmark cost. No AI4I economic assumptions."""
import numpy as np


def binary_vector(value, name="binary"):
    a = np.asarray(value)
    if (a.ndim != 1 or a.size == 0 or a.dtype.kind not in "biuf"
            or not np.isfinite(a).all() or not np.isin(a, [0, 1]).all()):
        raise ValueError(f"ERROR_INVALID_{name.upper()}")
    return a.astype(np.int8, copy=False)


def observed_aps_cost(y, actions):
    y, a = binary_vector(y, "labels"), binary_vector(actions, "actions")
    if y.shape != a.shape:
        raise ValueError("ERROR_SHAPE_MISMATCH")
    tp = int(np.count_nonzero((y == 1) & (a == 1)))
    fp = int(np.count_nonzero((y == 0) & (a == 1)))
    fn = int(np.count_nonzero((y == 1) & (a == 0)))
    tn = int(np.count_nonzero((y == 0) & (a == 0)))
    cost = 10 * fp + 500 * fn
    reference = 500 * int(np.count_nonzero(y))
    return dict(N=len(y), P=tp + fn, TP=tp, FP=fp, FN=fn, TN=tn,
                cost_fp=10 * fp, cost_fn=500 * fn, total_cost=cost,
                cost_per_observation=cost / len(y), reference_cost=reference,
                absolute_saving=reference - cost,
                saving_pct=100 * (reference - cost) / reference if reference else None)
