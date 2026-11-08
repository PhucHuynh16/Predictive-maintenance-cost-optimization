"""Phase 2 Constrained Optimization: Random Forest + Optuna TPE with P02 Threshold Contract.

Mathematical formulation:
    min_{theta in Theta, tau in [0, 1]}  f(theta, tau) = 10 * FP(theta, tau) + 500 * FN(theta, tau)
    subject to                          M(theta, tau) = TP + FP <= K = floor(N_val / 10) = 1200

Constraints & Contracts:
- Estimator: RandomForestClassifier(class_weight='balanced', random_state=42, n_jobs=1, bootstrap=True).
- Search space:
    * n_estimators: int in [20, 60], step 10
    * max_depth: int in [4, 12]
    * min_samples_split: int in [2, 10]
    * max_features: float in [0.2, 0.5]
- Optimizer: Optuna TPESampler(seed=42), sequential single-thread execution.
- Budget: Exactly 20 trials, max 1 fit per trial, max 20 fits total.
- Threshold contract: P02 (actions = probability >= tau, exact ties preserved).
- Threshold selection: evaluate all unique candidates in [0, 1] without refitting.
  Tie-breaking: (total_cost, M, -threshold).
- Fit accounting: reserve and durable start record BEFORE model.fit().
  Distinguish attempted, started, completed, and failed fits.
- Data scope: Train (48,000) and Validation (12,000). Official Test SEALED UNTIL G10.
- Strict JSON compliance: No NaN, Inf, or -Inf serialized.
"""
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple
import warnings

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import average_precision_score, roc_auc_score

from .cost_model import binary_vector
from .constraints import capacity_report, probabilities


class FitBudgetExceeded(RuntimeError):
    """Raised when an attempt is made to execute more fits than authorized."""
    pass


class OptimizationError(RuntimeError):
    """Raised when an optimization invariant or data contract is violated."""
    pass


class DurableLoggingError(RuntimeError):
    """Raised when writing or syncing a durable fit marker to disk fails."""
    pass


def write_durable_marker(directory: Path, filename: str, data: Dict[str, Any]) -> Path:
    """Atomically and durably write JSON marker to disk with flush and sync.

    Fail-closed: raises DurableLoggingError if write or sync fails.
    """
    directory = Path(directory)
    if not directory.is_dir():
        directory.mkdir(parents=True, exist_ok=True)

    target_path = directory / filename
    temp_path = directory / f".tmp_{secrets.token_hex(8)}_{filename}"
    payload = json.dumps(data, indent=2).encode("utf-8")

    try:
        with open(temp_path, "wb") as f:
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        temp_path.replace(target_path)
    except Exception as exc:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise DurableLoggingError(
            f"DURABLE_MARKER_WRITE_FAILED: Failed to write {filename}: {exc}"
        ) from exc
    return target_path


