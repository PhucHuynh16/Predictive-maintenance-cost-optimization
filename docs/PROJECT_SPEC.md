# PROJECT SPEC — quyết định đã phê duyệt và chi tiết chờ chốt

Ngày cập nhật: 2026-10-21 (Asia/Saigon). Đồ án cá nhân, 5 tuần, 10 giai đoạn theo `ROADMAP.md`. Lượt hiện tại chỉ cập nhật spec và tạo PR. **Không code cost model, train ML, chạy baseline/optimization hoặc đánh giá test trong nhiệm vụ này.**

## 0. Bằng chứng phê duyệt và phạm vi

- Commit [72b3d67526ca56e81900e301cbfcb310de916557](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/commit/72b3d67526ca56e81900e301cbfcb310de916557) đã đổi nhãn A1–A6 thành “Phê duyệt”. Chủ dự án sau đó cung cấp quyết định cụ thể A1–A7 trong câu trả lời cùng chat ngày 2026-10-21, mở đầu “Tôi là chủ dự án và xác nhận phê duyệt A1–A6 với các thông số cụ thể sau”. Quyết định chi tiết này là nguồn của các giá trị được ghi là đã phê duyệt bên dưới.
- Chủ dự án yêu cầu cập nhật toàn bộ `docs/PROJECT_SPEC.md`, bảo toàn hai tài liệu review, tạo nhánh/PR và không tự merge main. Đây là quyền sửa riêng file chung này; không bao gồm config, task board hay tài liệu của Antigravity.
- A7 đã kích hoạt riêng **W1-G1-C** (review, Codex) và **W1-G2-A** (kiểm tra dữ liệu, Antigravity). Không tự kích hoạt AI khác hoặc nhận thêm giai đoạn. Lượt Codex hiện tại không thực hiện task dữ liệu của Antigravity.
- Hai bản W1-G1-C `docs/problem_formulation.md` và `docs/cost_model_review.md` được giữ nguyên như bản review lịch sử. Chúng còn ghi “chờ duyệt” và đề xuất cũ; các quyết định mới trong spec này thay thế phần chờ duyệt tương ứng, không sửa ngầm bản review. Hai file còn untracked từ lượt trước, không nằm trong PR chỉ sửa spec.
- Chỉ dùng trạng thái **Đã phê duyệt** cho một mục đã đủ quyết định trong phạm vi được ghi. **Phê duyệt một phần** nghĩa là các lựa chọn/giá trị cụ thể đã được chấp nhận, nhưng còn quy tắc chi tiết cần chốt; không được suy diễn rằng phần chưa chốt cũng đã được duyệt. Chi tiết tại §10.

## 1. Problem statement và đơn vị quan sát — A1

Từ đặc trưng vận hành, ước lượng nguy cơ hỏng và chọn chính sách bảo trì có tổng chi phí mô phỏng nhỏ, đáp ứng nguồn lực. So sánh cùng dữ liệu, kịch bản và constraints cho mọi baseline/phương pháp.

**Đã phê duyệt:** một dòng AI4I là một quan sát vận hành; mô hình cost một kỳ; đơn vị **cost units**, không phải VND. Chi phí được cộng theo quan sát bằng công thức A2. Không suy ra mỗi hàng là một máy độc lập hoặc một lịch theo thời gian; không khẳng định tiết kiệm tiền thật. Công thức hiện tại không mô hình hóa horizon trước lỗi, phụ tùng, chi phí theo đợt hoặc constraint từng máy. Thay đổi đơn vị phân tích/giả định cần quyết định mới.

## 2. Dataset, target và features — A5

**Đã phê duyệt nguồn:** [AI4I 2020 — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C). Metadata UCI: dữ liệu tổng hợp, 10.000 quan sát, 6 feature, CC BY 4.0, metadata báo không missing. Đây là thông tin nguồn được xem ngày 2026-10-21, chưa phải kiểm tra CSV local. Theo mô tả UCI, nhiệt độ được sinh bằng random walk; cần kiểm tra phụ thuộc dữ liệu trước split.

