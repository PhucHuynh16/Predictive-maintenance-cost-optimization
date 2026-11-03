"""B1 tests use fixed mock workers, never real Train/Validation or fitting."""
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from src.scania import g4_b1_contract as c
from src.scania import g4_b1_supervisor as s
from src.scania import g4_b1_worker as w
from src.scania import g4_b1_windows as win
from src.scania.g4_b1_evidence import Evidence, verify_evidence, write_json

ROOT = Path(__file__).resolve().parents[2]


class FakeJob:
    """Simulation only. Real Win32 integration is tested separately below."""
    cases = {}
    def __init__(self, argv, env, cwd, memory_bytes, active_limit):
        self.path = c.output_path(cwd, env["SC_G4_B1_RUN"])
        self.scenario = env["SC_G4_B1_SCENARIO"]
        self.pi = SimpleNamespace(pid=1234)
        self.active, self.closed, self.resumed, self.killed = 1, False, False, False
        type(self).cases[self.path.name] = self
    def limits(self): return dict(job_memory_bytes=512 * 1024**2, active_process_limit=2)
    def resume(self):
        self.resumed = True
        if self.scenario == "normal":
            write_json(self.path / "worker_result.json", dict(kind=c.profile("normal")["kind"],
                       scenario="normal", status="PASS", fixture_digest="fake-fixture",
                       real_estimator_fits=0, validation_scored=False))
            self.active = 0
    def poll(self): return 0 if self.scenario == "normal" else 37 if self.scenario == "crash" else None
    def accounting(self): return dict(active_processes=self.active)
    def terminate(self): self.active = 0; self.killed = True
    def wait_empty(self, seconds): return self.active == 0
    def close(self): self.closed = True


@pytest.fixture
def mock_runtime(monkeypatch):
    monkeypatch.setattr(s, "WindowsJob", FakeJob)
    monkeypatch.setattr(s, "protected_snapshot", lambda root: {"fixture": "protected"})
    monkeypatch.setattr(s, "source_manifest", lambda root: {"source_digest": "mock-source"})
    monkeypatch.setattr(s, "verify_environment", lambda root: {"kind": "MOCK_ENVIRONMENT"})
    monkeypatch.setattr(s, "memory_snapshot", lambda: {"available_physical_bytes": 1024**3})


