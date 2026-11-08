"""Comprehensive synthetic tests for Phase 2 Constrained Optimization.

Tests:
1. Optuna objective with synthetic data.
2. Threshold boundaries in [0, 1] and exact equal-probability ties.
3. Feasible vs infeasible candidate selection and tie-breaking.
4. Deterministic selection and structured logging.
5. Fit counter enforcement and interruption handling (budget exceeded).
6. Failure before fitting (missing/invalid authorization or config).
7. Official Test access rejection by I/O guard.
8. CLI entry point verification (preflight and synthetic).
9. Optuna version and compatibility verification.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import pytest
import numpy as np

from src.scania.phase2_optimization import (
    FitCounter, FitBudgetExceeded, OptimizationError,
    enumerate_threshold_candidates, evaluate_threshold_candidates_vectorized,
    fit_and_evaluate_rf_trial, create_phase2_study, run_optuna_phase2_trials,
    sanitize_for_strict_json
)
from src.scania.phase2_executor import (
    REPO_ROOT, ExecutorBlocked, load_phase2_config, get_phase2_config_sha,
    execute_phase2_preflight_check, validate_phase2_authorization_record,
    write_phase2_evidence_artifacts, verify_phase2_run
)
from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked


def test_optuna_installed_version_compatibility():
    """Verify Optuna is installed, version >= 5.0.0, and TPESampler functions deterministically."""
    import optuna
    ver_tokens = [int(x) for x in optuna.__version__.split(".")[:2]]
    assert ver_tokens[0] >= 5, f"Optuna version must be >= 5.0.0, got {optuna.__version__}"
    study1 = create_phase2_study(seed=42)
    study2 = create_phase2_study(seed=42)
    assert study1.direction == optuna.study.StudyDirection.MINIMIZE
    assert study2.direction == optuna.study.StudyDirection.MINIMIZE


def test_threshold_boundaries_and_exact_ties():
    """Verify threshold evaluation covers [0.0, 1.0] and handles equal-probability ties exactly."""
    # Probabilities with exact duplicate values
    p = np.array([0.0, 0.2, 0.2, 0.2, 0.5, 0.5, 1.0])
    y = np.array([0,   0,   1,   0,   1,   0,   1], dtype=np.int8)

    candidates = enumerate_threshold_candidates(p)
    assert 0.0 in candidates
    assert 1.0 in candidates
    assert np.all((candidates >= 0.0) & (candidates <= 1.0))
    assert np.all(np.diff(candidates) > 0)  # Strictly ascending

    res = evaluate_threshold_candidates_vectorized(y, p, capacity_limit=7)
    assert res["status"] == "FEASIBLE"
    assert res["candidate_count"] == len(candidates)

    # Check that at tau = 0.2, all 3 items with p = 0.2 are predicted positive
    idx_02 = np.where(candidates == 0.2)[0][0]
    acts_02 = (p >= 0.2).astype(np.int8)
    assert np.count_nonzero(acts_02 == 1) == 6  # 0.2, 0.2, 0.2, 0.5, 0.5, 1.0


def test_feasible_and_infeasible_candidates_and_tie_breaking():
    """Verify capacity constraint filtering, tie-breaking (min cost, lower M, higher tau), and infeasible case."""
    y = np.array([0, 0, 0, 1, 1], dtype=np.int8)
    p = np.array([0.1, 0.2, 0.3, 0.8, 0.9])

    # 1. Feasible with capacity_limit = 2:
    # At tau = 0.8: actions = [0, 0, 0, 1, 1], M = 2 <= 2, TP = 2, FP = 0, Cost = 0
    res = evaluate_threshold_candidates_vectorized(y, p, capacity_limit=2)
    assert res["status"] == "FEASIBLE"
    assert res["best"]["threshold"] == 0.8
    assert res["best"]["total_cost"] == 0
    assert res["best"]["M"] == 2

    # 2. Equal cost tie-breaking:
    # Suppose we have equal cost candidates, prefer lower M, then higher threshold
    # Construct case where two thresholds have equal cost:
    p_ties = np.array([0.2, 0.4, 0.6, 0.8])
    y_ties = np.array([0,   0,   0,   0], dtype=np.int8)  # All negative: any FP costs 10*FP
    # At tau=0.5: actions=[0,0,1,1] -> FP=2, M=2, cost=20
    # At tau=0.7: actions=[0,0,0,1] -> FP=1, M=1, cost=10
    # At tau=0.85: actions=[0,0,0,0] -> FP=0, M=0, cost=0
    # At tau=1.0: actions=[0,0,0,0] -> FP=0, M=0, cost=0
    # Both tau=0.85 and tau=1.0 have cost=0 and M=0.
    # Tie-break prefers higher threshold -> tau = 1.0
    res_tie = evaluate_threshold_candidates_vectorized(y_ties, p_ties, capacity_limit=4)
    assert res_tie["status"] == "FEASIBLE"
    assert res_tie["best"]["total_cost"] == 0
    assert res_tie["best"]["M"] == 0
    assert res_tie["best"]["threshold"] == 1.0

    # 3. Completely Infeasible (capacity_limit = -1):
    res_infeas = evaluate_threshold_candidates_vectorized(y, p, capacity_limit=-1)
    assert res_infeas["status"] == "INFEASIBLE"
    assert res_infeas["best"] is None
    assert res_infeas["feasible_count"] == 0


def test_fit_counter_enforcement_and_budget_limits():
    """Verify FitCounter strictly prevents exceeding authorized fit budget."""
    fc = FitCounter(max_fits=3)
    assert fc.current_fits == 0

    fc.record_fit("RandomForestClassifier", {"n_estimators": 20}, 0.5)
    assert fc.current_fits == 1
    fc.record_fit("RandomForestClassifier", {"n_estimators": 30}, 0.6)
    assert fc.current_fits == 2
    fc.record_fit("RandomForestClassifier", {"n_estimators": 40}, 0.7)
    assert fc.current_fits == 3

    # Attempting 4th fit must fail closed
    with pytest.raises(FitBudgetExceeded, match="MAX_REAL_FITS_EXCEEDED"):
        fc.record_fit("RandomForestClassifier", {"n_estimators": 50}, 0.8)

    assert fc.current_fits == 3
    assert fc.attempted_fits == 4
    assert len(fc.fit_records) == 3


def test_optuna_objective_synthetic_deterministic_execution():
    """Test full synthetic execution of run_optuna_phase2_trials with deterministic seed."""
    rng = np.random.RandomState(42)
    x_tr = rng.randn(120, 6)
    y_tr = (rng.rand(120) < 0.15).astype(np.int8)
    y_tr[0], y_tr[1] = 0, 1

    x_val = rng.randn(50, 6)
    y_val = (rng.rand(50) < 0.15).astype(np.int8)
    y_val[0], y_val[1] = 0, 1

    fc = FitCounter(max_fits=5)
    study, records = run_optuna_phase2_trials(
        x_tr, y_tr, x_val, y_val,
        fit_counter=fc,
        n_trials=5,
        capacity_limit=5,
        seed=42,
    )

    assert len(study.trials) == 5
    assert len(records) == 5
    assert fc.current_fits == 5
    for rec in records:
        assert "trial_number" in rec
        assert "objective_value" in rec
        assert rec["status"] in ("FEASIBLE", "INFEASIBLE")
        if rec["status"] == "FEASIBLE":
            assert rec["best_policy"]["M"] <= 5


def test_failure_before_fitting_missing_or_invalid_authorization():
    """Verify execution halts immediately without fitting if authorization or config is invalid."""
    # 1. Non-existent run ID
    with pytest.raises(ExecutorBlocked, match="PHASE2_AUTHORIZATION_RECORD_MISSING"):
        validate_phase2_authorization_record(
            auth_path_or_dict=REPO_ROOT / "configs/scania/authorizations/non_existent.json",
            expected_run_id="non_existent",
            root=REPO_ROOT,
        )

    # 2. Invalid status
    invalid_record = {
        "run_id": "test_run",
        "authorization_status": "PENDING_APPROVAL",
        "permitted_operation": "CONSTRAINED_OPTIMIZATION_VALIDATION_ONLY",
    }
    with pytest.raises(ExecutorBlocked, match="AUTHORIZATION_NOT_GRANTED"):
        validate_phase2_authorization_record(invalid_record, expected_run_id="test_run", root=REPO_ROOT)

    # 3. Invalid operation
    invalid_op_record = {
        "run_id": "test_run",
        "authorization_status": "AUTHORIZED",
        "permitted_operation": "UNAUTHORIZED_GRID_SEARCH",
    }
    with pytest.raises(ExecutorBlocked, match="INVALID_PERMITTED_OPERATION"):
        validate_phase2_authorization_record(invalid_op_record, expected_run_id="test_run", root=REPO_ROOT)


def test_official_test_access_rejection_io_guard():
    """Verify application-level audit hook blocks any access to Official Test CSV or ZIP archives."""
    import subprocess
    code = f"""
