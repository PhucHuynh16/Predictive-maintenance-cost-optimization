"""Gate A evidence, independent of immutable G3 writer/digest implementation."""
import csv
import datetime
import io
import json
import os
from pathlib import Path
import re
import uuid
import xml.etree.ElementTree as ET
from .contracts import canonical, digest, environment
from .g4_contract import CONFIG_SHA, Blocked, code_digest, git


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class EvidenceRun:
    def __init__(self, repository, run_id):
        root = Path(repository).resolve()
        if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
            raise Blocked("INVALID_RUN_ID")
        base = root / "results/scania_aps/g4"
        if base.resolve() != base.absolute():
            raise Blocked("OUTPUT_ALIAS_OR_ESCAPE")
        base.mkdir(parents=True, exist_ok=True)
        self.path = base / run_id
        try:
            self.path.mkdir(exist_ok=False)
        except FileExistsError:
            attempt = EvidenceRun(root, "collision_" + uuid.uuid4().hex)
            attempt.json("failure_diagnostics.json", dict(reason="RUN_ID_EXISTS", requested_run_id=run_id))
            attempt.json("run_summary.json", dict(status="BLOCKED", lifecycle="FAILED", mode="NO_EXECUTION"))
            attempt.text("execution.txt", "RUN_ID_EXISTS: previous run preserved\n")
            attempt.finalize()
            raise Blocked("RUN_ID_EXISTS")
        self.reservation_token = uuid.uuid4().hex
        self._reserved_root = root
        self._reserved_run_id = run_id
        self._reserved_pid = os.getpid()

    def validate_reservation_contract(self, expected_root, expected_run_id):
        expected_root = Path(expected_root).resolve()
        if self._reserved_run_id != expected_run_id:
            raise Blocked(f"RESERVATION_RUN_ID_MISMATCH: {self._reserved_run_id} != {expected_run_id}")
        if self._reserved_root.resolve() != expected_root:
            raise Blocked("RESERVATION_ROOT_MISMATCH")
        if self._reserved_pid != os.getpid():
            raise Blocked("RESERVATION_PID_MISMATCH")
        if not self.path.is_dir():
            raise Blocked("RESERVATION_DIRECTORY_NOT_FOUND")
        return True

    def _file(self, name):
        if not re.fullmatch(r"[a-z0-9_]+\.(json|txt|csv)", name):
            raise Blocked("OUTPUT_FILENAME_NOT_ALLOWED")
        return self.path / name

    def text(self, name, value):
        with self._file(name).open("xb") as f:
            f.write(value.replace("\r\n", "\n").encode("utf-8"))

    def json(self, name, value):
        self.text(name, canonical(value).decode("utf-8"))

    def csv(self, name, rows):
        stream = io.StringIO(newline="")
        fields = list(rows[0])
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v
                             for k, v in r.items()})
        self.text(name, stream.getvalue())

    def finalize(self):
        files = list(self.path.iterdir())
        self.json("checksums.json", {p.name: digest(p.read_bytes().replace(b"\r\n", b"\n")) for p in sorted(files) if p.is_file()})


def verify_run(path):
    path = Path(path)
    manifest = json.loads((path / "checksums.json").read_text(encoding="utf-8"))
    if not {"run_summary.json", "failure_diagnostics.json", "execution.txt"}.issubset(manifest):
        return False
    if set(manifest) != {p.name for p in path.iterdir() if p.name != "checksums.json"}:
        return False
    for name, sha in manifest.items():
        if not re.fullmatch(r"[a-z0-9_]+\.(json|txt|csv)", name):
            return False
        p = path / name
        if p.resolve() != p.absolute() or not p.is_file() or digest(p.read_bytes().replace(b"\r\n", b"\n")) != sha:
            return False
    summary = json.loads((path / "run_summary.json").read_text(encoding="utf-8"))
    if summary["lifecycle"] == "COMPLETE":
        required = {"config.json", "environment.json", "stable_manifest.json"}
        if summary["mode"] == "SYNTHETIC_FIXTURE":
            required |= {"baseline_metrics.json", "baseline_metrics.csv"}
        elif summary["mode"] == "READ_ONLY_PREFLIGHT":
            required |= {"input_manifest.json", "preflight.json", "tests_summary.json"}
        elif summary["mode"] in {"GATE_B2_REAL_BASELINE", "GATE_B2_SYNTHETIC"}:
            required |= {"baseline_metrics.json", "baseline_metrics.csv"}
        else:
            return False
        return required.issubset(manifest)
    return summary["lifecycle"] == "FAILED" and summary["status"] in {"BLOCKED", "ERROR", "FAILED"}


def summarize_junit(root, junit_path, run_id, execution=None):
    root = Path(root).resolve()
    p = Path(junit_path).resolve()
    allowed = [(root / rel).resolve() for rel in ("results/scania_aps/g4", "data/processed/scania_aps/g4")]
    if not any(p.is_relative_to(a) for a in allowed) or p.suffix != ".xml":
        raise Blocked("JUNIT_PATH_NOT_ALLOWED")
    raw = p.read_bytes()
    tree = ET.fromstring(raw)
    cases = []
    groups = {}
    for c in tree.iter("testcase"):
        state = "passed"
        for tag in ("failure", "error", "skipped"):
            if c.find(tag) is not None: state = tag
        name = c.attrib["name"]
        match = re.search(r"(?:^|_)(G3\d{2}|[CKMBR]\d{2})(?:_|$)", name)
        if match:
            group = groups.setdefault(match[1], dict(passed=0, failure=0, error=0, skipped=0))
            group[state] += 1
        cases.append(dict(name=name, status=state, seconds=float(c.attrib.get("time", 0))))
    # Standalone conversion of historical XML cannot prove which source ran it.
    bound = execution is not None
    if bound and (execution["code_digest"] != code_digest(root) or execution["environment"] != environment()):
        raise Blocked("SOURCE_OR_ENV_CHANGED_DURING_TESTS")
    evidence = dict(kind="PYTEST_JUNIT" if bound else "UNBOUND_HISTORICAL_JUNIT",
                    code_digest=execution["code_digest"] if bound else None,
                    config_sha256=CONFIG_SHA if bound else None,
                    environment=execution["environment"] if bound else None,
                    execution_base_commit=execution["execution_base_commit"] if bound else None,
                    execution=execution, source_binding="CAPTURED_BEFORE_PYTEST" if bound else "NOT_CAPTURED",
                    failures=sum(c["status"] == "failure" for c in cases),
                    errors=sum(c["status"] == "error" for c in cases),
                    skipped=sum(c["status"] == "skipped" for c in cases),
                    passed=sum(c["status"] == "passed" for c in cases), groups=groups, cases=cases,
                    junit_bytes_sha256=digest(raw), raw_junit="LOCAL_G4_ONLY", captured_utc=utc(),
                    junit_suite_seconds=sum(float(t.attrib.get("time",0)) for t in tree.iter("testsuite")))
    run = EvidenceRun(root, run_id)
    run.json("tests_summary.json", evidence)
    run.json("run_summary.json", dict(status="TEST_EVIDENCE_CAPTURED", mode="JUNIT_SUMMARY", lifecycle="FAILED"
                                     if evidence["failures"] or evidence["errors"] else "EVIDENCE_ONLY"))
    run.json("failure_diagnostics.json", dict(errors=[]))
    run.text("execution.txt", "JUnit outcomes preserved; not a production or baseline PASS\n")
    run.finalize()
    return run.path
