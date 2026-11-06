"""Fixed mock tasks / import-only probe. Deliberately no estimator fit API."""
import ctypes
import json
import os
from pathlib import Path
import sys
import time
import re
from .g4_b1_contract import THREAD_ENV, output_path, profile, verify_pools, SafetyBlocked, sha
from .g4_b1_evidence import write_json, append_event


def install_io_guard(root, output):
    """Worker-only audit hook: no datasets/archive reads or out-of-run writes.

    This is an application guard, not an OS sandbox for arbitrary native code.
    """
    root, output = Path(root).resolve(), Path(output).resolve()
    def audit(name, args):
        if name != "open" or isinstance(args[0], int):
            return
        raw = os.fsdecode(args[0]); p = Path(raw).resolve()
        if ((root / "data") == p or (root / "data") in p.parents
                or "aps_failure_test" in p.name.casefold() or p.suffix.casefold() in {".zip", ".npz", ".npy", ".csv"}):
            raise SafetyBlocked("WORKER_DATA_AND_TEST_ACCESS_DENIED")
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
        if writing and not p.is_relative_to(output):
            raise SafetyBlocked("WORKER_OUTPUT_OUTSIDE_OWN_RUN")
    sys.addaudithook(audit)


def thread_probe(event=lambda stage: None):
    """Import after env verification; controller failure remains BLOCKED."""
    if any(os.environ.get(k) != v for k, v in THREAD_ENV.items()):
        raise SafetyBlocked("THREAD_ENV_NOT_SET_BEFORE_IMPORT")
    if any(n in sys.modules for n in ("numpy", "scipy", "sklearn")):
        raise SafetyBlocked("NUMERIC_IMPORT_TOO_EARLY")

    # Handshake with env discovery before numeric imports
    try:
        from . import g4_env_discovery as _env_disc
        if getattr(_env_disc, "_PREPARED_PID", None) != os.getpid():
            _env_disc.prepare_imports()
    except Exception:
        pass

    # Imports load the same native stacks needed by the two approved estimators.
    event("IMPORT_NUMPY")
    import numpy
    event("IMPORT_SCIPY")
    import scipy.linalg
    event("IMPORT_SKLEARN_TREE")
    from sklearn.tree import DecisionTreeClassifier
    event("IMPORT_SKLEARN_LR")
    from sklearn.linear_model import LogisticRegression

    def public(pools):
        return [{k: (Path(v).name if k == "filepath" else v) for k, v in p.items()} for p in pools]

    # Pre-warming verification
    event("ESTIMATOR_PREWARM")
    try:
        import scipy.optimize
    except Exception:
        pass

    event("NATIVE_INVENTORY")
    libraries = []
    try:
        from .g4_env_discovery import NativeSession
        session = NativeSession()
        inventory = [r.path for r in session.initial]
        libraries = [dict(name=Path(p).name, sha256=sha(Path(p).read_bytes())) for p in inventory]
        event("NATIVE_POOL_DISCOVERY")
        before = session.controller.info()
        event("NATIVE_POOL_LIMIT_AND_VERIFY")
        with session:
            pools = session.controller.info()
            verify_pools(pools, inventory)
            # Fabricated numeric work only; no model fitting or real-data loading.
            numpy.dot(numpy.ones((2, 2)), numpy.ones((2, 2)))
            during = session.controller.info()
        after = session.controller.info()
        inventory_after = [r.path for r in session.initial]
        verify_pools(after, inventory_after)
        return dict(status="PASS", reason="IMPORT_ONLY_POOLS_VERIFIED_NOT_REAL_RUN",
                    before=public(before), during=public(during), after=public(after),
                    native_libraries=libraries,
                    session=session.public())
    except Exception as exc:
        return dict(status="BLOCKED", reason="THREAD_POLICY_NOT_VERIFIED", error_type=type(exc).__name__,
                    winerror=getattr(exc, "winerror", None),
                    dll_names=re.findall(r"[^\\/'\"\s]+\.dll", str(exc)),
                    native_libraries=libraries, num_threads=None, num_threads_reason="DISCOVERY_OR_VERIFICATION_FAILED")


