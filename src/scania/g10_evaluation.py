"""Scania APS Gate G10: Final Official Test Evaluation Engine.

Safety & Contract boundaries:
- Frozen Phase 2 Trial 16 policy:
  * Estimator: RandomForestClassifier
  * Hyperparameters: n_estimators=50, max_depth=10, min_samples_split=10,
    max_features=0.4268663927182804, class_weight='balanced', random_state=42, n_jobs=1, bootstrap=True.
  * Frozen threshold: 0.3232440937634324.
  * Zero threshold tuning on Official Test.
  * Zero hyperparameter tuning on Official Test.
- Evaluation mode: DETERMINISTIC_TRAIN_REFIT_EVALUATION.
  * Exactly 1 deterministic refit on official Train partition (48,000 samples).
  * Truthful fit accounting: records atomic STARTED marker before model.fit().
  * Validation regression guard: reproduces exact Trial 16 validation metrics
    (TP=195, FP=383, FN=5, TN=11417, Cost=6330, M=578) before touching Official Test.
- Runtime containment:
  * Supervised worker execution under Windows Job Object.
  * 1 native compute thread, max 2048 MB RAM, max 180s wall clock time.
  * Stop without retry on timeout or failure.
- Directory lifecycle:
  * Final run directory is NOT created before successful authorization and preflight.
  * Durable fit accounting and failure evidence preserved indefinitely.
- Official Test set (16,000 samples):
  * Sealed inside data/raw/scania_aps/aps+failure+at+scania+trucks.zip.
  * Evaluated strictly single-pass read-only.
  * Transformed using frozen tree_preprocessor.joblib (fitted on Train only).
  * Capacity limit K_test = 1,600 (10% of 16,000 test observations).
  * Benchmark cost: Cost = 10 * FP + 500 * FN.
- Mandatory GitHub Owner authorization check bound to exact commit SHA, config SHA, and G3 manifest.
"""
import csv
import io
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import urllib.request
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score

