# SC-G3-C — Implementation and validation handoff

Ngày: **2026-10-29 (Asia/Saigon)**. Owner đã giao SC-G3-C và phê duyệt P04/P05; G3 **đã triển khai, chờ independent review và owner nghiệm thu**, chưa tự chuyển board/Done hoặc mở G4.

Nguồn quyền và nội dung chuẩn ở [decision register, phụ lục P04/P05](decision_register.md). PR #14 merge/main base `f2217c3ea7c56f579ed8b82ef23db703055e6489`. Nhánh `codex/sc-g3-data-pipeline`. **Source commit cho hai run cuối (03/04):** `4789c0d6b8220a5f70758b019e4f0a639919e67c`. Delivery commit bổ sung evidence/docs giữ nguyên source/config đó. `worktree_clean=false` trong run là do artifacts/docs mới chưa commit; code digest xác định code đã chạy, không tự đổi thành clean.

## 1. Phạm vi và các ranh giới

- Scania riêng: `src/scania/{contracts,data,preprocessing,acquisition,artifacts}.py`, `tests/scania/test_pipeline.py`, hai script acquisition/pipeline, hai config/lock. Không sửa AI4I hoặc sản phẩm Antigravity/G2.
- P04: official Train60000, một chính sách split80/20 stratified seed42; giữ returned order. Hai lượt chạy cùng cấu hình là **tái lập**, không hai phương án chọn theo kết quả. Membership freeze local `data/processed/scania_aps/official_split.json`; mismatch không overwrite.
- P05: giữ170numericX, `na` missing, median/keep_empty_features/noindicators/copy, Train-only; LR scaler sau impute, tree không scale. Không drop hàng/cột, feature selection, weighting, SMOTE hoặc clipping.
- Parser dùng UTF-8 strict/noBOM, tìm header động, exact ordered whitelist từ G2, pos1/neg0 và outer-token trim như G2. Numeric grammar tường minh; overflow/underflow hoặc decimal spelling mất phân biệt khi round-trip float64 → STOP thay vì làm tròn để tạo duplicate giả. 0/-0 chuẩn hóa cùng số0. Exact-X hash buckets **có kiểm equality**, missing mask phân biệt; duplicate/conflict → BLOCKED trước splitter.
- No-Test: acquisition chỉ `ZipFile.read` tên Train và description allowlisted, không extractall hoặc đọc memberTest; parser chỉ nhận path officialTrain trong raw directory thuộc worktree; source size/SHA pin trước parse. Không có tham số Test/cache/evaluation ở CLI. G308 dùng sentinel và spy archive; đây là software guard, không tuyên bố OS air-gap hoặc chưa ai từng nhìn Test.

## 2. Acquisition và provenance thực

UCI421: `https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip`; opaqueZIP56.618.034bytes SHA5504d040… theo G2. Chỉ extract Train và description4.874bytes SHA57b1eb3c…. Train44.669.194bytes SHA `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da` **được Codex tính lại từ bytes local**, không còn chỉ đọc metadata G2.

Lượt tải đầu `acquire_a02a4dd5f9e3`:28.8959s trước source commit, log gốc giữ nguyên, entrypoint tại thời điểm đó được lưu snapshot/reconstruction có ghi rõ ở source_reference; helper acquisition không đổi. Lượt verify lại bằng committed code `acquire_4d1dccf1c9c4`:0.2691s, hashes khớp, không download lại/ghi đè raw. Không giả source commit đã tồn tại lúc lượt tải đầu chạy.

## 3. Môi trường khóa trước official split/fit

Dùng **.venv của worktree Codex**, Python3.11.9 (khác venv Antigravity); không thay requirements chung hoặc môi trường AI4I. Các packages thực tế được khóa riêng trong [g3_requirements.lock.txt](../../configs/scania/g3_requirements.lock.txt), config pin15 runtime/test dependencies; mỗi run lưu đầy đủ all_distributions. Numpy2.4.6/scipy1.17.1/sklearn1.9.1/joblib1.6.0/pandas3.1.0. `pip check`: No broken requirements found. Chưa kiểm cài mới từ PyPI hoặc tái lập ở OS/máy sạch khác; không tuyên bố đã chạy kiểm tra đó.

