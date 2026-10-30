"""G301–G310, synthetic fixtures only. No official source or Test is read."""
from copy import deepcopy
import io
import json
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import train_test_split

import src.scania.contracts as contracts
import src.scania.data as data
from src.scania.contracts import FEATURES, GateError, canonical, digest
from src.scania.preprocessing import build_preprocessor
from src.scania.artifacts import write_json, verify_artifacts
import src.scania.acquisition as acquisition
import scripts.run_scania_pipeline as runner

ROOT = Path(__file__).resolve().parents[2]


def payload(rows=None, header="class,a,b", preamble="notice\n---\n"):
    rows = rows or ["neg,1,na", "pos,2,3", "neg,4,5"]
    return (preamble + header + "\n" + "\n".join(rows) + "\n").encode()


def parsed_fixture(n=100):
    X = np.column_stack([np.arange(n, dtype=float), np.arange(n, dtype=float) + 0.5])
    return data.ParsedTrain(X, (np.arange(n) % 5 == 0).astype(np.int8), "a" * 64, 3, ("a", "b"))


def test_G301_valid_parser_dynamic_header_mapping():
    p = data.parse_train(payload(), ("a", "b"), 3)
    assert p.header_line_1based == 3 and p.features == ("a", "b")
    assert p.y.tolist() == [0, 1, 0] and np.isnan(p.X[0, 1])
    assert p.sha256 == digest(payload()) and p.X.shape == (3, 2)


@pytest.mark.parametrize("fault", ["bom", "utf8", "header", "order", "duplicate_col", "extra", "width", "label", "missing_label", "empty", "count"])
def test_G301_invalid_parser(fault):
    raw = payload()
    if fault == "bom": raw = b"\xef\xbb\xbf" + raw
    if fault == "utf8": raw = raw.replace(b"notice", b"\xff")
    if fault == "header": raw = payload(header="target,a,b")
    if fault == "order": raw = payload(header="class,b,a")
    if fault == "duplicate_col": raw = payload(header="class,a,a")
    if fault == "extra": raw = payload(header="class,a,b,UDI")
    if fault == "width": raw = payload(rows=["neg,1", "pos,2,3", "neg,4,5"])
    if fault == "label": raw = raw.replace(b"pos,", b"positive,")
    if fault == "missing_label": raw = raw.replace(b"pos,", b",")
    if fault == "empty": raw = b""
    if fault == "count": raw += b"neg,7,8\n"
    with pytest.raises(GateError): data.parse_train(raw, ("a", "b"), 3)


def test_G302_source_hash_size_path_before_parse(tmp_path, monkeypatch):
    raw = tmp_path / "data/raw/scania_aps"
    raw.mkdir(parents=True)
    source = raw / "aps_failure_training_set.csv"
    source.write_bytes(payload())
    spec = {"bytes": len(payload()), "sha256": "0" * 64, "rows": 3}
    monkeypatch.setattr(data, "parse_train", lambda *a: pytest.fail("parser called before hash gate"))
    with pytest.raises(GateError, match="SOURCE_HASH"): data.read_train(source, raw, tmp_path, spec)
    spec["sha256"] = digest(payload()); spec["bytes"] += 1
    with pytest.raises(GateError, match="SOURCE_HASH"): data.read_train(source, raw, tmp_path, spec)
    with pytest.raises(GateError, match="PATH_OUTSIDE"): data.safe_path(tmp_path.parent / "other.csv", tmp_path)


def test_G302_config_schema_version_mismatch(monkeypatch):
    cfg = json.loads((ROOT / "configs/scania/g3_pipeline.json").read_text())
    contracts.validate_config(cfg)
    for key in ("split", "schema", "environment"):
        wrong = deepcopy(cfg); wrong[key] = {}
        with pytest.raises(GateError, match="CONFIG_MISMATCH"): contracts.validate_config(wrong)
    monkeypatch.setattr(contracts, "environment", lambda: {"python": "wrong", "packages": {}})
    with pytest.raises(GateError, match="VERSION_MISMATCH"): contracts.validate_config(cfg)


@pytest.mark.parametrize("conflict", [False, True])
def test_G303_duplicates_missing_masks_block_before_split(conflict, monkeypatch):
    p = parsed_fixture(); p.X[0] = [1, np.nan]; p.X[1] = [1, np.nan]
    p.y[0] = 0; p.y[1] = int(conflict)
    report = data.duplicate_audit(p)
    assert report["duplicate_groups"] == 1 and report["surplus_rows"] == 1
    assert report["conflict_groups"] == int(conflict)
    monkeypatch.setattr(data, "train_test_split", lambda *a, **k: pytest.fail("split called despite P03"))
    with pytest.raises(GateError, match="P03_BLOCKED"): data.official_split(p)