def summary(path):
    return json.loads((path / "run_summary.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("mode", ["official", "reproduce", "fit", "test", "../data/raw/aps_failure_test_set.csv"])
def test_B1G01_no_real_entrypoint(tmp_path, mode):
    with pytest.raises(c.SafetyBlocked): c.real_execution_gate(authorized=True, mode=mode)
    with pytest.raises(c.SafetyBlocked): c.profile(mode)


@pytest.mark.parametrize("key,value", [("wall_seconds", 300), ("minimum_available_ram_bytes", 0),
        ("real_fitting_allowed", True), ("real_fitting_allowed", 0), ("job_memory_bytes", 4 * 1024**3), ("active_process_limit", 99)])
def test_B1G02_config_limits_are_test_profiles_not_owner_approval(tmp_path, mock_runtime, key, value):
    p = copy.deepcopy(c.profile("normal")); p[key] = value
    out = s.run_qualification(tmp_path, run_id="invalid", config=p)
    assert summary(out)["status"] == "BLOCKED" and not summary(out)["worker_started"]
    assert verify_evidence(out)


def test_B1G03_memory_gate_before_worker(tmp_path, mock_runtime, monkeypatch):
    monkeypatch.setattr(s, "memory_snapshot", lambda: {"available_physical_bytes": 1})
    factory = Mock(side_effect=AssertionError("must not spawn")); monkeypatch.setattr(s, "WindowsJob", factory)
    p = s.run_qualification(tmp_path, run_id="memory")
    assert summary(p)["status"] == "BLOCKED" and verify_evidence(p)
    factory.assert_not_called()


@pytest.mark.parametrize("scenario,status", [("normal", "PASS"), ("crash", "FAILED"), ("sleep", "FAILED")])
def test_B1G04_finalization_normal_crash_timeout(tmp_path, mock_runtime, scenario, status):
    p = s.run_qualification(tmp_path, run_id="case", scenario=scenario)
    r = summary(p); job = FakeJob.cases["case"]
    assert r["status"] == status and r["job_empty_verified"] and job.closed
    assert r["real_estimator_fits"] == 0 and r["validation_scored"] is False
    if scenario != "normal": assert job.killed
    assert verify_evidence(p)


def test_B1G05_cleanup_failure_never_pass(tmp_path, mock_runtime, monkeypatch):
    monkeypatch.setattr(FakeJob, "wait_empty", lambda *args: False)
    p = s.run_qualification(tmp_path, run_id="cleanup")
    assert summary(p)["status"] == "FAILED" and not summary(p)["job_empty_verified"]
    assert verify_evidence(p)


def test_B1G06_source_change_during_worker_stops(tmp_path, mock_runtime, monkeypatch):
    calls = []
    def changed(root):
        calls.append(1)
        return {"digest": "before" if len(calls) == 1 else "after"}
    monkeypatch.setattr(s, "protected_snapshot", changed)
    p = s.run_qualification(tmp_path, run_id="changed")
    assert summary(p)["status"] == "FAILED" and verify_evidence(p)


def test_B1G07_repeated_run_preserves_old_evidence(tmp_path, mock_runtime):
    p = s.run_qualification(tmp_path, run_id="same")
    previous = {f.name: f.read_bytes() for f in p.iterdir()}
    with pytest.raises(FileExistsError): s.run_qualification(tmp_path, run_id="same", scenario="crash")
    assert previous == {f.name: f.read_bytes() for f in p.iterdir()}


def test_B1G08_reproducibility_fixed_mock_only(tmp_path, mock_runtime):
    a = s.run_qualification(tmp_path, run_id="one")
    b = s.run_qualification(tmp_path, run_id="two")
    assert summary(a)["stable_digest"] == summary(b)["stable_digest"]
    assert verify_evidence(a) and verify_evidence(b)


@pytest.mark.parametrize("bad", [[], [{"user_api": "blas", "num_threads": 1}],
    [{"user_api": "blas", "internal_api": "openblas", "num_threads": 2, "filepath": "blas.dll"},
     {"user_api": "openmp", "internal_api": "openmp", "num_threads": 1, "filepath": "omp.dll"}],
    [{"user_api": "blas", "internal_api": "openblas", "num_threads": True, "filepath": "blas.dll"},
     {"user_api": "openmp", "internal_api": "openmp", "num_threads": 1, "filepath": "omp.dll"}]])
def test_B1G09_thread_evidence_fail_closed(bad):
    with pytest.raises(c.SafetyBlocked): c.verify_pools(bad, ["blas.dll", "omp.dll"])


def test_B1G10_all_pools_accounted_and_unknown_rejected():
    pools = [dict(user_api="blas", internal_api="openblas", num_threads=1, filepath="blas.dll"),
             dict(user_api="openmp", internal_api="openmp", num_threads=1, filepath="omp.dll")]
    assert c.verify_pools(pools, ["blas.dll", "omp.dll"])
    with pytest.raises(c.SafetyBlocked): c.verify_pools(pools, ["blas.dll", "omp.dll", "unknown.dll"])


def test_B1G11_environment_set_before_import_no_parent_mutation(monkeypatch):
    original = {"OMP_NUM_THREADS": "8", "OPENBLAS_NUM_THREADS": "99", "PYTHONPATH": "untrusted"}
    child = c.child_environment(original)
    assert all(child[k] == v for k, v in c.THREAD_ENV.items())
    assert original["OMP_NUM_THREADS"] == "8" and "PYTHONPATH" not in child
    monkeypatch.setenv("OMP_NUM_THREADS", "8")
    with pytest.raises(c.SafetyBlocked, match="THREAD_ENV"): w.thread_probe()


@pytest.mark.parametrize("run_id", ["../g3/run", "data/raw/Test", "a\\b", "", "a" * 73])
def test_B1G12_output_scope(tmp_path, run_id):
    with pytest.raises(c.SafetyBlocked): c.output_path(tmp_path, run_id)


def test_B1G13_checksum_missing_extra_tamper_crlf(tmp_path, mock_runtime):
    p = s.run_qualification(tmp_path, run_id="check")
    f = p / "journal.jsonl"; original = f.read_bytes()
    f.write_bytes(original.replace(b"\n", b"\r\n")); assert verify_evidence(p)
    f.write_bytes(b"tampered"); assert not verify_evidence(p)
    f.write_bytes(original)
    (p / "extra.json").write_text("{}"); assert not verify_evidence(p)
    (p / "extra.json").unlink(); f.unlink(); assert not verify_evidence(p)


def test_B1G14_supervisor_import_graph_stdlib_only_and_no_fit():
    paths = [ROOT / n for n in c.SOURCE_FILES if n.endswith(".py") and not n.startswith("tests/")]
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        assert not any(isinstance(n, ast.Attribute) and n.attr in {"fit", "fit_transform", "predict", "predict_proba"}
                       for n in ast.walk(tree))
        if path.name != "g4_b1_worker.py":
            assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) and any(
                part in ast.unparse(n) for part in ("numpy", "sklearn", "scipy", "g4_contract", "baselines"))
                for n in ast.walk(tree))


