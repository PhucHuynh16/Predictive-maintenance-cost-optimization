"""Synthetic fixtures only: no access to the real Test labels or raw CSV."""

from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml
from sklearn.base import clone
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import src.data as data
import scripts.run_data_pipeline as runner
from scripts.run_data_pipeline import validate_config
from src.preprocessing import build_preprocessor, prepare_development


@pytest.fixture
def raw():
    i = np.arange(100)
    values = {
        "UDI": i + 1, "Product ID": [f"L{x + 10000}" for x in i], "Type": ["L"] * len(i),
        "Air temperature [K]": 298.0 + i / 100,
        "Process temperature [K]": 308.0 + i / 50,
        "Rotational speed [rpm]": 1200 + i,
        "Torque [Nm]": 30.0 + i / 10, "Tool wear [min]": i,
        data.TARGET: (i % 5 == 0).astype(int),
        **{label: np.zeros(100, dtype=int) for label in data.SUBLABELS},
    }
    return pd.DataFrame(values, columns=data.RAW_COLUMNS)


def test_schema_and_feature_whitelist(raw):
    data.validate_raw(raw, expected_rows=100)
    features = data.select_features(raw)
    assert tuple(features.columns) == data.FEATURES
    assert not {"UDI", "Product ID", data.TARGET, *data.SUBLABELS}.intersection(features.columns)
    assert features.index.equals(raw.index)


@pytest.mark.parametrize("extra", ["UDI", "Product ID", data.TARGET, *data.SUBLABELS])
def test_preprocessor_rejects_extra_label_or_id(raw, extra):
    X = data.select_features(raw).assign(**{extra: raw[extra]})
    with pytest.raises(data.DataGateError, match="whitelist"):
        build_preprocessor("lr").fit(X)


def test_raw_hash_and_loader(tmp_path, raw):
    path = tmp_path / "fixture.csv"
    payload = raw.to_csv(index=False, lineterminator="\n").encode()
    path.write_bytes(payload)
    with pytest.raises(data.DataGateError, match="SHA-256 mismatch"):
        data.load_verified_raw(path)
    actual = data.load_verified_raw(path, expected=data.sha256_bytes(payload), expected_rows=100)
    pd.testing.assert_frame_equal(actual, raw)


@pytest.mark.parametrize("fault", ["missing_column", "extra_column", "duplicate_column", "missing",
                                  "infinite", "nonnumeric", "invalid_type", "invalid_target",
                                  "float_id", "duplicate_id", "wrong_order", "bad_product", "empty"])
def test_invalid_raw_is_rejected(raw, fault):
    frame = raw.copy()
    if fault == "missing_column":
        frame = frame.drop(columns="Torque [Nm]")
    elif fault == "extra_column":
        frame["unknown"] = 0
    elif fault == "duplicate_column":
        frame.columns = ["UDI", *list(frame.columns)[1:-1], "UDI"]
    elif fault == "missing":
        frame.loc[0, "Air temperature [K]"] = np.nan
    elif fault == "infinite":
        frame.loc[0, "Torque [Nm]"] = np.inf
    elif fault == "nonnumeric":
        frame["Torque [Nm]"] = "not a number"
    elif fault == "invalid_type":
        frame.loc[0, "Type"] = "Z"
    elif fault == "invalid_target":
        frame.loc[0, data.TARGET] = 2
    elif fault == "float_id":
        frame["UDI"] = frame["UDI"].astype(float)
    elif fault == "duplicate_id":
        frame.loc[1, "UDI"] = 1
    elif fault == "wrong_order":
        frame = frame.iloc[::-1]
    elif fault == "bad_product":
        frame.loc[0, "Product ID"] = "M10000"
    elif fault == "empty":
        frame = frame.iloc[:0]
    with pytest.raises(data.DataGateError):
        data.validate_raw(frame)


@pytest.mark.parametrize("content", ["UDI,UDI\n1,2\n", "", "\n"])
def test_bad_csv_header(tmp_path, content):
    payload = content.encode()
    path = tmp_path / "bad.csv"
    path.write_bytes(payload)
    with pytest.raises(data.DataGateError, match="header"):
        data.load_verified_raw(path, data.sha256_bytes(payload), expected_rows=None)


def test_malformed_csv_row_width(tmp_path, raw):
    payload = (raw.to_csv(index=False, lineterminator="\n") + "one,two\n").encode()
    path = tmp_path / "bad.csv"
    path.write_bytes(payload)
    with pytest.raises(data.DataGateError, match="row width"):
        data.load_verified_raw(path, data.sha256_bytes(payload), expected_rows=None)


