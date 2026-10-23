"""AI4I integrity gates and the single A5.4 split; no model evaluation."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

RAW_SHA256 = "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"
UCI_URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
NUMERIC_FEATURES = (
    "Air temperature [K]", "Process temperature [K]",
    "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]",
)
FEATURES = ("Type", *NUMERIC_FEATURES)
TARGET = "Machine failure"
SUBLABELS = ("TWF", "HDF", "PWF", "OSF", "RNF")
RAW_COLUMNS = ("UDI", "Product ID", *FEATURES, TARGET, *SUBLABELS)
ACF_LAGS = (1, 5, 10, 50, 100)
SPLIT_SEED = 42


class DataGateError(ValueError):
    """A gate failure: do not generate a split or silently repair data."""


class DuplicateFeaturesError(DataGateError):
    def __init__(self, report: dict):
        self.report = report
        super().__init__(f"STOP: exact duplicates on six features: {report}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_json(value: object) -> bytes:
    """UTF-8, sorted keys, compact separators, LF; no volatile fields."""
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def verify_hash(payload: bytes, expected: str) -> str:
    actual = sha256_bytes(payload)
    if actual != expected:
        raise DataGateError(f"STOP: raw SHA-256 mismatch; expected={expected}; actual={actual}")
    return actual


def acquire_raw(path: Path) -> dict:
    """Download only from UCI, never overwrite, validate bytes before writing."""
    if path.exists():
        payload = path.read_bytes()
        return {"downloaded": False, "csv_sha256": verify_hash(payload, RAW_SHA256),
                "csv_bytes": len(payload), "url": UCI_URL}
    with urlopen(UCI_URL, timeout=60) as response:
        archive = response.read()
    with ZipFile(io.BytesIO(archive)) as bundle:
        payload = bundle.read("ai4i2020.csv")
    digest = verify_hash(payload, RAW_SHA256)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
    return {"downloaded": True, "csv_sha256": digest, "csv_bytes": len(payload),
            "url": UCI_URL, "archive_sha256": sha256_bytes(archive),
            "archive_bytes": len(archive)}


def validate_features(frame: pd.DataFrame) -> None:
    """Strict feature-only contract; unknown nonempty Type is valid at inference."""
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise DataGateError("Features must be a nonempty pandas DataFrame")
    if tuple(frame.columns) != FEATURES:
        raise DataGateError("Feature whitelist/order must be exactly the six A5 features")
    if frame.isna().any().any():
        raise DataGateError("Unexpected missing feature value; no imputation is authorized")
    if not frame["Type"].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise DataGateError("Type must contain nonempty strings")
    for name in NUMERIC_FEATURES:
        series = frame[name]
        if (not pd.api.types.is_numeric_dtype(series.dtype)
                or pd.api.types.is_bool_dtype(series.dtype)
                or pd.api.types.is_complex_dtype(series.dtype)
                or not np.isfinite(series.to_numpy(dtype=float)).all()):
            raise DataGateError(f"Invalid/nonfinite numeric feature: {name}")


def select_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Explicit raw-to-X boundary, preserving order and index, excluding all labels/IDs."""
    if not isinstance(frame, pd.DataFrame) or not frame.columns.is_unique:
        raise DataGateError("Input must be a DataFrame with unique column names")
    if not set(FEATURES).issubset(frame.columns):
        raise DataGateError("Missing approved feature columns")
    result = frame.loc[:, list(FEATURES)].copy()
    validate_features(result)
    return result


def validate_raw(frame: pd.DataFrame, expected_rows: int | None = None) -> None:
    if not isinstance(frame, pd.DataFrame) or tuple(frame.columns) != RAW_COLUMNS:
        raise DataGateError("Raw schema/order must be exactly the 14 AI4I columns")
    if frame.empty or (expected_rows is not None and len(frame) != expected_rows):
        raise DataGateError("Invalid raw observation count")
    if frame.isna().any().any():
        raise DataGateError("Unexpected missing raw value")
    select_features(frame)
    integer_columns = ("UDI", "Rotational speed [rpm]", "Tool wear [min]", TARGET, *SUBLABELS)
    for name in integer_columns:
        if (not pd.api.types.is_integer_dtype(frame[name].dtype)
                or pd.api.types.is_bool_dtype(frame[name].dtype)):
            raise DataGateError(f"Expected integer column: {name}")
    if not np.array_equal(frame["UDI"].to_numpy(), np.arange(1, len(frame) + 1)):
        raise DataGateError("UDI must be unique, consecutive from 1, in source order; do not reorder")
    for name in (TARGET, *SUBLABELS):
        if not frame[name].isin([0, 1]).all():
            raise DataGateError(f"Expected binary labels in {name}")
    product = frame["Product ID"]
    if (not product.map(lambda x: isinstance(x, str)).all()
            or not product.str.fullmatch(r"[LMH]\d{5}").all()
            or not product.is_unique
            or not frame["Type"].isin(["L", "M", "H"]).all()
            or not product.str[0].equals(frame["Type"])):
        raise DataGateError("Invalid Product ID/Type format or uniqueness")
    if (frame.loc[:, list(NUMERIC_FEATURES)] < 0).any().any():
        raise DataGateError("Negative physical input; report, do not repair")
    if (frame.loc[:, list(NUMERIC_FEATURES[:3])] == 0).any().any():
        raise DataGateError("Temperature and speed must be positive")


