# PROJECT SPEC — đặc tả đề xuất chờ phê duyệt

Ngày chuẩn bị: 2026-10-21 (Asia/Saigon). Phạm vi đồ án: cá nhân, 5 tuần, 10 giai đoạn theo `ROADMAP.md`. Phạm vi lần này: bootstrap và chuẩn bị giao việc. **Chưa có quyết định phê duyệt formulation/chi phí, code mô hình hay số liệu thực nghiệm.**

## 1. Problem statement

Từ đặc trưng vận hành của mỗi quan sát, ước lượng xác suất hỏng hóc và chọn chính sách đề xuất bảo trì có tổng chi phí mô phỏng nhỏ, đáp ứng nguồn lực. Đơn vị phân tích là quan sát, không mặc nhiên là một máy độc lập hoặc một lịch bảo trì theo thời gian. Đánh giá bằng cùng dữ liệu, kịch bản và constraints cho mọi baseline/phương pháp.

## 2. Dataset và nguồn

[AI4I 2020 — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C). Theo metadata UCI kiểm tra ngày 2026-10-21: dữ liệu tổng hợp, 10.000 quan sát, 6 feature, giấy phép CC BY 4.0; metadata báo không có missing. Đây là thông tin nguồn, chưa phải kiểm tra bản CSV local.

Target dự kiến `Machine failure`. Feature dự kiến: `Type`, `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`. Xác minh tên cột thực tế khi tải. Loại ID `UID`/`UDI`, `Product ID` và nhãn phụ `TWF`, `HDF`, `PWF`, `OSF`, `RNF` khỏi feature. Xem `../data/README.md` để ghi provenance.

## 3. Decision variables

Giữ nguyên đề xuất của lộ trình: `x=(h, τ)`, trong đó `h` là hyperparameter mô hình, `τ ∈ [0,1]`. Với xác suất `p_i(h)`:

```text
a_i(h, τ) = 1[p_i(h) >= τ]
```

`a_i=1` nghĩa là đề xuất bảo trì cho quan sát i. Phương án đơn giản chỉ tối ưu `τ` khi cố định `h` cần chủ dự án chọn phạm vi. Chưa tạo search space thực thi.

## 4. Objective function

**Công thức đề xuất trích từ lộ trình, chưa được duyệt để triển khai:**

```text
min C(h, τ) = Σ_i [C_PM * a_i + C_F * y_i * (1 - η * a_i)]
```

`C_PM` là chi phí mỗi hành động; `C_F` là tổn thất mỗi sự cố; `η` là hiệu quả tránh tổn thất giả định. Chi phí cộng chi phí bảo trì với phần tổn thất còn lại; cùng đơn vị chi phí mô phỏng. Điều kiện đề xuất `C_PM >= 0`, `C_F >= 0`, `0 <= η <= 1`; cần xác nhận miền và ý nghĩa trước khi code.

Dùng `y_i` của validation để chấm và chọn chính sách. Không dùng nhãn test khi tìm kiếm. Chi phí kỳ vọng thay `y_i` bằng `p_i` là một đánh giá khác, không được tráo với chi phí quan sát hoặc dùng như bằng chứng can thiệp.

**AI4I không cung cấp chi phí bảo trì thực tế hoặc kết quả phản thực tế sau can thiệp. Toàn bộ `C_PM`, `C_F`, `η`, đơn vị tiền và số tiết kiệm là mô phỏng. Không đặt giá trị kinh tế mặc định trong code/config khi chưa duyệt.** Ví dụ tiền trong lộ trình không được tự chuyển thành cấu hình chạy.

## 5. Constraints và điểm cần review

Đề xuất giới hạn năng lực `Σ a_i <= floor(b*N)`, `b ∈ [0,1]`. Con số 10% trong roadmap là ví dụ chưa phê duyệt. Có thể cân nhắc `recall >= R_min` nếu định nghĩa rõ và có nghiệm khả thi; chưa kích hoạt constraint recall.

Phải định nghĩa `feasible`, lượng vi phạm và lý do; nghiệm vi phạm không được báo là nghiệm tốt nhất khả thi. Không thêm penalty, top-k, tie-breaking hay constraint tiền tệ thay constraint số lượng mà chưa duyệt. Recall khi không có positive phải được quy định, không tự ép thành một giá trị đẹp.

Điểm biên cần giải quyết: với `p_i >= τ`, `τ=1` vẫn bảo trì các quan sát có `p_i=1`, nên miền này không bảo đảm biểu diễn chính sách không bảo trì. B0 là policy riêng; Codex phải đề xuất cách xử lý candidate/ties và miền khả thi, chủ dự án phê duyệt trước khi sửa công thức/miền. Không tự đổi `>=` thành `>` hoặc thêm `τ>1`.

Đây là chấm chính sách một kỳ trên dữ liệu tĩnh, chưa có horizon trước lỗi, hành động theo lịch, spare parts hoặc ràng buộc từng máy. Không khẳng định nhãn phản ánh kết quả thực tế sau khi áp dụng hành động.

## 6. Baseline

| Mã | Đề xuất | Điều kiện đánh giá |
|---|---|---|
| B0 | Reactive, mọi `a_i=0` | Policy riêng, cùng cost function |
| B1 | Quy tắc ngưỡng `Tool wear` | Chọn quy tắc bằng train/validation, không test |
| B2 | Logistic Regression, ngưỡng 0.5 | Báo cả feasibility, không miễn constraint |
| P | Random Forest + tối ưu `h, τ` | Cùng split và giả định với baseline |