def test_duplicate_gate_ignores_ids_target_and_sublabels(raw, monkeypatch):
    raw.loc[99, list(data.FEATURES)] = raw.loc[0, list(data.FEATURES)].to_numpy()
    raw.loc[99, data.TARGET] = 1 - raw.loc[0, data.TARGET]
    raw.loc[99, "HDF"] = 1
    original = raw.copy(deep=True)
    report = data.duplicate_report(raw)
    assert report["observations_in_duplicate_groups"] == 2
    assert report["duplicate_groups"] == 1
    assert report["redundant_observations"] == 1
    monkeypatch.setattr(data, "train_test_split", lambda *a, **k: pytest.fail("Split called after duplicate gate"))
    with pytest.raises(data.DuplicateFeaturesError):
        data.create_splits(raw, dependence_reviewed=True)
    pd.testing.assert_frame_equal(raw, original)


def test_dependence_review_gate_precedes_split(raw, monkeypatch):
    monkeypatch.setattr(data, "train_test_split", lambda *a, **k: pytest.fail("Split called before review"))
    with pytest.raises(data.DataGateError, match="dependence review"):
        data.create_splits(raw)


def test_dependence_measurement_uses_no_labels(raw):
    expected = data.dependence_report(raw)
    unlabeled = raw.loc[:, ["UDI", *data.NUMERIC_FEATURES[:2]]]
    assert data.dependence_report(unlabeled) == expected
    x = raw[data.NUMERIC_FEATURES[0]].to_numpy()
    z = x - x.mean()
    assert expected["acf"][data.NUMERIC_FEATURES[0]]["1"] == pytest.approx(np.dot(z[:-1], z[1:]) / np.dot(z, z))
    assert expected["uses_labels"] is False


def test_split_disjoint_sizes_conservation_and_exact_a5_order(raw):
    before = raw.copy(deep=True)
    split = data.create_splits(raw, dependence_reviewed=True)
    assert {k: len(v) for k, v in split.items()} == {"train": 60, "validation": 20, "test": 20}
    assert set(split["train"]).isdisjoint(split["validation"])
    assert set(split["train"]).isdisjoint(split["test"])
    assert set(split["test"]).isdisjoint(split["validation"])
    assert sorted(np.concatenate(list(split.values()))) == list(range(len(raw)))
    remaining, test = train_test_split(np.arange(100), test_size=.2, stratify=raw[data.TARGET], random_state=42)
    train, validation = train_test_split(remaining, test_size=.25,
                                        stratify=raw.iloc[remaining][data.TARGET], random_state=42)
    for key, expected in (("train", train), ("validation", validation), ("test", test)):
        np.testing.assert_array_equal(split[key], expected)
    pd.testing.assert_frame_equal(before, raw)


def test_split_and_metadata_are_deterministic(raw):
    first = data.create_splits(raw, dependence_reviewed=True)
    second = data.create_splits(raw, dependence_reviewed=True)
    ids, one = data.split_manifest(raw, first, "synthetic-fixture-hash")
    ids2, two = data.split_manifest(raw, second, "synthetic-fixture-hash")
    assert ids == ids2
    assert data.canonical_json(one) == data.canonical_json(two)
    for name, values in ids.items():
        assert one["ordered_udi_sha256"][name] == data.sha256_bytes(data.canonical_json(values))
    changed = deepcopy(first)
    changed["train"] = changed["train"][::-1]
    assert data.split_manifest(raw, changed, "synthetic-fixture-hash")[1] != one
    bad = deepcopy(first)
    bad["test"] = first["train"][:20]
    with pytest.raises(data.DataGateError, match="overlap/coverage"):
        data.split_manifest(raw, bad, "synthetic-fixture-hash")


def test_single_class_does_not_fallback_to_another_split(raw):
    raw[data.TARGET] = 0
    with pytest.raises(data.DataGateError, match="both target classes"):
        data.create_splits(raw, dependence_reviewed=True)


