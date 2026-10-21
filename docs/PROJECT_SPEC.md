# PROJECT SPEC — đặc tả và đối chiếu quyết định phê duyệt

Ngày chuẩn bị và đối chiếu: 2026-10-21 (Asia/Saigon). Phạm vi đồ án: cá nhân, 5 tuần, 10 giai đoạn theo `ROADMAP.md`. Phạm vi lượt này: đối chiếu A1–A7, cập nhật riêng tài liệu này trên nhánh riêng và tạo Pull Request. **Không triển khai code cost model, training, baseline hoặc optimization trong nhiệm vụ này.**

### Bằng chứng và cách đọc trạng thái

- Chủ dự án đã đổi nhãn A1–A6 thành “Phê duyệt” tại commit [72b3d67526ca56e81900e301cbfcb310de916557](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/commit/72b3d67526ca56e81900e301cbfcb310de916557). Diff của commit này chỉ đổi sáu nhãn trạng thái, không bổ sung giá trị tham số hay lựa chọn giữa các phương án.
- Nguồn đối chiếu là báo cáo W1-G1-C trong chat ngày 2026-10-21 và hai bản review local `docs/problem_formulation.md` (§2–§9), `docs/cost_model_review.md` (§1–§7). Các bản này nêu khuyến nghị, trường trống và phương án chờ chọn; chưa có bản ghi điền các giá trị còn thiếu. Hai file review chưa được commit vào nhánh nguồn của PR; PR này chỉ sửa spec.
- Chỉ dẫn tiếp theo trong cùng chat cho phép sửa toàn bộ `docs/PROJECT_SPEC.md`, tạo nhánh/PR và yêu cầu không tự suy diễn những mục thiếu hoặc mâu thuẫn. Đây là bằng chứng cho phép sửa file chung ở lượt này, không cấp quyền sửa config/board hay tự tích hợp vào main.
- Việc chủ dự án đánh dấu phê duyệt được giữ trong lịch sử và ghi nhận ở §10. Một hàng chỉ có trạng thái **Đã phê duyệt** khi quyết định cụ thể đủ để chốt toàn bộ nội dung của hàng đó. Hiện A1–A6 đều còn phần thiếu; trạng thái đối chiếu là **Cần bổ sung quyết định**. Điều này không phủ nhận việc chủ dự án đã đánh dấu, nhưng không biến ô trống thành giá trị mặc định.
- Các công thức và lựa chọn có nhãn **đề xuất** dưới đây được giữ để chủ dự án hoàn thiện quyết định; không phải cấu hình được phép chạy. Các quy tắc chống leakage, phân quyền, lưu bằng chứng và không dùng test để tuning theo `AGENTS.md` vẫn bắt buộc.

## 1. Problem statement

Từ đặc trưng vận hành của mỗi quan sát, ước lượng xác suất hỏng hóc và chọn chính sách đề xuất bảo trì có tổng chi phí mô phỏng nhỏ, đáp ứng nguồn lực. Đơn vị phân tích là quan sát, không mặc nhiên là một máy độc lập hoặc một lịch bảo trì theo thời gian. Đánh giá bằng cùng dữ liệu, kịch bản và constraints cho mọi baseline/phương pháp.

**Đề xuất A1:** mỗi hàng là một trạng thái vận hành được chấm trong một kỳ giả lập; cost cộng theo hàng. Không có horizon trước lỗi, lịch bảo trì, phụ tùng hoặc constraint từng máy trong formulation này. Cần xác nhận không cộng trùng cùng một hành động/tổn thất khi các hàng liên quan cùng máy, tên đơn vị chi phí và ranh giới khoản PM/failure. Chưa đủ thông tin để khóa A1 chỉ từ nhãn phê duyệt.

## 2. Dataset và nguồn

[AI4I 2020 — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C). Theo metadata UCI kiểm tra ngày 2026-10-21: dữ liệu tổng hợp, 10.000 quan sát, 6 feature, giấy phép CC BY 4.0; metadata báo không có missing. Đây là thông tin nguồn, chưa phải kiểm tra bản CSV local.

Target dự kiến `Machine failure`. Feature dự kiến cho A5: `Type`, `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`. Xác minh tên cột thực tế khi nhiệm vụ dữ liệu được giao; không coi metadata là kiểm tra CSV. Loại target, ID `UID`/`UDI`, `Product ID` và nhãn phụ `TWF`, `HDF`, `PWF`, `OSF`, `RNF` khỏi feature. ID chỉ phục vụ truy vết/split. Xem [hướng dẫn dữ liệu](../data/README.md) để ghi provenance.