**Đã phê duyệt target:** `Machine failure`. Sáu feature vận hành:

| Feature | Đơn vị/kiểu dự kiến |
|---|---|
| `Type` | Categorical |
| `Air temperature [K]` | K |
| `Process temperature [K]` | K |
| `Rotational speed [rpm]` | rpm |
| `Torque [Nm]` | Nm |
| `Tool wear [min]` | min |

Loại target, ID `UID`/`UDI`, `Product ID` và năm nhãn phụ `TWF`, `HDF`, `PWF`, `OSF`, `RNF` khỏi features. ID chỉ phục vụ truy vết/split, không suy ra timestamp hoặc machine ID. Xác minh tên cột thực tế trong task dữ liệu; ghi provenance theo [data/README](../data/README.md).

Chưa có quyền dùng EDA toàn bộ dữ liệu để lựa chọn mô hình. Quy tắc duplicate/nhóm/thứ tự, phân biệt kiểm tra integrity và EDA định hướng mô hình, cùng các điều kiện trước split còn cần chốt ở §9. Không ghi kiểm tra dữ liệu là đã chạy chỉ từ metadata.

## 3. Decision variables và policy — A3/A4

**Đã phê duyệt:** tối ưu `x=(h,τ)`, mô hình chính Random Forest. Giữ công thức policy/miền nguồn:

```text
h ∈ H, τ ∈ [0,1], p_i(h) ∈ [0,1]
a_i(h,τ) = 1[p_i(h) >= τ]
```

`h` là hyperparameter của pipeline fit trên train; `a_i=1` nghĩa là đề xuất bảo trì. Actions được suy ra từ p, không phải N biến nhị phân tự chọn theo nhãn y. H và quy tắc threshold cụ thể vẫn chờ duyệt ở §5/§7. Seed, split và kịch bản chi phí là điều kiện thí nghiệm, không phải biến để chọn kết quả đẹp. τ-only có thể làm ablation theo review nhưng chưa được giao chạy.

## 4. Objective, tham số và sensitivity — A2

**Công thức đã phê duyệt**, giữ nguyên từ roadmap; hậu tố `obs` chỉ phân biệt cách chấm bằng nhãn:

```text
min C_obs(h,τ) = Σ_i [C_PM*a_i + C_F*y_i*(1-η*a_i)]
```

| Đại lượng | Quyết định đã phê duyệt | Ý nghĩa |
|---|---|---|
| `C_PM` | 1 cost unit/hành động | Trả cho mọi action, kể cả hàng không lỗi |
| `C_F` | 20 cost units/sự cố | Tổn thất đầy đủ khi không can thiệp |
| `η` | 0.8 | Phần tổn thất giả định được tránh trên hàng lỗi được chọn |
| Đơn vị tổng cost | cost units | Chi phí mô phỏng, không phải VND |
| Sensitivity `C_F` | `{5,10,20,40}` | Giả định nghiên cứu được chủ dự án chọn |
| Sensitivity `η` | `{0.7,0.8,1.0}` | Giả định nghiên cứu được chủ dự án chọn |

Công thức cộng PM với tổn thất còn lại, không thay y bằng nhãn sau can thiệp. Với `y=1,a=1`, cost là `1+20*(1-0.8)=5 cost units`. Đây là **minh họa tính tay theo tham số đã duyệt**, không phải kết quả thực nghiệm. Miền công thức nguồn: cost hữu hạn không âm, `0<=η<=1`; mọi giá trị đã chọn nằm trong miền.

Dùng nhãn validation để chấm/chọn policy theo objective nguồn, không dùng test để tìm kiếm. Đặt `M=Σa_i`, `P=Σy_i`, `TP=Σy_i*a_i`: `C_obs=M+20*P-16*TP`; B0 tốn `20*P`. Đây là suy diễn đại số. Saving mô phỏng `C_B0-C_policy` có thể âm; không tạo số liệu thực nghiệm từ đẳng thức.

Chi phí kỳ vọng là đánh giá khác:

```text
C_exp(h,τ) = Σ_i [C_PM*a_i + C_F*p_i*(1-η*a_i)]
```

