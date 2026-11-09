"""Synthetic Unit Tests for Scania APS Gate G10: Final Official Test Evaluator.

Guarantees:
- Official Test set (16,000 samples) remains strictly sealed during all tests.
- 0 touches to aps_failure_test_set.csv.
- Full verification of authorization validator, durable fit accounting,
  validation regression guard, and synthetic evaluation pipeline.
"""
import json
from pathlib import Path
import tempfile
import pytest
import numpy as np

from src.scania.g10_evaluation import (
    REPO_ROOT,
    TARGET_RUN_ID,
    EVALUATION_MODE,
    FROZEN_THRESHOLD,
    CAPACITY_LIMIT_K_TEST,
    OFFICIAL_TEST_EXPECTED_ROWS,
    FROZEN_RF_HYPERPARAMS,
    VALIDATION_REGRESSION_TARGET,
    verify_g10_owner_approval_text,
    verify_g10_owner_approval_reference,
    write_durable_marker,
    evaluate_policy_predictions,
    execute_g10_evaluation,
    run_g10_preflight,
    load_g10_config,
    get_g10_config_sha,
)
from src.scania.g4_b2_executor import ExecutorBlocked, SafetyBlocked


def test_frozen_policy_constants():
    """Verify that frozen policy constants exactly match Phase 2 Trial 16."""
    assert TARGET_RUN_ID == "scania_g10_official_test_001"
    assert EVALUATION_MODE == "DETERMINISTIC_TRAIN_REFIT_EVALUATION"
    assert FROZEN_THRESHOLD == 0.3232440937634324
    assert CAPACITY_LIMIT_K_TEST == 1600
    assert OFFICIAL_TEST_EXPECTED_ROWS == 16000

    assert FROZEN_RF_HYPERPARAMS["n_estimators"] == 50
    assert FROZEN_RF_HYPERPARAMS["max_depth"] == 10
    assert FROZEN_RF_HYPERPARAMS["min_samples_split"] == 10
    assert abs(FROZEN_RF_HYPERPARAMS["max_features"] - 0.4268663927182804) < 1e-6
    assert FROZEN_RF_HYPERPARAMS["class_weight"] == "balanced"
    assert FROZEN_RF_HYPERPARAMS["random_state"] == 42
    assert FROZEN_RF_HYPERPARAMS["n_jobs"] == 1
    assert FROZEN_RF_HYPERPARAMS["bootstrap"] is True

    assert VALIDATION_REGRESSION_TARGET["TP"] == 195
    assert VALIDATION_REGRESSION_TARGET["FP"] == 383
    assert VALIDATION_REGRESSION_TARGET["FN"] == 5
    assert VALIDATION_REGRESSION_TARGET["TN"] == 11417
    assert VALIDATION_REGRESSION_TARGET["total_cost"] == 6330
    assert VALIDATION_REGRESSION_TARGET["M"] == 578


def test_g10_config_integrity():
    """Verify that g10_evaluation.json is readable and valid."""
    cfg = load_g10_config(REPO_ROOT)
    assert cfg["target_run_id"] == TARGET_RUN_ID
    assert cfg["evaluation_mode"] == EVALUATION_MODE
    assert cfg["source_policy"]["selected_trial"] == 16
    assert cfg["budget"]["total_max_fits"] == 1
    assert cfg["budget"]["max_trials"] == 1
    assert cfg["resource_limits"]["max_native_threads"] == 1

    sha = get_g10_config_sha(REPO_ROOT)
    assert len(sha) == 64


def test_authorization_validator_valid_comment():
    """Verify that an authentic Owner approval comment passes validation."""
    commit_sha = "a" * 40
    valid_comment = f"""# OWNER TASK AUTHORIZATION — G10 OFFICIAL TEST EVALUATION

Decision: APPROVED
Authorized Commit: {commit_sha}
Target Run ID: scania_g10_official_test_001
Permitted Operation: G10_OFFICIAL_TEST_EVALUATION
Approved Estimator: RandomForestClassifier
Evaluation Mode: DETERMINISTIC_TRAIN_REFIT_EVALUATION
Fit Budget: max_trials=1, total_max_fits=1, fits_per_trial=1
Frozen Threshold: 0.3232440937634324
Data Scope: Train (Refit), Validation (Guard), Official Test (Evaluation)
Resource Limits: max_native_threads=1, max_ram_mb=2048, max_wall_seconds=180
"""
    expected_record = {
        "source_integrity": {"authorized_commit": commit_sha},
        "target_run_id": TARGET_RUN_ID,
    }

    parsed = verify_g10_owner_approval_text(
        valid_comment, author="PhucHuynh16", expected_record=expected_record
    )
    assert parsed["authorized_commit"] == commit_sha
    assert parsed["target_run_id"] == TARGET_RUN_ID
    assert parsed["total_max_fits"] == 1
    assert parsed["evaluation_mode"] == EVALUATION_MODE


