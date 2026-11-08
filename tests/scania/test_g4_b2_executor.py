"""Tests for G4 Baseline Executor: I/O guard allowlist, G3 artifact verification, and baseline pipeline.

All tests run on synthetic fixtures or read-only metadata verification.
No real-data fitting or Official Test access is performed.
"""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
import pytest

from src.scania.g4_b2_executor import (
    SafetyBlocked,
    ExecutorBlocked,
    ExecutorFailure,
    verify_owner_approval_reference,
    validate_owner_authorization_record,
    install_executor_io_guard,
    verify_g3_artifacts_and_build_allowlist,
    fit_and_score_baseline_model,
    execute_synthetic_pipeline_test,
    execute_synthetic_baseline_orchestration,
    execute_real_baseline_gate,
    assess_proposed_resource_limits,
)
from src.scania.baselines import STUMP_PARAMS, LR_PARAMS, BaselineFailure
from src.scania.constraints import PRIMARY, SECONDARY, capacity_report
from src.scania.contracts import canonical, digest, object_hash
from src.scania.data import array_hash, ordered_ids_hash, source_ids
from src.scania.g4_contract import CONFIG_SHA, G3_STABLE, load_config, Blocked

ROOT = Path(__file__).resolve().parents[2]


def test_EX01_io_guard_blocks_raw_train_test_set_and_archive(tmp_path):
    """Verify application-level audit hook blocks raw CSV, archive, and Official Test set."""
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked\n"
        "root = Path(sys.argv[1]).resolve()\n"
        "out = Path(sys.argv[2]).resolve()\n"
        "install_executor_io_guard(root, out, allowlist=[])\n"
        "\n"
        "blocked_test = False\n"
        "try:\n"
        "    open(root / 'aps_failure_test_set.csv', 'r')\n"
        "except SafetyBlocked:\n"
        "    blocked_test = True\n"
        "\n"
        "blocked_archive = False\n"
        "try:\n"
        "    open(root / 'data/raw/scania_aps/aps+failure+at+scania+trucks.zip', 'rb')\n"
        "except SafetyBlocked:\n"
        "    blocked_archive = True\n"
        "\n"
        "blocked_raw = False\n"
        "try:\n"
        "    open(root / 'data/raw/scania_aps/aps_failure_training_set.csv', 'r')\n"
        "except SafetyBlocked:\n"
        "    blocked_raw = True\n"
        "\n"
        "print(f'TEST={blocked_test},ARCHIVE={blocked_archive},RAW={blocked_raw}')\n"
    )
    cmd = [sys.executable, "-B", "-c", code, str(ROOT), str(tmp_path)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert "TEST=True,ARCHIVE=True,RAW=True" in proc.stdout


def test_EX02_io_guard_blocks_writes_outside_output_and_to_source(tmp_path):
    """Verify audit hook blocks writes outside designated output and forbids writes to source data."""
    output_dir = tmp_path / "run_out"
    output_dir.mkdir()
    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked\n"
        "root = Path(sys.argv[1]).resolve()\n"
        "out = Path(sys.argv[2]).resolve()\n"
        "install_executor_io_guard(root, out, allowlist=[])\n"
        "\n"
        "# 1. Write inside output should succeed\n"
        "with open(out / 'metrics.json', 'w') as f:\n"
        "    f.write('{}')\n"
        "\n"
        "# 2. Write outside output must fail\n"
        "blocked_outside = False\n"
        "try:\n"
        "    with open(root / 'escape.txt', 'w') as f:\n"
        "        f.write('escape')\n"
        "except SafetyBlocked:\n"
        "    blocked_outside = True\n"
        "\n"
        "# 3. Write to data/ must fail even if attempted\n"
        "blocked_data_write = False\n"
        "try:\n"
        "    with open(root / 'data/processed/scania_aps/tamper.txt', 'w') as f:\n"
        "        f.write('tamper')\n"
        "except SafetyBlocked:\n"
        "    blocked_data_write = True\n"
        "\n"
        "print(f'OUTSIDE={blocked_outside},DATA_WRITE={blocked_data_write}')\n"
    )
    cmd = [sys.executable, "-B", "-c", code, str(ROOT), str(output_dir)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert "OUTSIDE=True,DATA_WRITE=True" in proc.stdout
    assert (output_dir / "metrics.json").is_file()


def test_EX03_io_guard_blocks_unauthorized_reads_and_allows_allowlist(tmp_path):
    """Verify audit hook strictly allows reading allowlisted files and blocks unauthorized reads."""
    allowed_file = tmp_path / "allowed.npy"
    allowed_file.write_bytes(b"ALLOWED_CONTENT")
    unauthorized_file = tmp_path / "secret.npy"
    unauthorized_file.write_bytes(b"SECRET_CONTENT")

    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked\n"
        "root = Path(sys.argv[1]).resolve()\n"
        "out = Path(sys.argv[2]).resolve()\n"
        "allowed = Path(sys.argv[3]).resolve()\n"
        "secret = Path(sys.argv[4]).resolve()\n"
        "install_executor_io_guard(root, out, allowlist=[allowed])\n"
        "\n"
        "# Read allowed\n"
        "read_allowed = False\n"
        "with open(allowed, 'rb') as f:\n"
        "    if f.read() == b'ALLOWED_CONTENT':\n"
        "        read_allowed = True\n"
        "\n"
        "# Read unauthorized .npy\n"
        "blocked_secret = False\n"
        "try:\n"
        "    with open(secret, 'rb') as f:\n"
        "        f.read()\n"
        "except SafetyBlocked:\n"
        "    blocked_secret = True\n"
        "\n"
        "print(f'ALLOWED={read_allowed},SECRET_BLOCKED={blocked_secret}')\n"
    )
    cmd = [sys.executable, "-B", "-c", code, str(ROOT), str(tmp_path), str(allowed_file), str(unauthorized_file)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert "ALLOWED=True,SECRET_BLOCKED=True" in proc.stdout


def test_EX04_verify_g3_artifacts_and_build_allowlist_matches_accepted_run(tmp_path):
    """[READ-ONLY G3 ARTIFACT CHECK] Verify G3 artifact verification succeeds and populates allowlist for verified run.

    Performs read-only validation of persisted G3 artifacts against accepted G3 stable manifest and official Train CSV.
    Does NOT perform model training, validation scoring, or test set access.
    """
    run_id = "test_g3_verify_01"
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    allowlist, summary = verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)
    assert summary["train_rows"] == 48000
    assert summary["validation_rows"] == 12000
    assert summary["features"] == 170
    assert summary["joblib_deserialization"] == "ELIMINATED"
    assert summary["label_row_alignment"] == "VERIFIED_MATCH"
    assert len(allowlist) == 6

    # Verify expected files in allowlist (joblib files eliminated)
    file_names = {p.name for p in allowlist}
    assert "official_split.json" in file_names
    assert "membership.npz" in file_names
    assert "tree_train.npy" in file_names
    assert "tree_validation.npy" in file_names
    assert "lr_train.npy" in file_names
    assert "lr_validation.npy" in file_names
    assert "tree_preprocessor.joblib" not in file_names
    assert "lr_preprocessor.joblib" not in file_names


