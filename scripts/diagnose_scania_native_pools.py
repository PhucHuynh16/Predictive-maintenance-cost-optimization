"""ENV-only native qualification. No data, estimator, scoring or B2 entrypoint."""
import argparse
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.scania import g4_env_discovery as env

BASE = "d78cfcd30601090211003ef3a6a6751f83dd6eb3"
NAMESPACE = "results/scania_aps/g4/env_fix"
SOURCES = ("src/scania/g4_env_discovery.py", "scripts/diagnose_scania_native_pools.py",
           "tests/scania/test_g4_env_discovery.py")
SCENARIOS = {"normal", "crash", "timeout", "late_import", "data_guard"}
FILES = {"reservation.json", "config.json", "source_manifest.json", "environment.json",
         "journal.jsonl", "worker_journal.jsonl", "worker_claim.json", "worker_result.json",
         "run_summary.json", "failure_diagnostics.json", "checksums.json"}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def object_hash(value):
    return env.digest(canonical(value))


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", *args], cwd=ROOT)


def write_json(path, value):
    with Path(path).open("xb") as f:
        f.write(canonical(value)); f.flush(); os.fsync(f.fileno())


def event(path, stage):
    with Path(path).open("ab") as f:
        f.write(canonical({"stage": stage})); f.flush(); os.fsync(f.fileno())


def output_path(run_id):
    env.require(isinstance(run_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,72}", run_id), "INVALID_RUN_ID")
    path = ROOT / NAMESPACE / run_id
    env.require(path.resolve() == path.absolute() and path.resolve().is_relative_to(ROOT), "OUTPUT_ALIAS_OR_ESCAPE")
    return path


def protected_snapshot():
    names = git("ls-tree", "-r", "--name-only", BASE).decode().splitlines()
    query = "".join(BASE + ":" + n + "\n" for n in names).encode()
    data = subprocess.run(["git", "cat-file", "--batch"], cwd=ROOT, input=query,
                          stdout=subprocess.PIPE, check=True).stdout
    result, offset = {}, 0
    for name in names:
        end = data.index(b"\n", offset); size = int(data[offset:end].split()[-1])
        expected = data[end + 1:end + size + 1]; offset = end + size + 2
        path = ROOT / name
        env.require(path.resolve() == path.absolute(), "PROTECTED_ALIAS")
        actual = path.read_bytes()
        if path.suffix not in {".png", ".jpg", ".pdf"}:
            actual, expected = actual.replace(b"\r\n", b"\n"), expected.replace(b"\r\n", b"\n")
        env.require(actual == expected, "PROTECTED_ASSET_CHANGED")
        result[name] = env.digest(actual)
    return {"files": len(result), "digest": object_hash(result)}


def source_manifest():
    files = {p: env.digest((ROOT / p).read_bytes().replace(b"\r\n", b"\n")) for p in SOURCES}
    head = git("rev-parse", "HEAD").decode().strip()
    bound = not git("status", "--porcelain", "--", *SOURCES).strip()
    return {"head": head, "source_commit": head if bound else None,
            "binding": "COMMITTED_SOURCE" if bound else "CAPTURED_WORKING_TREE_BEFORE_EXECUTION",
            "files": files, "source_digest": object_hash(files)}


def environment():
    lock = json.loads((ROOT / "configs/scania/g3_pipeline.json").read_text("utf-8"))["environment"]
    actual = {"python": platform.python_version(), "packages": {k: version(k) for k in lock["packages"]}}
    env.require(actual == lock, "LOCKED_ENVIRONMENT_MISMATCH")
    return {**actual, "platform": platform.platform(), "threadpoolctl_sha256": env.THREADPOOLCTL_SHA256,
            "g3_config_sha256": env.digest((ROOT / "configs/scania/g3_pipeline.json").read_bytes())}


def install_io_guard(output):
    def hook(name, args):
        if name not in {"open", "os.listdir", "os.scandir"} or not args or isinstance(args[0], int):
            return
        path = Path(os.fsdecode(args[0])).resolve()
        if (path == ROOT / "data" or ROOT / "data" in path.parents
                or "aps_failure_test" in path.name.casefold()
                or path.suffix.casefold() in {".csv", ".npy", ".npz", ".zip", ".pkl", ".joblib"}):
            raise env.NativeBlocked("DIAGNOSTIC_DATA_ACCESS_DENIED")
        if name == "open":
            mode, flags = args[1], args[2]
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT))
            if writing and not path.is_relative_to(output):
                raise env.NativeBlocked("DIAGNOSTIC_WRITE_OUTSIDE_RUN")
    sys.addaudithook(hook)


