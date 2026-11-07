"""SC-G4 Gate A only: synthetic fixture validation or read-only real preflight.

No command for official fitting/scoring exists. Gate B requires a new owner task.
"""
import argparse
import json
from pathlib import Path
import sys
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.scania.contracts import object_hash, environment
from src.scania import baselines
from src.scania.g4_contract import (Blocked, CONFIG_SHA, code_digest, git, load_config,
                                    protected_snapshot, verify_frozen_inputs, verify_test_evidence)
from src.scania.g4_artifacts import EvidenceRun, summarize_junit, utc, verify_run
from src.scania.g4_b2_executor import execute_synthetic_baseline_orchestration, ExecutorBlocked


def run_gate_a(root=ROOT, *, run_id, mode, test_evidence=None):
    out = EvidenceRun(root, run_id)
    start = time.perf_counter()
    report = dict(run_id=run_id, mode=mode, status="RUNNING", lifecycle="RUNNING", started_utc=utc(),
                  gate_b_authorized=False, official_test="SEALED_UNTIL_G10",
                  real_estimator_fits=0, real_validation_scored=False,
                  thread_control="PROCESS_DEFAULT_GATE_B_POLICY_PENDING",
                  runtime={"load_verify_seconds": None, "fit_seconds": None, "predict_seconds": None,
                           "metrics_seconds": None, "total_seconds": None})
    events, errors, stage = [], [], "MODE_GATE"
    report["runtime_reasons"] = {key: "NOT_COMPUTED" for key in report["runtime"]}
    try:
        if mode not in {"SYNTHETIC_FIXTURE", "READ_ONLY_PREFLIGHT"}:
            raise Blocked("GATE_B_NOT_AUTHORIZED")
        stage = "CONFIG_ENVIRONMENT"
        config = load_config(root)
        report.update(code_digest=code_digest(root), config_sha256=CONFIG_SHA,
                      execution_base_commit=git(root, "rev-parse", "HEAD").decode().strip(),
                      worktree_clean=not bool(git(root, "status", "--porcelain").strip()))
        out.json("config.json", config)
        out.json("environment.json", environment())
        if mode == "READ_ONLY_PREFLIGHT":
            stage = "TEST_EVIDENCE"
            out.json("tests_summary.json", verify_test_evidence(root, test_evidence))
            stage = "READ_ONLY_INPUT_PREFLIGHT"
            inputs = verify_frozen_inputs(root)
            out.json("input_manifest.json", inputs)
            out.json("preflight.json", dict(status="VERIFIED_READ_ONLY", estimator_fit=False, validation_scored=False))
            # Recheck tracked assets; inputs were mmap/parsed only, never written.
            if protected_snapshot(root) != inputs["protected"]:
                raise Blocked("PROTECTED_POSTCHECK_MISMATCH")
            stable = dict(mode=mode, config_sha256=CONFIG_SHA, code_digest=report["code_digest"], inputs=inputs)
            report["runtime"]["load_verify_seconds"] = time.perf_counter() - start
            report["runtime_reasons"].pop("load_verify_seconds")
            report["status"] = "PREFLIGHT_VERIFIED_GATE_B_LOCKED"
        else:
            stage = "SYNTHETIC_FIXTURE"
            x, y, v, yv = baselines.synthetic_fixture()
            scores, model_runtime = {}, {}
            report["runtime"]["load_verify_seconds"] = time.perf_counter() - start
            report["runtime_reasons"].pop("load_verify_seconds")
            for name in ("B1", "B2"):
                stage = "SYNTHETIC_FIT_PREDICT_" + name
                scores[name], model_runtime[name] = baselines.fit_predict_synthetic(name, x, y, v,
                                                           mode="SYNTHETIC_FIXTURE")
            stage = "SYNTHETIC_METRICS"
            t = time.perf_counter()
            rows = baselines.fixed_policy_rows(yv, scores)
            report["runtime"].update(metrics_seconds=time.perf_counter() - t,
                                    fit_seconds=sum(r["fit_seconds"] for r in model_runtime.values()),
                                    predict_seconds=sum(r["predict_seconds"] for r in model_runtime.values()))
            for key in ("fit_seconds", "predict_seconds", "metrics_seconds"):
                report["runtime_reasons"].pop(key)
            model_runtime["B0"] = dict(fit_seconds=0, predict_seconds=0, reason="NOT_APPLICABLE",
                                       probability_model=False)
            report["synthetic_model_runtime"] = model_runtime
            out.json("baseline_metrics.json", dict(kind="SYNTHETIC_FIXTURE_NOT_REAL_RESULTS", rows=rows))
            out.csv("baseline_metrics.csv", rows)
            stable = dict(mode=mode, config_sha256=CONFIG_SHA, code_digest=report["code_digest"], rows=rows,
                          probabilities={k: object_hash(p.tolist()) for k, p in scores.items()})
            report["status"] = "SYNTHETIC_VALIDATED_NOT_PRODUCTION"
        out.json("stable_manifest.json", dict(**stable, stable_digest=object_hash(stable)))
        report["lifecycle"] = "COMPLETE"
        events.append("Gate A completed; Gate B remains locked; no real baseline results")
    except Exception as exc:
        status = "BLOCKED" if isinstance(exc, (Blocked, FileNotFoundError)) else "ERROR" if isinstance(exc, ValueError) else "FAILED"
        report.update(status=status, lifecycle="FAILED")
        errors.append(dict(stage=stage, error_type=type(exc).__name__, reason=str(exc).replace(str(Path(root)), "<repository>"),
                           warnings=getattr(exc, "warnings", []),
                           uncomputed_metrics=dict(value=None, reason="NOT_COMPUTED")))
        events.append("Stopped at " + stage + "; error evidence saved before re-raise")
        raise
    finally:
        report["ended_utc"] = utc()
        report["runtime"]["total_seconds"] = time.perf_counter() - start
        report["runtime_reasons"].pop("total_seconds", None)
        out.json("run_summary.json", report)
        out.json("failure_diagnostics.json", dict(errors=errors))
        out.text("execution.txt", "\n".join(events + ["status=" + report["status"]]) + "\n")
        out.finalize()
    return out.path