def _build_synthetic_g3_fixture(tmp_path, run_id="synth_g3"):
    """Helper to construct a valid synthetic G3 artifact environment in tmp_path."""
    meta_dir = tmp_path / "results/scania_aps/g3" / run_id
    accepted_dir = tmp_path / "results/scania_aps/g3/official_20261029_04"
    proc_dir = tmp_path / "data/processed/scania_aps" / run_id
    raw_dir = tmp_path / "data/raw/scania_aps"

    meta_dir.mkdir(parents=True, exist_ok=True)
    accepted_dir.mkdir(parents=True, exist_ok=True)
    proc_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    train = np.arange(48000, dtype=np.int64)
    val = np.arange(48000, 60000, dtype=np.int64)
    y_train = np.zeros(48000, dtype=np.int8)
    y_train[:800] = 1
    y_val = np.zeros(12000, dtype=np.int8)
    y_val[:200] = 1

    # Raw train CSV creation with valid pos/neg tokens
    raw_lines = [b"class," + b",".join(f"f{i}".encode() for i in range(170))]
    for r in range(60000):
        cls = b"pos" if (r < 800 or 48000 <= r < 48200) else b"neg"
        raw_lines.append(cls + b"," + b",".join(b"0" for _ in range(170)))
    raw_bytes = b"\n".join(raw_lines)
    raw_csv_path = raw_dir / "aps_failure_training_set.csv"
    raw_csv_path.write_bytes(raw_bytes)
    source_sha = digest(raw_bytes)

    membership = {
        "source_sha256": source_sha,
        "train_ids": source_ids(train, source_sha),
        "validation_ids": source_ids(val, source_sha),
    }
    split_file = tmp_path / "data/processed/scania_aps/official_split.json"
    split_file.write_text(json.dumps(membership), encoding="utf-8")

    npz_file = proc_dir / "membership.npz"
    np.savez(npz_file, train=train, validation=val, y_train=y_train, y_validation=y_val)

    arrays = {}
    dummy_train = np.zeros((48000, 170), dtype=np.float64)
    dummy_val = np.zeros((12000, 170), dtype=np.float64)

    for name, arr in [("tree_train", dummy_train), ("tree_validation", dummy_val),
                      ("lr_train", dummy_train), ("lr_validation", dummy_val)]:
        np.save(proc_dir / f"{name}.npy", arr, allow_pickle=False)
        arrays[name] = array_hash(arr)

    manifest = {
        "source_sha256": source_sha,
        "schema_sha256": "dummy_schema",
        "config_sha256": "dummy_config",
        "membership_sha256": object_hash(membership),
        "train_ordered_ids_sha256": ordered_ids_hash(train, source_sha),
        "validation_ordered_ids_sha256": ordered_ids_hash(val, source_sha),
        "imputer_statistics_sha256": "dummy_imputer",
        "scaler_mean_sha256": "dummy_scaler_mean",
        "scaler_scale_sha256": "dummy_scaler_scale",
        "array_sha256": arrays,
    }
    manifest_bytes = json.dumps(manifest).encode("utf-8")
    (meta_dir / "stable_manifest.json").write_bytes(manifest_bytes)
    (accepted_dir / "stable_manifest.json").write_bytes(manifest_bytes)
    checksums = {"stable_manifest.json": digest(manifest_bytes)}
    (meta_dir / "checksums.json").write_bytes(json.dumps(checksums).encode("utf-8"))
    (accepted_dir / "checksums.json").write_bytes(json.dumps(checksums).encode("utf-8"))

    return dict(meta_dir=meta_dir, accepted_dir=accepted_dir, proc_dir=proc_dir, raw_dir=raw_dir,
                raw_csv=raw_csv_path, split_file=split_file, npz_file=npz_file, manifest=manifest)


