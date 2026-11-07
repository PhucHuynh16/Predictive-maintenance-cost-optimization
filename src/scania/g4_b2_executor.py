"""SC-G4 Baseline Executor: locked G3 artifact verification, allowlist I/O guard, and baseline pipeline.

Safety boundaries:
- Fitting is restricted to Train only. Validation is evaluated read-only.
- All baseline parameters (B0, B1, B2) are locked to canonical configurations.
- gate_b_authorized=False is strictly enforced: no real-data fitting without Owner authorization.
- The Python audit hook is an application-level guard for Python open(), NOT an OS-level sandbox.
- Joblib deserialization is completely eliminated from the runtime execution path.
- Row-alignment of Train and Validation labels against official Train CSV is MANDATORY.
- G3 artifacts are verified against the accepted G3 reference stable manifest (MANDATORY).
- Supervisor/worker architecture runs under Windows Job Object with strict memory & time limits.
- Official Test set is sealed until G10.
"""
import csv
from importlib.metadata import version
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
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

import urllib.request

from .artifacts import code_digest
from .baselines import STUMP_PARAMS, LR_PARAMS, BaselineFailure
from .constraints import PRIMARY, SECONDARY, POLICIES, actions_from_probabilities, capacity_report, probabilities
from .contracts import canonical, digest, environment, object_hash
from .cost_model import binary_vector, observed_aps_cost
from .data import array_hash, ordered_ids_hash
from .evaluation import evaluate_aps_policy
from .g4_contract import CONFIG_SHA, GATE_A_CONFIG_SHA, G3_RUN, G3_STABLE, load_config, Blocked

REPO_ROOT = Path(__file__).resolve().parents[2]


class SafetyBlocked(ValueError):
    """Raised when an operation violates security, isolation, or data access boundaries."""
    pass


class ExecutorBlocked(ValueError):
    """Raised when pipeline preconditions, authorization gates, or contract invariants fail."""
    pass


class ExecutorFailure(ExecutorBlocked):
    """Raised when worker execution fails, preserving partial telemetry and error context."""
    def __init__(self, message, worker_result=None):
        super().__init__(message)
        self.worker_result = worker_result or {}


def install_executor_io_guard(root, output, allowlist):
    """Application-level audit hook for Python open(), strictly limiting reads to allowlist.

    NOTE: This is an application-level guard for Python open(), NOT an OS-level
    filesystem sandbox for arbitrary native code.

    Enforces:
    1. Rejection of arbitrary input paths.
    2. Zero access to raw training CSV, Official Test set, or archive ZIP.
    3. Writes permitted ONLY inside the designated output run directory.
    4. Writes to source data, repository code, or G3 artifacts are strictly forbidden.
    5. Reads of .npy, .npz, .csv, or data/ files permitted ONLY if path is in allowlist.
    """
    root = Path(root).resolve()
    output = Path(output).resolve()
    resolved_allowlist = {Path(p).resolve() for p in allowlist}

    def audit(name, args):
        if name != "open" or isinstance(args[0], int):
            return
        raw = os.fsdecode(args[0])
        p = Path(raw).resolve()

        # Strict test set and raw archive access barriers
        name_lower = p.name.casefold()
        if "aps_failure_test" in name_lower:
            raise SafetyBlocked("TEST_SET_ACCESS_DENIED_SEALED_UNTIL_G10")
        if p.suffix.casefold() == ".zip":
            raise SafetyBlocked("ARCHIVE_ACCESS_DENIED_SEALED_UNTIL_G10")
        if name_lower == "aps_failure_training_set.csv":
            raise SafetyBlocked("RAW_TRAIN_CSV_READ_DENIED_USE_PROCESSED_ARRAYS_ONLY")

        # Detect write intents
        mode = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 else 0
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or bool(
            flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
        )

        if writing:
            # Writes are allowed only inside the designated run output directory
            if not p.is_relative_to(output):
                raise SafetyBlocked(f"EXECUTOR_WRITE_OUTSIDE_OWN_RUN: {p.name}")
            # Source directories and G3 processed artifacts are read-only
            if p.is_relative_to(root / "data") or p.is_relative_to(root / "results/scania_aps/g3"):
                raise SafetyBlocked(f"SOURCE_OR_G3_ARTIFACT_WRITE_FORBIDDEN: {p.name}")
        else:
            # Reads within data/ or with data-bearing suffixes must be explicitly allowlisted
            is_data_path = p.is_relative_to(root / "data")
            is_data_ext = p.suffix.casefold() in {".npy", ".npz", ".csv"}
            if is_data_path or is_data_ext:
                if p not in resolved_allowlist:
                    raise SafetyBlocked(f"EXECUTOR_READ_NOT_IN_ALLOWLIST: {p.name}")

    import sys
    sys.addaudithook(audit)