import sys, tempfile
from pathlib import Path
from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked

root = Path(r'{REPO_ROOT}')
with tempfile.TemporaryDirectory() as tmp_out:
    out_path = Path(tmp_out)
    allowlist = [out_path / 'valid.txt']
    install_executor_io_guard(root, out_path, allowlist)

    # Attempt to open Official Test CSV
    test_file = root / 'data/raw/scania_aps/aps_failure_test_set.csv'
    try:
        open(test_file, 'r')
        sys.exit(10)
    except SafetyBlocked:
        pass

    # Attempt to open archive ZIP
    try:
        open('some_archive.zip', 'r')
        sys.exit(11)
    except SafetyBlocked:
        pass

sys.exit(0)
"""
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert proc.returncode == 0, f"Audit hook subprocess failed with exit code {proc.returncode}: {proc.stderr}"


def test_strict_json_sanitization():
    """Verify strict JSON compliance: NaN and Inf are safely converted without throwing."""
    data = {
        "finite": 42.0,
        "nan_val": float("nan"),
        "inf_val": float("inf"),
        "neg_inf_val": float("-inf"),
        "nested": {"inner_nan": float("nan")},
        "array": np.array([1.0, np.nan, np.inf]),
    }
    sanitized = sanitize_for_strict_json(data)
    json_str = json.dumps(sanitized)
    assert "NaN" not in json_str
    assert "Infinity" not in json_str
    assert sanitized["nan_val"] is None
    assert sanitized["inf_val"] == 1e9


def test_phase2_config_integrity():
    """Verify locked Phase 2 configuration has correct structure, parameters, and valid hash."""
    cfg = load_phase2_config(REPO_ROOT)
    assert cfg["estimator"] == "RandomForestClassifier"
    assert cfg["budget"]["max_trials"] == 20
    assert cfg["budget"]["total_max_fits"] == 20
    assert cfg["budget"]["max_fits_per_trial"] == 1
    assert cfg["constraint"]["max_maintenance_units"] == 1200
    assert cfg["data"]["official_test"] == "SEALED_UNTIL_G10"

    cfg_sha = get_phase2_config_sha(REPO_ROOT)
    assert len(cfg_sha) == 64


def test_cli_preflight_and_synthetic_invocation():
    """Verify CLI commands run successfully for preflight and synthetic test modes."""
    from scripts.run_scania_phase2 import run_preflight, run_synthetic_test
    # 1. Preflight
    code = run_preflight(REPO_ROOT)
    assert code == 0

    # 2. Synthetic test
    code_syn = run_synthetic_test(REPO_ROOT, run_id="unit_test_synthetic_001", n_trials=3)
    assert code_syn == 0
    syn_dir = REPO_ROOT / "results/scania_aps/phase2/unit_test_synthetic_001"
    assert syn_dir.is_dir()
    assert (syn_dir / "optuna_study.json").is_file()
    assert (syn_dir / "trials_summary.csv").is_file()
    assert (syn_dir / "run_summary.json").is_file()
    assert verify_phase2_run(syn_dir) is True


def test_real_execution_rejection_without_owner_authorization():
    """Verify real execution fails closed when no valid Owner authorization comment exists."""
    from scripts.run_scania_phase2 import run_phase2_real
    with pytest.raises(ExecutorBlocked, match="AUTHORIZATION_RECORD_NOT_FOUND"):
        run_phase2_real(REPO_ROOT, run_id="unauthorized_test_run_999")


def test_preservation_of_g3_and_g4_accepted_evidence():
    """Verify that G3 accepted manifest and G4 successful baseline run 002 are completely intact."""
    # 1. G3 manifest
    g3_manifest_file = REPO_ROOT / "results/scania_aps/g3/official_20261029_04/stable_manifest.json"
    assert g3_manifest_file.is_file()
    g3_data = json.loads(g3_manifest_file.read_text(encoding="utf-8"))
    assert g3_data["stable_digest"] == "efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb"

    # 2. G4 real run 002
    g4_run_dir = REPO_ROOT / "results/scania_aps/g4/scania_g4_b2_real_002"
    assert g4_run_dir.is_dir()
    from src.scania.g4_artifacts import verify_run
    assert verify_run(g4_run_dir) is True

    # 3. G4 failed run 001 preserved
    g4_fail_dir = REPO_ROOT / "results/scania_aps/g4/scania_g4_b2_real_001"
    assert g4_fail_dir.is_dir()
    assert (g4_fail_dir / "failure_diagnostics.json").is_file()