Không tráo C_exp với objective C_obs hoặc dùng làm bằng chứng can thiệp. Review đề xuất chỉ báo C_exp như chẩn đoán nếu cần; chưa giao thực nghiệm này. AI4I không cung cấp chi phí thực tế hoặc cặp kết quả phản thực tế để xác nhận η; các tham số/saving đều là giả định/kết quả mô phỏng có điều kiện.

**Thiết kế sensitivity còn cần duyệt chi tiết:** review chưa chốt quét từng yếu tố hay tích Descartes, đánh giá policy cố định hay tối ưu lại từng kịch bản. Đề xuất trình duyệt: đủ `4*3=12` tổ hợp C_F/η, giữ C_PM=1 và b=0.10; vòng đầu đánh giá lại policy đã khóa trên development data, reoptimization là nhánh riêng cần budget/giao việc riêng. Kịch bản chính (20,0.8) nằm trong 12 tổ hợp, không tính trùng. Các tập giá trị đã được duyệt; cách kết hợp và cách chạy này **chưa được duyệt**. Không thêm sensitivity b từ ví dụ roadmap.

## 5. Constraints, ties và ca biên — A3

**Đã phê duyệt:**

```text
b = 0.10
K = floor(b*N)
M = Σ_i a_i <= K
Recall là metric, không phải constraint.
```

N là số quan sát trong batch/tập đang chấm. Đây là capacity số hành động, không phải ngân sách tiền. Không đặt R_min hoặc penalty recall. B0 là policy không bảo trì riêng, a toàn 0, không giả làm τ=1. Ties được giữ nguyên nhóm, không âm thầm top-k. Policy vi phạm capacity được ghi `infeasible`, không nhận làm nghiệm tốt nhất khả thi. Áp dụng cùng constraint cho baseline và P.

Theo comparator/miền nguồn: τ=0 chọn mọi hàng kể cả p=0; τ=1 chọn các hàng p=1. Nếu `count(p=1)>K`, h cố định đó không có threshold capacity-feasible; không suy rộng rằng mọi H vô nghiệm. Với N nhỏ, b*N<1 cho K=0; không làm tròn lên. Capacity của cả batch dùng floor trên N toàn batch, không cộng floor của batch con. Threshold khóa trên validation có thể vi phạm trên test/dữ liệu mới; báo nguyên trạng, không tune lại bằng test.

Chủ dự án đã yêu cầu kiểm tra τ=0/1 và p=0/1. Các **quy ước chi tiết đề xuất, chưa tự coi đã duyệt**:

| Nội dung | Đề xuất trình duyệt |
|---|---|
| Tập threshold | `T(p)={0,1}∪unique(p_i)`, quét đủ policy biểu diễn được bởi `>=` và `[0,1]`; không tách ties |
| N=0/input sai | Reject evaluation với lỗi rõ; không báo feasibility/cost trung bình giả |
| P=0 | Recall=null và reason; capacity vẫn quyết định feasible vì recall không là constraint |
| Violation | `capacity_excess=max(0,M-K)` (hành động) và `capacity_excess_rate=capacity_excess/N`; không gộp khác đơn vị |
| Không có candidate khả thi | Best=null, `NO_FEASIBLE_CANDIDATE` kèm phạm vi tìm; không đưa B0 vào miền h,τ một cách ngầm định |
| Floor chính xác | Dùng biểu diễn b thập phân chính xác, tránh sai số float làm lệch K |
| Hòa cost | Ưu tiên M nhỏ hơn, rồi τ lớn hơn trong cùng h, rồi thứ tự h đăng ký trước |

Không tự đổi `>=` sang `>`, thêm τ>1 hoặc mở rộng miền policy. Đây là những thay đổi formulation cần quyết định mới.

## 6. Baseline và đề xuất ngưỡng — A6

| Mã | Đã phê duyệt | Chi tiết còn chờ duyệt |
|---|---|---|
| B0 | Reactive, không bảo trì trước, mọi a=0 | Dùng cùng cost/capacity, không cần p |
| B1 | Fixed Rule theo Tool wear | Comparator, w cụ thể và quy tắc cố định ngưỡng |
| B2 | Logistic Regression, threshold=0.5 | Cấu hình LR/preprocessing/calibration |
| P | Random Forest + tối ưu h,τ | Miền H và quy tắc tìm kiếm ở §7 |