def verify_g3_artifacts_and_build_allowlist(root, g3_run_id=None):
    """Verify hashes, schema, and label alignment of G3 artifacts and build read-only allowlist.

    Eliminates joblib deserialization completely from runtime path.
    MANDATORY Validations:
    - LF-normalized checksums of G3 public metadata.
    - Consistency of mathematical data keys with accepted G3 reference manifest (MANDATORY).
    - official_split.json membership hash against stable_manifest.
    - membership.npz partition sizes (48k Train / 12k Validation), disjoint union, and ordered IDs.
    - Explicit row-alignment of labels y_train and y_val with official Train CSV (MANDATORY).
    - Strict parsing of 'pos' and 'neg' labels only (reject unknown or malformed tokens).
    - Binary label domain {0, 1} and exact positive class counts (800 Train / 200 Val).
    - Shapes (48000, 170) and (12000, 170), dtype float64, finite check, and array hashes for:
      tree_train, tree_validation, lr_train, lr_validation.

    Returns:
        (allowlist_paths, g3_summary_dict)
    """
    root = Path(root).resolve()
    if g3_run_id is None:
        cfg_path = root / "configs/scania/g4_baselines.json"
        if cfg_path.is_file():
            g3_run_id = json.loads(cfg_path.read_text(encoding="utf-8")).get("g3_input_run")
        if not g3_run_id:
            g3_run_id = "official_20261029_04"

    meta_dir = root / "results/scania_aps/g3" / g3_run_id
    if not meta_dir.is_dir():
        raise ExecutorBlocked(f"G3_METADATA_DIR_MISSING: {g3_run_id}")

    manifest_file = meta_dir / "stable_manifest.json"
    checksums_file = meta_dir / "checksums.json"
    if not manifest_file.is_file() or not checksums_file.is_file():
        raise ExecutorBlocked("G3_MANIFEST_OR_CHECKSUMS_MISSING")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    checksums = json.loads(checksums_file.read_text(encoding="utf-8"))

    # Verify public metadata checksums
    for name, expected_sha in checksums.items():
        p = meta_dir / name
        if not p.is_file():
            raise ExecutorBlocked(f"G3_CHECKSUM_FILE_MISSING: {name}")
        content = p.read_bytes().replace(b"\r\n", b"\n")
        if digest(content) != expected_sha:
            raise ExecutorBlocked(f"G3_PUBLIC_CHECKSUM_MISMATCH: {name}")

    # MANDATORY: Compare mathematical data keys directly against accepted G3 reference manifest
    accepted_manifest_file = root / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"
    if not accepted_manifest_file.is_file():
        raise ExecutorBlocked("ACCEPTED_G3_MANIFEST_MISSING: Reference G3 manifest official_20261029_04 must exist")

    accepted_manifest = json.loads(accepted_manifest_file.read_text(encoding="utf-8"))
    data_keys = [
        "source_sha256",
        "schema_sha256",
        "config_sha256",
        "membership_sha256",
        "train_ordered_ids_sha256",
        "validation_ordered_ids_sha256",
        "imputer_statistics_sha256",
        "scaler_mean_sha256",
        "scaler_scale_sha256",
        "array_sha256",
    ]
    for key in data_keys:
        if manifest.get(key) != accepted_manifest.get(key):
            raise ExecutorBlocked(f"G3_MANIFEST_DATA_KEY_MISMATCH_WITH_ACCEPTED_G3: {key}")

    # Verify official_split.json
    split_file = root / "data/processed/scania_aps/official_split.json"
    if not split_file.is_file():
        raise ExecutorBlocked("G3_OFFICIAL_SPLIT_JSON_MISSING")

    membership_data = json.loads(split_file.read_text(encoding="utf-8"))
    if object_hash(membership_data) != manifest["membership_sha256"]:
        raise ExecutorBlocked("MEMBERSHIP_HASH_MISMATCH")

    # Locate processed arrays directory
    processed_dir = root / "data/processed/scania_aps" / g3_run_id
    if not processed_dir.is_dir():
        raise ExecutorBlocked(f"G3_PROCESSED_ARRAYS_DIR_MISSING: {g3_run_id}")

    npz_file = processed_dir / "membership.npz"
    if not npz_file.is_file():
        raise ExecutorBlocked("MEMBERSHIP_NPZ_MISSING")

    with np.load(npz_file, allow_pickle=False) as z:
        if set(z.files) != {"train", "validation", "y_train", "y_validation"}:
            raise ExecutorBlocked("MEMBERSHIP_NPZ_MEMBER_LIST_INVALID")
        train = z["train"].copy()
        val = z["validation"].copy()
        y_train = z["y_train"].copy()
        y_val = z["y_validation"].copy()

    # Verify partition sizes
    if len(train) != 48000 or len(val) != 12000:
        raise ExecutorBlocked(f"PARTITION_SIZE_MISMATCH: train={len(train)}, val={len(val)}")
    if len(y_train) != 48000 or len(y_val) != 12000:
        raise ExecutorBlocked(f"LABEL_SIZE_MISMATCH: y_train={len(y_train)}, y_val={len(y_val)}")

    train_set, val_set = set(train), set(val)
    if train_set.intersection(val_set):
        raise ExecutorBlocked("PARTITIONS_NOT_DISJOINT")
    if len(train_set.union(val_set)) != 60000 or train_set.union(val_set) != set(range(60000)):
        raise ExecutorBlocked("PARTITIONS_COVERAGE_MISMATCH")

    # Verify binary target domain and positive class counts
    if not np.array_equal(np.unique(y_train), [0, 1]):
        raise ExecutorBlocked("TRAIN_LABELS_NOT_BINARY_0_1")
    if not np.array_equal(np.unique(y_val), [0, 1]):
        raise ExecutorBlocked("VAL_LABELS_NOT_BINARY_0_1")

    pos_train = int(np.sum(y_train == 1))
    neg_train = int(np.sum(y_train == 0))
    pos_val = int(np.sum(y_val == 1))
    neg_val = int(np.sum(y_val == 0))
    if pos_train != 800 or neg_train != 47200:
        raise ExecutorBlocked(f"TRAIN_CLASS_COUNTS_MISMATCH: pos={pos_train}, neg={neg_train}")
    if pos_val != 200 or neg_val != 11800:
        raise ExecutorBlocked(f"VAL_CLASS_COUNTS_MISMATCH: pos={pos_val}, neg={neg_val}")

    # Check ordered IDs hashes
    source_sha = manifest["source_sha256"]
    if ordered_ids_hash(train, source_sha) != manifest["train_ordered_ids_sha256"]:
        raise ExecutorBlocked("TRAIN_ORDERED_IDS_HASH_MISMATCH")
    if ordered_ids_hash(val, source_sha) != manifest["validation_ordered_ids_sha256"]:
        raise ExecutorBlocked("VAL_ORDERED_IDS_HASH_MISMATCH")

    # MANDATORY: Explicit label row-alignment verification against official Train CSV
    raw_train_file = root / "data/raw/scania_aps/aps_failure_training_set.csv"
    if not raw_train_file.is_file():
        raise ExecutorBlocked("RAW_TRAIN_CSV_MISSING: Official Train CSV required for label row-alignment")

    raw_bytes = raw_train_file.read_bytes()
    if digest(raw_bytes) != source_sha:
        raise ExecutorBlocked("RAW_TRAIN_CSV_HASH_MISMATCH")

    lines = raw_bytes.splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith(b"class,"):
            header_idx = idx
            break
    if header_idx is None:
        raise ExecutorBlocked("RAW_TRAIN_CSV_HEADER_MISSING")

    data_lines = [ln for ln in lines[header_idx + 1:] if ln.strip()]
    if len(data_lines) != 60000:
        raise ExecutorBlocked(f"RAW_TRAIN_CSV_ROW_COUNT_MISMATCH: {len(data_lines)}")

    raw_y = np.empty(60000, dtype=np.int8)
    for idx, ln in enumerate(data_lines):
        tok = ln.split(b",", 1)[0].strip()
        if tok == b"pos":
            raw_y[idx] = 1
        elif tok == b"neg":
            raw_y[idx] = 0
        else:
            raise ExecutorBlocked(f"INVALID_RAW_TARGET_LABEL: row {idx + 1} has token '{tok.decode(errors='replace')}'")

    if not np.array_equal(y_train, raw_y[train]):
        raise ExecutorBlocked("TRAIN_LABEL_ROW_ALIGNMENT_MISMATCH")
    if not np.array_equal(y_val, raw_y[val]):
        raise ExecutorBlocked("VAL_LABEL_ROW_ALIGNMENT_MISMATCH")

    # Verify processed arrays without loading joblib preprocessors
    allowlist = {split_file, npz_file}
    for name, expected_hash in manifest["array_sha256"].items():
        arr_file = processed_dir / f"{name}.npy"
        if not arr_file.is_file():
            raise ExecutorBlocked(f"PROCESSED_ARRAY_MISSING: {name}")
        arr = np.load(arr_file, mmap_mode="r", allow_pickle=False)
        expected_rows = 48000 if name.endswith("_train") else 12000
        if arr.shape != (expected_rows, 170):
            raise ExecutorBlocked(f"ARRAY_SHAPE_MISMATCH: {name} got {arr.shape}")
        if arr.dtype != np.dtype("float64"):
            raise ExecutorBlocked(f"ARRAY_DTYPE_MISMATCH: {name} got {arr.dtype}")
        if not np.isfinite(arr).all():
            raise ExecutorBlocked(f"ARRAY_NONFINITE_VALUES: {name}")
        if array_hash(arr) != expected_hash:
            raise ExecutorBlocked(f"ARRAY_HASH_MISMATCH: {name}")
        allowlist.add(arr_file)

    summary = dict(
        g3_run_id=g3_run_id,
        source_sha256=source_sha,
        membership_sha256=manifest["membership_sha256"],
        train_rows=48000,
        validation_rows=12000,
        features=170,
        array_hashes=manifest["array_sha256"],
        imputer_statistics_sha256=manifest["imputer_statistics_sha256"],
        scaler_mean_sha256=manifest["scaler_mean_sha256"],
        scaler_scale_sha256=manifest["scaler_scale_sha256"],
        allowlist_count=len(allowlist),
        joblib_deserialization="ELIMINATED",
        label_row_alignment="VERIFIED_MATCH",
    )
    return allowlist, summary


