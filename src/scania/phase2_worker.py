"""Phase 2 Constrained Optimization Worker: isolated subprocess execution under Windows Job Object.

Execution constraints:
- Spawned exclusively under Windows Job Object with strict memory and process limits.
- Prewarming of native environment occurs before numeric imports.
- 1 native compute thread strictly enforced (OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, etc.).
- Allowlist I/O guard strictly enforced inside worker (Official Test sealed until G10).
- Max 20 Optuna trials with exactly 1 real estimator fit per trial.
- Measured timings, RAM telemetry, and trial lifecycle recorded truthfully.
"""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import warnings

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
    for mod in ("numpy", "scipy", "sklearn", "optuna"):
        if mod in sys.modules:
            raise ValueError(f"EARLY_NUMERIC_IMPORT_DETECTED: {mod}")


def execute_worker():
    # Read environment handshake
    run_id = os.environ.get("SC_PHASE2_RUN")
    task_path_str = os.environ.get("SC_PHASE2_TASK_PATH")
    allowlist_path_str = os.environ.get("SC_PHASE2_ALLOWLIST_PATH")
    output_dir_str = os.environ.get("SC_PHASE2_OUTPUT_DIR")
    root_dir_str = os.environ.get("SC_PHASE2_ROOT_DIR")

    if not all([run_id, task_path_str, allowlist_path_str, output_dir_str, root_dir_str]):
        sys.stderr.write("WORKER_HANDSHAKE_MISSING_ENV\n")
        return 101

    output_dir = Path(output_dir_str).resolve()
    root_dir = Path(root_dir_str).resolve()
    task_path = Path(task_path_str).resolve()
    allowlist_path = Path(allowlist_path_str).resolve()

    result_path = output_dir / "worker_result.json"

    fits_count = 0
    attempted_fits = 0
    trials_records = []

    try:
        # 1. Thread env verification
        verify_thread_environment()

        # 2. Early numeric import verification
        verify_no_early_numeric_imports()

        # 3. Native discovery handshake before numeric imports
        from . import g4_env_discovery as _env_disc
        if getattr(_env_disc, "_PREPARED_PID", None) != os.getpid():
            _env_disc.prepare_imports()

        # 4. Safe to import numeric libraries now
        import numpy as np
        import optuna
        from sklearn.ensemble import RandomForestClassifier

        from .g4_b2_executor import install_executor_io_guard
        from .g4_env_discovery import NativeSession
        from .cost_model import binary_vector
        from .phase2_optimization import (
            FitCounter, run_optuna_phase2_trials, sanitize_for_strict_json
        )

        # 5. Read allowlist and install I/O guard
        allowlist = [Path(p).resolve() for p in json.loads(allowlist_path.read_text(encoding="utf-8"))]
        install_executor_io_guard(root_dir, output_dir, allowlist)

        # 6. Read task config
        task_config = json.loads(task_path.read_text(encoding="utf-8"))
        worker_mode = task_config.get("mode", "SYNTHETIC")
        n_trials = int(task_config.get("n_trials", 20))
        max_fits = int(task_config.get("max_fits", 20))
        seed = int(task_config.get("seed", 42))
        capacity_limit = int(task_config.get("capacity_limit", 1200))

        # 7. Initialize NativeSession and verify 1 thread
        session = NativeSession()
        with session:
            pools = session.controller.info()
            for p in pools:
                if p.get("num_threads") != 1:
                    raise ValueError(f"NATIVE_THREAD_NOT_ONE: {p.get('filepath')} has {p.get('num_threads')}")

            # 8. Load data according to mode
            if worker_mode == "REAL":
                cfg_file = root_dir / "configs/scania/phase2_optimization.json"
                if not cfg_file.is_file():
                    raise ValueError("PHASE2_CONFIG_FILE_MISSING")

                # Load labels from membership.npz
                npz_path = Path(task_config["membership_path"]).resolve()
                with np.load(npz_path, allow_pickle=False) as z:
                    y_train_raw = z["y_train"].copy()
                    y_val_raw = z["y_validation"].copy()

                y_train = binary_vector(y_train_raw, "train_labels")
                y_val = binary_vector(y_val_raw, "val_labels")

                # Load tree-processed feature arrays
                tree_train_path = Path(task_config["tree_train_path"]).resolve()
                tree_val_path = Path(task_config["tree_val_path"]).resolve()
                x_train = np.load(tree_train_path, mmap_mode="r", allow_pickle=False)
                x_val = np.load(tree_val_path, mmap_mode="r", allow_pickle=False)

                if x_train.shape != (48000, 170):
                    raise ValueError(f"REAL_TRAIN_SHAPE_MISMATCH: {x_train.shape}, expected (48000, 170)")
                if x_val.shape != (12000, 170):
                    raise ValueError(f"REAL_VAL_SHAPE_MISMATCH: {x_val.shape}, expected (12000, 170)")
            else:
                # Synthetic mode
                n_train = task_config.get("n_train", 200)
                n_val = task_config.get("n_val", 60)
                n_features = task_config.get("n_features", 4)
                rng = np.random.RandomState(seed)
                x_train = rng.randn(n_train, n_features).astype(np.float64)
                y_train = (rng.rand(n_train) < 0.1).astype(np.int8)
                y_train[0], y_train[1] = 0, 1
                x_val = rng.randn(n_val, n_features).astype(np.float64)
                y_val = (rng.rand(n_val) < 0.1).astype(np.int8)
                y_val[0], y_val[1] = 0, 1
                capacity_limit = n_val // 10 if capacity_limit == 1200 else capacity_limit

            # 9. Instantiate FitCounter
            fit_counter = FitCounter(max_fits=max_fits)

            # 10. Run Optuna Phase 2 trials
            t0_optuna = time.perf_counter()
            study, trials_records = run_optuna_phase2_trials(
                x_train, y_train, x_val, y_val,
                fit_counter=fit_counter,
                n_trials=n_trials,
                capacity_limit=capacity_limit,
                seed=seed,
            )
            optuna_wall_sec = time.perf_counter() - t0_optuna
            fits_count = fit_counter.current_fits
            attempted_fits = fit_counter.attempted_fits

            # 11. Find best feasible trial
            feasible_trials = [t for t in trials_records if t["status"] == "FEASIBLE" and t.get("best_policy")]
            if feasible_trials:
                best_trial_rec = min(feasible_trials, key=lambda t: (
                    t["best_policy"]["total_cost"],
                    t["best_policy"]["M"],
                    -t["best_policy"]["threshold"]
                ))
            else:
                best_trial_rec = None

            # 12. Build structured worker result
            worker_result = {
                "status": "PASS",
                "mode": worker_mode,
                "run_id": run_id,
                "total_estimator_fits": fits_count,
                "attempted_fits": attempted_fits,
                "n_trials_completed": len(study.trials),
                "optuna_wall_seconds": optuna_wall_sec,
                "best_trial": sanitize_for_strict_json(best_trial_rec),
                "trials_records": sanitize_for_strict_json(trials_records),
                "fit_records": sanitize_for_strict_json(fit_counter.fit_records),
                "validation_scored": True,
            }

            result_path.write_bytes(json.dumps(worker_result, indent=2).encode("utf-8"))
            return 0

    except Exception as exc:
        err_type = type(exc).__name__
        err_msg = str(exc)
        tb_str = traceback.format_exc()

        failure_record = {
            "status": "FAILED",
            "error_type": err_type,
            "reason": err_msg,
            "traceback": tb_str,
            "total_estimator_fits": fits_count,
            "attempted_fits": attempted_fits,
            "n_trials_completed": len(trials_records),
            "trials_records": sanitize_for_strict_json(trials_records),
            "validation_scored": False,
        }
        try:
            result_path.write_bytes(json.dumps(failure_record, indent=2).encode("utf-8"))
        except Exception:
            pass
        sys.stderr.write(f"WORKER_EXCEPTION: {err_type}: {err_msg}\n")
        return 1


if __name__ == "__main__":
    sys.exit(execute_worker())
