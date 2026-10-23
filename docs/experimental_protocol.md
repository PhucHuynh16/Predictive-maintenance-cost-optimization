# Rà soát A5 trước G3 — đề xuất, chưa phải protocol thực thi

Ngày: **2026-10-23 (Asia/Saigon)**. Codex thực hiện theo yêu cầu chủ dự án “Đóng checkpoint Tuần 1 và rà soát A5 trước G3”. Bản này chỉ review và trình lựa chọn; **chưa phê duyệt A5 bổ sung, chưa kích hoạt W2-G3-C**, chưa tạo split hay code pipeline.

## 1. Căn cứ và mức độ kiểm chứng

- Base `origin/main`: `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f`, sau PR #1/#3/#4/#5. Đã đọc AGENTS, ROADMAP, PROJECT_SPEC, TASK_BOARD, prompt Codex và [Issue #2](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2).
- Đối chiếu tĩnh [EDA findings](eda_findings.md), [dictionary](data_dictionary.md), source/output [notebook](../notebooks/01_eda.ipynb), [proposal](project_proposal.md) và [pipeline](../figures/pipeline.mmd) đã merge. Không chạy lại notebook, không tải/đọc raw ở worktree Antigravity. Codex hiện không có raw trong worktree của mình.
- Các số EDA dưới đây là kết quả Antigravity đã báo cáo, không phải phép đo mới của Codex. Chưa đo autocorrelation theo lag, độ dài phụ thuộc hoặc effective sample size; không đưa ra hệ số hay p-value chưa tính.
- A5 hiện hành ở [PROJECT_SPEC §2/§9/§10](PROJECT_SPEC.md): sáu features và target đã chốt; random stratified 60/20/20 seed 42 có điều kiện kiểm tra phụ thuộc; train-only fit, train-fold calibration và khóa test đã chốt. Những đề xuất dưới đây không sửa các quyết định đó.

## 2. Phụ thuộc theo UDI và nhiệt độ

Nguồn [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) mô tả hai biến nhiệt độ dùng random walk; nhiệt độ quá trình còn cộng nhiệt độ môi trường. EDA ghi nhận 108/115 HDF ở UDI 4000–4999, 7 ca còn lại ở 3000–3999, cùng biến thiên nhiệt theo thứ tự. Đây là bằng chứng định tính rõ rằng không nên giả định các hàng độc lập, phân phối đồng nhất theo mọi đoạn UDI.

Mức độ định lượng còn chưa biết: tương quan Air–Process `r=0.876` trong dictionary là tương quan giữa hai feature, không phải tự tương quan giữa các hàng. Cụm HDF thể hiện phân bố lỗi thay đổi theo đoạn; không tự chứng minh quan hệ nhân quả hay sự phụ thuộc còn lại sau khi điều kiện hóa đủ features. Chưa đủ bằng chứng để ấn định một gap/block width hay kết luận random split không có bất kỳ giá trị nào.

UDI là thứ tự hàng, chưa được xác nhận là timestamp, lịch sản xuất hoặc machine ID. Các phát biểu EDA về chu kỳ ngày/đêm/mùa vụ là diễn giải chưa có timestamp để kiểm chứng; random walk không tự chứng minh tính tuần hoàn. Tool wear có tích lũy/reset theo cơ chế nguồn, nhưng chưa có ID xác thực cho mỗi tool/máy. Không tự tạo machine groups bằng Product ID duy nhất hoặc coi các giá trị nhiệt độ bằng nhau là cùng máy.

Trộn ngẫu nhiên có thể đưa các hàng gần nhau/cùng chế độ nhiệt vào cả train và test. Bỏ UDI khỏi features ngăn dùng ID trực tiếp, nhưng không loại phụ thuộc thông qua nhiệt độ. Vì vậy điểm số có thể thuận lợi hơn cho nội suy cùng chế độ so với dự báo một đoạn mới; sai số dưới giả định IID có thể đánh giá thiếu bất định. Chưa có số đo mức chênh lệch này.

## 3. Random stratified 60/20/20 seed 42: ý nghĩa và giới hạn

