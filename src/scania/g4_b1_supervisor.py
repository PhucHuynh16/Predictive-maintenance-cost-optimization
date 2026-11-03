"""B1 safety qualification, stdlib-only supervisor. No official fitting path."""
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import secrets
import sys
import time
from .g4_b1_contract import (profile, validate_profile, child_environment, SafetyBlocked,
                             protected_snapshot, source_manifest, object_sha)
from .g4_b1_evidence import Evidence
from .g4_b1_windows import WindowsJob, memory_snapshot


def environment():
    names = ("numpy", "scipy", "scikit-learn", "threadpoolctl", "joblib", "pandas",
             "python-dateutil", "six", "tzdata", "pytest", "iniconfig", "packaging", "pluggy", "Pygments", "colorama")
    return dict(locked=dict(python=platform.python_version(), packages={n: version(n) for n in names}),
                platform=platform.platform())


def verify_environment(root):
    actual = environment()
    expected = json.loads((Path(root) / "configs/scania/g4_baselines.json").read_text(encoding="utf-8"))["environment"]
    if actual["locked"] != expected:
        raise SafetyBlocked("DEPENDENCY_VERSION_MISMATCH")
    return actual


def run_qualification(root, *, run_id, scenario="normal", config=None):
    """Only fixed mock/readonly import profiles. All real slot attempts blocked.

    config exists for strict validation tests, not as a CLI policy override.
    Lowering memory/time or forging authorization is rejected before launch.
    """
    root = Path(root).resolve()
    out = Evidence(root, run_id)
    begin = time.perf_counter()
    report = dict(kind="B1_SYNTHETIC_INFRASTRUCTURE_ONLY", scenario=scenario,
                  status="RUNNING", lifecycle="RUNNING", real_estimator_fits=0,
                  validation_scored=False, official_test="SEALED_UNTIL_G10",
                  b2_authorized=False, worker_started=False, job_empty_verified=False,
                  thread_verification="NOT_APPLICABLE_STDLIB_MOCK",
                  worker_wall_seconds=None, cleanup_seconds=None, total_seconds=None)
    resources, errors, job, before, source = {}, [], None, None, None
    stage = "PROFILE_GATE"
    out.event(stage)
    try:
        expected = profile(scenario)
        cfg = validate_profile(expected if config is None else config)
        out.json("config.json", cfg)
        report["config_sha256"] = object_sha(cfg)
        stage = "SOURCE_GUARD"
        source = source_manifest(root); before = protected_snapshot(root)
        out.json("source_manifest.json", source)
        out.json("environment.json", verify_environment(root))
        report["source_digest"] = source["source_digest"]
        stage = "RESOURCE_GATE"
        resources["before"] = memory_snapshot()
        if resources["before"]["available_physical_bytes"] < cfg["minimum_available_ram_bytes"]:
            raise SafetyBlocked("INSUFFICIENT_MEMORY_SYNTHETIC_PROFILE")
        stage = "CREATE_SUSPENDED_JOB"
        env = child_environment()
        env.update(SC_G4_B1_RUN=run_id, SC_G4_B1_SCENARIO=scenario,
                   SC_G4_B1_NONCE=secrets.token_hex(24))
        # All launch timing belongs to the same absolute wall deadline.
        start = time.perf_counter(); deadline = start + cfg["wall_seconds"]
        argv = [sys.executable, "-B", "-X", "utf8", "-m", "src.scania.g4_b1_worker"]
        job = WindowsJob(argv, env, root, cfg["job_memory_bytes"], cfg["active_process_limit"])
        resources["job_limits_before_resume"] = job.limits()
        out.event("JOB_VERIFIED_BEFORE_RESUME", job_limits=resources["job_limits_before_resume"])
        if time.perf_counter() >= deadline:
            raise TimeoutError("RUN_WALL_TIMEOUT_BEFORE_RESUME")
        stage = "WORKER_RUNNING"
        job.resume(); report["worker_started"] = True
        out.event(stage, pid=int(job.pi.pid))
        while True:
            code = job.poll()
            now = time.perf_counter()
            if now >= deadline:
                raise TimeoutError("RUN_WALL_TIMEOUT")
            if code is not None:
                break
            time.sleep(min(0.02, deadline - now))
        report["worker_exit_code"] = code
        report["worker_wall_seconds"] = now - start
        stage = "WORKER_RESULT"
        result_path = out.path / "worker_result.json"
        if not result_path.is_file():
            raise RuntimeError("WORKER_CRASH_OR_MISSING_RESULT")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if (result.get("scenario") != scenario or result.get("kind") != cfg["kind"]
                or type(result.get("real_estimator_fits")) is not int or result["real_estimator_fits"] != 0
                or result.get("validation_scored") is not False):
            raise RuntimeError("WORKER_RESULT_CONTRACT_MISMATCH")
        if result.get("status") != "PASS" or code != 0:
            if scenario == "thread_probe":
                report["thread_verification"] = "BLOCKED"
                raise SafetyBlocked("THREAD_POLICY_NOT_VERIFIED")
            raise RuntimeError("WORKER_FAILURE")
        if scenario == "thread_probe":
            if result.get("thread_verification", {}).get("status") != "PASS":
                raise SafetyBlocked("THREAD_POLICY_NOT_VERIFIED")
            report["thread_verification"] = "VERIFIED_IMPORT_ONLY_NOT_REAL_FIT"
        report["fixture_digest"] = result.get("fixture_digest")
        stage = "POSTCHECK"
        if protected_snapshot(root) != before or source_manifest(root)["source_digest"] != source["source_digest"]:
            raise SafetyBlocked("SOURCE_OR_PROTECTED_POSTCHECK_MISMATCH")
        report.update(status="PASS", lifecycle="COMPLETE")
    except (Exception, KeyboardInterrupt) as exc:
        report.update(status="BLOCKED" if isinstance(exc, SafetyBlocked) else "FAILED", lifecycle="FAILED")
        reason = str(exc) if isinstance(exc, (SafetyBlocked, TimeoutError)) else "SUPERVISOR_OR_WORKER_ERROR"
        errors.append(dict(stage=stage, error_type=type(exc).__name__, reason=reason,
                           winerror=getattr(exc, "winerror", None)))
        out.event("STOPPED", stage_failed=stage, reason=reason)
    finally:
        if job is not None:
            clean_start = time.perf_counter()
            try:
                if job.accounting()["active_processes"]:
                    job.terminate()
                report["job_empty_verified"] = job.wait_empty(5.0)
                resources["job_final"] = job.accounting()
                resources["job_limits_final"] = job.limits()
                if not report["job_empty_verified"]:
                    raise RuntimeError("TERMINATION_NOT_CONFIRMED")
            except Exception as exc:
                report.update(status="FAILED", lifecycle="FAILED", job_empty_verified=False)
                errors.append(dict(stage="CLEANUP", error_type=type(exc).__name__, reason="TERMINATION_NOT_CONFIRMED"))
            finally:
                try:
                    job.close()
                except Exception as exc:
                    report.update(status="FAILED", lifecycle="FAILED")
                    errors.append(dict(stage="CLOSE_HANDLES", error_type=type(exc).__name__, reason="JOB_CLOSE_FAILED"))
            report["cleanup_seconds"] = time.perf_counter() - clean_start
            if report["worker_wall_seconds"] is None:
                report["worker_wall_seconds"] = clean_start - start
        if before is not None:
            try:
                resources["protected_before"] = before
                resources["protected_after"] = protected_snapshot(root)
                if (resources["protected_after"] != before
                        or source_manifest(root)["source_digest"] != source["source_digest"]):
                    raise SafetyBlocked("SOURCE_OR_PROTECTED_POSTCHECK_MISMATCH")
            except Exception as exc:
                report.update(status="FAILED", lifecycle="FAILED")
                errors.append(dict(stage="FINAL_POSTCHECK", error_type=type(exc).__name__, reason="PROTECTED_POSTCHECK_FAILED"))
        if report["status"] == "PASS" and not report["job_empty_verified"]:
            report.update(status="FAILED", lifecycle="FAILED")
        report["total_seconds"] = time.perf_counter() - begin
        report["stable_digest"] = object_sha(dict(scenario=scenario, status=report["status"],
                 fixture_digest=report.get("fixture_digest"), source_digest=report.get("source_digest"),
                 config_sha256=report.get("config_sha256")))
        out.event("FINALIZING", status=report["status"])
        out.json("resource_usage.json", resources)
        out.json("failure_diagnostics.json", dict(errors=errors, metrics=None, metrics_reason="NOT_APPLICABLE_NO_ML"))
        out.json("run_summary.json", report)
        out.finalize()
    return out.path
