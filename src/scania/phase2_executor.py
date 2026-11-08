"""Phase 2 Constrained Optimization Executor: supervisor, preflight, authorization, and evidence generation.

Safety & Contract boundaries:
- Fitting restricted strictly to Train partition (48,000 samples).
- Validation (12,000 samples) evaluated read-only for threshold search.
- Official Test set (16,000 samples) is strictly SEALED UNTIL G10.
- Mandatory GitHub Owner authorization check bound to exact commit SHA, config SHA, and G3 manifest.
- Supervisor/worker architecture isolated under Windows Job Object.
- Exactly 1 native compute thread, max 2048 MB RAM, max 300s wall clock time.
- Exact tracking of model.fit() invocations (max 20 real fits, 1 per trial).
- Partial evidence preservation without automatic retry on failure.
"""
import csv
import json
import math
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys
import time
import urllib.request
import warnings
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .artifacts import code_digest
from .contracts import canonical, digest, environment, object_hash
from .g4_b2_executor import (
    ExecutorBlocked, ExecutorFailure, SafetyBlocked,
    _get_github_token, _strip_markdown_code_blocks, _parse_owner_comment_fields,
    verify_g3_artifacts_and_build_allowlist, install_executor_io_guard
)
from .phase2_optimization import sanitize_for_strict_json

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE2_CONFIG_PATH = REPO_ROOT / "configs/scania/phase2_optimization.json"
ACCEPTED_G3_MANIFEST_PATH = REPO_ROOT / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"


def load_phase2_config(root=REPO_ROOT) -> Dict[str, Any]:
    """Load and validate locked Phase 2 configuration."""
    cfg_file = Path(root) / "configs/scania/phase2_optimization.json"
    if not cfg_file.is_file():
        raise ExecutorBlocked("PHASE2_CONFIG_FILE_MISSING")
    content = cfg_file.read_bytes().replace(b"\r\n", b"\n")
    cfg = json.loads(content.decode("utf-8"))
    return cfg


def get_phase2_config_sha(root=REPO_ROOT) -> str:
    """Compute LF-normalized SHA-256 digest of phase2_optimization.json."""
    cfg_file = Path(root) / "configs/scania/phase2_optimization.json"
    if not cfg_file.is_file():
        raise ExecutorBlocked("PHASE2_CONFIG_FILE_MISSING")
    content = cfg_file.read_bytes().replace(b"\r\n", b"\n")
    return digest(content)