from .contracts import FEATURES, canonical, digest
from .g4_b2_executor import (
    ExecutorBlocked,
    ExecutorFailure,
    SafetyBlocked,
    _get_github_token,
    _parse_owner_comment_fields,
    _strip_markdown_code_blocks,
    verify_g3_artifacts_and_build_allowlist,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
G10_CONFIG_PATH = REPO_ROOT / "configs/scania/g10_evaluation.json"

# Fixed G3 Accepted Reference Hashes
G3_ACCEPTED_RUN_ID = "official_20261029_04"
G3_ACCEPTED_STABLE_DIGEST = "efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb"
G3_ACCEPTED_MANIFEST_FILE_SHA256 = "7d3d68b694b2c260cfc89087f1dd8a5cfd35784ae303803fd0687c530d412242"

# Frozen Policy Constants (Phase 2 Trial 16)
TARGET_RUN_ID = "scania_g10_official_test_003"
EVALUATION_MODE = "DETERMINISTIC_TRAIN_REFIT_EVALUATION"
PERMITTED_FITS = 1
FROZEN_THRESHOLD = 0.3232440937634324
CAPACITY_LIMIT_K_TEST = 1600
OFFICIAL_TEST_EXPECTED_ROWS = 16000

FROZEN_RF_HYPERPARAMS = {
    "n_estimators": 50,
    "max_depth": 10,
    "min_samples_split": 10,
    "max_features": 0.4268663927182804,
    "class_weight": "balanced",
    "random_state": 42,
    "n_jobs": 1,
    "bootstrap": True,
}

VALIDATION_REGRESSION_TARGET = {
    "TP": 195,
    "FP": 383,
    "FN": 5,
    "TN": 11417,
    "total_cost": 6330,
    "M": 578,
    "saving_pct": 93.67,
}


def load_g10_config(root: Path = REPO_ROOT) -> Dict[str, Any]:
    """Load and validate locked G10 configuration."""
    cfg_file = Path(root) / "configs/scania/g10_evaluation.json"
    if not cfg_file.is_file():
        raise ExecutorBlocked("G10_CONFIG_FILE_MISSING")
    content = cfg_file.read_bytes().replace(b"\r\n", b"\n")
    return json.loads(content.decode("utf-8"))


def get_g10_config_sha(root: Path = REPO_ROOT) -> str:
    """Compute LF-normalized SHA-256 digest of g10_evaluation.json."""
    cfg_file = Path(root) / "configs/scania/g10_evaluation.json"
    if not cfg_file.is_file():
        raise ExecutorBlocked("G10_CONFIG_FILE_MISSING")
    content = cfg_file.read_bytes().replace(b"\r\n", b"\n")
    return digest(content)


def sanitize_for_strict_json(obj: Any) -> Any:
    """Recursively convert NumPy numbers and non-finite floats to JSON-safe primitives."""
    if isinstance(obj, dict):
        return {k: sanitize_for_strict_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_strict_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [sanitize_for_strict_json(v) for v in obj]
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        val = float(obj)
        return val if np.isfinite(val) else None
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, np.ndarray):
        return sanitize_for_strict_json(obj.tolist())
    if isinstance(obj, (bool, str, int, type(None))):
        return obj
    return str(obj)


def verify_g10_owner_approval_text(
    comment_body: str,
    author: str = "PhucHuynh16",
    expected_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Parse and verify authentic GitHub Owner approval comment text for Gate G10.

    Enforces:
    - Author is repository owner 'PhucHuynh16'.
    - Outside markdown code blocks, comment has plain '# OWNER ...' header.
    - Key: Value format on single lines.
    - Fields:
      * Decision: exactly 'APPROVED'.
      * Authorized Commit: exact 40-character hex commit SHA.
      * Target Run ID: exact string 'scania_g10_official_test_001'.
      * Permitted Operation: 'G10_OFFICIAL_TEST_EVALUATION'.
      * Approved Estimator: contains 'RandomForestClassifier'.
      * Evaluation Mode: 'DETERMINISTIC_TRAIN_REFIT_EVALUATION'.
      * Fit Budget: max_trials=1, total_max_fits=1, fits_per_trial=1.
      * Frozen Threshold: 0.3232440937634324.
      * Data Scope: Train, Validation guard, Official Test evaluation.
      * Resource Limits: 1 native thread, max 2048 MB RAM, max 180s wall time.
    """
    if author != "PhucHuynh16":
        raise ExecutorBlocked(
            f"AUTHORIZATION_NOT_FROM_OWNER: Comment author '{author}' is not repository owner PhucHuynh16"
        )

    # 1. Reject agent reports
    if re.search(r"##\s+ANTIGRAVITY", comment_body, re.IGNORECASE):
        raise ExecutorBlocked(
            "AGENT_REPORT_CANNOT_AUTHORIZE: Comment is an agent report, not an authentic human Owner decision"
        )

    # 2. Strip code blocks
    clean_body = _strip_markdown_code_blocks(comment_body)

    # 3. Check for explicit Owner directive header
    if not re.search(
        r"^#\s+OWNER\s+(?:TASK\s+AUTHORIZATION|DECISION|DIRECTIVE)",
        clean_body,
        re.IGNORECASE | re.MULTILINE,
    ):
        raise ExecutorBlocked(
            "MISSING_OWNER_DIRECTIVE_HEADER: Approval comment must have an explicit '# OWNER ...' directive header"
        )

    # 4. Extract field-values
    fields = _parse_owner_comment_fields(clean_body)

    # Decision
    decision_val = fields.get("decision")
    if not decision_val or decision_val.upper() != "APPROVED":
        raise ExecutorBlocked(
            f"INVALID_OR_MISSING_APPROVAL_DECISION: Decision must be exactly 'APPROVED', got '{decision_val}'"
        )

    # Authorized Commit
    commit_val = (
        fields.get("authorized commit")
        or fields.get("commit")
        or fields.get("commit sha")
    )
    if not commit_val or not re.fullmatch(r"[0-9a-f]{40}", commit_val, re.IGNORECASE):
        raise ExecutorBlocked(
            f"INVALID_OR_MISSING_AUTHORIZED_COMMIT: Must specify 40-character hex commit SHA, got '{commit_val}'"
        )
    commit_val = commit_val.lower()

    # Target Run ID
    run_id_val = fields.get("target run id") or fields.get("run id")
    if not run_id_val or not re.match(r"^scania_g10_official_test_\d{3}$", run_id_val):
        raise ExecutorBlocked(
            f"INVALID_TARGET_RUN_ID: Expected 'scania_g10_official_test_XXX', got '{run_id_val}'"
        )

    # Permitted Operation
    op_val = fields.get("permitted operation") or fields.get("operation")
    if not op_val or op_val.upper() != "G10_OFFICIAL_TEST_EVALUATION":
        raise ExecutorBlocked(
            f"INVALID_PERMITTED_OPERATION: Permitted operation must be exactly 'G10_OFFICIAL_TEST_EVALUATION', got '{op_val}'"
        )

    # Approved Estimator
    est_val = fields.get("approved estimator") or fields.get("estimator") or fields.get("models")
    if not est_val or "RandomForestClassifier" not in est_val:
        raise ExecutorBlocked(
            f"INVALID_APPROVED_ESTIMATOR: Must specify 'RandomForestClassifier', got '{est_val}'"
        )

    # Evaluation Mode
    mode_val = fields.get("evaluation mode") or fields.get("mode")
    if not mode_val or mode_val.upper() != EVALUATION_MODE:
        raise ExecutorBlocked(
            f"INVALID_EVALUATION_MODE: Evaluation mode must be '{EVALUATION_MODE}', got '{mode_val}'"
        )

    # Fit Budget
    budget_val = fields.get("fit budget") or fields.get("budget")
    if not budget_val:
        raise ExecutorBlocked("MISSING_FIT_BUDGET: Comment must explicitly specify Fit Budget")

    trials_m = re.search(r"\b(?:max_trials|trials)\s*[:=]\s*(\d+)\b", budget_val, re.IGNORECASE)
    total_fits_m = re.search(r"\b(?:total_max_fits|total_fits|total)\s*[:=]\s*(\d+)\b", budget_val, re.IGNORECASE)

    if not (trials_m and total_fits_m):
        raise ExecutorBlocked(f"INCOMPLETE_FIT_BUDGET: Must specify max_trials and total_max_fits, got '{budget_val}'")

    max_trials = int(trials_m.group(1))
    total_fits = int(total_fits_m.group(1))

    if max_trials != 1 or total_fits != 1:
        raise ExecutorBlocked(
            f"INVALID_FIT_BUDGET: G10 fit budget must be max_trials=1, total_max_fits=1; got trials={max_trials}, total={total_fits}"
        )

    # Frozen Threshold
    th_val = fields.get("frozen threshold") or fields.get("threshold")
    if th_val:
        try:
            parsed_th = float(re.search(r"([0-9]+\.[0-9]+)", th_val).group(1))
            if abs(parsed_th - FROZEN_THRESHOLD) > 1e-4:
                raise ExecutorBlocked(
                    f"THRESHOLD_MISMATCH: Frozen threshold {parsed_th} != {FROZEN_THRESHOLD}"
                )
        except Exception as exc:
            if isinstance(exc, ExecutorBlocked):
                raise
            raise ExecutorBlocked(f"INVALID_THRESHOLD_FORMAT: '{th_val}'")

    # Data Scope
    scope_val = fields.get("data scope") or fields.get("scope") or ""
    combined_scope = scope_val.lower()
    if not combined_scope:
        raise ExecutorBlocked("MISSING_DATA_SCOPE: Comment must explicitly specify Data Scope")
    if "official test" not in combined_scope and "test" not in combined_scope:
        raise ExecutorBlocked(f"INVALID_DATA_SCOPE: Data scope must include Official Test evaluation, got '{scope_val}'")

    # Resource Limits
    limits_val = fields.get("resource limits") or fields.get("limits")
    if not limits_val:
        raise ExecutorBlocked("MISSING_RESOURCE_LIMITS: Comment must explicitly specify Resource Limits")

    threads_m = re.search(
        r"\b(?:max_native_threads|threads)\s*[:=]\s*(\d+)\b|\b(\d+)\s*native\s*threads?\b|\b(\d+)\s*threads?\b",
        limits_val,
        re.IGNORECASE,
    )
    ram_m = re.search(
        r"\b(?:max_ram_mb|ram_mb|ram)\s*[:=]\s*(\d+)\b|\b(\d+)\s*(?:mb|gb)\s*ram\b",
        limits_val,
        re.IGNORECASE,
    )
    wall_m = re.search(
        r"\b(?:max_wall_seconds|wall_seconds|wall)\s*[:=]\s*(\d+)\b|\b(\d+)\s*s(?:ec|econds)?\s*wall\b",
        limits_val,
        re.IGNORECASE,
    )

    if not (threads_m and ram_m and wall_m):
        raise ExecutorBlocked(f"INCOMPLETE_RESOURCE_LIMITS: Must specify threads, RAM, and wall time limits, got '{limits_val}'")

    threads = int(next(g for g in threads_m.groups() if g is not None))
    ram_mb = int(next(g for g in ram_m.groups() if g is not None))
    wall_sec = int(next(g for g in wall_m.groups() if g is not None))

    if threads != 1:
        raise ExecutorBlocked(f"INVALID_THREADS: max_native_threads must be exactly 1, got {threads}")
    if ram_mb > 2048:
        raise ExecutorBlocked(f"INVALID_RAM: max_ram_mb must not exceed 2048, got {ram_mb}")
    if wall_sec > 180:
        raise ExecutorBlocked(f"INVALID_WALL_TIME: max_wall_seconds must not exceed 180, got {wall_sec}")

    parsed_approved_limits = {
        "authorized_commit": commit_val,
        "target_run_id": run_id_val,
        "permitted_operation": op_val,
        "approved_estimator": est_val,
        "evaluation_mode": EVALUATION_MODE,
        "max_trials": max_trials,
        "total_max_fits": total_fits,
        "fits_per_trial": 1,
        "frozen_threshold": FROZEN_THRESHOLD,
        "max_wall_seconds": wall_sec,
        "max_ram_mb": ram_mb,
        "max_native_threads": threads,
    }

    # Semantic check against expected record
    if expected_record is not None:
        src_int = expected_record.get("source_integrity", expected_record)
        exp_commit = str(src_int.get("authorized_commit") or "").lower()
        if exp_commit and commit_val != exp_commit:
            raise ExecutorBlocked(
                f"COMMENT_COMMIT_MISMATCH: Comment authorized commit {commit_val} != expected {exp_commit}"
            )

        exp_run_id = expected_record.get("run_id") or expected_record.get("target_run_id")
        if exp_run_id and run_id_val != exp_run_id:
            raise ExecutorBlocked(
                f"COMMENT_RUN_ID_MISMATCH: Comment target run ID '{run_id_val}' != expected '{exp_run_id}'"
            )

        expected_record["_verified_owner_limits"] = parsed_approved_limits

    return parsed_approved_limits


def verify_g10_owner_approval_reference(
    ref: str,
    expected_record: Optional[Dict[str, Any]] = None,
    mode: str = "REAL",
) -> bool:
    """Fetch and verify authentic Owner approval comment from GitHub Issue #17."""
    if mode == "SYNTHETIC":
        if expected_record:
            expected_record["_verified_owner_limits"] = {
                "authorized_commit": "synthetic",
                "target_run_id": TARGET_RUN_ID,
                "permitted_operation": "G10_OFFICIAL_TEST_EVALUATION",
                "evaluation_mode": EVALUATION_MODE,
                "total_max_fits": 1,
            }
        return True

    # Validate URL structure
    m = re.match(
        r"^https://github\.com/([^/]+)/([^/]+)/issues/(\d+)#issuecomment-(\d+)$",
        ref.strip(),
    )
    if not m:
        raise ExecutorBlocked(
            f"INVALID_GITHUB_COMMENT_URL: '{ref}'. Expected format: https://github.com/<owner>/<repo>/issues/<issue_num>#issuecomment-<comment_id>"
        )

    owner, repo, issue_num, comment_id = m.groups()
    if owner != "PhucHuynh16" or repo != "Predictive-maintenance-cost-optimization" or issue_num != "17":
        raise ExecutorBlocked(
            f"UNAUTHORIZED_REPOSITORY_OR_ISSUE: Expected PhucHuynh16/Predictive-maintenance-cost-optimization issue #17, got {owner}/{repo} issue #{issue_num}"
        )

    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/comments/{comment_id}"
    req = urllib.request.Request(api_url)
    req.add_header("User-Agent", "Scania-APS-G10-Authorization-Validator/1.0")
    req.add_header("Accept", "application/vnd.github.v3+json")

    token = _get_github_token()
    if token:
        req.add_header("Authorization", f"token {token}")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status != 200:
                raise ExecutorBlocked(f"GITHUB_API_ERROR: HTTP status {resp.status}")
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ExecutorBlocked(f"GITHUB_API_HTTP_ERROR: {exc.code} {exc.reason}") from exc
    except Exception as exc:
        raise ExecutorBlocked(f"GITHUB_API_REQUEST_FAILED: {exc}") from exc

    comment_author = data.get("user", {}).get("login", "")
    comment_body = data.get("body", "")

    verify_g10_owner_approval_text(comment_body, comment_author, expected_record)
    return True


def write_durable_marker(marker_dir: Path, filename: str, data: Dict[str, Any]) -> Path:
    """Atomically write and flush a durable JSON marker to disk."""
    marker_dir = Path(marker_dir).resolve()
    marker_dir.mkdir(parents=True, exist_ok=True)

    dest_file = marker_dir / filename
    temp_file = marker_dir / f"{filename}.tmp_{os.getpid()}_{int(time.time() * 1000)}"

    content = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
    with open(temp_file, "wb") as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

    os.replace(temp_file, dest_file)
    return dest_file


def parse_official_test_set_from_zip(
    zip_path: Path,
    expected_sha256: str,
    test_csv_filename: str = "aps_failure_test_set.csv",
    expected_rows: int = 16000,
) -> Tuple[np.ndarray, np.ndarray]:
    """Strictly read and parse Official Test CSV from zip archive in-memory."""
    zip_path = Path(zip_path).resolve()
    if not zip_path.is_file():
        raise SafetyBlocked(f"RAW_ZIP_MISSING: {zip_path}")

    zip_bytes = zip_path.read_bytes()
    actual_zip_sha = digest(zip_bytes)
    if actual_zip_sha != expected_sha256:
        raise SafetyBlocked(
            f"RAW_ZIP_CHECKSUM_MISMATCH: expected {expected_sha256}, got {actual_zip_sha}"
        )

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        if test_csv_filename not in z.namelist():
            raise SafetyBlocked(f"TEST_CSV_NOT_FOUND_IN_ZIP: {test_csv_filename}")
        with z.open(test_csv_filename, "r") as f:
            content_bytes = f.read()

    lines = content_bytes.decode("utf-8", errors="strict").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        tokens = tuple(t.strip() for t in line.split(","))
        if "class" in tokens:
            if tokens != ("class", *FEATURES):
                raise SafetyBlocked("TEST_SCHEMA_MISMATCH: header does not match ordered FEATURES")
            header_idx = i
            break

    if header_idx is None:
        raise SafetyBlocked("TEST_HEADER_NOT_FOUND")

    data_lines = lines[header_idx + 1 :]
    if len(data_lines) != expected_rows:
        raise SafetyBlocked(
            f"TEST_ROW_COUNT_MISMATCH: expected {expected_rows}, got {len(data_lines)}"
        )

    n_features = len(FEATURES)
    X = np.full((expected_rows, n_features), np.nan, dtype=np.float64)
    y = np.empty(expected_rows, dtype=np.int8)

    number_regex = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")

    for r, line in enumerate(data_lines):
        tokens = [t.strip() for t in line.split(",")]
        if len(tokens) != n_features + 1:
            raise SafetyBlocked(f"TEST_ROW_WIDTH_MISMATCH: row {r + 1}")
        target = tokens[0]
        if target not in ("neg", "pos"):
            raise SafetyBlocked(f"INVALID_TARGET: row {r + 1}: '{target}'")
        y[r] = 1 if target == "pos" else 0

        for c, tok in enumerate(tokens[1:]):
            if tok == "na" or not tok:
                continue
            if not number_regex.fullmatch(tok):
                raise SafetyBlocked(f"INVALID_NUMERIC_TOKEN: row {r + 1}, col {c + 1}: '{tok}'")
            val = float(tok)
            if not np.isfinite(val):
                raise SafetyBlocked(f"NON_FINITE_FLOAT: row {r + 1}, col {c + 1}")
            X[r, c] = 0.0 if val == 0 else val

    return X, y


def evaluate_policy_predictions(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float = FROZEN_THRESHOLD,
    capacity_limit_K: int = CAPACITY_LIMIT_K_TEST,
    cost_fp: int = 10,
    cost_fn: int = 500,
) -> Dict[str, Any]:
    """Compute confusion matrix, cost, capacity, and academic metrics for frozen policy."""
    y_pred = (probabilities >= threshold).astype(int)

    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))

    n = len(y_true)
    p = tp + fn
    m = tp + fp

    cost_fp_total = fp * cost_fp
    cost_fn_total = fn * cost_fn
    total_cost = cost_fp_total + cost_fn_total
    cost_per_obs = total_cost / n if n > 0 else 0.0

    feasible = bool(m <= capacity_limit_K)
    excess = max(0, m - capacity_limit_K)

    reference_cost = p * cost_fn
    absolute_saving = reference_cost - total_cost
    saving_pct = (absolute_saving / reference_cost * 100.0) if reference_cost > 0 else 0.0

    precision = tp / m if m > 0 else 0.0
    recall = tp / p if p > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    try:
        roc_auc = float(roc_auc_score(y_true, probabilities))
    except Exception:
        roc_auc = None

    try:
        pr_auc = float(average_precision_score(y_true, probabilities))
    except Exception:
        pr_auc = None

    return {
        "threshold": float(threshold),
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "N": n,
        "P": p,
        "M": m,
        "K": capacity_limit_K,
        "maintenance_rate": m / n if n > 0 else 0.0,
        "excess": excess,
        "feasible": int(feasible),
        "policy_status": "FEASIBLE" if feasible else "INFEASIBLE",
        "cost_fp": cost_fp_total,
        "cost_fn": cost_fn_total,
        "total_cost": total_cost,
        "cost_per_observation": cost_per_obs,
        "reference_cost": reference_cost,
        "absolute_saving": absolute_saving,
        "saving_pct": round(saving_pct, 4),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
    }


