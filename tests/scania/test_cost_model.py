"""Hand-computed synthetic cost oracles, C01–C06."""
import numpy as np
import pytest
from src.scania.cost_model import observed_aps_cost


@pytest.mark.parametrize("y,a,c", [(0, 0, 0), (0, 1, 10), (1, 0, 500), (1, 1, 0)])
def test_C01_four_cost_cells(y, a, c):
    assert observed_aps_cost([y], [a])["total_cost"] == c


def test_C02_hand_oracle_permutation():
    y = np.array([1, 1] + [0] * 18)
    a = np.array([1, 0, 1] + [0] * 17)
    r = observed_aps_cost(y, a)
    assert (r["TP"], r["FP"], r["FN"], r["TN"], r["total_cost"], r["absolute_saving"]) == (1, 1, 1, 17, 510, 490)
    assert observed_aps_cost(y[::-1], a[::-1]) == r


def test_C03_additive_cost():
    y, a = [0, 1, 1, 0], [1, 0, 1, 0]
    assert observed_aps_cost(y, a)["total_cost"] == sum(observed_aps_cost(y[i:i+2], a[i:i+2])["total_cost"] for i in (0, 2))


@pytest.mark.parametrize("y", [[0]*10, [1]*10, [0, 1]*5])
def test_C04_zero_all_perfect(y):
    n, p = len(y), sum(y)
    assert observed_aps_cost(y, [0]*n)["total_cost"] == 500*p
    assert observed_aps_cost(y, [1]*n)["total_cost"] == 10*(n-p)
    assert observed_aps_cost(y, y)["total_cost"] == 0


def test_C05_saving_sign_and_zero_reference():
    assert observed_aps_cost([0, 1], [1, 1])["absolute_saving"] == 490
    assert observed_aps_cost([0, 1], [1, 0])["absolute_saving"] == -10
    assert observed_aps_cost([0, 1], [0, 0])["absolute_saving"] == 0
    r = observed_aps_cost([0]*10, [1]+[0]*9)
    assert r["absolute_saving"] == -10 and r["saving_pct"] is None


@pytest.mark.parametrize("y,a", [([], []), ([[0]], [0]), ([0], [0, 1]), ([2], [0]),
                                  ([np.nan], [0]), ([0], [np.inf]), (["0"], [0]), ([0], [-1])])
def test_C06_cost_invalid_inputs(y, a):
    with pytest.raises(ValueError): observed_aps_cost(y, a)
