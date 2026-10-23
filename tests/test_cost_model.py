"""Hand-computable synthetic cases, never project data."""

import json

import numpy as np
import pytest

from src.cost_model import EvaluationInputError, observed_cost, savings
from src.evaluation import evaluate_policy


@pytest.mark.parametrize("y,a,cost", [(0, 0, 0), (0, 1, 1), (1, 0, 20), (1, 1, 5)])
def test_four_hand_computed_cells(y, a, cost):
    assert observed_cost([y], [a]) == pytest.approx(cost)


def test_aggregate_formula_and_residual_failure_cost():
    y, a = [0, 0, 1, 1], [0, 1, 0, 1]
    assert observed_cost(y, a) == pytest.approx(26)
    assert observed_cost(y, a) == pytest.approx(2 + 20 * 2 - 16)
    assert observed_cost(y, a) == pytest.approx(sum(observed_cost([yi], [ai]) for yi, ai in zip(y, a)))


@pytest.mark.parametrize("eta,cost", [(0, 42), (1, 22)])
def test_eta_domain_boundaries(eta, cost):
    assert observed_cost([0, 0, 1, 1], [0, 1, 0, 1], eta=eta) == pytest.approx(cost)


@pytest.mark.parametrize("y,a", [([], []), ([[1]], [1]), ([1], [1, 0]), ([2], [1]),
                                  ([0.5], [1]), ([1], [-1]), ([1], [np.nan]),
                                  ([np.inf], [0]), (["1"], [0]), ([1 + 0j], [0])])
def test_reject_invalid_inputs(y, a):
    with pytest.raises(EvaluationInputError):
        observed_cost(y, a)


@pytest.mark.parametrize("kw", [{"c_pm": -1}, {"c_f": np.inf}, {"eta": 1.01}, {"eta": -0.1},
                                {"c_pm": True}, {"eta": "0.8"}])
def test_reject_invalid_parameters(kw):
    with pytest.raises(EvaluationInputError):
        observed_cost([1], [1], **kw)


@pytest.mark.parametrize("reference,cost,absolute,percent", [(20, 5, 15, 75), (20, 21, -1, -5),
                                                          (20, 20, 0, 0), (0, 1, -1, None)])
def test_positive_negative_and_zero_reference_saving(reference, cost, absolute, percent):
    result = savings(reference, cost)
    assert result["absolute_saving"] == absolute
    assert result["saving_pct"] == percent
    assert result["saving_pct_reason"] == ("ZERO_REFERENCE_COST" if reference == 0 else None)


def test_no_positives_and_no_actions_metric_nulls():
    result = evaluate_policy([0, 0], [0, 0], [0.1, 0.2])
    for name, reason in {"precision": "NO_PREDICTED_POSITIVES", "recall": "NO_POSITIVES",
                         "f1": "NO_TRUE_OR_PREDICTED_POSITIVES", "roc_auc": "SINGLE_CLASS",
                         "average_precision": "NO_POSITIVES", "saving_pct": "ZERO_REFERENCE_COST"}.items():
        assert result[name] is None and result[name + "_reason"] == reason
    assert result["brier_score"] == pytest.approx(0.025)
    assert result["total_cost"] == 0 and result["feasible"]
    assert '"recall": null' in json.dumps(result, allow_nan=False)


@pytest.mark.parametrize("y,a", [([1, 0], [0, 0]), ([0, 0], [1, 0])])
def test_f1_zero_when_exactly_one_denominator_count_is_zero(y, a):
    assert evaluate_policy(y, a)["f1"] == 0


def test_no_positives_still_computes_infeasible_cost():
    result = evaluate_policy([0] * 10, [1] * 10)
    assert result["total_cost"] == 10 and not result["feasible"]
    assert result["constraint_excess"] == 9 and result["absolute_saving"] == -10
    assert result["recall"] is None


def test_all_positive_scores():
    result = evaluate_policy([1, 1], [0, 1], [0.3, 0.8])
    assert result["average_precision"] == 1
    assert result["roc_auc"] is None and result["roc_auc_reason"] == "SINGLE_CLASS"
    assert result["brier_score"] == pytest.approx(0.265)


def test_confusion_and_score_metrics_hand_computed():
    result = evaluate_policy([0, 1, 1, 0], [0, 1, 0, 1], [0.1, 0.9, 0.4, 0.7])
    assert [result[k] for k in ("tp", "fp", "fn", "tn")] == [1, 1, 1, 1]
    assert [result[k] for k in ("precision", "recall", "f1")] == [0.5] * 3
    assert result["average_precision"] == pytest.approx((1 + 2 / 3) / 2)
    assert result["roc_auc"] == 0.75
    assert result["brier_score"] == pytest.approx(0.2175)
    assert result["cost_per_observation"] == pytest.approx(6.5)


def test_policy_without_scores_does_not_invent_probabilities():
    result = evaluate_policy([0, 1], [0, 0])
    for name in ("average_precision", "roc_auc", "brier_score"):
        assert result[name] is None and result[name + "_reason"] == "NO_PROBABILITY_MODEL"


@pytest.mark.parametrize("p", [[0.2], [np.nan, 0.2], [-0.1, 0.2], [1.1, 0.2], [[0.1], [0.2]]])
def test_invalid_probability_metrics_rejected(p):
    with pytest.raises(EvaluationInputError):
        evaluate_policy([0, 1], [0, 1], p)