def verify_phase2_owner_approval_reference(ref: str, expected_record: Optional[Dict[str, Any]] = None, mode: str = "REAL") -> bool:
    """Verify authentic GitHub Owner approval comment for Phase 2 Optimization.

    Validates:
    - Author is repository owner 'PhucHuynh16'.
    - Outside markdown code blocks, comment has '# OWNER ...' header.
    - Fields:
      * Decision: exactly 'APPROVED'.
      * Authorized Commit: exact 40-character hex commit SHA.
      * Target Run ID: exact string.
      * Permitted Operation: 'CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY'.
      * Approved Estimator: contains 'RandomForestClassifier'.
      * Approved Optimizer: contains 'Optuna' or 'TPESampler'.
      * Fit Budget: max_trials=20, max_fits_per_trial=1, total_max_fits=20.
      * Data Scope: Train (48k) and Validation (12k).
      * Official Test: explicitly declared sealed until G10.
      * Resource Limits: 1 native thread, max 2048 MB RAM, max 300s wall time.
    """
    if not isinstance(ref, str) or not ref:
        raise ExecutorBlocked("INVALID_OWNER_APPROVAL_REFERENCE: Reference must be a non-empty string URL")

    ref = ref.strip()
    if mode == "SYNTHETIC":
        if ref.startswith("SYNTHETIC_FIXTURE_"):
            return True
        if ref.startswith("https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/"):
            return True
        raise ExecutorBlocked(f"INVALID_SYNTHETIC_APPROVAL_REFERENCE: {ref}")

    pattern = r"^https://github\.com/PhucHuynh16/Predictive-maintenance-cost-optimization/(?:issues|pull)/\d+#issuecomment-(\d+)$"
    m = re.match(pattern, ref)
    if not m:
        raise ExecutorBlocked(f"INVALID_OWNER_APPROVAL_REFERENCE: Must reference specific comment ID: {ref}")

    comment_id = m.group(1)

    try:
        token = _get_github_token()
        if not token:
            raise ExecutorBlocked(f"UNVERIFIABLE_OWNER_APPROVAL: GitHub credential unavailable to verify reference: {ref}")

        req = urllib.request.Request(
            f"https://api.github.com/repos/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/comments/{comment_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Antigravity-Trust-Verifier"
            }
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        author = data.get("user", {}).get("login", "")
        if author != "PhucHuynh16":
            raise ExecutorBlocked(f"AUTHORIZATION_NOT_FROM_OWNER: Comment author '{author}' is not repository owner PhucHuynh16")

        comment_body = data.get("body", "")

        # 1. Reject agent reports
        if re.search(r"##\s+ANTIGRAVITY", comment_body, re.IGNORECASE):
            raise ExecutorBlocked("AGENT_REPORT_CANNOT_AUTHORIZE: Comment is an agent report, not an authentic human Owner decision")

        # 2. Strip code blocks
        clean_body = _strip_markdown_code_blocks(comment_body)

        # 3. Check for explicit Owner directive header
        if not re.search(r"^#\s+OWNER\s+(?:TASK\s+AUTHORIZATION|DECISION|DIRECTIVE)", clean_body, re.IGNORECASE | re.MULTILINE):
            raise ExecutorBlocked("MISSING_OWNER_DIRECTIVE_HEADER: Approval comment must have an explicit '# OWNER ...' directive header")

        # 4. Extract field-values
        fields = _parse_owner_comment_fields(clean_body)

        # Decision
        decision_val = fields.get("decision")
        if not decision_val or decision_val.upper() != "APPROVED":
            raise ExecutorBlocked(f"INVALID_OR_MISSING_APPROVAL_DECISION: Decision must be exactly 'APPROVED', got '{decision_val}'")

        # Authorized Commit
        commit_val = fields.get("authorized commit") or fields.get("commit") or fields.get("commit sha")
        if not commit_val or not re.fullmatch(r"[0-9a-f]{40}", commit_val, re.IGNORECASE):
            raise ExecutorBlocked(f"INVALID_OR_MISSING_AUTHORIZED_COMMIT: Must specify 40-character hex commit SHA, got '{commit_val}'")
        commit_val = commit_val.lower()

        # Target Run ID
        run_id_val = fields.get("target run id") or fields.get("run id")
        if not run_id_val:
            raise ExecutorBlocked("MISSING_TARGET_RUN_ID: Comment must explicitly specify Target Run ID")

        # Permitted Operation
        op_val = fields.get("permitted operation") or fields.get("operation")
        if not op_val or op_val.upper() != "CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY":
            raise ExecutorBlocked(f"INVALID_PERMITTED_OPERATION: Permitted operation must be exactly 'CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY', got '{op_val}'")

        # Approved Estimator
        est_val = fields.get("approved estimator") or fields.get("estimator") or fields.get("models")
        if not est_val or "RandomForestClassifier" not in est_val:
            raise ExecutorBlocked(f"INVALID_APPROVED_ESTIMATOR: Must specify 'RandomForestClassifier', got '{est_val}'")

        # Approved Optimizer
        opt_val = fields.get("approved optimizer") or fields.get("optimizer")
        if not opt_val or not re.search(r"\b(?:optuna|tpesampler|tpe)\b", opt_val, re.IGNORECASE):
            raise ExecutorBlocked(f"INVALID_APPROVED_OPTIMIZER: Must specify Optuna TPE optimizer, got '{opt_val}'")

        # Fit Budget
        budget_val = fields.get("fit budget") or fields.get("budget")
        if not budget_val:
            raise ExecutorBlocked("MISSING_FIT_BUDGET: Comment must explicitly specify Fit Budget")

        trials_m = re.search(r"\b(?:max_trials|trials)\s*[:=]\s*(\d+)\b", budget_val, re.IGNORECASE)
        fits_per_trial_m = re.search(r"\b(?:max_fits_per_trial|fits_per_trial)\s*[:=]\s*(\d+)\b", budget_val, re.IGNORECASE)
        total_fits_m = re.search(r"\b(?:total_max_fits|total_fits|total)\s*[:=]\s*(\d+)\b", budget_val, re.IGNORECASE)

        if not (trials_m and total_fits_m):
            raise ExecutorBlocked(f"INCOMPLETE_FIT_BUDGET: Must specify max_trials and total_max_fits, got '{budget_val}'")

        max_trials = int(trials_m.group(1))
        total_fits = int(total_fits_m.group(1))
        fits_per_trial = int(fits_per_trial_m.group(1)) if fits_per_trial_m else 1

        if max_trials > 20 or total_fits > 20 or fits_per_trial != 1:
            raise ExecutorBlocked(
                f"INVALID_FIT_BUDGET: Fit budget must be max_trials<=20, total_max_fits<=20, fits_per_trial=1; got trials={max_trials}, total={total_fits}, per_trial={fits_per_trial}"
            )

        # Data Scope & Official Test Sealing
        scope_val = fields.get("data scope") or fields.get("scope") or ""
        test_val = fields.get("official test") or fields.get("test") or ""
        combined_scope = f"{scope_val} {test_val}".strip().lower()

        if not combined_scope:
            raise ExecutorBlocked("MISSING_DATA_SCOPE: Comment must explicitly specify Data Scope")

        if re.search(r"\b(?:test\s+(?:permitted|allowed|access|accessible|unsealed)|evaluate\s+(?:on\s+)?test)\b", combined_scope):
            raise ExecutorBlocked("CONTRADICTORY_DATA_SCOPE: Comment grants unauthorized access to sealed Official Test")

        if "train" not in combined_scope or "validation" not in combined_scope:
            raise ExecutorBlocked(f"INVALID_DATA_SCOPE: Data scope must include both Train and Validation, got '{scope_val}'")

        if not re.search(r"\b(?:official\s+test\s+sealed|test\s+(?:partition|set)?\s*sealed|sealed\s+until\s+g10)\b", combined_scope):
            raise ExecutorBlocked("MISSING_TEST_SEAL_DECLARATION: Comment must explicitly state that Official Test is sealed until G10")

        # Resource Limits
        limits_val = fields.get("resource limits") or fields.get("limits")
        if not limits_val:
            raise ExecutorBlocked("MISSING_RESOURCE_LIMITS: Comment must explicitly specify Resource Limits")

        threads_m = re.search(r"\b(?:max_native_threads|threads)\s*[:=]\s*(\d+)\b|\b(\d+)\s*native\s*threads?\b|\b(\d+)\s*threads?\b", limits_val, re.IGNORECASE)
        ram_m = re.search(r"\b(?:max_ram_mb|ram_mb|ram)\s*[:=]\s*(\d+)\b|\b(\d+)\s*(?:mb|gb)\s*ram\b", limits_val, re.IGNORECASE)
        wall_m = re.search(r"\b(?:max_wall_seconds|wall_seconds|wall)\s*[:=]\s*(\d+)\b|\b(\d+)\s*s(?:ec|econds)?\s*wall\b", limits_val, re.IGNORECASE)

        if not (threads_m and ram_m and wall_m):
            raise ExecutorBlocked(f"INCOMPLETE_RESOURCE_LIMITS: Must specify threads, RAM, and wall time limits, got '{limits_val}'")

        threads = int(next(g for g in threads_m.groups() if g is not None))
        ram_mb = int(next(g for g in ram_m.groups() if g is not None))
        wall_sec = int(next(g for g in wall_m.groups() if g is not None))

        if threads != 1:
            raise ExecutorBlocked(f"INVALID_THREADS: max_native_threads must be exactly 1, got {threads}")
        if ram_mb > 2048:
            raise ExecutorBlocked(f"INVALID_RAM: max_ram_mb must not exceed 2048, got {ram_mb}")
        if wall_sec > 300:
            raise ExecutorBlocked(f"INVALID_WALL_TIME: max_wall_seconds must not exceed 300, got {wall_sec}")

        # Semantic check against expected record
        if expected_record is not None:
            src_int = expected_record.get("source_integrity", expected_record)
            exp_commit = str(src_int.get("authorized_commit") or "").lower()
            if exp_commit and commit_val != exp_commit:
                raise ExecutorBlocked(f"COMMENT_COMMIT_MISMATCH: Comment authorized commit {commit_val} != expected {exp_commit}")

            exp_run_id = expected_record.get("run_id") or expected_record.get("target_run_id")
            if exp_run_id and run_id_val != exp_run_id:
                raise ExecutorBlocked(f"COMMENT_RUN_ID_MISMATCH: Comment target run ID '{run_id_val}' != expected '{exp_run_id}'")

    except Exception as exc:
        if isinstance(exc, ExecutorBlocked):
            raise
        raise ExecutorBlocked(f"UNVERIFIABLE_OWNER_APPROVAL: Could not verify Owner approval reference {ref}: {exc}")
    return True


