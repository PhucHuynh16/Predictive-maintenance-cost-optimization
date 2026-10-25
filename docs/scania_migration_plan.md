# P0 — Migration Impact Review: AI4I → Scania APS

Ngày: **2026-10-25 (Asia/Saigon)**. Trạng thái: **tài liệu P0 trình nghiệm thu**, chưa triển khai Scania. Chủ dự án đã phê duyệt chuyển dataset chính và các định hướng nêu ở §2; các lựa chọn kỹ thuật mang nhãn **ĐỀ XUẤT** chưa phải quyết định đã duyệt.

## 1. Quyền, nguồn chuẩn và mốc bảo tồn

Chỉ dẫn chat ngày 2026-10-25 “PHÊ DUYỆT CHUYỂN ĐỔI DATASET – NHIỆM VỤ P0” cho phép tạo tài liệu này và **chỉ bổ sung** phân tích vào [problem_formulation.md](problem_formulation.md). Các file chung, code, tests, dữ liệu và sản phẩm Antigravity chỉ đọc. Tạo branch/commit/push/PR, báo cáo Issue #2; không tự merge. Sau nghiệm thu P0 mới được giao riêng Scania G1/G2.

Đã fetch `origin/main`; [PR #11](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/11) có `merged=true`, merge SHA **`cea27fb004fd2761c12d6a055d420c8b8c95bddb`** (2026-10-23 16:33:12 UTC). Nhánh P0 `codex/p0-scania-migration-review` tạo trực tiếp từ mốc này. Đây là mốc Git bảo toàn G1–G4 AI4I, không cần di chuyển/đổi tên/xóa sản phẩm cũ để chuyển dataset chính.

Đã đọc AGENTS, PROJECT_SPEC, TASK_BOARD, ROADMAP, prompt Codex, Issue #2 và các tài liệu G1–G4: formulation/cost review, project proposal, dictionary/EDA, experimental protocol, G4 review/config/code/tests/logs. Kiểm kê theo **72 file tracked tại mốc main trên**, không kiểm kê bằng cách mở raw/processed; cây tracked ở mốc này chưa có tài liệu Scania. Khi hoàn tất bàn giao đã đọc thêm báo cáo P0-A của Antigravity tại Issue #2 (§3.1). Chưa tìm thấy bảng S1–S10 gốc độc lập. Bảng §2 là **chỉ mục đối chiếu P0 theo thứ tự 10 định hướng trong chỉ dẫn hiện tại**, không tái tạo nguyên văn hoặc khẳng định số mục của một kế hoạch bên ngoài chưa được cung cấp.

PROJECT_SPEC/ROADMAP/README/TASK_BOARD hiện còn nội dung AI4I và một số trạng thái trước G4; P0 ghi nhận khác biệt, không sửa ngầm. Phê duyệt chat mới xác lập hướng Scania, không làm cho runner AI4I hiện tại tự trở thành runner Scania. Trạng thái G4 trong board cũ không phủ nhận bằng chứng merge PR #11.

## 2. Đối chiếu S1–S10 và phạm vi đã phê duyệt

| Chỉ mục P0 | Định hướng đã được chủ dự án phê duyệt | Phần chưa được suy diễn là đã chốt |
|---|---|---|
| S1 | APS Failure at Scania Trucks là dataset chính | Phiên bản bytes/hash/schema local; hợp đồng parser |
| S2 | Bảo tồn AI4I và toàn bộ sản phẩm G1–G4 | Không chuyển số liệu/model/threshold sang nhãn Scania; không rename artifact cũ trong P0 |
| S3 | Objective Scania `10*FP + 500*FN` | Không thêm C_PM, η hoặc tổn thất TP; không coi là hóa đơn/hiệu quả can thiệp thật |
| S4 | Capacity tối đa 10% số quan sát | Floor là hệ quả số nguyên của mức10%; cần ghi batch/ties/comparator/no-feasible/tie-break và exceptions cho Scania (§7) |
| S5 | Official Test 16000 giữ tới G10 | Quy trình quản lý file/quyền mở tại G10; không EDA, fit, transform hoặc chọn bằng Test trong G1–G4 |
| S6 | Official Train 60000 → Train48000/Validation12000, stratified, seed42 | Parser/source-order/row IDs, API và versions; duplicate/dependence có thể kích hoạt dừng, không tự đổi split |
| S7 | Preprocessing và xử lý missing Train-only, chống leakage | Median/constant, indicators, all-missing columns/rows, schema và scaling cụ thể (§7) |
| S8 | B0, B1 Decision Stump, B2 Logistic Regression | Params, score/actions/threshold, weighting, calibration/refit và xử lý failed/infeasible |
| S9 | Random Forest là mô hình chính | H, fixed params, calibration, trials/seeds/runtime; không tự chuyển 30 trials/miền AI4I sang Scania |
| S10 | Tests, provenance và tái lập cho mọi kết quả | Manifest schema, version snapshot, commands/log paths và nghiệm thu từng cổng |

Không yêu cầu duyệt lại mười định hướng. G1 cần cụ thể hóa các khoảng trống kỹ thuật thành quyết định Scania; A1–A7/A3-a–g/A6-a–g cũ tiếp tục là nguồn lịch sử của AI4I, không bị xóa hoặc đổi nghĩa hồi tố.

## 3. Đối chiếu nguồn UCI — metadata, không phải audit CSV

Nguồn chính xem ngày 2026-10-25: [UCI dataset421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks), DOI [10.24432/C51S51](https://doi.org/10.24432/C51S51). Nguồn đối chiếu xuất xứ: [UCI IDA2016Challenge, dataset414](https://archive.ics.uci.edu/dataset/414/ida2016challenge), DOI [10.24432/C5V60Q](https://doi.org/10.24432/C5V60Q). Chọn **421** làm định danh chính đề xuất; không ghép hai bản/mirror hoặc giả định bytes giống nhau khi chưa hash. Chưa tải ZIP/CSV, đọc header hay đếm dữ liệu Scania local.

| Mục | Thông tin nguồn / điểm cần kiểm tra |
|---|---|
| Target | Lớp dương: lỗi component APS cụ thể; lớp âm: lỗi component ngoài APS. Không diễn giải neg là xe khỏe hoặc không có lỗi nào. Mapping dự kiến `pos→1, neg→0` cần xác nhận tokens khi audit. [UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) |
| Official partitions | Nguồn nêu Train60000 (59000 neg,1000 pos), Test16000; tên file `aps_failure_training_set.csv`, `aps_failure_test_set.csv`, kèm `aps_failure_description.txt`. Đây là metadata công bố, không phải số đo P0. [UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) |
| Feature schema | Trang tổng quan ghi171 features; mô tả ghi171 attributes với class rồi biến ẩn danh. **Dự kiến 170 predictors + class**, chưa xác minh; phải đếm header/roles thật, không dùng class làm feature. [UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) |
| Đặc trưng | Counters/histogram bins ẩn danh; không suy ra Tool wear, Type, UDI, timestamp, vehicle ID hoặc cơ chế vật lý AI4I. [UCI414](https://archive.ics.uci.edu/dataset/414/ida2016challenge) |
| Missing | Nguồn ghi có missing, ký hiệu `na`; tỷ lệ, cột/hàng all-missing và tokens khác **chưa audit**. [UCI414](https://archive.ics.uci.edu/dataset/414/ida2016challenge) |
| Benchmark | Cost_1=10 cho false positive (kiểm tra không cần thiết), Cost_2=500 cho false negative (bỏ sót APS). Không có khoản benchmark cho TP/TN; không có capacity10% trong công thức cost nguồn. [UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) |
| License/provenance | UCI hiện ghi CC BY4.0, nhưng phần mô tả nguồn có thông báo Scania GPLv3-or-later. Ghi cả hai, lưu notices/citation khi acquisition được giao; chưa kết luận pháp lý hoặc tự chọn license mã. P0/đề xuất không redistributes raw. [UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) |

Không dùng số liệu leaderboard hoặc nhãn/phân bố Test từ bài viết/mirror làm tiêu chí thiết kế. Test công khai không có nghĩa được phép khảo sát. P0 chỉ xem trang metadata/API docs, không mở official Test; điều này không chứng minh mọi người chưa từng xem Test hoặc rằng dữ liệu được thu thập theo một thiết kế prospective/time split.

Truy cập mô tả `.txt` riêng qua web gặp lỗi decode; metadata endpoint không truy cập được bằng công cụ web. Các kết luận bảng trên dựa vào phần mô tả hiển thị trên hai trang UCI, không tuyên bố đã đọc file mô tả local hoặc xác thực checksum do UCI công bố. Hash/bytes/version local đều **CHƯA XÁC MINH**.

### 3.1. Đối chiếu báo cáo P0-A của Antigravity tại Issue #2

Khi hoàn tất PR P0 đã đọc thêm [báo cáo P0-A](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6394297738), tự mô tả là review nguồn/read-only. Đây là đầu vào đối chiếu, không phải phê duyệt bổ sung từ chủ dự án; Codex không sửa báo cáo hoặc worktree Antigravity.

- Thống nhất về UCI421/target APS/cost10FP+500FN và giữ Test. Báo cáo không kèm CSV hash, audit script hoặc log kiểm đếm local; các phát biểu170 predictors, skip20 dòng comment và tỷ lệ missing>50%/>80% không được chuyển thành audit PASS của Codex. G2 phải xác minh header/preamble/tokens/counts theo bytes thực, không hard-code skip20 chỉ từ review.
- Đề xuất drop cột thiếu/zero-variance và kết luận model ngưỡng0.5 sẽ thất bại chưa là quyết định hoặc kết quả Scania đã chạy. Giữ T5/T6/T7 ở trạng thái đề xuất, không tự thêm feature selection/class weighting/tuning; mọi tỷ lệ/hiệu quả cần nguồn hoặc audit/run có provenance phù hợp.
- Kế hoạch EDA/association screening trên toàn official Train60000 trong P0-A cần tách khỏi Train48000 sau split: integrity/duplicate/count audit có thể cần60000, nhưng học preprocessing, chọn cột/threshold và khảo sát nhãn phục vụ chọn model chỉ dùng Train48000 (hoặc train folds tương ứng). Không dùng Validation12000 để fit/feature selection. Tỷ lệ48000/12000/seed42 đã được chủ dự án duyệt, không chờ chọn lại giữa holdout và K-fold.
- P0-A gợi ý bàn giao vào `docs/data_dictionary.md`/`docs/eda_findings.md` hiện là AI4I; đề nghị giao Antigravity path Scania riêng ở §8 để bảo tồn S2. Các diễn giải kinh tế chi tiết trong báo cáo không thay thế benchmark cost hoặc chứng minh hóa đơn/cứu hộ/horizon thật của từng hàng.

Các điểm này là đề xuất điều phối cho chủ dự án, không phải yêu cầu gửi việc hoặc tự kích hoạt/sửa sản phẩm AI kia. Cần đối chiếu trong nhiệm vụ G1/G2 riêng sau nghiệm thu P0.

## 4. Formulation Scania và thay đổi ngữ nghĩa

Đơn vị đề xuất: một quan sát trong nguồn APS có nhãn về component; không khẳng định mỗi hàng là một xe độc lập, một chu kỳ thời gian hoặc một sự cố duy nhất. `a=1` là quyết định dự đoán dương/đề xuất kiểm tra APS trong benchmark, không phải bằng chứng bảo trì đã xảy ra và tránh được lỗi.

```text
y_i = 1[class_i = pos]; a_i(h,τ) = 1[p_i(h) >= τ]
FP = Σ (1-y_i)*a_i; FN = Σ y_i*(1-a_i)
C_APS = 10*FP + 500*FN
K = floor(N/10); M = Σa_i; M <= K
```

Objective, 10/500 và mức capacity đã duyệt; comparator/miền τ/ties cùng floor và ngữ nghĩa action chi tiết được đề nghị ghi nhận cho Scania ở T2 (§7). Không thêm recall constraint. Với các tập đã chỉ định, suy ra capacity Train4800, Validation1200, Test1600 **nếu áp dụng floor trên toàn partition**; đây là số học từ kích thước đã duyệt, không phải số action thực nghiệm hoặc quyền đánh giá Train/Test.

Ma trận minh họa tính tay, **không phải kết quả Scania**:

| y | a | Cell | Cost benchmark |
|---:|---:|---|---:|
| 0 | 0 | TN | 0 |
| 0 | 1 | FP | 10 |
| 1 | 0 | FN | 500 |
| 1 | 1 | TP | 0 |

Khác AI4I: cost của TP trước đây là5 (C_PM1, C_F20, η0.8), giờ bằng0 theo benchmark. `10*M+500*P-510*TP` là biến đổi đại số của C_APS, không phải đặt C_PM=10,C_F=500,η=1 trong công thức AI4I (cách đó vẫn thu10 ở TP và là objective sai). B0 a=0 có C_B0=500P; saving tuyệt đối C_B0-C_APS có thể âm. Saving% null/ZERO_REFERENCE_COST khi C_B0=0 là đề xuất tiếp tục quy tắc robust, không tạo số mới.

`10FP+500FN` đo misclassification benchmark có chi phí bất đối xứng. Capacity10% là giả định nguồn lực của đồ án. Đây không phải tổng chi phí bảo trì doanh nghiệp, không ước lượng η/horizon hay tác động nhân quả. Nhãn Scania không cho phép gán những cơ chế failure/chi phí can thiệp của AI4I sang xe tải. Không so tổng cost AI4I1360 với Scania như cùng thang đo. Không so kết quả có capacity với leaderboard benchmark không capacity như một cải thiện có cùng giao thức.

Nếu dùng p như xác suất đúng, cost kỳ vọng một action là10(1-p), không action là500p; ngưỡng hòa vốn10/510 chỉ là suy diễn lý thuyết không capacity. **Không** mặc định đó là threshold B1/B2/P, hoặc giả định p đã calibrated. Threshold phải khóa theo quyết định/giao thức riêng trước Test.

## 5. Kiểm kê tác động — file và artifact

Phân loại: **G** giữ nguyên bản AI4I; **R** tái sử dụng có kiểm thử Scania; **C** cần chỉnh/adapter mới cho Scania; **N** phải viết mới. C/N nghĩa là tạo bản Scania riêng trong task sau, **không overwrite bản cũ trong P0**. Một file có thể G ở nhánh AI4I và R/C cho nhánh mới. Không có thay đổi code nào ở P0.

| File/nhóm hiện có | Loại | Tác động và đường chuyển đổi |
|---|---|---|
| `.gitignore`, `.gitattributes`, mọi `.gitkeep` | G/R | Không sửa P0. `data/*` đang ignore cả thư mục dataset mới, model/joblib bị ignore; kiểm chứng lại trước artifact thật, không thêm raw Git |
| `AGENTS.md`, `docs/WEEK1_CODEX.md`, `docs/WEEK1_ANTIGRAVITY.md`, `docs/BOOTSTRAP_HANDOFF.md` | G/C | Giữ lịch sử/phân quyền; task Scania phải cấp quyền cho các path mới chưa có trong bảng sở hữu |
| `docs/PROJECT_SPEC.md`, `docs/TASK_BOARD.md`, `README.md`, `data/README.md` | G/C | Cần cập nhật dataset/chứng cứ/cổng và chỉ dẫn entrypoint sau quyền chung riêng; P0 chỉ ghi yêu cầu, không sửa |
| `docs/ROADMAP.md` | G | Giữ tài liệu nguồn; dùng kế hoạch Scania riêng và liên kết có duyệt, không replace toàn roadmap |
| `requirements.txt` | G/R | Versions G3/G4 là bằng chứng AI4I, chưa lock Scania. Recheck Python3.11/API/imputer, RAM/runtime trong task sau; không cài/sửa P0 |
| `docs/problem_formulation.md` | G + C | Giữ nguyên toàn bộ183 dòng review AI4I; chỉ append phụ lục P0 Scania và link tài liệu này |
| `docs/cost_model_review.md`, `docs/experimental_protocol.md` | G/N | Không đổi công thức/quy tắc lịch sử; viết `docs/scania/cost_model_review.md`, `docs/scania/experimental_protocol.md` khi giao riêng |
| `docs/project_proposal.md`, `figures/pipeline.mmd` | G/N | Antigravity tạo proposal/pipeline Scania riêng, sửa nhãn APS/cost mới, không dùng sơ đồ sáu features cũ |
| `docs/data_dictionary.md`, `docs/eda_findings.md` | G/N | Antigravity tạo dictionary/audit Scania; schema ẩn danh/missing khác hoàn toàn, không sửa diễn giải AI4I |
| `notebooks/01_eda.ipynb` (12 code cells) | G/N | Không chạy lại/đổi output. Notebook Scania riêng, dev-only và provenance mới |
| `figures/eda/01_target_distribution.png`, `02_feature_distributions.png`, `03_feature_boxplots_by_failure.png`, `04_correlation_heatmap.png`, `05_physical_failure_mechanisms.png`, `06_temporal_sequence_hdf_cluster.png` | G/N | Giữ6 hình AI4I; Scania không có TWF/HDF/UDI/Tool wear để tái đặt tên đồ thị |
| `src/visualization.py` | G/R/C | Style có thể dùng; các hàm target/subfailures, vật lý/temporal phải thay bằng module Scania do Antigravity nhận quyền |
| `src/data.py` | G/R/C | Hash/canonical JSON tái sử dụng; raw schema, constants, split/order, duplicate/dependence cần adapter khác (§6) |
| `src/preprocessing.py` | G/C/N | Validator/OHE/6X/no-missing không phù hợp; builder Scania numeric/imputer mới, không nới validator AI4I |
| `src/cost_model.py` | G/R/N | Validators/savings có thể dùng; observed_cost chứa AI4I η nên giữ nguyên, viết cost APS riêng |
| `src/constraints.py` | G/R | Capacity/threshold/candidates/selection gần dataset-independent; kiểm chứng Scania/kích thước/ties mới, không tự coi đã nghiệm thu |
| `src/evaluation.py` | G/C | Confusion/metric/null logic R nhưng hàm đang gọi observed_cost AI4I và B0 cost cũ; cần evaluator Scania riêng/injection có tests |
| `src/baselines.py` | G/R/C/N | B0/R và fail wrapper; wear B1 không dùng lại; B2 phụ thuộc preprocessor AI4I. Stump/N; LR cấu hình cần xác nhận (§7) |
| `scripts/run_data_pipeline.py`, `configs/data_pipeline.yaml` | G/C/N | Hard-code UCI601/hash/10000/sáuX/2 bước split/ACF; entrypoint/config Scania mới; giữ toàn runner G3 |
| `scripts/run_baselines.py`, `configs/baselines.yaml` | G/C/N | Hard-code g3_submission/hash,6000/2000, raw path, feature/cost/baseline/schema/guard/tests; không sửa dataset name rồi chạy |
| `tests/test_data_pipeline.py` | G/R/C/N | Fixture14 cột/UDI/Type/ACF/60-20-20 cũ; cần tests parser/missing/official boundary/80-20/row IDs Scania |
| `tests/test_cost_model.py` | G/R/N | Giữ cost4cells0/1/20/5/η; thêm tests APS0/10/500/0, không đổi expected cũ để che regression |
| `tests/test_constraints.py` | G/R | Integer floor, exact ties, no-feasible/tie-break tái kiểm thử bằng fixture Scania/stump |
| `tests/test_baselines.py` | G/R/C/N | Reuse ý tưởng fit-spy/no-Test/failure gates; thay wear/schema/manifests, thêm stump class order/tie0.5/all-negative |
| `results/w2_g3/acquisition.json`, `unit_tests.json`, `unit_tests_recheck.json`, `runs/{g3_primary,g3_reproduce,g3_verified,g3_submission}/run.json` (7 file) | G | Giữ BLOCKED BOM cùng mọi COMPLETE/hash/43 tests; không viết đè hoặc ghi lại thành metadata Scania |
| `results/baseline_metrics.csv` | G | Bảng AI4I B0/B1/B2 cost1360/1022/1169 đã merge; Scania phải có CSV khác |
| `results/w2_g4/review.md`, `reproducibility_check.json`; `runs/{g4_primary,g4_reproduce}/{baseline_metrics.csv,run.json,tests.xml,tests_stdout.txt,tests_stderr.txt,unit_tests.json}` (14 file) | G | Giữ132 PASS và stable hash của AI4I, không phải kiểm thử Scania. Chỉ đọc metadata ở P0 |
| `data/raw/ai4i2020.csv`, `data/processed/w2_g3/**`, `.venv` (local/ignored) | G | Không mở/di chuyển/thay đổi trong P0; manifest/hashes tham chiếu đọc từ logs tracked, không tái hash raw |
| Code RF/calibration/optimization/demo; kết quả G5–G10 | N | Chưa có triển khai tracked tương ứng ở mốc P0; không báo như đã có để tái dùng |

Các file chưa có như `docs/reproducibility.md`, `docs/results_analysis.md`, notebook baseline/optimization, model_metrics.csv không phải sản phẩm hiện hữu đã được chuyển. Chỉ `.gitkeep` hiện có trong report/slides, không có báo cáo/slide Scania hoặc AI4I hoàn chỉnh để di trú.

## 6. Rà soát theo hàm và phụ thuộc

| Hàm/hằng số hiện có | Loại | Kiểm chứng/việc phải làm ở task Scania |
|---|---|---|
| `src.data.sha256_bytes`, `canonical_json`, `verify_hash`; `DataGateError` | R | Hash canonical/format và mismatch gate có thể dùng; dataset identity mới phải có hash thật khi acquisition |
| `RAW_SHA256`, `UCI_URL`, `FEATURES`, `NUMERIC_FEATURES`, `RAW_COLUMNS`, `TARGET`, `SUBLABELS`, `ACF_LAGS` | C/N | Đều gắn AI4I; schema Scania được đóng băng sau audit, không overwrite constants cũ |
| `acquire_raw`, `load_verified_raw`, `validate_raw` | C/N | Hàm hiện đọc ZIP ai4i2020/schema14/BOM/UDI/ProductID; parser Scania cần header/preamble/class/na/numeric mới, không áp luật vật lý AI4I |
| `select_features`, `validate_features` | C/N | Whitelist6X/Type/nonmissing hard-code. Validator Scania chấp nhận missing đã định nghĩa, reject unknown token/Inf/label/ID; danh sách numeric đúng schema audit |
| `duplicate_report`, `dependence_report` | C/N | Duplicate Scania dùng mọi predictor trước imputation, không target/row ID; phụ thuộc không thể đo bằng UDI/nhiệt AI4I, thiếu machine/time IDs là giới hạn |
| `create_splits`, `split_manifest` | C/N | Hai lần split và UDI phải thay bằng một lần split official Train80/20 + source-row IDs; Test ngoài hàm, không stratify/chia lại Test |
| `FeatureValidator`, `build_preprocessor`, `prepare_development` | C/N | G3 không impute; nhánh Scania mới chỉ fit Train và schema/missing contract, fold-safe cho tương lai |
| `EvaluationInputError`, `vector`, `scalar`, `paired`, `savings` | R | Binary/shape/finite/null conventions có thể dùng; không truyền X còn missing vào validator y/p; retest zero/overflow |
| `observed_cost` | N cho APS | Không dùng default C_PM/C_F/η hoặc giả lập APS bằng đổi params; API `observed_aps_cost` đề xuất mới |
| `capacity`, `threshold_actions`, `candidate_thresholds`, `select_candidate` | R | Fixed10%/floor/exact ties phù hợp định hướng; cần duyệt quy tắc Scania và tests score rời rạc/stump/h_order |
| `evaluate_policy` | C | Nhánh classification metrics gần chung nhưng cost/B0 reference đã hard-code, B1 Scania nay có score thật |
| `reactive_actions`, `BaselineFailure` | R | B0 action0, không probability model; retain failed/warnings behavior |
| `fixed_wear_actions` | N/thay ở APS | Không có wear cột hợp lệ; DecisionStump train-only mới, không dựng tên feature vật lý |
| `build_b2`, `fit_b2_development`, `LR_PARAMS` | C/R | Thay preprocessor; params/class_weight/calibration/threshold phải ghi quyết định riêng Scania; không refit/tune ngầm |
| Runner `git`, `array_digest`, `write_new`, `unit_test_gate` | R | Mẫu provenance/exclusive writes/tests-before-run dùng lại sau tests; run IDs, tests list và source hashes mới |
| Runner `validate_config`, `expected_config`, `development_access_guard`, `load_development`, `run` | C/N | Config equality và guard chỉ cho bốn file G3; whitelist Scania mới, không fallback AI4I/gộp Test, nguồn manifest riêng |
| `set_plot_style` | R, Antigravity | Kiểu hình có thể dùng; `plot_target_and_subfailures`, `plot_numerical_distributions`, `plot_boxplots_by_target`, `plot_correlation_matrix`, `plot_physical_mechanisms`, `plot_temporal_patterns` cần schema/title/API Scania riêng |

## 7. Chi tiết kỹ thuật cần khóa — đề xuất, chưa phê duyệt

Các T dưới đây không sửa S đã duyệt. Chốt theo cổng, không cần quyết định H/optimizer trước khi chỉ giao audit G2. Nếu bản S1–S10 gốc có chi tiết khác, chủ dự án đối chiếu bản gốc trước khi giao triển khai phụ thuộc; P0 không tự lấp bằng các quyết định AI4I.

| ID / cổng | Đề xuất cụ thể để nghiệm thu/giao việc | Phần phải được xác nhận hoặc dừng |
|---|---|---|
| T1 / G1–G2 | UCI421 là nguồn chính; giữ official Train/Test tách biệt; mapping pos1/neg0; source-row ID=(file hash, tên partition nguồn, số thứ tự dòng dữ liệu sau header). ID chỉ truy vết, không feature | Audit actual header/tokens/count; nếu không khớp metadata thì dừng trình lại, không đổi target bằng suy đoán |
| T2 / G1 trước cost/G4 | Xác nhận cho Scania comparator `>=`, τ∈[0,1], exact ties nguyên nhóm, N//10 toàn partition, no top-k; N0/input sai ERROR, P0 cost/capacity vẫn tính. T(p)={0,1}∪unique(p); no-feasible best=null; hòa cost≤1e-9 so minimum toàn bộ rồi M/τ/H order đăng ký trước, không arrival order | Mức10% đã duyệt, N//10 là hệ quả số nguyên; đề nghị khóa các lựa chọn ngữ nghĩa còn lại cho Scania, không mở domain τ>1/recall constraint/thay B0 |
| T3 / audit G2 → trước split G3 | Audit duplicate trên predictor raw canonical trước imputation, `na` là missing marker ổn định, không gồm class/rowID. Không tự drop/sửa nhãn. Có exact-X duplicate, nhãn mâu thuẫn hoặc liên hệ group/time mới thì dừng split, báo counts/hash nhóm và trình phương án giữ fixed protocol hay group-disjoint | Không tự hy sinh 48000/12000/stratify42 để xử lý duplicate. Không mở Test để tìm overlap; cross-official-boundary duplicate chưa xác minh đến G10 |
| T4 / G3 | Một `train_test_split` trên positions của official Train theo source order, `test_size=0.20`, stratify mapped class, shuffle=True, random_state42; giữ returned order; official Test không là argument. Schema/hashes/order/version trong manifest | Chỉ sau audit và review T3; không sort theo feature/label, thử seed khác hoặc lựa split có coverage tốt. 48000/12000 phải đạt đúng, không gộp16000 vào split |
| T5 / trước fit G3 | Numeric: chỉ token missing đã audit (`na`), median fit Train; đề xuất `SimpleImputer(strategy='median', keep_empty_features=True, add_indicator=False)`; all-missing Train giữ cột và fill0 theo contract đã test; không drop theo missing rate. Không indicators ở cấu hình cơ sở. LR: StandardScaler sau impute; stump/RF: impute, không scaling bắt buộc; float64 và ordered schema cố định | Median/fallback0/no-indicators là **đề xuất**, không có trong phê duyệt S7 chi tiết. All-missing rows giữ nếu class hợp lệ sau chủ dự án chấp nhận policy; không class/Inf/unknown token thì ERROR. Nếu muốn indicators/drop/KNN/SMOTE, cần quyết định trước nhìn Validation; không auto-tune preprocessing |
| T6 / trước G4 | B0 a0 không scores. B1 `DecisionTreeClassifier(max_depth=1, criterion='gini', splitter='best', min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0, max_features=None, max_leaf_nodes=None, min_impurity_decrease=0, class_weight=None, ccp_alpha=0, monotonic_cst=None, random_state=42)`; dùng p lớp1 và **p>=0.5**. Fit tree chỉ Train | Decision Stump đã duyệt; depth1 cụ thể hóa định nghĩa đó. Full params/threshold/weighting còn cần chốt. Không dùng `.predict` thay `>=` vì tie0.5 có thể khác; không tìm feature/threshold bằng Validation. Tree được phép không split, cho policy constant; capacity vi phạm giữ nguyên |
| T7 / trước G4 | B2 đề xuất LR L2/C1/lbfgs/tol1e-4/max_iter2000/intercept/seed42/class_weightNone, các params khác như snapshot A6-b AI4I; p lớp1>=0.5. Không CV/tune, sample_weight, post-calibration hoặc refit Train+Val; ConvergenceWarning/nonfinite => FAILED, không retry | Chọn rõ params đầy đủ theo version Scania. Không mặc định class_weight balanced hoặc ngưỡng cost10/510 chỉ vì imbalance/cost mới |
| T8 / G1 trước metrics/G4 | Dùng lại AP non-interpolated, ROC-AUC/Brier từ score thật; precision/recall/F1/null reasons, P0/one-class/saving0 theo quy tắc A6 đã kiểm thử; log TP/FP/FN/TN và10FP/500FN. B1 stump/B2 có score nên có thể báo AP/AUC/Brier; B0 null/NO_PROBABILITY_MODEL. Không loại baseline infeasible khỏi bảng gốc; tách feasible ranking | Xác nhận quy tắc cho Scania, không tiếp tục gán B1 Scania NO_PROBABILITY_MODEL chỉ vì B1 AI4I là rule. Không thay undefined bằng0 |
| T9 / trước G5–G7 | Chốt RF params/calibration, fold count/seed/clone-preprocessing, H/order, attempts/budget/seeds/runtime và phiên bản. Đề xuất giữ nguyên nguyên tắc fold-safe/no Train+Val refit trước Test | RF đã duyệt về họ model; chi tiết A5.6/30 trials AI4I không tự phê duyệt cho Scania. Không thực thi G5–G7 trong P0/G1–G4 |
| T10 / trước triển khai và G10 | Chốt namespace/quyền file ở §8–§9; freeze versions và schema sau audit; log cả FAILED/BLOCKED/infeasible; Test custodian có thể hash bytes khi acquisition được giao, không parse/EDA trước G10 | Chỉ G10 được load/transform/evaluate Test với quyền riêng sau khóa đủ thành phần. Metadata/source.Test public không đồng nghĩa quyền đọc; khác license notices phải ghi nguyên trạng, không redistribute raw khi chưa xử lý |

Tham khảo API để thiết kế T5/T6: [SimpleImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html), [DecisionTreeClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html), truy cập 2026-10-25. API hiện hành giải thích `keep_empty_features`/fallback0; cần fixture theo version khóa. `.predict` của tree xử lý hòa theo thứ tự class, nên T6 dùng comparator rõ để tránh đổi policy ở p=0.5. Không import/fit constructor nào trong P0 để tạo bằng chứng thực nghiệm.

## 8. Cấu trúc tách biệt đề xuất — chưa tạo thư mục/artifact

Không di chuyển các path AI4I đang có. Thêm nhánh path riêng cho Scania, `dataset_id`, `protocol_version`, `cost_model_id` bắt buộc trong mỗi config/manifest/CSV/figure; CLI dataset selection tường minh, không default/fallback sang dataset khác.

```text
data/raw/scania_aps/<source-hash>/                  # local, original bytes + notices
data/processed/scania_aps/<protocol>/<run-id>/     # local, Train/Val IDs, arrays, fitted pipeline
data/raw/scania_aps/<source-hash>/sealed_test/     # local, chưa parse; custodian/guard
src/scania/{data,preprocessing,cost_model,evaluation,baselines}.py
src/scania/visualization.py                       # Antigravity khi được cấp quyền riêng
scripts/run_scania_data_pipeline.py
scripts/run_scania_baselines.py
tests/scania/{test_data_pipeline,test_preprocessing,test_cost_model,test_constraints,test_baselines,test_evaluation}.py
configs/scania/{data_pipeline,baselines}.yaml      # quyền file chung cần cấp riêng
docs/scania/{problem_formulation,cost_model_review,experimental_protocol,reproducibility}.md
docs/scania/{project_proposal,data_dictionary,eda_findings,baseline_analysis}.md
notebooks/scania/{01_eda,02_baselines}.ipynb
figures/scania/{pipeline.mmd,eda/,baselines/}
results/scania_aps/{g2_audit/,g3/,g4/,baseline_metrics.csv}
```

Scania docs của Antigravity, module visualization mới, và mọi path chưa có phân quyền rõ cần được chỉ định chủ sở hữu trong task riêng; không suy ra Codex có quyền chỉ vì tên bắt đầu `src/`. Data custodian không dùng chung raw/worktree/.venv hai AI. Nếu hai AI tải cùng nguồn ở hai worktree, đối chiếu bytes/hash/notice riêng; không chép/ghi đè dữ liệu của AI kia. `src/constraints.py` và validators có thể import read-only hoặc tái dùng sau tests; nếu cần refactor chung thì đề xuất quyền riêng và bảo đảm hồi quy AI4I.

Official Test không đi vào dev manifest chi tiết/CSV cache. Public metadata chỉ nhận hash/size acquisition được phép và trạng thái sealed; không có row IDs, labels, coverage/missing histogram Test. Train/Val IDs chi tiết local; public manifest có hash theo thứ tự, dataset/config/code hashes, features/output names, preprocessing statistics digest, seed/versions/lệnh/runtime/status. Không public raw rows/prediction vectors hoặc fitted models lớn.

## 9. Trình tự nhiệm vụ — đề xuất, không tự kích hoạt AI

| Thứ tự / mã đề xuất | Người nhận | Nội dung, dependency và quyền cần giao |
|---|---|---|
| P0 hiện tại | Codex | Hai Markdown hiện tại, PR review; chủ dự án nghiệm thu trước mọi task Scania |
| SC-G1-C | Codex | Chốt target/decision/unit/objective/capacity/T1–T3/T8; đặc tả cost/API/tests và protocol boundaries; docs/scania tương ứng. Chủ dự án cấp riêng cập nhật spec/board/README/cross-links nếu muốn công bố active protocol mới |
| SC-G1-A | Antigravity | Sau formulation đủ duyệt: proposal và sơ đồ Scania riêng, diễn giải target APS/benchmark đúng; không chạy data/model từ diagram |
| SC-G2-A | Antigravity | Acquisition/audit official Train theo hợp đồng G1, source manifests/hashes/notices, schema/na/duplicates và dictionary; Test giữ sealed. Chỉ integrity cần thiết trên60000, không khảo sát Test; EDA có nhãn dùng Train48000 sau split G3, tách audit ban đầu với EDA phát triển |
| Audit gate | Chủ dự án | Nghiệm thu hash/schema/label mapping, xử lý T3/missing toàn cột/hàng và bất thường; cấp quyền G3/config. Có vấn đề cần đổi S thì dừng trình quyết định mới |
| SC-G3-C | Codex | Pipeline namespace mới; split80/20 Train nguồn, fixed seeds/order, imputer/scaler Train-only, no-Test guard, unit tests synthetic và provenance; nếu raw thiếu cần quyền acquisition tại worktree Codex, không đọc worktree Antigravity |
| SC-G2-A phần EDA | Antigravity | Chạy notebook/figures trên Train48000 theo membership đã khóa, không đụng raw/processed Codex; đề xuất thay đổi feature/preprocessing cần chủ dự án duyệt, không tự refit lại protocol |
| SC-G4-C | Codex | Sau G3/T2/T5–T8 và quyền code/config/log: cost APS/tests PASS trước baseline; B0/stump/LR, score Validation12000, reproducibility; không Test/optimizer |
| SC-G4-A | Antigravity | Chỉ sau logs Codex được nghiệm thu: đọc bảng, tạo notebook/figures/analysis Scania riêng; không sửa CSV/log gốc |
| G5 trở đi | Chủ dự án giao riêng | RF/calibration, G6 mở rộng, search/budget/sensitivity, report/demo và Test G10 qua cổng riêng; không bắt đầu từ việc merge P0 |

Không ấn định lại lịch5 tuần hoặc yêu cầu kích hoạt đồng thời hai AI. Trình tự này thể hiện các phụ thuộc: audit trước split; split trước EDA phát triển; tests trước baseline; nghiệm thu trước mở giai đoạn kế tiếp.

## 10. Tiêu chí nghiệm thu G1–G4 Scania đề xuất

| Gate | Bằng chứng tối thiểu để nghiệm thu | Không được coi là đã đạt ở P0 |
|---|---|---|
| G1 | Tài liệu có target pos/neg, đơn vị hàng/action, ma trận0/10/500/0, objective10FP+500FN, capacityfloor10%, tách benchmark/giả định; bảng quyết định accepted/pending, scope Test, namespace/owner và đặc tả tests; chủ dự án chốt các T phụ thuộc | Có approved direction không nghĩa full params/missing/calibration đã chốt |
| G2 | Acquisition Train UCI có URL cuối/DOI/time/hash/size/notices; audit header/schema/count/class/na/finite/duplicates/conflicting labels; không tự chữa dữ liệu; Test sealed + metadata không nhãn; dictionary và các stop findings có xử lý được duyệt. EDA sau split dùng đúng Train IDs | Không dùng metadata60000/171 để tuyên bố local audit PASS; chưa có checksum hoặc stats Scania P0 |
| G3 | Tests synthetic PASS; split đúng48000/12000 từ Train60000, disjoint/coverage/order/hashes/seed42 reproducible; official Test không là input. Imputer/scaler/selection chỉ fit Train, missing all-column/row/new-transform cases đúng policy, IDs/target không là X; không leakage, không overwrite AI4I; versions/config/code hashes/logs thật | Không copy manifest G3 AI4I hoặc gọi132 PASS AI4I là Scania PASS |
| G4 | Cost/constraints/metric/input/leakage tests PASS trước run thật; B0/B1stump/B2LR fixed config/threshold, fit Train-only, no Test; Validation cost components10FP và500FN, cost/N, saving, M/K/excess/rates/feasible, confusion, metrics/null reasons, runtimes/warnings/status; baseline infeasible giữ nguyên và tách ranking; source commit/config/versions/seed/split/raw hashes/commands/reproduction đầy đủ | Không dùng số AI4I, ví dụ tính tay hoặc leaderboard như kết quả; chưa kết luận P tốt hơn baseline, chưa hoàn thành G6/G7 |

### Test matrix cần triển khai sau phê duyệt

| Nhóm | Ca bắt buộc / expected |
|---|---|
| APS cost | TN0/FP10/FN500/TP0; fixture y=[0,1,1,0],a=[1,0,1,0] cho510; cost khớp10FP+500FN và10M+500P-510TP; B0=500P, savings âm/dương/zero reference; reject input/overflow |
| Constraints | N0 ERROR; floor biên9/10/11999/12000, K1200; P0 không đổi capacity; ties p0/1/0.5, constant stump scores, exact candidates/no rounding; all-infeasible báo bestnull, không B0 substitution; tie-break độc lập arrival |
| Parser/schema | BOM/preamble/header tìm đúng, duplicate/missing/extra columns, class pos/neg/unknown, source-row IDs/order, na/token lạ/nonfinite/numeric types; không suy luận cột vật lý hoặc ép dấu theo AI4I |
| Duplicate/split | Exact-X có missing bằng canonical key trước impute; nhãn mâu thuẫn giữ nguyên và BLOCKED; 60000→48000/12000 đúng một split/seed42; hash/IDs lặp lại, giữ source order đầu vào; không đọc Test/không retry split |
| Missing/leakage | Sentinel median/scaler/category/column statistics chứng minh fit Train-only; cột Train all-missing và missing chỉ ở Validation; all-missing row đúng policy; output stable schema/finite; fold clones không mang fitted statistics cả Train vào calibration folds sau này |
| Baselines/metrics | B0 no fake p; stump depth≤1 (root-only hợp lệ), class1 index/tie0.5 đúng comparator; LR full params/convergence FAILED/no retry; B1/B2 probability metrics dùng score thật, not actions; P0/P=N/M0/F1zero/null reasons và infeasible giữ nguyên |
| Orchestration/provenance | Tests/hash/config mismatch chặn trước run; no-Test sentinel/spy file opens; no Train+Val refit; read-only AI4I paths, exclusive new run IDs, FAILED/BLOCKED logs retained; stable result digest tách runtime/timestamp; reproduce không chọn seed/run tốt nhất |

## 11. Rủi ro và điều kiện dừng

| Rủi ro/tín hiệu | Dừng ở đâu / xử lý |
|---|---|
| Sai nguồn/mirror/hash/count/header/labels; missing token không rõ | Dừng acquisition/parser trước split/fit; giữ bytes, log discrepancy, xin xác nhận; không sửa schema/target hoặc tải bản “dễ hơn” |
| Exact-X duplicates/conflicting labels, cấu trúc nhóm/thời gian có bằng chứng | Dừng split; báo counts/nhóm, trình ảnh hưởng fixed stratified split và phương án riêng; không tự drop/dedup/impute rồi gọi hết duplicate |
| Cột/hàng all-missing hoặc thiếu quá cao chưa có policy; imputer đổi số cột | Dừng fit khi contract chưa đủ; chốt T5 và tests schema/fallback. Không chọn cutoff bằng Validation/Test hoặc silently drop |
| Class quá ít cho calibration folds sau này, LR không hội tụ, p không hợp lệ | Log FAILED/BLOCKED đúng giai đoạn; không tự đổi folds/method/C/solver/weight/threshold hoặc thêm oversampling |
| Capacity vượt/không candidate feasible | Đây là policy infeasible, vẫn báo cost/metrics/excess, không “sửa” top-k hoặc tuning baseline; NO_FEASIBLE_CANDIDATE đúng scope, không kết luận cảH vô nghiệm |
| Vô tình parse/EDA Test hoặc làm lộ nội dung nhãn | Dừng development phụ thuộc; ghi phạm vi exposure trung thực, báo chủ dự án xử lý protocol. Không chia lại/đổi tên để tuyên bố Test pristine |
| Thiếu machine/time IDs; chọn mẫu dịch vụ, nhãn neg không phải healthy | Hạn chế suy luận; không gọi dự báo horizon/prospective/causal hoặc tổng quát hóa xe mới nếu không có bằng chứng. Không tự invent group/time IDs |
| Thay log/overwrite artifact AI4I hoặc data worktree kia | Dừng mutation, trình path/ảnh hưởng và cách xử lý bảo toàn; namespace/type checks trước run, không tự di chuyển/xóa |
| Không đủ RAM/runtime/versions; metadata license khác nhau | Ghi điều kiện cụ thể; xin budget/version/scope phù hợp, không sample lại để chạy đẹp hoặc public raw/đổi license mã tùy ý |

## 12. Kiểm tra P0 đã làm và chưa làm

Đã làm: Git status/remote/fetch/PR11 merge; đọc tài liệu và Issue2; `git ls-files`, `rg` dependency inventory và parse AST **chỉ source tracked**, xác nhận72 file/12 code cells notebook; đọc metadata web UCI và API docs; đối chiếu logic/công thức bằng phân tích tài liệu. Đây không phải unit tests hoặc audit dữ liệu Scania. Kiểm tra phạm vi diff, bảo toàn prefix AI4I, Markdown links/fences và whitespace được báo theo kết quả thực khi bàn giao PR.

Chưa làm: tải ZIP/CSV, hash/parse raw hoặc processed Scania/AI4I, audit nhãn/missing/duplicates mới, split, fit preprocessing, import/fit model, baseline, calibration, optimization, sensitivity, Test evaluation; không chạy lại132 tests AI4I hoặc kiểm tra/cài dependency. Con số43/132 PASS và cost1360/1022/1169 là **bằng chứng lịch sử G3/G4 AI4I đã merge**, không có số đo hay kết quả Scania.

**READY FOR SCANIA G1/G2: YES — về mức sẵn sàng trình giao nhiệm vụ sau nghiệm thu P0.** Nguồn/định hướng/phạm vi và kế hoạch audit đã xác định; G1 để chốt kỹ thuật, G2 để xác minh bytes/schema/missing. **Chưa có quyền bắt đầu G1/G2**, chưa xác nhận dữ liệu sẵn sàng, và **G3/G4: NO** đến khi các T/audit/quyền tương ứng đủ. Chủ dự án cần nghiệm thu P0 và giao task/file rights riêng; không cần giả định mọi chi tiết còn thiếu phải chốt trước khi chỉ thực hiện audit G2.

Bàn giao P0 chỉ gồm tài liệu này và phụ lục append của problem_formulation; commit SHA/PR và báo cáo Issue2 dùng giá trị thực khi tạo, không tự điền mốc giả vào kế hoạch. Không tự cập nhật file chung hoặc triển khai nhiệm vụ kế tiếp.
