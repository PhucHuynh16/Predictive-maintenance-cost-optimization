"""Scania APS Gate G10 Worker: isolated subprocess execution under Windows Job Object.

Execution invariants:
- Spawned exclusively under Windows Job Object with strict memory and process limits.
- Prewarming of native environment occurs before numeric imports.
- 1 native compute thread strictly enforced (OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, etc.).
- Allowlist I/O guard strictly enforced inside worker.
- Exactly 1 deterministic refit on Train partition (48,000 samples).
- Durable fit accounting: records atomic STARTED marker before model.fit() executes.
- Validation regression guard: reproduces exact Trial 16 validation metrics
  (TP=195, FP=383, FN=5, TN=11417, Cost=6330, M=578) before touching Official Test.
- Official Test set (16,000 samples): single-pass read-only, transformed with frozen preprocessor.
- Fail-closed: Stop without retry on timeout or failure.
"""
import csv
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback
import zipfile
from typing import Any, Dict, List, Optional, Tuple

# Step 1: Thread environment verification before any numeric library is imported
THREAD_ENV_KEYS = (
    "OMP_NUM_THREADS",
    "OMP_THREAD_LIMIT",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def verify_thread_environment():
    for k in THREAD_ENV_KEYS:
        val = os.environ.get(k)
        if val != "1":
            raise ValueError(f"THREAD_ENV_VIOLATION: {k}={val}, expected '1'")
    if os.environ.get("OMP_DYNAMIC") != "FALSE":
        raise ValueError("THREAD_ENV_VIOLATION: OMP_DYNAMIC must be 'FALSE'")
    if os.environ.get("MKL_DYNAMIC") != "FALSE":
        raise ValueError("THREAD_ENV_VIOLATION: MKL_DYNAMIC must be 'FALSE'")


def verify_no_early_numeric_imports():
    for mod in ("numpy", "scipy", "sklearn"):
        if mod in sys.modules:
            raise ValueError(f"EARLY_NUMERIC_IMPORT_DETECTED: {mod}")


def sanitize_for_strict_json(obj: Any) -> Any:
    """Recursively convert NumPy numbers and non-finite floats to JSON-safe primitives."""
    import numpy as np

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
    test_csv_filename: str,
    expected_rows: int,
    features: Tuple[str, ...],
) -> Tuple[Any, Any]:
    """Strictly read and parse Official Test CSV from zip archive in-memory."""
    import hashlib
    import numpy as np

    zip_path = Path(zip_path).resolve()
    if not zip_path.is_file():
        raise ValueError(f"RAW_ZIP_MISSING: {zip_path}")

    zip_bytes = zip_path.read_bytes()
    actual_zip_sha = hashlib.sha256(zip_bytes).hexdigest()
    if actual_zip_sha != expected_sha256:
        raise ValueError(
            f"RAW_ZIP_CHECKSUM_MISMATCH: expected {expected_sha256}, got {actual_zip_sha}"
        )

    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as z:
        if test_csv_filename not in z.namelist():
            raise ValueError(f"TEST_CSV_NOT_FOUND_IN_ZIP: {test_csv_filename}")
        with z.open(test_csv_filename, "r") as f:
            content_bytes = f.read()

    lines = content_bytes.decode("utf-8", errors="strict").splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        tokens = tuple(t.strip() for t in line.split(","))
        if "class" in tokens:
            if tokens != ("class", *features):
                raise ValueError("TEST_SCHEMA_MISMATCH: header does not match ordered features")
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("TEST_HEADER_NOT_FOUND")

    data_lines = lines[header_idx + 1 :]
    if len(data_lines) != expected_rows:
        raise ValueError(
            f"TEST_ROW_COUNT_MISMATCH: expected {expected_rows}, got {len(data_lines)}"
        )

    n_features = len(features)
    X = np.full((expected_rows, n_features), np.nan, dtype=np.float64)
    y = np.empty(expected_rows, dtype=np.int8)

    number_regex = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")

    for r, line in enumerate(data_lines):
        tokens = [t.strip() for t in line.split(",")]
        if len(tokens) != n_features + 1:
            raise ValueError(f"TEST_ROW_WIDTH_MISMATCH: row {r + 1}")
        target = tokens[0]
        if target not in ("neg", "pos"):
            raise ValueError(f"INVALID_TARGET: row {r + 1}: '{target}'")
        y[r] = 1 if target == "pos" else 0

        for c, tok in enumerate(tokens[1:]):
            if tok == "na" or not tok:
                continue
            if not number_regex.fullmatch(tok):
                raise ValueError(f"INVALID_NUMERIC_TOKEN: row {r + 1}, col {c + 1}: '{tok}'")
            val = float(tok)
            if not np.isfinite(val):
                raise ValueError(f"NON_FINITE_FLOAT: row {r + 1}, col {c + 1}")
            X[r, c] = 0.0 if val == 0 else val

    return X, y