**Đề xuất B1 để chủ dự án duyệt:** `a_i=1[Tool wear [min]>=200]`, w=200 phút, giữ cố định trước thực nghiệm, không chọn w bằng test và không sửa rule bằng top-k khi vi phạm. Mốc này là heuristic đề xuất theo mô tả wear failure 200–240 phút của [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset); không phải ngưỡng đã được chứng minh hiệu quả hoặc được chủ dự án duyệt. Chủ dự án có thể chọn mốc khác trước thực nghiệm. So với review cũ đề xuất tìm w trên validation, lựa chọn fixed w này phù hợp tên Fixed Rule vừa được xác nhận và vẫn cần phê duyệt giá trị/comparator.

B2 ngưỡng 0.5 giữ nguyên, không đổi để sửa capacity. Cần trình cấu hình LR cụ thể cùng encoder/scaler/imputer, handling category lạ và calibration trước task baseline; không tự dùng mọi default thư viện làm protocol đã được duyệt. Baseline vi phạm được ghi infeasible, vẫn báo cost/metrics đầy đủ và tách khỏi xếp hạng feasible.

## 7. Thuật toán, search space và budget — A4

**Đã phê duyệt:** Random Forest, tối ưu x=(h,τ), Optuna TPE, ngân sách ban đầu **30 trials**, seed chính **42**. Random Search cùng ngân sách làm đối chứng **nếu đủ thời gian**; đánh giá ổn định **5 seeds nếu khả thi**. Hai phần tùy điều kiện không được báo là đã thực hiện hoặc tự tăng budget khi thiếu kế hoạch.

**Miền H đề xuất để chủ dự án duyệt trước tối ưu**, chưa phải cấu hình chạy:

| Hyperparameter | Miền categorical đề xuất | Lý do thiết kế |
|---|---|---|
| `n_estimators` | `{100,200,300}` | Ba mức số cây, giữ quy mô tìm kiếm vừa phải |
| `max_depth` | `{5,10,20,None}` | So sánh cây bị giới hạn và không giới hạn độ sâu |
| `min_samples_leaf` | `{1,2,5,10}` | Điều chỉnh độ chi tiết của lá |
| `max_features` | `{"sqrt",0.75,1.0}` | Từ chọn ít feature đến toàn bộ; áp dụng trên feature sau encoding |

Có 144 tổ hợp danh nghĩa; không khẳng định chúng khác nhau hoàn toàn hoặc đủ để tìm optimum. TPE chọn h trong miền này, τ dự kiến quét theo §5. Các kiểu giá trị đối chiếu [RandomForestClassifier chính thức](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html); miền cụ thể là đề xuất của Codex, không phải kết luận của tài liệu hay kết quả tuning.

Đề xuất giữ cố định ngoài H: `criterion="gini"`, `bootstrap=True`, `class_weight=None`, `min_samples_split=2`, `oob_score=False`, `max_samples=None`, random_state theo model seed và không sample weighting. Chưa duyệt các lựa chọn cố định này; trước chạy phải khóa toàn bộ params của phiên bản thư viện cùng pipeline/calibration, không chỉ bốn tham số search.

**Các quy tắc còn chờ chốt:**