A5 còn cần xác nhận danh sách feature, cách xử lý duplicate/nhóm/thứ tự và phạm vi EDA trước khi tạo split. Đồ án không mặc nhiên chứng minh dự báo lỗi tương lai hoặc hiệu quả can thiệp ngoài đời thực.

## 3. Decision variables

**Đề xuất nguồn cho A4:** `x=(h, τ)`, trong đó `h ∈ H` là hyperparameter của pipeline mô hình, `τ ∈ [0,1]`. Với xác suất lớp lỗi `p_i(h) ∈ [0,1]` hữu hạn từ mô hình fit trên train:

```text
a_i(h, τ) = 1[p_i(h) >= τ]
```

`a_i=1` nghĩa là đề xuất bảo trì cho quan sát i. `a_i` được suy ra từ p và τ, không phải biến nhị phân được chọn độc lập bằng nhãn y. Seed/split/kịch bản là điều kiện thí nghiệm, không phải biến để chọn kết quả tốt.

Review khuyến nghị tìm đồng thời h,τ làm phương pháp chính, τ-only với h cố định làm mốc/ablation. Chủ dự án còn cần chọn phạm vi, H cụ thể và các tham số giữ cố định. Không tạo search space thực thi từ các ví dụ của roadmap. Comparator `>=` và miền `[0,1]` vẫn là công thức nguồn được giữ để đối chiếu; đề xuất xử lý candidate/ties ở §5 chưa tự trở thành quyết định đầy đủ A3/A4.

## 4. Objective function

**Công thức nguồn giữ để đối chiếu A2; chưa đủ quyết định cụ thể để triển khai:**

```text
min C_obs(h, τ) = Σ_i [C_PM * a_i + C_F * y_i * (1 - η * a_i)]
C_exp(h, τ) = Σ_i [C_PM * a_i + C_F * p_i * (1 - η * a_i)]
```

Hậu tố `obs` chỉ phân biệt cách chấm, không đổi hàm mục tiêu nguồn. `C_PM` là chi phí mỗi hành động, kể cả hành động trên hàng không lỗi; `C_F` là tổn thất mỗi sự cố; `η` là phần tổn thất giả định được tránh trên hàng lỗi được chọn. Chi phí PM cộng phần tổn thất còn lại, cùng đơn vị chi phí mô phỏng: `y=1,a=1` tốn `C_PM+(1-η)*C_F`. Cần xác nhận ranh giới hai khoản để tránh cộng trùng; η không đổi nhãn y sau can thiệp.

| Tham số A1/A2 | Miền đề xuất | Giá trị/quyết định cụ thể hiện có |
|---|---|---|
| `C_PM` | Hữu hạn, `>=0` | Chưa cung cấp |
| `C_F` | Hữu hạn, `>=0` | Chưa cung cấp |
| `η` | Hữu hạn, `[0,1]` | Chưa cung cấp |
| Đơn vị chi phí | Cùng đơn vị cho PM, failure và tổng cost | Chưa đặt tên; không tự chọn VND hoặc đơn vị chuẩn hóa |
| Kịch bản chính/sensitivity | Liệt kê mỗi bộ tham số và cách đánh giá | Chưa có bảng giá trị hoặc lựa chọn fixed-policy/reoptimization |

Dùng `y_i` của validation để chấm/chọn chính sách theo objective nguồn; không dùng nhãn test khi tìm kiếm. `C_obs` vẫn là cost mô phỏng dù dùng nhãn quan sát. Review khuyến nghị `C_exp` chỉ là chẩn đoán theo mô hình xác suất, không tráo thành objective hoặc bằng chứng can thiệp; chủ dự án cần xác nhận lựa chọn này cùng A2. Việc so sánh h bằng C_exp có thể bị ảnh hưởng bởi xác suất dự đoán thấp, không chứng minh policy tốt.

Đẳng thức kiểm tra bằng ký hiệu: với `M=Σa_i`, `P=Σy_i`, `TP=Σy_i*a_i`, có `C_obs=C_PM*M+C_F*P-η*C_F*TP`. B0 tốn `C_F*P`; saving mô phỏng so B0 là `η*C_F*TP-C_PM*M`, có thể âm. Đây là suy diễn công thức, không phải kết quả thực nghiệm.