Probe API bằng synthetic data đã đạt: median/all-missing fallback0, giữ Validation observed value, clone unfitted. Config/version mismatch chặn trước parse/split/fit. Config là JSON canonical sortedkeys/compactUTF8/LF; objects sortkeys, arrays IDs giữ thứ tự. Source rawSHA là hash binary; code digest chuẩn hóa LF; stable digest loại timestamps/runtime/runID/sourcecommit (code digest vẫn khóa source).

## 4. Kiểm thử đã chạy

Lệnh: `.venv/Scripts/python.exe -m pytest tests/scania -q --junitxml=data/processed/scania_aps/g3_tests_final.xml`. **40/40 PASS**,10/10groups; JUnit chi tiết local, bản tổng hợp có test names/status/time public tại [test_results.json](../../results/scania_aps/g3/validation_final/test_results.json).

| Nhóm | Cases | Kết quả |
|---|---:|---|
| G301 | 12 | PASS |
| G302 | 2 | PASS |
| G303 | 3 | PASS |
| G304 | 1 | PASS |
| G305 | 1 | PASS |
| G306 | 3 | PASS |
| G307 | 13 | PASS |
| G308 | 2 | PASS |
| G309 | 2 | PASS |
| G310 | 1 | PASS |

G301 parser/error/no repair; G302 source/schema/config/version; G303 exact-X/mask/conflict/collision; G304 một call/seed42/exact returned order/disjoint/coverage; G305 ordered tuples/hash/noIDfeature; G306 median/scaler Train sentinels, constant/all-missing row/column/eight high-missing columns; G307 new missing/invalid/nonfinite/precision; G308 Test path/archive spy; G309 failure evidence/checksum tamper/exclusive write; G310 same-policy reproduction và fold-clone unfitted.

Validation sentinel cực lớn không thay median/mean/scale; Train-all-missing fill0 cho missing, giá trị15 quan sát ở Validation vẫn15. Cột hằng vẫn170X và LR scale=1/output0. Mọi tests dùng synthetic, không officialTest.

## 5. Kết quả chính thức

| Partition | N | neg | pos |
|---|---:|---:|---:|
| Train | 48000 | 47200 | 800 |
| Validation | 12000 | 11800 | 200 |

Header dòng21;170X, uniqueX60000, duplicate/conflict0. Mỗi tree/LR output đúng170cột/hữu hạn, imputer/scaler chỉ fit48000, Validation transform-only. Không predictive estimator nào được tạo/fit.

Hai run đầu được giữ nguyên. Sau QA bổ sung verifier canonicalLF/CRLF (và test thứ40), chỉ source `artifacts.py` thay đổi; parser/split/preprocessing/config/dependencies không đổi. Bốn run dùng cùng frozen membership và mọi array/statistics hash giống nhau. Cặp01/02 có cùng stable digest riêng; **cặp cuối03/04 có cùng stable digest mới vì code digest bao gồm verifier đã sửa**, không do đổi split hoặc chọn run có kết quả thuận lợi.

| Run | Source commit | Seconds | Status |
|---|---|---:|---|
| official_20261029_01 | 3ff36a5 | 15.6395 | PASS |
| official_20261029_02 | 3ff36a5 | 15.5414 | PASS |
| official_20261029_03 | 4789c0d | 88.5334 | PASS |
| official_20261029_04 | 4789c0d | 87.8397 | PASS |

Runtime bao parse/audit/split/preprocess/local arrays, chốt trước summary/checksum final writes; không gọi là full process wall-clock. Hai manifest cuối khớp hoàn toàn; sourceSHA/IDs/preprocessed arrays/statistics khớp cả bốn run:

| Hash | Giá trị |
|---|---|
| Config | `06f4ffd56e4c599774fb7113cd68c406070bb9120d8c5e9ef7c7a47d6bfb59c6` |
| Schema | `fb832a2c220bdcd38d970a1dba34bb1e3d1d08900490e4b258a21b9c6d50f634` |
| Train ordered IDs | `32e559a01d4806789c16524d040ebb11692d33a9cd3ea83907afb6e67fd618f1` |
| Validation ordered IDs | `e494719437e70ca804190d623af9eaa068165aa4a1e44399888ea0489c5f19c6` |
| Full local membership | `543b61e8c436c2f0f394b000e9e6ca9a8097a14b71373a8d9b2a3d3f4fd97a6b` |
| Code | `126821f9b59f2bd8e6b02817e696a195601244190b176a6d2fc910a15f61a4f8` |
| Stable digest hai run | `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb` |

