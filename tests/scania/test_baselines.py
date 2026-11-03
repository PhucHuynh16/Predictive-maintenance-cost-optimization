from unittest.mock import Mock
import warnings
import numpy as np
import pytest
from sklearn.exceptions import ConvergenceWarning
from src.scania import baselines as b
from src.scania.constraints import POLICIES, actions_from_probabilities


def test_B01_full_stump_params_and_root_only():
    m = b.build_baseline("B1")
    assert m.get_params() == b.STUMP_PARAMS
    # Synthetic constant features, balanced labels: root-only p=.5.
    m.fit(np.zeros((20,2)),[0,1]*10)
    assert m.tree_.max_depth == 0
    p = m.predict_proba(np.zeros((2,2)))[:,list(m.classes_).index(1)]
    assert p.tolist() == [.5,.5]
    assert actions_from_probabilities(p,.5).tolist() == [1,1]
    assert m.predict(np.zeros((2,2))).tolist() == [0,0]
    assert b.build_baseline("B0") is None


def test_B02_lr_params_no_preprocessing_and_one_predict(monkeypatch):
    lr = b.build_baseline("B2")
    assert all(lr.get_params()[k] == v for k,v in b.LR_PARAMS.items())
    import src.scania.preprocessing as preprocessing
    monkeypatch.setattr(preprocessing,"build_preprocessor",Mock(side_effect=AssertionError("no preprocessing refit")))
    fake = Mock(classes_=np.array([0,1]))
    fake.predict_proba.return_value = np.tile([.8,.2],(20,1))
    fake.get_params.return_value = b.LR_PARAMS
    monkeypatch.setattr(b,"build_baseline",lambda name:fake)
    x,y,v,yv = b.synthetic_fixture()
    p,r = b.fit_predict_synthetic("B2",x,y,v,mode="SYNTHETIC_FIXTURE")
    import json
    json.dumps(r, allow_nan=False)  # sklearn numpy class labels must be JSON scalars.
    assert fake.fit.call_count == 1 and fake.predict_proba.call_count == 1
    assert fake.fit.call_args.args[0] is x
    for tau in POLICIES.values(): actions_from_probabilities(p,tau)
    assert fake.fit.call_count == 1


@pytest.mark.parametrize("fault",["warning","nan","domain","class"])
def test_B02_warning_invalid_probability_no_retry(monkeypatch,fault):
    fake = Mock(classes_=np.array([0,1]))
    fake.predict_proba.return_value = np.tile([.8,.2],(20,1))
    if fault == "warning":
        fake.fit.side_effect = lambda *args: warnings.warn("synthetic nonconvergence",ConvergenceWarning)
    if fault == "nan": fake.predict_proba.return_value[0] = [np.nan,np.nan]
    if fault == "domain": fake.predict_proba.return_value[0] = [-.2,1.2]
    if fault == "class": fake.classes_ = np.array([0])
    monkeypatch.setattr(b,"build_baseline",lambda name:fake)
    x,y,v,_ = b.synthetic_fixture()
    with pytest.raises(RuntimeError): b.fit_predict_synthetic("B2",x,y,v,mode="SYNTHETIC_FIXTURE")
    assert fake.fit.call_count == 1


def test_B02_real_fit_gate_b_closed_before_constructor(monkeypatch):
    spy = Mock(side_effect=AssertionError("must not construct"))
    monkeypatch.setattr(b,"build_baseline",spy)
    x,y,v,_ = b.synthetic_fixture()
    with pytest.raises(PermissionError): b.fit_predict_synthetic("B2",x,y,v,mode="PRODUCTION")
    with pytest.raises(ValueError): b.fit_predict_synthetic("B2",np.zeros((48000,1)),np.zeros(48000),v,mode="SYNTHETIC_FIXTURE")
    spy.assert_not_called()