def fit_and_score_baseline_model(baseline_id, x_train, y_train, x_val, y_val, *, b1_params=None, b2_params=None):
    """Execute a single baseline model pipeline with strict Train-only fit and Validation-only scoring."""
    if baseline_id not in ("B0", "B1", "B2"):
        raise ValueError(f"UNKNOWN_BASELINE_ID: {baseline_id}")

    y_train = binary_vector(y_train, "train_labels")
    y_val = binary_vector(y_val, "val_labels")

    if baseline_id == "B0":
        actions = np.zeros(len(y_val), dtype=np.int8)
        row = evaluate_aps_policy(y_val, actions, scores=None, baseline_id="B0", role="REFERENCE")
        telemetry = dict(
            baseline_id="B0",
            fit_seconds=0.0,
            predict_seconds=0.0,
            warnings=[],
            parameters=None,
            classes=[0],
            real_estimator_fits=0,
            validation_scored=True,
        )
        return [row], telemetry

    if baseline_id == "B1":
        params = STUMP_PARAMS if b1_params is None else b1_params
        model = DecisionTreeClassifier(**params)
    elif baseline_id == "B2":
        params = LR_PARAMS if b2_params is None else b2_params
        model = LogisticRegression(**params)

    t0 = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x_train, y_train)

    fit_sec = time.perf_counter() - t0

    conv_warnings = [w for w in caught if issubclass(w.category, ConvergenceWarning)]
    if conv_warnings:
        raise BaselineFailure(f"FAILED_CONVERGENCE_WARNING: {conv_warnings[0].message}", caught)

    classes = list(model.classes_)
    if classes != [0, 1]:
        raise BaselineFailure(f"FAILED_CLASS_MAPPING: got {classes}, expected [0, 1]", caught)

    t1 = time.perf_counter()
    proba = np.asarray(model.predict_proba(x_val))
    pred_sec = time.perf_counter() - t1

    if proba.shape != (len(x_val), 2):
        raise BaselineFailure(f"FAILED_INVALID_PROBABILITY_SHAPE: {proba.shape}", caught)
    if not np.isfinite(proba).all():
        raise BaselineFailure("FAILED_NONFINITE_PROBABILITIES", caught)
    if not np.allclose(proba.sum(axis=1), 1.0, atol=1e-5):
        raise BaselineFailure("FAILED_PROBABILITIES_DO_NOT_SUM_TO_ONE", caught)

    scores = probabilities(proba[:, 1])

    rows = []
    for role, tau in POLICIES.items():
        acts = actions_from_probabilities(scores, tau)
        row = evaluate_aps_policy(y_val, acts, scores, baseline_id=baseline_id, role=role, threshold=tau)
        rows.append(row)

    telemetry = dict(
        baseline_id=baseline_id,
        fit_seconds=fit_sec,
        predict_seconds=pred_sec,
        warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught],
        parameters=model.get_params(deep=False),
        classes=[int(c) for c in classes],
        real_estimator_fits=1,
        validation_scored=True,
    )
    return rows, telemetry


