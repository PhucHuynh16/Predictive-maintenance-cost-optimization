from pathlib import Path
import json
from unittest.mock import Mock
import pytest
import scripts.run_scania_baselines as runner
from src.scania.g4_artifacts import EvidenceRun, verify_run, summarize_junit
from src.scania import g4_contract as contract
from src.scania.baselines import synthetic_fixture

ROOT = Path(__file__).resolve().parents[2]


def fixture_runtime(monkeypatch):
    config = contract.load_config(ROOT)
    monkeypatch.setattr(runner,"load_config",lambda root:config)
    monkeypatch.setattr(runner,"code_digest",lambda root:"fixture-code")
    monkeypatch.setattr(runner,"git",lambda root,*args:b"fixture-commit\n" if args[0]=="rev-parse" else b"")


@pytest.mark.parametrize("stage",["config","test_gate","missing_raw","wrong_hash","fit","warning","predict","metrics","gate_b"])
def test_R01_failure_finalization_end_to_end(tmp_path,monkeypatch,stage):
    fixture_runtime(monkeypatch)
    mode = "SYNTHETIC_FIXTURE"
    def fail(*args,**kwargs): raise RuntimeError("synthetic failure: "+stage)
    if stage == "config": monkeypatch.setattr(runner,"load_config",fail)
    elif stage in ("test_gate","missing_raw","wrong_hash"):
        mode = "READ_ONLY_PREFLIGHT"
        if stage == "test_gate": monkeypatch.setattr(runner,"verify_test_evidence",fail)
        else:
            monkeypatch.setattr(runner,"verify_test_evidence",lambda *args:{"fixture":"synthetic evidence"})
            def preflight(*args):
                if stage == "missing_raw": raise FileNotFoundError("synthetic Train absent")
                raise contract.Blocked("SOURCE_HASH_MISMATCH fixture")
            monkeypatch.setattr(runner,"verify_frozen_inputs",preflight)
    elif stage == "fit": monkeypatch.setattr(runner.baselines,"fit_predict_synthetic",fail)
    elif stage == "warning":
        import warnings
        from sklearn.exceptions import ConvergenceWarning
        fake = Mock(classes_=[0,1])
        fake.fit.side_effect = lambda *args: warnings.warn("synthetic warning", ConvergenceWarning)
        monkeypatch.setattr(runner.baselines,"build_baseline",lambda name:fake)
    elif stage == "predict":
        from src.scania import baselines as b
        fake = Mock(classes_=[0,1]); fake.predict_proba.side_effect = RuntimeError("predict fixture error")
        monkeypatch.setattr(b,"build_baseline",lambda name:fake)
    elif stage == "metrics": monkeypatch.setattr(runner.baselines,"fixed_policy_rows",fail)
    else: mode = "PRODUCTION"
    # A previous valid fixture is not overwritten or used as a latest PASS.
    old = EvidenceRun(tmp_path,"old")
    old.json("run_summary.json",{"status":"old fixture"})
    old_bytes = (old.path/"run_summary.json").read_bytes()
    with pytest.raises(Exception): runner.run_gate_a(tmp_path,run_id="new",mode=mode)
    p = tmp_path/"results/scania_aps/g4/new"
    summary = json.loads((p/"run_summary.json").read_text())
    assert summary["lifecycle"] == "FAILED" and summary["status"] in {"ERROR","FAILED","BLOCKED"}
    assert summary["real_estimator_fits"] == 0 and summary["real_validation_scored"] is False
    assert json.loads((p/"failure_diagnostics.json").read_text())["errors"][0]["uncomputed_metrics"]["reason"] == "NOT_COMPUTED"
    if stage == "warning":
        assert json.loads((p/"failure_diagnostics.json").read_text())["errors"][0]["warnings"][0]["category"] == "ConvergenceWarning"
    assert verify_run(p)
    assert (old.path/"run_summary.json").read_bytes() == old_bytes


def test_R01_readonly_preflight_never_fit_and_missing_evidence(tmp_path,monkeypatch):
    fixture_runtime(monkeypatch)
    spy = Mock(side_effect=AssertionError("no fit allowed"))
    monkeypatch.setattr(runner.baselines,"fit_predict_synthetic",spy)
    with pytest.raises(contract.Blocked): runner.run_gate_a(tmp_path,run_id="no_evidence",mode="READ_ONLY_PREFLIGHT")
    spy.assert_not_called()


def test_R02_two_synthetic_runs_stable_no_test_no_preprocess(tmp_path,monkeypatch):
    fixture_runtime(monkeypatch)
    import src.scania.preprocessing as pp
    import src.scania.data as data
    monkeypatch.setattr(pp,"build_preprocessor",Mock(side_effect=AssertionError("no refit")))
    monkeypatch.setattr(data,"official_split",Mock(side_effect=AssertionError("no split")))
    original = Path.open
    def no_test(p,*args,**kwargs):
        if p.name == "aps_failure_test_set.csv" or p.suffix == ".zip": raise AssertionError("Test access")
        return original(p,*args,**kwargs)
    monkeypatch.setattr(Path,"open",no_test)
    p1 = runner.run_gate_a(tmp_path,run_id="one",mode="SYNTHETIC_FIXTURE")
    p2 = runner.run_gate_a(tmp_path,run_id="two",mode="SYNTHETIC_FIXTURE")
    stable = lambda p:json.loads((p/"stable_manifest.json").read_text())
    assert stable(p1) == stable(p2) and verify_run(p1) and verify_run(p2)
    rows = json.loads((p1/"baseline_metrics.json").read_text())
    assert rows["kind"] == "SYNTHETIC_FIXTURE_NOT_REAL_RESULTS" and len(rows["rows"]) == 5


def test_R01_checksum_missing_tamper_crlf_and_path_escape(tmp_path,monkeypatch):
    fixture_runtime(monkeypatch)
    p = runner.run_gate_a(tmp_path,run_id="one",mode="SYNTHETIC_FIXTURE")
    f = p/"execution.txt"; original = f.read_bytes()
    f.write_bytes(original.replace(b"\n",b"\r\n"))
    assert verify_run(p)
    f.write_bytes(b"tampered")
    assert not verify_run(p)
    f.unlink()
    assert not verify_run(p)
    with pytest.raises(contract.Blocked): EvidenceRun(tmp_path,"../../g3/run")
    before = (p/"run_summary.json").read_bytes()
    with pytest.raises(contract.Blocked,match="RUN_ID_EXISTS"): EvidenceRun(tmp_path,"one")
    assert before == (p/"run_summary.json").read_bytes()


def test_R01_junit_summary_keeps_failed_and_missing_groups(tmp_path,monkeypatch):
    import src.scania.g4_artifacts as art
    monkeypatch.setattr(art,"code_digest",lambda root:"fixture")
    monkeypatch.setattr(art,"git",lambda *args:b"fixture-commit")
    p = tmp_path/"results/scania_aps/g4/junit.xml"
    p.parent.mkdir(parents=True)
    p.write_text('<testsuites><testsuite><testcase name="test_C01_example" time="0.1"/><testcase name="test_K01_error"><failure/></testcase></testsuite></testsuites>')
    out = summarize_junit(tmp_path,p,"summary")
    e = json.loads((out/"tests_summary.json").read_text())
    assert e["kind"] == "UNBOUND_HISTORICAL_JUNIT" and e["code_digest"] is None
    assert e["failures"] == 1 and e["passed"] == 1 and e["groups"]["K01"]["failure"] == 1
    assert not verify_run(out)  # Evidence-only record is not a complete Gate A run.
