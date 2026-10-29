"""SC-G3-C runner: locked Train split and preprocessing only, no estimator."""
import argparse
import datetime
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import joblib
import numpy as np
from src.scania.contracts import (GateError, CONFIG_SHA256, SCHEMA_SHA256, canonical,
                                  digest, environment, object_hash, validate_config)
from src.scania.data import (array_hash, official_split, ordered_ids_hash, read_train,
                             safe_path, source_ids)
from src.scania.preprocessing import build_preprocessor
from src.scania.artifacts import code_digest, write_json


def run(repository=ROOT, run_id=None, expected_stable=None):
    root = Path(repository).resolve()
    run_id = run_id or (datetime.datetime.now(datetime.timezone.utc).strftime("run_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8])
    if Path(run_id).name != run_id or run_id in (".", ".."):
        raise GateError("INVALID_RUN_ID")
    public = safe_path(root / "results/scania_aps/g3" / run_id, root)
    public.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    report = {"run_id": run_id, "status": "RUNNING", "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "command": " ".join(["python", "scripts/run_scania_pipeline.py", *sys.argv[1:]]),
              "official_test": "SEALED", "model_fitted": False}
    events = []
    try:
        config = validate_config(json.loads((root / "configs/scania/g3_pipeline.json").read_text(encoding="utf-8")))
        # Freeze/verify actual environment and code before any official split/fit.
        report.update(environment=environment(), platform=platform.platform(),
                      source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip(),
                      worktree_clean=not bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root).strip()),
                      code_digest=code_digest(root), config_sha256=CONFIG_SHA256, schema_sha256=SCHEMA_SHA256)
        write_json(public / "environment.json", {"locked": environment(), "all_distributions":
                   {d.metadata["Name"]: d.version for d in distributions()}})
        write_json(public / "config.json", config)
        events.append("config/environment frozen and verified before source/split/fit")
        raw_dir = root / "data/raw/scania_aps"
        parsed = read_train(raw_dir / config["source"]["file"], raw_dir, root, config["source"])
        if int(np.sum(parsed.y == 1)) != 1000 or int(np.sum(parsed.y == 0)) != 59000:
            raise GateError("G2_CLASS_COUNTS_MISMATCH")
        events.append("only official Train opened; source size/hash/schema/tokens verified")
        train, val, audit = official_split(parsed)
        if len(train) != 48000 or len(val) != 12000:
            raise GateError("OFFICIAL_SPLIT_SIZE_MISMATCH")
        events.append("P03 zero duplicates/conflicts; single stratified seed42 split; coverage/disjoint verified")
        local_root = safe_path(root / "data/processed/scania_aps", root)
        local_root.mkdir(parents=True, exist_ok=True)
        membership = {"source_sha256": parsed.sha256, "schema_sha256": SCHEMA_SHA256,
                      "config_sha256": CONFIG_SHA256, "environment": environment(),
                      "train_ids": source_ids(train, parsed.sha256), "validation_ids": source_ids(val, parsed.sha256)}
        split_lock = local_root / "official_split.json"
        if split_lock.exists():
            if split_lock.read_bytes() != canonical(membership):
                raise GateError("FROZEN_SPLIT_MISMATCH: no overwrite or alternative split")
        else:
            write_json(split_lock, membership)
        local = local_root / run_id
        local.mkdir(exist_ok=False)
        with (local / "membership.npz").open("xb") as stream:
            np.savez(stream, train=train, validation=val, y_train=parsed.y[train], y_validation=parsed.y[val])
        tree = build_preprocessor("tree").fit(parsed.X[train])
        # LR adds a Train-only scaler; both imputers must learn identical statistics.
        from sklearn.base import clone
        lr = build_preprocessor("lr")
        lr.fit(parsed.X[train])
        arrays = {}
        for kind, pipeline in [("tree", tree), ("lr", lr)]:
            for partition, positions in [("train", train), ("validation", val)]:
                transformed = pipeline.transform(parsed.X[positions])
                if transformed.shape != (len(positions), 170) or not np.isfinite(transformed).all():
                    raise GateError("PREPROCESSING_OUTPUT_FAILURE")
                arrays[kind + "_" + partition] = array_hash(transformed)
                with (local / (kind + "_" + partition + ".npy")).open("xb") as stream:
                    np.save(stream, transformed, allow_pickle=False)
            with (local / (kind + "_preprocessor.joblib")).open("xb") as stream:
                joblib.dump(pipeline, stream)
        if not np.array_equal(tree.named_steps["imputer"].statistics_, lr.named_steps["imputer"].statistics_):
            raise GateError("TREE_LR_IMPUTER_MISMATCH")
        if hasattr(clone(lr).named_steps["imputer"], "statistics_"):
            raise GateError("CLONE_FITTED_STATE_LEAK")
        events.append("preprocessors fit Train48000 only; Validation transform only; finite170X; clone unfitted")
        stable = {"source_sha256": parsed.sha256, "schema_sha256": SCHEMA_SHA256,
                  "config_sha256": CONFIG_SHA256, "environment": environment(), "code_digest": report["code_digest"],
                  "train_ordered_ids_sha256": ordered_ids_hash(train, parsed.sha256),
                  "validation_ordered_ids_sha256": ordered_ids_hash(val, parsed.sha256),
                  "membership_sha256": object_hash(membership), "array_sha256": arrays,
                  "imputer_statistics_sha256": array_hash(tree.named_steps["imputer"].statistics_),
                  "scaler_mean_sha256": array_hash(lr.named_steps["scaler"].mean_),
                  "scaler_scale_sha256": array_hash(lr.named_steps["scaler"].scale_)}
        stable_digest = object_hash(stable)
        if expected_stable is not None and stable_digest != expected_stable:
            raise GateError("REPRODUCIBILITY_MISMATCH")
        write_json(public / "stable_manifest.json", {**stable, "stable_digest": stable_digest})
        report.update(status="PASS", stable_digest=stable_digest, rows={"train": len(train), "validation": len(val)},
                      classes={name: {"neg": int(np.sum(parsed.y[p] == 0)), "pos": int(np.sum(parsed.y[p] == 1))}
                               for name, p in [("train", train), ("validation", val)]},
                      duplicate_audit=audit, header_line_1based=parsed.header_line_1based,
                      preprocessing={"features": 170, "finite": True, "imputer_fit_rows": len(train),
                                     "scaler_fit_rows": int(lr.named_steps["scaler"].n_samples_seen_)})
    except Exception as exc:
        report.update(status="BLOCKED", error_type=type(exc).__name__,
                      error=str(exc).replace(str(root), "<workspace_root>"))
        events.append("STOP/BLOCKED; no policy/seed/version substitution")
        raise
    finally:
        report["runtime_seconds"] = time.perf_counter() - start
        report["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        write_json(public / "run_summary.json", report)
        with (public / "execution.txt").open("x", encoding="utf-8", newline="\n") as stream:
            stream.write("\n".join(events + ["status=" + report["status"]]) + "\n")
        write_json(public / "checksums.json", {p.name: digest(p.read_bytes()) for p in public.iterdir() if p.is_file()})
        print(public.relative_to(root).as_posix(), report["status"])
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id")
    parser.add_argument("--expect-stable", help="First run stable_digest for exact reproduction")
    args = parser.parse_args()
    run(run_id=args.run_id, expected_stable=args.expect_stable)
