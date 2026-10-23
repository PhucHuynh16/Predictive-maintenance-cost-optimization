"""A3 boundaries and ties on synthetic scores only; no real threshold search."""

import numpy as np
import pytest

from src.constraints import candidate_thresholds, capacity, select_candidate, threshold_actions
from src.cost_model import EvaluationInputError


@pytest.mark.parametrize("n,k", [(1, 0), (9, 0), (10, 1), (19, 1), (20, 2), (29, 2), (2000, 200)])
def test_integer_floor(n, k):
    assert capacity([0] * n)["capacity_k"] == k


def test_infeasible_is_valid_input_and_not_repaired():
    actions = np.array([1] * 3 + [0] * 17)
    original = actions.copy()
    result = capacity(actions)
    assert not result["feasible"] and result["constraint_excess"] == 1
    assert result["constraint_excess_rate"] == 0.05 and result["maintenance_rate"] == 0.15
    np.testing.assert_array_equal(actions, original)
    assert capacity([1] + [0] * 9)["feasible"]


@pytest.mark.parametrize("a", [[], [[0, 1]], [0, 2], [0, np.inf], [0, "1"]])
def test_invalid_is_error_not_infeasible(a):
    with pytest.raises(EvaluationInputError):
        capacity(a)


def test_exact_ties_and_endpoints():
    p = [0, 0.5, 0.5, 1]
    assert threshold_actions(p, 0).tolist() == [1, 1, 1, 1]
    assert threshold_actions(p, 0.5).tolist() == [0, 1, 1, 1]
    assert threshold_actions(p, 1).tolist() == [0, 0, 0, 1]
    assert not capacity(threshold_actions([1] * 10, 1))["feasible"]


def test_candidate_exact_no_rounding():
    next_score = np.nextafter(0.5, 1)
    p = [next_score, 0.5, next_score]
    np.testing.assert_array_equal(candidate_thresholds(p), [0, 0.5, next_score, 1])
    assert threshold_actions(p, next_score).tolist() == [1, 0, 1]


@pytest.mark.parametrize("p,t", [([], 0.5), ([np.nan], 0.5), ([1.1], 0.5), ([0.2], -0.1),
                                 ([0.2], 1.1), ([0.2], True), ([0.2], np.inf)])
def test_invalid_threshold_input(p, t):
    with pytest.raises(EvaluationInputError):
        threshold_actions(p, t)


def row(h="a", threshold=0.5, cost=10, m=1, feasible=True):
    return dict(h=h, threshold=threshold, total_cost=cost, n_maintenance=m, feasible=feasible)


def test_no_feasible_not_replaced_by_b0():
    result = select_candidate([row(feasible=False)], ["a"])
    assert result == {"best": None, "status": "NO_FEASIBLE_CANDIDATE", "h_scope": ["a"], "candidate_count": 1}


def test_select_only_feasible_minimum():
    result = select_candidate([row(cost=0, feasible=False), row(threshold=0.7, cost=11)], ["a"])
    assert result["best"]["total_cost"] == 11


def test_tiebreak_m_threshold_then_registered_h_not_arrival():
    records = [row("b", 0.9, 10, 1), row("a", 0.5, 10, 1), row("a", 0.7, 10, 1), row("a", 0.8, 10, 2)]
    result = select_candidate(records, ["a", "b"])
    assert result["best"] == row("a", 0.7, 10, 1)
    assert select_candidate(list(reversed(records)), ["a", "b"])["best"] == result["best"]


def test_tolerance_against_global_minimum_not_chain():
    records = [row("a", cost=1, m=3), row("b", cost=1 + 0.75e-9, m=2), row("c", cost=1 + 1.5e-9, m=1)]
    assert select_candidate(records, ["a", "b", "c"])["best"]["h"] == "b"


def test_invalid_candidates():
    with pytest.raises(EvaluationInputError):
        select_candidate([row(cost=np.nan)], ["a"])
    with pytest.raises(EvaluationInputError):
        select_candidate([row(), row()], ["a"])
