"""B1 infrastructure contract. No data input or real experiment capability."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ACCEPTED = "67df203c99fb77ec1b0949a61a7780dd0eed6e2e"
DOC = "docs/scania/g4_execution.md"
NAMESPACE = "results/scania_aps/g4/gate_b1"
SOURCE_FILES = ["src/scania/g4_b1_" + n + ".py" for n in
                ("contract", "windows", "worker", "supervisor", "evidence")]
SOURCE_FILES += ["scripts/run_scania_gate_b1.py", "tests/scania/test_g4_b1.py"]
THREAD_ENV = {k: "1" for k in ("OMP_NUM_THREADS", "OMP_THREAD_LIMIT", "OPENBLAS_NUM_THREADS",
              "MKL_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}
THREAD_ENV.update(OMP_DYNAMIC="FALSE", MKL_DYNAMIC="FALSE")
SCENARIOS = {"normal", "crash", "sleep", "busy", "native_busy", "thread_probe", "child_attempt", "memory_limit"}


class SafetyBlocked(ValueError):
    pass


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def object_sha(value):
    return sha(canonical(value))


def real_execution_gate(*args, **kwargs):
    # No boolean, permit file, or profile may enable real fitting in this delivery.
    raise SafetyBlocked("GATE_B2_NOT_AUTHORIZED_NO_REAL_ENTRYPOINT")


def profile(scenario):
    if scenario not in SCENARIOS:
        raise SafetyBlocked("UNAPPROVED_SCENARIO_NO_DATA_ACCESS")
    return dict(kind="B1_SYNTHETIC_INFRASTRUCTURE_ONLY", scenario=scenario,
                wall_seconds=1.0 if scenario in {"sleep", "busy", "native_busy"} else 15.0,
                minimum_available_ram_bytes=64 * 1024**2,
                job_memory_bytes=512 * 1024**2, active_process_limit=2,
                cleanup_seconds=5.0, real_fitting_allowed=False,
                operational_policy=dict(minimum_ram_bytes=None, wall_seconds=None,
                                        approval="PENDING_OWNER_B2_VALUES"),
                thread_environment=dict(THREAD_ENV))


def validate_profile(value):
    if not isinstance(value, dict) or canonical(value) != canonical(profile(value.get("scenario"))):
        raise SafetyBlocked("INVALID_PROFILE_OR_UNAPPROVED_LIMIT")
    return value


def child_environment(parent=None):
    env = dict(os.environ if parent is None else parent)
    # No inherited Python code hooks or parallelism overrides enter the worker.
    for k in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(k, None)
    env.update(THREAD_ENV, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    return env


def output_path(root, run_id):
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,72}", run_id):
        raise SafetyBlocked("INVALID_RUN_ID")
    root = Path(root).resolve()
    p = root / NAMESPACE / run_id
    if p.resolve() != p.absolute() or not p.resolve().is_relative_to(root):
        raise SafetyBlocked("OUTPUT_ALIAS_OR_ESCAPE")
    return p


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def normalize(path, data):
    return data if Path(path).suffix in {".png", ".jpg", ".pdf"} else data.replace(b"\r\n", b"\n")


def protected_snapshot(root):
    root = Path(root)
    names = git(root, "ls-tree", "-r", "--name-only", ACCEPTED).decode().splitlines()
    query = "".join(ACCEPTED + ":" + n + "\n" for n in names).encode()
    data = subprocess.run(["git", "cat-file", "--batch"], cwd=root, input=query,
                          stdout=subprocess.PIPE, check=True).stdout
    hashes, offset = {}, 0
    for n in names:
        end = data.index(b"\n", offset)
        size = int(data[offset:end].split()[-1])
        expected = normalize(n, data[end + 1:end + 1 + size])
        offset = end + size + 2
        path = root / n
        if path.resolve() != path.absolute():
            raise SafetyBlocked("PROTECTED_PATH_ALIAS")
        actual = normalize(n, path.read_bytes())
        if actual != expected and not (n == DOC and actual.startswith(expected)):
            raise SafetyBlocked("PROTECTED_ASSET_CHANGED: " + n)
        hashes[n] = sha(actual)
    return dict(files=len(hashes), digest=object_sha(hashes))


def source_manifest(root):
    root = Path(root)
    files = {n: sha(normalize(n, (root / n).read_bytes())) for n in SOURCE_FILES}
    return dict(accepted_head=ACCEPTED, base_commit=git(root, "rev-parse", "HEAD").decode().strip(),
                working_tree_clean=not bool(git(root, "status", "--porcelain").strip()),
                files=files, source_digest=object_sha(files), source_commit=None,
                source_commit_reason="B1_COMMIT_NOT_AUTHORIZED_WORKING_TREE_SOURCE_HASHED")


def verify_pools(pools, inventory):
    if not isinstance(pools, list) or not pools or not isinstance(inventory, list) or not inventory:
        raise SafetyBlocked("THREAD_POOL_EVIDENCE_MISSING")
    if {p.get("user_api") for p in pools} != {"blas", "openmp"}:
        raise SafetyBlocked("MISSING_OR_UNKNOWN_RUNTIME_API")
    if any(type(p.get("num_threads")) is not int or p["num_threads"] != 1
           or not p.get("internal_api") or not p.get("filepath") for p in pools):
        raise SafetyBlocked("THREAD_POOL_NOT_VERIFIED_SINGLE")
    controlled = {str(Path(p["filepath"]).resolve()).casefold() for p in pools}
    loaded = {str(Path(p).resolve()).casefold() for p in inventory}
    if controlled != loaded:
        raise SafetyBlocked("UNACCOUNTED_NATIVE_RUNTIME")
    return True
