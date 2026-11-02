# SC-G4-C Gate A — implementation and handoff

Ngày 2026-11-02, Asia/Saigon. Owner giao **SC-G4-C GATE A AUTHORIZED** trực tiếp trong chat, đúng 15 file mới/3 tài liệu sửa của [packet6527632450](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6527632450). P02/P06/P07/P08 theo [owner6527262534](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6527262534). Base main/PR15 merge `d78cfcd30601090211003ef3a6a6751f83dd6eb3`; G3 accepted HEAD `0b01dc9fce1e3dbafd1770d481bd77b4098ba84b` giữ nguyên.

**Gate A chờ independent review; Gate B NOT AUTHORIZED.** Không có official fitting/scoring command. `preflight` chỉ đọc/xác minh G3, không trả real y/X cho baseline runner; `synthetic` chỉ dùng fixture dựng trong code (40 Train/20 Validation,3 features, seed-independent deterministic), không đọc raw/processed. B1/B2 constructors đúng full params; fit helper từ chối production mode và arrays vượt200rows/8features. Đây là software boundary, không khẳng định API thư viện hoặc OS không thể bị code ngoài runner sử dụng.

## Protocol

- Cost10FP+500FN, whole-partition K=N//10, exact comparator>=/ties/no top-k, error khác infeasible. B0 a0/no model/no fake p.
- PRIMARY0.5 và SECONDARY10/510 lấy từ cùng probability vector mỗi baseline; không tìm/chọn threshold theo Validation. B0 reference +4fixed rows, không chọn role thắng. AP non-interpolated, AUC/Brier dùng score; undefined/null/reasons theo owner. No weighting/calibration/CV/refit preprocessing/Train+Val.
- LR ConvergenceWarning/invalid p=>FAILED/no retry; warning category/text lưu diagnostics. Không thay solver/C/iterations/seed/version. Gate A synthetic dùng process-default threads; Gate B thread/runtime/budget fields=null để chờ quyền cụ thể, không giả đã khóa runtime policy B.
- Config canonical SHA-256: `8b9cbbd2a14d23f256a677fc6a61eecf7dbf7c6261c78529670cbfddc00b88ad`. `gate_b_authorized=false`, real results disabled. Thay config hoặc dependency mismatch chặn trước fit.

## Commands (Gate A only)

Từ root Codex, Python3.11.9 và lock G3 hiện có, không nâng/hạ deps. Mỗi run-id mới/exclusive; các ví dụ không tự tạo quyền chạy Gate B.

```powershell
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/run_scania_baselines.py tests --run-id gate_a_tests_unique
.venv/Scripts/python.exe scripts/run_scania_baselines.py synthetic --run-id gate_a_synthetic_unique
.venv/Scripts/python.exe scripts/run_scania_baselines.py preflight --run-id gate_a_preflight_unique --test-evidence results/scania_aps/g4/gate_a_tests_unique/tests_summary.json
```

`tests` chụp code/config/environment/commit trước pytest, chạy synthetic/G301–G310, kiểm source/env không đổi và ghi sanitized JUnit evidence. `summarize-tests --junit <G4_LOCAL_XML> --run-id <new>` chỉ chuyển log lịch sử thành **UNBOUND_HISTORICAL_JUNIT**; không biến source hiện tại thành source đã chạy XML cũ, không mở production gate. Không defaults `tests_pass=True`; preflight yêu cầu actual bound summary đủ16groups+10G3groups, mọi cases passed, counts/env/config/code khớp. Raw XML chi tiết có paths chỉ local ignored dưới `data/processed/scania_aps/g4/gate_a_tests/`.

## Input and preservation

Trusted Git base pins all pre-existing files except3authorized docs, canonical LF for text/binary exact; G3 public manifest/checksums lấy từ accepted tree, whitelist5artifact names trước read. G4 digest có file list riêng, không gọi broad G3 digest rồi ép khớp code G4. Read paths exact/containment/no aliases before open; writer chỉ root G4/run-id mới, collision diagnostic ở attempt-id riêng, không overwrite.

