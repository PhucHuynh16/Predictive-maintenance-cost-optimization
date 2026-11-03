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

## Gate B1 — infrastructure implementation, pending review (2026-11-02)

Các đoạn Gate A phía trên là lịch sử bàn giao. Owner đã [ACCEPTED Gate A](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6572371245), yêu cầu PR16 giữ Draft/no merge. Task mới **OWNER AUTHORIZATION — SC-G4-C GATE B1**, attachment `9fe68a41-5de9-4abf-8354-3b37d5db19c6`, chỉ cấp hạ tầng/fixtures/read-only checks và append tài liệu này; **chưa cho commit/push/cập nhật Issue/PR**, chưa giao Gate B2. Trước sửa code đã fetch main, đọc đủ snapshot47comments Issue2 và đối chiếu owner/latest; PR16 vẫn open/draft/merged=false/HEAD `67df203c99fb77ec1b0949a61a7780dd0eed6e2e`, base/origin-main `d78cfcd30601090211003ef3a6a6751f83dd6eb3`, Codex branch sạch tại bắt đầu. Không có comment mới sau readiness6572602866 làm đổi scope. Public GitHub API được đọc, không mutations; browser local bị tắt và connector methods không có trong session. Không truy cập worktree Antigravity.

### IMPLEMENTED — separate infrastructure, no real execution path

7file mới: `src/scania/g4_b1_contract.py`, `g4_b1_windows.py`, `g4_b1_worker.py`, `g4_b1_supervisor.py`, `g4_b1_evidence.py`; `scripts/run_scania_gate_b1.py`; `tests/scania/test_g4_b1.py`. Giữ nguyên mọi module/config/test Gate A/G3. Không tạo config được phê duyệt mới, không thay P02/P06/P07/P08 hoặc thresholds PRIMARY0.5/SECONDARY10/510.

Supervisor chỉ stdlib, không import NumPy/sklearn ở top-level. Tạo worker process **suspended**, tạo/config/query Windows Job Object, assign và IsProcessInJob trước ResumeThread. Kill-on-close, job committed-memory cap và active-process limit được query/readback. Không breakaway flags. Profile mock giới hạn2active processes để tính cả Windows venv redirector và worker Python; đây không phải tuyên bố chỉ1OSprocess hoặc policy Gate B2 đã duyệt. Host child-attempt test bị từ chối; job cumulative process count có thể lớn hơn active limit (khác đơn vị). Một worker mock/attempt, không workerpool hoặc estimator jobs.

Wall deadline tuyệt đối tính từ ngay trước CreateProcess tới workerexit, bao gồm startup/import/thread checks, không reset theo stage; poll20ms. Timeout/crash/error => TerminateJobObject nếu còn active, xác minh active_processes=0 trước kết thúc. Parent ghi reservation/journal flush+fsync, sở hữu final diagnostics/checksums; không dựa worker finally. Worker claim exclusive/one-use, run-id collision không ghi đè lượt trước; B1 fit budget luôn0. Không CLI official/reproduce/data/Test/threshold/seed/solver override; `real_execution_gate()` luôn BLOCKED dù truyền authorized=True. Không có API fit/predict/score trong code B1. Runtime OS không hard-real-time: observed timeout overshoot khoảng6–10ms, không báo deadline chính xác tuyệt đối. Process creation/kernel/host crash/power loss không thể bảo đảm luôn có final JSON; reservation/journal tồn tại, incomplete không là PASS. Disk/write error không được báo evidence đã lưu nếu ghi thất bại.

**Giới hạn profile mock — không phải owner-approved production limits:** 64MiB available RAM tối thiểu, 512MiB job committed memory; wall1s cho sleep/busy/native-busy, 15s cho các scenarios khác, cleanup5s. Các giá trị này chỉ kiểm tra hạ tầng bằng worker không dữ liệu/không ML. Production RAM/timeout fields=null/PENDING_OWNER_B2_VALUES. **4GiB/300s vẫn PROPOSED**, không được dùng kết quả mock để tự chốt hoặc nới điều kiện vận hành B2. Worker real-data vẫn bị từ chối bất kể tài nguyên có đủ. Không sửa pagefile/registry/ACL/dependencies/DLL/venv/OS settings.

Native probe đặt env1thread trước imports (OMP_NUM_THREADS/OMP_THREAD_LIMIT/OPENBLAS_NUM_THREADS/MKL_NUM_THREADS/BLIS_NUM_THREADS/VECLIB_MAXIMUM_THREADS/NUMEXPR_NUM_THREADS=1, OMP_DYNAMIC/MKL_DYNAMIC=FALSE). Worker ghi stage import, dùng Unicode Win32 module inventory+DLL hashes rồi threadpoolctl discovery/limits(1)/check cảBLAS vàOpenMP; thiếu/unknown/pool≠1/null/discoveryerror => BLOCKED. Env không là bằng chứng num_threads. Audit hook trong worker từ chối raw/processed/CSV/NPY/NPZ/ZIP/Test trước open và writes ngoài own-run; software guard không là OS sandbox cho arbitrary nativecode.

### TESTED / VERIFIED — evidence from this task

[Final bound suite](../../results/scania_aps/g4/gate_b1/b1_regression_02/tests_summary.json): **174 passed,0failed/error/skipped**, pytest10.40s; supervisor duration11.106457s. **47B1 cases (B1G01–B1G26) +87Gate A +40G3**, source captured before pytest, source/protected unchanged after. B1 tests gồm config/type/limits, memory before launch, normal/crash/timeout/finalization, cleanup failure, source mutation, repeat/collision, deterministic mock, thread missing/unknown/>1/bool/discoveryfail, env/importorder, output/Test aliases, checksums/missing/tamper/CRLF, no-fit AST/CLI/direct-worker negatives, dependency mismatch, forgedresult, I/O fail, real Win32 assignment/kill/kill-on-close and suspended assignment-denial. Không lấy Test/Validation thật làm fixtures.