def test_preprocessing_fits_only_train_and_handles_unseen_type(raw, monkeypatch):
    train = data.select_features(raw.iloc[:60])
    validation = data.select_features(raw.iloc[60:80])
    validation.loc[:, "Type"] = "UNSEEN"
    validation.loc[:, "Torque [Nm]"] = 10000.0  # Synthetic outlier must survive RF transform.
    fit_indices = []
    original_fit = OneHotEncoder.fit

    def observed_fit(self, X, y=None):
        fit_indices.append(X.index.tolist())
        return original_fit(self, X, y)

    monkeypatch.setattr(OneHotEncoder, "fit", observed_fit)
    prepared = prepare_development(train, validation)
    assert fit_indices == [train.index.tolist(), train.index.tolist()]
    lr = prepared["lr"][0]
    rf = prepared["rf"][0]
    scaler = lr.named_steps["columns"].named_transformers_["numeric"]
    np.testing.assert_allclose(scaler.mean_, train.loc[:, list(data.NUMERIC_FEATURES)].mean())
    assert scaler.n_samples_seen_ == 60
    mean_before = scaler.mean_.copy()
    np.testing.assert_allclose(prepared["lr"][1][:, -5:].mean(axis=0), 0, atol=1e-12)
    np.testing.assert_array_equal(prepared["rf"][2][:, -5:], validation.loc[:, list(data.NUMERIC_FEATURES)])
    assert np.count_nonzero(prepared["rf"][2][:, :-5]) == 0
    # Synthetic test-like input only; no labels provided to either preprocessor.
    rf.transform(data.select_features(raw.iloc[80:]))
    lr.transform(data.select_features(raw.iloc[80:]))
    np.testing.assert_array_equal(scaler.mean_, mean_before)
    assert not hasattr(clone(lr).named_steps["columns"], "transformers_")


@pytest.mark.parametrize("fault", ["nan", "inf", "missing_column", "empty_type", "not_dataframe"])
def test_transform_validates_holdout_input(raw, fault):
    X = data.select_features(raw)
    preprocessor = build_preprocessor("rf").fit(X.iloc[:60])
    bad = X.iloc[60:].copy()
    if fault == "nan":
        bad.loc[60, "Torque [Nm]"] = np.nan
    elif fault == "inf":
        bad.loc[60, "Torque [Nm]"] = np.inf
    elif fault == "missing_column":
        bad = bad.drop(columns="Type")
    elif fault == "empty_type":
        bad.loc[60, "Type"] = " "
    else:
        bad = bad.to_numpy()
    with pytest.raises(data.DataGateError):
        preprocessor.transform(bad)


def test_config_rejects_unapproved_protocol_changes():
    config = yaml.safe_load(Path("configs/data_pipeline.yaml").read_text(encoding="utf-8"))
    validate_config(config)
    for change in ("seed", "ratio", "hash", "features", "review", "extra"):
        bad = deepcopy(config)
        if change == "seed":
            bad["split"]["random_state_both_steps"] = 43
        elif change == "ratio":
            bad["split"]["test_fraction_first"] = .3
        elif change == "hash":
            bad["raw_sha256"] = "0" * 64
        elif change == "features":
            bad["features"].append(data.TARGET)
        elif change == "review":
            bad["dependence_review"]["dataset_sha256"] = "0" * 64
        else:
            bad["smote"] = True
        with pytest.raises(data.DataGateError):
            validate_config(bad)


@pytest.mark.parametrize("gate", ["hash", "duplicate"])
def test_entrypoint_preserves_blocked_run_without_creating_split(tmp_path, raw, monkeypatch, gate):
    import json

    # Isolated synthetic workspace; neither real raw nor real Test is opened.
    for name in ("src/data.py", "src/preprocessing.py", "scripts/run_data_pipeline.py",
                 "configs/data_pipeline.yaml", "requirements.txt"):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(Path(name).read_bytes())
    local_raw = tmp_path / "data/raw/ai4i2020.csv"
    local_raw.parent.mkdir(parents=True)
    local_raw.write_bytes(b"synthetic hash mismatch fixture")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "git", lambda *args: "synthetic-test-commit" if args[0] == "rev-parse" else "")
    if gate == "duplicate":
        raw.loc[99, list(data.FEATURES)] = raw.loc[0, list(data.FEATURES)].to_numpy()
        monkeypatch.setattr(runner, "acquire_raw", lambda path: {"fixture": True})
        monkeypatch.setattr(runner, "load_verified_raw", lambda path: raw)
    monkeypatch.setattr(runner, "create_splits", lambda *a, **k: pytest.fail("Split invoked after stop condition"))
    assert runner.run(tmp_path / "configs/data_pipeline.yaml", "blocked-fixture") == 2
    report = json.loads((tmp_path / "results/w2_g3/runs/blocked-fixture/run.json").read_text())
    assert report["status"] == "BLOCKED"
    assert report["error_type"] == ("DuplicateFeaturesError" if gate == "duplicate" else "DataGateError")
    assert not (tmp_path / "data/processed").exists()
    assert "stable" not in report
    assert local_raw.read_bytes() == b"synthetic hash mismatch fixture"
    with pytest.raises(FileExistsError):
        runner.run(tmp_path / "configs/data_pipeline.yaml", "blocked-fixture")