def test_authorization_validator_rejects_unauthorized_author():
    """Verify rejection when author is not PhucHuynh16."""
    comment = "# OWNER DIRECTIVE\nDecision: APPROVED"
    with pytest.raises(ExecutorBlocked, match="AUTHORIZATION_NOT_FROM_OWNER"):
        verify_g10_owner_approval_text(comment, author="RandomUser")


def test_authorization_validator_rejects_agent_report():
    """Verify rejection when comment is an agent report."""
    comment = "## ANTIGRAVITY REPORT\n# OWNER DIRECTIVE\nDecision: APPROVED"
    with pytest.raises(ExecutorBlocked, match="AGENT_REPORT_CANNOT_AUTHORIZE"):
        verify_g10_owner_approval_text(comment, author="PhucHuynh16")


def test_authorization_validator_rejects_missing_decision():
    """Verify rejection when decision is not APPROVED."""
    comment = f"""# OWNER DIRECTIVE
Authorized Commit: {'b'*40}
Target Run ID: scania_g10_official_test_001
Permitted Operation: G10_OFFICIAL_TEST_EVALUATION
Decision: REJECTED
"""
    with pytest.raises(ExecutorBlocked, match="INVALID_OR_MISSING_APPROVAL_DECISION"):
        verify_g10_owner_approval_text(comment, author="PhucHuynh16")


def test_authorization_validator_rejects_wrong_mode():
    """Verify rejection when evaluation mode is not DETERMINISTIC_TRAIN_REFIT_EVALUATION."""
    comment = f"""# OWNER DIRECTIVE
Decision: APPROVED
Authorized Commit: {'c'*40}
Target Run ID: scania_g10_official_test_001
Permitted Operation: G10_OFFICIAL_TEST_EVALUATION
Approved Estimator: RandomForestClassifier
Evaluation Mode: SINGLE_PASS_ZERO_FIT
Fit Budget: max_trials=1, total_max_fits=1, fits_per_trial=1
"""
    with pytest.raises(ExecutorBlocked, match="INVALID_EVALUATION_MODE"):
        verify_g10_owner_approval_text(comment, author="PhucHuynh16")


def test_authorization_validator_rejects_excessive_fits():
    """Verify rejection when fit budget exceeds 1."""
    comment = f"""# OWNER DIRECTIVE
Decision: APPROVED
Authorized Commit: {'d'*40}
Target Run ID: scania_g10_official_test_001
Permitted Operation: G10_OFFICIAL_TEST_EVALUATION
Approved Estimator: RandomForestClassifier
Evaluation Mode: DETERMINISTIC_TRAIN_REFIT_EVALUATION
Fit Budget: max_trials=5, total_max_fits=5, fits_per_trial=1
"""
    with pytest.raises(ExecutorBlocked, match="INVALID_FIT_BUDGET"):
        verify_g10_owner_approval_text(comment, author="PhucHuynh16")


def test_authorization_validator_rejects_wrong_commit():
    """Verify rejection when comment commit does not match expected record."""
    commit_1 = "1" * 40
    commit_2 = "2" * 40
    comment = f"""# OWNER DIRECTIVE
Decision: APPROVED
Authorized Commit: {commit_1}
Target Run ID: scania_g10_official_test_001
Permitted Operation: G10_OFFICIAL_TEST_EVALUATION
Approved Estimator: RandomForestClassifier
Evaluation Mode: DETERMINISTIC_TRAIN_REFIT_EVALUATION
Fit Budget: max_trials=1, total_max_fits=1, fits_per_trial=1
Data Scope: Train, Validation, Official Test
Resource Limits: max_native_threads=1, max_ram_mb=2048, max_wall_seconds=180
"""
    expected_record = {
        "source_integrity": {"authorized_commit": commit_2},
        "target_run_id": TARGET_RUN_ID,
    }
    with pytest.raises(ExecutorBlocked, match="COMMENT_COMMIT_MISMATCH"):
        verify_g10_owner_approval_text(comment, author="PhucHuynh16", expected_record=expected_record)