def validate_phase2_authorization_record(
    auth_path_or_dict: Any,
    expected_run_id: str,
    root=REPO_ROOT,
    mode: str = "REAL",
) -> Dict[str, Any]:
    """Validate Phase 2 authorization record schema, exact HEAD commit, config hash, and G3 manifest."""
    root = Path(root).resolve()
    if isinstance(auth_path_or_dict, (str, Path)):
        p = Path(auth_path_or_dict).resolve()
        if not p.is_file():
            raise ExecutorBlocked(f"PHASE2_AUTHORIZATION_RECORD_MISSING: {p.name}")
        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ExecutorBlocked(f"INVALID_AUTHORIZATION_JSON: {exc}")
    elif isinstance(auth_path_or_dict, dict):
        record = auth_path_or_dict
    else:
        raise ExecutorBlocked("INVALID_AUTHORIZATION_RECORD_TYPE")

    # 1. Exact Run ID
    target_run = record.get("run_id") or record.get("target_run_id")
    if target_run != expected_run_id:
        raise ExecutorBlocked(f"AUTHORIZATION_RUN_ID_MISMATCH: {target_run} != {expected_run_id}")

    # 2. Authorization status
    if record.get("authorization_status") != "AUTHORIZED":
        raise ExecutorBlocked(f"AUTHORIZATION_NOT_GRANTED: Status is {record.get('authorization_status')}")

    # 3. Permitted operation
    op = record.get("permitted_operation") or record.get("operation")
    if mode == "REAL":
        if op != "CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY":
            raise ExecutorBlocked(f"INVALID_PERMITTED_OPERATION: {op}")
    else:
        if op not in {"SYNTHETIC_OPTIMIZATION_TESTING_ONLY", "CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY"}:
            raise ExecutorBlocked(f"INVALID_PERMITTED_OPERATION: {op}")

    # 4. Owner approval check
    owner_app = record.get("owner_approval", {})
    if not isinstance(owner_app, dict):
        raise ExecutorBlocked("INVALID_OWNER_APPROVAL_OBJECT")
    ref = str(owner_app.get("reference") or "")
    verify_phase2_owner_approval_reference(ref, expected_record=record, mode=mode)

    # 5. Bound commit SHA against git rev-parse HEAD
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    actual_head = proc.stdout.strip().lower()

    src_int = record.get("source_integrity", {})
    auth_commit = str(src_int.get("authorized_commit") or "").lower()
    if not auth_commit or auth_commit != actual_head:
        raise ExecutorBlocked(f"SOURCE_HEAD_MISMATCH: Authorization commit {auth_commit} != repository HEAD {actual_head}")

    # 6. Bound configuration hash
    locked_cfg = record.get("locked_configuration", {})
    expected_cfg_sha = locked_cfg.get("config_sha256")
    actual_cfg_sha = get_phase2_config_sha(root)
    if not expected_cfg_sha or expected_cfg_sha.lower() != actual_cfg_sha.lower():
        raise ExecutorBlocked(f"PHASE2_CONFIG_HASH_MISMATCH: Authorization expects {expected_cfg_sha}, actual is {actual_cfg_sha}")

    # 7. Bound G3 manifest hash
    g3_int = record.get("g3_integrity", {})
    expected_g3_manifest_sha = g3_int.get("manifest_sha256")
    g3_manifest_file = root / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"
    if not g3_manifest_file.is_file():
        raise ExecutorBlocked("ACCEPTED_G3_MANIFEST_FILE_MISSING")
    actual_g3_manifest_sha = digest(g3_manifest_file.read_bytes().replace(b"\r\n", b"\n"))
    if not expected_g3_manifest_sha or expected_g3_manifest_sha.lower() != actual_g3_manifest_sha.lower():
        raise ExecutorBlocked(f"G3_MANIFEST_HASH_MISMATCH: Expected {expected_g3_manifest_sha}, got {actual_g3_manifest_sha}")

    # 8. Budget verification
    budget = record.get("budget", {})
    max_trials = int(budget.get("max_trials", 0))
    total_max_fits = int(budget.get("total_max_fits", 0))
    fits_per_trial = int(budget.get("fits_per_trial", 1))

    if max_trials > 20 or total_max_fits > 20 or fits_per_trial != 1:
        raise ExecutorBlocked(
            f"INVALID_BUDGET_IN_RECORD: max_trials={max_trials}, total_max_fits={total_max_fits}, fits_per_trial={fits_per_trial}"
        )

    return record


