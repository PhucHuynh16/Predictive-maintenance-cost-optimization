import numpy as np
import pytest
from sklearn.metrics import auc, precision_recall_curve
from src.scania.evaluation import evaluate_aps_policy as evaluate
from src.scania.baselines import fixed_policy_rows


def test_M01_undefined_and_reason_precedence():
    r = evaluate([0]*10,[0]*10,baseline_id="B0",role="REFERENCE")
    assert r["precision"] is None and r["recall"] is None and r["f1"] is None
    assert r["reasons"]["precision"] == "NO_PREDICTED_POSITIVES"
    assert r["reasons"]["saving_pct"] == "ZERO_REFERENCE_COST"
    assert all(r["reasons"][k] == "NO_PROBABILITY_MODEL" for k in ("average_precision","roc_auc","brier"))
    r = evaluate([0]*10,[1]*10,[.1]*10,baseline_id="B1",role="PRIMARY",threshold=.5)
    assert r["f1"] == 0 and r["brier"] == pytest.approx(.01)
    assert r["reasons"]["average_precision"] == "NO_POSITIVES"
    assert r["reasons"]["roc_auc"] == "SINGLE_CLASS"
    assert r["policy_status"] == "INFEASIBLE" and r["total_cost"] == 100
    r = evaluate([1]*10,[0]*10,[.2]*10,baseline_id="B2",role="SECONDARY",threshold=10/510)
    assert r["average_precision"] == 1 and r["brier"] == pytest.approx(.64) and r["f1"] == 0
    with pytest.raises(ValueError): evaluate([0],[0],[0.],baseline_id="B0",role="REFERENCE")


def test_M02_average_precision_not_trapezoid_or_hard_actions():
    y, p = [1,0,1], [.9,.8,.7]
    r = evaluate(y,[1,1,1],p,baseline_id="B1",role="PRIMARY",threshold=.5)
    precision, recall, _ = precision_recall_curve(y,p)
    assert r["average_precision"] == pytest.approx(5/6)
    assert r["average_precision"] != pytest.approx(auc(recall,precision))
    assert r["roc_auc"] == .5 and r["brier"] == pytest.approx((.01+.64+.09)/3)


def test_M02_five_fixed_rows_probability_metrics_shared():
    y, p = [1,0]*10, np.linspace(0,1,20)
    rows = fixed_policy_rows(y,{"B1":p,"B2":p[::-1]})
    assert [(r["baseline_id"],r["role"]) for r in rows] == [
        ("B0","REFERENCE"),("B1","PRIMARY"),("B2","PRIMARY"),("B1","SECONDARY"),("B2","SECONDARY")]
    assert rows[1]["average_precision"] == rows[3]["average_precision"]
    assert rows[1]["brier"] == rows[3]["brier"]
    assert rows[1]["threshold"] == .5 and rows[3]["threshold"] == 10/510
