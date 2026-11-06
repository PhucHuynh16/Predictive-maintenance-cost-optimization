"""Integration tests for Gate B1 worker + native ENV discovery adapter.

Verifies adapter lifecycle, native thread limiting, pre-warming, fail-closed guards,
real Windows Job Object containment/cleanup, and configuration invariance without
accessing real Scania data or official test sets.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
import threadpoolctl

from src.scania import g4_b1_contract as c
from src.scania import g4_b1_worker as w
from src.scania import g4_env_discovery as env
from src.scania.g4_b1_evidence import write_json, verify_evidence
from src.scania.g4_b1_windows import WindowsJob

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def setup_integration_env(monkeypatch):
    """Ensure thread environment and pre-import PID state are configured for integration tests."""
    for k, v in c.THREAD_ENV.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setattr(env, "_PREPARED_PID", os.getpid())
    monkeypatch.setattr(env, "_ACTIVE", None)
    yield
    env._ACTIVE = None


def test_INT01_adapter_startup_lifecycle():
    """Verify that thread_probe executes through NativeSession adapter and passes in clean child process."""
    cmd = [
        sys.executable, "-B", "-c",
        "import json; from src.scania.g4_b1_worker import thread_probe; "
        "events = []; r = thread_probe(events.append); "
        "r['events'] = events; print(json.dumps(r))"
    ]
    env_vars = c.child_environment()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env_vars, capture_output=True, text=True, check=True)
    result = json.loads(proc.stdout)
    assert result["status"] == "PASS"
    assert result["reason"] == "IMPORT_ONLY_POOLS_VERIFIED_NOT_REAL_RUN"
    assert "IMPORT_NUMPY" in result["events"]
    assert "IMPORT_SCIPY" in result["events"]
    assert "IMPORT_SKLEARN_TREE" in result["events"]
    assert "IMPORT_SKLEARN_LR" in result["events"]
    assert "ESTIMATOR_PREWARM" in result["events"]
    assert "NATIVE_POOL_LIMIT_AND_VERIFY" in result["events"]

    # Verify pool controllers
    before = result["before"]
    during = result["during"]
    after = result["after"]
    assert len(before) == 3
    assert len(during) == 3
    assert len(after) == 3
    for p in during:
        assert p["num_threads"] == 1
        assert p["user_api"] in {"blas", "openmp"}


def test_INT02_native_discovery_and_thread_limiting():
    """Verify WideController discovers and limits NumPy, SciPy and OpenMP runtimes."""
    code = (
        "import json\n"
        "from pathlib import Path\n"
        "from src.scania import g4_env_discovery as env\n"
        "env.prepare_imports()\n"
        "import numpy as np, scipy.linalg, sklearn.tree, sklearn.linear_model, threadpoolctl\n"
        "backend = env.Win32Modules()\n"
        "symbols = sorted({s for cls in threadpoolctl._ALL_CONTROLLERS for s in cls.check_symbols})\n"
        "runtimes = env.collect(backend, symbols)\n"
        "runtime_names = sorted(Path(r.path).name.lower() for r in runtimes)\n"
        "session = env.NativeSession()\n"
        "with session:\n"
        "    info = session.controller.info()\n"
        "    a = np.ones((2, 2), dtype=np.float64)\n"
        "    dot_res = float(np.dot(a, a).sum())\n"
        "payload = dict(runtimes=runtime_names, initial_len=len(session.initial), info=info, dot=dot_res)\n"
        "print(json.dumps(payload))\n"
    )
    cmd = [sys.executable, "-B", "-c", code]
    env_vars = c.child_environment()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env_vars, capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    assert set(res["runtimes"]) == set(env.RUNTIMES)
    assert res["initial_len"] == 3
    assert len(res["info"]) == 3
    for pool in res["info"]:
        assert pool["num_threads"] == 1
        assert pool["user_api"] in {"blas", "openmp"}
    assert res["dot"] == 8.0


def test_INT03_late_import_fail_closed_and_restoration():
    """Verify that late import inside active session raises NativeBlocked and restores state.

    Tests real runtime late import interception and fail-closed session restoration.
    """
    code = (
        "import json, sys\n"
        "from src.scania import g4_env_discovery as env\n"
        "env.prepare_imports()\n"
        "import numpy as np, scipy.linalg, sklearn.tree\n"
        "session = env.NativeSession()\n"
        "blocked = False\n"
        "with session:\n"
        "    try:\n"
        "        import sklearn.ensemble\n"
        "    except env.NativeBlocked:\n"
        "        blocked = True\n"
        "reuse_blocked = False\n"
        "try:\n"
        "    with session:\n"
        "        pass\n"
        "except env.NativeBlocked:\n"
        "    reuse_blocked = True\n"
        "payload = dict(blocked=blocked, closed=session.closed, reuse_blocked=reuse_blocked)\n"
        "print(json.dumps(payload))\n"
    )
    cmd = [sys.executable, "-B", "-c", code]
    env_vars = c.child_environment()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env_vars, capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    assert res["blocked"] is True
    assert res["closed"] is True
    assert res["reuse_blocked"] is True


def test_INT04_synthetic_estimator_prewarming_lifecycle():
    """Verify pre-warmed estimators fit and predict without new native DLLs or C-extensions.

    Uses Win32Modules (K32EnumProcessModules) at the OS loader level to verify 0 new DLLs.
    """
    code = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "from src.scania import g4_env_discovery as env\n"
        "env.prepare_imports()\n"
        "import numpy as np\n"
        "from sklearn.tree import DecisionTreeClassifier\n"
        "from sklearn.linear_model import LogisticRegression\n"
        "import scipy.optimize\n"
        "backend = env.Win32Modules()\n"
        "dlls_before = {Path(p).name.lower() for h, p in backend.snapshot()}\n"
        "modules_before = set(sys.modules.keys())\n"
        "X_synth = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0],\n"
        "                    [5.0, 6.0], [6.0, 7.0], [7.0, 8.0], [8.0, 9.0]], dtype=np.float64)\n"
        "y_synth = np.array([0, 0, 0, 0, 1, 1, 1, 1], dtype=np.int32)\n"
        "session = env.NativeSession()\n"
        "with session:\n"
        "    dt = DecisionTreeClassifier(max_depth=2, random_state=42)\n"
        "    dt.fit(X_synth, y_synth)\n"
        "    preds_dt = dt.predict(X_synth).tolist()\n"
        "    lr = LogisticRegression(solver='lbfgs', random_state=42)\n"
        "    lr.fit(X_synth, y_synth)\n"
        "    preds_lr = lr.predict(X_synth).tolist()\n"
        "dlls_after = {Path(p).name.lower() for h, p in backend.snapshot()}\n"
        "modules_after = set(sys.modules.keys())\n"
        "new_native_dlls = sorted(list(dlls_after - dlls_before))\n"
        "new_python_numeric = sorted(list({m for m in (modules_after - modules_before)\n"
        "                                  if m.split('.')[0] in {'numpy', 'scipy', 'sklearn'}}))\n"
        "payload = dict(len_dt=len(preds_dt), len_lr=len(preds_lr),\n"
        "               dlls_count_before=len(dlls_before), dlls_count_after=len(dlls_after),\n"
        "               new_native_dlls=new_native_dlls, new_python_numeric=new_python_numeric)\n"
        "print(json.dumps(payload))\n"
    )
    cmd = [sys.executable, "-B", "-c", code]
    env_vars = c.child_environment()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env_vars, capture_output=True, text=True, check=True)
    res = json.loads(proc.stdout)
    assert res["len_dt"] == 8
    assert res["len_lr"] == 8
    assert res["new_native_dlls"] == [], f"Unexpected native DLLs loaded: {res['new_native_dlls']}"
    assert res["new_python_numeric"] == [], f"Unexpected Python numeric modules loaded: {res['new_python_numeric']}"


def test_INT05_io_guard_blocks_raw_processed_and_official_test(tmp_path, monkeypatch):
    """Verify application-level audit hook blocks access to raw, processed, and official test sets.

    Note: This validates the Python-level audit hook (sys.addaudithook), not OS-level sandboxing.
    """
    hooks = []
    monkeypatch.setattr(sys, "addaudithook", hooks.append)
    output = tmp_path / "results/scania_aps/g4/env_fix/test_run"
    w.install_io_guard(tmp_path, output)
    audit = hooks[0]

    # Raw dataset path
    with pytest.raises(c.SafetyBlocked, match="WORKER_DATA_AND_TEST_ACCESS_DENIED"):
        audit("open", (str(tmp_path / "data/raw/scania_aps/aps_failure_training_set.csv"), "r", os.O_RDONLY))

    # Official test set
    with pytest.raises(c.SafetyBlocked, match="WORKER_DATA_AND_TEST_ACCESS_DENIED"):
        audit("open", (str(tmp_path / "aps_failure_test_set.csv"), "r", os.O_RDONLY))

    # Processed artifact
    with pytest.raises(c.SafetyBlocked, match="WORKER_DATA_AND_TEST_ACCESS_DENIED"):
        audit("open", (str(tmp_path / "data/processed/scania_aps/train_matrix.npy"), "r", os.O_RDONLY))

    # Forbidden write outside output
    with pytest.raises(c.SafetyBlocked, match="WORKER_OUTPUT_OUTSIDE_OWN_RUN"):
        audit("open", (str(tmp_path / "src/scania/tamper.py"), "w", os.O_CREAT | os.O_WRONLY))

    # Legitimate write inside output directory allowed
    audit("open", (str(output / "worker_result.json"), "x", os.O_CREAT | os.O_WRONLY))

    # Subprocess verification of real Python open() interception
    code = (
        "import sys, os\n"
        "from pathlib import Path\n"
        "from src.scania.g4_b1_worker import install_io_guard\n"
        "from src.scania.g4_b1_contract import SafetyBlocked\n"
        "root = Path(sys.argv[1]).resolve()\n"
        "out = root / 'results/scania_aps/g4/gate_b1/tmp_io'\n"
        "out.mkdir(parents=True, exist_ok=True)\n"
        "install_io_guard(root, out)\n"
        "blocked_raw = False\n"
        "try:\n"
        "    open(root / 'data/raw/scania_aps/aps_failure_training_set.csv', 'r')\n"
        "except SafetyBlocked:\n"
        "    blocked_raw = True\n"
        "blocked_test = False\n"
        "try:\n"
        "    open(root / 'aps_failure_test_set.csv', 'r')\n"
        "except SafetyBlocked:\n"
        "    blocked_test = True\n"
        "print(f'BLOCKED_RAW={blocked_raw},BLOCKED_TEST={blocked_test}')\n"
    )
    cmd = [sys.executable, "-B", "-c", code, str(ROOT)]
    proc = subprocess.run(cmd, cwd=str(ROOT), env=c.child_environment(), capture_output=True, text=True, check=True)
    assert "BLOCKED_RAW=True,BLOCKED_TEST=True" in proc.stdout


def test_INT06_real_windows_job_object_containment_and_cleanup(tmp_path):
    """Verify real Windows Job Object assignment, containment, and process termination.

    Executes a real WindowsJob with kill-on-close + active process limits, verifies
    accounting, terminates the job, and confirms that wait_empty reaches 0 active processes.
    """
    if os.name != "nt":
        pytest.skip("Windows Job Object requires Windows NT")

    argv = [sys.executable, "-B", "-c", "import time; time.sleep(10)"]
    env_vars = dict(os.environ)
    job = WindowsJob(argv, env_vars, ROOT, memory_bytes=64 * 1024 * 1024, active_limit=2)
    assert job.confirmed is True

    # Verify limits
    limits = job.limits()
    assert bool(limits["flags"] & 0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    assert limits["active_process_limit"] == 2
    assert limits["job_memory_bytes"] == 64 * 1024 * 1024

    # Resume and verify containment
    job.resume()
    import time
    time.sleep(0.05)
    acc_before = job.accounting()
    assert acc_before["active_processes"] >= 1

    # Terminate and verify cleanup
    job.terminate()
    empty = job.wait_empty(5.0)
    assert empty is True
    acc_after = job.accounting()
    assert acc_after["active_processes"] == 0
    job.close()


def test_INT07_config_and_accepted_assets_invariance():
    """Verify that G3 and G4 configs and accepted assets remain unchanged."""
    g3_config_path = ROOT / "configs/scania/g3_pipeline.json"
    g4_config_path = ROOT / "configs/scania/g4_baselines.json"

    assert g3_config_path.exists(), "g3_pipeline.json missing!"
    assert g4_config_path.exists(), "g4_baselines.json missing!"

    g3_cfg = json.loads(g3_config_path.read_text(encoding="utf-8"))
    g4_cfg = json.loads(g4_config_path.read_text(encoding="utf-8"))

    # Verify locked parameters
    assert g4_cfg["cost"]["FP"] == 10
    assert g4_cfg["cost"]["FN"] == 500
    assert g4_cfg["capacity"]["denominator"] == 10
    assert g4_cfg["thresholds"]["PRIMARY"]["numerator"] == 1
    assert g4_cfg["thresholds"]["PRIMARY"]["denominator"] == 2
    assert g4_cfg["thresholds"]["SECONDARY"]["numerator"] == 10
    assert g4_cfg["thresholds"]["SECONDARY"]["denominator"] == 510
    assert g4_cfg["gate_b_authorized"] is False
    assert g4_cfg["official_test"] == "SEALED_UNTIL_G10"
    assert g3_cfg["source"]["rows"] == 60000
    assert g3_cfg["split"]["test_size"] == 0.2
    assert g3_cfg["test_status"] == "SEALED_UNTIL_G10"
