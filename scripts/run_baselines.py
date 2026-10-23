"""G4 only: verify G3, pass synthetic tests, fit fixed B2 on Train, score Validation.

Example: .venv/Scripts/python.exe -X utf8 scripts/run_baselines.py --run-id g4_primary --publish
Each run writes a new directory, including failures. --publish creates the public
summary once; reproduction runs keep their own CSV without overwriting it.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.baselines import (  # noqa: E402
    BaselineFailure, LR_PARAMS, fit_b2_development, fixed_wear_actions, reactive_actions,
)
from src.cost_model import EvaluationInputError, vector  # noqa: E402
from src.data import FEATURES, RAW_SHA256, TARGET, canonical_json, select_features, sha256_bytes  # noqa: E402
from src.evaluation import evaluate_policy  # noqa: E402
from scripts.run_data_pipeline import array_digest  # noqa: E402

MANIFEST_HASH = "6dd33ba68c5a4d5d18b8db1fbe4d6f57f8dbfe667d96fe21d6d61bf62cf64522"
TEST_FILES = ["tests/test_cost_model.py", "tests/test_constraints.py", "tests/test_baselines.py",
              "tests/test_data_pipeline.py"]
SOURCE_FILES = ["src/cost_model.py", "src/constraints.py", "src/evaluation.py", "src/baselines.py",
                "scripts/run_baselines.py", "configs/baselines.yaml", *TEST_FILES,
                "src/data.py", "src/preprocessing.py", "scripts/run_data_pipeline.py",
                "configs/data_pipeline.yaml", "requirements.txt",
                "results/w2_g3/runs/g3_submission/run.json"]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def write_new(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)


def expected_config():
    return {"protocol": "W2-G4-C", "g3_artifacts": "data/processed/w2_g3/g3_submission",
            "g3_reference": "results/w2_g3/runs/g3_submission/run.json",
            "g3_manifest_sha256": MANIFEST_HASH, "raw_path": "data/raw/ai4i2020.csv",
            "cost": {"c_pm": 1.0, "c_f": 20.0, "eta": 0.8}, "capacity": 0.10,
            "seed": 42, "b1_threshold_minutes": 200, "b2_threshold": 0.5,
            "b2_params": LR_PARAMS, "post_calibration": False,
            "refit_train_validation": False, "evaluation_partition": "validation"}


def validate_config(config):
    # Compare canonical JSON too: reject booleans masquerading as numeric parameters.
    if canonical_json(config) != canonical_json(expected_config()):
        raise EvaluationInputError("Config differs from approved fixed G4 protocol")


@contextmanager
def development_access_guard(root):
    """Audit all Python opens under data/, denying every file outside four inputs.

    Raw is hashed as bytes only. No Test CSV, split_ids.json, saved model or array
    is opened. Guard is enabled only for this run, and never inspects denied files.
    """
    data_root = (root / "data").resolve()
    local = data_root / "processed/w2_g3/g3_submission"
    allowed = {data_root / "raw/ai4i2020.csv", local / "manifest.json",
               local / "train.csv", local / "validation.csv"}
    reads, active = [], [True]

    def audit(event, args):
        if not active[0] or event != "open" or not isinstance(args[0], (str, bytes)):
            return
        path = Path(args[0].decode() if isinstance(args[0], bytes) else args[0]).resolve()
        if path.is_relative_to(data_root):
            if path not in allowed:
                raise PermissionError("G4 forbids data access outside verified development inputs")
            reads.append(str(path.relative_to(root)).replace("\\", "/"))

    sys.addaudithook(audit)
    try:
        yield reads
    finally:
        active[0] = False


def load_development(local, reference):
    """Read only manifest + two dev CSVs, checking hashes/order before model use."""
    payload = (local / "manifest.json").read_bytes()
    expected = reference["stable"]
    if (sha256_bytes(payload) != reference["stable_manifest_sha256"]
            or json.loads(payload) != expected):
        raise EvaluationInputError("G3 local manifest mismatch")
    if expected["split"]["dataset_sha256"] != RAW_SHA256:
        raise EvaluationInputError("G3 dataset mismatch")
    frames = {}
    for name in ("train", "validation"):
        payload = (local / f"{name}.csv").read_bytes()
        if sha256_bytes(payload) != expected["split_csv_sha256"][name]:
            raise EvaluationInputError(f"{name} CSV hash mismatch")
        frame = pd.read_csv(io.BytesIO(payload))
        if tuple(frame.columns) != ("UDI", *FEATURES, TARGET):
            raise EvaluationInputError(f"{name} unexpected schema")
        if len(frame) != expected["split"]["sizes"][name]:
            raise EvaluationInputError(f"{name} row count mismatch")
        ids = frame["UDI"]
        if not pd.api.types.is_integer_dtype(ids.dtype) or not ids.is_unique:
            raise EvaluationInputError(f"{name} invalid UDI")
        if sha256_bytes(canonical_json(ids.tolist())) != expected["split"]["ordered_udi_sha256"][name]:
            raise EvaluationInputError(f"{name} ordered UDI hash mismatch")
        select_features(frame)
        vector(frame[TARGET], name + " target", binary=True)
        frames[name] = frame
    if set(frames["train"]["UDI"]) & set(frames["validation"]["UDI"]):
        raise EvaluationInputError("Train/Validation overlap")
    return frames


def unit_test_gate(directory):
    command = [sys.executable, "-X", "utf8", "-m", "pytest", *TEST_FILES,
               "-q", "-p", "no:cacheprovider", f"--junitxml={directory / 'tests.xml'}"]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    write_new(directory / "tests_stdout.txt", completed.stdout.encode("utf-8"))
    write_new(directory / "tests_stderr.txt", completed.stderr.encode("utf-8"))
    tree = ET.parse(directory / "tests.xml")
    counts = {k: sum(int(s.get(k, 0)) for s in tree.iter("testsuite"))
              for k in ("tests", "failures", "errors", "skipped")}
    result = {"command": command, "exit_code": completed.returncode, **counts,
              "runtime_seconds": time.perf_counter() - started,
              "fixture_data": "synthetic only; no real Test file access",
              "test_source_sha256": {p: sha256_bytes((ROOT / p).read_bytes()) for p in TEST_FILES}}
    write_new(directory / "unit_tests.json", canonical_json(result))
    if completed.returncode or counts["failures"] or counts["errors"] or counts["skipped"] or not counts["tests"]:
        raise EvaluationInputError("Synthetic unit test gate FAILED; no real baseline run")
    return result


def run(config_path, run_id, *, publish=False):
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run-id must be a new simple name")
    directory = ROOT / "results/w2_g4/runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    record = {"run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "command": [sys.executable, *sys.argv], "source_commit": git("rev-parse", "HEAD"),
              "working_tree_status_at_start": git("status", "--porcelain"),
              "python": sys.version, "platform": platform.platform(),
              "dependencies": dict(sorted((d.metadata["Name"], d.version)
                                          for d in importlib.metadata.distributions())),
              "warnings": [], "baseline_results": [],
              "test_evaluation_performed": False, "test_transform_performed": False,
              "test_labels_loaded": False, "threshold_search_performed": False,
              "post_calibration_performed": False, "refit_train_validation": False}
    accesses = []
    try:
        record["source_file_sha256"] = {p: sha256_bytes((ROOT / p).read_bytes()) for p in SOURCE_FILES}
        tracked = set(git("ls-files").splitlines())
        record["source_files_match_commit"] = (not bool(git("diff", "HEAD", "--", *SOURCE_FILES))
                                               and set(SOURCE_FILES).issubset(tracked))
        if not record["source_files_match_commit"]:
            raise EvaluationInputError("Commit exact source/config/tests before real baseline run")
        config_bytes = config_path.read_bytes()
        config = yaml.safe_load(config_bytes)
        validate_config(config)
        record.update(config=config, config_sha256=sha256_bytes(config_bytes), seed=42)
        reference = json.loads((ROOT / config["g3_reference"]).read_bytes())
        if (reference["status"] != "COMPLETE_G3" or reference["stable_manifest_sha256"] != MANIFEST_HASH
                or sha256_bytes(canonical_json(reference["stable"])) != MANIFEST_HASH):
            raise EvaluationInputError("G3 reference manifest is not the locked successful run")
        if platform.python_version() != reference["stable"]["python_version"] or sys.version_info[:2] != (3, 11):
            raise EvaluationInputError("Use the G3 Python 3.11.9 environment")
        for dependency in ("numpy", "pandas", "scipy", "scikit-learn", "joblib", "PyYAML"):
            if importlib.metadata.version(dependency) != reference["dependencies"][dependency]:
                raise EvaluationInputError(f"G3 dependency mismatch: {dependency}")
        pip_command = [sys.executable, "-X", "utf8", "-m", "pip", "check"]
        pip_result = subprocess.run(pip_command, capture_output=True, text=True, encoding="utf-8")
        record["pip_check"] = {"command": pip_command, "exit_code": pip_result.returncode,
                               "stdout": pip_result.stdout, "stderr": pip_result.stderr}
        if pip_result.returncode:
            raise EvaluationInputError("pip check failed")
        record["unit_tests"] = unit_test_gate(directory)
        if publish and (ROOT / "results/baseline_metrics.csv").exists():
            raise EvaluationInputError("Summary exists; reproduce without --publish, never overwrite")
        with development_access_guard(ROOT) as accesses:
            raw_digest = sha256_bytes((ROOT / config["raw_path"]).read_bytes())
            if raw_digest != RAW_SHA256:
                raise EvaluationInputError("Raw hash mismatch; raw bytes not parsed in G4")
            frames = load_development(ROOT / config["g3_artifacts"], reference)
            train, validation = frames["train"], frames["validation"]
            if len(train) != 6000 or len(validation) != 2000:
                raise EvaluationInputError("Locked G3 sizes must be 6000/2000")
            record.update(dataset_sha256=raw_digest, g3_manifest_sha256=MANIFEST_HASH,
                          development_partition_hashes={name: reference["stable"]["split"]["ordered_udi_sha256"][name]
                                                        for name in ("train", "validation")},
                          development_csv_hashes={name: reference["stable"]["split_csv_sha256"][name]
                                                  for name in ("train", "validation")})
            X_train, X_validation = select_features(train), select_features(validation)
            y = validation[TARGET].to_numpy()
            for name, action_function in (("B0", lambda: reactive_actions(len(y))),
                                          ("B1", lambda: fixed_wear_actions(X_validation))):
                baseline_start = time.perf_counter()
                actions = action_function()
                action_seconds = time.perf_counter() - baseline_start
                metrics = evaluate_policy(y, actions, **config["cost"])
                record["baseline_results"].append(dict(metrics, baseline=name, partition="validation",
                    status="COMPLETE", fit_seconds=0.0, prediction_seconds=action_seconds,
                    runtime_seconds=time.perf_counter() - baseline_start))
            baseline_start = time.perf_counter()
            fitted = fit_b2_development(X_train, train[TARGET].to_numpy(), X_validation)
            record["warnings"].extend(fitted["warnings"])
            model = fitted["model"]
            preprocessor = model.named_steps["preprocess"]
            hashes = {name: array_digest(preprocessor.transform(X))
                      for name, X in (("train", X_train), ("validation", X_validation))}
            if any(hashes[name] != reference["stable"]["preprocessing"]["lr"][name + "_array_sha256"]
                   for name in hashes):
                raise EvaluationInputError("B2 preprocessing differs from approved G3 output")
            metrics = evaluate_policy(y, fitted["actions"], fitted["probabilities"], **config["cost"])
            record["baseline_results"].append(dict(metrics, baseline="B2", partition="validation", status="COMPLETE",
                fit_seconds=fitted["fit_seconds"], prediction_seconds=fitted["prediction_seconds"],
                runtime_seconds=time.perf_counter() - baseline_start))
            record["b2"] = {"estimator_params": model.named_steps["model"].get_params(),
                            "n_iter": model.named_steps["model"].n_iter_.tolist(),
                            "fit_partition": "train", "fit_rows": len(train),
                            "preprocessing_matches_g3": True, "development_array_sha256": hashes,
                            "validation_probabilities_sha256": array_digest(fitted["probabilities"]),
                            "validation_actions_sha256": sha256_bytes(canonical_json(fitted["actions"].tolist()))}
        record["feasible_ranking"] = [r["baseline"] for r in sorted(record["baseline_results"],
                                    key=lambda r: r["total_cost"]) if r["feasible"]]
        stable_metrics = [{k: v for k, v in row.items() if not k.endswith("_seconds")}
                          for row in record["baseline_results"]]
        record["stable_result_sha256"] = sha256_bytes(canonical_json({
            "metrics": stable_metrics, "b2": record["b2"], "dataset": raw_digest,
            "manifest": MANIFEST_HASH, "config": record["config_sha256"]}))
        csv = pd.DataFrame(record["baseline_results"]).to_csv(index=False, lineterminator="\n").encode("utf-8")
        write_new(directory / "baseline_metrics.csv", csv)
        record["metrics_csv_sha256"] = sha256_bytes(csv)
        if publish:
            write_new(ROOT / "results/baseline_metrics.csv", csv)
        record["status"] = "COMPLETE_G4_VALIDATION"
    except Exception as exc:
        record.update(status="FAILED", error_type=type(exc).__name__, error=str(exc))
        if isinstance(exc, BaselineFailure):
            record["warnings"].extend(exc.warning_records)
            record["baseline_results"].append({"baseline": "B2", "status": "FAILED", "reason": str(exc)})
    record["data_file_opens"] = accesses
    record["runtime_seconds"] = time.perf_counter() - start
    write_new(directory / "run.json", canonical_json(record))
    print(json.dumps({"status": record["status"], "report": str(directory.relative_to(ROOT)),
                      "error": record.get("error"), "stable_result_sha256": record.get("stable_result_sha256")}))
    return 0 if record["status"] == "COMPLETE_G4_VALIDATION" else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/baselines.yaml")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.config, args.run_id, publish=args.publish))