def test_B1G15_cli_real_options_and_direct_worker_denied():
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for args in (["official", "--run-id", "blocked"], ["qualify", "--run-id", "x", "--threshold", "0.1"]):
        p = subprocess.run([sys.executable, "-B", "scripts/run_scania_gate_b1.py", *args], cwd=ROOT,
                           capture_output=True, env=env, timeout=10)
        assert p.returncode == 2
    env = {k: v for k, v in env.items() if not k.startswith("SC_G4_B1_")}
    p = subprocess.run([sys.executable, "-B", "-m", "src.scania.g4_b1_worker"], cwd=ROOT,
                        env=env, capture_output=True, timeout=10)
    assert p.returncode == 126


def test_B1G16_job_setup_error_finalized(tmp_path, mock_runtime, monkeypatch):
    monkeypatch.setattr(s, "WindowsJob", Mock(side_effect=OSError("synthetic assign failure")))
    p = s.run_qualification(tmp_path, run_id="assign")
    assert summary(p)["status"] == "FAILED" and not summary(p)["worker_started"]
    assert verify_evidence(p)


def test_B1G17_invalid_real_scenario_finalized_no_spawning(tmp_path, mock_runtime, monkeypatch):
    factory = Mock(); monkeypatch.setattr(s, "WindowsJob", factory)
    p = s.run_qualification(tmp_path, run_id="denied", scenario="official")
    assert summary(p)["status"] == "BLOCKED" and verify_evidence(p)
    factory.assert_not_called()


def test_B1G18_worker_write_error_not_claimed_saved(tmp_path, mock_runtime, monkeypatch):
    original = Evidence.json
    def fail(self, name, value):
        if name == "run_summary.json": raise OSError("fixture disk failure")
        return original(self, name, value)
    monkeypatch.setattr(Evidence, "json", fail)
    with pytest.raises(OSError): s.run_qualification(tmp_path, run_id="io_error")
    assert not verify_evidence(c.output_path(tmp_path, "io_error"))


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration required")
def test_B1G19_real_windows_job_limits_assignment_kill_and_cleanup():
    from src.scania.g4_b1_contract import child_environment
    job = win.WindowsJob([sys.executable, "-B", "-c", "import time; time.sleep(30)"],
                         child_environment(), ROOT, 512 * 1024**2, 2)
    try:
        assert job.confirmed and job.limits()["flags"] == (0x2000 | 0x200 | 0x8)
        job.resume(); assert job.poll() is None
        job.terminate(); assert job.wait_empty(5)
        assert job.accounting()["active_processes"] == 0
    finally:
        job.close()


@pytest.mark.parametrize("name", ["data/raw/scania_aps/aps_failure_test_set.csv",
    "data/processed/scania_aps/tree_validation.npy", "archive.zip", "outside/aps_failure_test_cache.txt"])