def worker(run_id, scenario):
    output = output_path(run_id)
    nonce = os.environ.get("SC_ENV_WORKER_NONCE", "")
    env.require(len(nonce) == 48 and all(c in "0123456789abcdef" for c in nonce), "WORKER_HANDSHAKE_MISSING")
    reservation = json.loads((output / "reservation.json").read_text("utf-8"))
    env.require(reservation["scenario"] == scenario and reservation["real_fit_budget"] == 0,
                "WORKER_RESERVATION_MISMATCH")
    env.require(env.digest(nonce.encode()) == reservation.get("nonce_sha256"), "WORKER_HANDSHAKE_MISMATCH")
    write_json(output / "worker_claim.json", {"single_use": True, "scenario": scenario})
    install_io_guard(output)
    C.WinDLL("kernel32").SetErrorMode(0x1 | 0x2 | 0x8000)
    result = {"scenario": scenario, "status": "RUNNING", "real_estimator_fits": 0,
              "validation_scored": False, "official_test": "SEALED_UNTIL_G10", "b2_authorized": False}
    stage = "PREIMPORT"
    session = None
    try:
        event(output / "worker_journal.jsonl", stage)
        env.prepare_imports()
        if scenario == "crash":
            event(output / "worker_journal.jsonl", "INTENTIONAL_CRASH"); os._exit(37)
        if scenario == "timeout":
            event(output / "worker_journal.jsonl", "INTENTIONAL_SLEEP"); time.sleep(60)
        stage = "IMPORT_NUMERICAL_STACK"
        event(output / "worker_journal.jsonl", stage)
        import numpy as np
        from scipy.linalg.blas import dgemm
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics._pairwise_fast import _sparse_manhattan
        from sklearn.utils._openmp_helpers import _openmp_parallelism_enabled
        stage = "DISCOVERY_AND_CONTEXT"
        event(output / "worker_journal.jsonl", stage)
        session = env.NativeSession()
        with session:
            if scenario == "late_import":
                __import__("numpy._ENV_LATE_IMPORT_SENTINEL")
            if scenario == "data_guard":
                # This nonexistent sentinel is rejected before any file is opened.
                (output / "aps_failure_test_SENTINEL.txt").open("rb")
            a = np.ones((2, 2), dtype=np.float64)
            n = float(np.dot(a, a).sum())
            env.require(n == 8.0, "NUMPY_SYNTHETIC_ORACLE_FAILED")
            session.checkpoint("after_numpy")
            s = float(dgemm(1.0, a, a).sum())
            env.require(s == 8.0, "SCIPY_SYNTHETIC_ORACLE_FAILED")
            session.checkpoint("after_scipy")
            env.require(_openmp_parallelism_enabled(), "OPENMP_COMPILED_SUPPORT_MISSING")
            values = np.array([1.0, 2.0], dtype=np.float64)
            indices = np.array([0, 1], dtype=np.int32)
            indptr = np.array([0, 1, 2], dtype=np.int32)
            distances = np.zeros((2, 2), dtype=np.float64)
            _sparse_manhattan(values, indices, indptr, values, indices, indptr, distances)
            env.require(np.array_equal(distances, np.array([[0.0, 3.0], [3.0, 0.0]])),
                        "OPENMP_SYNTHETIC_ORACLE_FAILED")
            session.checkpoint("after_openmp")
            result["synthetic"] = {"numpy_dot_sum": n, "scipy_dgemm_sum": s,
                                   "openmp_pairwise_l1_sum": float(distances.sum()), "rows": 2,
                                   "openmp_compiled_support": True}
        result.update(status="PASS", native_verification="PASS", session=session.public())
        event(output / "worker_journal.jsonl", "CONTEXT_CLOSED_NO_REAL_FIT")
    except BaseException as exc:
        result.update(status="BLOCKED" if isinstance(exc, env.NativeBlocked) else "FAILED",
                      native_verification="NOT_VERIFIED", stage_failed=stage,
                      error_type=type(exc).__name__,
                      reason=str(exc) if isinstance(exc, env.NativeBlocked) else "NATIVE_QUALIFICATION_ERROR")
        if session is not None:
            result["session"] = session.public()
        event(output / "worker_journal.jsonl", "STOPPED")
    write_json(output / "worker_result.json", result)
    return 0 if result["status"] == "PASS" else 2