def write_gate_b2_evidence_artifacts(out, root, *, run_id, mode, config_obj, result, report):
    """Write complete, verifiable evidence artifacts required by verify_run().

    Required artifacts:
    - config.json
    - environment.json
    - stable_manifest.json
    - baseline_metrics.json
    - baseline_metrics.csv
    """
    out.json("config.json", config_obj)
    out.json("environment.json", environment())
    is_real = (mode == "GATE_B2_REAL_BASELINE")
    manifest_data = dict(
        run_id=run_id,
        mode=mode,
        synthetic=(not is_real),
        code_digest=code_digest(root),
        config_sha256=object_hash(config_obj) if isinstance(config_obj, dict) else str(config_obj),
        g3_run_id=report.get("g3_input_run") or "official_20261029_04",
        models=["B0", "B1", "B2"],
        cost_equation="10*FP + 500*FN",
        capacity_constraint="floor(N/10)",
        official_test_sealed=True,
    )
    out.json("stable_manifest.json", manifest_data)
    metrics_data = dict(
        run_id=run_id,
        mode=mode,
        kind="REAL_SCANIA_APS" if is_real else "SYNTHETIC_NOT_REAL",
        rows=result.get("rows"),
        fitted_estimator_count=result.get("real_estimator_fits" if is_real else "synthetic_estimator_fits", 0),
        observed_timings=result.get("observed_timings"),
        measured_peak_ram_mb=result.get("measured_peak_ram_mb"),
    )
    out.json("baseline_metrics.json", metrics_data)
    out.csv("baseline_metrics.csv", result.get("rows", []))


