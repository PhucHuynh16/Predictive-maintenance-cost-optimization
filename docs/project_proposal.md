# ĐỀ CƯƠNG NGHIÊN CỨU & MÔ HÌNH HÓA BÀI TOÁN

- **Đề tài:** Tối ưu hóa chi phí bảo trì dự đoán bằng Machine Learning trên thiết bị gia công công nghiệp
- **Mã nhiệm vụ:** W1-G1-A (Tuần 1 – Giai đoạn 1: Phân tích đề tài và mô hình hóa bài toán)
- **Tác giả phụ trách:** Antigravity (theo phân quyền `AGENTS.md`)
- **Ngày hoàn thiện:** 2026-10-22 (Asia/Saigon)
- **Tài liệu căn cứ:** [PROJECT_SPEC PR #1](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/1), [Codex Review PR #3](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/3), [EDA Findings](eda_findings.md), [Pipeline Diagram](../figures/pipeline.mmd).

---

## 1. Bối Cảnh Thực Tế & Vấn Đề Nghiên Cứu

Trong sản xuất công nghiệp 4.0, bảo trì phản ứng (run-to-failure) gây gián đoạn dây chuyền và tổn thất sự cố nặng nề ($C_F$). Ngược lại, bảo trì phòng ngừa định kỳ theo thời gian làm lãng phí nhân lực và chi phí linh kiện ($C_{PM}$) khi thiết bị vẫn còn tốt. Bảo trì dự đoán (Predictive Maintenance - PdM) tích hợp cảm biến IoT nhằm nhận diện sớm nguy cơ sự cố để can thiệp kịp thời.

Phần lớn nghiên cứu PdM hiện nay chỉ tối ưu hóa các độ đo thống kê thuần túy (F1, ROC-AUC, Accuracy) với giả định sai lầm đối xứng hoặc dùng ngưỡng mặc định $\tau = 0.5$. Tuy nhiên, thực tế vận hành đòi hỏi:
1. **Bất đối xứng chi phí nghiêm trọng:** Bỏ sót sự cố (False Negative) gây tổn thất lớn gấp 20 lần việc kiểm tra phòng ngừa không cần thiết (False Positive): $C_F / C_{PM} = 20 / 1$.
2. **Ràng buộc năng lực nguồn lực hữu hạn (Capacity Constraint):** Số hành động bảo trì mỗi kỳ bị khống chế tối đa $b = 10\%$ số thiết bị do giới hạn nhân lực và thời gian dừng máy.

**Vấn đề nghiên cứu:** Thiết lập mô hình toán học và pipeline thực nghiệm tối ưu hóa đồng thời cấu hình mô hình ML và ngưỡng quyết định can thiệp $x = (h, \tau)$ nhằm tối thiểu hóa tổng chi phí vận hành mô phỏng dưới ràng buộc năng lực nghiêm ngặt.

---

## 2. Mục Tiêu Nghiên Cứu & Câu Hỏi Nghiên Cứu (RQs)

- **Mục tiêu tổng quát:** Xây dựng khung phương pháp luận tích hợp Machine Learning và Tối ưu hóa toán học để ra quyết định bảo trì chi phí tối thiểu thỏa mãn ràng buộc năng lực.
- **Mục tiêu cụ thể:** (1) Kiểm toán dữ liệu AI4I 2020 và kiểm soát rò rỉ; (2) Thiết lập mô hình bài toán chi phí đơn kỳ và bộ ca kiểm thử đơn vị; (3) Xây dựng 3 baseline đối chuẩn B0, B1, B2; (4) Tối ưu hóa đồng thời $x=(h,\tau)$ qua Random Forest và Optuna TPE; (5) Phân tích độ nhạy và kiểm chứng tái lập.
- **Câu hỏi nghiên cứu:**
  - **RQ1:** Mô hình Random Forest kết hợp tối ưu ngưỡng $\tau^*$ có giúp giảm tổng chi phí vận hành so với chính sách phản ứng B0 và các heuristic công nghiệp B1, B2 dưới cùng ràng buộc capacity không?
  - **RQ2:** Tối ưu hóa đồng thời $x = (h, \tau)$ bằng Optuna TPE mang lại lợi ích giảm chi phí ra sao so với chỉ tối ưu ngưỡng $\tau$ trên mô hình cố định?
  - **RQ3:** Chính sách tối ưu thể hiện độ bền vững thế nào trước biến thiên của tổn thất sự cố $C_F \in \{5, 10, 20, 40\}$ và hiệu quả can thiệp $\eta \in \{0.7, 0.8, 1.0\}$?

---

## 3. Dữ Liệu AI4I 2020 & Kiểm Soát Rủi Ro Dữ Liệu

- **Nguồn gốc:** UCI AI4I 2020 Predictive Maintenance Dataset (DOI: [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C)), công bố bởi Stephan Matzka (2020), giấy phép CC BY 4.0. Gồm 10,000 quan sát, 14 cột, 0 missing, nhãn chính `Machine failure` mất cân bằng nghiêm trọng (339 ca lỗi, 3.39%).
- **Inputs hợp lệ (6 features vận hành):** `Type` (phân loại L/M/H), `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`.
- **Loại trừ chống Target & ID Leakage:** Cấm dùng `UDI`, `Product ID` và 5 nhãn phụ nguyên nhân sau lỗi (`TWF`, `HDF`, `PWF`, `OSF`, `RNF`).
- **Giao thức chia tập (Split Protocol):** Đề xuất Stratified Random Split 60% Train, 20% Validation, 20% Test (seed 42) là phương án phê duyệt có điều kiện, cần đánh giá mức độ phụ thuộc dữ liệu theo chuỗi UDI trước G3 (chi tiết tại [docs/eda_findings.md](eda_findings.md)).
- **Kiểm soát rủi ro Exposure:** Nhận diện rủi ro phơi nhiễm thông tin do đã thực hiện kiểm toán EDA trên toàn bộ nhãn raw ban đầu. Trong giai đoạn development, rủi ro này được kiểm soát nghiêm ngặt bằng cách cô lập hoàn toàn tập Test: cấm dùng Test để chọn feature, tuning siêu tham số hay sửa đổi protocol.

---

## 4. Biến Quyết Định, Objective & Ràng Buộc

### 4.1. Biến quyết định & Chính sách
$$x = (h, \tau), \quad h \in \mathcal{H}, \quad \tau \in [0, 1]$$
- $h$: Siêu tham số của mô hình Random Forest (fit duy nhất trên Train).
- $\tau$: Ngưỡng quyết định can thiệp bảo trì. Hành động nhị phân: $a_i(h, \tau) = \mathbb{I}[p_i(h) \ge \tau]$.
- **Lưu ý:** Tập Validation sinh xác suất $p_i(h)$ thuần túy từ ma trận đặc trưng; nhãn thực $y_{val}$ chỉ dùng để tính chi phí $C_{obs}$ và chọn chính sách, không tham gia sinh xác suất.

### 4.2. Hàm mục tiêu chi phí quan sát ($C_{obs}$)
$$\min_{x = (h, \tau)} C_{obs}(h, \tau) = \sum_{i=1}^{N} \left[ C_{PM} \cdot a_i(h, \tau) + C_F \cdot y_i \cdot (1 - \eta \cdot a_i(h, \tau)) \right]$$
- **Tham số đã duyệt:** $C_{PM} = 1\text{ cost unit}$ (chi phí mỗi lần PM); $C_F = 20\text{ cost units}$ (tổn thất sự cố khi không can thiệp); $\eta = 0.8$ (tỷ lệ tổn thất tránh được khi PM thành công).
- **Ý nghĩa đơn vị:** Đơn vị chuẩn hóa là *cost units*. Dữ liệu AI4I là dữ liệu mô phỏng; toàn bộ chi phí và mức tiết kiệm mang bản chất mô phỏng học thuật, không đại diện cho dòng tiền hay chi phí tài chính thực tế. Chi phí kỳ vọng $C_{exp}$ chỉ dùng chẩn đoán xác suất nội bộ, không tráo đổi với $C_{obs}$.

### 4.3. Ràng buộc năng lực (Capacity Constraint)
$$M = \sum_{i=1}^{N} a_i(h, \tau) \le K = \lfloor b \cdot N \rfloor, \quad b = 0.10$$
- Trên tập Validation ($N = 2,000$ mẫu): Giới hạn tối đa $K = 200$ hành động bảo trì.
- Chính sách có $M > K$ bị phân loại là `Infeasible`, ghi nhận lượng vi phạm `capacity_excess = M - K` và bị loại khỏi nghiệm tối ưu.
- **Quy định về Recall:** Recall được xác định là **chỉ số đánh giá (metric)**, **KHÔNG PHẢI ràng buộc cứng (hard constraint)**.

---

## 5. Hệ Thống Baselines & Phương Pháp Đề Xuất P

1. **B0 (Reactive Baseline):** Chính sách không bảo trì trước (mọi $a_i = 0$). Là policy độc lập, chi phí $C_{B0} = C_F \cdot P = 20 \cdot P$.
2. **B1 (Fixed Rule Baseline):** Heuristic công nghiệp $a_i = \mathbb{I}[\text{Tool wear [min]} \ge w]$, với mốc đề xuất $w = 200$ phút (chờ duyệt chính thức).
3. **B2 (ML Standard Baseline):** Mô hình Logistic Regression chuẩn (fit trên Train), áp dụng ngưỡng mặc định $\tau = 0.5$.
4. **P (Proposed Optimization Method):** Random Forest Classifier kết hợp thuật toán tối ưu hóa Bayes **Optuna TPE** (30 trials, seed 42) tìm kiếm đồng thời $x^* = (h^*, \tau^*)$ trên Validation.
- *Nguyên tắc phân biệt:* Baselines B0, B1, B2 được đánh giá độc lập làm đối chuẩn; Optuna TPE chỉ tìm kiếm cấu hình cho phương pháp đề xuất P.

---

## 6. Quy Trình Thực Nghiệm, Pipeline & Metrics

- **Tiền xử lý:** Pipeline tiền xử lý (Encoder, Scaler) **CHỈ ĐƯỢC FIT TRÊN TẬP TRAIN**. Tập Validation và Test chỉ áp dụng phép biến đổi (transform) từ preprocessor đã fit, tuyệt đối không fit lại.
- **Bộ chỉ số đánh giá (Metrics):**
  - *Kinh tế & Tối ưu:* `total_cost` ($C_{obs}$), `cost_per_observation`, `n_maintenance` ($M$), `maintenance_rate`, `feasible`, `capacity_excess`, `cost_saving` so với B0.
  - *Chất lượng ML:* Recall, Precision, F1-score, PR-AUC, ROC-AUC, Brier score, Runtime.
- **Sơ đồ Pipeline phương pháp luận:** Toàn bộ kiến trúc luồng dữ liệu, cô lập chống rò rỉ, đánh giá baseline và vòng lặp TPE được đặc tả đầy đủ tại tệp sơ đồ riêng: [figures/pipeline.mmd](../figures/pipeline.mmd).
- **Cổng nghiệm thu Test cuối:** Tập Test được khóa kín tuyệt đối. Quyết định A7 hiện tại chỉ mở các nhiệm vụ Tuần 1; việc mở và đánh giá Test cuối bắt buộc phải có **phê duyệt riêng tại G10 (W5-G10-C)** sau khi chính sách tối ưu đã được đóng băng.

---

## 7. Kế Hoạch 5 Tuần & Phân Định Quyết Định (A1–A7)

### 7.1. Kế hoạch triển khai 5 tuần (10 giai đoạn)
- **Tuần 1 (G1–G2):** Mô hình hóa bài toán, API cost/constraints, đề cương nghiên cứu, kiểm toán dữ liệu và EDA ([W1-G1-C](problem_formulation.md), [W1-G1-A](project_proposal.md), [W1-G2-A](eda_findings.md)).
- **Tuần 2 (G3–G4):** Xây dựng pipeline dữ liệu chuẩn hóa, chia tập 60/20/20, triển khai và đánh giá độc lập các baseline B0, B1, B2.
- **Tuần 3 (G5–G7):** Huấn luyện mô hình ML xác suất, hoàn thiện module cost/constraints, chạy tối ưu Optuna TPE (30 trials, seed 42).
- **Tuần 4 (G8):** Thực nghiệm mở rộng, phân tích độ nhạy ($C_F, \eta$), kiểm tra độ ổn định đa hạt giống và ablation study.
- **Tuần 5 (G9–G10):** Soạn thảo báo cáo học thuật 8–12 trang, slide bảo vệ, demo giao diện, mở đánh giá Test cuối và kiểm chứng tái lập.

### 7.2. Phân định quyết định đã duyệt và chi tiết còn chờ duyệt
- **Đã phê duyệt:** $C_{PM}=1$, $C_F=20$, $\eta=0.8$; Capacity $b=0.10$; Recall là metric; B0 policy riêng; Random Forest + Optuna TPE (30 trials, seed 42); Split 60/20/20 seed 42 (có điều kiện).
- **Chi tiết A2–A6 còn chờ phê duyệt trước khi code:**
  - *A2:* Thiết kế độ nhạy (quét 12 tổ hợp $C_F \times \eta$ hay từng biến đơn lẻ; đánh giá fixed-policy hay re-optimization).
  - *A3:* Quy ước tập ngưỡng ứng viên $\mathcal{T}(p)$, xử lý hòa chi phí và trường hợp không có nhãn dương ($P=0$).
  - *A4:* Miền 4 siêu tham số của Random Forest (`n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`) và các tham số cố định.
  - *A5:* Đánh giá phụ thuộc chuỗi UDI trước G3, cấu hình calibration (folds/method) và phê duyệt mở Test tại G10.
  - *A6:* Mốc ngưỡng $w = 200$ phút của B1 và cấu hình tiền xử lý chi tiết cho Logistic Regression (B2).