- Đề xuất 30 trials là 30 attempts h cho mỗi study/seed, mỗi h dùng cùng quy tắc threshold; tính cả failed/pruned/infeasible vào attempts, không tự thay bằng 30 lượt thành công. Ghi số fit thực, số threshold/vector a chấm và thời gian fit/search/tổng. Chưa có quyết định cụ thể về đơn vị trial, retry/pruning hoặc runtime cap.
- Nếu chạy Random Search, đề xuất cùng H, 30 attempts, threshold routine, calibration, seed schedule và quy tắc dừng. Số threshold phụ thuộc p nên bằng trials không có nghĩa bằng wall-clock. Điều kiện “đủ thời gian” cần quyết định trước khi xem kết quả, không chọn có/không theo phương pháp thắng.
- Seed chính 42 đã duyệt; đề xuất năm seed `{42,43,44,45,46}` cho model/optimizer, giữ split seed 42, trường seed tách vai trò. Danh sách bổ sung, 30 trials mỗi seed và tổng ngân sách nhiều seed còn cần duyệt; không coi “5 seeds nếu khả thi” là quyền tự mở 150 trials/phương pháp.
- Quy tắc hòa cost, τ-only ablation, runtime cap và phiên bản dependencies chưa được khóa. Không mở tuning/test ở nhiệm vụ tài liệu.

## 8. Metrics và edge cases — A6

**Đã phê duyệt:** chính gồm `total_cost`, `cost_per_observation`, `maintenance_rate`, `feasible`, `constraint_violation`; phụ gồm Recall, Precision, F1, PR-AUC, ROC-AUC, Brier score và runtime. Số action/N và TP/FP/FN/TN được ghi để kiểm chứng các tỷ lệ/cost. Mọi phương pháp dùng cùng công thức/đơn vị và constraint.

**Chi tiết metric trình duyệt:**

| Nội dung | Quy ước đề xuất, chưa được chốt |
|---|---|
| PR-AUC | Chọn `average_precision` (AP) có tên rõ, phân biệt diện tích PR hình thang |
| Action metrics | Tính confusion matrix bằng a; probability metrics dùng p |
| Recall P=0; precision M=0 | null kèm reason, không tự ép 0/1 |
| F1 | `2TP/(2TP+FP+FN)`; null chỉ khi mẫu số 0 |
| ROC-AUC một lớp; AP không positive | null kèm reason |
| B0/B1 không có mô hình p | AUC/AP/Brier=null với reason, không dựng p giả |
| Cost trung bình/rate khi N=0 | Reject batch như §5 |
| Saving | Tuyệt đối `C_B0-C_policy` có thể âm; tỷ lệ null nếu C_B0=0 |
| Brier/calibration | Brier dùng p và y; không dùng riêng Brier để khẳng định calibration tốt |

