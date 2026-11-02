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