def evaluate_policy_predictions(
    y_true: Any,
    probabilities: Any,
    threshold: float,
    capacity_limit_K: int,
    cost_fp: int = 10,
    cost_fn: int = 500,
) -> Dict[str, Any]:
    """Compute confusion matrix, cost, capacity, and academic metrics for frozen policy."""
    import numpy as np
    from sklearn.metrics import average_precision_score, roc_auc_score

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


def execute_worker() -> int:
    # 1. Read environment handshake
    run_id = os.environ.get("SC_G10_RUN")
    task_path_str = os.environ.get("SC_G10_TASK_PATH")
    allowlist_path_str = os.environ.get("SC_G10_ALLOWLIST_PATH")
    output_dir_str = os.environ.get("SC_G10_OUTPUT_DIR")
    root_dir_str = os.environ.get("SC_G10_ROOT_DIR")

    if not all([run_id, task_path_str, allowlist_path_str, output_dir_str, root_dir_str]):
        sys.stderr.write("G10_WORKER_HANDSHAKE_MISSING_ENV\n")
        return 101

    output_dir = Path(output_dir_str).resolve()
    root_dir = Path(root_dir_str).resolve()
    task_path = Path(task_path_str).resolve()
    allowlist_path = Path(allowlist_path_str).resolve()

    result_path = output_dir / "worker_result.json"
    durable_dir = output_dir / "durable_fits"
    durable_dir.mkdir(parents=True, exist_ok=True)

    t0_worker = time.time()

    try:
        # Step 2: Thread env verification
        verify_thread_environment()

        # Step 3: Early numeric import verification
        verify_no_early_numeric_imports()

        # Step 4: Native discovery handshake before numeric imports
        from . import g4_env_discovery as _env_disc

        if getattr(_env_disc, "_PREPARED_PID", None) != os.getpid():
            _env_disc.prepare_imports()

        # Step 5: Safe to import numeric libraries now
        import hashlib
        import numpy as np
        from sklearn.ensemble import RandomForestClassifier
        import joblib

        from .contracts import FEATURES, digest
        from .g10_evaluation import install_g10_io_guard
        from .g4_env_discovery import NativeSession

        # Step 6: Read task config
        task_config = json.loads(task_path.read_text(encoding="utf-8"))
        mode = task_config.get("mode", "REAL")
        frozen_rf_params = task_config["frozen_rf_params"]
        frozen_threshold = float(task_config["frozen_threshold"])
        capacity_limit_K = int(task_config["capacity_limit_K"])
        cost_fp = int(task_config["cost_fp"])
        cost_fn = int(task_config["cost_fn"])

        # Step 7: Read allowlist and install G10 I/O guard
        allowlist = [Path(p).resolve() for p in json.loads(allowlist_path.read_text(encoding="utf-8"))]
        install_g10_io_guard(root_dir, output_dir, allowlist, mode=mode)

        # Step 8: Verify NativeSession 1 thread
        session = NativeSession()
        with session:
            pools = session.controller.info()
            for p in pools:
                if p.get("num_threads") != 1:
                    raise ValueError(f"NATIVE_THREAD_NOT_ONE: {p.get('filepath')} has {p.get('num_threads')}")

            # Step 9: Load Train and Validation data
            train_x_path = root_dir / task_config["train_processed_path"]
            membership_path = root_dir / task_config["membership_path"]
            val_x_path = root_dir / task_config["validation_processed_path"]

            X_train = np.load(train_x_path)
            membership = np.load(membership_path)
            y_train = membership["y_train"]
            X_val = np.load(val_x_path)
            y_val = membership["y_validation"]

            if len(y_train) != 48000 or len(y_val) != 12000:
                raise ValueError(f"SPLIT_SIZE_MISMATCH: train={len(y_train)}, val={len(y_val)}")

            # Step 10: Exactly 1 Deterministic Train Refit
            fit_marker_start = {
                "fit_index": 1,
                "trial_id": "g10_refit_001",
                "status": "STARTED",
                "timestamp_start": time.time(),
                "model_type": "RandomForestClassifier",
                "hyperparameters": frozen_rf_params,
                "train_samples": len(y_train),
            }
            # Fail closed BEFORE model.fit() if start marker cannot be written
            write_durable_marker(durable_dir, "fit_001_STARTED.json", fit_marker_start)

            t_fit_0 = time.perf_counter()
            model = RandomForestClassifier(**frozen_rf_params)
            model.fit(X_train, y_train)
            fit_duration = time.perf_counter() - t_fit_0

            fit_marker_completed = {
                "fit_index": 1,
                "trial_id": "g10_refit_001",
                "status": "COMPLETED",
                "timestamp_completed": time.time(),
                "fit_duration_seconds": fit_duration,
                "train_samples": len(y_train),
            }
            write_durable_marker(durable_dir, "fit_001_COMPLETED.json", fit_marker_completed)

            # Step 11: Validation Regression Guard
            val_probs = model.predict_proba(X_val)[:, 1]
            val_metrics = evaluate_policy_predictions(
                y_val,
                val_probs,
                threshold=frozen_threshold,
                capacity_limit_K=1200,  # 10% of 12,000 validation
                cost_fp=cost_fp,
                cost_fn=cost_fn,
            )

            # Verify exact bit-level reproduction of Phase 2 Trial 16 targets
            validation_expected = {
                "TP": 195,
                "FP": 383,
                "FN": 5,
                "TN": 11417,
                "total_cost": 6330,
                "M": 578,
            }
            mismatches = []
            for k, exp_val in validation_expected.items():
                act_val = val_metrics.get(k)
                if act_val != exp_val:
                    mismatches.append(f"{k}: expected {exp_val}, got {act_val}")

            if mismatches:
                raise ValueError(
                    f"VALIDATION_REGRESSION_MISMATCH: Trained model deviates from Phase 2 Trial 16: {', '.join(mismatches)}"
                )

            # Save validation guard metrics
            (output_dir / "validation_guard_metrics.json").write_text(
                json.dumps(sanitize_for_strict_json(val_metrics), indent=2), encoding="utf-8"
            )

            # Step 12: Test Ingestion & Transformation
            if mode == "REAL":
                raw_zip_path = root_dir / task_config["raw_zip_path"]
                expected_zip_sha = task_config["raw_zip_sha256"]
                test_csv_filename = task_config["test_filename_in_zip"]
                expected_rows = int(task_config["expected_test_rows"])

                X_test_raw, y_test = parse_official_test_set_from_zip(
                    raw_zip_path,
                    expected_zip_sha,
                    test_csv_filename,
                    expected_rows,
                    tuple(FEATURES),
                )

                preproc_path = root_dir / task_config["preprocessor_path"]
                preprocessor = joblib.load(preproc_path)
                X_test_transformed = preprocessor.transform(X_test_raw)
            else:
                # Synthetic mode
                synth_data = task_config.get("synthetic_test_data")
                if synth_data:
                    X_test_transformed = np.array(synth_data["X"])
                    y_test = np.array(synth_data["y"])
                else:
                    np.random.seed(42)
                    n_synth = 500
                    X_test_transformed = np.random.randn(n_synth, 170)
                    y_test = np.random.choice([0, 1], size=n_synth, p=[0.97, 0.03])

            # Step 13: Single-Pass Test Evaluation (Zero tuning on Test)
            t_eval_0 = time.perf_counter()
            test_probs = model.predict_proba(X_test_transformed)[:, 1]
            predict_seconds = time.perf_counter() - t_eval_0

            test_metrics = evaluate_policy_predictions(
                y_test,
                test_probs,
                threshold=frozen_threshold,
                capacity_limit_K=capacity_limit_K,
                cost_fp=cost_fp,
                cost_fn=cost_fn,
            )
            test_metrics["predict_seconds"] = predict_seconds

            # Step 14: Evidence Persistence
            # 1. test_metrics.json
            (output_dir / "test_metrics.json").write_text(
                json.dumps(sanitize_for_strict_json(test_metrics), indent=2), encoding="utf-8"
            )

            # 2. confusion_matrix_test.csv
            cm_path = output_dir / "confusion_matrix_test.csv"
            with open(cm_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["actual", "pred_neg", "pred_pos", "total"])
                writer.writerow(["neg", test_metrics["TN"], test_metrics["FP"], test_metrics["TN"] + test_metrics["FP"]])
                writer.writerow(["pos", test_metrics["FN"], test_metrics["TP"], test_metrics["FN"] + test_metrics["TP"]])
                writer.writerow(["total", test_metrics["TN"] + test_metrics["FN"], test_metrics["M"], test_metrics["N"]])

            # 3. best_policy.json
            policy_doc = {
                "gate": "G10_FINAL_OFFICIAL_TEST_EVALUATION",
                "run_id": run_id,
                "evaluation_mode": "DETERMINISTIC_TRAIN_REFIT_EVALUATION",
                "source_policy": {
                    "source_run": "scania_phase2_rf_optuna_002",
                    "selected_trial": 16,
                    "estimator": "RandomForestClassifier",
                    "hyperparameters": frozen_rf_params,
                    "frozen_threshold": frozen_threshold,
                },
                "validation_guard": {
                    "status": "PASSED_EXACT_REPRODUCTION",
                    "metrics": val_metrics,
                },
                "official_test_results": test_metrics,
                "execution_telemetry": {
                    "fit_duration_seconds": fit_duration,
                    "predict_seconds": predict_seconds,
                    "total_wall_seconds": time.time() - t0_worker,
                },
            }
            (output_dir / "best_policy.json").write_text(
                json.dumps(sanitize_for_strict_json(policy_doc), indent=2), encoding="utf-8"
            )

            # 4. run_summary.json
            run_summary = {
                "run_id": run_id,
                "gate": "G10",
                "mode": mode,
                "status": "COMPLETED_SUCCESSFULLY",
                "evaluation_mode": "DETERMINISTIC_TRAIN_REFIT_EVALUATION",
                "fits_consumed": 1,
                "validation_guard": "PASSED",
                "official_test_metrics": {
                    "TP": test_metrics["TP"],
                    "FP": test_metrics["FP"],
                    "FN": test_metrics["FN"],
                    "TN": test_metrics["TN"],
                    "total_cost": test_metrics["total_cost"],
                    "capacity_M": test_metrics["M"],
                    "capacity_limit_K": test_metrics["K"],
                    "feasible": test_metrics["feasible"],
                    "saving_pct": test_metrics["saving_pct"],
                    "precision": test_metrics["precision"],
                    "recall": test_metrics["recall"],
                    "f1": test_metrics["f1"],
                    "roc_auc": test_metrics["roc_auc"],
                    "pr_auc": test_metrics["pr_auc"],
                },
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            (output_dir / "run_summary.json").write_text(
                json.dumps(sanitize_for_strict_json(run_summary), indent=2), encoding="utf-8"
            )

            # 5. stable_manifest.json
            manifest: Dict[str, str] = {}
            for p in sorted(output_dir.glob("*")):
                if p.is_file() and p.name != "worker_result.json":
                    manifest[p.name] = digest(p.read_bytes().replace(b"\r\n", b"\n"))
            for p in sorted(durable_dir.glob("*.json")):
                if p.is_file():
                    manifest[f"durable_fits/{p.name}"] = digest(p.read_bytes().replace(b"\r\n", b"\n"))

            (output_dir / "stable_manifest.json").write_text(
                json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
            )

            # Step 15: Worker Result Success
            worker_result = {
                "status": "PASS",
                "run_id": run_id,
                "fits_consumed": 1,
                "total_wall_seconds": time.time() - t0_worker,
                "summary": run_summary,
            }
            result_path.write_text(
                json.dumps(sanitize_for_strict_json(worker_result), indent=2), encoding="utf-8"
            )
            return 0

    except Exception as exc:
        tb = traceback.format_exc()
        sys.stderr.write(f"G10_WORKER_ERROR: {exc}\n{tb}\n")

        failure_diag = {
            "status": "FAILED",
            "error": str(exc),
            "traceback": tb,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_wall_seconds": time.time() - t0_worker,
        }
        try:
            (output_dir / "failure_diagnostics.json").write_text(
                json.dumps(failure_diag, indent=2), encoding="utf-8"
            )
            worker_result = {
                "status": "FAILED",
                "reason": str(exc),
                "traceback": tb,
                "total_wall_seconds": time.time() - t0_worker,
            }
            result_path.write_text(
                json.dumps(worker_result, indent=2), encoding="utf-8"
            )
        except Exception:
            pass
        return 1


def main():
    try:
        rc = execute_worker()
        sys.exit(rc)
    except Exception as exc:
        sys.stderr.write(f"UNHANDLED_WORKER_EXCEPTION: {exc}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
