"""Five fixed policy rows; no selection between PRIMARY and SECONDARY."""
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score
from .cost_model import observed_aps_cost
from .constraints import capacity_report, probabilities


def evaluate_aps_policy(y, actions, scores=None, *, baseline_id, role, threshold=None):
    if baseline_id not in ("B0", "B1", "B2"):
        raise ValueError("ERROR_BASELINE_ID")
    r = observed_aps_cost(y, actions)
    r.update(capacity_report(actions), baseline_id=baseline_id, role=role, threshold=threshold)
    reasons = {}
    n, p, m, tp = r["N"], r["P"], r["M"], r["TP"]
    r["precision"] = tp / m if m else None
    r["recall"] = tp / p if p else None
    r["f1"] = 2 * tp / (p + m) if p + m else None
    if not m: reasons["precision"] = "NO_PREDICTED_POSITIVES"
    if not p: reasons["recall"] = "NO_POSITIVES"
    if not p + m: reasons["f1"] = "NO_TRUE_OR_PREDICTED_POSITIVES"
    if not r["reference_cost"]: reasons["saving_pct"] = "ZERO_REFERENCE_COST"
    if baseline_id == "B0":
        if scores is not None or m or role != "REFERENCE" or threshold is not None:
            raise ValueError("ERROR_B0_NO_PROBABILITY_MODEL")
        for key in ("average_precision", "roc_auc", "brier"):
            r[key], reasons[key] = None, "NO_PROBABILITY_MODEL"
    else:
        s = probabilities(scores)
        if len(s) != n:
            raise ValueError("ERROR_SCORE_SHAPE")
        r["average_precision"] = float(average_precision_score(y, s)) if p else None
        if not p: reasons["average_precision"] = "NO_POSITIVES"
        r["roc_auc"] = float(roc_auc_score(y, s)) if 0 < p < n else None
        if p in (0, n): reasons["roc_auc"] = "SINGLE_CLASS"
        r["brier"] = float(np.mean((s - np.asarray(y)) ** 2))
    r["reasons"] = reasons
    return r