Định nghĩa AP và nguyên tắc calibration tham khảo [AP scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [calibration scikit-learn](https://scikit-learn.org/stable/modules/calibration.html). Cần duyệt wrapper xử lý null/reasons thay vì để default thư viện khác nhau giữa phương pháp. Không sửa tên PR-AUC thành AP đã khóa khi chủ dự án chưa chọn estimator.

## 9. Protocol và điều kiện dữ liệu — A5

**Đã phê duyệt:** AI4I UCI, target/features §2; stratified train/validation/test **60/20/20, seed 42 sau kiểm tra phụ thuộc dữ liệu**; fit preprocessing chỉ trên train; calibration dùng train folds; không dùng test để tuning; khóa mô hình/policy trước đánh giá test cuối.

Thứ tự và các điểm cần chốt:

1. Trong W1-G2-A, Antigravity kiểm tra nguồn/schema, provenance, hash CSV, thiếu/trùng và phụ thuộc quan sát theo phạm vi được giao. Chưa có CSV/hash/split được kiểm chứng trong lượt Codex này. Không ghi đè raw hoặc split của AI kia.
2. Cần xác định kiểm tra integrity toàn dữ liệu ở mức đủ tạo split và giữ test kín; EDA để chọn feature/mô hình chỉ train/validation. Trình cách xử lý duplicate/nhóm/thứ tự trước split; không tự loại dòng/outlier hay suy ra thời gian từ UID. Kiểm tra phụ thuộc phải có bằng chứng trước dùng random split. Nếu phát hiện điều kiện không đạt hoặc mâu thuẫn với random split đã chọn, báo chủ dự án để quyết định protocol thay thế, không tự đổi split.
3. Khi task pipeline được giao và điều kiện đạt, tạo một split đã duyệt, lưu IDs/hash và dùng chung mọi phương pháp. Tách split/model/optimizer/fold seed; không thử nhiều split để chọn kết quả tốt. Đề xuất multi-seed giữ split cố định, không trộn thay split với thay model seed.
4. Fit encoder/imputer/scaler/feature selection chỉ trên train. Trong calibration CV, mỗi fold fit preprocessing/model bằng train-fold tương ứng và calibrator dùng dự đoán ngoài fold thuộc train; không fit calibrator trên validation/test.
5. Chủ dự án chưa chốt có/không calibration, method/folds/seed hoặc xử lý quá ít positives. Đề xuất sigmoid với 5 stratified train folds, fold seed 42, chỉ khi mỗi lớp đủ cho folds; nếu không đủ thì báo lại, không tự thay method/folds. Có/không calibration và ablation cần chốt trước chạy; đây không phải phần mặc nhiên được duyệt bởi câu “calibration dùng train folds”.
6. Chọn h/τ bằng validation theo objective và budget đã khóa. Best validation cost là development estimate có thiên lệch lựa chọn. Không dùng test chọn threshold/hyperparameter/preprocessing/calibration/feature/algorithm/scenario/seed.
7. Chỉ chạy các phần sau khi task tương ứng được kích hoạt và chi tiết phê duyệt đủ. Lưu code commit, dependency/Python versions, dataset/split hash, config/hash, seeds, lệnh, params/threshold, cost, feasibility/violations, null reasons, runtime, status và best-so-far feasible. Giữ failed/pruned/infeasible, không làm đẹp log.
8. Sensitivity/multi-seed/ablation chỉ dùng development data, đăng ký kế hoạch và budget trước; phân biệt chấm policy cố định và tối ưu lại. Không tự chạy do roadmap nêu tuần tương ứng.
9. Trước test cuối khóa model đã fit, policy, scenario và protocol; cần quyền đánh giá test cuối riêng theo AGENTS. Review đề xuất không refit train+validation ở lượt test đầu; refit policy chưa được chốt. Báo cả vi phạm/không cải thiện, không mở lại tuning sau test. Tái lập chỉ xác minh cấu hình đã khóa.

Sơ đồ roadmap có tiền xử lý trước split không cho phép fit toàn dữ liệu: phân biệt kiểm tra schema với fit transformer. Đây là yêu cầu chống leakage, không phải quyền sửa roadmap hoặc task board ở lượt này.

## 10. Bảng đối chiếu A1–A7

Các quyết định dưới đây đối chiếu với **câu trả lời phê duyệt chi tiết ngày 2026-10-21 trong cùng chat**, thay thế tình trạng thiếu giá trị khi chỉ có commit đổi nhãn. Không yêu cầu chủ dự án xác nhận lại những giá trị đã cung cấp.

| ID | Phần đã được chủ dự án phê duyệt | Chi tiết còn chờ duyệt/điều kiện | Trạng thái toàn mục |
|---|---|---|---|
| A1 | Một dòng=một quan sát, mô hình cost một kỳ, cost units, không phải VND (§1) | Không thiếu quyết định trong phạm vi mô hình hiện tại | Đã phê duyệt |
| A2 | Objective nguồn; C_PM=1, C_F=20, η=0.8; sensitivity C_F={5,10,20,40}, η={0.7,0.8,1.0}; giả định nghiên cứu (§4) | Thiết kế sensitivity: tích tổ hợp/từng yếu tố, fixed-policy/reoptimization và phạm vi giữ C_PM/b | Phê duyệt một phần |
| A3 | b=0.10, M<=floor(b*N); recall chỉ là metric; B0 riêng; ties nguyên nhóm; không top-k; vi phạm=infeasible; kiểm tra τ/p=0/1 (§5) | Candidate thresholds, N=0/P=0, schema violation, no-feasible và hòa cost chi tiết | Phê duyệt một phần |
| A4 | h+τ, RF, TPE, 30 trials, seed chính 42; RS cùng budget/5 seeds theo điều kiện (§7) | Miền bốn hyperparameter, params cố định, đơn vị trial, seeds bổ sung, runtime/điều kiện phần mở rộng | Phê duyệt một phần |
| A5 | AI4I UCI, sáu feature, loại ID/nhãn phụ; stratified 60/20/20 seed42 sau kiểm tra phụ thuộc; train-only fit, train-fold calibration; test khóa (§2/§9) | Bằng chứng phụ thuộc trước split; duplicate/EDA policy; calibration on/off/method/folds; refit policy; quyền test cuối riêng | Phê duyệt một phần |
| A6 | B0/B1/B2/P, B2 τ=0.5, metrics chính/phụ; baseline vi phạm=infeasible (§6/§8) | B1 w/comparator; LR/pipeline/calibration; PR-AUC estimator và zero-denominator/undefined rules | Phê duyệt một phần |
| A7 | Chỉ W1-G1-C (Codex) và W1-G2-A (Antigravity); lượt này cho phép cập nhật spec và tạo PR (§0) | Các giai đoạn tiếp theo, thay đổi file chung khác, merge/tích hợp và test cuối vẫn chờ chỉ dẫn | Đã phê duyệt |

Trạng thái A7 chỉ áp dụng hai task được nêu, không phê duyệt toàn tuần/lộ trình. W1-G1-A/proposal và các task G3–G10 chưa được kích hoạt bằng quyết định này. Không tự gửi prompt hay khởi chạy Antigravity; chủ dự án điều phối W1-G2-A. Các mục mới đề xuất ở §4–§9 phải được duyệt trước task chạy tương ứng; trạng thái từng giá trị đã phê duyệt không bị mất chỉ vì toàn mục còn chi tiết.

Mẫu quyết định bổ sung: `A<ID>; chấp nhận/điều chỉnh đề xuất §...; giá trị/quy tắc; phạm vi; ngày; tham chiếu phiên bản`. Không tự đánh dấu Done hoặc sửa task board. Quyết định mới trong chat có giá trị hơn nhãn bootstrap/prompt cũ, nhưng không mở scope ngoài nội dung đã được giao.

## 11. Deliverables và cổng nghiệm thu

- Tuần 1 / G1–đầu G2: W1-G1-C đã bàn giao review; chủ dự án đã cho phép W1-G2-A kiểm tra dữ liệu, chưa tự xác nhận kết quả/Done. Bản review lịch sử được giữ nguyên. Đề cương/proposal và pipeline của Antigravity cần giao riêng nếu chưa được kích hoạt.
- Tuần 2 / G2–G4: pipeline/split cần task riêng và A5/điều kiện dữ liệu đạt. Cost/constraints tối thiểu cùng unit tests phải đạt trước báo baseline cost G4 sau khi quy tắc A1–A3/A6 đủ; không chờ tới G6 mới chấm cost. B2 cần fit LR tối thiểu trong G4 khi được giao, dù phần ML đầy đủ ở G5.
- Tuần 3 / G5–G7: ML/calibration, hoàn thiện cost/tests và optimization chỉ sau khi task được giao, miền H/quy tắc/budget đủ phê duyệt. 30 trials là mức ban đầu được chọn, không phải lệnh chạy ngay.
- Tuần 4 / G8: so sánh, sensitivity, stability/ablation và ít nhất hai hình từ log thật; kế hoạch chi tiết cùng budget được duyệt trước chạy.
- Tuần 5 / G9–G10: khóa nghiệm, test cuối sau cho phép riêng, báo cáo 8–12 trang, 5–8 slides/demo, reproduce và phát hành do chủ dự án quyết định.

Giấy phép mã nguồn chưa được chọn; không tự tạo LICENSE. CC BY 4.0 của dataset không quyết định license cho code. Không commit raw data, secrets hoặc artifact lớn; kiểm tra staged diff trước commit.

PR này chỉ sửa `docs/PROJECT_SPEC.md` trên nhánh `codex/reconcile-project-spec-approvals`, base main; không sửa main trực tiếp, roadmap, board, config, source/tests hoặc hai bản review. Không merge/rebase tích hợp, force-push, train, baseline, tối ưu, đọc test để tuning hay tạo kết quả thực nghiệm giả. Bootstrap và việc phê duyệt ngữ nghĩa không tự hoàn tất checkpoint học thuật W1.
