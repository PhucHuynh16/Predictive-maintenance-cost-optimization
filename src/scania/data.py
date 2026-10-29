"""Strict official-Train parser, P03 stop gate and the single P04 split."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

import numpy as np
from sklearn.model_selection import train_test_split

from .contracts import FEATURES, GateError, digest, object_hash

NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


@dataclass
class ParsedTrain:
    X: np.ndarray
    y: np.ndarray
    sha256: str
    header_line_1based: int
    features: tuple


def safe_path(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    if not path.is_relative_to(root):
        raise GateError("PATH_OUTSIDE_CODEX_WORKSPACE")
    return path


def read_train(path, raw_dir, repository, source):
    """Whitelist before opening; never discover/read other CSVs or Test caches."""
    path = safe_path(path, repository)
    raw_dir = safe_path(raw_dir, repository)
    if path.parent != raw_dir or path.name != "aps_failure_training_set.csv":
        raise GateError("NO_TEST_ACCESS: only the official Train path is accepted")
    payload = path.read_bytes()
    if len(payload) != source["bytes"] or digest(payload) != source["sha256"]:
        raise GateError("SOURCE_HASH_OR_SIZE_MISMATCH")
    return parse_train(payload, FEATURES, source["rows"])


def parse_train(payload, features=FEATURES, expected_rows=60000):
    """UTF-8 without BOM; trim outer tokens as G2, never coerce invalid tokens."""
    if payload.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
        raise GateError("BOM_NOT_ALLOWED")
    try:
        lines = payload.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as exc:
        raise GateError("INVALID_UTF8") from exc
    header_index = None
    for i, line in enumerate(lines):
        tokens = tuple(t.strip() for t in line.split(","))
        if "class" in tokens:
            if tokens != ("class", *features) or len(set(tokens)) != len(tokens):
                raise GateError("SCHEMA_MISMATCH: ordered numeric whitelist")
            header_index = i
            break
    if header_index is None:
        raise GateError("HEADER_MISSING")
    rows = lines[header_index + 1:]
    if len(rows) != expected_rows or expected_rows == 0:
        raise GateError("ROW_COUNT_MISMATCH")
    X = np.full((len(rows), len(features)), np.nan, dtype=np.float64)
    y = np.empty(len(rows), dtype=np.int8)
    for r, line in enumerate(rows):
        tokens = [t.strip() for t in line.split(",")]
        if len(tokens) != len(features) + 1:
            raise GateError(f"ROW_WIDTH_MISMATCH: data row {r + 1}")
        if tokens[0] not in ("neg", "pos"):
            raise GateError(f"INVALID_TARGET: data row {r + 1}")
        y[r] = int(tokens[0] == "pos")
        for c, token in enumerate(tokens[1:]):
            if token == "na":
                continue
            if not NUMBER.fullmatch(token):
                raise GateError(f"INVALID_NUMERIC_TOKEN: row {r + 1}, column {c + 1}")
            try:
                value = float(token)
                # Reject overflow, underflow and decimal distinctions lost by float64.
                # Decimal spelling differences such as 1/1.0 remain equivalent.
                if not np.isfinite(value) or Decimal(str(value)) != Decimal(token):
                    raise GateError(f"NUMERIC_PRECISION_OR_RANGE: row {r + 1}, column {c + 1}")
            except (ValueError, InvalidOperation, OverflowError) as exc:
                if isinstance(exc, GateError):
                    raise
                raise GateError("INVALID_NUMERIC") from exc
            X[r, c] = 0.0 if value == 0 else value
    return ParsedTrain(X, y, digest(payload), header_index + 1, tuple(features))


def duplicate_audit(data):
    """Hash buckets plus equality verification; missing mask is part of exact X."""
    buckets = {}
    groups = []
    for r, row in enumerate(data.X):
        key = digest(np.asarray(row, dtype="<f8").tobytes())
        bucket = buckets.setdefault(key, [])
        match = next((g for g in bucket if np.array_equal(data.X[g[0]], row, equal_nan=True)), None)
        if match is None:
            match = [r]
            bucket.append(match)
            groups.append(match)
        else:
            match.append(r)
    duplicates = [g for g in groups if len(g) > 1]
    report = {"unique_X": len(groups), "duplicate_groups": len(duplicates),
              "duplicate_rows": sum(map(len, duplicates)),
              "surplus_rows": sum(len(g) - 1 for g in duplicates),
              "conflict_groups": sum(len(set(data.y[g])) > 1 for g in duplicates)}
    return report


def official_split(data):
    audit = duplicate_audit(data)
    if audit["duplicate_groups"] or audit["conflict_groups"]:
        raise GateError(f"P03_BLOCKED: {audit}")
    positions = np.arange(len(data.y), dtype=np.int64)
    train, validation = train_test_split(positions, test_size=0.20, shuffle=True,
                                         stratify=data.y, random_state=42)
    if (len(np.intersect1d(train, validation)) or
            not np.array_equal(np.sort(np.concatenate([train, validation])), positions)):
        raise GateError("SPLIT_COVERAGE_OR_DISJOINT_FAILURE")
    return train, validation, audit


def source_ids(positions, sha256):
    return [[sha256, "train", int(p) + 1] for p in positions]


def ordered_ids_hash(positions, sha256):
    return object_hash(source_ids(positions, sha256))


def array_hash(values):
    a = np.ascontiguousarray(values, dtype="<f8")
    return digest(object_hash({"shape": list(a.shape), "dtype": "<f8"}).encode() + a.tobytes())
