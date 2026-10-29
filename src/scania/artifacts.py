"""Exclusive evidence writes and stable code provenance."""
import json
from pathlib import Path

from .contracts import canonical, digest, object_hash


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value))


def code_digest(repository):
    root = Path(repository)
    files = sorted([*root.glob("src/scania/*.py"), *root.glob("scripts/run_scania_*.py"),
                    *root.glob("configs/scania/*")])
    return object_hash({p.relative_to(root).as_posix(): digest(p.read_bytes().replace(b"\r\n", b"\n"))
                        for p in files if p.is_file()})


def verify_artifacts(directory):
    root = Path(directory)
    manifest = json.loads((root / "checksums.json").read_text(encoding="utf-8"))
    return all((root / p).is_file() and digest((root / p).read_bytes()) == sha
               for p, sha in manifest.items())