def test_G303_missing_mask_and_hash_collision_do_not_merge_rows(monkeypatch):
    p = parsed_fixture(10); p.X[0] = [1, np.nan]; p.X[1] = [np.nan, 1]
    monkeypatch.setattr(data, "digest", lambda _: "same bucket")
    assert data.duplicate_audit(p)["duplicate_groups"] == 0


def test_G304_single_stratified_call_and_exact_returned_order(monkeypatch):
    p = parsed_fixture(); real = train_test_split; calls = []
    def spy(*a, **kw):
        calls.append(kw)
        return real(*a, **kw)
    monkeypatch.setattr(data, "train_test_split", spy)
    t, v, _ = data.official_split(p)
    et, ev = real(np.arange(100), test_size=.2, shuffle=True, stratify=p.y, random_state=42)
    assert len(calls) == 1 and calls[0]["random_state"] == 42
    assert np.array_equal(t, et) and np.array_equal(v, ev)
    assert len(t) == 80 and len(v) == 20 and int(p.y[t].sum()) == 16 and int(p.y[v].sum()) == 4
    assert not set(t) & set(v) and set(t) | set(v) == set(range(100))


def test_G305_source_ids_order_hashes_and_exclusion():
    positions = np.array([2, 0, 1]); sha = "f" * 64
    assert data.source_ids(positions, sha) == [[sha, "train", 3], [sha, "train", 1], [sha, "train", 2]]
    assert data.ordered_ids_hash(positions, sha) != data.ordered_ids_hash(positions[::-1], sha)
    assert data.ordered_ids_hash(positions, sha) != data.ordered_ids_hash(positions, "e" * 64)
    assert len(FEATURES) == 170 and not {"class", "UDI", "source_row_id", "partition"} & set(FEATURES)
    frame = pd.DataFrame([[1., 2.]], columns=["a", "class"])
    with pytest.raises(GateError, match="SCHEMA_MISMATCH"): build_preprocessor("tree", ("a", "b")).fit(frame)


def test_G306_train_only_statistics_validation_sentinels_and_constant():
    train = np.array([[1., 9.], [3., 9.], [np.nan, 9.]])
    val = np.array([[100000., 9.], [np.nan, 9.]])
    lr = build_preprocessor("lr", ("a", "cd_000")).fit(train)
    imputer = lr.named_steps["imputer"]; scaler = lr.named_steps["scaler"]
    before = imputer.statistics_.copy(), scaler.mean_.copy(), scaler.scale_.copy()
    assert imputer.statistics_.tolist() == [2., 9.] and scaler.mean_.tolist() == [2., 9.]
    assert scaler.n_samples_seen_ == 3
    out = lr.transform(val)
    assert np.isfinite(out).all() and np.all(out[:, 1] == 0)
    assert np.array_equal(before[0], imputer.statistics_) and np.array_equal(before[1], scaler.mean_)
    assert np.array_equal(before[2], scaler.scale_) and out[1, 0] == 0


def test_G306_all_missing_column_row_observed_validation_and_no_drop():
    train = np.array([[np.nan, 4., 7.], [np.nan, np.nan, np.nan], [np.nan, 8., 7.]])
    val = np.array([[15., np.nan, np.nan], [np.nan, 99., 7.]])
    tree = build_preprocessor("tree", ("empty", "high_missing", "cd_000")).fit(train)
    assert tree.named_steps["imputer"].statistics_.tolist() == [0., 6., 7.]
    assert tree.transform(val).tolist() == [[15., 6., 7.], [0., 99., 7.]]
    assert tree.transform(train)[1].tolist() == [0., 6., 7.]
    assert tree.transform(train).shape == (3, 3)


def test_G306_eight_high_missing_columns_kept():
    train = np.full((10, 10), np.nan); train[0, :8] = np.arange(8); train[:, 8:] = 4
    pre = build_preprocessor("tree", tuple(f"f{i}" for i in range(10))).fit(train)
    assert pre.transform(train).shape == (10, 10) and np.isfinite(pre.transform(train)).all()


@pytest.mark.parametrize("token", ["NaN", "nan", "inf", "-inf", "null", "None", "NA", "", "1e999", "1e-999", "1.0000000000000001", "9007199254740993"])
def test_G307_invalid_nonfinite_precision_rejected(token):
    with pytest.raises(GateError): data.parse_train(payload(rows=[f"neg,{token},3"]), ("a", "b"), 1)


