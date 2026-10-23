# PROJECT SPEC — quyết định đã phê duyệt và chi tiết chờ chốt

Ngày cập nhật: **2026-10-23 (Asia/Saigon)**. Đồ án cá nhân, 5 tuần, 10 giai đoạn theo `ROADMAP.md`. Lượt hiện tại ghi nhận phê duyệt A3-a–g/A6-a–g trong đúng hai tài liệu được giao. **G3 đã nghiệm thu/merge PR #8; G4 chưa triển khai và chờ giao riêng.** Nội dung lịch sử A5/G3 bên dưới phản ánh thời điểm ghi nhận trước đây, không thay đổi quyết định A5.

## 0. Bằng chứng phê duyệt và phạm vi

**Phê duyệt chính thức ngày 2026-10-23 (Asia/Saigon):** chủ dự án gửi trong chat “PHÊ DUYỆT CHÍNH THỨC A3 VÀ A6 – CHUẨN BỊ GIAI ĐOẠN 4”, xác nhận PR #9 đã merge và phê duyệt nguyên văn A3-a–g/A6-a–g, bao gồm tham số, điều kiện dừng và ngoại lệ. Nguồn chuẩn chi tiết: [bảng gốc PR #9 tại commit 8a0f95a](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/blob/8a0f95aa4e0cc6176af12cb512315f440f1ef034/docs/TASK_BOARD.md); merge SHA `5459d78b17857b6a5562ac0e75ab5357f6e8d33b` đã xác minh trên origin/main. Quyền nhiệm vụ này chỉ sửa `docs/PROJECT_SPEC.md` và `docs/TASK_BOARD.md`, tạo branch/commit/push/PR riêng và báo cáo Issue #2. **“Đây là nhiệm vụ ghi nhận phê duyệt A3/A6, chưa phải lệnh triển khai W2-G4-C.”** Không sửa A1/A2/A4/A5 hoặc các quyết định khác; không tự merge. G3 đã nghiệm thu/merge qua PR #8; G4 chưa thực hiện và cần giao riêng sau khi PR ghi nhận này được merge.

Các câu lịch sử còn ghi threshold/B2/calibration/metrics A3/A6 “chưa chốt” được thay thế bởi quyết định hiện hành ở §5/§6/§8 và hàng A3/A6 tại §10. Phần A1/A2/A4/A5 và các quyết định khác giữ nguyên; chi tiết A4 chưa duyệt vẫn chờ task tương ứng.