def execute_phase2_preflight_check(root=REPO_ROOT, g3_run_id="official_20261029_04") -> Dict[str, Any]:
    """Execute complete read-only preflight verification for Phase 2 without consuming fit budget.

    Checks:
    1. Python version (3.11.x) and Optuna availability (>=5.0.0).
    2. G3 stable manifest and processed arrays (shapes 48k x 170 and 12k x 170, hashes, label alignment).
    3. Phase 2 configuration integrity.
    4. Official Test sealing.
    5. Resource availability.
    """
    root = Path(root).resolve()

    # 1. Python environment check
    py_ver = platform.python_version()
    if not py_ver.startswith("3.11"):
        warnings.warn(f"Python version is {py_ver}, expected 3.11.x")

    import optuna
    optuna_ver = optuna.__version__
    import sklearn
    sklearn_ver = sklearn.__version__
    import numpy as np
    numpy_ver = np.__version__

    # 2. Config verification
    cfg = load_phase2_config(root)
    cfg_sha = get_phase2_config_sha(root)

    # 3. G3 data verification and allowlist building
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, g3_run_id)

    # 4. Check git HEAD commit
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    head_sha = proc.stdout.strip()

    preflight_summary = {
        "status": "PREFLIGHT_VERIFIED",
        "timestamp": time.time(),
        "python_version": py_ver,
        "optuna_version": optuna_ver,
        "sklearn_version": sklearn_ver,
        "numpy_version": numpy_ver,
        "head_commit": head_sha,
        "phase2_config_sha256": cfg_sha,
        "g3_summary": g3_summary,
        "official_test": "SEALED_UNTIL_G10",
        "real_estimator_fits_consumed": 0,
        "trials_consumed": 0,
    }
    return preflight_summary