def test_evaluate_policy_predictions_math():
    """Verify metric calculations for a known confusion matrix."""
    y_true = np.array([1, 1, 0, 0, 0])
    probs = np.array([0.9, 0.1, 0.8, 0.2, 0.0])
    # At threshold 0.5:
    # y_pred = [1, 0, 1, 0, 0]
    # TP = 1 (idx 0), FN = 1 (idx 1)
    # FP = 1 (idx 2), TN = 2 (idx 3, 4)
    # Cost = 10 * 1 + 500 * 1 = 510
    # M = 2, K = 3 -> feasible = 1
    metrics = evaluate_policy_predictions(
        y_true, probs, threshold=0.5, capacity_limit_K=3, cost_fp=10, cost_fn=500
    )
    assert metrics["TP"] == 1
    assert metrics["FP"] == 1
    assert metrics["FN"] == 1
    assert metrics["TN"] == 2
    assert metrics["total_cost"] == 510
    assert metrics["M"] == 2
    assert metrics["feasible"] == 1
    assert metrics["policy_status"] == "FEASIBLE"
    assert metrics["reference_cost"] == 1000
    assert metrics["absolute_saving"] == 490
    assert metrics["saving_pct"] == 49.0
    assert abs(metrics["precision"] - 0.5) < 1e-6
    assert abs(metrics["recall"] - 0.5) < 1e-6


def test_durable_marker_atomic_write():
    """Verify atomic write of durable JSON marker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        marker_dir = Path(tmpdir)
        test_data = {"test_key": "test_val", "number": 123}
        out_file = write_durable_marker(marker_dir, "test_marker.json", test_data)
        assert out_file.is_file()
        content = json.loads(out_file.read_text(encoding="utf-8"))
        assert content == test_data


def test_official_test_unsealed_fails_without_authorization():
    """Verify that running REAL evaluation without authorization fails closed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = Path(tmpdir) / TARGET_RUN_ID
        with pytest.raises((ExecutorBlocked, SafetyBlocked)):
            execute_g10_evaluation(
                root=REPO_ROOT,
                mode="REAL",
                override_output_dir=tmp_output,
            )


def test_synthetic_end_to_end_pipeline():
    """Verify end-to-end evaluation pipeline on synthetic data without touching Official Test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = Path(tmpdir) / TARGET_RUN_ID

        # Generate synthetic test set: 500 samples, 170 features
        np.random.seed(42)
        X_test_synthetic = np.random.randn(500, 170)
        y_test_synthetic = np.random.choice([0, 1], size=500, p=[0.97, 0.03])

        summary = execute_g10_evaluation(
            root=REPO_ROOT,
            mode="SYNTHETIC",
            override_output_dir=tmp_output,
            synthetic_test_data=(X_test_synthetic, y_test_synthetic),
        )

        assert summary["status"] == "COMPLETED_SUCCESSFULLY"
        assert summary["fits_consumed"] == 1
        assert summary["validation_guard"] == "PASSED"

        # Verify durable markers
        durable_dir = tmp_output / "durable_fits"
        start_marker = durable_dir / "fit_001_STARTED.json"
        comp_marker = durable_dir / "fit_001_COMPLETED.json"
        assert start_marker.is_file()
        assert comp_marker.is_file()

        start_data = json.loads(start_marker.read_text(encoding="utf-8"))
        comp_data = json.loads(comp_marker.read_text(encoding="utf-8"))
        assert start_data["status"] == "STARTED"
        assert comp_data["status"] == "COMPLETED"
        assert comp_data["fit_duration_seconds"] > 0

        # Verify output artifacts
        assert (tmp_output / "validation_guard_metrics.json").is_file()
        assert (tmp_output / "test_metrics.json").is_file()
        assert (tmp_output / "confusion_matrix_test.csv").is_file()
        assert (tmp_output / "best_policy.json").is_file()
        assert (tmp_output / "run_summary.json").is_file()
        assert (tmp_output / "stable_manifest.json").is_file()

        # Check validation guard reproduced exact Phase 2 Trial 16 metrics
        val_guard = json.loads((tmp_output / "validation_guard_metrics.json").read_text(encoding="utf-8"))
        assert val_guard["TP"] == 195
        assert val_guard["FP"] == 383
        assert val_guard["FN"] == 5
        assert val_guard["TN"] == 11417
        assert val_guard["total_cost"] == 6330
        assert val_guard["M"] == 578

        # Verify Official Test CSV was NOT extracted to raw directory
        raw_test_csv = REPO_ROOT / "data/raw/scania_aps/aps_failure_test_set.csv"
        assert not raw_test_csv.exists(), "Official Test CSV must remain sealed inside zip!"
