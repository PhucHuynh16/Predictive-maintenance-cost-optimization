"""Synthetic model/runner tests. Do not open real project data, including Test."""

from copy import deepcopy
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import pytest
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression

import src.baselines as baselines
from src.constraints import capacity
from src.cost_model import EvaluationInputError
from src.data import FEATURES, RAW_SHA256, TARGET, canonical_json, sha256_bytes
from scripts import run_baselines as runner


@pytest.fixture
def X():
    i = np.arange(40)
    return pd.DataFrame({"Type": ["L", "M"] * 20, "Air temperature [K]": 298 + i / 10,
                         "Process temperature [K]": 309 + i / 20, "Rotational speed [rpm]": 1200 + i,
                         "Torque [Nm]": 30 + i, "Tool wear [min]": i * 10}, columns=FEATURES)


def test_fixed_policies_no_capacity_repair(X):
    assert baselines.reactive_actions(40).sum() == 0
    X.loc[:2, "Tool wear [min]"] = [199, 200, 201]
    actions = baselines.fixed_wear_actions(X)
    assert actions[:3].tolist() == [0, 1, 1]
    assert actions.sum() > 4 and not capacity(actions)["feasible"]


def test_exact_lr_configuration():
    model = baselines.build_b2().named_steps["model"]
    expected = {"C": 1.0, "l1_ratio": 0.0, "solver": "lbfgs", "dual": False,
                "fit_intercept": True, "tol": 1e-4, "max_iter": 2000,
                "class_weight": None, "random_state": 42, "warm_start": False,
                "verbose": 0, "n_jobs": None, "intercept_scaling": 1}
    assert all(model.get_params()[key] == value for key, value in expected.items())
    assert model.get_params()["penalty"] == "deprecated"


def test_train_only_fit_and_reproducibility(X):
    y = np.tile([0, 1, 0, 0], 10)
    validation = X.iloc[:4].copy()
    validation["Type"] = "UNSEEN"
    validation["Torque [Nm]"] = 5000  # Sentinel: must not enter fitted scaler.
    first = baselines.fit_b2_development(X, y, validation)
    second = baselines.fit_b2_development(X, y, validation)
    np.testing.assert_array_equal(first["probabilities"], second["probabilities"])
    prep = first["model"].named_steps["preprocess"].named_steps["columns"]
    assert prep.named_transformers_["numeric"].n_samples_seen_ == len(X)
    assert prep.named_transformers_["numeric"].mean_[3] == X["Torque [Nm]"].mean()
    assert "UNSEEN" not in prep.named_transformers_["type"].categories_[0]
    assert not first["warnings"]


def test_validation_labels_not_accepted(X):
    with pytest.raises(TypeError):
        baselines.fit_b2_development(X, np.tile([0, 1], 20), X, y_validation=[1] * 40)


def test_only_one_train_fit_no_validation_refit(X, monkeypatch):
    original = LogisticRegression.fit
    calls = []

    def spy(self, values, labels, *args, **kwargs):
        calls.append((len(values), len(labels)))
        return original(self, values, labels, *args, **kwargs)

    monkeypatch.setattr(LogisticRegression, "fit", spy)
    baselines.fit_b2_development(X, np.tile([0, 1], 20), X.iloc[:4])
    assert calls == [(40, 40)]


def test_convergence_warning_is_failed_no_retry(X, monkeypatch):
    calls = []

    def fail(self, *args, **kwargs):
        calls.append(1)
        warnings.warn("synthetic convergence failure", ConvergenceWarning)
        return self

    monkeypatch.setattr(LogisticRegression, "fit", fail)
    with pytest.raises(baselines.BaselineFailure) as exc:
        baselines.fit_b2_development(X, np.tile([0, 1], 20), X.iloc[:4])
    assert len(calls) == 1
    assert exc.value.warning_records[0]["category"] == "ConvergenceWarning"


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -0.1, 1.1])
def test_invalid_model_scores_fail(X, monkeypatch, invalid):
    def bad(self, values):
        return np.full((len(values), 2), invalid)

    monkeypatch.setattr(LogisticRegression, "predict_proba", bad)
    with pytest.raises(baselines.BaselineFailure):
        baselines.fit_b2_development(X, np.tile([0, 1], 20), X.iloc[:4])


