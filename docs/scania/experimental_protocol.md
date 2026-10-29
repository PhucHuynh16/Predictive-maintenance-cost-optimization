# SC-G1-C — Experimental protocol design Scania APS

> **Cập nhật SC-G3-C ngày 2026-10-29:** G2 được owner nghiệm thu; PR #14 đã merge. P04/P05 đã được owner phê duyệt và giao triển khai trong task hiện tại. Xem phụ lục phê duyệt cuối tài liệu; các đoạn G1 “chờ duyệt/chưa giao” bên dưới là lịch sử.

Ngày: **2026-10-25 (Asia/Saigon)**. **Thiết kế chờ nghiệm thu, không lệnh thực thi.** [Decision register](decision_register.md) là nguồn trạng thái D/P/A/L và các gói P01–P10. P0 đã nghiệm thu/PR #12 merge ở `c52d89ef7d9d0ee8f5e35f12c2f0f63777835d4b`; SC-G1-C hiện chỉ tạo bốn Markdown này, không sửa file chung/AI4I/code/config/tests/results/data hoặc sản phẩm Antigravity.

## 1. Ranh giới dữ liệu và quyền đã có

**D:** UCI 421, pos1/neg0, action dương APS, objective10FP+500FN/cost units, capacity 10%; official Train 60.000 chia Train 48.000/Validation 12.000 stratified split seed 42; official Test 16.000 khóa tới G10; preprocessing/missing Train-only; B0/stump/LR, RF về sau và provenance/tests/reproduce. Full model/scaler/imputer/threshold/metric config chưa được phê duyệt bằng việc giao G1.

| Dữ liệu | Dùng để làm gì theo giao thức đề xuất | Không được dùng để làm gì |
|---|---|---|
| Official Train 60.000 trước split | Acquisition/integrity/schema/format/target-token/count/duplicate audit cần thiết trước split, do SC-G2-A được giao riêng | Fit imputer/scaler/model, lọc feature theo thống kê/nhãn hoặc thử phương pháp trước khi khóa split |
| Train 48.000 sau split | Fit preprocessing/model, EDA phát triển; calibration chỉ train folds khi được giao sau này | Dùng raw/Test từ AI kia hoặc tự mở calibration/HPO chưa được giao |
| Validation 12.000 | Transform bằng fitted Train preprocessing; evaluation/selection chỉ trong scope/budget đã duyệt | Fit imputer/scaler/calibrator, feature selection hoặc Train+Val refit ngầm |
| Official Test 16.000 | Hiện chỉ giữ sealed; G10 load/transform/evaluate bằng artifacts/policy đã khóa khi có quyền riêng | Trước G10: parse/EDA/missing histogram/class distribution/feature association/fit/selection/metrics hoặc chia lại |

Development validation đã dùng để lựa chọn sẽ có selection bias; không gọi best Validation cost là unbiased final estimate. Official split không chứng minh temporal/vehicle-disjoint/causal validity; thiếu timestamps/vehicle IDs/horizon phải công khai. Không tuyên bố Test hoàn toàn chưa từng được người khác xem; G1 không đọc Test.

## 2. Data contract P01/P03/P10 — cần chốt trước audit G2