**AI4I không cung cấp chi phí bảo trì thực tế hoặc kết quả phản thực tế sau can thiệp. Toàn bộ `C_PM`, `C_F`, `η`, đơn vị tiền và số tiết kiệm là mô phỏng. Không đặt giá trị kinh tế mặc định trong code/config khi chưa duyệt.** Ví dụ tiền trong lộ trình không được tự chuyển thành cấu hình chạy.

## 5. Constraints và quyết định còn thiếu — A3

Đề xuất giới hạn năng lực `M=Σ a_i <= K=floor(b*N)`, `b ∈ [0,1]`, N là số hàng trong batch/tập đang chấm. **Chưa có b cụ thể.** Con số 10% trong roadmap là ví dụ, không phải cấu hình được chọn. Đây là capacity số hành động, không phải constraint tiền.

Review khuyến nghị vòng đầu chỉ dùng capacity và báo recall như metric. **Chưa có quyết định cụ thể bật/tắt recall constraint.** Nếu chọn bật `recall>=R_min`, cần chọn `R_min∈[0,1]`, định nghĩa recall bằng TP/P khi P>0 và kiểm tra khả thi. `K<ceil(R_min*P)` là điều kiện đủ để kết luận không khả thi; K đủ lớn chưa đảm bảo một threshold đạt được do thứ hạng/ties. Không tự đặt recall_min=0 để giả lập việc tắt constraint.

Phải định nghĩa `feasible`, lượng vi phạm và lý do; nghiệm vi phạm không được báo là nghiệm tốt nhất khả thi. Không thêm penalty, top-k, tie-breaking hay constraint tiền tệ thay constraint số lượng mà chưa duyệt. Recall khi không có positive phải được quy định, không tự ép thành một giá trị đẹp.

Các quy ước review đề xuất để chủ dự án xác nhận:

| Nội dung | Đề xuất chờ quyết định cụ thể |
|---|---|
| Tập ngưỡng cho h cố định | `T(p)={0,1} ∪ unique(p_i)`; đủ các vector a biểu diễn được bởi comparator/miền nguồn |
| Ties tại threshold | Giữ nguyên nhóm theo `>=`; không chia nhóm để lấp capacity |
| N nhỏ và capacity | Dùng floor chính xác; b*N<1 cho K=0; không cộng floor của các batch con thay floor toàn batch |
| N=0 hoặc input không hợp lệ | Từ chối evaluation, ghi lỗi input; không gọi là policy infeasible |
| P=0 | Recall=null kèm lý do; nếu hard recall bật thì `UNDEFINED_CONSTRAINT`, feasible=false |
| Lượng vi phạm | `capacity_excess=max(0,M-K)` và rate `/N`; `recall_shortfall=max(0,R_min-recall)` nếu bật và xác định; không cộng khác đơn vị |
| Không tìm được candidate khả thi | Best=null, `NO_FEASIBLE_CANDIDATE` kèm phạm vi h đã thử; không khẳng định toàn H vô nghiệm |
| Hòa cost | Ưu tiên M nhỏ hơn, rồi τ lớn hơn trong cùng h, rồi thứ tự h đăng ký trước; cần A4 xác nhận |

Điểm biên: với `p_i >= τ`, `τ=0` chọn mọi hàng kể cả p=0; `τ=1` vẫn chọn các hàng p=1, nên không luôn biểu diễn chính sách không bảo trì. Review khuyến nghị giữ B0 là policy riêng ngoài miền `(h,τ)`; lựa chọn mở rộng miền bằng nhánh no-maintenance vẫn cần quyết định riêng. Nếu `count(p=1)>K`, h cố định đó không có ngưỡng capacity-feasible. Không tự đổi `>=` thành `>` hoặc thêm `τ>1`.

Formulation một kỳ ở §1 không khẳng định nhãn phản ánh kết quả thực tế sau hành động. Threshold khả thi trên validation có thể vi phạm capacity trên test/dữ liệu mới; phải báo nguyên trạng, không sửa threshold bằng test. Nếu cần policy bảo đảm capacity từng batch, phải trình formulation mới trước khi triển khai.

## 6. Baseline — A6 còn cần quyết định cụ thể

| Mã | Đề xuất | Điều kiện đánh giá |
|---|---|---|
| B0 | Reactive, mọi `a_i=0` | Policy riêng, cùng cost function |
| B1 | Quy tắc ngưỡng `Tool wear` | Chưa chọn comparator, w cố định hay cách chọn w trên development data |
| B2 | Logistic Regression, ngưỡng 0.5 | Báo cả feasibility, không miễn constraint |
| P | Random Forest + tối ưu `h, τ` | Cùng split và giả định với baseline |

