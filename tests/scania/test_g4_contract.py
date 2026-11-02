"""Negative integrity tests are synthetic files, never official Test."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import Mock
import numpy as np
import pytest
from src.scania import g4_contract as c
from src.scania.contracts import canonical, object_hash
from src.scania.data import array_hash, ordered_ids_hash

ROOT = Path(__file__).resolve().parents[2]


def test_R01_locked_config_environment_and_protected_assets(tmp_path,monkeypatch):
    config = c.load_config(ROOT)
    assert config["gate_b_authorized"] is False
    assert c.protected_snapshot(ROOT)["files"] > 120
    p = tmp_path/"configs/scania/g4_baselines.json"
    p.parent.mkdir(parents=True)
    changed = deepcopy(config)
    changed["thresholds"]["SECONDARY"]["numerator"] = 11
    p.write_bytes(canonical(changed))
    with pytest.raises(c.Blocked,match="CONFIG_MISMATCH"): c.load_config(tmp_path)
    p.write_bytes(canonical(config))
    monkeypatch.setattr(c,"environment",lambda:{})
    with pytest.raises(c.Blocked,match="VERSION_MISMATCH"): c.load_config(tmp_path)


@pytest.mark.parametrize("path",["data/raw/scania_aps/aps_failure_test_set.csv", "source.zip",
                               "../Test.csv", "results/scania_aps/g4/../../Test.csv", "C:/Test.csv"])
def test_R01_no_test_path_before_open(tmp_path,path,monkeypatch):
    spy = Mock(side_effect=AssertionError("must not read Test"))
    monkeypatch.setattr(Path,"read_bytes",spy)
    with pytest.raises(c.Blocked): c.guarded_path(tmp_path,path,{"data/raw/scania_aps/aps_failure_training_set.csv"})
    spy.assert_not_called()


def test_R01_label_alignment_detects_swap_preserving_counts():
    t,v = np.array([2,0]),np.array([3,1])
    y = np.array([0,1,1,0],dtype=np.int8)
    manifest = dict(source_sha256="a"*64,train_ordered_ids_sha256=ordered_ids_hash(t,"a"*64),
                    validation_ordered_ids_sha256=ordered_ids_hash(v,"a"*64))
    assert set(c.validate_alignment(t,v,y[t],y[v],y,manifest)) == {"y_train","y_validation"}
    with pytest.raises(c.Blocked,match="LABEL_SOURCE"): c.validate_alignment(t,v,y[t][::-1],y[v],y,manifest)
    with pytest.raises(c.Blocked,match="COVERAGE"): c.validate_alignment(t,t,y[t],y[t],y,manifest)
    with pytest.raises(c.Blocked,match="ORDERED_IDS"): c.validate_alignment(t[::-1],v,y[t][::-1],y[v],y,manifest)


@pytest.mark.parametrize("fault",["hash","dtype","shape","nonfinite"])
def test_R01_frozen_matrix_tampering(tmp_path,fault):
    a = np.arange(12,dtype=float).reshape(4,3)
    sha = array_hash(a)
    if fault == "hash": a[0,0] = 99
    if fault == "dtype": a = a.astype(np.float32)
    if fault == "shape": a = a.reshape(3,4)
    if fault == "nonfinite": a[0,0] = np.nan
    p = tmp_path/"matrix.npy"
    np.save(p,a,allow_pickle=False)
    with pytest.raises(c.Blocked,match="MATRIX"): c.verify_matrix(p,sha,(4,3))


def test_R01_matrix_readonly_preserved(tmp_path):
    p = tmp_path/"matrix.npy"
    a = np.arange(12,dtype=float).reshape(4,3)
    np.save(p,a,allow_pickle=False)
    before = p.read_bytes()
    assert c.verify_matrix(p,array_hash(a),(4,3))
    assert before == p.read_bytes()


def test_R01_evidence_defaults_absent_and_stale(tmp_path):
    with pytest.raises(c.Blocked,match="MISSING"): c.verify_test_evidence(tmp_path,None)
    p = tmp_path/"results/scania_aps/g4/fake/tests_summary.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps(dict(kind="PYTEST_JUNIT",code_digest="stale",groups={},cases=[])))
    with pytest.raises(c.Blocked): c.verify_test_evidence(tmp_path,p.relative_to(tmp_path).as_posix())


@pytest.mark.parametrize("fault", ["source", "config", "failed", "missing_group", "boolean", "empty", "version"])
def test_R01_current_evidence_required_not_fixture_boolean(tmp_path,monkeypatch,fault):
    monkeypatch.setattr(c,"code_digest",lambda root:"fixture-source")
    groups = ["C01","C02","C03","C04","C05","C06","K01","K02","K03","K04",
              "M01","M02","B01","B02","R01","R02",*[f"G3{i:02d}" for i in range(1,11)]]
    cases = [dict(name="test_"+g+"_fixture",status="passed") for g in groups]
    e = dict(kind="PYTEST_JUNIT",source_binding="CAPTURED_BEFORE_PYTEST",execution={"pytest_exit_code":0},
             code_digest="fixture-source",config_sha256=c.CONFIG_SHA,
             environment=c.environment(),failures=0,errors=0,skipped=0,passed=len(cases),cases=cases,
             groups={g:dict(passed=1) for g in groups})
    p = tmp_path/"results/scania_aps/g4/evidence/tests_summary.json"
    p.parent.mkdir(parents=True)
    p.write_bytes(canonical(e))
    assert c.verify_test_evidence(tmp_path,p.relative_to(tmp_path).as_posix())["passed"] == 26
    if fault == "source": e["code_digest"] = "stale"
    if fault == "config": e["config_sha256"] = "wrong"
    if fault == "failed": e["cases"][0]["status"] = "failure"
    if fault == "missing_group": del e["groups"]["K04"]
    if fault == "boolean": e["failures"] = False
    if fault == "empty": e["cases"] = []
    if fault == "version": e["environment"] = {}
    p.write_bytes(canonical(e))
    with pytest.raises(c.Blocked): c.verify_test_evidence(tmp_path,p.relative_to(tmp_path).as_posix())


def test_R01_alias_rejected_before_read(tmp_path,monkeypatch):
    relative = "data/processed/scania_aps/frozen.npy"
    target = tmp_path/relative
    original = Path.resolve
    monkeypatch.setattr(Path,"resolve",lambda p,*a,**kw:tmp_path/"Test.csv" if p==target else original(p,*a,**kw))
    with pytest.raises(c.Blocked,match="ALIAS"): c.guarded_path(tmp_path,relative,{relative})


def test_R01_protected_mutation_on_fixture_git(tmp_path):
    import subprocess
    subprocess.run(["git","init","-q",str(tmp_path)],check=True)
    (tmp_path/"asset.txt").write_text("accepted\n")
    subprocess.run(["git","add","asset.txt"],cwd=tmp_path,check=True)
    subprocess.run(["git","-c","user.name=Fixture","-c","user.email=fixture@example.invalid","commit","-qm","fixture"],cwd=tmp_path,check=True)
    sha = c.git(tmp_path,"rev-parse","HEAD").decode().strip()
    # Override only pinned base in this isolated synthetic repository.
    from unittest.mock import patch
    with patch.object(c,"BASE",sha):
        assert c.protected_snapshot(tmp_path)["files"] == 1
        (tmp_path/"asset.txt").write_text("tampered\n")
        with pytest.raises(c.Blocked,match="PROTECTED"): c.protected_snapshot(tmp_path)
