# BẢN THẢO ĐỀ CƯƠNG SLIDES THUYẾT TRÌNH BÀI TẬP LỚN: NHẬP MÔN TỐI ƯU HÓA (7 SLIDES DRAFT)

> **TRẠNG THÁI TÀI LIỆU:** BẢN THẢO ĐỀ CƯƠNG (DRAFT OUTLINE) — Cần sinh bản trình chiếu chính thức (PPTX/PDF) và kiểm chứng trực quan trước khi báo cáo.

**Đề tài:** Tối ưu hóa Chi phí Bảo trì Dự đoán Hệ thống Khí nén trên Xe tải nặng Scania (UCI 421)  
**Sinh viên:** Huỳnh Phúc — Khoa Công nghệ Thông tin, Trường Đại học Văn Lang  
**Thời lượng báo cáo:** 5–7 phút  

---

## SLIDE 1: TỔNG QUAN & BỐI CẢNH BÀI TOÁN

- **Bài toán công nghiệp:** Chẩn đoán hư hỏng hệ thống khí nén (Air Pressure System - APS) trên xe tải hạng nặng Scania (UCI Dataset #421: 60.000 mẫu Train, 16.000 mẫu Test, 170 thuộc tính cảm biến ẩn danh).
- **Ngữ nghĩa dữ liệu chuẩn (UCI Interpretation):**
  - **Lớp dương tính ($y=1$):** Xe hỏng hóc thực sự do lỗi hệ thống APS ($1.67\%$).
  - **Lớp âm tính ($y=0$):** Xe vào xưởng do hỏng hóc ở các **bộ phận KHÁC không thuộc APS** (không phải xe hoàn toàn khỏe mạnh).
- **Mục tiêu tối ưu:** Xác định chính sách can thiệp kiểm tra nhằm **cực tiểu hóa tổng chi phí benchmark**, đồng thời **thỏa mãn ràng buộc năng lực tiếp nhận của xưởng**.

---

## SLIDE 2: MÔ HÌNH HÓA TOÁN HỌC & HÀM MỤC TIÊU PHI ĐỐI XỨNG

- **Biến quyết định:** Vector can thiệp $A \in \{0, 1\}^N$ thông qua ngưỡng phân loại $\tau \in (0, 1)$ và siêu tham số mô hình $\theta$:
  $$a_i(\theta, \tau) = \mathbb{I}[P(y_i = 1 \mid x_i; \theta) \ge \tau]$$
- **Hàm mục tiêu (Ma trận chi phí benchmark):**
  - Chi phí kiểm tra thừa ($FP$, hỏng bộ phận khác nhưng tháo kiểm tra APS): **$10$ đơn vị chi phí**.
  - Chi phí sự cố dọc đường ($FN$, bỏ sót lỗi APS dẫn đến chết máy): **$500$ đơn vị chi phí** (tỷ lệ $50:1$).
  - Chi phí khi xử lý đúng ($TN = 0$, $TP = 0$).
  $$\min_{\theta, \tau} \quad f(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \quad [\text{đơn vị chi phí benchmark}]$$
- *Lưu ý:* Chi phí mang tính quy ước chuẩn hóa (benchmark cost units), không phải giá trị tiền tệ thực tế (USD/VND).

---

## SLIDE 3: RÀNG BUỘC CÔNG SUẤT XƯỞNG & ĐÁNH ĐỔI VẬN HÀNH

- **Giả định ràng buộc năng lực xưởng (Maintenance Capacity Assumption):**
  - Đề tài thiết lập giả định kịch bản vận hành: số lượt xe được đưa vào kiểm tra APS ($M = TP + FP$) trong một chu kỳ không vượt quá **10% quy mô phân vùng**:
    $$M(\theta, \tau) = TP + FP \le K = \left\lfloor \frac{N}{10} \right\rfloor$$
  - Trên tập Validation ($N = 12.000$ mẫu): $K_{\text{val}} = 1.200$ lượt xe.
- **Sự đánh đổi cốt lõi (Core Trade-off):**
  - Giảm ngưỡng $\tau \to 0$ để bắt hết lỗi $FN$ $\implies$ số lượt kiểm tra $M$ bùng nổ, **vi phạm giới hạn công suất xưởng** ($M > 1200$).
  - Nâng ngưỡng $\tau$ để giảm tải cho xưởng $\implies$ bỏ sót lỗi $FN$, **chi phí bùng nổ** do hệ số phạt 500.

---

## SLIDE 4: PHÂN TÍCH LÝ THUYẾT VỀ NGƯỠNG TỶ LỆ CHI PHÍ BAYES

- **Ngưỡng tối ưu Bayes lý thuyết (Unconstrained Cost-ratio Bayes Threshold):**
  $$\tau^*_{\text{Bayes}} = \frac{C_{FP}}{C_{FP} + C_{FN}} = \frac{10}{10 + 500} = \frac{10}{510} \approx 0.0196078$$
- **Ranh giới khoa học quan trọng:**
  - $\tau = 10/510$ chỉ là nghiệm tối ưu lý thuyết khi **KHÔNG CÓ RÀNG BUỘC CÔNG SUẤT** và xác suất dự báo hoàn hảo.
  - Khi có ràng buộc công suất $M \le 1200$, việc áp dụng $\tau = 10/510$ có thể làm vi phạm ràng buộc khả thi ($M > 1200$).
  - Do đó, ngưỡng tối ưu thực tế phải được tìm kiếm thông qua tối ưu hóa có điều kiện.

---

## SLIDE 5: GIAO THỨC DỮ LIỆU & BẢO TOÀN TÍNH KHOA HỌC (G3 & G4)

- **Phân vùng dữ liệu đã khóa (Locked G3 Split):**
  - Train: 48.000 mẫu ($800$ ca dương / $47.200$ ca âm — tỷ lệ $1.67\%$).
  - Validation: 12.000 mẫu ($200$ ca dương / $11.800$ ca âm — tỷ lệ $1.67\%$).
  - **Official Test (16.000 mẫu): NIÊM PHONG TUYỆT ĐỐI (SEALED UNTIL G10)**.
- **Nguyên tắc không rò rỉ dữ liệu (No Data Leakage):**
  - Điền khuyết thiếu (`median`) và chuẩn hóa (`StandardScaler`) fit duy nhất trên 48.000 mẫu Train.
- **Hệ thống mô hình đường cơ sở (G4 Baselines):**
  - **B0:** Majority Dummy ($a_i = 0$, chi phí trần: $500 \times 200 = 100.000$ đơn vị chi phí).
  - **B1:** Decision Stump (`max_depth=1`, đánh giá tại $\tau = 0.5$ và $\tau = 10/510$).
  - **B2:** Logistic Regression (`solver='lbfgs'`, `max_iter=2000`, đánh giá tại $\tau = 0.5$ và $\tau = 10/510$).

---

## SLIDE 6: KẾT QUẢ THỰC NGHIỆM ĐƯỜNG CƠ SỞ TRÊN VALIDATION (GATE B2 HOÀN TẤT)

- **Bảng đo đạc thực tế 5 chính sách cố định (Lượt chạy thực nghiệm `scania_g4_b2_real_002`):**

| Chính sách | Mô hình | Ngưỡng $\tau$ | TP | FP | TN | FN | Tổng chi phí benchmark | Số xe kiểm tra ($M$) | Ràng buộc ($M \le 1200$) | Mức tiết kiệm vs B0 |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | **B0:** Majority Dummy | N/A | 0 | 0 | 11.800 | 200 | **100.000** | $0$ | **Khả thi** | $0.00\%$ |
| **P2** | **B1:** Decision Stump | 0.5000 | 0 | 0 | 11.800 | 200 | **100.000** | $0$ | **Khả thi** | $0.00\%$ |
| **P3** | **B1:** Decision Stump | 0.0196 | 160 | 253 | 11.547 | 40 | **22.530** | $413$ | **Khả thi** | **+77.47%** |
| **P4** | **B2:** Logistic Regression | 0.5000 | 129 | 48 | 11.752 | 71 | **35.980** | $177$ | **Khả thi** | **+64.02%** |
| **P5** | **B2:** Logistic Regression | 0.0196 | 186 | 323 | 11.477 | 14 | **10.230** | $509$ | **Khả thi** | **+89.77%** |

- **Nhận xét thực nghiệm cốt lõi:**
  - **Mô hình tốt nhất:** Logistic Regression tại ngưỡng Bayes $\tau = 10/510 \approx 0.0196$ (P5) đạt chi phí **10.230 đơn vị chi phí benchmark**, bắt được $186/200$ ca lỗi APS (Recall 93.0%), tiết kiệm **+89.77%** so với B0.
  - **Kiểm chứng khả thi:** Số xe kiểm tra $M = 509 \le 1.200$ xe (thỏa mãn ràng buộc công suất 10% của xưởng).
  - **Tài nguyên thực thi:** Đúng 2 lượt fit thực tế (`B1=1, B2=1`), thời gian fit 1.417s, RAM đỉnh 201.90 MB, toàn bộ 11 artifacts được kiểm chứng toàn vẹn mã băm SHA-256 (`verify_run() == True`).

---

## SLIDE 7: TỔNG KẾT, TÍNH TÁI LẬP & LỘ TRÌNH TỐI ƯU HÓA (PHASE 2)

- **Mốc so sánh cơ sở đã khóa (Locked G4 Baseline Cost):**
  - Chi phí benchmark cần vượt qua hoặc đối sánh trong Phase 2 là **10.230 đơn vị chi phí** (B2 tại $\tau = 0.0196$).
- **Lộ trình tối ưu hóa cốt lõi (Phase 2 Optimization):**
  - Thực thi thuật toán tối ưu bắt buộc của học phần: **Random Forest kết hợp Bayesian HPO (Optuna TPE)** và dò ngưỡng có điều kiện.
  - Không gian tìm kiếm: Số cây $n \in [20, 60]$, độ sâu $d \in [4, 12]$, tỷ lệ thuộc tính $[0.2, 0.5]$, ngân sách 20 trials (1 fit/trial trên Train 48k, dò ngưỡng trên Validation 12k không cần refit).
  - Sinh 02 đồ thị bắt buộc: (1) Đồ thị hội tụ Optuna, (2) Đồ thị đánh đổi Chi phí vs Công suất xưởng trên dải ngưỡng $\tau$.
- **Khả năng tái lập khoa học & Liêm chính học thuật:**
  - Môi trường: Python 3.11.9, seed cố định 42, khóa dependency qua `g3_requirements.lock.txt`.
  - Giám sát: Windows Job Object (1 thread, trần RAM 2048 MB, timeout 120s/300s).
  - **Official Test (16.000 mẫu) được niêm phong tuyệt đối (Sealed until G10)** nhằm chống rò rỉ và thiên lệch lựa chọn (selection bias).
- **Khai báo AI hỗ trợ (AI Assistance Disclosure):**
  - Trợ lý AI (Codex & Antigravity) hỗ trợ rà soát unit tests, runner CLI, kiểm tra I/O guard và khung tài liệu.
  - Sinh viên tự xây dựng mô hình toán, xác thực dữ liệu, trực tiếp nghiệm thu và chịu trách nhiệm học thuật hoàn toàn.
- **Kết luận:** Đề tài đã hoàn thành vững chắc giai đoạn **Bài toán $\rightarrow$ Mô hình hóa $\rightarrow$ Baselines**, sẵn sàng bước vào giai đoạn **Tối ưu hóa cốt lõi (Phase 2)** nhằm tìm kiếm chính sách tối ưu toàn diện.