| Khía cạnh | Đánh giá |
|---|---|
| Ưu điểm | Dễ tái lập, dùng chung B0/B1/B2/P; tận dụng dữ liệu cho bài toán mô phỏng tĩnh; stratify theo target giúp duy trì tỷ lệ lớp hiếm ở mức gần nhau do làm tròn |
| Hạn chế | Không tách chế độ nhiệt/đoạn UDI, không bảo đảm độc lập; một split không phản ánh bất định do chọn mẫu; tập validation nhỏ với lớp lỗi hiếm dễ overfit qua nhiều trials |
| Nhãn phụ | Stratify `Machine failure` không bảo đảm coverage/tỷ lệ từng TWF/HDF/PWF/OSF/RNF; không thêm stratification đa nhãn chỉ vì muốn coverage đẹp |
| Seed | 42 là quy tắc tái lập đã chọn, không là bằng chứng split đại diện hoặc tối ưu; không thử seed/split rồi chọn theo nhãn test hay điểm số |
| Tuyên bố được phép nếu duyệt | So sánh chi phí mô phỏng khi nội suy giữa các quan sát trong cùng bộ dữ liệu tổng hợp và các chế độ đã trộn |
| Tuyên bố chưa được hỗ trợ | Tổng quát hóa theo thời gian, máy/nhà máy mới, dự báo trước một horizon hoặc hiệu quả bảo trì thực tế |

Đề xuất giữ phương án chính random split để phù hợp mục tiêu đồ án một kỳ, **với việc chủ dự án chấp nhận giới hạn và điều kiện duplicate ở §5**. Đây là chấp nhận đánh giá nội suy có phụ thuộc, không phải xác nhận IID. Theo [hướng dẫn cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html), cấu trúc nhóm/thời gian cần thiết kế đánh giá phù hợp; stratification không thay thế việc đó.

Không loại chronological split vì thấy đoạn test dự kiến thiếu HDF. Thiếu một cơ chế lỗi phản ánh distribution shift và giới hạn phạm vi đánh giá, không tự làm split sai. Không dùng nhãn phụ của test tương lai để chọn ranh giới hay chiến lược chia. Nếu mục tiêu chính chuyển sang tổng quát hóa theo thứ tự, cần chủ dự án phê duyệt protocol khác; UDI vẫn chỉ là proxy cho thứ tự sinh, chưa là thời gian thực.

## 4. Exposure từ EDA toàn dữ liệu

Notebook đọc toàn CSV ở cell có `execution_count=3`; các cell 4/6/8/9/10/11/12 phân tích nhãn, Type–failure, tỷ lệ failure trong outlier, boxplot theo target, quy tắc nhãn phụ, tương quan và cụm theo thứ tự. Báo cáo còn dùng phân bố HDF để khuyến nghị random split và tỷ lệ lỗi ở outlier để khuyến nghị không clipping. Những thông tin này có khả năng ảnh hưởng quyết định phát triển, dù tác giả gọi là integrity audit.

Chưa thấy bằng chứng đã fit/tune mô hình trên test; cũng chưa có split chính thức. Tuy nhiên các hàng sau này thành test đã góp vào EDA, nên không có cơ sở gọi test đó là hoàn toàn chưa bị xem xét. Chia lại hoặc đổi seed trên cùng dataset không xóa exposure. Cô lập sau split chỉ hạn chế sử dụng tiếp, không khôi phục tính độc lập hồi tố.

Hai lựa chọn trình chủ dự án:

1. **Khuyến nghị cho phạm vi 5 tuần:** tiếp tục AI4I, công khai exposure và coi holdout cuối là đánh giá giới hạn trên dữ liệu đã được khảo sát; từ lúc khóa protocol, ngừng mọi EDA/selection trên test. Không dùng test để sửa policy sau đánh giá cuối.
2. Nếu bắt buộc có kiểm chứng độc lập nghiêm ngặt: cần dữ liệu mới chưa góp vào lựa chọn, nguồn/quyền/protocol được duyệt riêng. Không có dữ liệu như vậy đã xác minh trong checkpoint này; không tự đổi dataset hoặc tuyên bố đã có holdout sạch.

Chỉ kiểm tra integrity tối thiểu, định trước, cần để tạo split được phép chạm toàn dữ liệu sau phê duyệt: hash/schema/ID, kiểm tra duplicate theo X và cơ chế phân tầng target. Tách bước đó khỏi EDA định hướng mô hình; không xuất khám phá test, tỷ lệ lỗi theo nhóm hoặc hình test trong development. Nhãn test chỉ được bộ tạo split dùng cơ học theo quy tắc đã duyệt; không dùng để so sánh các phương án chia.

## 5. Duplicate và phụ thuộc hàng: kiểm tra hiện có và đề xuất

| Định nghĩa | Bằng chứng đã có | Kết luận |
|---|---|---|
| Trùng toàn 14 cột | Notebook cell 3: `df.duplicated().sum()` = 0 | Đã có output của Antigravity, Codex chưa tái chạy raw |
| Trùng 12 cột sau bỏ hai ID | `df.drop(columns=["UDI", "Product ID"]).duplicated().sum()` = 0 | Còn target và 5 nhãn phụ; không phải kiểm tra sáu features |
| Trùng đúng sáu features X, kể cả X giống nhưng target khác | Chưa thấy phép đếm riêng trong notebook | Chưa xác minh; không được báo 0 |
| Hàng gần nhau, gần trùng hoặc cùng chế độ nhiệt | Có EDA theo UDI, chưa có ngưỡng/khoảng phụ thuộc định lượng | Không thể loại trừ chỉ từ kết quả exact duplicates |