def run_gate_b2(root=ROOT, *, run_id, g3_run_id=None):
    """Fail-closed real baseline execution gate under Gate B2."""
    from src.scania.g4_b2_executor import execute_real_baseline_gate, ExecutorBlocked
    out = EvidenceRun(root, run_id)
    start = time.perf_counter()
    report = dict(
        run_id=run_id,
        mode="GATE_B2_REAL_BASELINE",
        status="BLOCKED",
        lifecycle="FAILED",
        started_utc=utc(),
        gate_b_authorized=False,
        official_test="SEALED_UNTIL_G10",
        real_estimator_fits=0,
        synthetic_estimator_fits=0,
        real_validation_scored=False,
        synthetic_validation_scored=False,
        g3_input_run=g3_run_id,
        thread_control="1_THREAD_LOCKED",
        runtime={"load_verify_seconds": None, "fit_seconds": None, "predict_seconds": None,
                 "metrics_seconds": None, "total_seconds": None},
        runtime_reasons={k: "NOT_COMPUTED" for k in ("load_verify_seconds", "fit_seconds", "predict_seconds", "metrics_seconds", "total_seconds")},
    )
    events, errors, stage = [], [], "GATE_B2_AUTHORIZATION"
    try:
        real_result = execute_real_baseline_gate(root, run_id, g3_run_id=g3_run_id, run_reservation=out)
        if "real_estimator_fits" not in real_result or "real_validation_scored" not in real_result:
            raise ExecutorBlocked("MALFORMED_WORKER_RESULT: Missing mandatory fit or scoring counts")
        if not real_result["real_validation_scored"]:
            raise ExecutorBlocked("INCOMPLETE_WORKER_RESULT: Validation was not scored")
        report.update(
            status="GATE_B2_SUCCESS",
            lifecycle="COMPLETE",
            gate_b_authorized=True,
            real_estimator_fits=real_result["real_estimator_fits"],
            synthetic_estimator_fits=0,
            real_validation_scored=real_result["real_validation_scored"],
            synthetic_validation_scored=False,
            rows=real_result.get("rows"),
            observed_timings=real_result.get("observed_timings"),
            measured_peak_ram_mb=real_result.get("measured_peak_ram_mb"),
        )
        events.append("Gate B2 baseline execution completed successfully")
        cfg_path = Path(root) / "configs/scania/g4_baselines.json"
        cfg_obj = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
        write_gate_b2_evidence_artifacts(out, root, run_id=run_id, mode="GATE_B2_REAL_BASELINE",
                                         config_obj=cfg_obj, result=real_result, report=report)
    except Exception as exc:
        status = "BLOCKED" if isinstance(exc, (Blocked, ExecutorBlocked, FileNotFoundError)) else "FAILED"
        report.update(status=status, lifecycle="FAILED")
        reason_str = str(exc).replace(str(Path(root)), "<repository>")

        # Collect available worker evidence before reporting (F3)
        worker_res = getattr(exc, "worker_result", {})
        if not worker_res and (out.path / "worker_result.json").is_file():
            try:
                worker_res = json.loads((out.path / "worker_result.json").read_text(encoding="utf-8"))
            except Exception:
                pass

        fits = worker_res.get("total_estimator_fits", 0)
        val_scored = worker_res.get("validation_scored", False)
        warnings_list = list(worker_res.get("warnings", []))
        if "telemetry" in worker_res:
            for m_info in worker_res["telemetry"].values():
                warnings_list.extend(m_info.get("warnings", []))

        report["real_estimator_fits"] = fits
        report["real_validation_scored"] = val_scored

        errors.append(dict(
            stage=stage,
            error_type=type(exc).__name__,
            reason=reason_str,
            real_estimator_fits=fits,
            synthetic_estimator_fits=0,
            real_validation_scored=val_scored,
            synthetic_validation_scored=False,
            official_test="SEALED_UNTIL_G10",
            warnings=warnings_list,
            partial_telemetry=worker_res.get("telemetry"),
        ))
        events.append(f"Stopped at {stage}: {reason_str}")
        raise
    finally:
        report["ended_utc"] = utc()
        report["runtime"]["total_seconds"] = time.perf_counter() - start
        report["runtime_reasons"].pop("total_seconds", None)
        out.json("run_summary.json", report)
        out.json("failure_diagnostics.json", dict(errors=errors))
        out.text("execution.txt", "\n".join(events + [f"status={report['status']}"]) + "\n")
        out.finalize()

        # Mandate: A run must not report COMPLETE unless mandatory worker evidence and output checks are valid
        if report.get("lifecycle") == "COMPLETE":
            if not verify_run(out.path):
                report["lifecycle"] = "FAILED"
                report["status"] = "BLOCKED"
                out.json("run_summary.json", report)
                out.finalize()
                raise ExecutorBlocked(f"OUTPUT_VERIFICATION_FAILED: Run {run_id} failed verify_run contract")
    return out.path