def test_test_file_access_blocked_without_reading_it(tmp_path):
    directory = tmp_path / "data/processed/w2_g3/g3_submission"
    directory.mkdir(parents=True)
    (directory / "test.csv").write_text("synthetic sentinel, never to be read")
    (directory / "train.csv").write_text("synthetic allowed")
    with runner.development_access_guard(tmp_path) as reads:
        assert (directory / "train.csv").read_text() == "synthetic allowed"
        with pytest.raises(PermissionError):
            (directory / "test.csv").read_bytes()
    assert reads == ["data/processed/w2_g3/g3_submission/train.csv"]


@pytest.fixture
def local_development(tmp_path, X):
    stable = {"split": {"dataset_sha256": RAW_SHA256, "sizes": {}, "ordered_udi_sha256": {}},
              "split_csv_sha256": {}}
    for name, indices in (("train", range(30)), ("validation", range(30, 40))):
        frame = X.iloc[list(indices)].copy()
        frame.insert(0, "UDI", np.array(list(indices)) + 1)
        frame[TARGET] = np.arange(len(frame)) % 2
        payload = frame.to_csv(index=False, lineterminator="\n").encode()
        (tmp_path / f"{name}.csv").write_bytes(payload)
        stable["split_csv_sha256"][name] = sha256_bytes(payload)
        stable["split"]["sizes"][name] = len(frame)
        stable["split"]["ordered_udi_sha256"][name] = sha256_bytes(canonical_json(frame["UDI"].tolist()))
    (tmp_path / "manifest.json").write_bytes(canonical_json(stable))
    return tmp_path, {"stable": stable, "stable_manifest_sha256": sha256_bytes(canonical_json(stable))}


def test_loader_opens_no_test_or_raw(local_development, monkeypatch):
    local, reference = local_development
    original = Path.open
    paths = []

    def spy(path, *args, **kwargs):
        paths.append(path.name)
        assert path.name in {"manifest.json", "train.csv", "validation.csv"}
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy)
    frames = runner.load_development(local, reference)
    assert [len(frames[n]) for n in ("train", "validation")] == [30, 10]
    assert paths == ["manifest.json", "train.csv", "validation.csv"]


@pytest.mark.parametrize("filename", ["manifest.json", "train.csv", "validation.csv"])
def test_loader_rejects_tampering(local_development, filename):
    local, reference = local_development
    with (local / filename).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(EvaluationInputError, match="mismatch"):
        runner.load_development(local, reference)


@pytest.mark.parametrize("key,value", [("b1_threshold_minutes", 201), ("b2_threshold", 0.4),
                                      ("evaluation_partition", "test"), ("capacity", 0.2),
                                      ("post_calibration", True), ("refit_train_validation", True)])
def test_config_rejects_protocol_changes(key, value):
    config = deepcopy(runner.expected_config())
    config[key] = value
    with pytest.raises(EvaluationInputError):
        runner.validate_config(config)


def test_failed_unit_gate_prevents_development_access(tmp_path, monkeypatch):
    from types import SimpleNamespace

    def failure(command, **kwargs):
        (tmp_path / "tests.xml").write_text('<testsuites><testsuite tests="1" failures="1" errors="0" skipped="0"/></testsuites>')
        return SimpleNamespace(returncode=1, stdout="synthetic gate FAIL", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", failure)
    with pytest.raises(EvaluationInputError, match="gate FAILED"):
        runner.unit_test_gate(tmp_path)
    assert json.loads((tmp_path / "unit_tests.json").read_text())["failures"] == 1


def test_new_artifacts_never_overwritten(tmp_path):
    path = tmp_path / "evidence.json"
    runner.write_new(path, b"first run")
    with pytest.raises(FileExistsError):
        runner.write_new(path, b"second run")
    assert path.read_bytes() == b"first run"
