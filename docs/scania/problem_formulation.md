# SC-G1-C — Problem formulation Scania APS

Ngày: **2026-10-25 (Asia/Saigon)**. Tài liệu thiết kế trình chủ dự án, **chưa code/chạy dữ liệu**. Trạng thái từng lựa chọn tại [decision_register.md](decision_register.md): D đã duyệt, P đề xuất chờ duyệt, A chờ audit, L giai đoạn sau. Phê duyệt P0/merge PR #12 không phê duyệt tất cả P.

## 1. Bài toán, bằng chứng và phạm vi

Chủ dự án nghiệm thu P0 và giao SC-G1-C trong chat ngày 2026-10-25. PR #12 đã merge/main tại `c52d89ef7d9d0ee8f5e35f12c2f0f63777835d4b`, đã fetch/API xác minh. Chỉ tạo bốn tài liệu `docs/scania/{problem_formulation,experimental_protocol,cost_model_review,decision_register}.md`; giữ nguyên mọi sản phẩm AI4I/P0/Antigravity và file chung. Không tải dataset/audit raw/split/train/baseline/Optuna/Test; không tự merge hoặc giao task kế tiếp.

Mục tiêu: học mô hình dự đoán lớp APS, chọn chính sách có benchmark misclassification cost thấp dưới capacity tối đa 10%, so sánh B0/B1/B2 và phương pháp RF tương lai trên cùng giao thức. G1 chỉ xây formulation/protocol/tests specification, không tạo “kết quả Scania”.

## 2. Dữ liệu, nhãn, đơn vị quan sát/action

