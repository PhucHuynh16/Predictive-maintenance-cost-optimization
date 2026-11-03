"""Exclusive B1 records. Supervisor owns final publication; no G3 writer reuse."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from .g4_b1_contract import canonical, output_path, SafetyBlocked, sha


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    with Path(path).open("xb") as f:
        f.write(canonical(value)); f.flush(); os.fsync(f.fileno())


def append_event(path, value):
    with Path(path).open("ab") as f:
        f.write(canonical(value)); f.flush(); os.fsync(f.fileno())


FILES = {"config.json", "source_manifest.json", "environment.json", "reservation.json",
         "journal.jsonl", "worker_journal.jsonl", "worker_claim.json", "worker_result.json",
         "run_summary.json", "failure_diagnostics.json", "resource_usage.json", "checksums.json"}


class Evidence:
    def __init__(self, root, run_id):
        self.path = output_path(root, run_id)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Collision never reuses a successful record or releases its consumed slot.
        self.path.mkdir(exist_ok=False)
        write_json(self.path / "reservation.json", dict(run_id=run_id, started_utc=utc(),
                   kind="B1_INFRASTRUCTURE_ATTEMPT", real_fit_budget=0, slot_consumed=True))

    def json(self, name, value):
        if name not in FILES or name == "checksums.json":
            raise SafetyBlocked("EVIDENCE_FILENAME_NOT_ALLOWED")
        write_json(self.path / name, value)

    def event(self, stage, **extra):
        append_event(self.path / "journal.jsonl", dict(stage=stage, utc=utc(), **extra))

    def finalize(self):
        entries = list(self.path.iterdir())
        if any(p.name not in FILES or p.resolve() != p.absolute() or not p.is_file() for p in entries):
            raise SafetyBlocked("UNSAFE_EVIDENCE_MEMBER")
        write_json(self.path / "checksums.json", {p.name: sha(p.read_bytes()) for p in sorted(entries)})


def verify_evidence(path):
    """Checksums + required stage records, never equates FAILED diagnostics to PASS."""
    path = Path(path)
    try:
        if path.resolve() != path.absolute():
            return False
        checks = json.loads((path / "checksums.json").read_text(encoding="utf-8"))
        if not isinstance(checks, dict):
            return False
        required = {"reservation.json", "journal.jsonl", "run_summary.json", "failure_diagnostics.json", "resource_usage.json"}
        if not required.issubset(checks) or set(checks) != {p.name for p in path.iterdir() if p.name != "checksums.json"}:
            return False
        for name, digest in checks.items():
            if name not in FILES or name == "checksums.json":
                return False
            p = path / name
            if p.resolve() != p.absolute() or sha(p.read_bytes().replace(b"\r\n", b"\n")) != digest:
                return False
        summary = json.loads((path / "run_summary.json").read_text(encoding="utf-8"))
        if summary["real_estimator_fits"] != 0 or summary["validation_scored"] is not False:
            return False
        if summary["status"] == "PASS":
            return (summary["kind"] == "B1_SYNTHETIC_INFRASTRUCTURE_ONLY"
                    and summary["lifecycle"] == "COMPLETE" and summary["job_empty_verified"] is True
                    and {"worker_result.json", "config.json", "environment.json", "source_manifest.json"}.issubset(checks))
        return summary["status"] in {"BLOCKED", "FAILED", "ERROR"} and summary["lifecycle"] == "FAILED"
    except (OSError, ValueError, KeyError, TypeError):
        return False
