"""SC-G4 Baseline Worker: isolated subprocess execution for B0, B1, and B2 models.

Execution constraints:
- Spawned exclusively under Windows Job Object with strict memory and process limits.
- Prewarming of native environment occurs before numeric imports.
- 1 native compute thread strictly enforced (OMP_NUM_THREADS=1, OPENBLAS_NUM_THREADS=1, etc.).
- Allowlist I/O guard strictly enforced inside worker.
- Train-only fitting for B1 (Decision Stump) and B2 (Logistic Regression); B0 has 0 fits.
- Validation-only scoring across PRIMARY (0.5) and SECONDARY (10/510) fixed policies.
- Measured timings and resource metrics recorded truthfully.
"""
import json
import os
from pathlib import Path
import sys
import time
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
    for mod in ("numpy", "scipy", "sklearn"):
        if mod in sys.modules:
            raise ValueError(f"EARLY_NUMERIC_IMPORT_DETECTED: {mod}")


def execute_worker():
    # Read environment handshake
    run_id = os.environ.get("SC_G4_B2_RUN")
    task_path_str = os.environ.get("SC_G4_B2_TASK_PATH")
    allowlist_path_str = os.environ.get("SC_G4_B2_ALLOWLIST_PATH")
    output_dir_str = os.environ.get("SC_G4_B2_OUTPUT_DIR")
    root_dir_str = os.environ.get("SC_G4_B2_ROOT_DIR")

    if not all([run_id, task_path_str, allowlist_path_str, output_dir_str, root_dir_str]):
        sys.stderr.write("WORKER_HANDSHAKE_MISSING_ENV\n")
        return 101

    output_dir = Path(output_dir_str).resolve()
    root_dir = Path(root_dir_str).resolve()
    task_path = Path(task_path_str).resolve()
    allowlist_path = Path(allowlist_path_str).resolve()

    result_path = output_dir / "worker_result.json"

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
        from sklearn.tree import DecisionTreeClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.exceptions import ConvergenceWarning

        from .g4_b2_executor import install_executor_io_guard
        from .g4_env_discovery import NativeSession
        from .constraints import PRIMARY, SECONDARY, POLICIES, actions_from_probabilities, capacity_report, probabilities
        from .cost_model import binary_vector
        from .evaluation import evaluate_aps_policy

        # 5. Read allowlist and install I/O guard
        allowlist = [Path(p).resolve() for p in json.loads(allowlist_path.read_text(encoding="utf-8"))]
        install_executor_io_guard(root_dir, output_dir, allowlist)

        # 6. Read task config
        task_config = json.loads(task_path.read_text(encoding="utf-8"))

        # 7. Initialize NativeSession and verify 1 thread
        session = NativeSession()
        with session:
            pools = session.controller.info()
            for p in pools:
                if p.get("num_threads") != 1:
                    raise ValueError(f"NATIVE_THREAD_NOT_ONE: {p.get('filepath')} has {p.get('num_threads')}")

            # 8. Load labels from membership.npz
            npz_path = Path(task_config["membership_path"]).resolve()
            with np.load(npz_path, allow_pickle=False) as z:
                y_train_raw = z["y_train"].copy()
                y_val_raw = z["y_validation"].copy()

            y_train = binary_vector(y_train_raw, "train_labels")
            y_val = binary_vector(y_val_raw, "val_labels")

            n_train = len(y_train)
            n_val = len(y_val)
            p_val = int(np.sum(y_val == 1))

            all_rows = []
            telemetry = {}
            fits_count = 0

            # --- Model B0: Majority Dummy (0 fits, fixed rule) ---
            t0_b0 = time.perf_counter()
            actions_b0 = np.zeros(n_val, dtype=np.int8)
            row_b0 = evaluate_aps_policy(y_val, actions_b0, scores=None, baseline_id="B0", role="REFERENCE")
            all_rows.append(row_b0)
            telemetry["B0"] = dict(
                baseline_id="B0",
                fit_seconds=0.0,
                predict_seconds=time.perf_counter() - t0_b0,
                warnings=[],
                parameters=None,
                classes=[0],
                real_estimator_fits=0,
                validation_scored=True,
            )

            # --- Model B1: Decision Stump (max_depth=1) ---
            tree_train_path = Path(task_config["tree_train_path"]).resolve()
            tree_val_path = Path(task_config["tree_val_path"]).resolve()
            x_tree_train = np.load(tree_train_path, mmap_mode="r", allow_pickle=False)
            x_tree_val = np.load(tree_val_path, mmap_mode="r", allow_pickle=False)

            if x_tree_train.shape[0] != n_train or x_tree_val.shape[0] != n_val:
                raise ValueError("B1_INPUT_SHAPE_MISMATCH")

            b1_params = task_config.get("b1_params", {"max_depth": 1, "random_state": 42})
            model_b1 = DecisionTreeClassifier(**b1_params)

            t0_b1_fit = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught_b1:
                warnings.simplefilter("always")
                model_b1.fit(x_tree_train, y_train)
            b1_fit_sec = time.perf_counter() - t0_b1_fit
            fits_count += 1

            t0_b1_pred = time.perf_counter()
            proba_b1 = np.asarray(model_b1.predict_proba(x_tree_val))
            b1_pred_sec = time.perf_counter() - t0_b1_pred

            if proba_b1.shape != (n_val, 2) or not np.isfinite(proba_b1).all():
                raise ValueError("B1_PROBABILITY_INVALID")
            scores_b1 = probabilities(proba_b1[:, 1])

            for role, tau in POLICIES.items():
                acts = actions_from_probabilities(scores_b1, tau)
                row = evaluate_aps_policy(y_val, acts, scores_b1, baseline_id="B1", role=role, threshold=tau)
                all_rows.append(row)

            telemetry["B1"] = dict(
                baseline_id="B1",
                fit_seconds=b1_fit_sec,
                predict_seconds=b1_pred_sec,
                warnings=[str(w.message) for w in caught_b1],
                parameters=model_b1.get_params(deep=False),
                classes=[int(c) for c in model_b1.classes_],
                real_estimator_fits=1,
                validation_scored=True,
            )

            # --- Model B2: Logistic Regression (max_iter=2000, lbfgs) ---
            lr_train_path = Path(task_config["lr_train_path"]).resolve()
            lr_val_path = Path(task_config["lr_val_path"]).resolve()
            x_lr_train = np.load(lr_train_path, mmap_mode="r", allow_pickle=False)
            x_lr_val = np.load(lr_val_path, mmap_mode="r", allow_pickle=False)

            if x_lr_train.shape[0] != n_train or x_lr_val.shape[0] != n_val:
                raise ValueError("B2_INPUT_SHAPE_MISMATCH")

            b2_params = task_config.get("b2_params", {
                "solver": "lbfgs",
                "max_iter": 2000,
                "random_state": 42,
                "tol": 1e-4,
                "C": 1.0,
            })
            model_b2 = LogisticRegression(**b2_params)

            t0_b2_fit = time.perf_counter()
            with warnings.catch_warnings(record=True) as caught_b2:
                warnings.simplefilter("always")
                model_b2.fit(x_lr_train, y_train)
            b2_fit_sec = time.perf_counter() - t0_b2_fit
            fits_count += 1

            conv_w = [w for w in caught_b2 if issubclass(w.category, ConvergenceWarning)]
            if conv_w:
                raise ValueError(f"B2_CONVERGENCE_FAILURE: {conv_w[0].message}")

            t0_b2_pred = time.perf_counter()
            proba_b2 = np.asarray(model_b2.predict_proba(x_lr_val))
            b2_pred_sec = time.perf_counter() - t0_b2_pred

            if proba_b2.shape != (n_val, 2) or not np.isfinite(proba_b2).all():
                raise ValueError("B2_PROBABILITY_INVALID")
            scores_b2 = probabilities(proba_b2[:, 1])

            for role, tau in POLICIES.items():
                acts = actions_from_probabilities(scores_b2, tau)
                row = evaluate_aps_policy(y_val, acts, scores_b2, baseline_id="B2", role=role, threshold=tau)
                all_rows.append(row)

            telemetry["B2"] = dict(
                baseline_id="B2",
                fit_seconds=b2_fit_sec,
                predict_seconds=b2_pred_sec,
                warnings=[str(w.message) for w in caught_b2],
                parameters=model_b2.get_params(deep=False),
                classes=[int(c) for c in model_b2.classes_],
                real_estimator_fits=1,
                validation_scored=True,
            )

        # Successful completion evidence
        worker_output = dict(
            status="PASS",
            run_id=run_id,
            total_estimator_fits=fits_count,
            validation_scored=True,
            rows=all_rows,
            telemetry=telemetry,
            observed_timings=dict(
                b0_predict_seconds=telemetry["B0"]["predict_seconds"],
                b1_fit_seconds=b1_fit_sec,
                b1_predict_seconds=b1_pred_sec,
                b2_fit_seconds=b2_fit_sec,
                b2_predict_seconds=b2_pred_sec,
                total_fit_seconds=b1_fit_sec + b2_fit_sec,
            ),
        )
        result_path.write_text(json.dumps(worker_output, indent=2), encoding="utf-8")
        return 0

    except Exception as exc:
        failure_output = dict(
            status="FAILED",
            run_id=run_id,
            error_type=type(exc).__name__,
            reason=str(exc),
            total_estimator_fits=locals().get("fits_count", 0),
            validation_scored=False,
        )
        try:
            result_path.write_text(json.dumps(failure_output, indent=2), encoding="utf-8")
        except Exception:
            pass
        sys.stderr.write(f"WORKER_ERROR: {type(exc).__name__}: {exc}\n")
        return 1


if __name__ == "__main__":
    sys.exit(execute_worker())