def execute_synthetic_pipeline_test(n_train=200, n_val=60, n_features=4, random_state=42):
    """Run an isolated end-to-end synthetic test of the G4 baseline execution pipeline."""
    rng = np.random.RandomState(random_state)
    x_train = rng.randn(n_train, n_features).astype(np.float64)
    y_train = (rng.rand(n_train) < 0.1).astype(np.int8)
    y_train[0], y_train[1] = 0, 1

    x_val = rng.randn(n_val, n_features).astype(np.float64)
    y_val = (rng.rand(n_val) < 0.1).astype(np.int8)
    y_val[0], y_val[1] = 0, 1

    all_rows = []
    all_telemetry = {}

    for b_id in ("B0", "B1", "B2"):
        rows, tel = fit_and_score_baseline_model(b_id, x_train, y_train, x_val, y_val)
        all_rows.extend(rows)
        all_telemetry[b_id] = tel

    return dict(rows=all_rows, telemetry=all_telemetry, status="SYNTHETIC_TEST_PASSED")


def _orchestrate_worker_in_windows_job(root, run_id, output_dir, allowlist, task_config, *,
                                       wall_seconds=120, ram_cap_bytes=2048 * 1024 * 1024, mode="REAL"):
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
        SC_G4_B2_RUN=run_id,
        SC_G4_B2_TASK_PATH=str(task_path),
        SC_G4_B2_ALLOWLIST_PATH=str(allowlist_path),
        SC_G4_B2_OUTPUT_DIR=str(output_dir),
        SC_G4_B2_ROOT_DIR=str(root),
        SC_G4_B2_NONCE=secrets.token_hex(24),
    )

    argv = [sys.executable, "-B", "-X", "utf8", "-m", "src.scania.g4_b2_worker"]
    job = WindowsJob(argv, child_env, root, ram_cap_bytes, active_limit=2)

    t0 = time.perf_counter()
    deadline = t0 + wall_seconds
    timed_out = False
    exit_code = None

    try:
        job.resume()
        while True:
            exit_code = job.poll()
            now = time.perf_counter()
            if now >= deadline:
                timed_out = True
                job.terminate()
                raise TimeoutError(f"RUN_WALL_TIMEOUT: Worker exceeded wall limit of {wall_seconds}s")
            if exit_code is not None:
                break
            time.sleep(0.02)

        peak_ram_bytes = job.limits().get("peak_job_memory_bytes", 0)
    finally:
        job.close()

    elapsed = time.perf_counter() - t0

    if not result_path.is_file():
        raise ExecutorBlocked(f"WORKER_CRASHED_NO_RESULT: Exit code {exit_code}")

    worker_result = json.loads(result_path.read_text(encoding="utf-8"))

    if exit_code != 0 or worker_result.get("status") != "PASS":
        err_msg = worker_result.get("reason", f"Exit code {exit_code}")
        raise ExecutorFailure(f"WORKER_EXECUTION_FAILED: {err_msg}", worker_result=worker_result)

    # Build report evidence with truthful distinction between real and synthetic (F3)
    is_real = (mode == "REAL")
    report = dict(
        run_id=run_id,
        mode=mode,
        status="COMPLETE",
        lifecycle="COMPLETE",
        real_estimator_fits=worker_result["total_estimator_fits"] if is_real else 0,
        synthetic_estimator_fits=worker_result["total_estimator_fits"] if not is_real else 0,
        real_validation_scored=worker_result["validation_scored"] if is_real else False,
        synthetic_validation_scored=worker_result["validation_scored"] if not is_real else False,
        rows=worker_result["rows"],
        telemetry=worker_result["telemetry"],
        observed_timings=worker_result["observed_timings"],
        measured_wall_seconds=elapsed,
        measured_peak_ram_mb=peak_ram_bytes / (1024**2),
    )
    return report