Đề xuất cho task G3 sau duyệt:

1. Giữ raw và nhãn UCI nguyên bản. Không xóa outlier, relabel, gộp trung bình hoặc làm tròn X để tạo nhóm; không biến các nhãn phụ thành feature. Sáu features giữ nguyên theo spec, không tự thêm ΔT/power/overstrain từ dictionary.
2. Audit exact duplicate trên sáu features trước split, theo giá trị đọc nguyên bản và kiểu/schema định trước, không dùng target/nhãn phụ làm khóa nhóm. Lưu số hàng, số nhóm và group IDs/hash trong metadata local. Chưa có phép audit mới được chạy trong nhiệm vụ review này.
3. Nếu không có nhóm X trùng và không phát hiện định danh phụ thuộc mới: dùng random split đã duyệt cho mục tiêu nội suy, vẫn ghi rủi ro phụ thuộc gần nhau. Không suy luận “không duplicate” thành “độc lập”.
4. Nếu có nhóm X trùng: **dừng trước split chính thức, trình kết quả để chủ dự án duyệt điều chỉnh**. Khuyến nghị giữ mọi hàng và đặt toàn bộ nhóm vào một partition/fold; nhóm không dựa trên y, kể cả nhãn mâu thuẫn. Cách chia group-disjoint có thể chỉ xấp xỉ 60/20/20 và stratification; cần phê duyệt thuật toán/tolerance cụ thể, không lặng lẽ đổi tỷ lệ hoặc tìm seed đẹp. Không tự deduplicate vì làm thay đổi trọng số quan sát và tổng cost.
5. Nếu sau này có bằng chứng ID máy/tool hoặc nhóm thật: trình group-aware split/CV cho mục tiêu máy mới; nếu mục tiêu thứ tự thì trình blocked/forward evaluation. Không tự gán độ rộng block/gap từ nhãn HDF hoặc chọn theo điểm số. Near-duplicate chỉ được xử lý khi đã có định nghĩa khoảng cách/tolerance và phê duyệt riêng.

## 6. Giao thức đánh giá đề xuất