Read-only real preflight: rehash/parse own rawTrain đã pin, kiểm frozen membership/positions/ordered IDs và y_train/y_validation so raw y theo positions (bắt swap giữ classcounts),4NPY hashes đúng G3 array_hash shape/dtype semantics; mmap readonly/allow_pickleFalse. Không gọi official_split/preprocessor.fit/transform/joblib load hoặc estimator. Label digests mới ở G4 input_manifest, không sửa G3 manifest. Tracked G3/G2/AI4I và accepted code được kiểm trước/sau. Không read/extract ZIP/Test/cache hoặc worktree Antigravity.

## Evidence and failure handling

Public evidence riêng `results/scania_aps/g4/<run_id>/`, nhỏ/sanitized. Synthetic metrics ghi rõ SYNTHETIC_FIXTURE_NOT_REAL_RESULTS. Real preflight không sinh baseline_metrics hoặc probabilities/models. Phase-specific required artifacts khác nhau: không giả có12production files khi Gate A chỉ preflight hoặc fixture. Checksum verifier kiểm missing/extra/content/path, canonicalLF chấp nhận GitCRLF; completion gate độc lập checksum list.

Failure E2E: config/test-evidence/input/fit/predict/metrics errors giữ run_summary, failure_diagnostics (stage/type/reason/warnings, metrics chưa tính null/NOT_COMPUTED), execution/checksums trước re-raise. Không dùng PASS cũ hoặc ghi đè run khác. I/O failure được báo thật, không nhận evidence đã lưu nếu writer lỗi. Runtime seconds load/verify, fit, predict, metrics,total; chưa chạy=null/reason, B0fit0/NOT_APPLICABLE; historical G3 elapsed không là runtime G4. Stable digest không có timestamps/runtime/run-id; hai synthetic runs không được gọi là real baseline reproducibility.

## Verification and limitations

16groups C01–C06/K01–K04/M01–M02/B01–B02/R01–R02 và G301–G310 được chạy lại; số cases/source/runtimes thực ở tests_summary/run_summary của lần bàn giao. K03/K04 là contract helpers chỉ synthetic, không search Validation thật. API/get_params, Train-only spies, both exact thresholds/nextafter/root-only, no fake p, warning diagnostics, stale evidence, Test paths/alias, protected mutation, tamper/missing/CRLF/collision, two fixture runs đều có tests.

Các lần kiểm thử thất bại ban đầu được giữ: sandbox Git fixture permission; runtime threadpoolctl Windows DLL path discovery; numpy int8 class labels chưa JSON-serializable. Git fixture chạy trong ngữ cảnh quyền phù hợp; bỏ optional threadpool runtime control chưa được yêu cầu, không đổi deps/model params; chuyển class labels metadata sang Python int và thêm assertion serialization. Không đổi oracles để làm PASS. XML cũ chuyển thành unbound history, không gắn nguồn sau sửa vào lượt cũ. Pending Gate B policy về threads cần owner riêng.

Chưa chạy official B0/B1/B2, real fitting/scoring, RF/calibration/optimization hoặc Test. Gate B cần independent Gate A review, owner authorization riêng cùng paths/budget/runtime/thread policy và command review; không mở bằng đổi flag CLI. G4 chưa được nghiệm thu và không tự sang G5. Không rerun AI4I tests/training ngoài scope; bảo toàn files được kiểm bằng Git/protected snapshots.

## Gate A delivery evidence — 2026-11-02

Implementation source commit **`a96da3642d055fb2fb90ba076884dfdc845d6f95`**, code digest `1cf2d86de06bba07c8ddaf1d990919c3470230977813507d0224667bf553ea98`. Evidence/docs delivery commit giữ nguyên source/config đó. [Bound pytest evidence](../../results/scania_aps/g4/gate_a_tests_20261102_01/tests_summary.json) chụp source trước pytest từ commit này, working tree sạch tại bắt đầu: **127 PASS,0 FAIL,0 ERROR,0 SKIP**, terminal9.02s; suite runtime theo JUnit lưu riêng. **87ca G4 +40ca G3**, đủ16groups mới và10groups regression.