Baseline vi phạm phải được đánh dấu; không âm thầm dùng top-k để làm khả thi. Ngưỡng wear, cách giới hạn hành động và mọi điều chỉnh baseline cần được duyệt trước thực nghiệm.

Review đề xuất B1 dùng `Tool wear>=w`, w có đơn vị phút, candidate từ các mức wear train cộng policy all/none riêng, chọn bằng observed cost/capacity trên validation. Đây là khuyến nghị chưa được xác nhận cụ thể; không tự coi comparator/candidate đã khóa. B2 vẫn là mốc ngưỡng 0.5 của nguồn, nhưng cần khóa cấu hình LR, preprocessing và có/không calibration trước chạy; không tune ngưỡng B2 để sửa vi phạm. Nếu B1/B2 không khả thi, báo đầy đủ cost/metrics và tách khỏi xếp hạng feasible.

## 7. Phương pháp tối ưu — A4 còn cần khóa search space và budget

Theo roadmap: Optuna TPE cho cấu hình Random Forest và tìm ngưỡng. Đối chứng Random Search cùng search space/budget nếu đủ thời gian. 30–50 trials và 5 seeds là kế hoạch tham khảo, chưa khóa. Cần định nghĩa budget bao gồm số lần thử threshold để so sánh công bằng; ghi toàn bộ trials và cách chọn candidate, không chỉ nghiệm thắng.

Review đề xuất mỗi lượt h quét toàn bộ T(p) theo §5, thay vì coi τ là tìm kiếm liên tục cần thêm sampler. Nếu chọn đối chứng TPE/Random Search, dùng cùng H, số attempts, calibration, seeds và quy tắc dừng; ghi cả failed/pruned/infeasible. Cùng số trials chưa đồng nghĩa cùng chi phí tính toán do số threshold/fit có thể khác.

| Nội dung A4 | Quyết định cụ thể còn thiếu |
|---|---|
| Phạm vi | τ-only hay h+τ là chính; có ablation nào |
| Thuật toán | Xác nhận TPE; Random Search có/không; cách chọn threshold và hòa cost |
| H | Giá trị/miền/sampling của `n_estimators`, `max_depth`, `min_samples_leaf`; toàn bộ tham số RF/pipeline giữ cố định |
| Budget | Số attempts h `B_h`; số lần chấm policy/fit; giới hạn runtime và cách tính failed/pruned |
| Seeds | Danh sách model/optimizer seeds; tách với split/fold seed; cách tổng hợp đa seed |

Không lấy số trial/seeds tham khảo làm default; không tự thêm algorithm, penalty hay tăng budget sau khi xem validation. Log phải có số candidate/vector a thực chấm và runtime fit/search/tổng. Chưa có search space/budget được phép chạy ở lượt này.

## 8. Metrics

Chính: `total_cost`, `cost_per_observation`, `n_maintenance`, `maintenance_rate`, `feasible`, `constraint_violation`. Bổ sung: recall, precision, F1, PR-AUC (ghi rõ estimator/định nghĩa), ROC-AUC, Brier score/calibration, runtime, trial count, mean/std qua seed. Dùng cùng quy tắc xử lý zero denominator/metric không xác định cho mọi phương pháp.

Review đề xuất gọi rõ `average_precision` (AP) thay tên PR-AUC không chỉ rõ estimator; đây là lựa chọn A6 còn cần xác nhận. Metric action dùng a; metric xác suất dùng p. Đề xuất edge cases: recall null khi P=0, precision null khi M=0, F1 dùng `2TP/(2TP+FP+FN)` và chỉ null nếu mẫu số 0; ROC-AUC null khi một lớp; AP null nếu không positive; probability metrics của B0/B1 không có mô hình p là null. Mọi null có reason. Saving tuyệt đối `C_B0-C_policy` có thể âm; saving tỷ lệ null khi C_B0=0. Không báo Brier riêng lẻ là bằng chứng calibration tốt. Chưa tự chọn zero-division default của thư viện.

## 9. Experimental protocol — đề xuất A5, chưa được khóa đầy đủ

