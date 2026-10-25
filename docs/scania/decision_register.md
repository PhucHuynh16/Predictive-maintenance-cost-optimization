# SC-G1-C — Decision register Scania APS

Ngày: **2026-10-25 (Asia/Saigon)**. **Dự thảo trình nghiệm thu G1**. Nguồn trạng thái quyết định của bốn tài liệu Scania là register này; nội dung đề xuất ở các tài liệu khác không tự trở thành phê duyệt.

## 1. Bằng chứng, phạm vi và quy tắc đọc

Chủ dự án gửi trong chat “NHIỆM VỤ SC-G1-C – PROBLEM FORMULATION SCANIA APS”, nghiệm thu P0, xác nhận [PR #12](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/12) merge tại **`c52d89ef7d9d0ee8f5e35f12c2f0f63777835d4b`**. Fetch/API đã xác minh `merged=true`, main ở đúng mốc này. Branch `codex/sc-g1-formulation-protocol` tạo trực tiếp từ origin/main.

Quyền hiện tại chỉ bốn file mới: `docs/scania/problem_formulation.md`, `experimental_protocol.md`, `cost_model_review.md`, `decision_register.md`. Không tải/audit/split/fit/train/baseline/Optuna/Test; không sửa tài liệu chung, code/config/tests/results, AI4I hoặc sản phẩm/worktree Antigravity. Commit/push/PR và báo cáo Issue #2 được phép; không tự merge, giao việc hoặc kích hoạt AI khác.

Đã đọc AGENTS, PROJECT_SPEC, TASK_BOARD, ROADMAP/prompt, [P0 migration plan](../scania_migration_plan.md), [formulation AI4I và phụ lục P0](../problem_formulation.md), Issue #2 và [P0-A Antigravity](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6394297738). P0 được nghiệm thu **không đồng nghĩa các đề xuất T1–T10 đã duyệt**; chỉ dẫn G1 nhắc lại yêu cầu giữ chúng ở trạng thái chờ. Các câu P0 “chưa giao G1” là lịch sử, các thông số AI4I không chuyển tự động sang Scania. Không sửa nguồn lịch sử để cập nhật trạng thái.

Ký hiệu theo đúng bốn nhóm chủ dự án yêu cầu:

| Nhóm | Nghĩa | Cách sử dụng |
|---|---|---|
| **D — ĐÃ DUYỆT** | Quyết định được chủ dự án nêu trong phê duyệt migration/S1–S10 hoặc nhiệm vụ G1 | Ghi nội dung và nguồn; hệ quả số học không phải quyết định mới |
| **P — CHỜ DUYỆT** | Đề xuất kỹ thuật cụ thể của Codex | Chưa dùng để code/run; chủ dự án cần chọn/điều chỉnh trước cổng tương ứng |
| **A — CHỜ AUDIT** | Sự kiện chỉ file/audit thật mới xác minh được | Không phê duyệt thay cho bằng chứng; bất thường có thể buộc trình quyết định mới |
| **L — GIAI ĐOẠN SAU** | Quyết định chi tiết chưa cần cho audit G2 hoặc G3/G4 | Trước giai đoạn dùng nó phải chốt; không phải quyền triển khai |

S1–S10 ở P0 là chỉ mục theo thứ tự mười định hướng trong chỉ dẫn migration, không có bảng đánh số gốc độc lập được cung cấp. Register giữ cách quy chiếu đó, thêm các khẳng định cụ thể mà chủ dự án nêu rõ trong nhiệm vụ G1. Không coi UCI/API docs hoặc P0-A là văn bản phê duyệt của chủ dự án.

## 2. Quyết định hiện có — không yêu cầu duyệt lại

| ID | Nội dung D | Căn cứ |
|---|---|---|
| D01 | Scania APS, **UCI 421**, dataset chính; AI4I cùng sản phẩm/kết quả G1–G4 bảo tồn | Migration S1/S2; G1 §I–II |
| D02 | `pos=1`, `neg=0`; neg không đồng nghĩa xe hoàn toàn khỏe | G1 §II; P0 T1 nay rõ về mapping |
| D03 | `a=1` là dự đoán dương/đề xuất kiểm tra APS | G1 §II; không chứng minh tác động bảo trì |
| D04 | `C_APS=10*FP+500*FN`; đơn vị cost units benchmark; không quy thành tiết kiệm tiền thật/hiệu quả can thiệp | Migration S3; G1 §II |
| D05 | Capacity tối đa 10% số quan sát | S4/G1 §II; vì M nguyên nên `M<=floor(N/10)` là hệ quả toán học, không mở lại mức 10% |
| D06 | Official Train 60.000 → Train 48.000/Validation 12.000, stratified, **split seed 42** | S6/G1 §II; source order/API/membership/hash còn P/A |
| D07 | Official Test 16.000 khóa tới G10; chưa được mở trong G1–G4 | S5/G1 §II, VI; quyền đánh giá cuối vẫn giao riêng |
| D08 | Preprocessing/missing chống leakage, fit Train-only | S7; cách impute/scaling/drop/indicators cụ thể chưa duyệt |
| D09 | B0 Reactive, B1 Decision Stump, B2 Logistic Regression | S8/G1 §II; depth tối đa1 cụ thể hóa định nghĩa stump, full params và score-to-action còn P |
| D10 | RF là mô hình chính giai đoạn sau; tests/provenance/tái lập bắt buộc | S9/S10/G1 §II, IV; RF/H/calibration/search budget cụ thể còn L |

## 3. Đối chiếu toàn bộ T1–T10 theo bốn nhóm

Một T có nhiều thành phần; không gắn một nhãn “đã duyệt” cho cả hàng chỉ vì một phần của nó thuộc D.

| T nguồn P0 | (1) D trong S/G1 | (2) P cụ thể chờ chủ dự án | (3) A sau audit | (4) L và cổng muộn nhất |
|---|---|---|---|---|
| **T1 Nguồn/nhãn/schema/ID** | UCI 421, pos1/neg0, ngữ nghĩa neg/action (D01–03) | P01: parser/header/missing token và source-row ID `(train_file_sha256, official_partition, data_row_number)`; không feature ID | Hash/bytes/header/count/predictors/tokens thực;170 predictors là dự kiến, chưa audit | Khi mở Test G10 mới kiểm schema nguồn Test; không kiểm nhãn/feature Test để phát triển |
| **T2 Threshold/ties/capacity/no-feasible/tie-break** |10% và action dương (D03/05); floor là hệ quả số nguyên | P02: `>=`, τ∈[0,1], exact ties, T(p), no-top-k, batch toàn partition; ERROR/P=0; NO_FEASIBLE_CANDIDATE; hòa1e-9/M/τ/H order | Xác suất/mức ties/feasibility chỉ được biết khi task model được giao; không có kết quả ở G1 | Thứ tự H cụ thể trước search G7; cơ chế P02 chốt trước tests/cost/baseline G4 |
| **T3 Duplicate/label conflict/stop** | Không có policy dedup/group-split cụ thể nào được duyệt; D06 vẫn giữ | P03: audit exact-X trước impute, exclude class/ID; giữ raw/nhãn/hàng, có duplicate/conflict/group mới thì dừng split, không tự repair | Số nhóm/hàng và conflicting labels, missing masks, group/time metadata nếu có | Không đọc Test để tìm overlap trước G10; xử lý bất thường cần chủ dự án trước split G3 |
| **T4 Split/provenance** | Official boundary,48000/12000,stratify42,provenance (D06/07/10) | P04: một train_test_split positions, test_size0.20, shuffle=True, source order, giữ returned order; manifest/version/ID hashing | Đủ rows/classes, audit T3 đạt; membership/ordered hashes chưa tồn tại | Freeze membership trước development fits; Test không là đầu vào splitter |
| **T5 Missing/preprocessing** | Train-only chống leakage (D08) | P05: median, keep_empty_features, fallback0/all-missing column, no indicators/drop; all-missing rows giữ nếu class hợp lệ; LR scaler sau impute, tree/RF không scale | Missing tokens/rates/cột/hàng trống/constant/numeric ranges; output dimension và precision cần tests | Thay strategy/feature selection/resampling phải duyệt riêng; fold-safe khi calibration về sau; P05 chốt trước fit G3 |
| **T6 Decision Stump** | Họ B1 stump/depth≤1 (D09) | P06: full params, model seed 42, class1 score, comparator p>=0.5, không weighting/calibration/tuning/refit | Root-only/ties/capacity/scores là kết quả model về sau; không biết ở G1 | Chốt trước G4; không đổi threshold sau thấy infeasible |
| **T7 Logistic Regression** | Họ LR (D09), preprocessing Train-only | P07: full LR config, model seed 42, p>=0.5, no class/sample weighting/CV/calibration/refit; warning/nonfinite=>FAILED/no retry | Hội tụ/scores/memory/runtime khi task thật; không được dự báo “sẽ thất bại” từ metadata | Chốt trước G4; mọi retry thay config cần quyết định mới |
| **T8 Metrics/undefined** | Benchmark cost/unit và tests/provenance (D04/10) | P08: confusion/rates/saving%, AP estimator/ROC-AUC/Brier, JSON null+reason; B1/B2 dùng score thật, B0 không fake p; infeasible tách ranking | P/M/class support từng partition thực; không có số liệu Scania G1 | Chốt trước evaluation/tests G4; CI/multi-seed/metric mở rộng trước G8 riêng |
| **T9 RF/calibration/optimization** | RF là họ model chính (D10), chống leakage vẫn bắt buộc | Chưa chọn full params/H/folds/algorithm/budget trong G1; P09 chỉ là danh sách cần khóa | Group/dependence/class support có thể ảnh hưởng calibration/folds và khả năng chạy | **L**: RF/calibration trước G5; H/order/search/trials/seeds/runtime trước G7; sensitivity/multi-seed trước G8; không tự dùng 30 trials/5-fold AI4I |
| **T10 Phân quyền/môi trường/Test** | Bảo tồn AI4I, Test G10, provenance; quyền hiện tại chỉ 4 Markdown | P10: namespace/owner, acquisition route/custodian, development guard, environment snapshot và freeze | Hash/notices/preamble thật, tài nguyên/môi trường tương thích chưa kiểm; không coi versions AI4I là chứng minh Scania | Quyền SC-G2-A cần cấp trước download/audit; quyền source/config G3/G4 riêng; release/đánh giá Test khóa đủ thành phần và quyền G10 |

## 4. Các gói lựa chọn cụ thể — tất cả P, chưa tự phê duyệt

| Gói | Khuyến nghị của Codex và tham chiếu chi tiết | Cổng |
|---|---|---|
| P01 | UCI 421 official Train nguyên bytes, phát hiện header class thay vì hard-code skip20; `na`→missing theo audit, labels chỉ pos/neg; source-row IDs theo file hash + thứ tự dòng dữ liệu sau header; schema whitelist sau audit | Chủ dự án chốt hợp đồng acquisition/audit trước G2; schema cuối là A |
| P02 | Cơ chế threshold/capacity/ties/ERROR/no-feasible/tie-break trong [formulation §4–5](problem_formulation.md); không có recall constraint hay top-k | Trước code/tests G3/G4 có dùng policy |
| P03 | Exact-X duplicate (missing mask + parsed numeric exact, không rounding) trước impute; cùngX khácclass là conflict. Có nhóm thì BLOCKED trước split, chỉ báo cáo/đề xuất owner; không drop/group-split tự động | Chốt cách audit/stop trước G2, giải quyết findings trước G3 |
| P04 | Split80/20 một lần theo [protocol §3](experimental_protocol.md); versions/source order/encoding hashes khóa, không retry seed | Trước split G3 |
| P05 | `SimpleImputer(strategy='median', keep_empty_features=True, add_indicator=False, copy=True)`; cột hoàn toàn thiếu ở Train fill0/giữ cột, không indicators hoặc lọc cột theo missing/variance; hàng X toàn thiếu có class hợp lệ giữ và impute. LR StandardScaler default mean/std sau impute; stump/RF giữ numeric đã impute; không OHE vì schema dự kiến numeric | Trước fit G3; audit bất thường cần xử lý trước, không tự áp phương án này khi chưa duyệt |
| P06 | Stump: criterion=gini, splitter=best, max_depth=1, min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features=None, max_leaf_nodes=None, min_impurity_decrease=0.0, class_weight=None, ccp_alpha=0.0, monotonic_cst=None, random_state=42. p lớp1>=0.5; root-only hợp lệ; không tuning, weights, post-calibration hoặc Train+Val refit | Trước G4 |
| P07 | LR L2: C=1.0,l1_ratio=0.0,solver=lbfgs,dual=False,fit_intercept=True,tol=1e-4,max_iter=2000,class_weight=None,random_state=42,warm_start=False,verbose=0. Không truyền penalty deprecated trong API 1.9.1; n_jobs=None/intercept_scaling=1 là default không tác dụng với lbfgs. p lớp1>=0.5; no sample_weight/CV/tuning/post-calibration/Train+Val refit; ConvergenceWarning hoặc p không hợp lệ=>FAILED, giữ log và xin quyết định, không tự retry | Trước G4; API version Scania cần freeze, không tự port params khi version khác |
| P08 | Metrics/null reasons/saving và logging như [cost review §3–4](cost_model_review.md); runtime định nghĩa rõ; AP không nội suy. B1 Scania có score mô hình thật, khác rule B1 AI4I | Trước G4 |
| P09 | RF family đã D, chưa có full config/search/calibration được chọn; [protocol §8](experimental_protocol.md) liệt kê quyết định cần khóa theo giai đoạn | L trước G5/G7/G8 |
| P10 | Bốn tài liệu G1 không cấp quyền cho path mới khác. Đề xuất quyền/task Antigravity, namespace và Test custody ở [protocol §2,7](experimental_protocol.md); snapshot Python 3.11/deps riêng, freeze trước split/fit; no overwrite log/AI4I | Phần acquisition/owner trước G2; environment/code/config trước G3/G4; quyền Test riêng G10 |

Model seed 42 trong P06/P07 là **đề xuất**, khác split seed 42 đã D. `max_depth=1` triển khai họ stump đã D; criterion/weights/threshold/model seed không mặc nhiên đã D. Comparator p>=0.5 phải được chọn rõ vì tree `.predict` có thể xử lý tie 0.5 khác. Tham khảo [tree API](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html), [LR API](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [imputer API](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html), xem 2026-10-25; không import/fit kiểm thử trong G1.

## 5. Quyết định trước từng lần kích hoạt

| Cổng | Chủ dự án cần phê duyệt/giao rõ | Chưa cần hoặc không thể chốt thay bằng chứng |
|---|---|---|
| **Trước SC-G2-A** | Nghiệm thu G1; task/data rights/paths/owner theo protocol §7; P01 source/parser/rowID/audit, P03 duplicate/stop; phạm vi chỉ integrity60000 và Test custody P10; route Train-only hoặc cho phép lưu ZIP opaque chứa Test; giữ raw/no-drop/no-label repair/no model EDA trước split | Không cần chọn stump/LR/RF/H/optimizer hoặc median trước khi chỉ audit. Hash/schema/rates là A, G2 phải báo thực tế |
| **Trước SC-G3-C** | G2 audit được nghiệm thu, findings được giải quyết; P04 split encoding/version, P05 toàn bộ missing/schema, quyền code/config/artifact local/log và tests; nếu duplicate cần đổi protocol thì quyết định mới trước split | Không thay tỷ lệ/seed hoặc feature schema chỉ nhờ phê duyệt chung G1; RF/H chưa cần |
| **Trước SC-G4-C** | G3 nghiệm thu; P02/P06/P07/P08 đủ cụ thể, config/tests/log rights; cost/constraints/metrics tests PASS trước baseline thật | G1 review/merge không phải quyền train; baseline không tune threshold; Test vẫn khóa |
| **Trước G5/G7/G8** | P09 và quyền riêng đúng giai đoạn; calibration fold-safe, H/order/trials/seeds/runtime, sensitivity thiết kế đủ | Không áp lại miền/budget/calibration AI4I bằng suy diễn |
| **Trước G10** | Khóa model/preprocessing/hyperparameters/threshold/cost/constraints/metrics/seeds/versions/protocol/artifact hashes; quyền Test riêng và lệnh chấm cố định | Không tuning sau thấy Test; không “reset” exposure bằng chia lại |

Chủ dự án có thể duyệt bằng `P<ID hoặc T-thành phần>; lựa chọn/giá trị; phạm vi task/file; ngày; commit tài liệu`, kèm findings cần xử lý. Mẫu này chưa phải bản ghi đồng ý. Không cần duyệt lại D01–D10.

## 6. Trạng thái bàn giao và giới hạn

**READY FOR SCANIA G1 REVIEW: YES** về độ đầy đủ bộ tài liệu thiết kế: đã phủ T1–T10, formulation/data contract/tests/stop gates và gói giao SC-G2-A. Chưa được chủ dự án nghiệm thu G1; **SC-G2-A/G3/G4 chưa được kích hoạt**. Không có dữ liệu/CSV hash/split/model/metrics Scania được tạo trong G1. Các lựa chọn P giữ nguyên CHỜ DUYỆT dù PR tài liệu được merge.

Kiểm tra document diff/links/fences/phạm vi và bảo toàn mọi file base sẽ được báo theo kết quả thực ở PR/Issue #2. Không chạy unit tests, kiểm tra/cài dependencies, tải/raw audit/split hoặc thực nghiệm. Mốc43/132 tests và các cost AI4I trong tài liệu nguồn chỉ là lịch sử, không là chứng cứ Scania.
