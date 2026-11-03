import numpy as np
import pytest
from src.scania.constraints import (PRIMARY, SECONDARY, actions_from_probabilities,
                                    capacity_report, select_candidate, threshold_candidates)


@pytest.mark.parametrize("n,k", [(1,0),(9,0),(10,1),(19,1),(11999,1199),(12000,1200)])
def test_K01_floor_and_excess(n,k):
    a = np.ones(n, dtype=np.int8)
    r = capacity_report(a)
    assert r["K"] == k and r["excess"] == n-k and r["excess_rate"] == (n-k)/n
    assert capacity_report(np.zeros(n))["feasible"]


def test_K01_whole_partition_not_micro_batch_floors():
    assert capacity_report([0]*10)["K"] == 1
    assert sum(capacity_report([0]*5)["K"] for _ in range(2)) == 0


@pytest.mark.parametrize("tau", [PRIMARY, SECONDARY])
def test_K02_exact_thresholds_nextafter_and_ties(tau):
    p = np.array([np.nextafter(tau, 0), tau, tau, np.nextafter(tau, 1)])
    assert actions_from_probabilities(p, tau).tolist() == [0, 1, 1, 1]
    assert capacity_report(actions_from_probabilities(p, tau))["M"] == 3
    assert threshold_candidates(p) == sorted(set([0., 1., *p]))
    assert SECONDARY == 10/510 and SECONDARY != 0.019608


def test_K02_endpoints_and_b0_distinct():
    assert actions_from_probabilities([0.,1.],0).tolist() == [1,1]
    assert actions_from_probabilities([0.,1.],1).tolist() == [0,1]


def test_K03_no_feasible_scope_no_b0():
    p = [1.,1.]+[0.]*8
    rows = [dict(h="h1", threshold=t, total_cost=0, **capacity_report(actions_from_probabilities(p,t)))
            for t in threshold_candidates(p)]
    r = select_candidate(rows,["h1"])
    assert r == dict(status="NO_FEASIBLE_CANDIDATE", best=None, candidate_count=2, h_scope=["h1"])


def test_K04_global_min_no_chaining_registered_order():
    rows = [dict(h="a",total_cost=c,M=m,threshold=.5,feasible=True)
            for c,m in [(0,3),(.75e-9,2),(1.5e-9,0)]]
    assert select_candidate(rows,["a"])["best"]["M"] == 2
    rows = [dict(h=h,total_cost=100,M=1,threshold=t,feasible=True) for h,t in [("b",1),("a",.2),("a",.7)]]
    rows.append(dict(h="a", total_cost=0,M=10,threshold=.1,feasible=False))
    assert select_candidate(rows[::-1],["a","b"])["best"]["threshold"] == .7


@pytest.mark.parametrize("p,t", [([], .5), ([True],.5), ([[.5]],.5), ([np.nan],.5),
                                ([np.inf],.5), ([-.1],.5), ([1.1],.5), ([.5], True),
                                ([.5],np.inf), ([.5],-.1), ([.5],1.1), ([.5],.5+0j)])
def test_C06_invalid_probability_threshold(p,t):
    with pytest.raises(ValueError): actions_from_probabilities(p,t)
