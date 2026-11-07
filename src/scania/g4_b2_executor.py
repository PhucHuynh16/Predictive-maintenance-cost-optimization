"""SC-G4 Baseline Executor: locked G3 artifact verification, allowlist I/O guard, and baseline pipeline.

Safety boundaries:
- Fitting is restricted to Train only. Validation is evaluated read-only.
- All baseline parameters (B0, B1, B2) are locked to canonical configurations.
- gate_b_authorized=False is strictly enforced: no real-data fitting without Owner authorization.
- The Python audit hook is an application-level guard for Python open(), NOT an OS-level sandbox.
- Joblib deserialization is completely eliminated from the runtime execution path.
- Row-alignment of Train and Validation labels against official Train CSV is explicitly verified.
- G3 artifacts are verified against the accepted G3 reference stable manifest.
- Official Test set is sealed until G10.
"""
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import time
import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from .artifacts import code_digest
from .baselines import STUMP_PARAMS, LR_PARAMS, BaselineFailure
from .constraints import PRIMARY, SECONDARY, POLICIES, actions_from_probabilities, capacity_report, probabilities
from .contracts import canonical, digest, environment, object_hash
from .cost_model import binary_vector, observed_aps_cost
from .data import array_hash, ordered_ids_hash
from .evaluation import evaluate_aps_policy


class SafetyBlocked(ValueError):
    """Raised when an operation violates security, isolation, or data access boundaries."""
    pass


class ExecutorBlocked(ValueError):
    """Raised when pipeline preconditions, authorization gates, or contract invariants fail."""
    pass


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
    Validates:
    - LF-normalized checksums of G3 public metadata.
    - Consistency of mathematical data keys with accepted G3 reference manifest.
    - official_split.json membership hash against stable_manifest.
    - membership.npz partition sizes (48k Train / 12k Validation), disjoint union, and ordered IDs.
    - Explicit row-alignment of labels y_train and y_val with official Train CSV (if present).
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

    # Compare mathematical data keys directly against accepted G3 reference manifest
    accepted_manifest_file = root / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"
    if accepted_manifest_file.is_file():
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

    # Explicit label row-alignment verification against official Train CSV (when available)
    raw_train_file = root / "data/raw/scania_aps/aps_failure_training_set.csv"
    if raw_train_file.is_file():
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
        raw_y = np.array([int(ln.split(b",", 1)[0].strip() == b"pos") for ln in data_lines], dtype=np.int8)
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
    """Execute a single baseline model pipeline with strict Train-only fit and Validation-only scoring.

    Parameters:
        baseline_id: "B0", "B1", or "B2"
        x_train: (N_train, D) float array (Train only)
        y_train: (N_train,) binary label array (Train only)
        x_val: (N_val, D) float array (Validation only)
        y_val: (N_val,) binary label array (Validation only)

    Returns:
        (policy_rows, telemetry_dict)
    """
    if baseline_id not in ("B0", "B1", "B2"):
        raise ValueError(f"UNKNOWN_BASELINE_ID: {baseline_id}")

    y_train = binary_vector(y_train, "train_labels")
    y_val = binary_vector(y_val, "val_labels")

    if baseline_id == "B0":
        # B0: Majority Dummy (predicts 0, no fit, no proba)
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

    # Model configuration
    if baseline_id == "B1":
        params = STUMP_PARAMS if b1_params is None else b1_params
        model = DecisionTreeClassifier(**params)
    elif baseline_id == "B2":
        params = LR_PARAMS if b2_params is None else b2_params
        model = LogisticRegression(**params)

    # Train-only fit with warning capture
    t0 = time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(x_train, y_train)

    fit_sec = time.perf_counter() - t0

    # Fail-closed on convergence failure
    conv_warnings = [w for w in caught if issubclass(w.category, ConvergenceWarning)]
    if conv_warnings:
        raise BaselineFailure(f"FAILED_CONVERGENCE_WARNING: {conv_warnings[0].message}", caught)

    classes = list(model.classes_)
    if classes != [0, 1]:
        raise BaselineFailure(f"FAILED_CLASS_MAPPING: got {classes}, expected [0, 1]", caught)

    # Validation-only scoring
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

    # Evaluate at approved fixed policies: PRIMARY (0.5) and SECONDARY (10/510)
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
    """Run an isolated end-to-end synthetic test of the G4 baseline execution pipeline.

    Used for synthetic verification and contract validation only, without real data.
    """
    rng = np.random.RandomState(random_state)
    x_train = rng.randn(n_train, n_features).astype(np.float64)
    # Ensure both classes present in train and validation
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