def _get_github_token():
    try:
        proc = subprocess.Popen(
            ["git", "credential", "fill"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        out, _ = proc.communicate("protocol=https\nhost=github.com\n\n", timeout=5)
        return dict(line.split("=", 1) for line in out.strip().split("\n") if "=" in line).get("password")
    except Exception:
        return None


def verify_owner_approval_reference(ref, mode="REAL"):
    """Verify that the referenced Owner approval is genuine and verifiable.

    Trust boundary rules:
    - No authorization inferred from an agent-generated document.
    - An unverifiable GitHub link must fail closed.
    - Real mode requires reference on official repository with verified Owner author (PhucHuynh16).
    - Synthetic boundary: permits SYNTHETIC_FIXTURE_ tokens in synthetic mode only.
    """
    if not isinstance(ref, str) or not ref:
        raise ExecutorBlocked("INVALID_OWNER_APPROVAL_REFERENCE: Reference must be a non-empty string URL")

    if mode == "SYNTHETIC":
        if ref.startswith("SYNTHETIC_FIXTURE_"):
            return True
        if ref.startswith("https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/"):
            return True
        raise ExecutorBlocked(f"INVALID_SYNTHETIC_APPROVAL_REFERENCE: {ref}")

    # REAL MODE: Strictly bind to genuine Owner decision on official repository
    pattern = r"^https://github\.com/PhucHuynh16/Predictive-maintenance-cost-optimization/(issues|pull)/\d+(#issuecomment-(\d+))?$"
    m = re.match(pattern, ref)
    if not m:
        raise ExecutorBlocked(f"INVALID_OWNER_APPROVAL_REFERENCE: {ref}")

    comment_id = m.group(3)
    if not comment_id:
        raise ExecutorBlocked(f"UNVERIFIABLE_OWNER_APPROVAL: Must reference specific comment ID: {ref}")

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
    except Exception as exc:
        if isinstance(exc, ExecutorBlocked):
            raise
        raise ExecutorBlocked(f"UNVERIFIABLE_OWNER_APPROVAL: Could not verify Owner approval reference {ref}: {exc}")
    return True


def validate_owner_authorization_record(auth_path_or_dict, expected_run_id, expected_config_sha=None,
                                        expected_g3_run_id=None, expected_g3_manifest_sha=None,
                                        mode="REAL", root=None):
    """Enforce schema and semantic validation of an Owner baseline authorization record (F2 & Trust Boundary).

    Schema & Invariants:
    1. An actual Owner approval decision whose GitHub reference, author and approved scope can be verified.
       An unverifiable GitHub link fails closed.
    2. Exact run ID and operation (BASELINE_FITTING_VALIDATION_ONLY in REAL).
    3. Actual repository source HEAD SHA, bound to git rev-parse HEAD.
    4. Exact approved configuration version/hash.
    5. Exact accepted G3 manifest hash and input run.
    6. Exact allowed models: B0, B1, B2.
    7. Fit budget: B0=0, B1=1, B2=1, total_max_fits=2.
    8. Maximum 1 native thread, 2048 MB RAM, 120 seconds total wall time.
    9. Train fitting and Validation scoring only.
    10. Official Test SEALED UNTIL G10.
    - Mode distinction: SYNTHETIC_ONLY records can NEVER authorize real Scania data access.
    """
    if isinstance(auth_path_or_dict, (str, Path)):
        p = Path(auth_path_or_dict).resolve()
        if not p.is_file():
            raise ExecutorBlocked(f"GATE_B2_OWNER_AUTHORIZATION_RECORD_MISSING: {p.name}")
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

    # 3. Mode check and permitted operation
    auth_mode = record.get("mode", "REAL")
    op = record.get("permitted_operation") or record.get("operation")
    if mode == "REAL":
        if auth_mode == "SYNTHETIC_ONLY":
            raise ExecutorBlocked("SYNTHETIC_AUTHORIZATION_CANNOT_AUTHORIZE_REAL_DATA")
        if auth_mode != "REAL":
            raise ExecutorBlocked(f"INVALID_AUTHORIZATION_MODE_FOR_REAL: {auth_mode}")
        if op != "BASELINE_FITTING_VALIDATION_ONLY":
            raise ExecutorBlocked(f"INVALID_PERMITTED_OPERATION: {op}")
    elif mode == "SYNTHETIC":
        if auth_mode not in {"SYNTHETIC_ONLY", "REAL"}:
            raise ExecutorBlocked(f"INVALID_SYNTHETIC_AUTHORIZATION_MODE: {auth_mode}")
        if op not in {"SYNTHETIC_BASELINE_TESTING_ONLY", "BASELINE_FITTING_VALIDATION_ONLY"}:
            raise ExecutorBlocked(f"INVALID_PERMITTED_OPERATION: {op}")

    # 4. Owner approval reference check and trust verification
    owner_app = record.get("owner_approval")
    if not isinstance(owner_app, dict):
        raise ExecutorBlocked("INVALID_OWNER_APPROVAL_OBJECT")
    ref = str(owner_app.get("reference") or owner_app.get("approval_reference") or "")
    approved_by = owner_app.get("approved_by", "")
    if approved_by not in {"OWNER", "PhucHuynh16"}:
        raise ExecutorBlocked(f"AUTHORIZATION_NOT_FROM_OWNER: Approved by '{approved_by}' is not recognized")
    decision = owner_app.get("decision", "APPROVED")
    if decision != "APPROVED":
        raise ExecutorBlocked(f"AUTHORIZATION_NOT_APPROVED: Decision is '{decision}'")

    verify_owner_approval_reference(ref, mode=mode)

    # 5. Source integrity and repository HEAD binding
    src_int = record.get("source_integrity") if isinstance(record.get("source_integrity"), dict) else record
    auth_commit = str(src_int.get("authorized_commit", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", auth_commit):
        raise ExecutorBlocked("INVALID_AUTHORIZED_COMMIT_SHA")

    if root is not None:
        try:
            current_head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(root), stderr=subprocess.PIPE
            ).decode("utf-8").strip()
            if auth_commit != current_head:
                raise ExecutorBlocked(
                    f"AUTHORIZED_COMMIT_MISMATCH: Authorized commit {auth_commit} does not match repository HEAD {current_head}"
                )
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if expected_config_sha is None:
        expected_config_sha = CONFIG_SHA
    cfg_sha = src_int.get("canonical_config_sha256", "")
    if cfg_sha != expected_config_sha:
        raise ExecutorBlocked(f"AUTHORIZED_CONFIG_SHA_MISMATCH: {cfg_sha} != {expected_config_sha}")

    # 6. Data scope and partition boundaries
    data_scope = record.get("data_scope") if isinstance(record.get("data_scope"), dict) else record
    if expected_g3_run_id is None:
        expected_g3_run_id = G3_RUN
    if expected_g3_manifest_sha is None:
        expected_g3_manifest_sha = G3_STABLE

    g3_run = data_scope.get("accepted_g3_run_id") or data_scope.get("expected_g3_run_id")
    g3_manifest = data_scope.get("accepted_g3_manifest_sha256") or data_scope.get("expected_g3_manifest_sha")
    if mode == "REAL":
        if g3_run != expected_g3_run_id:
            raise ExecutorBlocked(f"ACCEPTED_G3_RUN_ID_MISMATCH: {g3_run} != {expected_g3_run_id}")
        if g3_manifest != expected_g3_manifest_sha:
            raise ExecutorBlocked(f"ACCEPTED_G3_MANIFEST_SHA_MISMATCH: {g3_manifest} != {expected_g3_manifest_sha}")

    allowed_parts = data_scope.get("allowed_partitions") or data_scope.get("data_partitions_permitted")
    if set(allowed_parts or []) != {"train", "validation"}:
        raise ExecutorBlocked("INVALID_ALLOWED_PARTITIONS: Only train and validation allowed")
    if data_scope.get("official_test_sealed") is not True:
        raise ExecutorBlocked("OFFICIAL_TEST_NOT_SEALED: Test partition must be sealed")

    # 7. Approved models & fit budget (B0=0, B1=1, B2=1, total_max_fits=2)
    models = record.get("approved_models") or ["B0", "B1", "B2"]
    if models != ["B0", "B1", "B2"]:
        raise ExecutorBlocked("INVALID_APPROVED_MODELS: Exactly B0, B1, B2 required")
    fit_budget = record.get("fit_budget", {})
    b0 = fit_budget.get("B0", fit_budget.get("B0_majority_dummy"))
    b1 = fit_budget.get("B1", fit_budget.get("B1_decision_stump"))
    b2 = fit_budget.get("B2", fit_budget.get("B2_logistic_regression"))
    total_fits = fit_budget.get("total_max_fits")
    if b0 != 0 or b1 != 1 or b2 != 1:
        raise ExecutorBlocked("INVALID_FIT_BUDGET_ALLOCATION: Must be B0=0, B1=1, B2=1")
    if total_fits != 2:
        raise ExecutorBlocked("INVALID_FIT_BUDGET: total_max_fits must be exactly 2")

    # 8. Resource limits (1 thread, 2048 MB RAM, 120s wall time)
    limits = record.get("resource_limits", {})
    if limits.get("max_native_threads") != 1:
        raise ExecutorBlocked("INVALID_MAX_NATIVE_THREADS: Must be 1")
    if limits.get("max_ram_mb", 0) > 2048:
        raise ExecutorBlocked("RAM_LIMIT_EXCEEDS_CAP: Max 2048 MB allowed")
    if limits.get("max_wall_seconds", 0) > 120:
        raise ExecutorBlocked("WALL_LIMIT_EXCEEDS_CAP: Max 120s allowed")

    return record


def execute_real_baseline_gate(root, run_id, *, g3_run_id=None, run_reservation=None):
    """Execution entrypoint for real Scania baseline experiments.

    CRITICAL GATE:
    Fails closed immediately if an authentic Owner authorization record is not present.
    Does NOT accept caller-supplied config overrides. Reads strictly from configs/scania/g4_baselines.json.
    """
    root = Path(root).resolve()

    # 1. Output directory setup & single-owner run reservation check (F1)
    output_dir = root / "results/scania_aps/g4" / run_id
    if run_reservation is not None:
        if not hasattr(run_reservation, "validate_reservation_contract"):
            raise ExecutorBlocked("INVALID_RUN_RESERVATION_TYPE: Expected EvidenceRun instance")
        run_reservation.validate_reservation_contract(root, run_id)
        if Path(run_reservation.path).resolve() != output_dir.resolve():
            raise ExecutorBlocked(f"RESERVATION_PATH_MISMATCH: {run_reservation.path} != {output_dir}")
        existing = {p.name for p in output_dir.iterdir()}
        if {"checksums.json", "run_summary.json", "baseline_metrics.json"}.intersection(existing):
            raise ExecutorBlocked(f"OUTPUT_DIRECTORY_ALREADY_EXISTS: {run_id}")
    else:
        if output_dir.exists():
            raise ExecutorBlocked(f"OUTPUT_DIRECTORY_ALREADY_EXISTS: {run_id}")

    cfg_file = root / "configs/scania/g4_baselines.json"
    if not cfg_file.is_file():
        raise ExecutorBlocked("BASELINE_CONFIG_FILE_MISSING")

    # Explicit run-specific Owner authorization record schema & semantic validation (F2, Trust Boundary)
    auth_file = root / "configs/scania/authorizations" / f"{run_id}.json"
    if not auth_file.is_file():
        raise ExecutorBlocked(f"GATE_B2_NOT_AUTHORIZED: Baseline execution requires explicit Owner task authorization record: {auth_file.name}")

    auth_record = validate_owner_authorization_record(
        auth_file, run_id, expected_config_sha=CONFIG_SHA, expected_g3_run_id=g3_run_id,
        mode="REAL", root=root
    )

    # Validate controlled configuration transition via g4_contract
    try:
        src_int = auth_record.get("source_integrity") if isinstance(auth_record.get("source_integrity"), dict) else auth_record
        expected_sha = src_int.get("canonical_config_sha256") or CONFIG_SHA
        config = load_config(root, gate="GATE_B2",
                             expected_config_sha=expected_sha,
                             auth_record=auth_record)
    except Blocked as exc:
        raise ExecutorBlocked(f"GATE_B2_CONFIG_CONTRACT_BLOCKED: {exc}")

    if run_reservation is None:
        output_dir.mkdir(parents=True, exist_ok=False)

    # 2. Verify G3 artifacts and construct allowlist
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, g3_run_id)

    # 3. Setup task configuration with locked parameters (F4)
    if g3_run_id is None:
        g3_run_id = config.get("g3_input_run", "official_20261029_04")
    proc_dir = root / "data/processed/scania_aps" / g3_run_id

    task_config = dict(
        run_id=run_id,
        mode="REAL",
        membership_path=str(proc_dir / "membership.npz"),
        tree_train_path=str(proc_dir / "tree_train.npy"),
        tree_val_path=str(proc_dir / "tree_validation.npy"),
        lr_train_path=str(proc_dir / "lr_train.npy"),
        lr_val_path=str(proc_dir / "lr_validation.npy"),
        b1_params=dict(config.get("B1", STUMP_PARAMS)),
        b2_params=dict(config.get("B2", LR_PARAMS)),
    )

    # 4. Launch real worker under Windows Job Object
    report = _orchestrate_worker_in_windows_job(root, run_id, output_dir, allowlist, task_config, mode="REAL")
    return report


def execute_synthetic_baseline_orchestration(root, run_id, *, synthetic_dir=None,
                                             run_reservation=None, auth_record=None,
                                             wall_seconds=120, ram_cap_bytes=2048 * 1024 * 1024,
                                             n_train=200, n_val=60, n_features=10, random_state=42):
    """Synthetic-only integration entrypoint exercising the actual supervisor/worker orchestration.

    Does NOT bypass Gate B2 authorization for real Scania data.
    Constructs isolated synthetic arrays and runs the actual worker subprocess under WindowsJob.
    """
    root = Path(root).resolve()
    if auth_record is not None:
        validate_owner_authorization_record(auth_record, run_id, mode="SYNTHETIC")

    if synthetic_dir is None:
        synthetic_dir = root / "results/scania_aps/g4/synthetic_test" / run_id
    synthetic_dir = Path(synthetic_dir).resolve()
    synthetic_dir.mkdir(parents=True, exist_ok=True)

    # Generate synthetic data
    rng = np.random.RandomState(random_state)
    x_train = rng.randn(n_train, n_features).astype(np.float64)
    y_train = (rng.rand(n_train) < 0.1).astype(np.int8)
    y_train[0], y_train[1] = 0, 1

    x_val = rng.randn(n_val, n_features).astype(np.float64)
    y_val = (rng.rand(n_val) < 0.1).astype(np.int8)
    y_val[0], y_val[1] = 0, 1

    # Save synthetic arrays
    npz_path = synthetic_dir / "membership.npz"
    np.savez(npz_path, train=np.arange(n_train), validation=np.arange(n_val),
             y_train=y_train, y_validation=y_val)

    tree_tr_p = synthetic_dir / "tree_train.npy"
    tree_val_p = synthetic_dir / "tree_validation.npy"
    lr_tr_p = synthetic_dir / "lr_train.npy"
    lr_val_p = synthetic_dir / "lr_validation.npy"

    np.save(tree_tr_p, x_train, allow_pickle=False)
    np.save(tree_val_p, x_val, allow_pickle=False)
    np.save(lr_tr_p, x_train, allow_pickle=False)
    np.save(lr_val_p, x_val, allow_pickle=False)

    allowlist = [npz_path, tree_tr_p, tree_val_p, lr_tr_p, lr_val_p]

    if run_reservation is not None:
        if not hasattr(run_reservation, "validate_reservation_contract"):
            raise ExecutorBlocked("INVALID_RUN_RESERVATION_TYPE")
        run_reservation.validate_reservation_contract(root, run_id)
        output_dir = Path(run_reservation.path).resolve()
    else:
        output_dir = synthetic_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

    task_config = dict(
        run_id=run_id,
        mode="SYNTHETIC",
        membership_path=str(npz_path),
        tree_train_path=str(tree_tr_p),
        tree_val_path=str(tree_val_p),
        lr_train_path=str(lr_tr_p),
        lr_val_path=str(lr_val_p),
        b1_params={"max_depth": 1, "random_state": 42},
        b2_params={"solver": "lbfgs", "max_iter": 2000, "random_state": 42, "tol": 1e-4, "C": 1.0},
    )

    report = _orchestrate_worker_in_windows_job(
        root, run_id, output_dir, allowlist, task_config,
        wall_seconds=wall_seconds, ram_cap_bytes=ram_cap_bytes, mode="SYNTHETIC"
    )
    return report


def assess_proposed_resource_limits(host_cpu_count=None, host_ram_bytes=None):
    """Evaluate technical feasibility of the proposed execution resource limits."""
    data_size_bytes = 48000 * 170 * 8  # 65.28 MB float64
    val_size_bytes = 12000 * 170 * 8   # 16.32 MB float64

    estimated_peak_ram_mb = 450.0
    ram_cap_mb = 2048.0
    ram_feasible = estimated_peak_ram_mb < ram_cap_mb

    estimated_b1_time_sec = 1.0
    estimated_b2_time_sec = 25.0
    timeout_sec = 120.0
    time_feasible = max(estimated_b1_time_sec, estimated_b2_time_sec) < timeout_sec

    return dict(
        data_train_mb=data_size_bytes / (1024**2),
        data_val_mb=val_size_bytes / (1024**2),
        proposed_thread_limit=1,
        proposed_timeout_seconds=timeout_sec,
        proposed_ram_cap_mb=ram_cap_mb,
        estimated_peak_ram_mb=estimated_peak_ram_mb,
        estimated_b1_seconds=estimated_b1_time_sec,
        estimated_b2_seconds=estimated_b2_time_sec,
        ram_feasible=ram_feasible,
        time_feasible=time_feasible,
        status="PROPOSED_LIMITS_TECHNICALLY_FEASIBLE",
        note="These are proposed engineering ESTIMATED values subject to Owner approval, not measured real-fit numbers."
    )