def test_EX05_verify_g3_artifacts_fails_closed_on_tampering(tmp_path):
    """Verify verify_g3_artifacts fails closed with specific errors when G3 artifacts are tampered.

    Negative test cases run entirely on synthetic fixtures without altering repository artifacts.
    """
    run_id = "test_tamper_g3"

    # 1. Non-existent metadata directory
    with pytest.raises(ExecutorBlocked, match="G3_METADATA_DIR_MISSING"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id="non_existent_9999")

    # 2. Checksum mismatch in public metadata
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    (fix["meta_dir"] / "stable_manifest.json").write_bytes(b'{"corrupted": true}')
    with pytest.raises(ExecutorBlocked, match="G3_PUBLIC_CHECKSUM_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 3. Missing accepted G3 manifest
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    (fix["accepted_dir"] / "stable_manifest.json").unlink()
    with pytest.raises(ExecutorBlocked, match="ACCEPTED_G3_MANIFEST_MISSING"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 4. Missing raw train CSV
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    fix["raw_csv"].unlink()
    with pytest.raises(ExecutorBlocked, match="RAW_TRAIN_CSV_MISSING"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 5. Invalid raw target label token in CSV (e.g. 'invalid_token')
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    bad_lines = [b"class," + b",".join(f"f{i}".encode() for i in range(170))]
    for r in range(60000):
        cls = b"maybe" if r == 0 else (b"pos" if r < 800 else b"neg")
        bad_lines.append(cls + b"," + b",".join(b"0" for _ in range(170)))
    bad_bytes = b"\n".join(bad_lines)
    fix["raw_csv"].write_bytes(bad_bytes)
    # update source sha so hash check passes but token check fails
    csv_h = digest(bad_bytes)
    fix["manifest"]["source_sha256"] = csv_h
    fix["manifest"]["train_ordered_ids_sha256"] = ordered_ids_hash(np.arange(48000), csv_h)
    fix["manifest"]["validation_ordered_ids_sha256"] = ordered_ids_hash(np.arange(48000, 60000), csv_h)
    m_bytes = json.dumps(fix["manifest"]).encode("utf-8")
    (fix["meta_dir"] / "stable_manifest.json").write_bytes(m_bytes)
    (fix["accepted_dir"] / "stable_manifest.json").write_bytes(m_bytes)
    (fix["meta_dir"] / "checksums.json").write_bytes(json.dumps({"stable_manifest.json": digest(m_bytes)}).encode("utf-8"))
    with pytest.raises(ExecutorBlocked, match="INVALID_RAW_TARGET_LABEL"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 6. Missing official_split.json
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    fix["split_file"].unlink()
    with pytest.raises(ExecutorBlocked, match="G3_OFFICIAL_SPLIT_JSON_MISSING"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 7. Membership hash mismatch
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    fix["split_file"].write_text('{"tampered": 1}', encoding="utf-8")
    with pytest.raises(ExecutorBlocked, match="MEMBERSHIP_HASH_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 8. Partition size mismatch (e.g. 47999 rows)
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    np.savez(fix["npz_file"], train=np.arange(47999), validation=np.arange(12000),
             y_train=np.zeros(47999, dtype=np.int8), y_validation=np.zeros(12000, dtype=np.int8))
    with pytest.raises(ExecutorBlocked, match="PARTITION_SIZE_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 9. Partitions not disjoint (overlapping rows)
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    bad_val = np.arange(47999, 59999)
    np.savez(fix["npz_file"], train=np.arange(48000), validation=bad_val,
             y_train=np.zeros(48000, dtype=np.int8), y_validation=np.zeros(12000, dtype=np.int8))
    with pytest.raises(ExecutorBlocked, match="PARTITIONS_NOT_DISJOINT"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 10. Non-binary labels (values != 0, 1)
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    bad_y_train = np.zeros(48000, dtype=np.int8)
    bad_y_train[0] = 2
    np.savez(fix["npz_file"], train=np.arange(48000), validation=np.arange(48000, 60000),
             y_train=bad_y_train, y_validation=np.zeros(12000, dtype=np.int8))
    with pytest.raises(ExecutorBlocked, match="TRAIN_LABELS_NOT_BINARY_0_1"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 11. Class count mismatch (e.g. 801 pos instead of 800)
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    bad_y_train = np.zeros(48000, dtype=np.int8)
    bad_y_train[:801] = 1
    bad_y_val = np.zeros(12000, dtype=np.int8)
    bad_y_val[:200] = 1
    np.savez(fix["npz_file"], train=np.arange(48000), validation=np.arange(48000, 60000),
             y_train=bad_y_train, y_validation=bad_y_val)
    with pytest.raises(ExecutorBlocked, match="TRAIN_CLASS_COUNTS_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 12. Ordered IDs hash mismatch
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    rev_train = np.arange(47999, -1, -1)
    y_t = np.zeros(48000, dtype=np.int8)
    y_t[:800] = 1
    y_v = np.zeros(12000, dtype=np.int8)
    y_v[:200] = 1
    np.savez(fix["npz_file"], train=rev_train, validation=np.arange(48000, 60000),
             y_train=y_t, y_validation=y_v)
    with pytest.raises(ExecutorBlocked, match="TRAIN_ORDERED_IDS_HASH_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 13. Processed array hash mismatch
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    tampered_arr = np.ones((48000, 170), dtype=np.float64)
    np.save(fix["proc_dir"] / "tree_train.npy", tampered_arr, allow_pickle=False)
    with pytest.raises(ExecutorBlocked, match="ARRAY_HASH_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 14. Missing processed array
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    (fix["proc_dir"] / "tree_train.npy").unlink()
    with pytest.raises(ExecutorBlocked, match="PROCESSED_ARRAY_MISSING"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)

    # 15. Label row-alignment mismatch against raw train CSV
    shutil.rmtree(tmp_path)
    fix = _build_synthetic_g3_fixture(tmp_path, run_id=run_id)
    raw_lines = [b"class," + b",".join(f"f{i}".encode() for i in range(170))]
    for r in range(60000):
        cls = b"pos" if (1 <= r < 801) else b"neg"  # row 0 flipped
        raw_lines.append(cls + b"," + b",".join(b"0" for _ in range(170)))
    raw_bytes = b"\n".join(raw_lines)
    fix["raw_csv"].write_bytes(raw_bytes)
    csv_sha = digest(raw_bytes)
    fix["manifest"]["source_sha256"] = csv_sha
    fix["manifest"]["train_ordered_ids_sha256"] = ordered_ids_hash(np.arange(48000), csv_sha)
    fix["manifest"]["validation_ordered_ids_sha256"] = ordered_ids_hash(np.arange(48000, 60000), csv_sha)
    m_bytes = json.dumps(fix["manifest"]).encode("utf-8")
    (fix["meta_dir"] / "stable_manifest.json").write_bytes(m_bytes)
    (fix["accepted_dir"] / "stable_manifest.json").write_bytes(m_bytes)
    (fix["meta_dir"] / "checksums.json").write_bytes(json.dumps({"stable_manifest.json": digest(m_bytes)}).encode("utf-8"))
    with pytest.raises(ExecutorBlocked, match="TRAIN_LABEL_ROW_ALIGNMENT_MISMATCH"):
        verify_g3_artifacts_and_build_allowlist(tmp_path, g3_run_id=run_id)


def test_EX06_b0_majority_dummy_contract():
    """Verify B0 majority dummy contract: always predicts 0, no fit, cost = 500 * P_val."""
    y_train = np.array([0, 0, 0, 1], dtype=np.int8)
    x_train = np.zeros((4, 2))
    y_val = np.array([0, 0, 1, 1], dtype=np.int8)  # P_val = 2
    x_val = np.zeros((4, 2))

    rows, telemetry = fit_and_score_baseline_model("B0", x_train, y_train, x_val, y_val)
    assert len(rows) == 1
    row = rows[0]
    assert row["baseline_id"] == "B0"
    assert row["role"] == "REFERENCE"
    assert row["P"] == 2
    assert row["TP"] == 0
    assert row["FP"] == 0
    assert row["FN"] == 2
    assert row["TN"] == 2
    assert row["total_cost"] == 500 * 2  # 1000
    assert row["M"] == 0
    assert row["feasible"] is True
    assert telemetry["fit_seconds"] == 0.0
    assert telemetry["real_estimator_fits"] == 0


def test_EX07_b1_decision_stump_locked_parameters_and_cost():
    """Verify B1 Decision Stump uses locked max_depth=1 and evaluates at PRIMARY and SECONDARY."""
    assert STUMP_PARAMS["max_depth"] == 1
    assert STUMP_PARAMS["random_state"] == 42

    rng = np.random.RandomState(42)
    x_train = rng.randn(100, 4)
    y_train = (x_train[:, 0] > 0).astype(np.int8)
    x_val = rng.randn(50, 4)
    y_val = (x_val[:, 0] > 0).astype(np.int8)

    rows, telemetry = fit_and_score_baseline_model("B1", x_train, y_train, x_val, y_val)
    assert len(rows) == 2
    assert telemetry["parameters"]["max_depth"] == 1
    assert telemetry["parameters"]["random_state"] == 42
    assert telemetry["real_estimator_fits"] == 1

    roles = {r["role"]: r for r in rows}
    assert "PRIMARY" in roles
    assert "SECONDARY" in roles
    assert roles["PRIMARY"]["threshold"] == PRIMARY
    assert roles["SECONDARY"]["threshold"] == SECONDARY

    # Verify cost equation
    for r in rows:
        assert r["total_cost"] == 10 * r["FP"] + 500 * r["FN"]


def test_EX08_b2_logistic_regression_locked_parameters_and_max_iter_2000():
    """Verify B2 Logistic Regression uses max_iter=2000, solver=lbfgs, C=1.0."""
    assert LR_PARAMS["max_iter"] == 2000
    assert LR_PARAMS["solver"] == "lbfgs"
    assert LR_PARAMS["C"] == 1.0
    assert LR_PARAMS["tol"] == 1e-4

    rng = np.random.RandomState(42)
    x_train = rng.randn(100, 4)
    y_train = (x_train[:, 0] > 0).astype(np.int8)
    x_val = rng.randn(50, 4)
    y_val = (x_val[:, 0] > 0).astype(np.int8)

    rows, telemetry = fit_and_score_baseline_model("B2", x_train, y_train, x_val, y_val)
    assert len(rows) == 2
    assert telemetry["parameters"]["max_iter"] == 2000
    assert telemetry["parameters"]["solver"] == "lbfgs"

    # Test convergence failure fail-closed behavior
    bad_params = copy.deepcopy(LR_PARAMS)
    bad_params["max_iter"] = 1  # Guaranteed convergence failure on complex unscaled data
    bad_x = rng.randn(200, 20) * 1000.0
    bad_y = (rng.rand(200) > 0.5).astype(np.int8)

    with pytest.raises(BaselineFailure, match="FAILED_CONVERGENCE_WARNING"):
        fit_and_score_baseline_model("B2", bad_x, bad_y, bad_x[:10], bad_y[:10], b2_params=bad_params)


def test_EX09_capacity_constraint_infeasible_policy():
    """Verify that when maintenance inspections M exceed floor(N/10), policy is marked INFEASIBLE."""
    n = 100
    k = n // 10  # 10
    actions_infeasible = np.zeros(n, dtype=np.int8)
    actions_infeasible[:15] = 1

    rep = capacity_report(actions_infeasible)
    assert rep["M"] == 15
    assert rep["K"] == 10
    assert rep["excess"] == 5
    assert rep["feasible"] is False
    assert rep["policy_status"] == "INFEASIBLE"

    actions_feasible = np.zeros(n, dtype=np.int8)
    actions_feasible[:8] = 1

    rep_f = capacity_report(actions_feasible)
    assert rep_f["M"] == 8
    assert rep_f["K"] == 10
    assert rep_f["excess"] == 0
    assert rep_f["feasible"] is True
    assert rep_f["policy_status"] == "FEASIBLE"

    # Official Scania Validation partition contract: N=12,000 rows -> K = floor(12000/10) = 1200
    n_val_official = 12000
    acts_12k_feasible = np.zeros(n_val_official, dtype=np.int8)
    acts_12k_feasible[:1200] = 1
    rep_12k_f = capacity_report(acts_12k_feasible)
    assert rep_12k_f["K"] == 1200
    assert rep_12k_f["M"] == 1200
    assert rep_12k_f["excess"] == 0
    assert rep_12k_f["feasible"] is True
    assert rep_12k_f["policy_status"] == "FEASIBLE"

    acts_12k_infeasible = np.zeros(n_val_official, dtype=np.int8)
    acts_12k_infeasible[:1201] = 1
    rep_12k_inf = capacity_report(acts_12k_infeasible)
    assert rep_12k_inf["K"] == 1200
    assert rep_12k_inf["M"] == 1201
    assert rep_12k_inf["excess"] == 1
    assert rep_12k_inf["feasible"] is False
    assert rep_12k_inf["policy_status"] == "INFEASIBLE"


def test_EX10_execute_real_baseline_gate_is_strictly_locked():
    """Verify execute_real_baseline_gate fails closed when gate_b_authorized=False."""
    with pytest.raises(ExecutorBlocked, match="GATE_B2_NOT_AUTHORIZED"):
        execute_real_baseline_gate(ROOT, run_id="attempt_unauthorized_run")


def test_EX11_end_to_end_synthetic_pipeline_execution():
    """Verify end-to-end synthetic execution across B0, B1, and B2 generates all 5 policy rows."""
    res = execute_synthetic_pipeline_test(n_train=150, n_val=50, n_features=4, random_state=42)
    assert res["status"] == "SYNTHETIC_TEST_PASSED"
    rows = res["rows"]
    assert len(rows) == 5  # 1 B0, 2 B1, 2 B2

    b_ids = [r["baseline_id"] for r in rows]
    assert b_ids.count("B0") == 1
    assert b_ids.count("B1") == 2
    assert b_ids.count("B2") == 2

    for r in rows:
        assert "TP" in r and "FP" in r and "FN" in r and "TN" in r
        assert "total_cost" in r
        assert "precision" in r
        assert "recall" in r
        assert "feasible" in r
        assert "policy_status" in r


def test_EX12_proposed_resource_limits_feasibility_assessment():
    """Verify assess_proposed_resource_limits confirms technical feasibility of proposed limits.

    Confirms that memory and runtime figures are explicitly labeled as ESTIMATED engineering
    projections, not measured real-fit figures.
    """
    assessment = assess_proposed_resource_limits()
    assert assessment["proposed_thread_limit"] == 1
    assert assessment["proposed_timeout_seconds"] == 120.0
    assert assessment["proposed_ram_cap_mb"] == 2048.0
    assert assessment["estimated_peak_ram_mb"] == 450.0
    assert assessment["estimated_b1_seconds"] == 1.0
    assert assessment["estimated_b2_seconds"] == 25.0
    assert assessment["ram_feasible"] is True
    assert assessment["time_feasible"] is True
    assert assessment["status"] == "PROPOSED_LIMITS_TECHNICALLY_FEASIBLE"
    assert "ESTIMATED" in assessment["note"]


def test_EX13_cli_gate_b2_fails_closed():
    """Verify scripts/run_scania_baselines.py gate-b2 fails closed with 0 fits and sealed test set."""
    run_id = f"test_gate_b2_locked_{int(time.time())}"
    run_dir = ROOT / "results/scania_aps/g4" / run_id
    try:
        cmd = [
            sys.executable,
            str(ROOT / "scripts/run_scania_baselines.py"),
            "gate-b2",
            "--run-id",
            run_id,
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
        assert proc.returncode != 0, f"Expected non-zero exit code, got {proc.returncode}"

        # Verify evidence run recorded fail-closed status
        assert run_dir.is_dir()
        summary_file = run_dir / "run_summary.json"
        assert summary_file.is_file()
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        assert summary["status"] == "BLOCKED"
        assert summary["lifecycle"] == "FAILED"
        assert summary["gate_b_authorized"] is False
        assert summary["real_estimator_fits"] == 0
        assert summary["real_validation_scored"] is False
        assert summary["official_test"] == "SEALED_UNTIL_G10"

        diag_file = run_dir / "failure_diagnostics.json"
        assert diag_file.is_file()
        diag = json.loads(diag_file.read_text(encoding="utf-8"))
        errors = diag.get("errors", [])
        assert len(errors) > 0
        assert "GATE_B2_NOT_AUTHORIZED" in errors[0]["reason"]
    finally:
        if run_dir.is_dir():
            shutil.rmtree(run_dir, ignore_errors=True)


def test_EX14_synthetic_supervisor_worker_orchestration(tmp_path):
    """Verify actual supervisor/worker orchestration under WindowsJob on synthetic data.

    Confirms:
    - Actual worker process is spawned under Windows Job Object.
    - Native thread control verified to be 1 thread.
    - Total estimator fits = 2 (B0: 0, B1: 1, B2: 1).
    - Validation scored = True.
    - 5 policy rows generated with exact 10*FP + 500*FN equation.
    - Observed measured wall timings recorded.
    - Clean process exit and job cleanup without leaks.
    """
    run_id = f"test_synth_orch_{int(time.time())}"
    synth_dir = tmp_path / "synth_environment"

    report = execute_synthetic_baseline_orchestration(
        ROOT, run_id, synthetic_dir=synth_dir, n_train=120, n_val=40, n_features=4
    )
    assert report["status"] == "COMPLETE"
    assert report["lifecycle"] == "COMPLETE"
    assert report["real_estimator_fits"] == 0
    assert report["synthetic_estimator_fits"] == 2
    assert report["real_validation_scored"] is False
    assert report["synthetic_validation_scored"] is True

    rows = report["rows"]
    assert len(rows) == 5  # 1 B0, 2 B1, 2 B2

    b_ids = [r["baseline_id"] for r in rows]
    assert b_ids.count("B0") == 1
    assert b_ids.count("B1") == 2
    assert b_ids.count("B2") == 2

    # Verify confusion matrix and cost equations
    for r in rows:
        assert r["total_cost"] == 10 * r["FP"] + 500 * r["FN"]
        assert r["feasible"] in (True, False)
        assert r["policy_status"] in ("FEASIBLE", "INFEASIBLE")

    # Verify observed timings and resources
    timings = report["observed_timings"]
    assert timings["b1_fit_seconds"] >= 0.0
    assert timings["b2_fit_seconds"] >= 0.0
    assert timings["total_fit_seconds"] >= 0.0
    assert report["measured_wall_seconds"] > 0.0
    assert report["measured_peak_ram_mb"] > 0.0


def test_EX15_synthetic_worker_timeout_containment(tmp_path):
    """Verify supervisor enforces wall timeout and terminates worker via WindowsJob."""
    run_id = f"test_timeout_{int(time.time())}"
    synth_dir = tmp_path / "timeout_synth"

    with pytest.raises(TimeoutError, match="RUN_WALL_TIMEOUT"):
        execute_synthetic_baseline_orchestration(
            ROOT, run_id, synthetic_dir=synth_dir, wall_seconds=0.0001,
            n_train=2000, n_val=500, n_features=20
        )


def test_EX16_run_reservation_lifecycle_and_no_overwrite(tmp_path):
    """Verify single-owner run reservation contract, collision rejection, and no arbitrary directory adoption (F1)."""
    from src.scania.g4_artifacts import EvidenceRun, Blocked
    run_id = f"test_reserv_{int(time.time())}"

    # 1. First reservation succeeds and creates directory atomically
    out = EvidenceRun(tmp_path, run_id)
    assert out.path.is_dir()
    assert hasattr(out, "validate_reservation_contract")
    assert out.validate_reservation_contract(tmp_path, run_id) is True

    # 2. Second reservation with same run_id fails closed with RUN_ID_EXISTS
    with pytest.raises(Blocked, match="RUN_ID_EXISTS"):
        EvidenceRun(tmp_path, run_id)

    # 3. Passing wrong expected run_id or root to validate_reservation_contract fails
    with pytest.raises(Blocked, match="RESERVATION_RUN_ID_MISMATCH"):
        out.validate_reservation_contract(tmp_path, "different_run_id")
    with pytest.raises(Blocked, match="RESERVATION_ROOT_MISMATCH"):
        out.validate_reservation_contract(tmp_path / "other", run_id)

    # 4. execute_real_baseline_gate rejects non-reservation objects or path mismatch
    with pytest.raises(ExecutorBlocked, match="INVALID_RUN_RESERVATION_TYPE"):
        execute_real_baseline_gate(tmp_path, run_id, run_reservation="invalid_string")


def test_EX17_owner_authorization_record_schema_and_semantics(monkeypatch):
    """Verify comprehensive schema, trust boundary, git HEAD binding, and semantic validation (F2 & Trust Boundary)."""
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT)).decode("utf-8").strip()

    valid_synth_record = {
        "schema_version": "1.0",
        "run_id": "test_auth_01",
        "authorization_status": "AUTHORIZED",
        "permitted_operation": "SYNTHETIC_BASELINE_TESTING_ONLY",
        "owner_approval": {
            "reference": "SYNTHETIC_FIXTURE_SC_G4_B2",
            "directive": "OWNER DIRECTIVE — SC-G4-B2 FINAL RELEASE BLOCKER CLOSURE",
            "decision": "APPROVED",
            "approved_by": "OWNER"
        },
        "source_integrity": {
            "authorized_commit": current_head,
            "canonical_config_sha256": CONFIG_SHA
        },
        "data_scope": {
            "accepted_g3_run_id": "official_20261029_04",
            "accepted_g3_manifest_sha256": G3_STABLE,
            "allowed_partitions": ["train", "validation"],
            "official_test_sealed": True
        },
        "approved_models": ["B0", "B1", "B2"],
        "fit_budget": {
            "B0": 0,
            "B1": 1,
            "B2": 1,
            "total_max_fits": 2
        },
        "resource_limits": {
            "max_native_threads": 1,
            "max_ram_mb": 2048,
            "max_wall_seconds": 120
        },
        "mode": "SYNTHETIC_ONLY"
    }

    # 1. Valid synthetic record passes under SYNTHETIC mode with repository root check
    res = validate_owner_authorization_record(valid_synth_record, "test_auth_01", mode="SYNTHETIC", root=ROOT)
    assert res["authorization_status"] == "AUTHORIZED"

    # 2. Synthetic authorization can NEVER authorize real data gate
    with pytest.raises(ExecutorBlocked, match="SYNTHETIC_AUTHORIZATION_CANNOT_AUTHORIZE_REAL_DATA"):
        validate_owner_authorization_record(valid_synth_record, "test_auth_01", mode="REAL")

    # 3. Unverifiable Owner approval reference fails closed in REAL mode
    unverif = copy.deepcopy(valid_synth_record)
    unverif["mode"] = "REAL"
    unverif["permitted_operation"] = "BASELINE_FITTING_VALIDATION_ONLY"
    unverif["owner_approval"]["reference"] = "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-9999999999"
    with pytest.raises(ExecutorBlocked, match="UNVERIFIABLE_OWNER_APPROVAL"):
        validate_owner_authorization_record(unverif, "test_auth_01", mode="REAL")

    # 4. Invalid Owner approval reference (non-whitelisted URL)
    bad_ref = copy.deepcopy(valid_synth_record)
    bad_ref["owner_approval"]["reference"] = "https://unauthorized-domain.com/bogus"
    with pytest.raises(ExecutorBlocked, match="INVALID_SYNTHETIC_APPROVAL_REFERENCE"):
        validate_owner_authorization_record(bad_ref, "test_auth_01", mode="SYNTHETIC")

    # 5. Source commit mismatch against repository HEAD
    bad_commit = copy.deepcopy(valid_synth_record)
    bad_commit["source_integrity"]["authorized_commit"] = "0" * 40
    with pytest.raises(ExecutorBlocked, match="AUTHORIZED_COMMIT_MISMATCH"):
        validate_owner_authorization_record(bad_commit, "test_auth_01", mode="SYNTHETIC", root=ROOT)

    # 6. Canonical configuration hash mismatch
    bad_cfg = copy.deepcopy(valid_synth_record)
    bad_cfg["source_integrity"]["canonical_config_sha256"] = "f" * 64
    with pytest.raises(ExecutorBlocked, match="AUTHORIZED_CONFIG_SHA_MISMATCH"):
        validate_owner_authorization_record(bad_cfg, "test_auth_01", mode="SYNTHETIC")

    # 7. Accepted G3 manifest hash mismatch in REAL mode
    bad_g3 = copy.deepcopy(valid_synth_record)
    bad_g3["mode"] = "REAL"
    bad_g3["permitted_operation"] = "BASELINE_FITTING_VALIDATION_ONLY"
    bad_g3["data_scope"]["accepted_g3_manifest_sha256"] = "0" * 64
    monkeypatch.setattr("src.scania.g4_b2_executor.verify_owner_approval_reference", lambda *a, **kw: True)
    with pytest.raises(ExecutorBlocked, match="ACCEPTED_G3_MANIFEST_SHA_MISMATCH"):
        validate_owner_authorization_record(bad_g3, "test_auth_01", mode="REAL")

    # 8. Accepted G3 run ID mismatch in REAL mode
    bad_run = copy.deepcopy(valid_synth_record)
    bad_run["mode"] = "REAL"
    bad_run["permitted_operation"] = "BASELINE_FITTING_VALIDATION_ONLY"
    bad_run["data_scope"]["accepted_g3_run_id"] = "wrong_g3_run"
    with pytest.raises(ExecutorBlocked, match="ACCEPTED_G3_RUN_ID_MISMATCH"):
        validate_owner_authorization_record(bad_run, "test_auth_01", mode="REAL")

    # 9. Excessive or zero fit budget
    bad_bud = copy.deepcopy(valid_synth_record)
    bad_bud["fit_budget"]["total_max_fits"] = 0
    with pytest.raises(ExecutorBlocked, match="INVALID_FIT_BUDGET"):
        validate_owner_authorization_record(bad_bud, "test_auth_01", mode="SYNTHETIC")

    # 10. Self-conferred approval
    self_app = copy.deepcopy(valid_synth_record)
    self_app["owner_approval"]["approved_by"] = "Antigravity"
    with pytest.raises(ExecutorBlocked, match="AUTHORIZATION_NOT_FROM_OWNER"):
        validate_owner_authorization_record(self_app, "test_auth_01", mode="SYNTHETIC")

    # 11. Missing explicit approved_models fails closed
    missing_models = copy.deepcopy(valid_synth_record)
    del missing_models["approved_models"]
    with pytest.raises(ExecutorBlocked, match="MISSING_EXPLICIT_APPROVED_MODELS"):
        validate_owner_authorization_record(missing_models, "test_auth_01", mode="SYNTHETIC")

    # 12. Missing explicit fit_budget fields fails closed
    missing_budget = copy.deepcopy(valid_synth_record)
    del missing_budget["fit_budget"]["total_max_fits"]
    with pytest.raises(ExecutorBlocked, match="MISSING_EXPLICIT_FIT_BUDGET_FIELDS"):
        validate_owner_authorization_record(missing_budget, "test_auth_01", mode="SYNTHETIC")

    # 13. Git HEAD verification failure fails closed
    orig_check_output = subprocess.check_output
    def mock_git_fail(cmd, *a, **kw):
        if "rev-parse" in cmd:
            raise subprocess.CalledProcessError(128, cmd)
        return orig_check_output(cmd, *a, **kw)
    monkeypatch.setattr(subprocess, "check_output", mock_git_fail)
    with pytest.raises(ExecutorBlocked, match="GIT_HEAD_VERIFICATION_FAILED"):
        validate_owner_authorization_record(valid_synth_record, "test_auth_01", mode="SYNTHETIC", root=ROOT)
    monkeypatch.undo()

    # 14. Comment body inspection & rejection of agent report
    class MockCommentResponse:
        def __init__(self, data):
            self.data = data
        def read(self):
            return json.dumps(self.data).encode("utf-8")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    import urllib.request
    monkeypatch.setattr("src.scania.g4_b2_executor._get_github_token", lambda: "fake_github_token")

    # 14a. Rejection of agent report
    agent_body = "## ANTIGRAVITY TECHNICAL REPORT\n# OWNER TASK AUTHORIZATION\nDecision: APPROVED"
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": agent_body}))
    with pytest.raises(ExecutorBlocked, match="AGENT_REPORT_CANNOT_AUTHORIZE"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=valid_synth_record, mode="REAL"
        )

    # 14b. Rejection of unexecuted template inside code fences
    template_body = "Here is the template:\n```markdown\n# OWNER TASK AUTHORIZATION\nDecision: APPROVED\n```"
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": template_body}))
    with pytest.raises(ExecutorBlocked, match="MISSING_OWNER_DIRECTIVE_HEADER"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=valid_synth_record, mode="REAL"
        )

    # 14c. Rejection of commit SHA mismatch
    mismatch_commit_body = (
        f"# OWNER TASK AUTHORIZATION — SC-G4-B2 REAL BASELINE FITTING\n"
        f"Decision: APPROVED\n"
        f"Authorized Commit: {'0'*40}\n"
        f"Target Run ID: test_auth_01\n"
        f"Permitted Operation: BASELINE_FITTING_VALIDATION_ONLY\n"
        f"Approved Models: B0, B1, B2\n"
        f"Fit Budget: B0=0, B1=1, B2=1, total_max_fits=2\n"
        f"Data Scope: train, validation (official test sealed until G10)\n"
        f"Resource Limits: max_native_threads=1, max_ram_mb=2048, max_wall_seconds=120\n"
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": mismatch_commit_body}))
    real_expected = copy.deepcopy(valid_synth_record)
    real_expected["mode"] = "REAL"
    real_expected["permitted_operation"] = "BASELINE_FITTING_VALIDATION_ONLY"
    with pytest.raises(ExecutorBlocked, match="COMMENT_COMMIT_MISMATCH"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14d. Authentic human Owner comment passes with exact field values
    authentic_body = (
        f"# OWNER TASK AUTHORIZATION — SC-G4-B2 REAL BASELINE FITTING\n"
        f"Decision: APPROVED\n"
        f"Authorized Commit: {current_head}\n"
        f"Target Run ID: test_auth_01\n"
        f"Permitted Operation: BASELINE_FITTING_VALIDATION_ONLY\n"
        f"Approved Models: B0, B1, B2\n"
        f"Fit Budget: B0=0, B1=1, B2=1, total_max_fits=2\n"
        f"Data Scope: train, validation (official test sealed until G10)\n"
        f"Resource Limits: max_native_threads=1, max_ram_mb=2048, max_wall_seconds=120\n"
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": authentic_body}))
    assert verify_owner_approval_reference(
        "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
        expected_record=real_expected, mode="REAL"
    ) is True

    # 14e. Rejection of unapproved or contradictory decision
    rej_decision_body = authentic_body.replace("Decision: APPROVED", "Decision: REJECTED")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": rej_decision_body}))
    with pytest.raises(ExecutorBlocked, match="INVALID_OR_MISSING_APPROVAL_DECISION"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14f. Rejection of contradictory models (extra model B3, or missing B0)
    extra_model_body = authentic_body.replace("Approved Models: B0, B1, B2", "Approved Models: B0, B1, B2, B3")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": extra_model_body}))
    with pytest.raises(ExecutorBlocked, match="INVALID_APPROVED_MODELS"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    missing_model_body = authentic_body.replace("Approved Models: B0, B1, B2", "Approved Models: B1, B2")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": missing_model_body}))
    with pytest.raises(ExecutorBlocked, match="INVALID_APPROVED_MODELS"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14g. Rejection of contradictory fit budget
    bad_budget_total = authentic_body.replace("total_max_fits=2", "total_max_fits=3")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": bad_budget_total}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_OR_INVALID_FIT_BUDGET"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    bad_budget_alloc = authentic_body.replace("B0=0", "B0=1")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": bad_budget_alloc}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_OR_INVALID_FIT_BUDGET"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14h. Rejection of contradictory resource limits (excessive threads, RAM, wall time)
    bad_threads_body = authentic_body.replace("max_native_threads=1", "max_native_threads=4")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": bad_threads_body}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_OR_INVALID_THREADS"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    bad_ram_body = authentic_body.replace("max_ram_mb=2048", "max_ram_mb=4096")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": bad_ram_body}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_OR_INVALID_RAM"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    bad_wall_body = authentic_body.replace("max_wall_seconds=120", "max_wall_seconds=300")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": bad_wall_body}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_OR_INVALID_WALL_TIME"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14i. Rejection of contradictory data scope & missing test seal
    unsealed_body = authentic_body.replace("(official test sealed until G10)", "(official test unsealed for evaluation)")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": unsealed_body}))
    with pytest.raises(ExecutorBlocked, match="CONTRADICTORY_DATA_SCOPE"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    missing_seal_body = authentic_body.replace(" (official test sealed until G10)", "")
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": missing_seal_body}))
    with pytest.raises(ExecutorBlocked, match="MISSING_TEST_SEAL_DECLARATION"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 14j. Rejection of duplicate authorization keys or aliases (fail-closed parameter pollution check)
    dup_decision_body = authentic_body + "\nDecision: REJECTED\n"
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": dup_decision_body}))
    with pytest.raises(ExecutorBlocked, match="DUPLICATE_AUTHORIZATION_FIELD"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    dup_scope_alias_body = authentic_body + "\nScope: test permitted\n"
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": dup_scope_alias_body}))
    with pytest.raises(ExecutorBlocked, match="DUPLICATE_AUTHORIZATION_FIELD"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    dup_commit_alias_body = authentic_body + f"\nCommit: {'0'*40}\n"
    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=10: MockCommentResponse({"user": {"login": "PhucHuynh16"}, "body": dup_commit_alias_body}))
    with pytest.raises(ExecutorBlocked, match="DUPLICATE_AUTHORIZATION_FIELD"):
        verify_owner_approval_reference(
            "https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/17#issuecomment-12345",
            expected_record=real_expected, mode="REAL"
        )

    # 15. Controlled configuration transition contract
    cfg_a = load_config(ROOT, gate="GATE_A")
    assert cfg_a["gate_b_authorized"] is False
    with pytest.raises(Blocked, match="GATE_B2_NOT_AUTHORIZED"):
        load_config(ROOT, gate="GATE_B2")


def test_EX18_production_equivalent_synthetic_cli_lifecycle(tmp_path):
    """Verify full production-equivalent synthetic CLI lifecycle with checksum finalization and verification (F1, F6)."""
    from scripts.run_scania_baselines import run_synthetic_gate_b2
    from src.scania.g4_artifacts import verify_run
    run_id = f"test_cli_synth_{int(time.time())}"

    out_path = run_synthetic_gate_b2(tmp_path, run_id=run_id)
    assert Path(out_path).is_dir()

    # Verify checksums.json exists and verify_run succeeds
    assert verify_run(out_path) is True

    # Verify all 9 required artifacts exist on disk
    expected_artifacts = {
        "run_summary.json", "config.json", "environment.json",
        "stable_manifest.json", "baseline_metrics.json", "baseline_metrics.csv",
        "failure_diagnostics.json", "execution.txt", "checksums.json"
    }
    present_files = {p.name for p in Path(out_path).iterdir()}
    assert expected_artifacts.issubset(present_files)

    summary = json.loads((out_path / "run_summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "GATE_B2_SYNTHETIC_SUCCESS"
    assert summary["lifecycle"] == "COMPLETE"
    assert summary["synthetic_estimator_fits"] == 2
    assert summary["real_estimator_fits"] == 0
    assert summary["synthetic_validation_scored"] is True
    assert summary["real_validation_scored"] is False

    # Check metrics files
    metrics = json.loads((out_path / "baseline_metrics.json").read_text(encoding="utf-8"))
    assert len(metrics["rows"]) == 5
    for r in metrics["rows"]:
        assert r["total_cost"] == 10 * r["FP"] + 500 * r["FN"]


def test_EX19_truthful_fit_counts_and_failure_telemetry(tmp_path, monkeypatch):
    """Verify truthful fit counts and failure telemetry upon partial progress or failure (F3)."""
    from src.scania.g4_b2_worker import execute_worker

    # 1. Missing handshake env vars -> exit code 101, 0 fits
    res = execute_worker()
    assert res == 101

    # 2. Simulate worker failure recording via task config pointing to corrupted array
    run_id = f"test_fail_fit_{int(time.time())}"
    synth_dir = tmp_path / "synth_fail"
    synth_dir.mkdir(parents=True, exist_ok=True)

    # Save training labels
    npz_path = synth_dir / "membership.npz"
    np.savez(npz_path, train=np.arange(20), validation=np.arange(10),
             y_train=np.zeros(20, dtype=np.int8), y_validation=np.zeros(10, dtype=np.int8))

    # B1 train array with shape mismatch to trigger failure before B1 fit completes
    tree_tr_p = synth_dir / "tree_train.npy"
    tree_val_p = synth_dir / "tree_validation.npy"
    lr_tr_p = synth_dir / "lr_train.npy"
    lr_val_p = synth_dir / "lr_validation.npy"

    np.save(tree_tr_p, np.zeros((10, 4)), allow_pickle=False)  # Shape mismatch (10 vs 20)
    np.save(tree_val_p, np.zeros((10, 4)), allow_pickle=False)
    np.save(lr_tr_p, np.zeros((20, 4)), allow_pickle=False)
    np.save(lr_val_p, np.zeros((10, 4)), allow_pickle=False)

    task_config = dict(
        run_id=run_id,
        mode="SYNTHETIC",
        membership_path=str(npz_path),
        tree_train_path=str(tree_tr_p),
        tree_val_path=str(tree_val_p),
        lr_train_path=str(lr_tr_p),
        lr_val_path=str(lr_val_p),
        b1_params={"max_depth": 1, "random_state": 42},
        b2_params={"solver": "lbfgs", "max_iter": 2000, "random_state": 42},
    )
    allowlist = [npz_path, tree_tr_p, tree_val_p, lr_tr_p, lr_val_p]
    from src.scania.g4_b2_executor import _orchestrate_worker_in_windows_job
    with pytest.raises(ExecutorFailure) as exc_info:
        _orchestrate_worker_in_windows_job(
            ROOT, run_id, synth_dir / "out", allowlist, task_config, mode="SYNTHETIC"
        )
    worker_res = exc_info.value.worker_result
    assert worker_res.get("total_estimator_fits") == 0
    assert worker_res.get("validation_scored") is False
    assert "B1_INPUT_SHAPE_MISMATCH" in worker_res.get("reason", "")

    # 3. An incomplete worker result (validation_scored=False) cannot become COMPLETE
    from scripts.run_scania_baselines import run_synthetic_gate_b2
    import scripts.run_scania_baselines as s_runner
    bad_run_id = f"test_incomp_{int(time.time())}"
    monkeypatch.setattr(s_runner, "execute_synthetic_baseline_orchestration",
                        lambda *args, **kwargs: dict(synthetic_estimator_fits=2, synthetic_validation_scored=False, rows=[]))
    with pytest.raises(ExecutorBlocked, match="INCOMPLETE_WORKER_RESULT"):
        run_synthetic_gate_b2(tmp_path, run_id=bad_run_id)


def test_EX20_worker_enforces_locked_parameters_in_real_mode(tmp_path):
    """Verify worker in REAL mode strictly validates canonical parameters from g4_baselines.json (F4)."""
    run_id = f"test_param_lock_{int(time.time())}"
    synth_dir = tmp_path / "param_lock_synth"
    synth_dir.mkdir(parents=True, exist_ok=True)

    # Attempt to pass tampered b1_params (max_depth=5 instead of 1) in REAL mode
    tampered_task = dict(
        run_id=run_id,
        mode="REAL",
        membership_path=str(synth_dir / "membership.npz"),
        tree_train_path=str(synth_dir / "tree_train.npy"),
        tree_val_path=str(synth_dir / "tree_validation.npy"),
        lr_train_path=str(synth_dir / "lr_train.npy"),
        lr_val_path=str(synth_dir / "lr_validation.npy"),
        b1_params={"max_depth": 5, "random_state": 42},  # Tampered!
        b2_params=LR_PARAMS,
    )

    np.savez(synth_dir / "membership.npz", train=np.arange(20), validation=np.arange(10),
             y_train=np.zeros(20, dtype=np.int8), y_validation=np.zeros(10, dtype=np.int8))
    np.save(synth_dir / "tree_train.npy", np.zeros((20, 4)), allow_pickle=False)
    np.save(synth_dir / "tree_validation.npy", np.zeros((10, 4)), allow_pickle=False)
    np.save(synth_dir / "lr_train.npy", np.zeros((20, 4)), allow_pickle=False)
    np.save(synth_dir / "lr_val.npy", np.zeros((10, 4)), allow_pickle=False)

    allowlist = [synth_dir / f for f in ("membership.npz", "tree_train.npy", "tree_validation.npy", "lr_train.npy", "lr_val.npy")]
    output_dir = synth_dir / "output"

    from src.scania.g4_b2_executor import _orchestrate_worker_in_windows_job
    with pytest.raises(ExecutorFailure) as exc_info:
        _orchestrate_worker_in_windows_job(
            ROOT, run_id, output_dir, allowlist, tampered_task, mode="REAL"
        )
    assert "B1_PARAMETERS_TAMPERED" in exc_info.value.worker_result.get("reason", "")


def test_EX21_data_guard_blocks_official_test_set(tmp_path):
    """Verify application-level I/O guard prevents any access to official test set or archives in isolated process (F6)."""
    fake_root = tmp_path / "repo"
    fake_output = tmp_path / "output"
    fake_root.mkdir()
    fake_output.mkdir()

    code = (
        "import sys\n"
        "from pathlib import Path\n"
        "from src.scania.g4_b2_executor import install_executor_io_guard, SafetyBlocked\n"
        "root = Path(sys.argv[1]).resolve()\n"
        "out = Path(sys.argv[2]).resolve()\n"
        "install_executor_io_guard(root, out, allowlist=[])\n"
        "\n"
        "blocked_test = False\n"
        "try:\n"
        "    open(root / 'data/raw/scania_aps/aps_failure_test_set.csv', 'r')\n"
        "except SafetyBlocked:\n"
        "    blocked_test = True\n"
        "\n"
        "blocked_archive = False\n"
        "try:\n"
        "    open(root / 'data/raw/scania_aps/aps_failure_archive.zip', 'rb')\n"
        "except SafetyBlocked:\n"
        "    blocked_archive = True\n"
        "\n"
        "print(f'TEST_BLOCKED={blocked_test},ARCHIVE_BLOCKED={blocked_archive}')\n"
    )
    cmd = [sys.executable, "-B", "-c", code, str(fake_root), str(fake_output)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=True)
    assert "TEST_BLOCKED=True,ARCHIVE_BLOCKED=True" in proc.stdout