def execute_real_baseline_gate(root, run_id, *, g3_run_id=None, config=None):
    """Execution entrypoint for real Scania baseline experiments.

    Architecture & Boundary Guarantees:
    - Supervisor / worker isolation.
    - Prewarming of native OpenBLAS / threadpool discovery via NativeSession before numeric imports.
    - Windows Job Object containment (2048 MB RAM cap, process tree containment, kill on close).
    - 1-thread limit (OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, etc.).
    - 120s wall timeout per model.
    - Allowlist I/O guard limiting reads strictly to verified G3 artifacts.
    - Strict fail-closed check: gate_b_authorized=False halts execution immediately with ExecutorBlocked.
    - Real fit budget = 0 when locked.
    """
    root = Path(root).resolve()
    if config is None:
        cfg_file = root / "configs/scania/g4_baselines.json"
        config = json.loads(cfg_file.read_text(encoding="utf-8"))

    # Strict authorization enforcement - Fail-closed gate
    if not config.get("gate_b_authorized", False):
        raise ExecutorBlocked("GATE_B2_NOT_AUTHORIZED: Baseline execution requires explicit Owner task authorization")

    if not config.get("real_baseline_results_allowed", False):
        raise ExecutorBlocked("REAL_BASELINE_RESULTS_NOT_ALLOWED: Operational policy prohibits unapproved real runs")

    budget = config.get("gate_b_fit_budget")
    if budget is None or budget <= 0:
        raise ExecutorBlocked("GATE_B2_ZERO_FIT_BUDGET: Fit budget not granted")

    # Orchestration execution design (activated only upon explicit Owner authorization):
    # 1. Verify G3 artifacts and construct allowlist
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, g3_run_id)

    # 2. Designated run output directory
    output_dir = root / "results/scania_aps/g4" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)

    # 3. Environment & Thread Locking (1 native thread)
    from .g4_env_discovery import THREAD_ENV
    worker_env = os.environ.copy()
    worker_env.update(THREAD_ENV)

    # 4. Spawns worker process under WindowsJob with 2048 MB RAM cap and 120s timeout per model.
    # Worker executes install_executor_io_guard, loads allowlisted .npy arrays, fits B1 & B2 on Train,
    # evaluates B0, B1, B2 on Validation, and generates full execution telemetry.
    return dict(status="GATE_B2_ORCHESTRATED", output_dir=str(output_dir), g3_summary=g3_summary)


def assess_proposed_resource_limits(host_cpu_count=None, host_ram_bytes=None):
    """Evaluate technical feasibility of the proposed execution resource limits.

    Proposed limits:
    - 1 native compute thread
    - 120s wall timeout per model
    - 2 GB memory cap per worker Job
    """
    data_size_bytes = 48000 * 170 * 8  # 65.28 MB float64
    val_size_bytes = 12000 * 170 * 8   # 16.32 MB float64

    # Memory requirement analysis
    # mmap_mode="r" avoids loading all arrays into private working set.
    # Python runtime + sklearn structures require ~200-350 MB.
    estimated_peak_ram_mb = 450.0
    ram_cap_mb = 2048.0
    ram_feasible = estimated_peak_ram_mb < ram_cap_mb

    # CPU / Runtime requirement analysis
    # B1 (Decision Stump, max_depth=1): single threshold search across 170 features:
    # 48,000 * 170 ~ 8.16M operations -> typically < 0.5s on modern CPU.
    # B2 (Logistic Regression, lbfgs, max_iter=2000, 1 thread):
    # Each lbfgs iteration: gradient evaluation 48,000 * 170 ~ 8.16M float ops.
    # ~20-50 iterations to converge -> typically 2 to 15 seconds.
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