def main():
    # No argparse worker/data/fit overrides. Environment is supervisor handshake,
    # not a source of owner permission. Even forged env cannot select real fitting.
    if set(sys.argv[1:]):
        return 126
    try:
        root = Path(__file__).resolve().parents[2]
        run_id = os.environ["SC_G4_B1_RUN"]
        scenario = os.environ["SC_G4_B1_SCENARIO"]
        token = os.environ["SC_G4_B1_NONCE"]
        if len(token) != 48 or any(c not in "0123456789abcdef" for c in token):
            return 126
        cfg = profile(scenario)
        path = output_path(root, run_id)
        reservation = json.loads((path / "reservation.json").read_text(encoding="utf-8"))
        if reservation.get("kind") != "B1_INFRASTRUCTURE_ATTEMPT" or reservation.get("real_fit_budget") != 0:
            return 126
        write_json(path / "worker_claim.json", dict(pid=os.getpid(), scenario=scenario, single_use=True))
    except (KeyError, ValueError, OSError):
        return 126
    def event(stage):
        append_event(path / "worker_journal.jsonl", dict(stage=stage, pid=os.getpid()))
    install_io_guard(root, path)
    event("STARTED_NO_DATA_NO_FIT")
    # Do not let native loader/GP-fault dialogs outlive the supervised worker.
    if os.name == "nt":
        kernel32 = ctypes.WinDLL("kernel32")
        kernel32.SetErrorMode(0x1 | 0x2 | 0x8000)
    result = dict(status="PASS", reason="MOCK_COMPLETED", scenario=scenario,
                  kind=cfg["kind"], real_estimator_fits=0, validation_scored=False)
    try:
        if scenario == "crash":
            event("INTENTIONAL_CRASH"); os._exit(37)
        elif scenario == "sleep":
            event("SLEEPING"); time.sleep(60)
        elif scenario == "busy":
            event("CPU_BUSY")
            while True:
                sum(range(1000))
        elif scenario == "native_busy":
            event("NATIVE_SLEEP")
            k = ctypes.WinDLL("kernel32"); k.Sleep.argtypes = [ctypes.c_ulong]
            k.Sleep(60000)
        elif scenario == "memory_limit":
            event("INTENTIONAL_ALLOCATION_OVER_JOB_CAP")
            try:
                value = bytearray(cfg["job_memory_bytes"] + 64 * 1024**2)
            except MemoryError:
                result["reason"] = "SYNTHETIC_ALLOCATION_DENIED"
            else:
                del value
                raise RuntimeError("JOB_MEMORY_LIMIT_NOT_ENFORCED")
        elif scenario == "child_attempt":
            import subprocess
            event("CHILD_ATTEMPT")
            try:
                child = subprocess.Popen([sys.executable, "-B", "-c", "pass"],
                                         creationflags=0x8000000)
            except OSError:
                result["reason"] = "SYNTHETIC_CHILD_CREATION_DENIED"
            else:
                child.wait(timeout=3)
                raise RuntimeError("CHILD_CREATION_NOT_DENIED")
        elif scenario == "thread_probe":
            result["thread_verification"] = thread_probe(event)
            if result["thread_verification"]["status"] != "PASS":
                raise SafetyBlocked("THREAD_POLICY_NOT_VERIFIED")
            result["reason"] = "IMPORT_ONLY_PROBE_COMPLETED"
        else:
            result["fixture_digest"] = sha(b"B1 mock deterministic fixture: no ML / no data")
        event("COMPLETED")
    except Exception as exc:
        result.update(status="BLOCKED" if scenario == "thread_probe" else "FAILED",
                      reason="THREAD_POLICY_NOT_VERIFIED" if scenario == "thread_probe" else "MOCK_TASK_ERROR",
                      error_type=type(exc).__name__,
                      error_code=getattr(exc, "winerror", None))
        # Never publish raw exception strings containing Unicode user/workspace paths.
        event("STOPPED_" + result["reason"])
    write_json(path / "worker_result.json", result)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