# The isolated diagnostic launcher uses the same documented Win32 lifecycle as
# accepted B1, implemented here so main-based ENV code has no B1 dependency.
class Basic(C.Structure):
    _fields_ = [("pt", C.c_int64), ("jt", C.c_int64), ("flags", W.DWORD),
        ("minws", C.c_size_t), ("maxws", C.c_size_t), ("active", W.DWORD),
        ("affinity", C.c_size_t), ("priority", W.DWORD), ("scheduling", W.DWORD)]


class IO(C.Structure):
    _fields_ = [(n, C.c_uint64) for n in ("ro", "wo", "oo", "rb", "wb", "ob")]


class Limits(C.Structure):
    _fields_ = [("basic", Basic), ("io", IO), ("pm", C.c_size_t), ("jm", C.c_size_t),
               ("peakpm", C.c_size_t), ("peakjm", C.c_size_t)]


class Accounting(C.Structure):
    _fields_ = [(n, C.c_int64) for n in ("u", "k", "pu", "pk")]
    _fields_ += [(n, W.DWORD) for n in ("faults", "total", "active", "terminated")]


class Startup(C.Structure):
    _fields_ = [("cb", W.DWORD), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR), ("title", W.LPWSTR)]
    _fields_ += [(n, W.DWORD) for n in ("x", "y", "xs", "ys", "xc", "yc", "fill", "flags")]
    _fields_ += [("show", W.WORD), ("rs", W.WORD), ("rp", C.POINTER(C.c_byte))]
    _fields_ += [(n, W.HANDLE) for n in ("stdin", "stdout", "stderr")]


class Process(C.Structure):
    _fields_ = [("process", W.HANDLE), ("thread", W.HANDLE), ("pid", W.DWORD), ("tid", W.DWORD)]


class DiagnosticJob:
    def __init__(self, argv, environment_vars):
        env.require(os.name == "nt", "WINDOWS_JOB_REQUIRED")
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.job = None; self.pi = Process(); self.closed = False
        signatures = {
            "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
            "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
            "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
            "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL, W.DWORD,
                C.c_void_p, W.LPCWSTR, C.POINTER(Startup), C.POINTER(Process)], W.BOOL),
            "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
            "IsProcessInJob": ([W.HANDLE, W.HANDLE, C.POINTER(W.BOOL)], W.BOOL),
            "ResumeThread": ([W.HANDLE], W.DWORD), "CloseHandle": ([W.HANDLE], W.BOOL),
            "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
            "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
            "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
            "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
        }
        for n, (a, r) in signatures.items():
            fn = getattr(self.k, n); fn.argtypes = a; fn.restype = r
        try:
            self.job = self.check(self.k.CreateJobObjectW(None, None))
            limits = Limits(); limits.basic.flags = 0x2208; limits.basic.active = 2; limits.jm = 512 * 1024**2
            self.check(self.k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)))
            self.limits = self.read_limits()
            env.require(self.limits == {"flags": 0x2208, "active_limit": 2, "job_memory_bytes": 512 * 1024**2},
                        "JOB_LIMIT_READBACK_FAILED")
            si = Startup(); si.cb = C.sizeof(si)
            block = C.create_unicode_buffer("\0".join(k + "=" + v for k, v in sorted(environment_vars.items(), key=lambda x: x[0].upper())) + "\0\0")
            cmd = C.create_unicode_buffer(subprocess.list2cmdline(argv))
            self.check(self.k.CreateProcessW(str(argv[0]), cmd, None, None, False, 0x4 | 0x400 | 0x8000000,
                block, str(ROOT), C.byref(si), C.byref(self.pi)))
            self.check(self.k.AssignProcessToJobObject(self.job, self.pi.process))
            inside = W.BOOL(); self.check(self.k.IsProcessInJob(self.pi.process, self.job, C.byref(inside)))
            env.require(inside.value, "JOB_ASSIGNMENT_NOT_VERIFIED")
        except BaseException:
            if self.pi.process:
                self.k.TerminateProcess(self.pi.process, 125); self.k.WaitForSingleObject(self.pi.process, 5000)
            self.close()
            raise

    @staticmethod
    def check(value):
        env.require(value, "WIN32_JOB_API_FAILED")
        return value

    def read_limits(self):
        value = Limits()
        self.check(self.k.QueryInformationJobObject(self.job, 9, C.byref(value), C.sizeof(value), None))
        return {"flags": value.basic.flags, "active_limit": value.basic.active, "job_memory_bytes": value.jm}

    def resume(self):
        env.require(self.k.ResumeThread(self.pi.thread) != 0xffffffff, "WORKER_RESUME_FAILED")

    def poll(self):
        value = self.k.WaitForSingleObject(self.pi.process, 0)
        if value == 0x102:
            return None
        env.require(value == 0, "WORKER_WAIT_FAILED")
        code = W.DWORD(); self.check(self.k.GetExitCodeProcess(self.pi.process, C.byref(code)))
        return int(code.value)

    def active(self):
        value = Accounting()
        self.check(self.k.QueryInformationJobObject(self.job, 1, C.byref(value), C.sizeof(value), None))
        return int(value.active)

    def cleanup(self):
        if self.active():
            self.check(self.k.TerminateJobObject(self.job, 124))
        deadline = time.perf_counter() + 5
        while self.active() and time.perf_counter() < deadline:
            time.sleep(.01)
        return self.active() == 0

    def close(self):
        if self.closed:
            return
        for h in (self.job, self.pi.thread, self.pi.process):
            if h:
                self.check(self.k.CloseHandle(h))
        self.closed = True


