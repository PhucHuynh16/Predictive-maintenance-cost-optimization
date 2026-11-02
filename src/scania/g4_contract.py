"""Fail-closed Gate A contracts. Real inputs are read-only, never fit/scored."""
import json
import re
from pathlib import Path
import subprocess
import numpy as np
from .contracts import canonical, digest, object_hash, environment
from .data import array_hash, ordered_ids_hash, read_train
from .cost_model import binary_vector

BASE = "d78cfcd30601090211003ef3a6a6751f83dd6eb3"
ACCEPTED_HEAD = "0b01dc9fce1e3dbafd1770d481bd77b4098ba84b"
G3_RUN = "official_20261029_04"
G3_STABLE = "efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb"
CONFIG_SHA = "8b9cbbd2a14d23f256a677fc6a61eecf7dbf7c6261c78529670cbfddc00b88ad"
DOCS = {"docs/scania/decision_register.md", "docs/scania/experimental_protocol.md",
        "docs/scania/cost_model_review.md"}
SOURCE_FILES = ["src/scania/" + f + ".py" for f in
                ("cost_model", "constraints", "evaluation", "baselines", "g4_contract", "g4_artifacts")]
SOURCE_FILES += ["scripts/run_scania_baselines.py", "configs/scania/g4_baselines.json"]
SOURCE_FILES += ["tests/scania/test_" + f + ".py" for f in
                 ("cost_model", "constraints", "evaluation", "baselines", "g4_contract", "g4_runner", "pipeline")]


class Blocked(ValueError):
    """Preserve diagnostics; no estimator fit permitted after this gate."""


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root)


def content_bytes(path, payload):
    return payload if Path(path).suffix.lower() in {".png", ".jpg", ".pdf"} else payload.replace(b"\r\n", b"\n")


def code_digest(root):
    return object_hash({p: digest(content_bytes(p, (Path(root) / p).read_bytes())) for p in SOURCE_FILES})


def trusted_json(root, path):
    return json.loads(git(root, "show", BASE + ":" + path))


def load_config(root):
    value = json.loads((Path(root) / "configs/scania/g4_baselines.json").read_text(encoding="utf-8"))
    if object_hash(value) != CONFIG_SHA:
        raise Blocked("CONFIG_MISMATCH")
    if value["gate_b_authorized"] is not False or value["thresholds"] != {
            "PRIMARY": {"numerator": 1, "denominator": 2},
            "SECONDARY": {"numerator": 10, "denominator": 510}}:
        raise Blocked("GATE_B_NOT_AUTHORIZED_OR_POLICY_MISMATCH")
    if environment() != value["environment"]:
        raise Blocked("VERSION_MISMATCH")
    return value


def guarded_path(root, relative, allowed):
    """Only exact logical inputs, before stat/open; resolves junctions/symlinks."""
    if relative not in allowed or "\\" in relative or ".." in Path(relative).parts:
        raise Blocked("NO_TEST_ACCESS_OR_UNAPPROVED_PATH")
    root = Path(root).resolve()
    path = root / relative
    # Reject aliases even when they resolve to another in-workspace artifact.
    resolved = path.resolve()
    if resolved != root.joinpath(*Path(relative).parts).absolute() or not resolved.is_relative_to(root):
        raise Blocked("PATH_ALIAS_OR_ESCAPE")
    return resolved


def protected_snapshot(root):
    """All pre-existing tracked assets except the three authorized append-only docs."""
    names = git(root, "ls-tree", "-r", "--name-only", BASE).decode().splitlines()
    names = [n for n in names if n not in DOCS]
    query = "".join(BASE + ":" + n + "\n" for n in names).encode()
    proc = subprocess.run(["git", "cat-file", "--batch"], cwd=root, input=query,
                          stdout=subprocess.PIPE, check=True)
    payload, offset, hashes = proc.stdout, 0, {}
    for name in names:
        end = payload.index(b"\n", offset)
        size = int(payload[offset:end].split()[-1])
        expected = payload[end + 1:end + 1 + size]
        offset = end + size + 2
        actual = (Path(root) / name).read_bytes()
        if content_bytes(name, actual) != content_bytes(name, expected):
            raise Blocked("PROTECTED_ASSET_CHANGED: " + name)
        hashes[name] = digest(content_bytes(name, actual))
    return dict(files=len(hashes), digest=object_hash(hashes))


def validate_alignment(train, validation, y_train, y_validation, source_y, manifest):
    source_y = binary_vector(source_y, "source_labels")
    t, v = np.asarray(train), np.asarray(validation)
    if (t.ndim != 1 or v.ndim != 1 or not t.size or not v.size
            or t.dtype.kind not in "iu" or v.dtype.kind not in "iu"
            or not np.array_equal(np.sort(np.concatenate((t, v))), np.arange(len(source_y)))):
        raise Blocked("POSITIONS_COVERAGE_OR_DISJOINT_MISMATCH")
    for name, ids, labels in [("train", t, y_train), ("validation", v, y_validation)]:
        labels = binary_vector(labels, name + "_labels")
        if not np.array_equal(labels, source_y[ids]):
            raise Blocked("LABEL_SOURCE_ALIGNMENT_MISMATCH")
        if ordered_ids_hash(ids, manifest["source_sha256"]) != manifest[name + "_ordered_ids_sha256"]:
            raise Blocked("ORDERED_IDS_MISMATCH")
    return {name: digest(canonical({"shape": list(np.asarray(y).shape), "dtype": "|i1"}) +
                         np.asarray(y, dtype=np.int8).tobytes())
            for name, y in [("y_train", y_train), ("y_validation", y_validation)]}