def load_verified_raw(path: Path, expected: str = RAW_SHA256,
                      expected_rows: int | None = 10000) -> pd.DataFrame:
    payload = path.read_bytes()
    verify_hash(payload, expected)
    # Check before pandas could rename duplicate headers or coerce malformed rows.
    # Official CSV starts with a UTF-8 BOM. Decode the signature, not the raw bytes/hash.
    with io.StringIO(payload.decode("utf-8-sig"), newline="") as stream:
        rows = csv.reader(stream, strict=True)
        if tuple(next(rows, ())) != RAW_COLUMNS:
            raise DataGateError("Missing/duplicate/reordered raw CSV header")
        if any(len(row) != len(RAW_COLUMNS) for row in rows):
            raise DataGateError("Malformed CSV row width")
    frame = pd.read_csv(io.BytesIO(payload))
    validate_raw(frame, expected_rows)
    return frame


def duplicate_report(frame: pd.DataFrame) -> dict:
    features = select_features(frame)
    involved = features.duplicated(keep=False)
    return {"key_columns": list(FEATURES),
            "method": "pandas duplicated(subset=six X, keep=False); exact parsed values; no rounding",
            "observations_in_duplicate_groups": int(involved.sum()),
            "duplicate_groups": int(features.loc[involved].drop_duplicates().shape[0]),
            "redundant_observations": int(features.duplicated(keep="first").sum())}


def dependence_report(frame: pd.DataFrame) -> dict:
    """Descriptive biased ACF, no label access, p-values, gap selection or split search."""
    result = {}
    for name in NUMERIC_FEATURES[:2]:
        values = frame[name].to_numpy(dtype=float)
        centered = values - values.mean()
        denominator = float(centered @ centered)
        result[name] = {str(lag): (float(centered[:-lag] @ centered[lag:] / denominator)
                                  if denominator and lag < len(values) else None)
                        for lag in ACF_LAGS}
    return {"order": "source UDI", "lags": list(ACF_LAGS), "acf": result,
            "estimator": "sum((x[t]-mean)*(x[t+k]-mean))/sum((x-mean)^2), no lag correction",
            "uses_labels": False,
            "limitations": "Descriptive only; not stationarity, periodicity, IID or temporal validity proof"}


def create_splits(frame: pd.DataFrame, *, dependence_reviewed: bool = False) -> dict[str, np.ndarray]:
    """A5.4 exactly once per invocation. Returned arrays are positional row indices."""
    validate_raw(frame)
    duplicates = duplicate_report(frame)
    if duplicates["duplicate_groups"]:
        raise DuplicateFeaturesError(duplicates)
    if not dependence_reviewed:
        raise DataGateError("STOP: dependence review required before split")
    positions = np.arange(len(frame))
    target = frame[TARGET].to_numpy()
    if len(np.unique(target)) != 2:
        raise DataGateError("Stratified split requires both target classes")
    try:
        remaining, test = train_test_split(positions, test_size=0.2, stratify=target,
                                          random_state=SPLIT_SEED, shuffle=True)
        train, validation = train_test_split(remaining, test_size=0.25,
                                            stratify=target[remaining],
                                            random_state=SPLIT_SEED, shuffle=True)
    except ValueError as exc:
        raise DataGateError(f"STOP: stratification cannot satisfy approved protocol: {exc}") from exc
    parts = {"train": train, "validation": validation, "test": test}
    combined = np.concatenate(list(parts.values()))
    if len(combined) != len(frame) or not np.array_equal(np.sort(combined), positions):
        raise DataGateError("Split overlap/coverage failure")
    return parts


def split_manifest(frame: pd.DataFrame, parts: dict[str, np.ndarray], dataset_hash: str) -> tuple[dict, dict]:
    """Local IDs separate from the public summary; hashes encode ordered UDI lists."""
    if set(parts) != {"train", "validation", "test"}:
        raise DataGateError("Expected train/validation/test")
    all_positions = np.concatenate(list(parts.values()))
    if not np.array_equal(np.sort(all_positions), np.arange(len(frame))):
        raise DataGateError("Split overlap/coverage failure")
    ids = {name: frame.iloc[pos]["UDI"].astype(int).tolist() for name, pos in parts.items()}
    summary = {"dataset_sha256": dataset_hash, "split_seed": SPLIT_SEED,
               "algorithm": "sklearn.model_selection.train_test_split twice; shuffle=True; stratify=Machine failure",
               "sequence": "source UDI -> Test 20% -> Validation 25% of returned remaining 80%",
               "output_order": "retain sklearn returned positions; no sorting between split calls",
               "sizes": {name: len(values) for name, values in ids.items()},
               "ordered_udi_sha256": {name: sha256_bytes(canonical_json(values)) for name, values in ids.items()},
               "id_encoding": "canonical_json ordered integer UDI list, UTF-8 compact JSON plus LF",
               "disjoint": True, "all_observations_preserved": True}
    return ids, summary