def test_G307_transform_validation_only_missing_and_invalid():
    pre = build_preprocessor("tree", ("a", "b")).fit([[1., 2.], [3., 4.]])
    assert pre.transform([[np.nan, np.nan]]).tolist() == [[2., 3.]]
    for invalid in ([[np.inf, 0.]], [[1., 2., 3.]], [["bad", "na"]], [[True, False]]):
        with pytest.raises(GateError): pre.transform(invalid)


def test_G308_test_path_and_archive_member_sentinel(tmp_path, monkeypatch):
    test = tmp_path / "aps_failure_test_set.csv"
    def no_open(*args, **kwargs): pytest.fail("Test was opened")
    monkeypatch.setattr(Path, "read_bytes", no_open)
    with pytest.raises(GateError, match="NO_TEST_ACCESS"):
        data.read_train(test, tmp_path, tmp_path, {})
    class SentinelBundle:
        def read(self, name): pytest.fail("Test member read")
    for member in ["aps_failure_test_set.csv", "other.csv", "../aps_failure_training_set.csv"]:
        with pytest.raises(GateError, match="NO_TEST_ACCESS"): acquisition.read_member(SentinelBundle(), member)


def test_G308_acquisition_opens_only_train_description(tmp_path, monkeypatch):
    sink = io.BytesIO()
    members = {"aps_failure_training_set.csv": b"train bytes", "aps_failure_description.txt": b"notice"}
    with ZipFile(sink, "w") as z:
        for k, v in members.items(): z.writestr(k, v)
        z.writestr("aps_failure_test_set.csv", b"SEALED synthetic sentinel")
    archive = sink.getvalue()
    monkeypatch.setattr(acquisition, "SOURCES", {acquisition.ARCHIVE: (len(archive), digest(archive)), **{k: (len(v), digest(v)) for k, v in members.items()}})
    raw = tmp_path / "data/raw/scania_aps"; raw.mkdir(parents=True)
    (raw / acquisition.ARCHIVE).write_bytes(archive)
    opened = []; real = ZipFile.open
    def spy(self, name, *args, **kwargs):
        opened.append(name)
        assert name != "aps_failure_test_set.csv"
        return real(self, name, *args, **kwargs)
    monkeypatch.setattr(ZipFile, "open", spy)
    report = acquisition.acquire(tmp_path)
    assert opened == list(members) and report["downloaded_archive"] is False
    assert not (raw / "aps_failure_test_set.csv").exists()


def test_G309_exclusive_writes_failure_logs_and_checksum_detection(tmp_path):
    path = tmp_path / "original.json"; write_json(path, {"old": True}); old = path.read_bytes()
    with pytest.raises(FileExistsError): write_json(path, {"old": False})
    assert path.read_bytes() == old
    cfgdir = tmp_path / "configs/scania"; cfgdir.mkdir(parents=True)
    (cfgdir / "g3_pipeline.json").write_text("{}")
    with pytest.raises(GateError, match="CONFIG_MISMATCH"): runner.run(tmp_path, "blocked_fixture")
    out = tmp_path / "results/scania_aps/g3/blocked_fixture"
    assert json.loads((out / "run_summary.json").read_text())["status"] == "BLOCKED"
    assert verify_artifacts(out)
    (out / "execution.txt").write_text("changed")
    assert not verify_artifacts(out)
    with pytest.raises(FileExistsError): runner.run(tmp_path, "blocked_fixture")


def test_G310_two_reproductions_and_fold_clone():
    p = parsed_fixture(); a, b, _ = data.official_split(p); c, d, _ = data.official_split(p)
    assert np.array_equal(a, c) and np.array_equal(b, d)
    first = build_preprocessor("lr", ("a", "b")).fit(p.X[a])
    second = build_preprocessor("lr", ("a", "b")).fit(p.X[c])
    assert data.array_hash(first.transform(p.X[b])) == data.array_hash(second.transform(p.X[d]))
    fresh = clone(first)
    assert not hasattr(fresh.named_steps["imputer"], "statistics_")
    assert not hasattr(fresh.named_steps["scaler"], "mean_")
    fresh.fit(p.X[a[:20]])
    assert fresh.named_steps["scaler"].n_samples_seen_ == 20
    assert first.named_steps["scaler"].n_samples_seen_ == 80


def test_G309_public_checksums_survive_git_crlf_and_detect_tampering(tmp_path):
    content = b'{"status":"PASS"}\n'
    (tmp_path / "summary.json").write_bytes(content)
    write_json(tmp_path / "checksums.json", {"summary.json": digest(content)})
    assert verify_artifacts(tmp_path)
    (tmp_path / "summary.json").write_bytes(content.replace(b"\n", b"\r\n"))
    assert verify_artifacts(tmp_path)
    (tmp_path / "summary.json").write_bytes(content.replace(b"PASS", b"FAIL"))
    assert not verify_artifacts(tmp_path)
