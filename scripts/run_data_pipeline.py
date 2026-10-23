"""Reproduce G3 only. No model fit, calibration, metrics or test-label summaries."""

from __future__ import annotations

import argparse
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

import joblib
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data import (  # noqa: E402
    DataGateError, DuplicateFeaturesError, FEATURES, RAW_SHA256, TARGET,
    acquire_raw, canonical_json, create_splits, dependence_report, duplicate_report,
    load_verified_raw, select_features, sha256_bytes, split_manifest, verify_hash,
)
from src.preprocessing import prepare_development  # noqa: E402


def validate_config(config):
    expected = {
        "protocol": "A5.1-A5.7", "raw_path": "data/raw/ai4i2020.csv",
        "raw_sha256": RAW_SHA256, "expected_rows": 10000, "features": list(FEATURES),
        "split": {"target": TARGET, "source_order": "UDI", "test_fraction_first": 0.2,
                  "validation_fraction_of_remaining": 0.25, "random_state_both_steps": 42,
                  "stratify": True},
        "preprocessing": {"type_encoder": "one_hot", "handle_unknown": "ignore",
                          "lr_numeric": "standard_scaler", "rf_numeric": "passthrough",
                          "missing": "error", "feature_engineering": False, "resampling": False},
    }
    if not isinstance(config, dict) or set(config) != {*expected, "dependence_review"}:
        raise DataGateError("Config must contain exactly the approved G3 keys")
    if any(config[key] != value for key, value in expected.items()):
        raise DataGateError("Config differs from the approved A5 protocol; stop for owner decision")
    review = config["dependence_review"]
    if (not isinstance(review, dict)
            or set(review) != {"dataset_sha256", "reviewed_for", "basis"}
            or review["dataset_sha256"] != RAW_SHA256
            or review["reviewed_for"] != "interpolation_with_known_order_dependence"
            or not isinstance(review["basis"], str) or not review["basis"].strip()):
        raise DataGateError("Missing dataset-bound dependence review")


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()


def array_digest(array):
    values = np.asarray(array, dtype="<f8", order="C")
    return sha256_bytes(canonical_json({"shape": list(values.shape), "dtype": "<f8"})
                        + values.tobytes(order="C"))


def write_new(path, payload):
    with path.open("xb") as stream:
        stream.write(payload)