def test_B1G20_worker_data_test_archive_guard_before_open(tmp_path, monkeypatch, name):
    hooks = []; monkeypatch.setattr(sys, "addaudithook", hooks.append)
    output = tmp_path / "results/scania_aps/g4/gate_b1/run"
    w.install_io_guard(tmp_path, output)
    with pytest.raises(c.SafetyBlocked, match="DATA_AND_TEST"):
        hooks[0]("open", (str(tmp_path / name), "r", os.O_RDONLY))
    with pytest.raises(c.SafetyBlocked, match="OUTPUT_OUTSIDE"):
        hooks[0]("open", (str(tmp_path / "src/forbidden.py"), "w", os.O_CREAT | os.O_WRONLY))
    hooks[0]("open", (str(output / "worker_result.json"), "x", os.O_CREAT | os.O_WRONLY))


def test_B1G21_dependency_mismatch_blocks_before_spawn(tmp_path, mock_runtime, monkeypatch):
    def invalid(root): raise c.SafetyBlocked("DEPENDENCY_VERSION_MISMATCH")
    monkeypatch.setattr(s, "verify_environment", invalid)
    factory = Mock(); monkeypatch.setattr(s, "WindowsJob", factory)
    p = s.run_qualification(tmp_path, run_id="env")
    assert summary(p)["status"] == "BLOCKED" and verify_evidence(p)
    factory.assert_not_called()


def test_B1G22_worker_thread_failure_preserved_and_blocked(tmp_path, mock_runtime, monkeypatch):
    def blocked(self):
        self.active = 0
        write_json(self.path / "worker_result.json", dict(kind=c.profile("thread_probe")["kind"],
                   scenario="thread_probe", status="BLOCKED", reason="THREAD_POLICY_NOT_VERIFIED",
                   real_estimator_fits=0, validation_scored=False))
    monkeypatch.setattr(FakeJob, "resume", blocked)
    monkeypatch.setattr(FakeJob, "poll", lambda self: 2)
    p = s.run_qualification(tmp_path, run_id="thread", scenario="thread_probe")
    assert summary(p)["status"] == "BLOCKED" and summary(p)["thread_verification"] == "BLOCKED"
    assert verify_evidence(p)


def test_B1G23_worker_result_cannot_claim_real_fit_or_pass(tmp_path, mock_runtime, monkeypatch):
    original = FakeJob.resume
    def forged(self):
        original(self)
        f = self.path / "worker_result.json"
        value = json.loads(f.read_text()); value["real_estimator_fits"] = 1
        f.write_text(json.dumps(value))
    monkeypatch.setattr(FakeJob, "resume", forged)
    p = s.run_qualification(tmp_path, run_id="forged")
    assert summary(p)["status"] == "FAILED" and verify_evidence(p)


def test_B1G24_profile_cannot_mutate_global_thread_policy():
    p = c.profile("normal"); p["thread_environment"]["OMP_NUM_THREADS"] = "8"
    assert c.profile("normal")["thread_environment"]["OMP_NUM_THREADS"] == "1"
    with pytest.raises(c.SafetyBlocked): c.validate_profile(p)


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration required")
def test_B1G25_job_close_alone_kills_worker():
    import ctypes
    from ctypes import wintypes
    k = win.kernel()
    job = win.WindowsJob([sys.executable, "-B", "-c", "import time; time.sleep(30)"],
                         c.child_environment(), ROOT, 512 * 1024**2, 2)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    observer = None
    try:
        job.resume()
        observer = win.check(k.OpenProcess(0x100000, False, job.pi.pid))
        job.close()
        assert k.WaitForSingleObject(observer, 5000) == 0
    finally:
        if observer: k.CloseHandle(observer)
        job.close()


@pytest.mark.skipif(os.name != "nt", reason="Windows Job Object integration required")
def test_B1G26_assignment_failure_suspended_worker_never_resumed(monkeypatch):
    actual = win.kernel()
    class DenyAssign:
        process = None
        def __getattr__(self, name):
            if name == "AssignProcessToJobObject":
                def deny(job, process):
                    self.process = process
                    raise OSError("synthetic assignment denial")
                return deny
            if name == "ResumeThread": raise AssertionError("must not resume")
            return getattr(actual, name)
    denied = DenyAssign(); monkeypatch.setattr(win, "kernel", lambda: denied)
    with pytest.raises(OSError):
        win.WindowsJob([sys.executable, "-B", "-c", "raise AssertionError('should never execute')"],
                       c.child_environment(), ROOT, 512 * 1024**2, 2)
    assert denied.process is not None
