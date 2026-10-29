"""UCI acquisition: opaque archive, allowlisted Train/description members only."""
import io
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from .contracts import GateError, digest
from .data import safe_path

URL = "https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip"
ARCHIVE = "aps+failure+at+scania+trucks.zip"
SOURCES = {
    ARCHIVE: (56618034, "5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89"),
    "aps_failure_training_set.csv": (44669194, "bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da"),
    "aps_failure_description.txt": (4874, "57b1eb3c551a678ffc1c8112e5b34c566dd16457642563f58aeb3ca65beeb820"),
}


def verify(payload, name):
    size, sha = SOURCES[name]
    if len(payload) != size or digest(payload) != sha:
        raise GateError(f"SOURCE_MISMATCH: {name}; size={len(payload)}; sha256={digest(payload)}")
    return {"bytes": size, "sha256": sha}


def read_member(bundle, member):
    if member not in ("aps_failure_training_set.csv", "aps_failure_description.txt"):
        raise GateError("NO_TEST_ACCESS: archive member denied")
    return bundle.read(member)


def acquire(repository):
    raw = safe_path(Path(repository) / "data/raw/scania_aps", repository)
    raw.mkdir(parents=True, exist_ok=True)
    target = safe_path(raw / ARCHIVE, repository)
    downloaded = False
    if target.exists():
        archive = target.read_bytes()
    else:
        with urlopen(URL, timeout=60) as response:
            if response.geturl() != URL:
                raise GateError("UNEXPECTED_DOWNLOAD_REDIRECT")
            archive = response.read()
        verify(archive, ARCHIVE)
        with target.open("xb") as stream:
            stream.write(archive)
        downloaded = True
    records = {ARCHIVE: verify(archive, ARCHIVE)}
    with ZipFile(io.BytesIO(archive)) as bundle:
        # Never extractall, enumerate/open Test, or use a loader that merges partitions.
        for member in ("aps_failure_training_set.csv", "aps_failure_description.txt"):
            destination = safe_path(raw / member, repository)
            payload = destination.read_bytes() if destination.exists() else read_member(bundle, member)
            records[member] = verify(payload, member)
            if not destination.exists():
                with destination.open("xb") as stream:
                    stream.write(payload)
    return {"url": URL, "downloaded_archive": downloaded, "sources": records,
            "members_allowed": ["aps_failure_training_set.csv", "aps_failure_description.txt"],
            "official_test": "SEALED: no member content read/extracted"}
