"""Acquire only owner-authorized Scania Train/description; no official Test reads."""
import datetime
from pathlib import Path
import sys
import time
import uuid
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.scania.acquisition import acquire
from src.scania.artifacts import write_json, code_digest
from src.scania.contracts import environment


def main():
    run = ROOT / "results/scania_aps/g3" / ("acquire_" + uuid.uuid4().hex[:12])
    run.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    report = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
              "code_digest": code_digest(ROOT), "environment": environment(),
              "command": "python scripts/run_scania_acquire.py"}
    try:
        report.update(acquire(ROOT))
        report["status"] = "PASS"
    except Exception as exc:
        report.update(status="BLOCKED", error_type=type(exc).__name__,
                      error=str(exc).replace(str(ROOT), "<workspace_root>"))
        raise
    finally:
        report["runtime_seconds"] = time.perf_counter() - start
        write_json(run / "acquisition.json", report)
        print(run.relative_to(ROOT).as_posix(), report["status"])


if __name__ == "__main__":
    main()