def run(config_path: Path, run_id: str, *, audit_only=False) -> int:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("run-id must be a simple new name, without path separators")
    directory = ROOT / "results" / "w2_g3" / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=False)  # Preserve every prior run, including failures.
    started = time.perf_counter()
    source_paths = ["src/data.py", "src/preprocessing.py", "scripts/run_data_pipeline.py",
                    "configs/data_pipeline.yaml", "requirements.txt"]
    record = {
        "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "command": [sys.executable, *sys.argv],
        "source_commit": git("rev-parse", "HEAD"),
        "working_tree_status_at_start": git("status", "--porcelain"),
        "source_files_match_commit": not bool(git("diff", "HEAD", "--", *source_paths)),
        "source_file_sha256": {p: sha256_bytes((ROOT / p).read_bytes()) for p in source_paths},
        "python": sys.version, "platform": platform.platform(),
        "dependencies": dict(sorted((d.metadata["Name"], d.version)
                                     for d in importlib.metadata.distributions())),
        "test_evaluation_performed": False, "test_transform_performed": False,
    }
    try:
        if sys.version_info[:2] != (3, 11):
            raise DataGateError("Use the project's separate Python 3.11 environment")
        config_bytes = config_path.read_bytes()
        config = yaml.safe_load(config_bytes)
        validate_config(config)
        record["config_sha256"] = sha256_bytes(config_bytes)
        raw_path = ROOT / config["raw_path"]
        record["acquisition"] = acquire_raw(raw_path)
        frame = load_verified_raw(raw_path)
        record["audit"] = {
            "dataset_sha256": RAW_SHA256, "rows": len(frame), "columns": list(frame.columns),
            "dtypes": {name: str(dtype) for name, dtype in frame.dtypes.items()},
            "missing_values": int(frame.isna().sum().sum()),
            "source_udi_order_valid": True, "binary_label_format_valid": True,
            "duplicates": duplicate_report(frame), "dependence": dependence_report(frame),
        }
        if record["audit"]["duplicates"]["duplicate_groups"]:
            raise DuplicateFeaturesError(record["audit"]["duplicates"])
        record["dependence_review"] = config["dependence_review"]
        if audit_only:
            record["status"] = "AUDIT_ONLY_NO_SPLIT"
        else:
            parts = create_splits(frame, dependence_reviewed=True)
            ids, manifest = split_manifest(frame, parts, RAW_SHA256)
            if manifest["sizes"] != {"train": 6000, "validation": 2000, "test": 2000}:
                raise DataGateError("Unexpected approved split sizes; do not retry another seed")
            # No Test labels or features go into preprocessing development functions.
            development = prepare_development(
                select_features(frame.iloc[parts["train"]]),
                select_features(frame.iloc[parts["validation"]]),
            )
            local = ROOT / "data" / "processed" / "w2_g3" / run_id
            local.mkdir(parents=True, exist_ok=False)
            split_file_hashes = {}
            for name, positions in parts.items():
                # All datasets including Test stay local/ignored. No auxiliary labels are copied.
                payload = frame.iloc[positions].loc[:, ["UDI", *FEATURES, TARGET]].to_csv(
                    index=False, lineterminator="\n").encode("utf-8")
                write_new(local / f"{name}.csv", payload)
                split_file_hashes[name] = sha256_bytes(payload)
            write_new(local / "split_ids.json", canonical_json(ids))
            preprocessing = {}
            for kind, (preprocessor, train, validation) in development.items():
                buffer = io.BytesIO()
                joblib.dump(preprocessor, buffer)
                write_new(local / f"{kind}_preprocessor.joblib", buffer.getvalue())
                for name, values in (("train", train), ("validation", validation)):
                    with (local / f"{kind}_{name}.npy").open("xb") as stream:
                        np.save(stream, values, allow_pickle=False)
                preprocessing[kind] = {
                    "fit_partition": "train", "fit_ordered_udi_sha256": manifest["ordered_udi_sha256"]["train"],
                    "fit_rows": len(train), "validation_rows_transformed": len(validation),
                    "input_features": list(FEATURES),
                    "output_features": preprocessor.get_feature_names_out().tolist(),
                    "train_array_sha256": array_digest(train),
                    "validation_array_sha256": array_digest(validation),
                    "test_transformed": False,
                }
            stable = {"audit": record["audit"], "split": manifest,
                      "split_csv_sha256": split_file_hashes, "preprocessing": preprocessing,
                      "config_sha256": record["config_sha256"],
                      "python_version": platform.python_version(),
                      "sklearn_version": importlib.metadata.version("scikit-learn")}
            write_new(local / "manifest.json", canonical_json(stable))
            record.update(status="COMPLETE_G3", stable=stable,
                          stable_manifest_sha256=sha256_bytes(canonical_json(stable)),
                          local_artifacts=str(local.relative_to(ROOT)).replace("\\", "/"))
        verify_hash(raw_path.read_bytes(), RAW_SHA256)
    except Exception as exc:
        record.update(status="BLOCKED" if isinstance(exc, DataGateError) else "FAILED",
                      error_type=type(exc).__name__, error=str(exc))
    record["runtime_seconds"] = time.perf_counter() - started
    write_new(directory / "run.json", canonical_json(record))
    print(json.dumps({"status": record["status"], "report": str(directory.relative_to(ROOT)),
                      "error": record.get("error"),
                      "stable_manifest_sha256": record.get("stable_manifest_sha256")}, ensure_ascii=False))
    return 0 if record["status"] in {"COMPLETE_G3", "AUDIT_ONLY_NO_SPLIT"} else 2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/data_pipeline.yaml")
    parser.add_argument("--run-id", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    parser.add_argument("--audit-only", action="store_true")
    args = parser.parse_args()
    raise SystemExit(run(args.config, args.run_id, audit_only=args.audit_only))