Lượt `b1_regression_01` giữ **173PASS/1FAIL** do fixture Git của Gate A không ghi được .git/config trong sandbox. `b1_regression_02` chạy ngoài sandbox với quyền thích hợp, không đổi test/oracle/source giữa2lượt. Raw JUnit chứa path chỉ local ngoài repo; summary đã hash/bind source, commit mới=null vì owner chưa cấp quyền commit. Log failure đầu giữ nguyên để chủ dự án review local, chưa phải gói sẵn sàng publish. Các lượt B1-only trước đó36/36 rồi46/46 là kiểm tra trung gian, không thay final174case evidence.

Host Windows qualification, source digest `ba9a6dd24134f8f650c766f35135f3cb1f94945a54ec014129ff09391be085e0`:

| Run prefix `b1_delivery_` | Actual result | Safety assertion |
|---|---|---|
| normal_01 / normal_02 | PASS, wall0.192051s/0.169348s | Job empty verified; same stable digest `7e9b05ff471a872ce4ed7d33ac245ec4475b49470367a00cd712d600dccbbd69` |
| crash_01 | FAILED, worker exit37, wall0.171196s | Missing worker result không thành PASS; diagnostics saved; job empty |
| sleep_01 / busy_01 / native_busy_01 | FAILED/RUN_WALL_TIMEOUT, wall1.010381s/1.005998s/1.008272s | Sleep, CPU loop và blocking native call bị supervisor dừng; job empty |
| memory_limit_01 | PASS control, wall0.210970s | Synthetic allocation>512MiB bị từ chối, không OOM toàn máy |
| child_attempt_01 | PASS control, wall0.294285s | Extra process creation denied trên host/job layout này |
| thread_probe_01 | **BLOCKED**, wall2.839634s | num_threads chưa verified; không fit; job empty |

`b1_simulated_insufficient_memory_01` ghi rõ memoryreading SIMULATED=1byte => BLOCKED trước worker; `b1_simulated_invalid_configuration_01` thử300s thay fixed mockprofile => BLOCKED, không suy ra300s đã được phê duyệt. Hai test này là mô phỏng gate, không host thiếu1byte. All evidence mới dưới [Gate B1](../../results/scania_aps/g4/gate_b1/), mỗi qualification có reservation/config/source/environment/journals/workerclaim nếu đã chạy/resource/diagnostics/runsummary/checksums. Failed/blocked có thể thiếu workerresult thật, không fake completion. Không ghi models/probabilities/real baseline metrics.

262existing files giữ nguyên trong suốt test/hostqualification trước appenddoc, digest `980721cbc1caca8a5abca75c75b3d3a349ea259fbcf944da059eab3d1261da87`. Tài liệu này chỉ append sau kiểm; các261files còn lại exact/canonical match acceptedtree. Không gọi lại G3 runner hoặc broad digest rồi sửa manifest; không đọc raw/processed/ZIP/Test trong B1, không rerun G2audit hoặc G3pipeline. Regression chỉ fixtures; no actual Train/Validation estimatorfit/scoring. Chưa rehash raw G3inputs trong nhiệm vụ này: current data integrity ngoài accepted history **NOT TESTED**, không lấy historic PASS thay preflight B2 sau này.

### BLOCKED / NOT TESTED / PROPOSED — no owner acceptance claimed

Native verification **BLOCKED** thật: module inventory nhận3DLL vàSHA (NumPyOpenBLAS `63c857e7…`, SciPyOpenBLAS `64eda39e…`, vcomp140 `95d4ce4a…`), threadpoolctl FileNotFoundError khi discovery NumPyOpenBLAS. `num_threads=null/DISCOVERY_OR_VERIFICATION_FAILED`; không kết luận môi trường đang chạy1compute thread, không sửa DLL hoặc deps. `b1_initial_thread_probe_01` timeout15s được giữ; thêm stage diagnostics/error-mode để ngăn native-error dialogs, lượt import_diagnostics và verified/delivery sau đó BLOCKED đúng nguyên nhân. Không tăng timeout/memory để ép PASS.

RAM available ở delivery probe2,508,808,192bytes (~2.34GiB), thấp hơn proposed4GiB nhưng không phải vi phạm production limit đã duyệt. Job/memory/timeout đã VERIFIED trong mock profile trên Windows hiện tại; **300s full realrun,4GiB cap, real fit concurrency/convergence, peakRAM thật, process/fit budget official+reproduction, cross-OS/freshenv và same-worker prefit checks thật: NOT TESTED/NOT IMPLEMENTED FOR B2**. B1 không triển khai thực nghiệm để lấy kết quả đó. ASCIIvenv đề xuất trong Readiness chưa được cấp quyền/khởi tạo; không chuyển môi trường hoặc patch dependency.

Đề nghị Antigravity review **local diff + source hashes**, không review nhầm remotePR16 như đã có codeB1; tách mock tests khỏi hostqualification; kiểm suspended/job readback/cleanup/finalization/nooverwrite, native discoveryBLOCKED, no-real/Test guards, regression evidence và append-only preservation. Owner xem xét quyền commit/push/Issue riêng sau review bản này. **Gate B1 implementation/tests sẵn để xem xét với blocker native rõ ràng; Gate B2 BLOCKED/NOT AUTHORIZED.** Không tự nghiệm thuB1, tự giaoAI khác, mergePR16 hoặc sangG5/Test.
