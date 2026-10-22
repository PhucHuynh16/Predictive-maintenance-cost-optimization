# ĐỀ CƯƠNG NGHIÊN CỨU & MÔ HÌNH HÓA BÀI TOÁN

- **Đề tài:** Tối ưu hóa chi phí bảo trì dự đoán bằng Machine Learning trên thiết bị gia công công nghiệp
- **Mã nhiệm vụ:** W1-G1-A (Tuần 1 – Giai đoạn 1) | **Phụ trách:** Antigravity (theo `AGENTS.md`)
- **Tài liệu căn cứ:** [PROJECT_SPEC PR #1](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/1), [Codex Review PR #3](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/3), [EDA Findings](eda_findings.md), [Pipeline Diagram](../figures/pipeline.mmd).

---

## 1. Bối Cảnh, Vấn Đề Nghiên Cứu & Mục Tiêu

Trong sản xuất 4.0, bảo trì phản ứng (run-to-failure) gây tổn thất sự cố nặng nề ($C_F$), còn bảo trì phòng ngừa định kỳ gây lãng phí chi phí ($C_{PM}$) khi thiết bị chưa hỏng. Bảo trì dự đoán (PdM) sử dụng cảm biến IoT để phát hiện sớm sự cố. Tuy nhiên, ML truyền thống chỉ tối ưu độ đo thống kê (F1, ROC-AUC) với ngưỡng $\tau = 0.5$, bỏ qua hai yếu tố thực tế:
1. **Bất đối xứng chi phí:** Bỏ sót sự cố (FN) gây thiệt hại gấp 20 lần bảo trì phòng ngừa không cần thiết (FP): $C_F / C_{PM} = 20 / 1$.
2. **Ràng buộc năng lực:** Số hành động bảo trì bị giới hạn tối đa $b = 10\%$ **tổng số quan sát vận hành** (không mặc định là số máy độc lập).

**Vấn đề nghiên cứu:** Tối ưu hóa đồng thời cấu hình ML và ngưỡng can thiệp $x = (h, \tau)$ để tối thiểu tổng chi phí vận hành mô phỏng dưới ràng buộc năng lực quan sát.

**Mục tiêu tổng quát:** Xây dựng khung phương pháp luận và pipeline thực nghiệm tích hợp phân loại xác suất ML và tối ưu hóa toán học ra quyết định bảo trì chi phí tối thiểu thỏa mãn capacity.

**Câu hỏi nghiên cứu (RQs):**
- **RQ1:** Random Forest kết hợp tối ưu ngưỡng $\tau^*$ có giảm tổng chi phí so với baselines B0, B1, B2 dưới cùng ràng buộc capacity không?
- **RQ2:** Tối ưu đồng thời $x = (h, \tau)$ bằng Optuna TPE mang lại lợi ích chi phí ra sao so với chỉ tối ưu $\tau$ trên mô hình cố định?
- **RQ3:** Chính sách tối ưu bền vững thế nào trước biến thiên của $C_F \in \{5, 10, 20, 40\}$ và $\eta \in \{0.7, 0.8, 1.0\}$?

---

## 2. Dữ Liệu AI4I 2020 & Kiểm Soát Rò Rỉ

- **Dataset:** UCI AI4I 2020 ([DOI: 10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C), CC BY 4.0), 10,000 quan sát, 0 missing, target `Machine failure` mất cân bằng 3.39% (339 ca lỗi).
- **Lọc đặc trưng hợp lệ (6 features):** `Type` (L/M/H), `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`.
- **Loại trừ chống Leakage:** Loại bỏ hoàn toàn `UDI`, `Product ID` và 5 nhãn phụ nguyên nhân sự cố (`TWF`, `HDF`, `PWF`, `OSF`, `RNF`) **trước khi fit pipeline tiền xử lý**.
- **Giao thức chia tập:** Stratified Random Split 60% Train (6,000), 20% Validation (2,000), 20% Test (2,000), seed 42 là phương án duyệt có điều kiện, cần Codex đánh giá phụ thuộc chuỗi UDI trước G3 (xem [docs/eda_findings.md](eda_findings.md)).
- **Kiểm soát rủi ro Exposure:** Nhận diện rủi ro phơi nhiễm do đã kiểm toán EDA toàn nhãn raw ban đầu; kiểm soát trong development bằng cách cô lập hoàn toàn tập Test khỏi tiền xử lý và tìm kiếm mô hình.

---

## 3. Biến Quyết Định, Objective & Ràng Buộc

### 3.1. Biến quyết định & Chính sách
$$x = (h, \tau), \quad h \in \mathcal{H}, \quad \tau \in [0, 1], \quad a_i(h, \tau) = \mathbb{I}[p_i(h) \ge \tau]$$
- $h$: Siêu tham số Random Forest fit duy nhất trên Train. $\tau$: Ngưỡng quyết định can thiệp.
- *Lưu ý:* Validation sinh xác suất $p_i(h)$ thuần túy từ ma trận đặc trưng; nhãn thực $y_{val}$ chỉ dùng tính chi phí $C_{obs}$ và chọn chính sách, không tham gia sinh xác suất.

### 3.2. Hàm mục tiêu chi phí quan sát ($C_{obs}$)
$$\min_{x = (h, \tau)} C_{obs}(h, \tau) = \sum_{i=1}^{N} \left[ C_{PM} \cdot a_i(h, \tau) + C_F \cdot y_i \cdot (1 - \eta \cdot a_i(h, \tau)) \right]$$
- **Tham số đã duyệt:** $C_{PM} = 1\text{ cost unit}$, $C_F = 20\text{ cost units}$, $\eta = 0.8$.
- **Bản chất mô phỏng:** Đơn vị chuẩn hóa là *cost units*. Dữ liệu AI4I là mô phỏng, toàn bộ chi phí và mức tiết kiệm mang tính học thuật, không đại diện dòng tiền hay chi phí thực tế. Chi phí kỳ vọng $C_{exp}$ chỉ dùng chẩn đoán xác suất, không tráo đổi với $C_{obs}$.

### 3.3. Ràng buộc năng lực (Capacity Constraint)
$$M = \sum_{i=1}^{N} a_i(h, \tau) \le K = \lfloor b \cdot N \rfloor, \quad b = 0.10$$
- Giới hạn tối đa **10% số quan sát của tập đánh giá** ($K = 200$ trên Validation $N = 2,000$).
- Chính sách có $M > K$ bị phân loại `Infeasible`, ghi nhận vi phạm `capacity_excess = M - K` và bị loại.
- **Quy định Recall:** Recall là **metric đánh giá**, **KHÔNG PHẢI ràng buộc cứng (hard constraint)**.

---

## 4. Hệ Thống Baselines & Phương Pháp Đề Xuất P

- **B0 (Reactive Baseline):** Mọi $a_i = 0$ (policy không can thiệp riêng biệt), chi phí $C_{B0} = 20 \cdot P$.
- **B1 (Fixed Rule Baseline):** Heuristic $a_i = \mathbb{I}[\text{Tool wear} \ge w]$ (đề xuất $w = 200$ min chờ duyệt).
- **B2 (ML Standard Baseline):** Logistic Regression chuẩn fit trên Train, ngưỡng $\tau = 0.5$.
- **P (Proposed Method):** Random Forest Classifier kết hợp **Optuna TPE** (30 trials, seed 42) tìm $x^* = (h^*, \tau^*)$ trên Validation.
- *Phân biệt:* Baselines B0, B1, B2 được đánh giá độc lập làm đối chuẩn; Optuna TPE chỉ tìm kiếm nghiệm cho phương pháp P.

---

## 5. Quy Trình Thực Nghiệm, Pipeline & Metrics

- **Tiền xử lý:** Tách 6 features $\rightarrow$ fit preprocessor (Encoder, Scaler) **DUY NHẤT TRÊN TRAIN** $\rightarrow$ transform Validation và Test (không fit lại). Sơ đồ luồng chi tiết tại [figures/pipeline.mmd](../figures/pipeline.mmd).
- **Bộ chỉ số:** Kinh tế ($C_{obs}$, cost/obs, $M$, maintenance rate, feasibility, capacity excess, saving) và ML (Recall, Precision, F1, PR-AUC, ROC-AUC, Brier score, runtime).
- **Cổng nghiệm thu Test cuối:** Tập Test được khóa kín. Quyết định A7 hiện tại chỉ mở nhiệm vụ Tuần 1; việc mở Test cuối bắt buộc phải có **phê duyệt riêng tại G10 (W5-G10-C)** sau khi chính sách tối ưu đã đóng băng.

---

## 6. Kế Hoạch 5 Tuần & Phân Định Quyết Định (A1–A7)

- **Lộ trình 5 tuần:** W1 (G1–G2: Đề cương, review toán học, kiểm toán dữ liệu); W2 (G3–G4: Pipeline split, Baselines); W3 (G5–G7: ML xác suất, cost model, Optuna TPE); W4 (G8: Độ nhạy $C_F \times \eta$, multi-seed, ablation); W5 (G9–G10: Báo cáo, demo, mở Test cuối và kiểm chứng tái lập).
- **Đã phê duyệt:** $C_{PM}=1, C_F=20, \eta=0.8$; Capacity $b=0.10$ số quan sát; Recall là metric; B0 policy riêng; RF + Optuna TPE (30 trials, seed 42); Split 60/20/20 seed 42 (có điều kiện).
- **Chi tiết chờ duyệt trước khi code (A2–A6):** Thiết kế sensitivity ($12$ tổ hợp $C_F \times \eta$ hay từng yếu tố); candidate thresholds $\mathcal{T}(p)$ và hòa cost; miền 4 siêu tham số $\mathcal{H}$; đánh giá phụ thuộc UDI trước G3 và calibration; mốc $w=200$ min của B1 và cấu hình LR của B2 (đối chiếu tại [docs/problem_formulation.md](problem_formulation.md) và [docs/cost_model_review.md](cost_model_review.md)).
