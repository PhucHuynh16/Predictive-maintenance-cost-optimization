"""Gate B1 only: mock-worker Job Object qualification or import-only pool probe.

No real fitting/scoring command. 4 GiB and 300 s remain proposed B2 values.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.scania.g4_b1_contract import SCENARIOS
from src.scania.g4_b1_supervisor import run_qualification


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=["qualify"])
    p.add_argument("--run-id", required=True)
    p.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    args = p.parse_args()
    path = run_qualification(ROOT, run_id=args.run_id, scenario=args.scenario)
    import json
    summary = json.loads((path / "run_summary.json").read_text(encoding="utf-8"))
    print(path.relative_to(ROOT).as_posix())
    print("B1 " + summary["status"] + "; B2 NOT AUTHORIZED; no model fits / no Validation scoring")
    return 0 if summary["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