def run_synthetic_gate_b2(root=ROOT, *, run_id, synthetic_dir=None, wall_seconds=120):
    """Synthetic production-equivalent execution path under Gate B2 architecture."""
    out = EvidenceRun(root, run_id)
    start = time.perf_counter()
    report = dict(
        run_id=run_id,
        mode="GATE_B2_SYNTHETIC",
        status="BLOCKED",
        lifecycle="FAILED",
        started_utc=utc(),
        gate_b_authorized=False,
        official_test="SEALED_UNTIL_G10",
        real_estimator_fits=0,
        synthetic_estimator_fits=0,
        real_validation_scored=False,
        synthetic_validation_scored=False,
        thread_control="1_THREAD_LOCKED",
        runtime={"load_verify_seconds": None, "fit_seconds": None, "predict_seconds": None,
                 "metrics_seconds": None, "total_seconds": None},
        runtime_reasons={k: "NOT_COMPUTED" for k in ("load_verify_seconds", "fit_seconds", "predict_seconds", "metrics_seconds", "total_seconds")},
    )
    events, errors, stage = [], [], "SYNTHETIC_B2_EXECUTION"
    try:
        synth_result = execute_synthetic_baseline_orchestration(
            root, run_id, synthetic_dir=synthetic_dir, run_reservation=out, wall_seconds=wall_seconds
        )
        if "synthetic_estimator_fits" not in synth_result or "synthetic_validation_scored" not in synth_result:
            raise ExecutorBlocked("MALFORMED_WORKER_RESULT: Missing mandatory fit or scoring counts")
        if not synth_result["synthetic_validation_scored"]:
            raise ExecutorBlocked("INCOMPLETE_WORKER_RESULT: Validation was not scored")
        report.update(
            status="GATE_B2_SYNTHETIC_SUCCESS",
            lifecycle="COMPLETE",
            gate_b_authorized=False,
            real_estimator_fits=0,
            synthetic_estimator_fits=synth_result["synthetic_estimator_fits"],
            real_validation_scored=False,
            synthetic_validation_scored=synth_result["synthetic_validation_scored"],
            rows=synth_result.get("rows"),
            observed_timings=synth_result.get("observed_timings"),
            measured_peak_ram_mb=synth_result.get("measured_peak_ram_mb"),
        )
        events.append("Gate B2 synthetic execution completed successfully")
        synth_config = dict(
            mode="SYNTHETIC",
            run_id=run_id,
            thresholds={"PRIMARY": {"numerator": 1, "denominator": 2},
                        "SECONDARY": {"numerator": 10, "denominator": 510}},
            official_test="SEALED_UNTIL_G10"
        )
        write_gate_b2_evidence_artifacts(out, root, run_id=run_id, mode="GATE_B2_SYNTHETIC",
                                         config_obj=synth_config, result=synth_result, report=report)
    except Exception as exc:
        status = "BLOCKED" if isinstance(exc, (Blocked, ExecutorBlocked, FileNotFoundError)) else "FAILED"
        report.update(status=status, lifecycle="FAILED")
        reason_str = str(exc).replace(str(Path(root)), "<repository>")
        errors.append(dict(
            stage=stage,
            error_type=type(exc).__name__,
            reason=reason_str,
            real_estimator_fits=0,
            synthetic_estimator_fits=0,
            real_validation_scored=False,
            synthetic_validation_scored=False,
            official_test="SEALED_UNTIL_G10",
        ))
        events.append(f"Stopped at {stage}: {reason_str}")
        raise
    finally:
        report["ended_utc"] = utc()
        report["runtime"]["total_seconds"] = time.perf_counter() - start
        report["runtime_reasons"].pop("total_seconds", None)
        out.json("run_summary.json", report)
        out.json("failure_diagnostics.json", dict(errors=errors))
        out.text("execution.txt", "\n".join(events + [f"status={report['status']}"]) + "\n")
        out.finalize()

        # Mandate: A run must not report COMPLETE unless mandatory worker evidence and output checks are valid
        if report.get("lifecycle") == "COMPLETE":
            if not verify_run(out.path):
                report["lifecycle"] = "FAILED"
                report["status"] = "BLOCKED"
                out.json("run_summary.json", report)
                out.finalize()
                raise ExecutorBlocked(f"OUTPUT_VERIFICATION_FAILED: Run {run_id} failed verify_run contract")
    return out.path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["synthetic", "preflight", "tests", "summarize-tests", "gate-b2", "gate-b2-synthetic"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--test-evidence")
    parser.add_argument("--junit")
    parser.add_argument("--g3-run", default=None)
    args = parser.parse_args()
    if args.action == "tests":
        result, exit_code = run_tests(ROOT, args.run_id)
        print(Path(result).relative_to(ROOT).as_posix())
        return exit_code
    elif args.action == "summarize-tests":
        result = summarize_junit(ROOT, args.junit or "", args.run_id)
    elif args.action == "gate-b2":
        try:
            result = run_gate_b2(ROOT, run_id=args.run_id, g3_run_id=args.g3_run)
            print(Path(result).relative_to(ROOT).as_posix())
            return 0
        except Exception:
            return 1
    elif args.action == "gate-b2-synthetic":
        try:
            result = run_synthetic_gate_b2(ROOT, run_id=args.run_id)
            print(Path(result).relative_to(ROOT).as_posix())
            return 0
        except Exception:
            return 1
    else:
        result = run_gate_a(run_id=args.run_id, mode="SYNTHETIC_FIXTURE" if args.action == "synthetic"
                            else "READ_ONLY_PREFLIGHT", test_evidence=args.test_evidence)
    print(Path(result).relative_to(ROOT).as_posix())
    return 0


def run_tests(root, run_id):
    """Capture source BEFORE pytest; never bind historical XML to today's code."""
    root = Path(root).resolve()
    load_config(root)
    # Reserve a private local XML path; public summary remains small/sanitized.
    import re
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id): raise Blocked("INVALID_RUN_ID")
    local = root / "data/processed/scania_aps/g4/gate_a_tests"
    if local.resolve() != local.absolute(): raise Blocked("JUNIT_ALIAS")
    local.mkdir(parents=True, exist_ok=True)
    xml = local / (run_id + ".xml")
    if xml.exists(): raise Blocked("JUNIT_ALREADY_EXISTS")
    execution = dict(code_digest=code_digest(root), environment=environment(), started_utc=utc(),
                     execution_base_commit=git(root,"rev-parse","HEAD").decode().strip(),
                     worktree_clean=not bool(git(root,"status","--porcelain").strip()),
                     command="python -m pytest tests/scania -q -p no:cacheprovider --junitxml=<G4_LOCAL_XML>")
    proc = subprocess.run([sys.executable,"-m","pytest","tests/scania","-q","-p","no:cacheprovider",
                           "--junitxml="+str(xml)],cwd=root,
                          env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    execution["ended_utc"] = utc()
    execution["pytest_exit_code"] = proc.returncode
    if not xml.is_file():
        out = EvidenceRun(root, run_id)
        out.json("run_summary.json",dict(status="FAILED",lifecycle="FAILED",mode="TEST_EXECUTION"))
        out.json("failure_diagnostics.json",dict(reason="JUNIT_NOT_PRODUCED",exit_code=proc.returncode))
        out.text("execution.txt","pytest did not produce XML; no PASS\n")
        out.finalize()
        return out.path, proc.returncode or 1
    return summarize_junit(root,xml,run_id,execution), proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
