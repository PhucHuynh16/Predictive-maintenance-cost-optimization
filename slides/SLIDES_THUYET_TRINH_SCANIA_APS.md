# SLIDES THUYẾT TRÌNH BÀI TẬP LỚN: NHẬP MÔN TỐI ƯU HÓA (7 SLIDES)

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

## SLIDE 6: KHUNG ĐÁNH GIÁ THỰC NGHIỆM TRÊN TẬP VALIDATION (12.000 MẪU)

- **Bảng so sánh 5 chính sách cố định (Chuẩn bị nghiệm thu Gate B2):**

| Chính sách | Mô hình | Ngưỡng $\tau$ | Tổng chi phí benchmark | Số xe vào xưởng ($M$) | Ràng buộc ($M \le 1200$) |
|:---:|---|:---:|:---:|:---:|:---:|
| **P1** | **B0:** Majority Dummy | N/A | **100.000** | $0$ | **Khả thi** |
| **P2** | **B1:** Decision Stump | 0.5000 | *Pending Gate B2* | *Pending* | *Pending* |
| **P3** | **B1:** Decision Stump | 0.0196 | *Pending Gate B2* | *Pending* | *Pending* |
| **P4** | **B2:** Logistic Regression | 0.5000 | *Pending Gate B2* | *Pending* | *Pending* |
| **P5** | **B2:** Logistic Regression | 0.0196 | *Pending Gate B2* | *Pending* | *Pending* |

- **Quy tắc liêm chính học thuật:** Toàn bộ trạng thái hiển thị rõ ràng là `Pending Gate B2` cho đến khi có lượt chạy thực tế được Chủ dự án cấp quyền. Không tạo số liệu giả mạo.

---

## SLIDE 7: TỔNG KẾT, TÍNH TÁI LẬP & KHAI BÁO AI HỖ TRỢ

- **Khả năng tái lập khoa học (Reproducibility):**
  - Môi trường: Python 3.11.9, seed cố định 42, khóa dependency qua `g3_requirements.lock.txt`.
  - Quản lý tiến trình bằng Windows Job Object (1 thread, trần RAM 2048 MB, timeout 120s).
  - Toàn bộ 271 Scania unit tests PASS 100%. Mọi artifact kết quả có chữ ký băm SHA-256 trong `checksums.json`.
- **Khai báo AI hỗ trợ (AI Assistance Disclosure):**
  - Codex & Antigravity hỗ trợ viết unit test, kiểm tra biên, rà soát I/O guard và khung tài liệu.
  - Sinh viên tự kiểm chứng, trực tiếp xây dựng mô hình toán, xác thực dữ liệu và chịu trách nhiệm học thuật hoàn toàn.
- **Kết luận:** Đề tài hoàn thành chuỗi logic: **Bài toán $\rightarrow$ Mô hình hóa $\rightarrow$ Baseline $\rightarrow$ Tối ưu hóa $\rightarrow$ Thực nghiệm $\rightarrow$ Quyết định**, đáp ứng đầy đủ yêu cầu của bài tập lớn môn học.