- **Đánh giá chính:** một split duy nhất theo X/y gốc đã duyệt. Đề xuất chốt thứ tự stable theo UDI, giữ 20% test trước bằng stratified shuffle seed 42 theo `Machine failure`, rồi chia 80% còn lại thành train/validation tỷ lệ 75/25, stratify target với seed 42. Như vậy tỷ lệ danh nghĩa toàn bộ là 60/20/20. Chưa chạy hai bước này; thứ tự chia phải được duyệt vì cùng tỷ lệ/seed nhưng đảo bước sẽ cho IDs khác.
- Lưu dataset SHA-256, split IDs/hash, thuật toán/thứ tự, version scikit-learn và split seed; dùng chung mọi phương pháp. Model/optimizer/fold seeds có trường riêng. Không thử nhiều split để chọn coverage/cost/recall thuận lợi. Group case ở §5 buộc dừng để trình lại protocol.
- EDA từ đây chỉ development; fit encoding/scaling/imputation trên train, transform validation/test. Trong CV, fit **cả preprocessor và model bên trong từng train fold**, không dùng preprocessor đã fit toàn train cho dự đoán ngoài fold. Chi tiết encoder/scaler/missing/category handling cần khóa trước triển khai G3; không coi sơ đồ proposal là config được duyệt.
- **Calibration trình duyệt:** RF dùng sigmoid với 5 stratified train folds, shuffle=True, fold seed 42, `ensemble=False`: calibrator fit trên xác suất ngoài fold trong train; base pipeline fit lại toàn train, không train+validation. Các lựa chọn API phải được đối chiếu phiên bản đã cài trước G5. Nếu mỗi fold không đủ cả hai lớp hoặc phát hiện nhóm trùng thì dừng/trình lại, không tự giảm folds/đổi method. B2 đề xuất không post-calibration riêng, cần chốt cùng cấu hình baseline A6. Không mở ablation calibration trong task này. [Tài liệu calibration](https://scikit-learn.org/stable/modules/calibration.html) mô tả cách tách fit model/calibrator; không bảo đảm sigmoid tốt trên dữ liệu này.
- Hyperparameter/threshold/scenarios chỉ chọn trên validation theo budget đã chốt. Không xem best validation cost là ước lượng không thiên lệch. B0/B1/B2/P cùng tập, công thức/cost/capacity; ghi cả infeasible và metric không xác định, không sửa threshold theo test.
- **Refit/test gate đề xuất:** giữ pipeline đã fit train, calibrator từ train folds và policy chọn validation; không refit train+validation ở lượt test đầu. Đóng băng artifact/hash, code, dependencies, config, seeds, policy/scenario và protocol trước khi xin quyền test cuối tại G10. Đánh giá các phương pháp đã đăng ký, ghi đủ kết quả/vi phạm; không quay lại tuning bằng test.
- **Chẩn đoán thứ tự tùy chọn:** chỉ đề xuất cho task development riêng, dùng blocked/forward folds theo UDI trên development data với ranh giới/gap cố định trước khi chấm, không can thiệp holdout chính. Đây là kiểm tra độ nhạy với thứ tự sinh, không chứng minh dự báo thời gian thực. Nếu cần làm, phải đăng ký ranh giới, ngân sách, cách xử lý lớp thiếu và train-only fit/calibration theo fold trước chạy; không chọn thiết kế theo nhãn test hoặc chỉ báo cáo kết quả tốt. Chưa chạy và không là điều kiện phải thực hiện để đóng sản phẩm W1.
- **Bất định:** nhiều model/optimizer seeds trên cùng split chỉ đo độ ngẫu nhiên thuật toán; không khắc phục split dependence/exposure hoặc thay bằng confidence interval IID. Kiểm chứng thời gian thực cần dữ liệu có timestamp, horizon và lịch sử sự cố phù hợp; thay phạm vi này phải được duyệt.

## 7. Quyết định tối thiểu trình chủ dự án trước W2-G3-C

Tất cả các hàng dưới đây **CHỜ QUYẾT ĐỊNH**; không yêu cầu duyệt lại sáu features, cost, capacity hoặc seed đã chốt.

| Mục bổ sung A5 | Khuyến nghị cụ thể | Lựa chọn còn cần chốt |
|---|---|---|
| Mục tiêu và phụ thuộc | Chấp nhận random split cho nội suy cùng dữ liệu tổng hợp có phụ thuộc; không tuyên bố temporal generalization | Chấp nhận giới hạn này, hoặc đổi mục tiêu/protocol trước split |
| Exposure | Công khai EDA toàn nhãn; cô lập test từ sau khóa protocol | Tiếp tục với holdout giới hạn, hoặc yêu cầu dữ liệu độc lập mới |
| Duplicate | Audit đúng sáu X; raw/nhãn giữ nguyên; nếu có X trùng thì dừng và trình group-disjoint | Phê duyệt audit và điều kiện dừng; không tự coi group split đã duyệt |
| Tạo split và EDA scope | UDI order; test 20% trước, validation 25% của 80% còn lại; stratify y, seed 42 mỗi bước; không chọn seed/coverage | Duyệt thứ tự/thuật toán, metadata IDs/hash và giới hạn truy cập test |
| Preprocessing G3 | Sáu features; đề xuất OneHotEncoder Type với handle_unknown=ignore, StandardScaler cho 5 numeric ở LR, numeric passthrough ở RF; không clipping/feature engineering/resampling; missing bất ngờ thì fail rõ | Duyệt cấu hình kỹ thuật cụ thể và quyền sửa config/metadata chung liên quan trong task G3 |
| Calibration và refit | RF sigmoid 5 train folds seed42, ensemble=False; B2 không calibration; không refit train+val; không ablation tự phát | Duyệt lựa chọn và điều kiện dừng ở §6; phần B2 còn thuộc chi tiết A6 trước baseline |
| Test gate | Freeze mọi artifact/protocol trước quyền đánh giá riêng G10; không tuning lại | Chấp nhận cổng này; chưa cấp quyền mở test cuối |

Sau quyết định A5 bổ sung, chủ dự án cần **giao riêng W2-G3-C**, xác định phạm vi config/split metadata chung được sửa và đầu vào raw đã xác minh hash trong worktree Codex. G3 chỉ bắt đầu khi các phụ thuộc đó đủ; nếu audit gặp duplicate/nhóm mới thì dừng phần chia tập. Dependency versions đã kiểm tra cài đặt cần được khóa và trình duyệt riêng trước số liệu thực nghiệm.

A2–A4/A6 còn các chi tiết ở PROJECT_SPEC cần chốt trước G4–G7 tương ứng; chúng không được tự coi là đã duyệt vì checkpoint W1 đóng. Nhiệm vụ hiện tại không sửa spec, quyết định A1–A7, config hoặc requirements; không có baseline/training/test cuối.