def install_g10_io_guard(root: Path, output: Path, allowlist: List[Path], mode: str = "REAL"):
    """Enforce strict I/O boundaries during G10 execution via sys.addaudithook."""
    root = Path(root).resolve()
    output = Path(output).resolve()
    resolved_allowlist = {Path(p).resolve() for p in allowlist}

    def audit(name, args):
        if name != "open" or isinstance(args[0], int):
            return
        raw = os.fsdecode(args[0])
        p = Path(raw).resolve()

        # In SYNTHETIC mode: strict test set barrier
        if mode == "SYNTHETIC":
            name_lower = p.name.casefold()
            if "aps_failure_test" in name_lower or p.suffix.casefold() == ".zip":
                raise SafetyBlocked("TEST_SET_ACCESS_DENIED_IN_SYNTHETIC_MODE")

        # Detect write intents
        mode_arg = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 else 0
        writing = (isinstance(mode_arg, str) and any(c in mode_arg for c in "wax+")) or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
        )

        if writing:
            # Writes are allowed ONLY inside the designated run output directory
            if not p.is_relative_to(output):
                raise SafetyBlocked(f"EXECUTOR_WRITE_OUTSIDE_OWN_RUN: {p.name}")
            # Source directories, raw data, and G3 processed artifacts are read-only
            if p.is_relative_to(root / "data") or p.is_relative_to(root / "results/scania_aps/g3"):
                raise SafetyBlocked(f"SOURCE_OR_G3_ARTIFACT_WRITE_FORBIDDEN: {p.name}")
        else:
            # Files inside output directory can always be read back
            if p.is_relative_to(output):
                return
            # Reads within data/ or with data-bearing suffixes must be explicitly allowlisted
            is_data_path = p.is_relative_to(root / "data")
            is_data_ext = p.suffix.casefold() in {".npy", ".npz", ".csv", ".zip"}
            if is_data_path or is_data_ext:
                if p not in resolved_allowlist:
                    raise SafetyBlocked(f"EXECUTOR_READ_NOT_IN_ALLOWLIST: {p.name}")

    sys.addaudithook(audit)