Nguồn chính [UCI 421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks), DOI [10.24432/C51S51](https://doi.org/10.24432/C51S51). Các tên nguồn dự kiến `aps_failure_training_set.csv`, `aps_failure_test_set.csv`, `aps_failure_description.txt` là metadata; chưa có bytes/hash local trong G1. Chọn route acquisition trong lệnh G2: **ưu tiên official Train-only**; nếu chỉ có archive chứa cả Test, cần cho phép rõ lưu archive opaque/custodian và chỉ extract Train/description. Không mở/extract/parse Test để “kiểm tra đủ 16.000” trước G10; không dùng package loader có thể gộp partitions ngầm.

Hợp đồng parser/audit đề xuất, chưa có code:

| Trường | Quy tắc đề xuất | Phần cần audit/stop |
|---|---|---|
| Original bytes | Không overwrite; SHA-256 archive/Train/description nếu thực sự tải; URL cuối/DOI/time/size/notice/version. Không coi hash tự tính là checksum có chữ ký UCI | Hash khác manifest đã khóa hoặc nguồn không rõ→BLOCKED, không tự thay bằng mirror |
| Header/preamble | Decode encoding/BOM có log, tìm header có cột class đúng một lần; count/column order/row widths rõ; không hard-code skip20 từ P0-A | Unknown encoding/header duplicate/width/count mismatch→dừng, không auto-rename/drop cột/hàng |
| Target | Chỉ pos→1/neg→0 đã D; raw token giữ audit. Nếu cần trim whitespace phải log trong contract; không lowercase/coerce unknown→neg | Missing/unknown target ERROR; không impute labels hoặc sửa conflicts |
| X schema | Ordered whitelist numeric predictors sau audit; loại class/source-row ID/path/partition. Dự kiến170X+class, chưa verified | Metadata171-feature ambiguity giải bằng header thực; không giả cột vật lý/dấu/domain AI4I; schema khác kỳ vọng trình lại |
| Missing | `na` là marker nguồn dự kiến; missing mask tách riêng; chỉ missing tokens được contract chấp nhận chuyển NaN ở X | Token lạ/Inf/nonfinite không phải missing đã duyệt→ERROR; không global pandas coercion biến mọi parse failure thành NaN |
| Source-row ID | Tuple `(official_train_sha256, official_partition_name, data_row_number)`; row_number1-based sau header, source order cố định | Không phải vehicle/time ID. ID duy nhất, không làm feature; giữ bytes/preamble metadata để tái dựng số dòng |
| Duplicates | Trước impute, khóa toàn bộ orderedX parsed values + missing mask, không rounding/target/ID; đếm số hàng trong nhóm, nhóm, hàng dư và nhóm xung đột label | Phân biệt identical raw-text row với exact numeric-X; nếu canonical hashing dùng phải kiểm equality để tránh collision. Có nhóm/conflict/new grouping→BLOCKED split theo P03, không tự dedup/majority vote |
| Dependence/domain | Tìm metadata về group/time và constraints hợp lệ nguồn; không tạo timestamp/vehicle ID từ row_number hoặc đo ACF nhiệt AI4I | Nếu phát hiện cấu trúc thay protocol thì trình owner; chưa có bằng chứng rows IID, không khẳng định split đo tương lai |

Audit được phép phát hiện cột/hàng all-missing/constant, số liệu chất lượng trên 60.000 để báo vấn đề; **không biến thống kê full 60.000 thành median/scaler/feature-selection mask**. Nếu chọn drop cột theo missing rate/variance sau này, criterion phải duyệt trước và fit chỉ Train 48.000/fold. Đề xuất P05 hiện không drop, không indicators; audit không tự chọn lại strategy.

Đối chiếu P0-A: metadata60k/16k/170X, skip20, missing>50%/>80% chưa có CSV hash/script/run log kèm báo cáo để coi audit PASS; các giải thích nguyên nhân missing/khẳng định model 0.5 thất bại không là kết quả được kiểm chứng. Không dùng chúng để tự loại cột/tune threshold. License notices UCI CC BY4.0 và GPLv3-or-later trong mô tả phải lưu nguyên trạng khi acquisition được giao, không tự chọn license mã/redistribute raw. [Mô tả UCI](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks).

## 3. Split contract P04 — ratio/seed D, API/order còn P

Chỉ sau G2 audit được nghiệm thu và findings P03 đủ quyết định. Đề xuất một lần `train_test_split` trên positions official Train theo source-file data-row order, `test_size=0.20`, `shuffle=True`, `stratify=mapped_class`, `random_state=42`; Train là80%, Validation20%. Giữ returned order của sklearn, không sort lại theo nhãn/feature. Official Test không là input argument, không ghép 76.000 rồi chia60/20/20.

Phải kiểm 48.000/12.000, disjoint và union bằng 60.000 source-row IDs, không mất/nhân bản rows. Lưu membership chi tiết local, ordered hashes public; retry khi tái lập chỉ cùng versions/bytes/order/seed/algorithm, **không thử nhiều seed/split rồi chọn**. Duplicate/group issues không cho phép tự đổi thành group split, ratios hoặc lọc hàng để đạt số lượng; dừng/trình quyết định mới nếu ảnh hưởng D06.

Provenance đề xuất: dataset ID `scania_aps_uci421`, protocol version đóng băng theo quyết định, cost-model ID `aps_fp10_fn500`; raw/train hash và schema hash, source order/encoding/data-row offset; splitter/dependency versions/all args/seeds/ordered Train+Validation IDs hashes, full config/source commit/hash, audit approval reference/status. Chưa có giá trị hash Scania cụ thể trong G1.

Encoding đề xuất: canonical UTF-8 JSON, sort object keys/compact separators/LF; mảng ordered IDs không sort; metadata source tuples và schema trong hash. Trạng thái/runtimes/timestamps tách khỏi stable digest. Thư mục run mới/exclusive writes, không overwrite thất bại cũ. Manifest không đưa nhãn/rows Test, IDs chi tiết hoặc prediction vectors lên GitHub.

## 4. Preprocessing P05 — D về Train-only, chưa chốt imputer

Đề xuất cơ sở: numeric parser+validator theo schema audit; `SimpleImputer(strategy='median', keep_empty_features=True, add_indicator=False, copy=True)` fit Train 48.000. Cột all-missing ở Train giữ chiều và fill0 theo contract được test với version khóa; hàng X all-missing có class hợp lệ giữ lại/impute, không tự drop. LR thêm StandardScaler với mean/std default **sau** impute; stump/RF dùng numeric đã impute, không scale bắt buộc. Float64/output schema cố định theo audit; không OHE Type hoặc feature engineering cơ chế AI4I.

Median/fallback0/giữ rows/no indicators/no column drop là P05, không phải đã được S7 duyệt chi tiết. Với cột all-missing lúc fit, chỉ các ô thiếu được thay bằng0; ô có giá trị quan sát được ở Validation vẫn giữ giá trị đó, không ép toàn cột thành0. Nếu audit cho thấy số học/precision/schema/all-missing chưa đáp ứng contract, dừng để chốt; không tự thay bằng KNN/mean/fill0 toàn bộ hoặc SMOTE. Numeric ranges chưa rõ không áp rule positive-temperature/speed của AI4I. Sentinel tests phải chứng minh mean/median/statistics không học Validation. Cột chỉ missing ở Validation vẫn transform theo imputer Train; output finite cùng số cột/order, không refit.

Mọi transformer/model nằm trong Pipeline có thể clone. Calibration tương lai phải fit preprocessing/model đúng từng train fold; không carry preprocessor đã fit cả 48.000 vào fold và gọi đó là OOF. B2 đề xuất no post-calibration/no Train+Val refit (P07), RF calibration method/folds/ensemble còn L trước G5, không tự dùng 5-fold sigmoid AI4I. [Imputer API tham khảo](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html), không thay kiểm thử phiên bản thực.

## 5. Baseline/evaluation design P02/P06/P07/P08

B0 a0, không fit/no score; B1 stump full params P06, B2 LR full params P07 tại [register §4](decision_register.md). Fit chỉ Train, predict p lớp1 trên Validation; chọn index theo classes_, không giả cột thứ hai luôn đúng khi mapping sai. Cả B1/B2 đề xuất p>=0.5 cố định, không CV/HPO/weighting/calibration/refit, không threshold search G4. Stump fit split trên Train không phải tune feature/threshold bằng Validation. Depth0/root-only và all-negative predictions là kết quả hợp lệ, không tự sửa để tăng recall/cost saving.

Comparator `.predict`/argmax ở tie 0.5 có thể khác `>=`, nên phải dùng đúng policy đã được chủ dự án chọn và tests; [tree API](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html). LR params theo API 1.9.1 là đề xuất, không cài/thay version G1; model seed 42 là P, split seed 42 là D. ConvergenceWarning/score invalid đề xuất FAILED, log/no retry solver/C/τ; lỗi không trở thành “baseline infeasible”.

Cost/metrics/output contract ở [cost review](cost_model_review.md). Trước baseline thật: cost/constraints/input/metrics/leakage tests synthetic PASS. Cùng G3 manifest/cost10FP+500FN/capacity/metric exceptions cho B0/B1/B2/P; infeasible vẫn có raw result row, không lọt feasible ranking/top-k. Runtime/versions/command/source commit/config/seeds/split/hash phải có; reproducibility giữ nguyên cả run đầu/tái lập, không chọn run đẹp. Test không thuộc runner development API.

## 6. Tiêu chí unit tests G3 và audit/stop gates — chưa thực hiện

| ID | Ca cần test sau giao G3 | Oracle/tiêu chí dự kiến |
|---|---|---|
| G301 | Parser synthetic header/preamble/BOM/width/schema/labels/tokens | Header đúng/class unique, pos1/neg0; unknown/missing label, extra column, malformed row/error không repair; không hard-code skip20 |
| G302 | Hash/schema/config/version mismatch; input data không phù hợp | BLOCKED trước split/fit; log mismatch và source, giữ bytes/artifact cũ |
| G303 | Duplicate-X có missing mask; cùngX kháclabel/ID | Key không target/ID; group counts đúng; dừng split có findings, không dedup tự động |
| G304 | Split stratified80/20 fixture independent | Một call/seed 42/giữ order, disjoint/coverage, determinism; Test không argument; kích thước thật 48.000/12.000 chỉ audit được khi task thật |
| G305 | Row ID/header-offset/ordered hashes | Bản gốc/order tái lập cùng IDs; ID không vàoX, mismatch order bắt được; không gọi source-row là vehicle/time |
| G306 | Median/scaler sentinel Train vs Validation; all-missing column/row | Fitted statistics chỉ Train/fold; behavior P05 đúng, dimension/order stable; không refit hoặc drop ngầm |
| G307 | Missing mới ở Validation, Inf/token lạ, numeric overflow/precision | Missing được xử lý theo contract; invalid ERROR, không coerced thành median hoặc silently round gây duplicate giả |
| G308 | No-Test file sentinel và spies ở loader/transform/model | Không open Test raw/labels/IDs/cache, không transform/evaluate, kể cả bước chọn config/preprocessing |
| G309 | Exclusive writes, failure/blocked logs, read-only paths AI4I | Run-id mới, giữ mọi trạng thái thất bại, không overwrite source/split/model AI kia |
| G310 | Two reproducibility runs và cloned fold-preprocessing | Same stable input/output digest ngoài volatile fields; clone unfitted; không select split/seed theo model score |

G4 có 16 nhóm test design C01–R02 trong [cost review §5](cost_model_review.md), không có số PASS/FAIL Scania. Mọi fixtures độc lập tổng hợp, không real Test hoặc lấy nhãn Validation làm fixture. Không dùng kết quả 43/132 PASS AI4I để bỏ qua Scania tests.

Điều kiện dừng đề xuất: nguồn/bytes/schema/rows/labels không khớp; duplicate/conflict/group mới; thiếu policy cho all-missing; stratify không đáp ứng; fitted preprocessing thay output schema hoặc học ngoàiTrain; insufficient class support/calibration tương lai; warning/nonfinite/numerical overflow; vô tình mở Test; thiếu quyền/môi trường/tài nguyên. Giữ evidence, báo owner trước phần phụ thuộc; không sửa raw/y/drop/đổi ratio/seed/folds/solver để vượt gate. Policy capacity violation riêng là INFEASIBLE, không tự dừng toàn bộ báo cáo hoặc tuning baseline.

## 7. Đề xuất giao SC-G2-A — chưa kích hoạt Antigravity

Chủ dự án cần nghiệm thu G1, chốt P01/P03/phần audit P10 và cấp **task/quyền cụ thể** sau đây. Không cần chốt LR/RF/H hoặc imputer median để chỉ acquisition/audit. Không tự gửi message/giao việc cho Antigravity bằng tài liệu này.

| Phạm vi đề nghị cấp cho Antigravity | Công việc và giới hạn |
|---|---|
| `data/raw/scania_aps/<source-hash>/**` local ở worktree Antigravity | Tải official Train/description/notices khi được phép, no overwrite; route chứaTest chỉ theo custodian authorization. Không dùng raw/worktree Codex hoặc thư mục AI4I |
| `docs/scania/data_dictionary.md` | Schema source-derived, mapping labels đã D, ordered feature roles/units unknown/missing tokens; tách metadata với kết quả parser/audit thật |
| `docs/scania/eda_findings.md` | Giai đoạn G2 ban đầu chỉ integrity/quality/duplicates/missing findings và stop recommendations; không fit/association feature selection trên 60.000 |
| `notebooks/scania/00_source_audit.ipynb` | Code kiểm toán có thể tái lập trên official Train, không production pipeline/model fit hoặc Test; ghi commands/environment/hash/runtime và output thật |
| `results/scania_aps/g2_audit/**` | Logs/provenance/audit summaries nhỏ, không rows/labels lists/raw. Đây là **quyền bổ sung cần chủ dự án cấp rõ** vì results mặc định Codex trong AGENTS |
| Sau G3: `notebooks/scania/01_eda.ipynb`, `figures/scania/eda/**` | Chỉ EDA phát triển trên Train 48.000 cùng manifest IDs đã khóa; cần giao quyền riêng/phase2, không đọc processed worktree Codex. Membership ở worktree riêng phải khớp hashes; Validation/Test không phục vụ feature selection |

G2 không sửa bốn tài liệu G1 Codex, AI4I dictionary/EDA/figures, source pipeline/tests/config/metrics Codex hoặc file chung. Không drop cột/hàng/repair label; không lập “feature whitelist tối ưu” theo toàn 60.000. Quyền tạo path mới chưa được bảng AGENTS phân cụ thể phải ghi trong task G2; không coi tên `docs/scania/` tự cấp quyền. `.gitkeep`, README/dataREADME/requirements/spec/board/AGENTS không thuộc quyền đề nghị tự sửa.

Deliverables G2 để chủ dự án nghiệm thu: finalURL/DOI/time/size/hash/notices; parser header/preamble/encoding/count; labels/formats/schema finite/na; raw numeric exact-X duplicates/conflicts; quality flags; status/commands/versions/runtime/source; stop findings và đề xuất. **Không** yêu cầu đo Test 16.000 bằng parse. Phải nêu0/unknown/không kiểm tra đúng nghĩa, không tự điền PASS từ metadata. Có bất thường thì báo, không triển khai split; sau đó chủ dự án duyệt findings/P04/P05 rồi giao Codex SC-G3-C.

Namespace production dự kiến `src/scania/**`, `tests/scania/**`, `configs/scania/**`, `scripts/run_scania_*.py`, `results/scania_aps/{g3,g4}/**`, local `data/processed/scania_aps/**`; đều là **đề xuất task sau**, không tạo ở G1. Scope/tests/config log rights G3/G4 cần cấp riêng. AI4I paths không di chuyển/đổi tên, source import/refactor chung chỉ sau quyền phù hợp và regression verification.

## 8. T9/T10 ở giai đoạn sau và cơ chế Test lock

RF family D, còn L: full params/seed/class weighting/calibration method/folds/ensemble, train-fold preprocessing trước G5; H/order/search algorithm/attempt accounting/pruning/retry/seeds/runtime/fair comparison trước G7; scenarios/multi-seed/sensitivity/CI trước G8. Không tự dùng 30 trials/TPE/5-fold sigmoid hoặc seeds AI4I. Nguyên tắc train-only/fold-safe vẫn phải giữ khi chi tiết được chọn.

Environment P10: đề xuất Python 3.11 riêng từng worktree, snapshot đầy đủ dependency/API/platform/threads; Scania version lock phải kiểm chứng trong task phù hợp và ghi vào config/metadata được cấp quyền. Môi trường AI4I có snapshot 3.11.9/sklearn1.9.1 là lịch sử, chưa kiểm tra lại G1 và không chứng minh imputer/model Scania chạy đúng. Nếu version khác API đề xuất thì trình lại mapping, không silent fallback hoặc sửa requirements chung.

Test custody đề xuất: dev entrypoints chỉ allow officialTrain/Train/Validation artifacts được hash/whitelist, deny Test files/labels/cache; không nhận tham số Test. Custodian giữ officialTest/archive opaque tại path tách quyền, public metadata chỉ source/hash/size/sealed status nếu được phép; hash opaque không phải parse/evaluate. Đây là thiết kế guard phải có tests, không tuyên bố đã có air-gap kỹ thuật hoặc data access controls thực tế ở G1.

Tới G10, chỉ sau owner cho phép và model/preprocessing/hyperparameters/threshold/policy/cost/capacity/metrics/seeds/versions/protocol/artifact hashes khóa: load officialTest, validate source/schema, transform bằng fitted Train artifacts và score theo lệnh cố định. Schema/label/problem hoặc capacity violation trênTest phải báo nguyên trạng; không quay lại sửa preprocessing/τ/seed/model/scenario nhờ Test. Nếu phát hiện exposure trước đó, ghi rõ/report và chờ quyết định protocol; không đổi split để gọi Test pristine.

## 9. Cổng nghiệm thu và kiểm tra G1 thực sự

**READY FOR SCANIA G1 REVIEW: YES**: bốn tài liệu có formulation/cost matrix/hand examples, T1–T10 bốn nhóm, source contract/boundaries, proposed tests/stop gates, yêu cầu quyết định trước G2/G3/G4 và đề xuất quyền SC-G2-A. Không tự đánh dấu owner nghiệm thu hoặc P approved, không tự cập nhật TASK_BOARD.

Đã thực hiện ở G1: Git status/fetch/PR #12 merge verification, đọc tài liệu/Issue #2/P0-A và metadata/API docs; soạn/review Markdown. Kiểm tra links/fences/diff/scope và bảo toàn mọi file base được báo bằng kết quả thực trong PR/Issue #2. **Chưa** download/hash/audit raw, split, fit preprocessing/model, run baseline/Optuna/unit tests, environment check/install hoặc mởTest. Chưa có giá trị hash/schema thực, metrics/model hoặc số tests Scania PASS; ví dụ/test oracles đều ghi là tổng hợp/tính tay.

## Phụ lục phê duyệt owner và kích hoạt SC-G3-C — 2026-10-29

Nguồn: chỉ dẫn trong chat **“OWNER APPROVAL P04/P05 & TASK ASSIGNMENT – SC-G3-C”**, attachment `46930803-a9d5-4cf0-8c4d-68cabdbe89af`, SHA-256 `1c8081d1857ac5561071047fee51a636436ab49eb0b7e0f40a9ddaf34079d672`. Owner nghiệm thu G2 tại [Issue #2 comment6501313014](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6501313014); PR #14 merged tại `f2217c3ea7c56f579ed8b82ef23db703055e6489`, tích hợp HEAD G2 `e65361f5de840f2ee7ce9c211d54bf8958bad398`. Đã fetch/API xác minh.

| Gói | Trạng thái hiện hành và nội dung owner phê duyệt | Giới hạn |
|---|---|---|
| P04 | **APPROVED FOR SC-G3-C**. OfficialTrain60000 → Train48000/Validation12000; một `train_test_split` positions theo source order, test_size0.20, shuffleTrue, stratifyy, seed42; giữ returned order. Lưu IDs/membership local, ordered hashes/source/schema/config/version/commit; disjoint/coverage và tái lập100%. | Không thử seed để chọn; duplicate/conflict hoặc source mismatch → STOP/BLOCKED, không tự sửa split. Test không là input. |
| P05 | **APPROVED FOR SC-G3-C**. Giữ170X và rows có class hợp lệ; chỉ `na` missing. Median imputer keep_empty_features=True, add_indicator=False, copy=True, fitTrain-only. Train-all-missing giữ cột/fallback0 cho ô missing, Validation observed value giữ nguyên. LR StandardScaler sau impute fitTrain-only; tree/RF không scale bắt buộc. | Không drop/SMOTE/KNN/clipping/feature engineering/indicators; outputfinite/shape/order; clone fold-safe; không refitValidation/Test. |

Quyền task: namespace `src/scania/**`, `tests/scania/**`, `configs/scania/**`, `scripts/run_scania_*.py`, `results/scania_aps/g3/**`, tài liệu Scania cần thiết; processed/membership local dưới `data/processed/scania_aps/**`. Owner cho phép tải UCI421 trong worktree Codex, opaqueZIP và chỉ đọc/extractTrain+description; Test SEALED đếnG10. Python3.11 riêng worktree, khóa dependency thực tế trước split/fit. Không sửa file chung/AI4I/sản phẩm hoặc worktree Antigravity.

G301–G310 bắt buộc trước nghiệm thu; source/precision/schema/duplicate/preprocessing/leakage mismatch phải giữ failed evidence và dừng, không đổi policy/seed/version để vượt gate. Đây là quyền triển khai G3 (preprocessing fit được phép), **không** quyền predictive-model training, baseline, optimization, mởTest, G4 hoặc auto-merge. P02/P06/P07/P08/P09 và các quyết định khác không được thay đổi bằng phụ lục này.

Phạm vi này được chủ dự án cấp trực tiếp trong chat; không yêu cầu phê duyệt lại P04/P05 chỉ vì các bảng G1 cũ còn ghi đề xuất. Trạng thái **triển khai/nghiệm thu G3** phải căn cứ kết quả và owner acceptance riêng, không mặc định Done từ phê duyệt này.