| Group | PASS cases | Group | PASS cases |
|---|---:|---|---:|
| C01 |4| C02 |1|
| C03 |1| C04 |3|
| C05 |1| C06 |20|
| K01 |7| K02 |3|
| K03 |1| K04 |1|
| M01 |1| M02 |2|
| B01 |1| B02 |6|
| R01 |34| R02 |1|

G3 groups G301–G310 lần lượt12/2/3/1/1/3/13/2/2/1. Không sửa G3 test oracle. [Gate A validation](../../results/scania_aps/g4/gate_a_delivery_20261102_01/gate_a_validation.json) và [source manifest](../../results/scania_aps/g4/gate_a_delivery_20261102_01/source_manifest.json) chỉ rõ hashes/outcomes/source. Môi trường Python3.11.9/lock15packages đúng G3, pipcheck đạt. Fresh install/cross-OS chưa chạy; Windows BLAS runtime-controller discovery có lỗi đường dẫn DLL, không tuyên bố threadpool inspection/control đạt. Synthetic run dùng defaults và log rõ; Gate B thread policy còn chờ owner.

Hai lượt **fixture synthetic** `gate_a_synthetic_20261102_01`/`_02` có stable digest `9135324eeb173752663bf26d9cf5f79d5bf2c38b399e5619fb028bf74876e230`, total0.138934s/0.188101s. Đây không phải reproducibility hoặc metrics của real baselines. [Preflight](../../results/scania_aps/g4/gate_a_preflight_20261102_01/input_manifest.json) real read-only đạt73.914710s total: rawTrain SHA/source/schema/membership/ordered IDs, nhãn theo positions và4matrix hashes khớp; estimator_fit=false, validation_scored=false. Postcheck **170 protected pre-existing files** unchanged, digest `05fe989ff1c0008ca8dae78b855c0760a4711fa78e9831a2388f7d7f6c6a71e8`. Không sinh lại preprocessing/split.

Label hashes mới chỉ ở G4: y_train `7991a3745644b10e30dee85329f4b9968cbb2e79d17209d63e48f7aa9e4d1ae4`, y_validation `6ebc6964cb5901f62ed223d63b589ba4f2c82df3887d3a35108f70b967165f5e`; canonical shape/dtype|i1 + int8bytes theo implementation, không phải SHA raw npz. Không thêm lại vào G3 manifest.

[Negative CLI run](../../results/scania_aps/g4/gate_a_negative_missing_evidence_20261102_01/run_summary.json) thiếu test evidence: exit1/BLOCKED/lifecycleFAILED, lưu diagnostics trước re-raise, không fit/scoring. Synthetic failure branches khác có kết quả trong R01 source-bound tests. Các thư mục `history_*` giữ cả initial114PASS/3FAIL, unsandboxed115PASS/2FAIL, thread_control_fix115PASS/2FAIL, validated117PASS, expanded127PASS, before_source_freeze127PASS. Chúng **UNBOUND_HISTORICAL_JUNIT/source_binding=NOT_CAPTURED**, không nguồn đủ để mở preflight; XML gốc vẫn local. Không đổi các lần fail thành pass hoặc gắn commit sau sửa cho XML cũ.

[Gate B handoff](../../results/scania_aps/g4/gate_a_delivery_20261102_01/gate_b_handoff.json) là manifest chuẩn bị, không executable: authorized=false, official_command/budget/runtime cap/thread policy=null. Sau independent review đạt, owner cần giao quyền/command Gate B riêng; source Gate A hiện không có real-fit entrypoint. Không tự yêu cầu đổi model params/thresholds đã duyệt. **READY FOR INDEPENDENT GATE A REVIEW**, chưa kết luận nghiệm thu G4.
