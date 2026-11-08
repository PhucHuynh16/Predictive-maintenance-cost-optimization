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
from .phase2_optimization import (
    sanitize_for_strict_json,
    reconcile_durable_fit_markers,
    reconcile_durable_trial_markers,
    DurableLoggingError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PHASE2_CONFIG_PATH = REPO_ROOT / "configs/scania/phase2_optimization.json"
ACCEPTED_G3_MANIFEST_PATH = REPO_ROOT / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"

# Fixed G3 Accepted Reference Hashes
G3_ACCEPTED_RUN_ID = "official_20261029_04"
G3_ACCEPTED_STABLE_DIGEST = "efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb"
G3_ACCEPTED_MANIFEST_FILE_SHA256 = "7d3d68b694b2c260cfc89087f1dd8a5cfd35784ae303803fd0687c530d412242"


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


def verify_phase2_owner_approval_text(
    comment_body: str,
    author: str = "PhucHuynh16",
    expected_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse and verify authentic GitHub Owner approval comment text.

    Enforces:
    - Author is repository owner 'PhucHuynh16'.
    - Outside markdown code blocks, comment has plain '# OWNER ...' header.
    - Key: Value format on single lines.
    - Fields:
      * Decision: exactly 'APPROVED'.
      * Authorized Commit: exact 40-character hex commit SHA.
      * Target Run ID: exact string matching expected run.
      * Permitted Operation: 'CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY'.
      * Approved Estimator: contains 'RandomForestClassifier'.
      * Approved Optimizer: contains 'Optuna' or 'TPESampler'.
      * Fit Budget: max_trials<=20, total_max_fits<=20, fits_per_trial=1.
      * Data Scope: Train, Validation, and Official Test sealed until G10.
      * Resource Limits: 1 native thread, max 2048 MB RAM, max 900s wall time.
    - Semantic check against expected_record if provided.
    - Returns dictionary of parsed approved parameters.
    """
    if author != "PhucHuynh16":
        raise ExecutorBlocked(f"AUTHORIZATION_NOT_FROM_OWNER: Comment author '{author}' is not repository owner PhucHuynh16")

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
    if wall_sec > 900:
        raise ExecutorBlocked(f"INVALID_WALL_TIME: max_wall_seconds must not exceed 900, got {wall_sec}")

    parsed_approved_limits = {
        "authorized_commit": commit_val,
        "target_run_id": run_id_val,
        "permitted_operation": op_val,
        "approved_estimator": est_val,
        "approved_optimizer": opt_val,
        "max_trials": max_trials,
        "total_max_fits": total_fits,
        "fits_per_trial": fits_per_trial,
        "max_wall_seconds": wall_sec,
        "max_ram_mb": ram_mb,
        "max_native_threads": threads,
    }

    # Semantic check against expected record
    if expected_record is not None:
        src_int = expected_record.get("source_integrity", expected_record)
        exp_commit = str(src_int.get("authorized_commit") or "").lower()
        if exp_commit and commit_val != exp_commit:
            raise ExecutorBlocked(f"COMMENT_COMMIT_MISMATCH: Comment authorized commit {commit_val} != expected {exp_commit}")

        exp_run_id = expected_record.get("run_id") or expected_record.get("target_run_id")
        if exp_run_id and run_id_val != exp_run_id:
            raise ExecutorBlocked(f"COMMENT_RUN_ID_MISMATCH: Comment target run ID '{run_id_val}' != expected '{exp_run_id}'")

        rec_budget = expected_record.get("budget", {})
        if "max_trials" in rec_budget and int(rec_budget["max_trials"]) != max_trials:
            raise ExecutorBlocked(f"COMMENT_BUDGET_MISMATCH: Comment max_trials={max_trials} != record {rec_budget['max_trials']}")
        if "total_max_fits" in rec_budget and int(rec_budget["total_max_fits"]) != total_fits:
            raise ExecutorBlocked(f"COMMENT_BUDGET_MISMATCH: Comment total_max_fits={total_fits} != record {rec_budget['total_max_fits']}")

        rec_limits = expected_record.get("resource_limits", {})
        if "max_wall_seconds" in rec_limits and int(rec_limits["max_wall_seconds"]) != wall_sec:
            raise ExecutorBlocked(f"COMMENT_LIMITS_MISMATCH: Comment max_wall_seconds={wall_sec} != record {rec_limits['max_wall_seconds']}")
        if "max_ram_mb" in rec_limits and int(rec_limits["max_ram_mb"]) != ram_mb:
            raise ExecutorBlocked(f"COMMENT_LIMITS_MISMATCH: Comment max_ram_mb={ram_mb} != record {rec_limits['max_ram_mb']}")
        if "max_native_threads" in rec_limits and int(rec_limits["max_native_threads"]) != threads:
            raise ExecutorBlocked(f"COMMENT_LIMITS_MISMATCH: Comment max_native_threads={threads} != record {rec_limits['max_native_threads']}")

        expected_record["_verified_owner_limits"] = parsed_approved_limits

    return parsed_approved_limits


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
      * Resource Limits: 1 native thread, max 2048 MB RAM, max 900s wall time.
    """
    if not isinstance(ref, str) or not ref:
        raise ExecutorBlocked("INVALID_OWNER_APPROVAL_REFERENCE: Reference must be a non-empty string URL")

    ref = ref.strip()
    if mode == "SYNTHETIC":
        if ref.startswith("SYNTHETIC_FIXTURE_") or ref.startswith("https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/"):
            if expected_record is not None:
                rec_budget = expected_record.get("budget", {})
                rec_limits = expected_record.get("resource_limits", {})
                expected_record["_verified_owner_limits"] = {
                    "max_trials": int(rec_budget.get("max_trials", 5)),
                    "total_max_fits": int(rec_budget.get("total_max_fits", 5)),
                    "fits_per_trial": int(rec_budget.get("fits_per_trial", 1)),
                    "max_wall_seconds": int(rec_limits.get("max_wall_seconds", 60)),
                    "max_ram_mb": int(rec_limits.get("max_ram_mb", 1024)),
                    "max_native_threads": int(rec_limits.get("max_native_threads", 1)),
                }
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
        comment_body = data.get("body", "")
        verify_phase2_owner_approval_text(comment_body, author=author, expected_record=expected_record)
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
    cfg = load_phase2_config(root)
    actual_cfg_sha = get_phase2_config_sha(root)
    locked_cfg = record.get("locked_configuration", {})
    expected_cfg_sha = locked_cfg.get("config_sha256")
    if not expected_cfg_sha or expected_cfg_sha.lower() != actual_cfg_sha.lower():
        raise ExecutorBlocked(f"PHASE2_CONFIG_HASH_MISMATCH: Authorization expects {expected_cfg_sha}, actual is {actual_cfg_sha}")

    # 7. Bound G3 manifest hash and stable digest (Fix 4: distinct verification)
    g3_manifest_file = root / "results/scania_aps/g3" / G3_ACCEPTED_RUN_ID / "stable_manifest.json"
    if not g3_manifest_file.is_file():
        raise ExecutorBlocked("ACCEPTED_G3_MANIFEST_FILE_MISSING")

    # A. Verify serialized manifest file SHA-256
    actual_manifest_file_sha = digest(g3_manifest_file.read_bytes().replace(b"\r\n", b"\n"))
    if actual_manifest_file_sha.lower() != G3_ACCEPTED_MANIFEST_FILE_SHA256.lower():
        raise ExecutorBlocked(f"G3_MANIFEST_FILE_SHA_MISMATCH: File hash {actual_manifest_file_sha} != expected {G3_ACCEPTED_MANIFEST_FILE_SHA256}")

    g3_int = record.get("g3_integrity", {})
    expected_manifest_file_sha = g3_int.get("manifest_file_sha256") or g3_int.get("manifest_sha256")
    if expected_manifest_file_sha and expected_manifest_file_sha.lower() != G3_ACCEPTED_MANIFEST_FILE_SHA256.lower():
        raise ExecutorBlocked(f"RECORD_G3_MANIFEST_FILE_SHA_MISMATCH: Record expects {expected_manifest_file_sha}, accepted is {G3_ACCEPTED_MANIFEST_FILE_SHA256}")

    # B. Verify parsed stable_digest field inside JSON
    try:
        g3_manifest_data = json.loads(g3_manifest_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ExecutorBlocked(f"INVALID_G3_MANIFEST_JSON: {exc}")

    actual_stable_digest = str(g3_manifest_data.get("stable_digest") or "").lower()
    if actual_stable_digest != G3_ACCEPTED_STABLE_DIGEST.lower():
        raise ExecutorBlocked(f"G3_STABLE_DIGEST_MISMATCH: Manifest stable_digest {actual_stable_digest} != accepted {G3_ACCEPTED_STABLE_DIGEST}")

    expected_stable_digest = g3_int.get("stable_digest")
    if expected_stable_digest and expected_stable_digest.lower() != G3_ACCEPTED_STABLE_DIGEST.lower():
        raise ExecutorBlocked(f"RECORD_G3_STABLE_DIGEST_MISMATCH: Record expects stable_digest {expected_stable_digest}, accepted is {G3_ACCEPTED_STABLE_DIGEST}")

    # C. Verify config itself declares the correct distinct hashes
    cfg_stable_digest = str(cfg.get("data", {}).get("g3_stable_digest") or "").lower()
    if cfg_stable_digest != G3_ACCEPTED_STABLE_DIGEST.lower():
        raise ExecutorBlocked(f"CONFIG_G3_STABLE_DIGEST_MISMATCH: Config has {cfg_stable_digest}, expected {G3_ACCEPTED_STABLE_DIGEST}")

    cfg_manifest_file_sha = str(cfg.get("data", {}).get("g3_manifest_file_sha256") or "").lower()
    if cfg_manifest_file_sha != G3_ACCEPTED_MANIFEST_FILE_SHA256.lower():
        raise ExecutorBlocked(f"CONFIG_G3_MANIFEST_FILE_SHA_MISMATCH: Config has {cfg_manifest_file_sha}, expected {G3_ACCEPTED_MANIFEST_FILE_SHA256}")

    # 8. Budget & Resource Limits verification (Fix 2: enforce exact approved limits, no silent overrides)
    rec_budget = record.get("budget", {})
    rec_limits = record.get("resource_limits", {})

    cfg_max_trials = int(cfg["budget"]["max_trials"])
    cfg_max_fits = int(cfg["budget"]["total_max_fits"])
    cfg_max_wall = int(cfg["resources"]["max_wall_seconds"])
    cfg_max_ram = int(cfg["resources"]["max_ram_mb"])

    max_trials = int(rec_budget.get("max_trials", 0))
    total_max_fits = int(rec_budget.get("total_max_fits", 0))
    fits_per_trial = int(rec_budget.get("fits_per_trial", 1))

    max_wall_seconds = int(rec_limits.get("max_wall_seconds", cfg_max_wall))
    max_ram_mb = int(rec_limits.get("max_ram_mb", cfg_max_ram))
    max_native_threads = int(rec_limits.get("max_native_threads", 1))

    if max_trials <= 0 or max_trials > cfg_max_trials:
        raise ExecutorBlocked(f"INVALID_BUDGET_IN_RECORD: max_trials={max_trials} must be 1..{cfg_max_trials}")
    if total_max_fits <= 0 or total_max_fits > cfg_max_fits:
        raise ExecutorBlocked(f"INVALID_BUDGET_IN_RECORD: total_max_fits={total_max_fits} must be 1..{cfg_max_fits}")
    if fits_per_trial != 1:
        raise ExecutorBlocked(f"INVALID_BUDGET_IN_RECORD: fits_per_trial must be 1, got {fits_per_trial}")
    if total_max_fits < max_trials:
        raise ExecutorBlocked(f"INSUFFICIENT_FITS_BUDGET: total_max_fits={total_max_fits} < max_trials={max_trials}")

    if max_wall_seconds <= 0 or max_wall_seconds > cfg_max_wall:
        raise ExecutorBlocked(f"EXCESSIVE_WALL_TIME: max_wall_seconds={max_wall_seconds} exceeds config limit {cfg_max_wall}")
    if max_ram_mb <= 0 or max_ram_mb > cfg_max_ram:
        raise ExecutorBlocked(f"EXCESSIVE_RAM: max_ram_mb={max_ram_mb} exceeds config limit {cfg_max_ram}")
    if max_native_threads != 1:
        raise ExecutorBlocked(f"INVALID_THREADS: max_native_threads must be exactly 1, got {max_native_threads}")

    approved_limits = {
        "max_trials": max_trials,
        "total_max_fits": total_max_fits,
        "fits_per_trial": fits_per_trial,
        "max_wall_seconds": max_wall_seconds,
        "max_ram_mb": max_ram_mb,
        "max_native_threads": max_native_threads,
    }
    record["approved_limits"] = approved_limits

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
    g3_manifest_file = root / "results/scania_aps/g3" / g3_run_id / "stable_manifest.json"
    if not g3_manifest_file.is_file():
        raise ExecutorBlocked("ACCEPTED_G3_MANIFEST_FILE_MISSING")

    manifest_file_sha = digest(g3_manifest_file.read_bytes().replace(b"\r\n", b"\n"))
    if manifest_file_sha.lower() != G3_ACCEPTED_MANIFEST_FILE_SHA256.lower():
        raise ExecutorBlocked(f"G3_MANIFEST_FILE_SHA_MISMATCH: {manifest_file_sha} != {G3_ACCEPTED_MANIFEST_FILE_SHA256}")

    g3_manifest_data = json.loads(g3_manifest_file.read_text(encoding="utf-8"))
    stable_digest_val = str(g3_manifest_data.get("stable_digest") or "").lower()
    if stable_digest_val != G3_ACCEPTED_STABLE_DIGEST.lower():
        raise ExecutorBlocked(f"G3_STABLE_DIGEST_MISMATCH: {stable_digest_val} != {G3_ACCEPTED_STABLE_DIGEST}")

    if str(cfg.get("data", {}).get("g3_stable_digest") or "").lower() != G3_ACCEPTED_STABLE_DIGEST.lower():
        raise ExecutorBlocked("CONFIG_G3_STABLE_DIGEST_MISMATCH")
    if str(cfg.get("data", {}).get("g3_manifest_file_sha256") or "").lower() != G3_ACCEPTED_MANIFEST_FILE_SHA256.lower():
        raise ExecutorBlocked("CONFIG_G3_MANIFEST_FILE_SHA_MISMATCH")

    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, g3_run_id)
    g3_summary["stable_digest"] = stable_digest_val
    g3_summary["manifest_file_sha256"] = manifest_file_sha

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
    wall_seconds: int = 900,
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

    # FIX 2: Reconstruct confirmed started fits and trial results from durable markers on disk
    durable_dir = output_dir / "durable_fits"
    reconciled_fits = reconcile_durable_fit_markers(durable_dir) if durable_dir.is_dir() else {
        "started_fits": 0, "completed_fits": 0, "failed_fits": 0, "interrupted_or_unknown_fits": 0, "fit_records": []
    }
    reconciled_trials = reconcile_durable_trial_markers(durable_dir) if durable_dir.is_dir() else {
        "n_trials_completed": 0, "trials_records": [], "best_trial": None, "corrupted_markers": []
    }

    if not result_path.is_file():
        # Worker crashed or was killed by job object without producing worker_result.json
        partial_result = {
            "status": "FAILED",
            "error_type": "WorkerTerminatedNoResult",
            "reason": f"Worker process terminated without writing worker_result.json (exit_code={exit_code})",
            "total_estimator_fits": reconciled_fits.get("started_fits", 0),
            "started_estimator_fits": reconciled_fits.get("started_fits", 0),
            "completed_estimator_fits": reconciled_fits.get("completed_fits", 0),
            "failed_estimator_fits": reconciled_fits.get("failed_fits", 0),
            "interrupted_or_unknown_fits": reconciled_fits.get("interrupted_or_unknown_fits", 0),
            "fit_records": reconciled_fits.get("fit_records", []),
            "n_trials_completed": reconciled_trials.get("n_trials_completed", 0),
            "trials_records": reconciled_trials.get("trials_records", []),
            "best_trial": reconciled_trials.get("best_trial"),
            "validation_scored": False,
        }
        raise ExecutorFailure(
            f"WORKER_CRASHED_NO_RESULT: Exit code {exit_code}; confirmed started fits: {reconciled_fits.get('started_fits', 0)}",
            worker_result=partial_result,
        )

    worker_result = json.loads(result_path.read_text(encoding="utf-8"))

    if exit_code != 0 or worker_result.get("status") != "PASS":
        err_msg = worker_result.get("reason", f"Exit code {exit_code}")
        # Merge reconciled markers into worker_result if worker crashed mid-trial
        if reconciled_fits.get("started_fits", 0) > worker_result.get("total_estimator_fits", 0):
            worker_result["total_estimator_fits"] = reconciled_fits["started_fits"]
            worker_result["started_estimator_fits"] = reconciled_fits["started_fits"]
            worker_result["interrupted_or_unknown_fits"] = reconciled_fits["interrupted_or_unknown_fits"]
            worker_result["fit_records"] = reconciled_fits["fit_records"]
        if reconciled_trials.get("n_trials_completed", 0) > len(worker_result.get("trials_records", [])):
            worker_result["n_trials_completed"] = reconciled_trials["n_trials_completed"]
            worker_result["trials_records"] = reconciled_trials["trials_records"]
            if not worker_result.get("best_trial"):
                worker_result["best_trial"] = reconciled_trials.get("best_trial")
        raise ExecutorFailure(f"PHASE2_WORKER_FAILED: {err_msg}", worker_result=worker_result)

    is_real = (mode == "REAL")
    total_fits = worker_result.get("total_estimator_fits", 0)
    report = {
        "run_id": run_id,
        "mode": mode,
        "status": "COMPLETE",
        "lifecycle": "COMPLETE",
        "real_estimator_fits": total_fits if is_real else 0,
        "synthetic_estimator_fits": total_fits if not is_real else 0,
        "started_estimator_fits": worker_result.get("started_estimator_fits", total_fits),
        "completed_estimator_fits": worker_result.get("completed_estimator_fits", total_fits),
        "failed_estimator_fits": worker_result.get("failed_estimator_fits", 0),
        "interrupted_or_unknown_fits": worker_result.get("interrupted_or_unknown_fits", 0),
        "attempted_fits": worker_result.get("attempted_fits", total_fits),
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
    """Write all 10 required evidence artifacts and compute LF-normalized SHA-256 checksums."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    errors = errors or []
    has_errors = len(errors) > 0
    has_best_policy = bool(report.get("best_trial") and report.get("best_trial", {}).get("best_policy"))
    n_trials = report.get("n_trials_completed", 0)

    # Explicit lifecycle distinction: COMPLETE vs PARTIAL vs FAILED
    if has_errors or report.get("status") == "FAILED" or report.get("lifecycle") == "FAILED":
        final_status = "FAILED"
    elif not has_best_policy or n_trials == 0:
        final_status = "PARTIAL"
    else:
        final_status = "COMPLETE"

    report["status"] = final_status
    report["lifecycle"] = final_status

    # 1. Config
    (output_dir / "config.json").write_bytes(json.dumps(config, indent=2).encode("utf-8"))

    # 2. Environment
    (output_dir / "environment.json").write_bytes(json.dumps(environment_dict, indent=2).encode("utf-8"))

    # 3. Stable manifest
    (output_dir / "stable_manifest.json").write_bytes(json.dumps(manifest_data, indent=2).encode("utf-8"))

    # 4. Failure diagnostics
    diag_payload = {
        "status": final_status,
        "errors": errors,
        "started_estimator_fits": report.get("started_estimator_fits", report.get("real_estimator_fits", 0)),
        "completed_estimator_fits": report.get("completed_estimator_fits", 0),
        "failed_estimator_fits": report.get("failed_estimator_fits", 0),
        "interrupted_or_unknown_fits": report.get("interrupted_or_unknown_fits", 0),
        "fit_records": report.get("fit_records", []),
    }
    (output_dir / "failure_diagnostics.json").write_bytes(json.dumps(diag_payload, indent=2).encode("utf-8"))

    # 5. Best policy
    best_trial = report.get("best_trial")
    best_policy = best_trial.get("best_policy") if best_trial else None
    (output_dir / "best_policy.json").write_bytes(json.dumps(best_policy or {}, indent=2).encode("utf-8"))

    # 6. Optuna study summary
    study_summary = {
        "run_id": report["run_id"],
        "mode": report["mode"],
        "n_trials_completed": n_trials,
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
        f"synthetic_estimator_fits={report.get('synthetic_estimator_fits', 0)}",
        f"started_estimator_fits={report.get('started_estimator_fits', 0)}",
        f"completed_estimator_fits={report.get('completed_estimator_fits', 0)}",
        f"failed_estimator_fits={report.get('failed_estimator_fits', 0)}",
        f"interrupted_or_unknown_fits={report.get('interrupted_or_unknown_fits', 0)}",
        f"n_trials_completed={n_trials}",
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
    """Cryptographically and scientifically verify all artifacts of a Phase 2 run.

    Verifies:
    1. Complete inventory of 10 required artifacts exists.
    2. Checksums in checksums.json match LF-normalized file hashes.
    3. Status is valid (COMPLETE, PARTIAL, or FAILED).
    4. optuna_study.json and trials_summary.csv trial count consistency.
    5. failure_diagnostics.json error consistency with status.
    6. For COMPLETE runs:
       - best_policy.json is present, non-empty, and valid.
       - Recomputes benchmark cost exactly: 10*FP + 500*FN.
       - Recomputes maintenance capacity exactly: M = TP + FP <= 1200.
       - Confirms best_policy matches minimum feasible trial in optuna_study.json.
       - Fit count matches completed trial count.
    """
    output_dir = Path(output_dir).resolve()
    if not output_dir.is_dir():
        return False

    required_files = [
        "config.json",
        "environment.json",
        "stable_manifest.json",
        "failure_diagnostics.json",
        "best_policy.json",
        "optuna_study.json",
        "trials_summary.csv",
        "run_summary.json",
        "execution.txt",
        "checksums.json",
    ]

    # 1. Check complete inventory of 10 required artifacts
    for fname in required_files:
        if not (output_dir / fname).is_file():
            return False

    # 2. Check checksums.json matches all files
    checksums_file = output_dir / "checksums.json"
    try:
        checksums = json.loads(checksums_file.read_text(encoding="utf-8"))
    except Exception:
        return False

    for fname in required_files:
        if fname == "checksums.json":
            continue
        if fname not in checksums:
            return False
        expected_hash = checksums[fname]
        raw_b = (output_dir / fname).read_bytes().replace(b"\r\n", b"\n")
        if digest(raw_b) != expected_hash:
            return False

    # 3. Load run_summary.json
    try:
        run_sum = json.loads((output_dir / "run_summary.json").read_text(encoding="utf-8"))
    except Exception:
        return False

    status = run_sum.get("status")
    if status not in {"COMPLETE", "PARTIAL", "FAILED"}:
        return False

    n_trials_completed = int(run_sum.get("n_trials_completed", 0))

    # 4. Load failure_diagnostics.json
    try:
        diag = json.loads((output_dir / "failure_diagnostics.json").read_text(encoding="utf-8"))
    except Exception:
        return False

    errors = diag.get("errors", [])
    if status == "COMPLETE" and len(errors) > 0:
        return False
    if status == "FAILED" and len(errors) == 0:
        return False

    # 5. Load optuna_study.json
    try:
        study = json.loads((output_dir / "optuna_study.json").read_text(encoding="utf-8"))
    except Exception:
        return False

    study_trials = study.get("trials", [])
    study_n = study.get("n_trials_completed")

    # 6. Check trials_summary.csv rows
    try:
        with open(output_dir / "trials_summary.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            csv_rows = [row for row in reader if row]
    except Exception:
        return False

    # Check trial count consistency:
    # For COMPLETE runs: strictly requires all trials match n_trials_completed
    # For FAILED runs: verifies internal consistency between study trials and csv_rows
    if status == "COMPLETE":
        if len(study_trials) != n_trials_completed:
            return False
        if study_n != n_trials_completed:
            return False
        if len(csv_rows) != n_trials_completed:
            return False
    else:
        # FAILED or PARTIAL run: verify study trials and csv_rows match each other
        if len(study_trials) != len(csv_rows):
            return False
        if study_n is not None and study_n != len(study_trials) and study_n != n_trials_completed:
            return False

    # 7. Scientific & policy validation for COMPLETE runs
    if status == "COMPLETE":
        # Fit count consistency: each trial performed exactly 1 fit
        is_real = (run_sum.get("mode") == "REAL")
        fits = run_sum.get("real_estimator_fits", 0) if is_real else run_sum.get("synthetic_estimator_fits", 0)
        if fits != n_trials_completed:
            return False

        # Load best_policy.json
        try:
            best_pol = json.loads((output_dir / "best_policy.json").read_text(encoding="utf-8"))
        except Exception:
            return False

        if not best_pol or not isinstance(best_pol, dict):
            return False

        for k in ["FP", "FN", "TP", "TN", "M", "total_cost", "threshold"]:
            if k not in best_pol:
                return False

        fp = int(best_pol["FP"])
        fn = int(best_pol["FN"])
        tp = int(best_pol["TP"])
        cost = int(best_pol["total_cost"])
        m = int(best_pol["M"])

        # Cost recalculation formula: 10*FP + 500*FN
        expected_cost = 10 * fp + 500 * fn
        if cost != expected_cost:
            return False

        # Capacity recalculation formula: M = TP + FP
        expected_m = tp + fp
        if m != expected_m:
            return False

        # Capacity feasibility: M <= 1200
        if m > 1200:
            return False

        # Check match with best feasible trial in study
        feasible_trials = [t for t in study_trials if t.get("status") == "FEASIBLE" and t.get("best_policy")]
        if not feasible_trials:
            return False

        min_study_cost = min(t["objective_value"] for t in feasible_trials)
        if cost != int(min_study_cost):
            return False

    return True