@dataclass
class FitCounter:
    """Atomic counter for model.fit() invocations with strict state tracking and durability."""
    max_fits: int
    attempted_fits: int = 0
    started_fits: int = 0
    completed_fits: int = 0
    failed_fits: int = 0
    interrupted_fits: int = 0
    durable_dir: Optional[Path] = None
    fit_records: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def current_fits(self) -> int:
        """Alias for completed_fits for backward compatibility."""
        return self.completed_fits

    def reserve_and_start_fit(
        self, estimator_name: str, params: Dict[str, Any], trial_number: Optional[int] = None
    ) -> int:
        """Reserve and record an attempted/started fit BEFORE invoking model.fit().

        Enforces:
        - If started_fits >= max_fits: raises FitBudgetExceeded immediately.
        - Increments attempted_fits.
        - Persists a durable start record to disk with atomic replacement and fsync.
        - If durable start record cannot be written, FAILS CLOSED before model.fit() can run.
        - Increments started_fits only upon successful reservation and persistence.
        """
        self.attempted_fits += 1
        if self.started_fits >= self.max_fits:
            raise FitBudgetExceeded(
                f"MAX_REAL_FITS_EXCEEDED: Cannot start fit {self.started_fits + 1}; authorized budget is {self.max_fits}"
            )
        candidate_fit_index = self.started_fits + 1

        record = {
            "fit_index": candidate_fit_index,
            "trial_number": trial_number,
            "estimator": estimator_name,
            "params": params,
            "status": "STARTED",
            "start_time": time.time(),
            "end_time": None,
            "fit_seconds": None,
            "error": None,
        }

        # FAIL-CLOSED: Persist fit STARTED marker BEFORE incrementing started_fits or returning
        if self.durable_dir:
            try:
                write_durable_marker(self.durable_dir, f"fit_{candidate_fit_index:03d}_started.json", record)
            except Exception as exc:
                raise DurableLoggingError(
                    f"DURABLE_START_MARKER_FAILED: Cannot write fit {candidate_fit_index} start marker: {exc}"
                ) from exc

        self.started_fits = candidate_fit_index
        self.fit_records.append(record)
        return candidate_fit_index

    def record_fit_completed(self, fit_index: int, fit_seconds: float) -> None:
        """Record successful completion of a fit. Never silently suppresses marker write errors."""
        self.completed_fits += 1
        rec_data = None
        for rec in self.fit_records:
            if rec["fit_index"] == fit_index:
                rec["status"] = "COMPLETED"
                rec["end_time"] = time.time()
                rec["fit_seconds"] = fit_seconds
                rec_data = rec
                break

        if rec_data is None:
            rec_data = {
                "fit_index": fit_index,
                "status": "COMPLETED",
                "end_time": time.time(),
                "fit_seconds": fit_seconds,
            }

        if self.durable_dir:
            try:
                write_durable_marker(self.durable_dir, f"fit_{fit_index:03d}_completed.json", rec_data)
            except Exception as exc:
                raise DurableLoggingError(
                    f"DURABLE_COMPLETION_MARKER_FAILED: Failed to write fit {fit_index} completed marker: {exc}"
                ) from exc

    def record_fit_failed(self, fit_index: int, error_msg: str) -> None:
        """Record failure or interruption of a fit. Never silently suppresses marker write errors."""
        self.failed_fits += 1
        rec_data = None
        for rec in self.fit_records:
            if rec["fit_index"] == fit_index:
                rec["status"] = "FAILED"
                rec["end_time"] = time.time()
                rec["error"] = error_msg
                rec_data = rec
                break

        if rec_data is None:
            rec_data = {
                "fit_index": fit_index,
                "status": "FAILED",
                "end_time": time.time(),
                "error": error_msg,
            }

        if self.durable_dir:
            try:
                write_durable_marker(self.durable_dir, f"fit_{fit_index:03d}_failed.json", rec_data)
            except Exception as exc:
                raise DurableLoggingError(
                    f"DURABLE_FAILURE_MARKER_FAILED: Failed to write fit {fit_index} failure marker: {exc}"
                ) from exc


def reconcile_durable_fit_markers(durable_dir: Path) -> Dict[str, Any]:
    """Scan and reconcile durable fit markers on disk after worker crash or termination.

    Reads:
    - fit_{idx:03d}_started.json
    - fit_{idx:03d}_completed.json
    - fit_{idx:03d}_failed.json

    Reconstructs the minimum confirmed number of started fits.
    Distinguishes COMPLETED, FAILED, and INTERRUPTED_OR_UNKNOWN fit states.
    Never assumes a STARTED marker implies successful completion.
    """
    durable_dir = Path(durable_dir)
    if not durable_dir.is_dir():
        return {
            "started_fits": 0,
            "completed_fits": 0,
            "failed_fits": 0,
            "interrupted_or_unknown_fits": 0,
            "fit_records": [],
        }

    started_files = {p.name.replace("_started.json", ""): p for p in durable_dir.glob("fit_*_started.json")}
    completed_files = {p.name.replace("_completed.json", ""): p for p in durable_dir.glob("fit_*_completed.json")}
    failed_files = {p.name.replace("_failed.json", ""): p for p in durable_dir.glob("fit_*_failed.json")}

    all_stems = sorted(set(list(started_files.keys()) + list(completed_files.keys()) + list(failed_files.keys())))

    fit_records = []
    completed_count = 0
    failed_count = 0
    interrupted_count = 0

    for stem in all_stems:
        fit_idx_str = stem.replace("fit_", "")
        fit_idx = int(fit_idx_str) if fit_idx_str.isdigit() else None

        s_data = None
        if stem in started_files:
            try:
                s_data = json.loads(started_files[stem].read_text(encoding="utf-8"))
            except Exception:
                s_data = {"fit_index": fit_idx, "status": "CORRUPTED_START_MARKER"}

        if stem in completed_files:
            try:
                c_data = json.loads(completed_files[stem].read_text(encoding="utf-8"))
                c_data["status"] = "COMPLETED"
                fit_records.append(c_data)
            except Exception:
                rec = s_data or {"fit_index": fit_idx}
                rec["status"] = "COMPLETED"
                fit_records.append(rec)
            completed_count += 1
        elif stem in failed_files:
            try:
                f_data = json.loads(failed_files[stem].read_text(encoding="utf-8"))
                f_data["status"] = "FAILED"
                fit_records.append(f_data)
            except Exception:
                rec = s_data or {"fit_index": fit_idx}
                rec["status"] = "FAILED"
                fit_records.append(rec)
            failed_count += 1
        else:
            # Started marker exists without completion or failure marker:
            # worker was killed, interrupted by job object, or crashed
            rec = dict(s_data) if s_data else {"fit_index": fit_idx}
            rec["status"] = "INTERRUPTED_OR_UNKNOWN"
            rec["error"] = "WORKER_TERMINATED_DURING_FIT"
            fit_records.append(rec)
            interrupted_count += 1

    started_count = len(all_stems)

    return {
        "started_fits": started_count,
        "completed_fits": completed_count,
        "failed_fits": failed_count,
        "interrupted_or_unknown_fits": interrupted_count,
        "fit_records": fit_records,
    }