def validate_worker(value, scenario):
    env.require(value.get("scenario") == scenario and type(value.get("real_estimator_fits")) is int
                and value["real_estimator_fits"] == 0 and value.get("validation_scored") is False
                and value.get("b2_authorized") is False and value.get("official_test") == "SEALED_UNTIL_G10",
                "WORKER_CONTRACT_INVALID")
    if value.get("status") == "PASS":
        session = value.get("session", {})
        env.require(scenario == "normal" and value.get("native_verification") == "PASS"
                    and session.get("kind") == "WINDOWS_NATIVE_DIAGNOSTIC" and session.get("context_closed") is True
                    and session.get("real_execution_authorized") is False,
                    "NATIVE_COMPLETION_MISSING")
        expected = ["before", "during_enter", "after_numpy", "after_scipy", "after_openmp", "during_exit", "after_restore"]
        checkpoints = session.get("checkpoints", [])
        env.require([c["stage"] for c in checkpoints] == expected,
                    "NATIVE_CHECKPOINTS_INCOMPLETE")
        synthetic = value.get("synthetic", {})
        env.require(synthetic == {"numpy_dot_sum": 8.0, "scipy_dgemm_sum": 8.0,
                    "openmp_pairwise_l1_sum": 6.0, "rows": 2, "openmp_compiled_support": True},
                    "SYNTHETIC_ORACLES_INCOMPLETE")
        env.require(type(synthetic.get("rows")) is int and synthetic.get("openmp_compiled_support") is True
                    and all(type(synthetic.get(k)) is float for k in
                            ("numpy_dot_sum", "scipy_dgemm_sum", "openmp_pairwise_l1_sum")),
                    "SYNTHETIC_ORACLE_TYPES_INVALID")
        rows = session.get("runtimes", [])
        env.require(len(rows) == 3 and {r["name"].lower() for r in rows} == set(env.RUNTIMES), "NATIVE_PUBLIC_INVENTORY_INCOMPLETE")
        for r in rows:
            env.require(r["sha256"] == env.RUNTIMES[r["name"].lower()][0], "NATIVE_PUBLIC_HASH_MISMATCH")
        for c in checkpoints:
            env.require(len(c["pools"]) == 3 and {p["name"].lower() for p in c["pools"]} == set(env.RUNTIMES),
                        "NATIVE_PUBLIC_POOLS_INCOMPLETE")
            for p in c["pools"]:
                expected_runtime = env.RUNTIMES[p["name"].lower()]
                env.require(type(p.get("num_threads")) is int and p["num_threads"] == 1
                    and p.get("user_api") == expected_runtime[1] and p.get("internal_api") == expected_runtime[2],
                    "NATIVE_PUBLIC_THREADS_OR_API_INVALID")
    else:
        env.require(value.get("status") in {"BLOCKED", "FAILED"}, "WORKER_STATUS_INVALID")


def finalize(path):
    members = list(path.iterdir())
    env.require(all(p.name in FILES and p.is_file() and p.resolve() == p.absolute() for p in members), "EVIDENCE_MEMBER_INVALID")
    write_json(path / "checksums.json", {p.name: env.digest(p.read_bytes().replace(b"\r\n", b"\n")) for p in sorted(members)})