Baseline vi phạm phải được đánh dấu; không âm thầm dùng top-k để làm khả thi. Ngưỡng wear, cách giới hạn hành động và mọi điều chỉnh baseline cần được duyệt trước thực nghiệm.

## 7. Phương pháp tối ưu

Theo roadmap: Optuna TPE cho cấu hình Random Forest và tìm ngưỡng. Đối chứng Random Search cùng search space/budget nếu đủ thời gian. 30–50 trials và 5 seeds là kế hoạch tham khảo, chưa khóa. Cần định nghĩa budget bao gồm số lần thử threshold để so sánh công bằng; ghi toàn bộ trials và cách chọn candidate, không chỉ nghiệm thắng.

## 8. Metrics

Chính: `total_cost`, `cost_per_observation`, `n_maintenance`, `maintenance_rate`, `feasible`, `constraint_violation`. Bổ sung: recall, precision, F1, PR-AUC (ghi rõ estimator/định nghĩa), ROC-AUC, Brier score/calibration, runtime, trial count, mean/std qua seed. Dùng cùng quy tắc xử lý zero denominator/metric không xác định cho mọi phương pháp.

## 9. Experimental protocol (đề xuất)

1. Tải đúng nguồn, ghi timestamp, SHA-256, schema và license. Không commit raw data.
2. Kiểm tra schema/nhãn/phân bố và rủi ro leakage; phê duyệt protocol trước khi EDA dùng để quyết định mô hình. Chuẩn bị split cố định để EDA định hướng lựa chọn chỉ dùng train/validation.
3. Đề xuất split stratified 60/20/20, seed 42; chưa thực hiện. Do metadata UCI và cách sinh có cấu trúc theo thứ tự, review rủi ro phụ thuộc quan sát trước khi chốt random split. Không giả định đây là chứng minh dự báo lỗi tương lai.
4. Lưu split IDs/hash; dùng cùng split cho mọi phương pháp trong một lượt so sánh. Nếu đổi seed chia dữ liệu, ghi riêng split seed, model seed và optimizer seed.
5. Fit preprocessing/model trên train; calibration trong train folds. Chọn threshold/hyperparameter bằng validation. Kiểm tra nguy cơ overfit validation khi thử nhiều cấu hình.
6. Chỉ chạy cost model sau khi duyệt công thức, đơn vị, chi phí, hiệu quả và constraints. So sánh B0/B1/B2/P cùng protocol; log thất bại và nghiệm không khả thi.
7. Lưu code commit, dependency versions, dataset/split hash, config, seeds, lệnh chạy, params, threshold, cost, feasibility, violation, runtime, status và best-so-far khả thi.
8. Multi-seed, sensitivity và ablation trên development data; phân biệt đánh giá policy cố định với tối ưu lại từng kịch bản. Không chọn kịch bản bằng test.
9. Khóa mô hình, policy, cost scenario và protocol trước đánh giá test cuối khi chủ dự án cho phép; ghi nhận kết quả dù không cải thiện. Không dùng kết quả test để mở lại tuning. Chạy tái lập về sau chỉ xác minh cấu hình đã khóa, không tạo vòng chọn cấu hình mới.

## 10. Assumptions và quyết định cần chủ dự án duyệt

| ID | Quyết định | Trạng thái |
|---|---|---|
| A1 | Ý nghĩa một quan sát, đơn vị chi phí, tính cộng được và mô hình một kỳ | Phê duyệt |
| A2 | Công thức objective, `C_PM`, `C_F`, `η`, miền giá trị và các kịch bản sensitivity | Phê duyệt |
| A3 | Giới hạn `b`, có dùng recall constraint không, cách báo infeasible/ties/boundaries | Phê duyệt |
| A4 | Chỉ tối ưu τ hay đồng thời h; search space, algorithm và budget công bằng | Phê duyệt |
| A5 | Feature list, split/seed, EDA scope, calibration và protocol khóa test | Phê duyệt |
| A6 | B0/B1/B2, ngưỡng heuristic, quy tắc feasibility và metrics edge cases | Phê duyệt |
| A7 | Kích hoạt nhiệm vụ tuần 1; thay đổi file chung và tích hợp các nhánh | Chờ chỉ dẫn |

Không có giá trị kinh tế nào được coi là đã duyệt nhờ việc tài liệu bootstrap có mặt trên main. Việc chấp nhận scope 5 tuần không đồng nghĩa với phê duyệt mọi con số ví dụ trong roadmap.

## 11. Deliverables và cổng nghiệm thu

- Tuần 1 / G1–đầu G2: formulation review, proposal, kiểm tra nguồn/schema, kế hoạch EDA và data dictionary; trình duyệt A1–A6. Bootstrap chưa hoàn tất checkpoint học thuật W1.
- Tuần 2 / G2–G4: EDA, pipeline/split không leakage, baseline và metadata tái lập sau phê duyệt.
- Tuần 3 / G5–G7: xác suất ML, cost/constraints đã duyệt, unit tests tính tay, optimization và trial logs thật.
- Tuần 4 / G8: so sánh, feasibility, stability/sensitivity/ablation, ít nhất hai hình sinh từ logs.
- Tuần 5 / G9–G10: khóa nghiệm, đánh giá test cuối, report 8–12 trang, 5–8 slides/demo, kiểm thử/tái lập và phát hành do chủ dự án quyết định.

Giấy phép mã nguồn của repository chưa được chủ dự án lựa chọn; không tự tạo LICENSE. Quyền dùng dataset theo CC BY 4.0 không tự đặt giấy phép cho mã nguồn dự án.
