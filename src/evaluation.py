"""A6 action metrics and probability metrics with explicit JSON null reasons."""

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from src.constraints import capacity
from src.cost_model import EvaluationInputError, observed_cost, paired, savings, vector


def evaluate_policy(y, actions, probabilities=None, *, c_pm=1.0, c_f=20.0, eta=0.8):
    y, actions = paired(y, actions)
    result = capacity(actions)
    n, m, positives = len(y), result["n_maintenance"], int(np.count_nonzero(y))
    tp = int(np.count_nonzero((y == 1) & (actions == 1)))
    fp, fn = m - tp, positives - tp
    result.update(tp=tp, fp=fp, fn=fn, tn=n - tp - fp - fn, n_positive=positives)
    result["total_cost"] = observed_cost(y, actions, c_pm=c_pm, c_f=c_f, eta=eta)
    result["cost_per_observation"] = result["total_cost"] / n
    reference = observed_cost(y, np.zeros(n), c_pm=c_pm, c_f=c_f, eta=eta)
    result.update(savings(reference, result["total_cost"]))

    def metric(name, value, reason=None):
        result[name], result[name + "_reason"] = value, reason

    metric("precision", tp / m if m else None, None if m else "NO_PREDICTED_POSITIVES")
    metric("recall", tp / positives if positives else None, None if positives else "NO_POSITIVES")
    metric("f1", 2 * tp / (positives + m) if positives + m else None,
           None if positives + m else "NO_TRUE_OR_PREDICTED_POSITIVES")
    if probabilities is None:
        for name in ("average_precision", "roc_auc", "brier_score"):
            metric(name, None, "NO_PROBABILITY_MODEL")
    else:
        p = vector(probabilities, "p", probability=True)
        if p.shape != y.shape:
            raise EvaluationInputError("y/p: shape mismatch")
        metric("average_precision", float(average_precision_score(y, p, pos_label=1))
               if positives else None, None if positives else "NO_POSITIVES")
        two_classes = 0 < positives < n
        metric("roc_auc", float(roc_auc_score(y, p)) if two_classes else None,
               None if two_classes else "SINGLE_CLASS")
        metric("brier_score", float(np.mean((p - y) ** 2)))
    return result
