# A5 — protocol đã phê duyệt, giới hạn và điều kiện dừng

Ngày cập nhật: **2026-10-23 (Asia/Saigon)**. A5.1–A5.7 đã được chủ dự án phê duyệt và tích hợp qua [PR #7](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/7). **W2-G3-C đã được kích hoạt riêng** bằng văn bản “NHIỆM VỤ CHÍNH THỨC W2-G3-C — GIAI ĐOẠN 3: DATA PIPELINE & EXPERIMENTAL PROTOCOL”. Đây là nhiệm vụ G3, không cho phép G4/G5, cost model, tối ưu hoặc đánh giá Test. Các trạng thái “chưa giao/chưa chạy” trong phần ghi nhận A5 bên dưới là snapshot trước G3; chỉ dẫn và tình trạng G3 hiện hành ở §9.

## 0. Bằng chứng phê duyệt và phạm vi nhiệm vụ

Phần §0–§8 giữ nguồn quyết định, phân tích và cổng phê duyệt A5 từ PR #7. Quyền ghi nhận A5 ở dưới đã hoàn thành; quyền triển khai G3 hiện tại được nêu riêng tại §9, không thay đổi A5 hoặc tự cấp quyền các giai đoạn sau.

Nguồn chỉ dẫn: `Văn bản đã dán.txt`, attachment `28ca3964-7860-4589-8d6c-ad9b1f10f831`, SHA-256 `5e9e9602543d1599477077b2e909f864d09791914b0665abef427b59d1f9c51b`, được chủ dự án gửi trong chat ngày 2026-10-23. Phạm vi được sửa chỉ `docs/PROJECT_SPEC.md`, `docs/experimental_protocol.md`, `docs/TASK_BOARD.md`; cho phép branch/commit/push/PR riêng và báo cáo Issue #2, không tự merge hoặc sửa quyết định A1–A4/A6/sản phẩm Antigravity.

Chỉ dẫn xác định: **“Đây là lệnh phê duyệt và ghi nhận A5, chưa phải lệnh triển khai W2-G3-C.”** Sau khi PR ghi nhận được merge, chủ dự án sẽ giao riêng G3 và quyền config/metadata. Các khuyến nghị review cũ chỉ trở thành quy tắc ở phần A5 tương ứng được chủ dự án chấp nhận; **đề xuất B2 không post-calibration chưa được duyệt**, B2 chờ A6 trước G4. Phê duyệt chính sách không phải kết quả audit, bằng chứng tái lập pipeline hoặc quyền đánh giá Test.

## 1. Căn cứ và mức độ kiểm chứng

- Base `origin/main` cho lượt ghi nhận A5: `8529fe4a428d221badee86aeb6e03170b274cc6f`, đã merge PR #6; review W1 trước đó đối chiếu main `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f` sau PR #1/#3/#4/#5. Đã đọc/đối chiếu AGENTS, ROADMAP, PROJECT_SPEC, TASK_BOARD, prompt Codex và [Issue #2](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2).
- Đối chiếu tĩnh [EDA findings](eda_findings.md), [dictionary](data_dictionary.md), source/output [notebook](../notebooks/01_eda.ipynb), [proposal](project_proposal.md) và [pipeline](../figures/pipeline.mmd) đã merge. Không chạy lại notebook, không tải/đọc raw ở worktree Antigravity. Codex hiện không có raw trong worktree của mình.
- Các số EDA dưới đây là kết quả Antigravity đã báo cáo, không phải phép đo mới của Codex. Chưa đo autocorrelation theo lag, độ dài phụ thuộc hoặc effective sample size; không đưa ra hệ số hay p-value chưa tính.
- A5 hiện hành ở [PROJECT_SPEC §2/§9/§10](PROJECT_SPEC.md): sáu features/target giữ nguyên; A5.1–A5.7 đã phê duyệt theo §0. Audit duplicate sáu X và rà soát phụ thuộc phải hoàn thành trước split khi G3 được giao; không tự xác nhận các kiểm tra này đã đạt từ việc phê duyệt văn bản.

## 2. Phụ thuộc theo UDI và nhiệt độ

Nguồn [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) mô tả hai biến nhiệt độ dùng random walk; nhiệt độ quá trình còn cộng nhiệt độ môi trường. EDA ghi nhận 108/115 HDF ở UDI 4000–4999, 7 ca còn lại ở 3000–3999, cùng biến thiên nhiệt theo thứ tự. Đây là bằng chứng định tính rõ rằng không nên giả định các hàng độc lập, phân phối đồng nhất theo mọi đoạn UDI.

Mức độ định lượng còn chưa biết: tương quan Air–Process `r=0.876` trong dictionary là tương quan giữa hai feature, không phải tự tương quan giữa các hàng. Cụm HDF thể hiện phân bố lỗi thay đổi theo đoạn; không tự chứng minh quan hệ nhân quả hay sự phụ thuộc còn lại sau khi điều kiện hóa đủ features. Chưa đủ bằng chứng để ấn định một gap/block width hay kết luận random split không có bất kỳ giá trị nào.

UDI là thứ tự hàng, chưa được xác nhận là timestamp, lịch sản xuất hoặc machine ID. Các phát biểu EDA về chu kỳ ngày/đêm/mùa vụ là diễn giải chưa có timestamp để kiểm chứng; random walk không tự chứng minh tính tuần hoàn. Tool wear có tích lũy/reset theo cơ chế nguồn, nhưng chưa có ID xác thực cho mỗi tool/máy. Không tự tạo machine groups bằng Product ID duy nhất hoặc coi các giá trị nhiệt độ bằng nhau là cùng máy.

Trộn ngẫu nhiên có thể đưa các hàng gần nhau/cùng chế độ nhiệt vào cả train và test. Bỏ UDI khỏi features ngăn dùng ID trực tiếp, nhưng không loại phụ thuộc thông qua nhiệt độ. Vì vậy điểm số có thể thuận lợi hơn cho nội suy cùng chế độ so với dự báo một đoạn mới; sai số dưới giả định IID có thể đánh giá thiếu bất định. Chưa có số đo mức chênh lệch này.

## 3. Random stratified 60/20/20 seed 42: phạm vi A5.1 đã chốt

| Khía cạnh | Đánh giá |
|---|---|
| Ưu điểm | Dễ tái lập, dùng chung B0/B1/B2/P; tận dụng dữ liệu cho bài toán mô phỏng tĩnh; stratify theo target giúp duy trì tỷ lệ lớp hiếm ở mức gần nhau do làm tròn |
| Hạn chế | Không tách chế độ nhiệt/đoạn UDI, không bảo đảm độc lập; một split không phản ánh bất định do chọn mẫu; tập validation nhỏ với lớp lỗi hiếm dễ overfit qua nhiều trials |
| Nhãn phụ | Stratify `Machine failure` không bảo đảm coverage/tỷ lệ từng TWF/HDF/PWF/OSF/RNF; không thêm stratification đa nhãn chỉ vì muốn coverage đẹp |
| Seed | 42 là quy tắc tái lập đã chọn, không là bằng chứng split đại diện hoặc tối ưu; không thử seed/split rồi chọn theo nhãn test hay điểm số |
| Phạm vi A5.1 đã phê duyệt | So sánh chi phí mô phỏng khi nội suy giữa các quan sát trong cùng bộ dữ liệu tổng hợp và các chế độ đã trộn |
| Tuyên bố chưa được hỗ trợ | Tổng quát hóa theo thời gian, máy/nhà máy mới, dự báo trước một horizon hoặc hiệu quả bảo trì thực tế |

**A5.1 đã phê duyệt:** giữ UCI AI4I 2020 và random split cho mục tiêu nội suy trên cùng dữ liệu tổng hợp; chấp nhận rủi ro phụ thuộc theo UDI/nhiệt độ và báo cáo giới hạn, không xác nhận IID. Audit duplicate/rà soát cấu trúc phụ thuộc vẫn cần hoàn thành trước split theo A5.3/A5.4. Theo [hướng dẫn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html), cấu trúc nhóm/thời gian cần thiết kế đánh giá phù hợp; stratification không thay thế việc đó.

Không loại chronological split vì thấy đoạn test dự kiến thiếu HDF. Thiếu một cơ chế lỗi phản ánh distribution shift và giới hạn phạm vi đánh giá, không tự làm split sai. Không dùng nhãn phụ của test tương lai để chọn ranh giới hay chiến lược chia. Nếu mục tiêu chính chuyển sang tổng quát hóa theo thứ tự, cần chủ dự án phê duyệt protocol khác; UDI vẫn chỉ là proxy cho thứ tự sinh, chưa là thời gian thực.

## 4. Exposure từ EDA toàn dữ liệu

Notebook đọc toàn CSV ở cell có `execution_count=3`; các cell 4/6/8/9/10/11/12 phân tích nhãn, Type–failure, tỷ lệ failure trong outlier, boxplot theo target, quy tắc nhãn phụ, tương quan và cụm theo thứ tự. Báo cáo còn dùng phân bố HDF để khuyến nghị random split và tỷ lệ lỗi ở outlier để khuyến nghị không clipping. Những thông tin này có khả năng ảnh hưởng quyết định phát triển, dù tác giả gọi là integrity audit.

Chưa thấy bằng chứng đã fit/tune mô hình trên test; cũng chưa có split chính thức. Tuy nhiên các hàng sau này thành test đã góp vào EDA, nên không có cơ sở gọi test đó là hoàn toàn chưa bị xem xét. Chia lại hoặc đổi seed trên cùng dataset không xóa exposure. Cô lập sau split chỉ hạn chế sử dụng tiếp, không khôi phục tính độc lập hồi tố.

Trong review PR #6 đã trình hai lựa chọn; **A5.2 chọn tiếp tục AI4I và công khai exposure**:

1. **Đã phê duyệt:** tiếp tục AI4I dù EDA đã khảo sát toàn bộ nhãn; công khai giới hạn trong phương pháp luận và báo cáo cuối. Từ thời điểm khóa giao thức, không dùng nhãn/kết quả Test để chọn features, thuật toán, hyperparameters, threshold, calibration hoặc thay đổi split. Không dùng Test để sửa policy sau đánh giá cuối hoặc tuyên bố holdout chưa từng bị xem xét.
2. Dữ liệu kiểm chứng độc lập mới là phương án lịch sử chưa được yêu cầu/kích hoạt; chưa có dữ liệu như vậy đã xác minh. Không tự đổi dataset, mở thí nghiệm mới hoặc tuyên bố đã có holdout sạch.

Khi được giao G3 và quyền dữ liệu/config/metadata tương ứng, chỉ audit trước split trong phạm vi đã duyệt và dùng target cơ học để phân tầng theo A5.4; không dùng thao tác tạo split làm quyền khám phá/đánh giá Test. Tách integrity/phụ thuộc khỏi EDA định hướng mô hình; không xuất khám phá Test, tỷ lệ lỗi theo nhóm hoặc hình Test trong development. Không dùng nhãn Test để so sánh các phương án chia. Nhiệm vụ hiện tại không thực hiện các bước audit/split này.

## 5. Duplicate và phụ thuộc hàng: kiểm tra hiện có và đề xuất

| Định nghĩa | Bằng chứng đã có | Kết luận |
|---|---|---|
| Trùng toàn 14 cột | Notebook cell 3: `df.duplicated().sum()` = 0 | Đã có output của Antigravity, Codex chưa tái chạy raw |
| Trùng 12 cột sau bỏ hai ID | `df.drop(columns=["UDI", "Product ID"]).duplicated().sum()` = 0 | Còn target và 5 nhãn phụ; không phải kiểm tra sáu features |
| Trùng đúng sáu features X, kể cả X giống nhưng target khác | Chưa thấy phép đếm riêng trong notebook | Chưa xác minh; không được báo 0 |
| Hàng gần nhau, gần trùng hoặc cùng chế độ nhiệt | Có EDA theo UDI, chưa có ngưỡng/khoảng phụ thuộc định lượng | Không thể loại trừ chỉ từ kết quả exact duplicates |

Quy tắc A5.3/A5.4 áp dụng cho task G3 **sau khi được giao riêng**. Các phương án group-disjoint/blocked hoặc xử lý near-duplicate bên dưới vẫn là **đề xuất cần phê duyệt riêng nếu phát sinh**, chưa là protocol thay thế được chốt:

1. Giữ raw và nhãn UCI nguyên bản. Không xóa outlier, relabel, gộp trung bình hoặc làm tròn X để tạo nhóm; không biến các nhãn phụ thành feature. Sáu features giữ nguyên theo spec, không tự thêm ΔT/power/overstrain từ dictionary.
2. Audit exact duplicate trên đúng sáu features trước split, không dùng target/nhãn phụ làm khóa nhóm. Báo số lượng quan sát trùng khi phát hiện. Chưa có phép audit mới được chạy trong nhiệm vụ ghi nhận này; phần lưu metadata chi tiết triển khai theo quyền G3 được giao riêng.
3. Nếu không có nhóm X trùng và không phát hiện định danh phụ thuộc mới: dùng random split đã duyệt cho mục tiêu nội suy, vẫn ghi rủi ro phụ thuộc gần nhau. Không suy luận “không duplicate” thành “độc lập”.
4. Nếu có nhóm X trùng: **dừng trước split chính thức, trình kết quả để chủ dự án duyệt điều chỉnh**. Khuyến nghị giữ mọi hàng và đặt toàn bộ nhóm vào một partition/fold; nhóm không dựa trên y, kể cả nhãn mâu thuẫn. Cách chia group-disjoint có thể chỉ xấp xỉ 60/20/20 và stratification; cần phê duyệt thuật toán/tolerance cụ thể, không lặng lẽ đổi tỷ lệ hoặc tìm seed đẹp. Không tự deduplicate vì làm thay đổi trọng số quan sát và tổng cost.
5. Nếu sau này có bằng chứng ID máy/tool hoặc nhóm thật: trình group-aware split/CV cho mục tiêu máy mới; nếu mục tiêu thứ tự thì trình blocked/forward evaluation. Không tự gán độ rộng block/gap từ nhãn HDF hoặc chọn theo điểm số. Near-duplicate chỉ được xử lý khi đã có định nghĩa khoảng cách/tolerance và phê duyệt riêng.

## 6. Quy tắc A5 đã phê duyệt

- **A5.1 — Mục tiêu:** giữ UCI AI4I 2020; random split cho nội suy cùng dữ liệu tổng hợp. Ghi nhận/kiểm tra cấu trúc phụ thuộc theo UDI/nhiệt độ, báo giới hạn; không giả định các hàng độc lập hoặc tuyên bố dự báo thời gian, máy/nhà máy mới, hiệu quả bảo trì thực tế.
- **A5.2 — Exposure:** tiếp tục AI4I và công khai EDA toàn nhãn trong phương pháp luận/báo cáo cuối. Từ thời điểm khóa giao thức, không dùng nhãn/kết quả Test để lựa chọn phát triển hoặc đổi split; không gọi holdout chưa từng bị xem xét. Các lệnh cấm tuning/scenario/seed bằng Test ở spec giữ nguyên.
- **A5.3 — Duplicate:** audit đúng sáu X, giữ raw/nhãn UCI; có X trùng thì dừng trước split chính thức, báo số lượng và trình group-disjoint để phê duyệt riêng. Không tự xóa dữ liệu, đổi tỷ lệ/seed hoặc dùng target/năm nhãn phụ làm khóa.
- **A5.4 — Trình tự split:** giữ thứ tự nguồn theo UDI; tách **Test 20% trước**, stratify `Machine failure`, `random_state=42`; từ **80% còn lại** lấy **Validation 25%** (20% toàn dataset), stratify target, `random_state=42`; Train là **60% toàn dataset**. Không đảo bước hoặc thử seed/split để có kết quả/coverage nhãn phụ thuận lợi. Audit duplicate và rà soát phụ thuộc phải hoàn thành trước split; bất thường cần đổi protocol thì dừng/trình lại. Chưa chạy split trong nhiệm vụ này.
- **A5.4 — Tái lập:** lưu dataset hash, split IDs/hash, seed, thuật toán, phiên bản thư viện và metadata tái lập; dùng chung split. Tách trường split/model/optimizer/fold seeds theo spec. Quyền triển khai config/metadata liên quan chờ giao riêng G3.
- **A5.5 — Preprocessing:** chỉ sáu features đã duyệt; `Type`: `OneHotEncoder(handle_unknown="ignore")`; LR: `StandardScaler` cho năm numeric features; RF: giữ nguyên numeric, không bắt buộc scaling. Fit chỉ Train, Validation/Test chỉ transform bằng preprocessor fit Train. Missing bất ngờ phải báo lỗi rõ; không âm thầm impute. Không tự clipping outliers, feature engineering, resampling/SMOTE hoặc dùng ID/nhãn phụ làm feature.
- **A5.6 — RF calibration tại G5:** sigmoid, **5 stratified train folds**, `shuffle=True`, `random_state=42`, `ensemble=False`. Fit **preprocessing/model đúng từng fold**; không dùng Validation/Test để fit calibrator. Dữ liệu không đáp ứng yêu cầu calibration thì báo cáo/xin quyết định mới, không tự đổi method/folds. [Tài liệu calibration](https://scikit-learn.org/stable/modules/calibration.html) mô tả cơ chế tách model/calibrator, không bảo đảm hiệu quả trên dataset này. Không fit calibration trong nhiệm vụ ghi nhận A5.
- **A5.6 — Refit và B2:** không refit model trên **Train+Validation trước lần đánh giá Test đầu tiên**. Cấu hình baseline Logistic Regression B2 phải chốt **riêng trong A6 trước G4**; đề xuất B2 không post-calibration ở PR #6 **chưa được phê duyệt**. Không mở ablation tự phát.
- **A5.7 — Cổng Test tại G10:** chỉ mở để đánh giá sau khi khóa model/toàn bộ preprocessing; hyperparameters/threshold/policy; cost scenarios/constraints; seeds/dependencies/metadata/protocol và có **phê duyệt riêng từ chủ dự án**. Không đánh giá Test trong nhiệm vụ A5. Báo kết quả/vi phạm nguyên trạng, không dùng Test mở lại tuning; tái lập chỉ xác minh cấu hình đã khóa.

Các nguyên tắc đánh giá đã có vẫn giữ nguyên:

- Hyperparameter/threshold/scenarios chỉ chọn trên validation theo budget đã chốt. Không xem best validation cost là ước lượng không thiên lệch. B0/B1/B2/P cùng tập, công thức/cost/capacity; ghi cả infeasible và metric không xác định, không sửa threshold theo test.
- **Chẩn đoán thứ tự tùy chọn:** chỉ đề xuất cho task development riêng, dùng blocked/forward folds theo UDI trên development data với ranh giới/gap cố định trước khi chấm, không can thiệp holdout chính. Đây là kiểm tra độ nhạy với thứ tự sinh, không chứng minh dự báo thời gian thực. Nếu cần làm, phải đăng ký ranh giới, ngân sách, cách xử lý lớp thiếu và train-only fit/calibration theo fold trước chạy; không chọn thiết kế theo nhãn test hoặc chỉ báo cáo kết quả tốt. Chưa chạy và không là điều kiện phải thực hiện để đóng sản phẩm W1.
- **Bất định:** nhiều model/optimizer seeds trên cùng split chỉ đo độ ngẫu nhiên thuật toán; không khắc phục split dependence/exposure hoặc thay bằng confidence interval IID. Kiểm chứng thời gian thực cần dữ liệu có timestamp, horizon và lịch sử sự cố phù hợp; thay phạm vi này phải được duyệt.

## 7. Bảng đối chiếu A5 và trạng thái thực thi

**A5.1–A5.7 ĐÃ PHÊ DUYỆT về quy tắc**; không yêu cầu duyệt lại. Trạng thái thực thi chưa thay đổi chỉ từ việc ghi nhận văn bản.

| Quyết định | Nội dung đã chốt | Kiểm tra/thực thi và quyền còn cần |
|---|---|---|
| A5.1 | Nội suy AI4I; công khai phụ thuộc và giới hạn tuyên bố | Rà soát phụ thuộc trước split trong task được giao; chưa đo mới ở lượt này |
| A5.2 | Tiếp tục dù EDA toàn nhãn; công khai exposure; cấm Test selection từ lúc khóa protocol | Không có holdout hoàn toàn chưa bị xem xét; không đánh giá Test |
| A5.3 | Audit sáu X; giữ raw/nhãn; có duplicate thì dừng, báo số lượng | Chưa audit sáu X; group-disjoint nếu cần vẫn phải duyệt riêng |
| A5.4 | Test 20% trước; Validation 25% phần còn lại; stratify target/seed42 cả hai bước; IDs/hash/metadata | Chưa split; audit/phụ thuộc phải hoàn thành; G3/config/metadata chưa được giao |
| A5.5 | OHE Type ignore unknown; LR scaler numeric; RF numeric giữ nguyên; train-only fit, missing báo lỗi, không xử lý tự phát | Chưa code/fit pipeline; cấu hình B2 đầy đủ vẫn thuộc A6 |
| A5.6 | RF sigmoid 5 stratified train folds shuffle/seed42, ensemble=False tại G5; không refit Train+Val trước Test đầu | Chưa calibration/refit; dữ liệu không đạt thì xin quyết định mới; không chốt calibration B2 |
| A5.7 | Test tại G10 sau khóa toàn bộ model/policy/scenarios/seeds/dependencies/metadata/protocol và quyền riêng | Chưa có quyền đánh giá Test cuối; không mở Test trong nhiệm vụ A5 |

## 8. Điều kiện dừng và cổng thực thi

| Thời điểm | Điều kiện dừng | Xử lý theo phê duyệt |
|---|---|---|
| Hiện tại | Chưa merge PR ghi nhận A5/chưa có nhiệm vụ G3 và quyền config/metadata | Chỉ cập nhật ba tài liệu và báo cáo; không audit raw mới, split hoặc code pipeline |
| Trước split sau giao G3 | Có exact duplicate sáu X | Giữ raw/nhãn; báo số lượng và đề xuất group-disjoint; chờ phê duyệt riêng, không chia chính thức |
| Trước split sau giao G3 | Audit duplicate/rà soát phụ thuộc chưa hoàn thành, hoặc bất thường cần đổi protocol | Hoàn thành kiểm tra trong phạm vi giao; nếu cần thay protocol thì dừng/trình lại, không đổi tỷ lệ/seed |
| Preprocessing sau giao task | Missing bất ngờ | Báo lỗi rõ, không âm thầm impute/clipping hoặc sửa dữ liệu |
| Calibration G5 sau giao task | Dữ liệu không đáp ứng yêu cầu calibration đã duyệt | Báo cáo, xin quyết định mới; không tự đổi method/folds hoặc dùng Validation/Test fit calibrator |
| Test G10 | Chưa khóa đủ thành phần hoặc chưa có phê duyệt riêng | Không đánh giá Test |

**Sau khi PR ghi nhận A5 được merge**, chủ dự án sẽ giao riêng W2-G3-C và quyền sửa config/metadata liên quan. Đầu vào raw/hashes, dependency versions và kiểm tra tái lập phải đáp ứng nhiệm vụ được giao; phê duyệt văn bản chưa xác nhận chúng đã đạt. B2 chờ A6 trước G4; A2–A4/A6 còn các chi tiết ở PROJECT_SPEC cần chốt trước task tương ứng, không được coi là đã duyệt bởi A5. Không sửa sản phẩm/nhánh/worktree Antigravity. Nhiệm vụ hiện tại không tạo dữ liệu/split, code pipeline, baseline, ML, calibration fit, optimization hoặc kết quả Test.

## 9. W2-G3-C — triển khai sau kích hoạt riêng

### 9.1. Bằng chứng giao việc và phạm vi

Chủ dự án gửi nhiệm vụ G3 trong chat ngày 2026-10-23, attachment `066b5d85-3d0b-4ee2-bb7b-465cc1540273`, tệp `Văn bản đã dán.txt`, SHA-256 `94a56f011308fe16a3f4e86fbd76f744c1b2f47f38d93aae6782c1a540040461`. PR #7 được xác minh đã merge vào main tại `48cb306f01540a41498cb091e992cdea84e44e88`; nhánh G3 xuất phát trực tiếp từ mốc này.

Quyền sửa: `src/data.py`, `src/preprocessing.py`, `tests/test_data_pipeline.py`, tài liệu này, `scripts/run_data_pipeline.py`, riêng `configs/data_pipeline.yaml`, dữ liệu local bị ignore trong `data/processed/**`, logs/metadata nhỏ không chứa raw hoặc nội dung nhãn Test trong `results/w2_g3/**`. Chủ dự án cho phép tải raw UCI vào worktree Codex nếu thiếu; không đọc/ghi raw hoặc worktree Antigravity. Các file chung README, requirements, TASK_BOARD, data/README, PROJECT_SPEC chỉ đọc. Không tự chuyển task board sang Done.

### 9.2. Hợp đồng triển khai và khả năng tái lập

- `src/data.py`: xác minh hash trước đọc CSV; kiểm tra đúng 14 cột, schema/format/missing/finite, UDI theo thứ tự nguồn, ID và target nhị phân; chỉ lấy sáu feature bằng whitelist. Audit duplicate dùng đúng sáu X, `keep=False` để đếm mọi quan sát trong nhóm trùng và đếm nhóm riêng. Không sửa raw/nhãn, không bỏ hay clip hàng.
- ACF nhiệt độ được đo trước split tại các lag cố định `{1,5,10,50,100}`, theo UDI, không dùng target/nhãn phụ. Công thức: `sum((x[t]-mean)*(x[t+k]-mean))/sum((x-mean)^2)`, không hiệu chỉnh theo lag. Đây là mô tả phụ thuộc, không phải kiểm định IID/stationarity hoặc ước lượng chu kỳ. Review gắn với hash dataset trong config; không dùng ACF làm điểm số để tìm nhiều split hoặc tự chọn gap.
- `create_splits` luôn kiểm tra lại duplicate và yêu cầu review phụ thuộc trước khi gọi splitter. Hai lần `train_test_split` dùng seed42, stratify target: Test20% trước, Validation25% phần80% còn lại. Giữ nguyên thứ tự `remaining` mà sklearn trả về cho bước thứ hai; không sort hay thử lại để chọn coverage. Mảng đầu ra giữ thứ tự sklearn; input nguồn vẫn theo UDI.
- `src/preprocessing.py`: Pipeline gồm validator sáu feature và ColumnTransformer. OHE Type `handle_unknown="ignore"`, dense float output; năm numeric dùng StandardScaler ở LR và passthrough ở RF. Validator chạy cả fit/transform, lỗi rõ với thiếu/thừa cột, missing/nonfinite hoặc kiểu sai. Không có estimator LR/RF, sampler, imputer, feature engineering hoặc calibration.
- `prepare_development` chỉ nhận X_train/X_validation, không nhận y hoặc Test; fit hai preprocessor trên Train, chỉ transform Validation. Preprocessor sklearn có thể clone để sau này fit lại trong từng train fold, không mang state toàn train vào calibration fold.
- Split CSV, split IDs, preprocessor joblib và các mảng đã transform chỉ lưu dưới `data/processed/w2_g3/<run-id>/`, bị Git ignore. **Không transform hoặc đánh giá Test thật trong G3**; đường transform Test được kiểm thử bằng fixture tổng hợp. Test được ghi local bằng partition cố định, nhãn chỉ dùng cơ học cho phân tầng/lưu split, không có histogram/coverage/metrics Test trong report.
- Manifest public có quy mô/hash ordered IDs, hash file local và mảng development, thông tin chống leakage, dependency versions/config hash/commit nguồn/lệnh/runtime; không có giá trị raw, danh sách nhãn hoặc thống kê nhãn Test. IDs chi tiết chỉ ở manifest local. Hash ordered IDs dùng JSON canonical UTF-8, compact/sort keys và LF; tên file/mtime không tham gia hash.
- Mỗi run dùng thư mục mới, không ghi đè log hoặc artifact. Nếu hash/schema/duplicate/review không đạt, ghi `BLOCKED` trước split; lỗi khác ghi `FAILED`, giữ nguyên bằng chứng. Config từ chối thay đổi seed/tỷ lệ/features/hash tham chiếu hoặc quy tắc preprocessing đã khóa.

Lệnh chạy từ worktree Codex, Python 3.11 riêng:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip check
.\.venv\Scripts\python.exe -X utf8 -m pytest tests/test_data_pipeline.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe -X utf8 scripts/run_data_pipeline.py --run-id g3_reproduce
.\.venv\Scripts\python.exe -X utf8 scripts/run_data_pipeline.py --run-id g3_submission
```

Các run sau chỉ xác minh lại **cùng cấu hình, seed và membership**, không tạo ứng viên split khác để chọn. Thư mục đã tồn tại phải dùng tên mới để giữ log cũ; không xóa/ghi đè. `--audit-only` chỉ chạy audit và không tạo split.

### 9.3. Kết quả G3 đã chạy

- Raw có sẵn/tải từ đúng URL UCI ghi ở trên, không lấy từ worktree Antigravity. Nhật ký acquisition ghi tải ZIP ngày `2026-10-23T14:14:54Z` bằng `urllib`/`ZipFile`, chỉ ghi CSV sau khi hash khớp. ZIP: 522,170 bytes, SHA-256 `f601f14294bcf190f9d720676b7f0aea46a26cde9ab8ebc7b4f8174d9d26b252`; CSV: 522,048 bytes, SHA-256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`. Đây là khớp hash Antigravity đã báo và hash cấu hình.
- Audit thực tế: 10,000 hàng, 14 cột đúng thứ tự UCI; UDI duy nhất/liên tục và raw đã ở thứ tự UDI; target/năm nhãn phụ nhị phân; không missing, chuỗi rỗng hoặc giá trị số nonfinite. Exact duplicate trên đúng sáu X được kiểm tra bằng `pandas.DataFrame.duplicated(subset=FEATURES, keep=False)`, không làm tròn/chuẩn hóa và không dùng ID/target/nhãn phụ làm khóa: **0 hàng trong nhóm trùng, 0 nhóm, 0 hàng dư**.
- ACF mô tả theo UDI, không dùng nhãn, công thức ở §9.2. Air temperature tại lag `{1,5,10,50,100}`: `0.999359, 0.997522, 0.995280, 0.979360, 0.960316`; Process temperature: `0.998466, 0.993409, 0.987248, 0.943709, 0.892249`. Tự tương quan cao và giảm theo lag, phù hợp phụ thuộc random-walk nhiệt đã biết. Không thấy cấu trúc mới trong phép rà soát này cần đổi protocol; đây không phải chứng minh IID, stationarity, chu kỳ hoặc khả năng tổng quát hóa theo thời gian. Kết luận chỉ hỗ trợ split nội suy đã duyệt và phải công khai giới hạn.
- Sau các audit trên, ba lần chạy thành công `g3_reproduce`, `g3_verified`, `g3_submission` đều tạo cùng manifest SHA-256 `6dd33ba68c5a4d5d18b8db1fbe4d6f57f8dbfe667d96fe21d6d61bf62cf64522`: Train 6,000, Validation 2,000, Test 2,000; không giao nhau và bảo toàn 10,000 IDs. Hash ID theo thứ tự đã trả về của sklearn: Train `45f20d18308b53ace240dc55b0af55812509fe5af4bfed76494396d31536b99d`, Validation `3783ff7b44647e94aba4a9c8f15332a0a3e1b5c16c0e5e5b71d094ea7318eeb9`, Test `708cea9ae5f5d450f609a34bf07b568a54be1485c6759a9fa1298a76c5b99f2b`. Chi tiết ID và split CSV chỉ nằm local trong `data/processed/w2_g3/` bị ignore.
- LR preprocessor dùng OHE + StandardScaler; RF dùng OHE + passthrough numeric. Manifest ghi cả hai fit trên 6,000 dòng Train và transform 2,000 Validation. Hàm chuẩn bị dữ liệu không nhận target hoặc Test; không transform Test thật, không xuất thống kê/coverage/metrics nhãn Test và không fit mô hình. Hash dữ liệu train/validation đã biến đổi, config, commit nguồn, lệnh, versions và runtime được ghi trong `results/w2_g3/runs/*/run.json`; metadata công khai chỉ có hash, không chứa hàng raw/nhãn Test.
- Python: 3.11.9 64-bit trên Windows 10 (build `10.0.26200-SP0`), pip 24.0. Dependencies đã xác minh trong môi trường gồm NumPy 2.4.6, pandas 3.1.0, SciPy 1.17.1, scikit-learn 1.9.1, Optuna 5.0.0, matplotlib 3.11.2, seaborn 0.13.2, joblib 1.6.0, PyYAML 6.0.3, pytest 9.1.1, JupyterLab 4.6.4, ipykernel 7.4.0. `pip check` đạt; không sửa `requirements.txt` hoặc cài thêm dependency trong G3.
- Kiểm thử: `43 passed`; lệnh đúng như block trên. Kết quả và SHA-256 source test được lưu ở `results/w2_g3/unit_tests_recheck.json`. Các test dùng fixture tổng hợp để kiểm tra hash mismatch, CSV/header/schema/missing, duplicate gate, dependency gate, split determinism/disjointness, fit chỉ trên Train, category chưa thấy, scaler và lỗi đầu vào; không đánh giá nhãn Test thật.
- Có một lần chạy đầu `g3_primary` ở commit `4a3271c2c19ee1ce62069c834fcb6146e97f857b` bị `BLOCKED` trước split vì parser header chưa xử lý UTF-8 BOM của CSV UCI. Lỗi đã được sửa trong commit `4f47134cdf74a251a676a535880e0ef7ecf82faf` bằng cách decode BOM để kiểm tra header trong khi giữ nguyên bytes/hash raw. Nhật ký BLOCKED được giữ lại, không ghi đè; kiểm thử và các lần chạy hoàn tất đều dùng commit sau sửa.

**Bàn giao G3:** pipeline, audit, split và preprocessing đã hoàn tất theo A5.3–A5.5; không train/calibrate, không đánh giá Test và không kích hoạt G4. `READY FOR G4` chưa đạt trong task này vì cần giao nhiệm vụ G4 riêng và hoàn tất/chốt các điều kiện G4 liên quan, bao gồm cấu hình B2 theo A6. Không cập nhật TASK_BOARD vì văn bản W2-G3-C chỉ cho phép đọc file chung đó.