**Ghi nhận lịch sử A5 ngày 2026-10-23 (PR #7):** chủ dự án gửi văn bản “PHÊ DUYỆT CHÍNH THỨC A5 – DATASET VÀ EXPERIMENTAL PROTOCOL”, căn cứ review đã merge qua [PR #6](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/6). Tệp chỉ dẫn `Văn bản đã dán.txt`, attachment `28ca3964-7860-4589-8d6c-ad9b1f10f831`, SHA-256 `5e9e9602543d1599477077b2e909f864d09791914b0665abef427b59d1f9c51b`, là bằng chứng cho A5.1–A5.7 ở §9. Chủ dự án cho phép sửa riêng `docs/PROJECT_SPEC.md`, `docs/experimental_protocol.md`, `docs/TASK_BOARD.md`; tạo branch/commit/push/PR và báo cáo Issue #2. Không sửa quyết định A1–A4/A6 đã có hoặc sản phẩm Antigravity; không tự merge.

Chỉ dẫn ghi rõ: **“Đây là lệnh phê duyệt và ghi nhận A5, chưa phải lệnh triển khai W2-G3-C.”** Sau khi PR ghi nhận A5 được merge, chủ dự án sẽ giao riêng G3 và quyền config/metadata. A5 được phê duyệt về quy tắc không có nghĩa duplicate/phụ thuộc đã kiểm tra đạt, split đã tạo hoặc Test đã được phép đánh giá.

Các gạch đầu dòng tiếp theo lưu bằng chứng lịch sử ngày 2026-10-21; các câu về “lượt hiện tại”, file untracked và PR chỉ sửa spec phản ánh lúc viết. Hai bản review đã được tích hợp qua PR #3; checkpoint/review A5 qua PR #6, merge commit `8529fe4a428d221badee86aeb6e03170b274cc6f`. Phần A5 tương ứng được cập nhật bởi quyết định mới; nội dung A1–A4/A6 bên dưới giữ nguyên.

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

Theo A5.1–A5.4 ngày 2026-10-23 (§9), tiếp tục AI4I cho đánh giá nội suy và công khai exposure do EDA ban đầu đã khảo sát toàn bộ nhãn. Không dùng nhãn/kết quả Test cho lựa chọn phát triển từ thời điểm khóa giao thức; không gọi holdout tương lai là hoàn toàn chưa từng bị xem xét. Quy tắc duplicate và thứ tự split đã được phê duyệt, nhưng audit sáu features/rà soát phụ thuộc và việc chia tập chưa được thực thi trong nhiệm vụ ghi nhận này. Không ghi kiểm tra dữ liệu là đã chạy chỉ từ metadata.

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

**A3-a đến A3-g đã phê duyệt đầy đủ** theo §0; bảng dưới sao nguyên văn nội dung/giải thích từ PR #9. Đây là quy tắc đã chốt, chưa có code/kiểm thử cost/constraints hoặc kết quả G4. M=Σa, P=Σy, TP=Σay; không có trọng số mẫu.

| Quyết định A3 | Quy tắc đã phê duyệt | Lý do/phạm vi từ bảng gốc |
|---|---|---|
| A3-a Candidate thresholds | Với mỗi h, trên Validation: T={0,1}∪unique(p), sort/deduplicate exact, không rounding; quét mỗi candidate, dùng `>=`; khóa τ trước Test | Bao phủ các action vectors biểu diễn được trong [0,1]; không grid tùy ý hoặc τ>1; B0 vẫn riêng |
| A3-b N=0 / input sai | Reject evaluation N=0; shape sai, nhãn/actions không binary, p không finite/ngoài [0,1], cost/domain sai đều ERROR với reason; không repair/clip hay gán feasible=false cho lỗi input | Phân biệt lỗi với policy capacity-infeasible; không chia 0 |
| A3-c P=0 | Cost, M/K và feasibility vẫn tính bình thường; Recall=null, reason=NO_POSITIVES; áp dụng bảng A6 về metrics khác | Không biến recall thành constraint; không loại batch khỏi cost |
| A3-d Ties | Giữ nhóm exact bằng nhau, không tolerance trên p, không tách nhóm/top-k. τ=0 chọn tất cả; τ=1 vẫn chọn p=1 | Comparator/domain/ties đã duyệt; chỉ làm rõ cách so sánh số và biên |
| A3-e Capacity violation | K=floor(N/10) bằng số nguyên cho b=0.10; excess=max(0,M-K), excess_rate=excess/N; feasible iff excess=0; log cả M,K,excess và rate | Không sai số float ở floor; không penalty tùy ý, không sửa action |
| A3-f No-feasible | best=null, status=NO_FEASIBLE_CANDIDATE; log số candidates và phạm vi h đã xét. h riêng có count(p=1)>K không có τ feasible; không suy ra toàn H vô nghiệm; B0 báo riêng | Không âm thầm mở domain hoặc thay bằng B0 trong kết quả P |
| A3-g Tie-break | Chọn feasible trước; minimum observed cost trên Validation, rồi M nhỏ hơn, rồi τ lớn hơn trong cùng h, cuối cùng thứ tự h cố định đăng ký trước search (không theo arrival). Hòa cost iff chênh tuyệt đối ≤1e-9 cost units so với minimum toàn bộ, không gom dây chuyền | Tái lập, ưu tiên ít hành động; không dùng Test/metric phụ chọn thắng. Thứ tự H cần khóa khi A4 được chốt |

Không tự đổi `>=` sang `>`, thêm τ>1 hoặc mở rộng miền policy. Đây là những thay đổi formulation cần quyết định mới.

## 6. Baseline và cấu hình đã phê duyệt — A6

**A6-a đến A6-g đã phê duyệt đầy đủ** theo §0, đúng bảng gốc PR #9 bên dưới. B0 reactive: mọi a=0; B1 fixed wear rule; B2 Logistic Regression với τ=0.5; P Random Forest tối ưu h/τ. Dùng cùng cost/capacity và các quy tắc chấm, giữ baseline infeasible. Miền H/thuật toán/budget còn thiếu thuộc A4, không được phê duyệt thêm ở đây. Preprocessing áp dụng A5.5 đã duyệt; RF calibration vẫn theo A5.6 tại G5. Chưa fit model/calibrator hoặc chạy baseline.

| Quyết định A6 | Quy tắc đã phê duyệt | Lý do/công bằng từ bảng gốc |
|---|---|---|
| A6-a B1 | `a=1[Tool wear [min]>=200]`, w=200 phút, cố định trước run; không fit/tune w | Heuristic đã nêu trong spec, chưa có chứng cứ hiệu quả; không dựa vào Test hoặc sửa ngưỡng để feasible |
| A6-b B2 LR | L2, C=1.0, solver=lbfgs, l1_ratio=0.0 (API1.9.1; không truyền penalty deprecated), dual=False, fit_intercept=True, tol=1e-4, max_iter=2000, class_weight=None, random_state=42, warm_start=False, verbose=0; n_jobs=None/intercept_scaling=1 là tham số API không tác dụng với lbfgs. Không sample_weight/CV/tuning; score=predict_proba lớp1, a=1[p>=0.5] | Một baseline cấu hình cố định; preprocessing A5.5 đã duyệt, chỉ fit Train. Seed ghi metadata dù lbfgs không dùng seed. ConvergenceWarning/nonfinite => FAILED, giữ log và xin quyết định, không tự retry solver/C |
| A6-c Calibration B2 | Không post-calibration; dùng xác suất LR trực tiếp; không fit calibrator hoặc refit Train+Val | Giữ baseline đơn giản, không chọn calibration bằng Validation/Test. RF sigmoid theo A5.6 vẫn áp dụng cho P tại G5; so sánh phản ánh toàn phương pháp, không quy hết lợi ích cho optimizer |
| A6-d PR-AUC estimator | Báo tên `average_precision` (AP non-interpolated), sklearn.average_precision_score(y,p,pos_label=1), không trapezoidal AUC; ROC-AUC từ cùng p. B2/P dùng score liên tục, không dùng actions; B0/B1 ranking/probability metrics=null reason=NO_PROBABILITY_MODEL | AP khác trapezoid PR area. B0/B1 chỉ là policy nên không bịa probability; vẫn báo đủ cost/action metrics cho cả bốn |
| A6-e Undefined metrics | Precision=TP/M nếu M>0, ngược lại null/NO_PREDICTED_POSITIVES; Recall=TP/P nếu P>0, ngược lại null/NO_POSITIVES; F1=2TP/(P+M) nếu P+M>0, ngược lại null/NO_TRUE_OR_PREDICTED_POSITIVES. ROC-AUC=null/SINGLE_CLASS nếu P=0 hoặc P=N; AP=null/NO_POSITIVES nếu P=0, AP=1 nếu P=N và có score hợp lệ. Brier=mean((p-y)^2) cho B2/P, vẫn hợp lệ nếu một lớp | Tính công thức rõ thay vì mặc định warning/0. F1=0 khi chỉ P hoặc M bằng0; null ghi JSON null, kèm reason, không thay bằng0 khi tổng hợp |
| A6-f Mẫu số saving=0 | Báo cost, cost/N và absolute saving=C_B0-C; saving_pct=null/ZERO_REFERENCE_COST nếu C_B0=0 | P=0 không thể báo % tiết kiệm có nghĩa; absolute saving có thể âm |
| A6-g Baseline infeasible | Giữ nguyên B1/B2 actions/τ, báo cost, classification metrics và excess như mọi policy; tách feasible ranking, không chọn best feasible từ chúng. B0 riêng luôn capacity-feasible khi N>0; nếu P không feasible thì báo tình trạng đó cạnh B0 | Không sửa baseline bằng top-k/retune; infeasible có thể cost thấp nhưng không là nghiệm đạt constraint |

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

**Chi tiết metric đã phê duyệt:** áp dụng nguyên văn A6-d/A6-e/A6-f/A6-g ở §6, bao gồm tên `average_precision`, công thức, các ca một lớp/zero denominator, JSON null kèm reason và xử lý infeasible. Action metrics dùng confusion matrix từ a; probability/ranking metrics dùng p, không dựng p giả cho B0/B1. N=0 bị từ chối theo A3-b; không thay undefined bằng default 0/1 của thư viện. Brier không tự chứng minh calibration tốt.

Các quy tắc metric này đã được chủ dự án chốt, chưa được triển khai/kiểm thử trong G4. Phê duyệt không cấp quyền mở Test; cổng G10 ở A5 giữ nguyên.

## 9. Protocol và điều kiện dữ liệu — A5

**Trạng thái: ĐÃ PHÊ DUYỆT A5.1–A5.7 về quy tắc, ngày 2026-10-23**, theo văn bản chủ dự án ở §0. Chi tiết áp dụng và giới hạn tại [experimental_protocol.md](experimental_protocol.md). Đây là ghi nhận quyết định, không là bằng chứng đã chạy kiểm tra/triển khai. B2 vẫn phải chốt cấu hình riêng trong A6 trước G4; quyền thực thi G3, config/metadata và quyền Test cuối được giao riêng.

### A5.1 — Mục tiêu đánh giá và phụ thuộc

Giữ UCI AI4I 2020 và Stratified Random Split cho **nội suy trên cùng dữ liệu tổng hợp**. Không tuyên bố dự báo theo thời gian, tổng quát hóa sang máy/nhà máy mới hoặc hiệu quả bảo trì thực tế. Ghi nhận phụ thuộc giữa các quan sát theo UDI và biến nhiệt độ; kiểm tra cấu trúc phụ thuộc, báo cáo giới hạn, không giả định các quan sát hoàn toàn độc lập. UDI chưa được xác nhận là timestamp hay machine ID.

### A5.2 — Data exposure

Chấp nhận tiếp tục AI4I dù EDA ban đầu đã khảo sát **toàn bộ nhãn**; công khai giới hạn này trong tài liệu phương pháp luận và báo cáo cuối. Từ thời điểm khóa giao thức, không dùng nhãn hoặc kết quả Test để chọn features, thuật toán, hyperparameters, threshold, calibration hoặc thay đổi phương án chia dữ liệu. Không tuyên bố holdout tương lai hoàn toàn chưa từng bị xem xét; chia lại không xóa exposure. Các quy tắc cấm dùng Test chọn scenario/seed ở phần khác của spec vẫn giữ nguyên.

### A5.3 — Exact duplicate trên sáu features

Kiểm tra exact duplicates trên **đúng sáu features ở §2**, không dùng target hoặc năm nhãn phụ làm khóa nhóm. Giữ nguyên raw và nhãn gốc UCI. Nếu có quan sát trùng sáu features: **dừng trước split chính thức**, báo số lượng và đề xuất group-disjoint để chủ dự án phê duyệt riêng. Không tự xóa dữ liệu, đổi tỷ lệ hoặc chọn seed khác. Quy tắc xử lý đã duyệt; chưa có kết quả audit sáu X mới trong nhiệm vụ này.

### A5.4 — Split cố định và metadata

Phê duyệt phân tầng theo `Machine failure`, `random_state=42`, trình tự cố định:

1. Giữ thứ tự dữ liệu nguồn theo UDI để tái lập.
2. Tách **Test 20% trước**, stratify theo target với `random_state=42`.
3. Từ **80% còn lại**, lấy **Validation 25%** của phần đó (20% toàn dataset), stratify theo target với `random_state=42`.
4. Train chiếm **60% toàn dataset**.
5. Lưu dataset hash, split IDs/hash, seed, thuật toán, phiên bản thư viện và metadata tái lập; dùng cùng split cho các phương pháp.

Không thử nhiều seed/split để chọn kết quả tốt hoặc phân bố nhãn phụ thuận lợi. **Trước thực thi split**, phải hoàn thành audit duplicate và rà soát phụ thuộc trong phạm vi được duyệt. Nếu phát hiện điều kiện bất thường đòi hỏi đổi protocol, dừng và trình lại; không tự đổi thuật toán, tỷ lệ hoặc seed. Chưa có split chính thức được tạo trong lượt ghi nhận này.

### A5.5 — Preprocessing

Chỉ sáu features đã duyệt ở §2:

- `Type`: `OneHotEncoder(handle_unknown="ignore")`.
- Logistic Regression: `StandardScaler` cho năm numeric features.
- Random Forest: giữ nguyên numeric features, không bắt buộc scaling.
- Fit preprocessing chỉ trên Train; Validation và Test chỉ transform bằng preprocessor đã fit Train. Trong CV phải giữ ranh giới từng fold theo A5.6.
- Missing bất ngờ phải báo lỗi rõ; không âm thầm impute/xử lý.
- Không tự clipping outliers, thêm feature engineering, resampling/SMOTE hoặc dùng ID/nhãn phụ làm feature.

Đây là phê duyệt quy tắc preprocessing A5; không chốt toàn bộ cấu hình baseline Logistic Regression B2 thuộc A6.

### A5.6 — Calibration Random Forest tại G5 và refit

Phê duyệt RF **sigmoid calibration**, **5 stratified train folds**, `shuffle=True`, `random_state=42`, `ensemble=False`. Fit preprocessing/model đúng ranh giới từng fold; không dùng Validation hoặc Test để fit calibrator. Không refit model trên **Train+Validation trước lần đánh giá Test đầu tiên**. Nếu dữ liệu không đáp ứng yêu cầu calibration, báo cáo và xin quyết định mới, không tự thay method/folds. Phương án này được phê duyệt cho **Giai đoạn 5**; task G5 vẫn cần giao riêng, không thực thi trong nhiệm vụ ghi nhận A5.

Cấu hình baseline LR B2, bao gồm quyết định calibration B2, **sẽ chốt riêng trong A6 trước G4**. Đề xuất “B2 không post-calibration” trong review PR #6 không được văn bản A5 này phê duyệt.

### A5.7 — Cổng Test cuối tại G10

Test chỉ được mở để đánh giá tại **Giai đoạn 10**, sau khi đã khóa:

- Model và toàn bộ preprocessing.
- Hyperparameters, threshold và policy.
- Cost scenarios và constraints.
- Seeds, dependencies, metadata và protocol.
- Có **phê duyệt riêng từ chủ dự án**.

Không đánh giá Test trong nhiệm vụ A5. Việc bộ tạo split sau này dùng target để phân tầng theo A5.4 không cấp quyền khám phá hay đánh giá Test. Không mở lại tuning bằng Test; báo cả vi phạm/không cải thiện. Tái lập chỉ xác minh cấu hình đã khóa.

Các quy tắc tái lập trước đây vẫn áp dụng: tách split/model/optimizer/fold seeds; lưu code commit, dependency/Python versions, dataset/split/config hash, lệnh, params/threshold, cost/feasibility/violations, null reasons, runtime/status; giữ failed/pruned/infeasible. Chọn h/τ trên validation theo objective/budget đã khóa; best validation cost có thiên lệch lựa chọn. Sensitivity/multi-seed/ablation chỉ development, cần kế hoạch/budget và nhiệm vụ riêng; phê duyệt A5 không kích hoạt chúng.

Sơ đồ roadmap có tiền xử lý trước split không cho phép fit toàn dữ liệu. **G3 vẫn chưa được giao**; sau khi PR ghi nhận A5 được merge, chủ dự án mới giao W2-G3-C và quyền config/metadata liên quan.

## 10. Bảng đối chiếu A1–A7

A1/A2/A4/A7 giữ nguyên theo câu trả lời phê duyệt ngày 2026-10-21; A5 giữ nguyên theo văn bản A5.1–A5.7 ngày 2026-10-23 ở §0/§9. Riêng A3/A6 được cập nhật theo phê duyệt chính thức 14 hàng PR #9 ở §0/§5/§6/§8. Không yêu cầu chủ dự án duyệt lại các giá trị đã chốt.

| ID | Phần đã được chủ dự án phê duyệt | Chi tiết còn chờ duyệt/điều kiện | Trạng thái toàn mục |
|---|---|---|---|
| A1 | Một dòng=một quan sát, mô hình cost một kỳ, cost units, không phải VND (§1) | Không thiếu quyết định trong phạm vi mô hình hiện tại | Đã phê duyệt |
| A2 | Objective nguồn; C_PM=1, C_F=20, η=0.8; sensitivity C_F={5,10,20,40}, η={0.7,0.8,1.0}; giả định nghiên cứu (§4) | Thiết kế sensitivity: tích tổ hợp/từng yếu tố, fixed-policy/reoptimization và phạm vi giữ C_PM/b | Phê duyệt một phần |
| A3 | Các quyết định A3 trước đây và A3-a–g tại §5, được phê duyệt nguyên văn từ PR #9 theo §0 | Không còn chờ chốt 7 quy tắc; thứ tự H cụ thể khóa khi A4 được chốt; triển khai/tests cần task riêng | Đã phê duyệt A3-a–g; chưa triển khai G4 |
| A4 | h+τ, RF, TPE, 30 trials, seed chính 42; RS cùng budget/5 seeds theo điều kiện (§7) | Miền bốn hyperparameter, params cố định, đơn vị trial, seeds bổ sung, runtime/điều kiện phần mở rộng | Phê duyệt một phần |
| A5 | A5.1–A5.7 (§2/§9): nội suy AI4I và công khai exposure; audit sáu X/điều kiện dừng; split Test trước 60/20/20 seed42; preprocessing; RF sigmoid 5 train folds shuffle seed42, ensemble=False; không refit Train+Val; cổng Test G10 | Quy tắc đã chốt, kiểm tra/triển khai chưa chạy. G3 và quyền config/metadata giao riêng sau merge PR này; group-disjoint nếu có duplicate cần duyệt riêng; B2 thuộc A6; Test cuối cần phê duyệt riêng | Đã phê duyệt A5.1–A5.7; chưa triển khai |
| A6 | B0/B1/B2/P và A6-a–g tại §6/§8, được phê duyệt nguyên văn từ PR #9 theo §0 | Không còn chờ B1/LR/calibration B2/AP/undefined/infeasible; thực thi G4 cần giao riêng | Đã phê duyệt A6-a–g; chưa triển khai G4 |
| A7 | Chỉ W1-G1-C (Codex) và W1-G2-A (Antigravity); lượt này cho phép cập nhật spec và tạo PR (§0) | Các giai đoạn tiếp theo, thay đổi file chung khác, merge/tích hợp và test cuối vẫn chờ chỉ dẫn | Đã phê duyệt |

Trạng thái A7 chỉ áp dụng hai task được nêu, không phê duyệt toàn tuần/lộ trình. W1-G1-A/proposal và các task G3–G10 chưa được kích hoạt bằng quyết định này. Không tự gửi prompt hay khởi chạy Antigravity; chủ dự án điều phối W1-G2-A. Các chi tiết thực sự còn chưa phê duyệt ở §4/§7 phải được chốt trước task tương ứng; A3/A6 ở §5/§6/§8 đã được phê duyệt theo §0; A5 ở §9 đã được phê duyệt bổ sung về quy tắc, vẫn cần điều kiện thực thi và nhiệm vụ riêng. Trạng thái từng giá trị đã phê duyệt không bị mất chỉ vì toàn mục còn chi tiết.

Mẫu quyết định bổ sung: `A<ID>; chấp nhận/điều chỉnh đề xuất §...; giá trị/quy tắc; phạm vi; ngày; tham chiếu phiên bản`. Không tự đánh dấu Done hoặc sửa task board. Quyết định mới trong chat có giá trị hơn nhãn bootstrap/prompt cũ, nhưng không mở scope ngoài nội dung đã được giao.

Lượt ghi nhận A5 này được chủ dự án cho phép cập nhật cổng A5/G3 trong TASK_BOARD theo §0; không thay đổi A7, không đánh dấu G3 đã thực hiện.

## 11. Deliverables và cổng nghiệm thu

- Tuần 1 / G1–đầu G2: W1-G1-C đã bàn giao review; chủ dự án đã cho phép W1-G2-A kiểm tra dữ liệu, chưa tự xác nhận kết quả/Done. Bản review lịch sử được giữ nguyên. Đề cương/proposal và pipeline của Antigravity cần giao riêng nếu chưa được kích hoạt.
- Tuần 2 / G2–G4: pipeline/split cần task riêng và A5/điều kiện dữ liệu đạt. Cost/constraints tối thiểu cùng unit tests phải đạt trước báo baseline cost G4 sau khi quy tắc A1–A3/A6 đủ; không chờ tới G6 mới chấm cost. B2 cần fit LR tối thiểu trong G4 khi được giao, dù phần ML đầy đủ ở G5.
- Tuần 3 / G5–G7: ML/calibration, hoàn thiện cost/tests và optimization chỉ sau khi task được giao, miền H/quy tắc/budget đủ phê duyệt. 30 trials là mức ban đầu được chọn, không phải lệnh chạy ngay.
- Tuần 4 / G8: so sánh, sensitivity, stability/ablation và ít nhất hai hình từ log thật; kế hoạch chi tiết cùng budget được duyệt trước chạy.
- Tuần 5 / G9–G10: khóa nghiệm, test cuối sau cho phép riêng, báo cáo 8–12 trang, 5–8 slides/demo, reproduce và phát hành do chủ dự án quyết định.

Giấy phép mã nguồn chưa được chọn; không tự tạo LICENSE. CC BY 4.0 của dataset không quyết định license cho code. Không commit raw data, secrets hoặc artifact lớn; kiểm tra staged diff trước commit.

Ghi chú PR lịch sử ngày 2026-10-21 và lượt ghi nhận A5 sau đó (không phải phạm vi nhiệm vụ hiện tại): chỉ sửa `docs/PROJECT_SPEC.md` trên nhánh `codex/reconcile-project-spec-approvals`; không sửa main trực tiếp, roadmap, board, config, source/tests hoặc hai bản review. Nhiệm vụ hiện tại ngày 2026-10-23 chỉ cập nhật ba tài liệu tại §0 trên nhánh `codex/record-a5-approval`, từ `origin/main` sau PR #6. Không merge/rebase tích hợp, force-push, tạo split, code pipeline, train, baseline, tối ưu, đánh giá Test hay tạo kết quả thực nghiệm giả. Checkpoint sản phẩm W1 đã được ghi nhận qua PR #6; phê duyệt A5 không tự hoàn tất G3.

**Phạm vi hiện hành sau ghi nhận A3/A6:** chỉ hai tài liệu ở §0; chờ chủ dự án review/merge PR ghi nhận, sau đó giao riêng W2-G4-C và quyền file/config/log/tiêu chí nghiệm thu. Không chạy baseline, train ML, code cost model, optimization hoặc Test trong nhiệm vụ này. Các đoạn ghi chú PR cũ ở trên là lịch sử, không mở thêm quyền.