Array/statistics hashes đầy đủ trong [stable manifest](../../results/scania_aps/g3/official_20261029_03/stable_manifest.json);5public text artifacts của mỗi run có checksums canonicalLF riêng; verifier chấp nhận GitCRLF và vẫn bắt nội dung bị sửa. Không upload raw/IDs/label lists/processed matrices hoặc fitted preprocessors. Chúng ở `data/processed/scania_aps/<run_id>/`, membership.npz/4npy/2joblib local ignored. Cùng physical source ID tuple `[sourceSHA,"train",row1based]`, không phải vehicle/time ID.

Kiểm tra bổ sung trực tiếp rawTrain/local artifacts: disjoint/coverage, labels/IDs/hashes/output đều khớp, medians đối chiếu `np.nanmedian(X[train])`, scaler mean đối chiếu mean của imputedTrain, clone unfitted. Tám cột missing>50% được giữ: ab_000,bm_000,bn_000,bo_000,bp_000,bq_000,br_000,cr_000; cd_000 vẫn giữ và LR output0. Script kiểm chứng, result và lịch sử ở `results/scania_aps/g3/validation/`; kiểm đối chiếu cặp cuối ở `validation_final/real_data_verification.json`. Một lần kiểm bổ sung ban đầu FAIL do checker scope tính nhầm file mới hợp lệ; đã sửa riêng checker so protected existing base files, không thay production code/config/data/split hoặc expected preprocessing để tạoPASS. Lần kiểm lại PASS; giữ lịch sử này.

## 6. Tái lập

Từ repository root trong Codex worktree, đúng Python3.11.9/deps đã khóa. Giữ source/config của final source commit; docs/evidence delivery không đổi code digest:

```powershell
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m pytest tests/scania -q
.venv/Scripts/python.exe scripts/run_scania_acquire.py
.venv/Scripts/python.exe scripts/run_scania_pipeline.py --run-id reproduce_unique_01 --expect-stable efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb
```

Chọn **run-id mới**, không thay seed/config. Acquisition không overwrite raw; mismatchSTOP. Runner đối chiếu official_split.json hiện có trước fit; stable mismatch giữ BLOCKED evidence và raise. Run-id trùng bị từ chối, không overwrite lần trước. Không có chức năng xóa/reset split lock. Raw/processed được phép tái tạo trong worktree khác được giao quyền, nhưng không đọc worktree Antigravity.

Muốn kiểm bổ sung: copy `results/scania_aps/g3/validation/verification_script.py.txt` thành local `data/processed/scania_aps/verify_g3.py`, chạy từ root. Output result hiện đã tồn tại nên writer exclusive sẽ từ chối overwrite; dùng checkout sạch hoặc sửa **đường dẫn evidence mới** của checker khi độc lập review, không sửa dữ liệu/expected hashes. Public run evidence/sourcecommit vẫn là record gốc.

## 7. Bảo toàn và giới hạn bàn giao

120 existing base files ngoài hai tài liệu Scania được cấp quyền giữ nguyên, gồm AI4I, notebook/G2sáuruns và artifacts Antigravity; kiểm bằng Git. Không rerun AI4I training/baseline hoặc full legacy tests trong nhiệm vụ này. Không thay PROJECT_SPEC/TASK_BOARD/README/AGENTS/ROADMAP/requirements chung. Metadata public không chứa paths cá nhân, IDs hoặc nhãn chi tiết.

Môi trường reuse existing Codex venv, không giả fresh installation. Split không chứng minh thời gian/vehicle-disjoint/causal validity. Đây là implementation self-validation, **chưa phải independent acceptance**. G4 cần owner nghiệm thu, task và quyết định/config riêng (P02/P06/P07/P08 nếu còn chờ). Test luôn SEALED trong task này, không tuyên bố về toàn bộ lịch sử người khác.

```text
P04 IMPLEMENTATION: PASS
P05 IMPLEMENTATION: PASS
G3 TESTS: PASS
SPLIT REPRODUCIBILITY: PASS
TRAIN-ONLY PREPROCESSING: PASS
OFFICIAL TEST: SEALED
AI4I ARTIFACTS PRESERVED: YES
READY FOR INDEPENDENT REVIEW: YES
READY FOR G4: NO – PENDING OWNER ACCEPTANCE
```