def enumerate_threshold_candidates(probs: np.ndarray) -> np.ndarray:
    """Enumerate all valid unique candidate thresholds in [0, 1] including endpoints."""
    p = probabilities(probs)
    return np.unique(np.concatenate(([0.0, 1.0], p)))


def evaluate_threshold_candidates_vectorized(
    y_val: np.ndarray,
    probs: np.ndarray,
    capacity_limit: int = 1200,
    cost_fp: int = 10,
    cost_fn: int = 500,
) -> Dict[str, Any]:
    """Evaluate all candidate thresholds on validation probabilities under P02 contract.

    Contract rules:
    - actions = (probs >= tau).astype(np.int8)
    - Equal-probability ties are preserved exactly.
    - Cost: 10 * FP + 500 * FN [benchmark cost units].
    - Capacity constraint: M = TP + FP <= capacity_limit.
    - Selection tie-breaking: on equal min cost, prefer lower M, then higher tau.
    - Zero refitting: evaluates candidate grid purely from precomputed probabilities.

    Returns:
        Dictionary containing selection status, best policy metrics, and candidate summary.
    """
    y = binary_vector(y_val, "validation_labels")
    p = probabilities(probs)
    n = len(y)
    if len(p) != n:
        raise ValueError(f"SHAPE_MISMATCH: labels ({n}) != probabilities ({len(p)})")

    total_p = int(np.count_nonzero(y == 1))
    total_n = n - total_p
    ref_cost = cost_fn * total_p

    thresholds = enumerate_threshold_candidates(p)

    # Sort probabilities for exact, fast cumulative evaluation
    order = np.argsort(p)
    p_sorted = p[order]
    y_sorted = y[order]

    # searchsorted with side='left' gives the index of first element >= tau
    idx = np.searchsorted(p_sorted, thresholds, side="left")
    m = n - idx

    # Cumulative positive labels count
    cum_y = np.concatenate(([0], np.cumsum(y_sorted)))
    tp = total_p - cum_y[idx]
    fp = m - tp
    fn = total_p - tp
    tn = total_n - fp
    cost = cost_fp * fp + cost_fn * fn

    # Check feasibility
    feasible_mask = m <= capacity_limit
    feasible_indices = np.where(feasible_mask)[0]

    candidate_count = len(thresholds)

    if len(feasible_indices) == 0:
        return {
            "status": "INFEASIBLE",
            "reason": "NO_FEASIBLE_THRESHOLD_FOUND",
            "candidate_count": candidate_count,
            "feasible_count": 0,
            "best": None,
            "objective_value": float(ref_cost) if ref_cost > 0 else 100000.0,
        }

    # Minimum cost among feasible candidates
    min_cost = int(np.min(cost[feasible_indices]))
    tie_indices = [i for i in feasible_indices if cost[i] == min_cost]

    # Tie-breaking contract: prefer lower M, then higher threshold
    best_idx = min(tie_indices, key=lambda i: (int(m[i]), -float(thresholds[i])))

    best_tau = float(thresholds[best_idx])
    best_tp = int(tp[best_idx])
    best_fp = int(fp[best_idx])
    best_fn = int(fn[best_idx])
    best_tn = int(tn[best_idx])
    best_m = int(m[best_idx])
    best_cost = int(cost[best_idx])

    # Precision, Recall, F1
    precision = best_tp / best_m if best_m > 0 else None
    recall = best_tp / total_p if total_p > 0 else None
    f1 = (2 * best_tp) / (total_p + best_m) if (total_p + best_m) > 0 else None

    # Savings
    abs_saving = ref_cost - best_cost
    saving_pct = (100.0 * abs_saving / ref_cost) if ref_cost > 0 else None

    excess = max(0, best_m - capacity_limit)

    best_policy = {
        "threshold": best_tau,
        "TP": best_tp,
        "FP": best_fp,
        "FN": best_fn,
        "TN": best_tn,
        "N": n,
        "P": total_p,
        "M": best_m,
        "K": capacity_limit,
        "maintenance_rate": best_m / n if n > 0 else 0.0,
        "excess": excess,
        "excess_rate": excess / n if n > 0 else 0.0,
        "feasible": excess == 0,
        "policy_status": "FEASIBLE" if excess == 0 else "INFEASIBLE",
        "cost_fp": cost_fp * best_fp,
        "cost_fn": cost_fn * best_fn,
        "total_cost": best_cost,
        "cost_per_observation": best_cost / n if n > 0 else 0.0,
        "reference_cost": ref_cost,
        "absolute_saving": abs_saving,
        "saving_pct": saving_pct,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

    return {
        "status": "FEASIBLE",
        "best": best_policy,
        "candidate_count": candidate_count,
        "feasible_count": len(feasible_indices),
        "objective_value": float(best_cost),
    }


def fit_and_evaluate_rf_trial(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    rf_params: Dict[str, Any],
    fit_counter: FitCounter,
    capacity_limit: int = 1200,
    trial_number: Optional[int] = None,
) -> Dict[str, Any]:
    """Execute a single trial evaluation with strict fit reservation BEFORE training."""
    y_train = binary_vector(y_train, "train_labels")
    y_val = binary_vector(y_val, "val_labels")

    fixed_params = {
        "class_weight": "balanced",
        "random_state": 42,
        "n_jobs": 1,
        "bootstrap": True,
    }
    all_params = {**fixed_params, **rf_params}

    model = RandomForestClassifier(**all_params)

    # Validate instantiated parameters
    inst_params = model.get_params()
    for k, v in all_params.items():
        if inst_params.get(k) != v:
            raise OptimizationError(f"PARAM_INSTANTIATION_MISMATCH: {k}={inst_params.get(k)}, expected {v}")

    # FIX 1: Reserve and durable record started fit BEFORE model.fit() is invoked
    fit_index = fit_counter.reserve_and_start_fit("RandomForestClassifier", rf_params, trial_number=trial_number)

    t0_fit = time.perf_counter()
    try:
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter("always")
            model.fit(x_train, y_train)
        fit_sec = time.perf_counter() - t0_fit
        # Record completion
        fit_counter.record_fit_completed(fit_index, fit_sec)
    except Exception as exc:
        fit_counter.record_fit_failed(fit_index, str(exc))
        raise

    classes = list(model.classes_)
    if classes != [0, 1]:
        raise OptimizationError(f"INVALID_CLASS_MAPPING: got {classes}, expected [0, 1]")

    t0_pred = time.perf_counter()
    proba = np.asarray(model.predict_proba(x_val))
    pred_sec = time.perf_counter() - t0_pred

    if proba.shape != (len(x_val), 2):
        raise OptimizationError(f"INVALID_PROBA_SHAPE: {proba.shape}, expected ({len(x_val)}, 2)")
    if not np.isfinite(proba).all():
        raise OptimizationError("NONFINITE_PROBABILITIES_PREDICTED")
    if not np.allclose(proba.sum(axis=1), 1.0, atol=1e-5):
        raise OptimizationError("PROBABILITIES_DO_NOT_SUM_TO_ONE")

    scores = proba[:, 1]

    # Evaluate candidate grid
    eval_result = evaluate_threshold_candidates_vectorized(
        y_val, scores, capacity_limit=capacity_limit
    )

    # Ranking metrics on probabilities
    p_val = int(np.sum(y_val == 1))
    roc_auc = float(roc_auc_score(y_val, scores)) if 0 < p_val < len(y_val) else None
    pr_auc = float(average_precision_score(y_val, scores)) if p_val > 0 else None
    brier = float(np.mean((scores - y_val) ** 2))

    return {
        "fit_index": fit_index,
        "rf_params": rf_params,
        "fit_seconds": fit_sec,
        "predict_seconds": pred_sec,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "brier": brier,
        "evaluation": eval_result,
        "warnings": [dict(category=w.category.__name__, message=str(w.message)) for w in caught_warnings],
    }


def create_phase2_study(seed: int = 42):
    """Instantiate a reproducible sequential Optuna Study using TPESampler."""
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(sampler=sampler, direction="minimize")
    return study


def run_optuna_phase2_trials(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray,
    y_val: np.ndarray,
    fit_counter: FitCounter,
    n_trials: int = 20,
    capacity_limit: int = 1200,
    seed: int = 42,
) -> Tuple[Any, List[Dict[str, Any]]]:
    """Execute exactly n_trials using Optuna TPE sampler with strict single-fit per trial."""
    study = create_phase2_study(seed=seed)
    trials_records: List[Dict[str, Any]] = []

    def objective(trial):
        # 1. Suggest parameters from locked search space
        rf_params = {
            "n_estimators": trial.suggest_int("n_estimators", 20, 60, step=10),
            "max_depth": trial.suggest_int("max_depth", 4, 12),
            "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
            "max_features": trial.suggest_float("max_features", 0.2, 0.5),
        }

        # 2. Evaluate trial with single fit
        trial_result = fit_and_evaluate_rf_trial(
            x_train, y_train, x_val, y_val,
            rf_params=rf_params,
            fit_counter=fit_counter,
            capacity_limit=capacity_limit,
            trial_number=trial.number,
        )

        eval_res = trial_result["evaluation"]
        status = eval_res["status"]
        best = eval_res.get("best")

        # 3. Record trial attributes
        trial.set_user_attr("trial_status", status)
        trial.set_user_attr("fit_index", trial_result["fit_index"])
        trial.set_user_attr("fit_seconds", trial_result["fit_seconds"])
        trial.set_user_attr("predict_seconds", trial_result["predict_seconds"])
        trial.set_user_attr("roc_auc", trial_result["roc_auc"])
        trial.set_user_attr("pr_auc", trial_result["pr_auc"])

        if status == "FEASIBLE" and best is not None:
            trial.set_user_attr("threshold", best["threshold"])
            trial.set_user_attr("M", best["M"])
            trial.set_user_attr("feasible", best["feasible"])
            trial.set_user_attr("cost", best["total_cost"])
            trial.set_user_attr("TP", best["TP"])
            trial.set_user_attr("FP", best["FP"])
            trial.set_user_attr("FN", best["FN"])
            trial.set_user_attr("TN", best["TN"])
            trial.set_user_attr("saving_pct", best["saving_pct"])
            objective_val = float(best["total_cost"])
        else:
            trial.set_user_attr("threshold", None)
            trial.set_user_attr("M", None)
            trial.set_user_attr("feasible", False)
            trial.set_user_attr("cost", eval_res.get("objective_value", 100000.0))
            objective_val = float(eval_res.get("objective_value", 100000.0))

        # Record structured trial data
        rec = {
            "trial_number": trial.number,
            "status": status,
            "objective_value": objective_val,
            "rf_params": rf_params,
            "fit_index": trial_result["fit_index"],
            "fit_seconds": trial_result["fit_seconds"],
            "predict_seconds": trial_result["predict_seconds"],
            "roc_auc": trial_result["roc_auc"],
            "pr_auc": trial_result["pr_auc"],
            "best_policy": best,
        }
        trials_records.append(rec)
        return objective_val

    study.optimize(objective, n_trials=n_trials)
    return study, trials_records


def sanitize_for_strict_json(obj: Any) -> Any:
    """Recursively sanitize Python data structures to guarantee strict JSON validity (no NaN, Inf)."""
    if isinstance(obj, dict):
        return {k: sanitize_for_strict_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_strict_json(v) for v in obj]
    elif isinstance(obj, tuple):
        return [sanitize_for_strict_json(v) for v in obj]
    elif isinstance(obj, (float, np.floating)):
        if math.isnan(obj):
            return None
        if math.isinf(obj):
            return 1e9 if obj > 0 else -1e9
        return float(obj)
    elif isinstance(obj, (int, np.integer)):
        return int(obj)
    elif isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return sanitize_for_strict_json(obj.tolist())
    return obj