**D01–D03:** dataset chính [APS Failure at Scania Trucks — UCI 421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks), DOI [10.24432/C51S51](https://doi.org/10.24432/C51S51); `pos=1`, `neg=0`. Neg chỉ lỗi ngoài APS, không đồng nghĩa xe hoàn toàn khỏe. `a=1` là dự đoán dương/đề xuất kiểm tra APS, `a=0` là không dự đoán dương APS; không xác nhận tác động can thiệp hoặc xe an toàn nói chung.

Đơn vị phân tích đề xuất P01: một hàng nguồn có nhãn component, chấm một quyết định/hàng. Không suy ra một hàng tương ứng một xe độc lập, một thời điểm hay một horizon trước hỏng; không có giả định machine/time IDs đã xác minh. Numeric features ẩn danh, không diễn giải thành Tool wear/Type/UDI/cơ chế failure của AI4I. Không áp luật dấu/miền vật lý AI4I cho các cột ẩn danh.

**D06–D08:** official Train 60.000 tách Train 48.000/Validation 12.000 stratified seed 42; official Test 16.000 khóa tới G10; fit preprocessing/handling missing chỉ Train. Schema local, số predictor, header/preamble, hash/bytes và missing/duplicates là A. Metadata UCI ghi171 features nhưng mô tả171 attributes gồm class; dự kiến170 predictors chỉ là giả thuyết audit. [Nguồn UCI](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks). Data contract và Test boundary ở [protocol](experimental_protocol.md), không đọc CSV để xác nhận trong G1.

## 3. Decision variables và objective

**D04/D10:** cost và RF family đã duyệt. **P02/P09:** miền policy và H chi tiết đề xuất, chưa phải cấu hình chạy:

```text
x = (h, τ), h ∈ H (chưa chốt), τ ∈ [0,1]
p_i(h) = score xác suất lớp APS=1 từ pipeline fit trên Train
a_i(h,τ) = 1[p_i(h) >= τ]
FP = Σ(1-y_i)*a_i; FN = Σy_i*(1-a_i)
min C_APS(h,τ) = 10*FP + 500*FN
```

Trọng số model được học từ Train; h/τ có thể được chọn bằng Validation trong task/budget được giao sau này, không phải N actions tự chọn theo y. Split seed, model seed, schema và preprocessing không là biến để thử nhiều phương án rồi chọn số đẹp. Giá trị seed 42 **đã duyệt cho split**, các seed model/optimizer/calibration phải ghi riêng theo P/L.

Cost có đơn vị **cost units benchmark**, không phải VND/SEK hoặc hóa đơn doanh nghiệp. TP/TN không phát sinh khoản benchmark, không có η/C_PM của AI4I. Ma trận và ví dụ tính tay ở [cost review](cost_model_review.md). Capacity10% là ràng buộc đồ án bổ sung benchmark nguồn, không là bằng chứng năng lực dịch vụ Scania thực tế.

Đặt `P=Σy`, `M=Σa`, `TP=Σya`: suy ra `C_APS=10M+500P-510TP`, B0 a0 có `C_B0=500P`. Đây là đại số, không thực nghiệm. So sánh cùng partition/objective; không so tổng cost AI4I và APS như cùng thang đo, không suy ra tiết kiệm tiền/counterfactual effect. Không đổi params của cost AI4I để giả làm APS: cách đó có thể thu cost ở TP, trái benchmark.

## 4. Constraints và ngữ nghĩa threshold — P02

Mức capacity **D05**; với M nguyên, `K=floor(N/10)`, `M<=K`. Số học trên kích thước đã duyệt cho K_Validation1200, K_Test1600, không phải số hành động thật hoặc quyền chấm Test. Đề xuất batch là **toàn partition đang chấm**, không cộng floor các batch nhỏ; recall chỉ metric, không thêm constraint hoặc penalty chưa duyệt.

| Quy ước P02 chờ duyệt | Cách xử lý đề xuất |
|---|---|
| Miền/comparator | τ∈[0,1], `>=`, p finite trong[0,1]; không rounding, clip, epsilon hoặc τ>1 |
| Ties | Các p exact bằng nhau được giữ nguyên nhóm; không top-k/tách ties theo y/ID/random để ép K |
| Endpoints | τ0 chọn tất cả kể cả p0; τ1 vẫn chọn p1; B0 policy riêng, không giả là τ1 |
| Capacity violation | excess=max(0,M-K), excess_rate=excess/N; feasibility iff excess0; báo nguyên trạng cost/actions/metrics, không tự sửa threshold baseline |
| Empty/invalid | N=0/shape/nonbinary/nonfinite/domain sai là ERROR input; khác policy input hợp lệ nhưng infeasible |
| P=0 | Cost/capacity vẫn tính; recall/null metrics theo P08, không bỏ batch khỏi cost |
| Threshold candidates | T(p)={0,1}∪unique(p Validation), exact sorted/dedup, chấm từng candidate và log count; không search thật trong G1 hoặc cho fixed baselines G4 |

T(p) phủ các action vectors biểu diễn được theo domain/comparator đề xuất. Với h cố định, `count(p=1)>K` làm mọi τ trong[0,1] vi phạm; không suy ra mọi H vô nghiệm. Nếu max(p)<1, τ1 biểu diễn all-zero cho h đó; B0 vẫn độc lập. Stump có ít mức p nên ties lớn có thể để trống capacity; không tự lấp bằng một phần leaf.

## 5. Chọn nghiệm/no-feasible — P02, H cụ thể L

Lọc candidates hợp lệ và feasible trước; chọn **minimum observed Validation cost**. Hòa khi chênh tuyệt đối≤1e-9 cost units so với minimum toàn bộ, không gom dây chuyền. Trong nhóm hòa: M nhỏ hơn; với cùng h, τ lớn hơn; sau đó thứ tự h cố định đăng ký trước search, không thứ tự trials hoàn thành. Thứ tự H cụ thể chỉ chốt trước G7. Benchmark cost số nguyên làm phần lớn so sánh hòa chính xác, nhưng quy tắc số vẫn phải khóa/test thống nhất.

Nếu không candidate feasible: `best=null`, `status=NO_FEASIBLE_CANDIDATE`, log candidate count/phạm vi h đã xét; không âm thầm thay bằng B0 hoặc kết luận toàn bài toán vô nghiệm. Baseline infeasible vẫn có row kết quả riêng, không tham gia feasible ranking. Đây là đề xuất Scania kế thừa ý tưởng kiểm chứng AI4I, **chưa tự phê duyệt T2**.

## 6. Baselines, công bằng và giới hạn so sánh

| Phương pháp | D về họ baseline/model | P cần chốt trước dùng |
|---|---|---|
| B0 Reactive | Không dự đoán dương APS, a0 | Output contract/cost/null metrics P08; không tạo p giả |
| B1 Decision Stump | Cây một mức (depth≤1, root-only hợp lệ) | P06 full params, preprocessing P05, model seed, p lớp1>=0.5; không chọn feature/leaf bằng Validation |
| B2 Logistic Regression | ML baseline LR | P07 full params/threshold/no weighting/calibration/refit, convergence failure; P05 |
| P Random Forest về sau | RF là mô hình chính | P09 H/fixed params/calibration/search/budget/seeds; không triển khai ở G1/G4 |

Cùng Train/Validation membership, target, cost, capacity và metric exceptions cho các phương pháp. Model fit/preprocessing chỉ Train; Validation chấm/selection trong budget đã duyệt, không fit calibrator/feature selection. B1 stump có probability model thật nếu dùng predict_proba nên AP/AUC/Brier khác rule B1 AI4I; B0 vẫn không có. Không tự dùng `.predict` ở tie 0.5 nếu policy đã chọn `>=`.

G4 dự kiến fixed B1/B2 p>=0.5; không tune threshold để baseline feasible, không đổi class_weight sau xem kết quả. Chưa kết luận fixed baseline ngưỡng 0.5 sẽ thất bại, P tốt hơn baseline hoặc lợi ích chỉ do optimizer. Search/calibration có budget khác; cần đối chứng/ablation riêng trước khi tách tác dụng. AP/Brier không tự chứng minh calibration hoặc tác động kinh tế.

## 7. Cổng nghiệm thu và giới hạn G1

G1 có đủ formulation, ma trận/ví dụ, decision register T1–T10 bốn nhóm, data boundary, proposed tests/stop gates và gói giao SC-G2-A tại [protocol](experimental_protocol.md). Đây là **READY FOR SCANIA G1 REVIEW: YES**, chưa chủ dự án nghiệm thu/chốt P. Chủ dự án duyệt gói audit/quyền trước G2, audit/missing/split trước G3, cost/policy/baseline/metric trước G4; không chốt tất cả RF/H để chỉ mở audit.

Không có raw/split/hash dataset local, thống kê missing/duplicate, model hoặc kết quả Test mới. Metadata công bố/nhận định P0-A không thay thế audit có provenance. Không tuyên bố IID, tổng quát hóa theo xe/thời gian/horizon hoặc official Test hoàn toàn chưa từng bị xem xét; từ nhiệm vụ này không mở Test. AI4I và mọi quyết định/kết quả lịch sử giữ nguyên.