1. Tải đúng nguồn, ghi timestamp, SHA-256, schema và license. Không commit raw data.
2. Kiểm tra integrity/schema và rủi ro leakage ở mức cần thiết để chuẩn bị split; không dùng EDA toàn bộ dữ liệu, feature–target relations hoặc nhãn test để quyết định phương pháp. Phê duyệt protocol, feature list và cách xử lý duplicate/nhóm trước EDA định hướng mô hình; EDA lựa chọn chỉ dùng train/validation.
3. Đề xuất split stratified 60/20/20, split seed 42 vẫn **chưa khóa**, chưa thực hiện. Cần review rủi ro phụ thuộc theo thứ tự/nhóm và xác nhận phạm vi nội suy trạng thái tổng hợp trước chọn random split; không suy ra machine ID/timestamp từ UID. Nếu cần split theo thời gian/nhóm thì trình phương án khác trước chạy, không thử nhiều split để chọn kết quả tốt.
4. Lưu split IDs/hash; dùng cùng split cho mọi phương pháp. Khóa riêng split seed, model seed, optimizer seed và calibration-fold seed. Review đề xuất multi-seed giữ split cố định; nếu đổi split thì báo như thiết kế lặp split riêng, không chọn seed thắng.
5. Fit preprocessing/model chỉ trên train. Nếu dùng calibration, fit preprocessing/model trong từng train-fold và calibrator từ dự đoán ngoài fold thuộc train; không fit calibrator trên validation/test. Review đề xuất không calibration so với sigmoid như ablation đăng ký trước, nhưng còn cần quyết định có/không, số folds/seed và cách xử lý ít positives. Chọn threshold/hyperparameter trên validation trong budget khóa trước; best validation cost có thiên lệch lựa chọn, không phải đánh giá độc lập.
6. Chỉ triển khai/chạy cost sau khi A1–A3/A6 đầy đủ và task tương ứng được giao. B1/B2 còn cần A5/pipeline đạt; tối ưu cần thêm A4. So sánh B0/B1/B2/P cùng protocol; log thất bại và nghiệm không khả thi. Việc đánh dấu A1–A6 không tự kích hoạt các task này.
7. Lưu code commit, dependency versions, dataset/split hash, config, seeds, lệnh chạy, params, threshold, cost, feasibility, violation, runtime, status và best-so-far khả thi.
8. Multi-seed, sensitivity và ablation trên development data; phân biệt đánh giá policy cố định với tối ưu lại từng kịch bản. Không chọn kịch bản bằng test.
9. Khóa mô hình, policy, cost scenario và protocol trước đánh giá test cuối khi chủ dự án cho phép; ghi nhận kết quả dù không cải thiện hoặc vi phạm capacity. Review khuyến nghị không refit train+validation ở lượt test đầu; nếu chọn refit cần protocol riêng trước khi đọc test vì p/policy có thể thay đổi. Không dùng kết quả test để mở lại tuning. Chạy tái lập về sau chỉ xác minh cấu hình đã khóa, không tạo vòng chọn cấu hình mới.

Pipeline phải phân biệt kiểm tra schema trước split với fit preprocessing sau split; không diễn giải sơ đồ roadmap có “tiền xử lý” trước split thành quyền fit toàn dữ liệu. Số liệu, hash và split chỉ được ghi khi có kiểm tra thực; lượt hiện tại chưa tải/đọc CSV, tạo split hoặc chạy mô hình.

## 10. Đối chiếu A1–A7 và nội dung cần chủ dự án bổ sung

| ID | Bằng chứng ghi nhận | Quyết định cụ thể còn thiếu hoặc cần xác nhận | Trạng thái đối chiếu |
|---|---|---|---|
| A1 | Chủ dự án đã đánh dấu phê duyệt; review §2/§4 đề xuất quan sát trạng thái, cộng cost một kỳ | Tên đơn vị chi phí; xác nhận không cộng trùng, ranh giới PM/failure và giả định một hàng/một kỳ ở §1 | Cần bổ sung quyết định |
| A2 | Chủ dự án đã đánh dấu phê duyệt; review §4 giữ objective nguồn và phân biệt observed/expected | `C_PM`, `C_F`, η, đơn vị; xác nhận công thức/miền; bảng kịch bản chính/sensitivity và fixed-policy/reoptimization ở §4 | Cần bổ sung quyết định |
| A3 | Chủ dự án đã đánh dấu phê duyệt; review §5 nêu capacity, ties/biên và các lựa chọn | b; recall off/on và R_min nếu on; xác nhận candidate/comparator/domain/B0, N=0/P=0, violations và infeasible ở §5 | Cần bổ sung quyết định |
| A4 | Chủ dự án đã đánh dấu phê duyệt; review §3/§7 đề xuất h+τ chính, τ-only làm mốc và TPE | Chọn phạm vi/thuật toán/đối chứng; H, budget, seeds/runtime và quy tắc hòa cụ thể ở §3/§7 | Cần bổ sung quyết định |
| A5 | Chủ dự án đã đánh dấu phê duyệt; review §2/§6 giữ whitelist và protocol train/validation/test | Xác nhận feature list, split/seed sau review thứ tự/nhóm; duplicate/EDA policy; calibration on/off, folds/seed, refit policy ở §2/§9; quyền test cuối cấp riêng | Cần bổ sung quyết định |
| A6 | Chủ dự án đã đánh dấu phê duyệt; review §7 và cost review §5 đề xuất B0/B1/B2 và metrics | B1 comparator/w hoặc candidate/selection rule; LR/preprocessing/calibration của B2; estimator AP/PR-AUC và metric edge cases ở §6/§8 | Cần bổ sung quyết định |
| A7 | Chat trước đã kích hoạt riêng W1-G1-C; chat hiện tại cho phép sửa spec và tạo nhánh/PR | Nhiệm vụ triển khai tiếp theo, sửa file chung khác và tích hợp nhánh chưa được giao; không coi review là kích hoạt cả tuần/lộ trình | Chờ chỉ dẫn |