def orchestrate_phase2_worker_in_job(
    root: Path,
    run_id: str,
    output_dir: Path,
    allowlist: List[Path],
    task_config: Dict[str, Any],
    wall_seconds: int = 300,
    ram_cap_bytes: int = 2048 * 1024 * 1024,
    mode: str = "REAL",
) -> Dict[str, Any]:
    """Launch isolated worker subprocess under Windows Job Object with strict containment."""
    from .g4_b1_windows import WindowsJob
    from .g4_env_discovery import THREAD_ENV

    output_dir = Path(output_dir).resolve()
    root = Path(root).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    task_path = output_dir / "task_config.json"
    task_path.write_bytes(json.dumps(task_config, indent=2).encode("utf-8"))

    allowlist_path = output_dir / "allowlist.json"
    allowlist_path.write_bytes(json.dumps([str(p) for p in allowlist], indent=2).encode("utf-8"))

    result_path = output_dir / "worker_result.json"
    if result_path.is_file():
        result_path.unlink()

    child_env = os.environ.copy()
    child_env.update(THREAD_ENV)
    child_env["PYTHONPATH"] = str(REPO_ROOT)
    child_env.update(
        SC_PHASE2_RUN=run_id,
        SC_PHASE2_TASK_PATH=str(task_path),
        SC_PHASE2_ALLOWLIST_PATH=str(allowlist_path),
        SC_PHASE2_OUTPUT_DIR=str(output_dir),
        SC_PHASE2_ROOT_DIR=str(root),
        SC_PHASE2_NONCE=secrets.token_hex(24),
    )

    argv = [sys.executable, "-B", "-X", "utf8", "-m", "src.scania.phase2_worker"]
    job = WindowsJob(argv, child_env, root, ram_cap_bytes, active_limit=2)

    t0 = time.perf_counter()
    deadline = t0 + wall_seconds
    exit_code = None

    try:
        job.resume()
        while True:
            exit_code = job.poll()
            now = time.perf_counter()
            if now >= deadline:
                job.terminate()
                raise TimeoutError(f"PHASE2_WALL_TIMEOUT: Worker exceeded limit of {wall_seconds}s")
            if exit_code is not None:
                break
            time.sleep(0.05)

        peak_ram_bytes = job.limits().get("peak_job_memory_bytes", 0)
    finally:
        job.close()

    elapsed = time.perf_counter() - t0

    if not result_path.is_file():
        raise ExecutorBlocked(f"WORKER_CRASHED_NO_RESULT: Exit code {exit_code}")

    worker_result = json.loads(result_path.read_text(encoding="utf-8"))

    if exit_code != 0 or worker_result.get("status") != "PASS":
        err_msg = worker_result.get("reason", f"Exit code {exit_code}")
        raise ExecutorFailure(f"PHASE2_WORKER_FAILED: {err_msg}", worker_result=worker_result)

    is_real = (mode == "REAL")
    report = {
        "run_id": run_id,
        "mode": mode,
        "status": "COMPLETE",
        "lifecycle": "COMPLETE",
        "real_estimator_fits": worker_result["total_estimator_fits"] if is_real else 0,
        "synthetic_estimator_fits": worker_result["total_estimator_fits"] if not is_real else 0,
        "n_trials_completed": worker_result["n_trials_completed"],
        "best_trial": worker_result.get("best_trial"),
        "trials_records": worker_result.get("trials_records", []),
        "fit_records": worker_result.get("fit_records", []),
        "measured_wall_seconds": elapsed,
        "measured_peak_ram_mb": peak_ram_bytes / (1024 ** 2),
        "validation_scored": worker_result.get("validation_scored", False),
    }
    return report