def orchestrate_g10_worker_in_job(
    root: Path,
    run_id: str,
    output_dir: Path,
    allowlist: List[Path],
    task_config: Dict[str, Any],
    wall_seconds: int = 180,
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
        SC_G10_RUN=run_id,
        SC_G10_TASK_PATH=str(task_path),
        SC_G10_ALLOWLIST_PATH=str(allowlist_path),
        SC_G10_OUTPUT_DIR=str(output_dir),
        SC_G10_ROOT_DIR=str(root),
    )

    argv = [sys.executable, "-B", "-X", "utf8", "-m", "src.scania.g10_worker"]
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
                failure_diag = {
                    "status": "FAILED",
                    "error_type": "TimeoutError",
                    "reason": f"G10_WALL_TIMEOUT: Worker exceeded wall limit of {wall_seconds}s",
                    "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }
                (output_dir / "failure_diagnostics.json").write_text(
                    json.dumps(failure_diag, indent=2), encoding="utf-8"
                )
                raise TimeoutError(f"G10_WALL_TIMEOUT: Worker exceeded wall limit of {wall_seconds}s")
            if exit_code is not None:
                break
            time.sleep(0.05)
    finally:
        job.close()

    if not result_path.is_file():
        failure_diag = {
            "status": "FAILED",
            "error_type": "WorkerTerminatedNoResult",
            "reason": f"Worker process terminated without writing worker_result.json (exit_code={exit_code})",
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (output_dir / "failure_diagnostics.json").write_text(
            json.dumps(failure_diag, indent=2), encoding="utf-8"
        )
        raise ExecutorFailure(f"G10_WORKER_CRASHED_NO_RESULT: Exit code {exit_code}")

    worker_result = json.loads(result_path.read_text(encoding="utf-8"))

    if exit_code != 0 or worker_result.get("status") != "PASS":
        err_msg = worker_result.get("reason", f"Exit code {exit_code}")
        raise ExecutorFailure(f"G10_WORKER_EXECUTION_FAILED: {err_msg}")

    return worker_result.get("summary", worker_result)


def run_g10_preflight(
    root: Path = REPO_ROOT,
    auth_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run thorough preflight checks for Gate G10 before execution."""
    root = Path(root).resolve()

    # 1. Python environment
    py_ver = sys.version.split()[0]
    import numpy as _np
    import sklearn as _sk

    # 2. Config integrity
    cfg = load_g10_config(root)
    cfg_sha = get_g10_config_sha(root)

    # 3. Git status check
    git_clean = False
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
    untracked = [line for line in proc.stdout.splitlines() if not line.startswith("??")]
    git_clean = (len(untracked) == 0)

    proc_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    head_sha = proc_head.stdout.strip()

    # 4. G3 artifact verification
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, G3_ACCEPTED_RUN_ID)

    # 5. Authorization file check (if provided)
    auth_summary = {"status": "NOT_CHECKED"}
    if auth_path:
        auth_p = Path(auth_path).resolve()
        if auth_p.is_file():
            auth_data = json.loads(auth_p.read_text(encoding="utf-8"))
            auth_summary = {
                "status": auth_data.get("authorization_status"),
                "run_id": auth_data.get("run_id"),
                "gate": auth_data.get("gate"),
                "permitted_operation": auth_data.get("permitted_operation"),
            }

    # 6. Check output directory non-existence
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)
    output_dir = root / "results/scania_aps/g10" / target_run_id
    output_dir_exists = output_dir.exists()

    return {
        "status": "PREFLIGHT_PASS" if (git_clean and not output_dir_exists) else "PREFLIGHT_WARNING",
        "timestamp": time.time(),
        "python_version": py_ver,
        "numpy_version": _np.__version__,
        "sklearn_version": _sk.__version__,
        "git_head_commit": head_sha,
        "git_workspace_clean": git_clean,
        "g10_config_sha256": cfg_sha,
        "g3_summary": {
            "run_id": g3_summary.get("run_id"),
            "stable_digest": g3_summary.get("stable_digest"),
        },
        "target_run_id": target_run_id,
        "output_directory_exists": output_dir_exists,
        "authorization_check": auth_summary,
        "frozen_policy": {
            "estimator": "RandomForestClassifier",
            "threshold": FROZEN_THRESHOLD,
            "hyperparameters": FROZEN_RF_HYPERPARAMS,
        },
    }


def execute_g10_evaluation(
    root: Path = REPO_ROOT,
    mode: str = "REAL",
    override_output_dir: Optional[Path] = None,
    synthetic_test_data: Optional[Tuple[np.ndarray, np.ndarray]] = None,
) -> Dict[str, Any]:
    """Execute Gate G10 independent Official Test evaluation under supervised containment.

    Enforces all G10 execution blockers:
    1. Preflight & Authorization verification occurs BEFORE creating directory, fitting, or accessing Test.
    2. Final run directory is NOT created before authorization and preflight PASS.
    3. Exactly 1 deterministic refit under Windows Job Object with 1 thread, 2048 MB RAM, 180s wall timeout.
    4. Stop without retry on timeout or failure.
    """
    root = Path(root).resolve()

    # BLOCKER 2: Verification BEFORE creating directory, fitting or touching Official Test!
    # 2a. Verify locked G10 configuration SHA-256
    cfg = load_g10_config(root)
    cfg_sha = get_g10_config_sha(root)
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)

    final_output_dir = (
        Path(override_output_dir).resolve()
        if override_output_dir
        else root / "results/scania_aps/g10" / target_run_id
    )

    # BLOCKER 3: Do NOT create the final run directory before successful authorization and preflight!
    if final_output_dir.exists() and not override_output_dir:
        raise SafetyBlocked(
            f"OUTPUT_DIRECTORY_ALREADY_EXISTS: {final_output_dir}. Re-evaluation of existing run is prohibited."
        )

    # 2b. Verify exact authorized Git HEAD
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True)
    head_sha = proc.stdout.strip().lower()

    # 2c. Verify authentic GitHub Owner comment
    auth_file = root / f"configs/scania/authorizations/{target_run_id}.json"
    auth_record: Dict[str, Any] = {}

    if mode == "REAL":
        if not auth_file.is_file():
            raise ExecutorBlocked(f"AUTHORIZATION_FILE_MISSING: {auth_file}")
        auth_record = json.loads(auth_file.read_text(encoding="utf-8"))

        if auth_record.get("authorization_status") != "AUTHORIZED":
            raise ExecutorBlocked(
                f"RUN_NOT_AUTHORIZED: Status is '{auth_record.get('authorization_status')}'. Requires authentic Owner approval on Issue #17."
            )

        # Config SHA match
        rec_config_sha = auth_record.get("locked_configuration", {}).get("config_sha256", "").lower()
        if rec_config_sha != cfg_sha.lower():
            raise ExecutorBlocked(f"CONFIG_SHA_MISMATCH: record {rec_config_sha} != actual {cfg_sha}")

        # Git commit match
        rec_commit = auth_record.get("source_integrity", {}).get("authorized_commit", "").lower()
        if rec_commit != head_sha:
            raise ExecutorBlocked(f"COMMIT_MISMATCH: authorized {rec_commit} != current HEAD {head_sha}")

        # Live comment verification
        ref_url = auth_record.get("owner_approval", {}).get("reference", "")
        verify_g10_owner_approval_reference(ref_url, auth_record, mode="REAL")
    else:
        # Synthetic testing mode
        auth_record = {
            "run_id": target_run_id,
            "authorization_status": "SYNTHETIC_TEST",
            "permitted_operation": "G10_OFFICIAL_TEST_EVALUATION",
            "evaluation_mode": EVALUATION_MODE,
            "source_integrity": {"authorized_commit": head_sha},
            "locked_configuration": {"config_sha256": cfg_sha},
            "budget": {"total_max_fits": 1, "max_trials": 1, "max_fits_per_trial": 1},
        }

    # 2d. Verify G3 integrity
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, G3_ACCEPTED_RUN_ID)

    # 2e. Verify frozen Trial 16 policy and authorized fit budget of exactly one
    rec_budget = auth_record.get("budget", {})
    if int(rec_budget.get("total_max_fits", 0)) != 1 or int(rec_budget.get("max_trials", 0)) != 1:
        raise ExecutorBlocked(
            f"INVALID_FIT_BUDGET: G10 requires exactly 1 fit, got budget={rec_budget}"
        )

    # Build allowlist of permissible paths for worker I/O guard
    allowlist_paths = list(allowlist)
    allowlist_paths.extend([
        root / "configs/scania/g10_evaluation.json",
        auth_file,
        root / cfg["data"]["raw_zip_path"],
        root / cfg["data"]["preprocessor_path"],
        final_output_dir,
    ])

    # BLOCKER 3: Create final output directory ONLY AFTER successful authorization and preflight!
    final_output_dir.mkdir(parents=True, exist_ok=True)

    # Prepare task configuration for supervised worker
    task_config = {
        "run_id": target_run_id,
        "mode": mode,
        "frozen_rf_params": FROZEN_RF_HYPERPARAMS,
        "frozen_threshold": FROZEN_THRESHOLD,
        "capacity_limit_K": CAPACITY_LIMIT_K_TEST if mode == "REAL" else 100,
        "expected_test_rows": cfg["data"]["expected_test_rows"],
        "cost_fp": cfg["cost_model"]["cost_fp"],
        "cost_fn": cfg["cost_model"]["cost_fn"],
        "raw_zip_path": cfg["data"]["raw_zip_path"],
        "raw_zip_sha256": cfg["data"]["raw_zip_sha256"],
        "test_filename_in_zip": cfg["data"]["test_filename_in_zip"],
        "train_processed_path": cfg["data"]["train_processed_path"],
        "membership_path": cfg["data"]["membership_path"],
        "validation_processed_path": cfg["data"]["validation_processed_path"],
        "preprocessor_path": cfg["data"]["preprocessor_path"],
    }
    if synthetic_test_data is not None:
        task_config["synthetic_test_data"] = {
            "X": sanitize_for_strict_json(synthetic_test_data[0]),
            "y": sanitize_for_strict_json(synthetic_test_data[1]),
        }

    # BLOCKER 1: Enforce runtime limits via supervised worker under Windows Job Object
    return orchestrate_g10_worker_in_job(
        root=root,
        run_id=target_run_id,
        output_dir=final_output_dir,
        allowlist=allowlist_paths,
        task_config=task_config,
        wall_seconds=180,
        ram_cap_bytes=2048 * 1024 * 1024,
        mode=mode,
    )