Không có giá trị kinh tế nào được coi là đã duyệt nhờ việc tài liệu bootstrap có mặt trên main. Việc chấp nhận scope 5 tuần không đồng nghĩa với phê duyệt mọi con số ví dụ trong roadmap.

Chưa hàng nào của A1–A6 đủ quyết định để đổi thành **Đã phê duyệt** theo tiêu chí chủ dự án yêu cầu ở lượt đối chiếu này. Để hoàn tất từng hàng, ghi: `A<ID>; quyết định cụ thể và giá trị; phạm vi; ngày; tham chiếu phiên bản/commit`. Có thể xác nhận trực tiếp một khuyến nghị bằng số mục nêu trên; trường bắt buộc còn trống vẫn khóa phần phụ thuộc. Không cần phát minh giá trị để làm bảng đủ trạng thái.

A7 giữ “Chờ chỉ dẫn” cho các việc chưa được kích hoạt, đồng thời lưu đúng hai phạm vi đã được giao. Việc tạo PR không phải quyền merge; main chỉ thay đổi sau quyết định tích hợp của chủ dự án. Các tài liệu bootstrap/prompt/board còn ghi chưa kích hoạt là bối cảnh lịch sử; chỉ dẫn chat cụ thể được ưu tiên, không mở thêm task ngoài phạm vi đó.

## 11. Deliverables và cổng nghiệm thu

- Tuần 1 / G1–đầu G2: W1-G1-C đã bàn giao review trong chat, chưa tự chuyển task board sang Done; hoàn thiện quyết định A1–A6 và chủ dự án nghiệm thu/giao riêng proposal, dữ liệu/EDA. Bootstrap và việc sửa nhãn phê duyệt chưa hoàn tất checkpoint học thuật W1.
- Tuần 2 / G2–G4: EDA, pipeline/split không leakage sau A5 và kích hoạt task. Trước baseline G4 phải có cost/constraints tối thiểu cùng unit tests sau A1–A3/A6, không chờ đến G6 mới định nghĩa cách chấm. B2 cần fit LR tối thiểu trong G4 khi được giao; không dùng mốc ML G5 để bỏ dependency này.
- Tuần 3 / G5–G7: xác suất ML, cost/constraints đã duyệt, unit tests tính tay, optimization và trial logs thật.
- Tuần 4 / G8: so sánh, feasibility, stability/sensitivity/ablation, ít nhất hai hình sinh từ logs.
- Tuần 5 / G9–G10: khóa nghiệm, đánh giá test cuối, report 8–12 trang, 5–8 slides/demo, kiểm thử/tái lập và phát hành do chủ dự án quyết định.

Giấy phép mã nguồn của repository chưa được chủ dự án lựa chọn; không tự tạo LICENSE. Quyền dùng dataset theo CC BY 4.0 không tự đặt giấy phép cho mã nguồn dự án.

Lượt đối chiếu chỉ sửa `docs/PROJECT_SPEC.md`; không sửa roadmap, task board, hai bản review, config, source/tests hoặc tài liệu của Antigravity. Không chạy training/baseline/optimization, đánh giá test hay tự kích hoạt AI khác. Bản diff và các điểm thiếu được trình bằng PR, không merge/rebase tích hợp hoặc push trực tiếp main.
