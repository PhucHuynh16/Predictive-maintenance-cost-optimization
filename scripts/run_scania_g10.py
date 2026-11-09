"""CLI Entry Point for Scania APS Gate G10: Final Official Test Evaluation.

Subcommands:
  preflight : Run preflight checks on git, G3 data, config, and environment.
  synthetic : Run full end-to-end evaluation on synthetic data (0 touches of Official Test).
  execute   : Execute real evaluation on Official Test (requires authentic GitHub approval).
  verify    : Verify manifest checksums and integrity of G10 evaluation results.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.scania.g10_evaluation import (
    TARGET_RUN_ID,
    run_g10_preflight,
    execute_g10_evaluation,
    load_g10_config,
    get_g10_config_sha,
)
from src.scania.contracts import digest


def cmd_preflight(args):
    print("=" * 60)
    print("SCANIA APS — GATE G10 PREFLIGHT VERIFICATION")
    print("=" * 60)
    cfg = load_g10_config(REPO_ROOT)
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)
    auth_file = REPO_ROOT / f"configs/scania/authorizations/{target_run_id}.json"
    summary = run_g10_preflight(root=REPO_ROOT, auth_path=auth_file)
    print(json.dumps(summary, indent=2))
    print("-" * 60)
    if summary["status"] == "PREFLIGHT_PASS":
        print("[PASS] Preflight checks passed successfully.")
        return 0
    else:
        print(f"[{summary['status']}] Preflight warnings/issues detected.")
        return 1


def cmd_synthetic(args):
    print("=" * 60)
    print("SCANIA APS — GATE G10 SYNTHETIC PIPELINE TEST")
    print("=" * 60)
    print("Testing end-to-end evaluation pipeline with SYNTHETIC test data.")
    print("Official Test set remains STRICTLY SEALED.")
    print("-" * 60)

    cfg = load_g10_config(REPO_ROOT)
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_output = Path(tmpdir) / target_run_id
        result = execute_g10_evaluation(
            root=REPO_ROOT,
            mode="SYNTHETIC",
            override_output_dir=tmp_output,
        )
        print("[SUCCESS] Synthetic evaluation completed successfully.")
        print(json.dumps(result, indent=2))
    return 0


def cmd_execute(args):
    print("=" * 60)
    print("SCANIA APS — GATE G10 OFFICIAL TEST EXECUTION")
    print("=" * 60)
    cfg = load_g10_config(REPO_ROOT)
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)
    output_dir = REPO_ROOT / "results/scania_aps/g10" / target_run_id
    if output_dir.exists():
        print(f"[BLOCKED] Output directory already exists: {output_dir}")
        print("Re-running evaluation over existing results is prohibited.")
        return 2

    try:
        result = execute_g10_evaluation(root=REPO_ROOT, mode="REAL")
        print("[SUCCESS] Gate G10 Official Test evaluation completed successfully.")
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"[BLOCKED / FAILED] Execution halted: {exc}", file=sys.stderr)
        return 1


def cmd_verify(args):
    print("=" * 60)
    print("SCANIA APS — GATE G10 ARTIFACT & MANIFEST VERIFICATION")
    print("=" * 60)
    cfg = load_g10_config(REPO_ROOT)
    target_run_id = cfg.get("target_run_id", TARGET_RUN_ID)
    run_dir = REPO_ROOT / "results/scania_aps/g10" / target_run_id
    if not run_dir.exists():
        print(f"[ERROR] Run directory not found: {run_dir}")
        return 1

    manifest_file = run_dir / "stable_manifest.json"
    if not manifest_file.is_file():
        print(f"[ERROR] Manifest file missing: {manifest_file}")
        return 1

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    mismatches = []
    checked = 0

    for rel_path, expected_hash in manifest.items():
        p = run_dir / rel_path
        if not p.is_file():
            mismatches.append(f"MISSING: {rel_path}")
            continue
        content = p.read_bytes().replace(b"\r\n", b"\n")
        actual_hash = digest(content)
        if actual_hash != expected_hash:
            mismatches.append(f"HASH_MISMATCH: {rel_path} (expected {expected_hash}, got {actual_hash})")
        checked += 1

    if mismatches:
        print(f"[FAILED] Integrity verification failed ({len(mismatches)} errors):")
        for m in mismatches:
            print(f"  - {m}")
        return 1

    print(f"[PASS] All {checked} artifacts verified against stable manifest.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Scania APS Gate G10 Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("preflight", help="Run preflight integrity checks")
    subparsers.add_parser("synthetic", help="Run synthetic pipeline evaluation test")
    subparsers.add_parser("execute", help="Execute real evaluation on Official Test")
    subparsers.add_parser("verify", help="Verify G10 artifacts against manifest")

    args = parser.parse_args()

    if args.command == "preflight":
        sys.exit(cmd_preflight(args))
    elif args.command == "synthetic":
        sys.exit(cmd_synthetic(args))
    elif args.command == "execute":
        sys.exit(cmd_execute(args))
    elif args.command == "verify":
        sys.exit(cmd_verify(args))


if __name__ == "__main__":
    main()