def verify_evidence(path):
    try:
        path = Path(path)
        env.require(path.resolve() == path.absolute(), "EVIDENCE_ALIAS")
        entries = list(path.iterdir())
        env.require(all(p.name in FILES and p.is_file() and p.resolve() == p.absolute() for p in entries),
                    "EVIDENCE_MEMBER_ALIAS_OR_TYPE")
        checks = json.loads((path / "checksums.json").read_text("utf-8"))
        env.require({"reservation.json", "journal.jsonl", "run_summary.json", "failure_diagnostics.json"} <= set(checks), "EVIDENCE_REQUIRED_MISSING")
        env.require(set(checks) == {p.name for p in path.iterdir() if p.name != "checksums.json"}, "EVIDENCE_MEMBERSET_MISMATCH")
        for n, h in checks.items():
            env.require(n in FILES and n != "checksums.json", "EVIDENCE_PATH_INVALID")
            env.require(env.digest((path / n).read_bytes().replace(b"\r\n", b"\n")) == h, "EVIDENCE_HASH_INVALID")
        summary = json.loads((path / "run_summary.json").read_text("utf-8"))
        env.require(type(summary["real_estimator_fits"]) is int and summary["real_estimator_fits"] == 0
                    and summary["validation_scored"] is False and summary["b2_authorized"] is False
                    and summary["official_test"] == "SEALED_UNTIL_G10", "EVIDENCE_REAL_DATA_CLAIM")
        if summary["status"] == "PASS":
            env.require({"config.json", "source_manifest.json", "environment.json", "worker_claim.json",
                         "worker_journal.jsonl", "worker_result.json"} <= set(checks), "EVIDENCE_PASS_PROVENANCE_MISSING")
            env.require(summary["job_empty_verified"] is True and summary["protected_unchanged"] is True
                        and summary["source_unchanged"] is True and summary["lifecycle"] == "COMPLETE"
                        and summary.get("native_verification") == "PASS" and summary.get("worker_exit_code") == 0,
                        "EVIDENCE_FALSE_PASS")
            validate_worker(json.loads((path / "worker_result.json").read_text("utf-8")), summary["scenario"])
        else:
            env.require(summary["status"] in {"BLOCKED", "FAILED"} and summary["lifecycle"] == "FAILED", "EVIDENCE_INVALID_FAILURE")
        return True
    except (OSError, ValueError, TypeError, KeyError):
        return False