def verify_test_evidence(root, relative):
    if not isinstance(relative, str) or not relative.startswith("results/scania_aps/g4/"):
        raise Blocked("TEST_EVIDENCE_MISSING")
    if Path(relative).name != "tests_summary.json":
        raise Blocked("TEST_EVIDENCE_PATH")
    p = guarded_path(root, relative, {relative})
    e = json.loads(p.read_text(encoding="utf-8"))
    groups = {"C01", "C02", "C03", "C04", "C05", "C06", "K01", "K02", "K03", "K04",
              "M01", "M02", "B01", "B02", "R01", "R02", *[f"G3{i:02d}" for i in range(1, 11)]}
    cases = e.get("cases", [])
    derived = {}
    for c in cases:
        if c.get("status") != "passed":
            raise Blocked("TEST_EVIDENCE_HAS_NONPASS_CASE")
        m = re.search(r"(?:^|_)(G3\d{2}|[CKMBR]\d{2})(?:_|$)", c.get("name", ""))
        if m: derived[m[1]] = derived.get(m[1], 0) + 1
    if (not cases or e.get("source_binding") != "CAPTURED_BEFORE_PYTEST"
            or e.get("execution", {}).get("pytest_exit_code") != 0
            or any(type(e.get(k)) is not int for k in ("passed", "failures", "errors", "skipped"))
            or e.get("passed") != len(cases)
            or e.get("kind") != "PYTEST_JUNIT" or e.get("code_digest") != code_digest(root)
            or e.get("config_sha256") != CONFIG_SHA or e.get("environment") != environment()
            or e.get("failures") != 0 or e.get("errors") != 0 or e.get("skipped") != 0
            or not groups.issubset(e.get("groups", {}))
            or any(e["groups"][g]["passed"] < 1 or derived.get(g) != e["groups"][g]["passed"] for g in groups)):
        raise Blocked("TEST_EVIDENCE_STALE_FAILED_OR_INCOMPLETE")
    return e


def verify_matrix(path, expected_hash, expected_shape):
    a = np.load(path, mmap_mode="r", allow_pickle=False)
    if (a.dtype != np.dtype("float64") or a.shape != expected_shape
            or not np.isfinite(a).all() or array_hash(a) != expected_hash):
        raise Blocked("FROZEN_MATRIX_MISMATCH")
    return True


def verify_frozen_inputs(root):
    root = Path(root).resolve()
    protected = protected_snapshot(root)
    prefix = "results/scania_aps/g3/" + G3_RUN + "/"
    manifest = trusted_json(root, prefix + "stable_manifest.json")
    if manifest["stable_digest"] != G3_STABLE or object_hash({k: v for k, v in manifest.items()
                                                            if k != "stable_digest"}) != G3_STABLE:
        raise Blocked("G3_MANIFEST_MISMATCH")
    checks = trusted_json(root, prefix + "checksums.json")
    expected_names = {"config.json", "environment.json", "execution.txt", "run_summary.json", "stable_manifest.json"}
    if set(checks) != expected_names:
        raise Blocked("G3_CHECKSUM_FILE_LIST")
    for name, sha in checks.items():
        rel = prefix + name
        if digest(guarded_path(root, rel, {prefix + n for n in expected_names}).read_bytes().replace(b"\r\n", b"\n")) != sha:
            raise Blocked("G3_PUBLIC_CHECKSUM_MISMATCH")
    cfg = trusted_json(root, "configs/scania/g3_pipeline.json")
    local = "data/processed/scania_aps/"
    rel = local + "official_split.json"
    membership = json.loads(guarded_path(root, rel, {rel}).read_text(encoding="utf-8"))
    if object_hash(membership) != manifest["membership_sha256"]:
        raise Blocked("MEMBERSHIP_HASH_MISMATCH")
    run = local + G3_RUN + "/"
    rel = run + "membership.npz"
    with np.load(guarded_path(root, rel, {rel}), allow_pickle=False) as z:
        if set(z.files) != {"train", "validation", "y_train", "y_validation"}:
            raise Blocked("MEMBERSHIP_MEMBER_LIST")
        train, val, yt, yv = [z[k].copy() for k in ("train", "validation", "y_train", "y_validation")]
    if (len(train), len(val)) != (48000, 12000):
        raise Blocked("PARTITION_SIZE_MISMATCH")
    raw = "data/raw/scania_aps/aps_failure_training_set.csv"
    # Exact known Train path only: no archive/Test fallback, no official_split call.
    parsed = read_train(guarded_path(root, raw, {raw}), root / "data/raw/scania_aps", root, cfg["source"])
    labels = validate_alignment(train, val, yt, yv, parsed.y, manifest)
    for name, positions in [("train", train), ("validation", val)]:
        if membership[name + "_ids"] != [[parsed.sha256, "train", int(i) + 1] for i in positions]:
            raise Blocked("MEMBERSHIP_POSITIONS_MISMATCH")
    for name, sha in manifest["array_sha256"].items():
        rel = run + name + ".npy"
        n = 48000 if name.endswith("_train") else 12000
        verify_matrix(guarded_path(root, rel, {rel}), sha, (n, 170))
    return dict(status="VERIFIED_READ_ONLY", g3_stable_digest=G3_STABLE,
                membership_sha256=manifest["membership_sha256"], label_hashes=labels,
                array_hashes=manifest["array_sha256"], protected=protected,
                source_sha256=parsed.sha256, train_rows=48000, validation_rows=12000,
                estimator_fit=False, validation_scored=False, official_test="SEALED")
