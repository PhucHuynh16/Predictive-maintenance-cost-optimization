"""Phase 2 CLI Entry Point: Preflight, Synthetic Validation, Real Execution, and Figure Generation.

Usage:
  # 1. Read-only preflight check (0 fits, verifies Python, Optuna, G3 manifest, config hash):
  python -m scripts.run_scania_phase2 preflight

  # 2. Synthetic optimization test (verifies Optuna TPE, threshold search, fit counter, job object):
  python -m scripts.run_scania_phase2 synthetic --run-id phase2_synthetic_test_001

  # 3. Real authorized execution (requires verified Owner approval comment and authorization record):
  python -m scripts.run_scania_phase2 execute --run-id scania_phase2_rf_optuna_001

  # 4. Generate optimization figures from completed run:
  python -m scripts.run_scania_phase2 generate-figures --run-id scania_phase2_rf_optuna_001
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.scania.contracts import environment, digest
from src.scania.artifacts import code_digest
from src.scania.phase2_optimization import reconcile_durable_fit_markers
from src.scania.phase2_executor import (
    REPO_ROOT, ExecutorBlocked, ExecutorFailure,
    load_phase2_config, get_phase2_config_sha,
    execute_phase2_preflight_check, validate_phase2_authorization_record,
    verify_g3_artifacts_and_build_allowlist, orchestrate_phase2_worker_in_job,
    write_phase2_evidence_artifacts, verify_phase2_run,
    G3_ACCEPTED_STABLE_DIGEST, G3_ACCEPTED_MANIFEST_FILE_SHA256,
)


def run_preflight(root=ROOT) -> int:
    """Run read-only preflight verification without consuming any real fit budget."""
    print("Executing Phase 2 Read-Only Preflight Verification...")
    try:
        summary = execute_phase2_preflight_check(root)
        print("PREFLIGHT STATUS: SUCCESS")
        print(f"  Python version: {summary['python_version']}")
        print(f"  Optuna version: {summary['optuna_version']}")
        print(f"  Config SHA-256: {summary['phase2_config_sha256']}")
        print(f"  HEAD Commit:    {summary['head_commit']}")
        print(f"  G3 Manifest:    {summary['g3_summary']['source_sha256'][:16]}... (Verified)")
        print(f"  Official Test:  {summary['official_test']}")
        print(f"  Fits Consumed:  {summary['real_estimator_fits_consumed']}")
        print(json.dumps(summary, indent=2))
        return 0
    except Exception as exc:
        print(f"PREFLIGHT FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def run_synthetic_test(root=ROOT, run_id: str = "phase2_synthetic_test_001", n_trials: int = 5) -> int:
    """Run an isolated end-to-end synthetic optimization test using synthetic data."""
    print(f"Executing Phase 2 Synthetic Test ({run_id}, n_trials={n_trials})...")
    output_dir = Path(root) / "results/scania_aps/phase2" / run_id
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    task_config = {
        "mode": "SYNTHETIC",
        "n_trials": n_trials,
        "max_fits": n_trials,
        "seed": 42,
        "n_train": 100,
        "n_val": 40,
        "n_features": 4,
        "capacity_limit": 4,
    }

    config = load_phase2_config(root)
    env_info = environment()
    manifest_data = {
        "mode": "SYNTHETIC_TEST",
        "timestamp": time.time(),
        "config_sha256": get_phase2_config_sha(root),
    }

    try:
        allowlist = [output_dir]
        report = orchestrate_phase2_worker_in_job(
            root=Path(root),
            run_id=run_id,
            output_dir=output_dir,
            allowlist=allowlist,
            task_config=task_config,
            wall_seconds=60,
            ram_cap_bytes=1024 * 1024 * 1024,
            mode="SYNTHETIC",
        )

        checksums = write_phase2_evidence_artifacts(
            output_dir=output_dir,
            report=report,
            config=config,
            environment_dict=env_info,
            manifest_data=manifest_data,
        )

        verified = verify_phase2_run(output_dir)
        print("SYNTHETIC TEST STATUS: SUCCESS")
        print(f"  Completed trials: {report['n_trials_completed']}")
        print(f"  Estimator fits:   {report['synthetic_estimator_fits']}")
        print(f"  Peak RAM:         {report['measured_peak_ram_mb']:.2f} MB")
        print(f"  Wall seconds:     {report['measured_wall_seconds']:.2f} s")
        print(f"  Artifacts verified: {verified} ({len(checksums)} artifacts)")
        if report.get("best_trial"):
            bp = report["best_trial"].get("best_policy", {})
            print(f"  Best policy: cost={bp.get('total_cost')}, M={bp.get('M')}, tau={bp.get('threshold'):.4f}")
        return 0
    except Exception as exc:
        print(f"SYNTHETIC TEST FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


def run_phase2_real(root=ROOT, run_id: str = "scania_phase2_rf_optuna_001", g3_run_id: str = "official_20261029_04") -> int:
    """Execute authorized Phase 2 Real Constrained Optimization."""
    print(f"Initiating Phase 2 Real Execution for Run ID: {run_id}...")
    root = Path(root).resolve()
    output_dir = root / "results/scania_aps/phase2" / run_id

    # 1. Output directory must not already exist (fail-closed)
    if output_dir.exists():
        raise ExecutorBlocked(f"OUTPUT_DIRECTORY_ALREADY_EXISTS: {output_dir}")

    # 2. Locate authorization record
    auth_file = root / "configs/scania/authorizations" / f"{run_id}.json"
    if not auth_file.is_file():
        raise ExecutorBlocked(f"AUTHORIZATION_RECORD_NOT_FOUND: {auth_file}")

    # 3. Validate authorization record and GitHub Owner comment
    print("Validating GitHub Owner authorization record...")
    auth_record = validate_phase2_authorization_record(auth_file, expected_run_id=run_id, root=root, mode="REAL")
    print("Authorization verified successfully against GitHub comment and HEAD commit.")
    approved_limits = auth_record["approved_limits"]
    print(
        f"  Approved limits bound: max_trials={approved_limits['max_trials']}, "
        f"total_max_fits={approved_limits['total_max_fits']}, "
        f"wall_seconds={approved_limits['max_wall_seconds']}, "
        f"ram_mb={approved_limits['max_ram_mb']}"
    )

    # 4. Verify G3 artifacts and build allowlist
    print("Verifying G3 data artifacts and building I/O allowlist...")
    allowlist, g3_summary = verify_g3_artifacts_and_build_allowlist(root, g3_run_id)

    # 5. Build task config using exact approved limits (Fix 2: no silent overrides)
    cfg = load_phase2_config(root)
    processed_dir = root / "data/processed/scania_aps" / g3_run_id
    task_config = {
        "mode": "REAL",
        "n_trials": approved_limits["max_trials"],
        "max_fits": approved_limits["total_max_fits"],
        "seed": 42,
        "capacity_limit": 1200,
        "membership_path": str(processed_dir / "membership.npz"),
        "tree_train_path": str(processed_dir / "tree_train.npy"),
        "tree_val_path": str(processed_dir / "tree_validation.npy"),
    }

    env_info = environment()
    manifest_data = {
        "mode": "REAL",
        "phase": "PHASE_2_CONSTRAINED_OPTIMIZATION",
        "run_id": run_id,
        "g3_input_run": g3_run_id,
        "g3_stable_digest": G3_ACCEPTED_STABLE_DIGEST,
        "g3_manifest_file_sha256": G3_ACCEPTED_MANIFEST_FILE_SHA256,
        "phase2_config_sha256": get_phase2_config_sha(root),
        "code_digest": code_digest(root),
    }

    t0_exec = time.perf_counter()
    errors = []
    try:
        print("Launching isolated worker subprocess under Windows Job Object...")
        report = orchestrate_phase2_worker_in_job(
            root=root,
            run_id=run_id,
            output_dir=output_dir,
            allowlist=list(allowlist),
            task_config=task_config,
            wall_seconds=approved_limits["max_wall_seconds"],
            ram_cap_bytes=approved_limits["max_ram_mb"] * 1024 * 1024,
            mode="REAL",
        )
        report["status"] = "COMPLETE"
        report["lifecycle"] = "COMPLETE"
    except Exception as exc:
        err_msg = str(exc)
        print(f"EXECUTION_FAILED: {type(exc).__name__}: {err_msg}", file=sys.stderr)
        errors.append({"error_type": type(exc).__name__, "reason": err_msg})

        # FIX 2: Reconstruct confirmed started fits from durable markers on disk
        durable_dir = output_dir / "durable_fits"
        reconciled = reconcile_durable_fit_markers(durable_dir) if durable_dir.is_dir() else {}

        w_res = getattr(exc, "worker_result", None)
        if not w_res:
            w_res_file = output_dir / "worker_result.json"
            if w_res_file.is_file():
                try:
                    w_res = json.loads(w_res_file.read_text(encoding="utf-8"))
                except Exception:
                    w_res = {}
            else:
                w_res = {}

        started_fits = max(reconciled.get("started_fits", 0), w_res.get("started_estimator_fits", 0))
        completed_fits = max(reconciled.get("completed_fits", 0), w_res.get("completed_estimator_fits", 0))
        failed_fits = max(reconciled.get("failed_fits", 0), w_res.get("failed_estimator_fits", 0))
        interrupted_fits = reconciled.get("interrupted_or_unknown_fits", 0)
        fit_records = reconciled.get("fit_records") or w_res.get("fit_records", [])

        report = {
            "run_id": run_id,
            "mode": "REAL",
            "status": "FAILED",
            "lifecycle": "FAILED",
            "real_estimator_fits": started_fits,  # Reconstructed confirmed started fits: NEVER 0 if fits started!
            "started_estimator_fits": started_fits,
            "completed_estimator_fits": completed_fits,
            "failed_estimator_fits": failed_fits,
            "interrupted_or_unknown_fits": interrupted_fits,
            "n_trials_completed": w_res.get("n_trials_completed", completed_fits),
            "trials_records": w_res.get("trials_records", []),
            "fit_records": fit_records,
            "measured_wall_seconds": time.perf_counter() - t0_exec,
            "measured_peak_ram_mb": 0.0,
        }

    # 6. Write evidence artifacts
    checksums = write_phase2_evidence_artifacts(
        output_dir=output_dir,
        report=report,
        config=cfg,
        environment_dict=env_info,
        manifest_data=manifest_data,
        errors=errors,
    )

    if report["status"] == "COMPLETE":
        verified = verify_phase2_run(output_dir)
        if not verified:
            raise ExecutorBlocked(f"OUTPUT_VERIFICATION_FAILED: Run {run_id} failed checksum verification")
        print("PHASE 2 REAL EXECUTION COMPLETED SUCCESSFULLY!")
        print(f"  Real fits:          {report['real_estimator_fits']}")
        print(f"  Completed trials:   {report['n_trials_completed']}")
        print(f"  Measured wall time: {report['measured_wall_seconds']:.2f} s")
        print(f"  Peak RAM:           {report['measured_peak_ram_mb']:.2f} MB")
        if report.get("best_trial"):
            bp = report["best_trial"].get("best_policy", {})
            print(f"  Best Policy Cost:   {bp.get('total_cost')} (M={bp.get('M')}, tau={bp.get('threshold'):.4f})")
            print(f"  Benchmark vs B2:    {bp.get('total_cost')} vs 10230")
        return 0
    else:
        return 1


def run_generate_figures(root=ROOT, run_id: str = "scania_phase2_rf_optuna_001") -> int:
    """Generate optimization convergence and cost-vs-capacity trade-off figures from completed run."""
    from src.scania.phase2_visualization import (
        plot_phase2_optimization_convergence, plot_phase2_cost_vs_capacity_tradeoff
    )
    run_dir = Path(root) / "results/scania_aps/phase2" / run_id
    if not run_dir.is_dir():
        print(f"ERROR: Run directory not found: {run_dir}", file=sys.stderr)
        return 1

    study_file = run_dir / "optuna_study.json"
    if not study_file.is_file():
        print(f"ERROR: optuna_study.json not found in {run_dir}", file=sys.stderr)
        return 1

    study_data = json.loads(study_file.read_text(encoding="utf-8"))
    trials = study_data.get("trials", [])

    fig_dir = Path(root) / "figures/optimization"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: Convergence
    conv_path = fig_dir / "optimization_convergence.png"
    plot_phase2_optimization_convergence(trials, save_path=str(conv_path))
    print(f"Saved convergence plot to {conv_path}")

    # Figure 2: Trade-off
    best_trial = study_data.get("best_trial")
    if best_trial and best_trial.get("best_policy"):
        tradeoff_path = fig_dir / "cost_vs_capacity_tradeoff.png"
        plot_phase2_cost_vs_capacity_tradeoff(trials, best_trial, save_path=str(tradeoff_path))
        print(f"Saved cost vs capacity trade-off plot to {tradeoff_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["preflight", "synthetic", "execute", "generate-figures"])
    parser.add_argument("--run-id", default="scania_phase2_rf_optuna_001")
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--g3-run", default="official_20261029_04")
    args = parser.parse_args()

    if args.action == "preflight":
        return run_preflight(ROOT)
    elif args.action == "synthetic":
        return run_synthetic_test(ROOT, run_id=args.run_id, n_trials=args.trials)
    elif args.action == "execute":
        return run_phase2_real(ROOT, run_id=args.run_id, g3_run_id=args.g3_run)
    elif args.action == "generate-figures":
        return run_generate_figures(ROOT, run_id=args.run_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