def qualify(run_id, scenario):
    env.require(scenario in SCENARIOS, "SCENARIO_NOT_ALLOWED")
    path = output_path(run_id); path.parent.mkdir(parents=True, exist_ok=True); path.mkdir(exist_ok=False)
    nonce = secrets.token_hex(24)
    write_json(path / "reservation.json", {"scenario": scenario, "run_id": run_id, "real_fit_budget": 0,
        "nonce_sha256": env.digest(nonce.encode()),
        "kind": "ENV_DIAGNOSTIC_ONLY", "created_utc": datetime.now(timezone.utc).isoformat()})
    summary = {"scenario": scenario, "status": "BLOCKED", "lifecycle": "FAILED", "real_estimator_fits": 0,
               "validation_scored": False, "official_test": "SEALED_UNTIL_G10", "b2_authorized": False,
               "worker_started": False, "job_empty_verified": False, "source_unchanged": False, "protected_unchanged": False}
    errors = []; before = None; source = None; job = None; stage = "PREFLIGHT"; start = time.perf_counter()
    event(path / "journal.jsonl", stage)
    try:
        source = source_manifest(); before = protected_snapshot()
        write_json(path / "source_manifest.json", source); write_json(path / "environment.json", environment())
        cap = 1.0 if scenario == "timeout" else 20.0
        config = {"kind": "ENV_SYNTHETIC_DIAGNOSTIC", "scenario": scenario, "wall_seconds": cap,
                  "job_memory_bytes": 512 * 1024**2, "active_process_limit": 2, "thread_environment": env.THREAD_ENV,
                  "production_policy": "PENDING_OWNER_APPROVAL", "real_fit_budget": 0}
        write_json(path / "config.json", config)
        child_env = dict(os.environ); child_env.update(env.THREAD_ENV, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
        child_env["SC_ENV_WORKER_NONCE"] = nonce
        for k in ("PYTHONHOME", "PYTHONPATH", "PYTHONSTARTUP"):
            child_env.pop(k, None)
        stage = "SUSPENDED_JOB_SETUP"; launch = time.perf_counter()
        job = DiagnosticJob([sys.executable, "-B", "-X", "utf8", str(Path(__file__)), "worker", "--run-id", run_id, "--scenario", scenario], child_env)
        summary["job_limits"] = job.limits
        env.require(time.perf_counter() - launch < cap, "DEADLINE_BEFORE_RESUME")
        job.resume(); summary["worker_started"] = True; stage = "WORKER_RUNNING"
        event(path / "journal.jsonl", stage)
        while True:
            code = job.poll()
            if time.perf_counter() - launch >= cap:
                raise TimeoutError("DIAGNOSTIC_WALL_TIMEOUT")
            if code is not None:
                break
            time.sleep(.02)
        summary["worker_exit_code"] = code
        stage = "WORKER_RESULT"
        if not (path / "worker_result.json").is_file():
            raise RuntimeError("WORKER_CRASH_OR_MISSING_RESULT")
        result = json.loads((path / "worker_result.json").read_text("utf-8")); validate_worker(result, scenario)
        summary.update(status=result["status"], lifecycle="COMPLETE" if result["status"] == "PASS" and code == 0 else "FAILED")
        env.require(code == (0 if result["status"] == "PASS" else 2), "WORKER_EXIT_MISMATCH")
        summary["native_verification"] = result["native_verification"]
        if result["status"] != "PASS":
            errors.append({"stage": result.get("stage_failed"), "reason": result.get("reason"), "error_type": result.get("error_type")})
    except BaseException as exc:
        summary.update(status="BLOCKED" if isinstance(exc, env.NativeBlocked) else "FAILED", lifecycle="FAILED")
        errors.append({"stage": stage, "error_type": type(exc).__name__,
            "reason": str(exc) if isinstance(exc, (env.NativeBlocked, TimeoutError)) else "DIAGNOSTIC_SUPERVISOR_ERROR"})
    finally:
        if job is not None:
            try:
                summary["job_empty_verified"] = job.cleanup()
                env.require(summary["job_empty_verified"], "JOB_CLEANUP_NOT_VERIFIED")
            except BaseException as exc:
                summary.update(status="FAILED", lifecycle="FAILED", job_empty_verified=False)
                errors.append({"stage": "CLEANUP", "error_type": type(exc).__name__, "reason": "JOB_CLEANUP_NOT_VERIFIED"})
            finally:
                try:
                    job.close()
                except BaseException as exc:
                    summary.update(status="FAILED", lifecycle="FAILED")
                    errors.append({"stage": "CLOSE", "error_type": type(exc).__name__, "reason": "JOB_CLOSE_FAILED"})
        try:
            summary["source_unchanged"] = source is not None and source_manifest()["source_digest"] == source["source_digest"]
            summary["protected_unchanged"] = before is not None and protected_snapshot() == before
            env.require(summary["source_unchanged"] and summary["protected_unchanged"], "SOURCE_OR_PROTECTED_CHANGED")
        except BaseException as exc:
            summary.update(status="FAILED", lifecycle="FAILED")
            errors.append({"stage": "POSTCHECK", "error_type": type(exc).__name__, "reason": "SOURCE_OR_PROTECTED_CHANGED"})
        if summary["status"] == "PASS" and not summary["job_empty_verified"]:
            summary.update(status="FAILED", lifecycle="FAILED")
        summary["total_seconds"] = time.perf_counter() - start
        stable = {"scenario": scenario, "status": summary["status"], "source_digest": source["source_digest"] if source else None}
        if (path / "worker_result.json").is_file():
            result = json.loads((path / "worker_result.json").read_text("utf-8"))
            stable["synthetic"] = result.get("synthetic")
            stable["checkpoints"] = result.get("session", {}).get("checkpoints")
        summary["stable_digest"] = object_hash(stable)
        write_json(path / "failure_diagnostics.json", {"errors": errors})
        event(path / "journal.jsonl", "FINALIZING_" + summary["status"])
        write_json(path / "run_summary.json", summary); finalize(path)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["qualify", "worker"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    args = parser.parse_args()
    if args.action == "worker":
        return worker(args.run_id, args.scenario)
    path = qualify(args.run_id, args.scenario)
    summary = json.loads((path / "run_summary.json").read_text("utf-8"))
    print(path.relative_to(ROOT).as_posix())
    print(summary["status"] + "; ENV diagnostic only; B2 NOT AUTHORIZED")
    return 0 if summary["status"] == "PASS" and verify_evidence(path) else 2


if __name__ == "__main__":
    raise SystemExit(main())