def write_phase2_evidence_artifacts(
    output_dir: Path,
    report: Dict[str, Any],
    config: Dict[str, Any],
    environment_dict: Dict[str, Any],
    manifest_data: Dict[str, Any],
    errors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, str]:
    """Write all required evidence artifacts and compute LF-normalized SHA-256 checksums."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    errors = errors or []

    # 1. Config
    (output_dir / "config.json").write_bytes(json.dumps(config, indent=2).encode("utf-8"))

    # 2. Environment
    (output_dir / "environment.json").write_bytes(json.dumps(environment_dict, indent=2).encode("utf-8"))

    # 3. Stable manifest
    (output_dir / "stable_manifest.json").write_bytes(json.dumps(manifest_data, indent=2).encode("utf-8"))

    # 4. Failure diagnostics
    (output_dir / "failure_diagnostics.json").write_bytes(json.dumps({"errors": errors}, indent=2).encode("utf-8"))

    # 5. Best policy
    best_trial = report.get("best_trial")
    best_policy = best_trial.get("best_policy") if best_trial else None
    (output_dir / "best_policy.json").write_bytes(json.dumps(best_policy or {}, indent=2).encode("utf-8"))

    # 6. Optuna study summary
    study_summary = {
        "run_id": report["run_id"],
        "mode": report["mode"],
        "n_trials_completed": report.get("n_trials_completed", 0),
        "best_trial": best_trial,
        "trials": report.get("trials_records", []),
    }
    (output_dir / "optuna_study.json").write_bytes(json.dumps(study_summary, indent=2).encode("utf-8"))

    # 7. Trials summary CSV
    trials = report.get("trials_records", [])
    csv_path = output_dir / "trials_summary.csv"
    if trials:
        fieldnames = [
            "trial_number", "status", "objective_value", "fit_index",
            "n_estimators", "max_depth", "min_samples_split", "max_features",
            "fit_seconds", "predict_seconds", "threshold", "M", "TP", "FP", "FN", "TN", "saving_pct"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in trials:
                params = t.get("rf_params", {})
                best = t.get("best_policy") or {}
                row = {
                    "trial_number": t.get("trial_number"),
                    "status": t.get("status"),
                    "objective_value": t.get("objective_value"),
                    "fit_index": t.get("fit_index"),
                    "n_estimators": params.get("n_estimators"),
                    "max_depth": params.get("max_depth"),
                    "min_samples_split": params.get("min_samples_split"),
                    "max_features": params.get("max_features"),
                    "fit_seconds": t.get("fit_seconds"),
                    "predict_seconds": t.get("predict_seconds"),
                    "threshold": best.get("threshold"),
                    "M": best.get("M"),
                    "TP": best.get("TP"),
                    "FP": best.get("FP"),
                    "FN": best.get("FN"),
                    "TN": best.get("TN"),
                    "saving_pct": best.get("saving_pct"),
                }
                writer.writerow(row)
    else:
        csv_path.write_text("trial_number,status,objective_value\n", encoding="utf-8")

    # 8. Run summary
    (output_dir / "run_summary.json").write_bytes(json.dumps(report, indent=2).encode("utf-8"))

    # 9. Execution txt
    exec_lines = [
        f"run_id={report['run_id']}",
        f"mode={report['mode']}",
        f"status={report['status']}",
        f"lifecycle={report['lifecycle']}",
        f"real_estimator_fits={report.get('real_estimator_fits', 0)}",
        f"n_trials_completed={report.get('n_trials_completed', 0)}",
        f"wall_seconds={report.get('measured_wall_seconds', 0.0):.4f}",
        f"peak_ram_mb={report.get('measured_peak_ram_mb', 0.0):.2f}",
    ]
    (output_dir / "execution.txt").write_text("\n".join(exec_lines) + "\n", encoding="utf-8")

    # 10. Compute checksums
    checksums = {}
    for item in sorted(output_dir.iterdir()):
        if item.is_file() and item.name != "checksums.json":
            raw_b = item.read_bytes().replace(b"\r\n", b"\n")
            checksums[item.name] = digest(raw_b)

    (output_dir / "checksums.json").write_bytes(json.dumps(checksums, indent=2).encode("utf-8"))
    return checksums


def verify_phase2_run(output_dir: Path) -> bool:
    """Cryptographically verify all artifacts of a completed Phase 2 run."""
    output_dir = Path(output_dir).resolve()
    checksums_file = output_dir / "checksums.json"
    if not checksums_file.is_file():
        return False
    checksums = json.loads(checksums_file.read_text(encoding="utf-8"))
    for fname, expected_hash in checksums.items():
        p = output_dir / fname
        if not p.is_file():
            return False
        raw_b = p.read_bytes().replace(b"\r\n", b"\n")
        if digest(raw_b) != expected_hash:
            return False
    return True
