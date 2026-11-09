# BỘ SLIDES THUYẾT TRÌNH BÁO CÁO BÀI TẬP LỚN: NHẬP MÔN TỐI ƯU HÓA (8 SLIDES)

> **TRẠNG THÁI TÀI LIỆU:** HOÀN CHỈNH — Đã tích hợp đầy đủ số liệu thực nghiệm đo đạc chính thức từ Baseline G4 (`scania_g4_b2_real_002`), Tối ưu hóa Phase 2 (`scania_phase2_rf_optuna_002`) và Đánh giá độc lập Official Test G10 (`scania_g10_official_test_003`).

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
  - **Mô hình tốt nhất G4:** Logistic Regression tại $\tau = 10/510$ (P5) đạt **10.230 đơn vị chi phí** ($Recall = 93.0\%$), thiết lập mốc chuẩn đối sánh cho Phase 2.
  - **Kiểm chứng khả thi:** Số xe kiểm tra $M = 509 \le 1.200$ xe (thỏa mãn ràng buộc công suất 10%).

---

## SLIDE 7: KẾT QUẢ TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RUN 002 HOÀN TẤT)

- **Cấu hình tối ưu hóa cốt lõi:**
  - Thuật toán: **Random Forest** kết hợp **Bayesian HPO (Optuna TPE, seed=42)**.
  - Ngân sách: 20 trials tuần tự, 1 native thread, trần 900s, fit trên Train 48k, dò ngưỡng vector hóa trên Validation 12k.
- **Chính sách khả thi tốt nhất quan sát được (Trial 16):**
  - **Siêu tham số:** $n_{\text{estimators}} = 50$, $\text{max\_depth} = 10$, $\text{min\_samples\_split} = 10$, $\text{max\_features} = 0.427$.
  - **Ngưỡng tối ưu:** $\tau^* = 0.3232$.
  - **Ma trận nhầm lẫn:** $TP = 195/200$ ($Recall = 97.50\%$), $FP = 383$, **$FN = 5$** (chỉ để lọt 5 xe chết máy), $TN = 11.417$.
  - **Tổng chi phí benchmark:** **6.330 đơn vị** ($10 \times 383 + 500 \times 5 = 3.830 + 2.500$).
  - **Năng lực tiếp nhận xưởng:** $M = 578 \le 1.200$ xe (**Khả thi**, dư 622 chỗ trống).
- **So sánh hiệu năng:**
  - Tiết kiệm **93.67%** chi phí so với mốc không can thiệp B0 ($100.000$).
  - Cắt giảm thêm **38.12%** chi phí (tiết kiệm thêm $3.900$ đơn vị) so với mốc tốt nhất G4 B2 ($10.230$).
- **Đồ thị minh chứng:** Đường cong hội tụ Optuna (`figures/optimization/optimization_convergence.png`) và Đường quét ngưỡng thực nghiệm 101 điểm (`figures/optimization/cost_vs_capacity_tradeoff.png`).

---

## SLIDE 8: ĐÁNH GIÁ ĐỘC LẬP OFFICIAL TEST (G10), TÍNH TÁI LẬP & KẾT LUẬN

- **Đánh giá độc lập trên tập Official Test (Gate G10 — Run 003):**
  - **Quy mô:** 16.000 mẫu kiểm thử hoàn toàn độc lập (375 ca lỗi APS thực tế).
  - **Chính sách đóng băng:** Random Forest Trial 16 ($\tau^* = 0.3232$, $K=1.600$, 0 fit trên Test).
  - **Hiệu năng thực tế:** $TP = 357$, $FP = 484$, **$FN = 18$**, $TN = 15.141$.
  - **Chỉ số đo đạc:** **$Recall = 95.20\%$**, **$Precision = 42.45\%$**, $ROC\text{-}AUC = 0.9861$, $PR\text{-}AUC = 0.7495$.
  - **Chi phí benchmark:** **13.840 đơn vị** (tiết kiệm **92.62%** so với mốc không can thiệp $187.500$).
  - **Ràng buộc công suất xưởng:** $M = 841 \le 1.600$ xe (**Khả thi**, dư 759 chỗ trống).
- **Khả năng tái lập khoa học (Full Reproducibility) & Liêm chính học thuật:**
  - Giám sát nghiêm ngặt qua Windows Job Object: 1 thread cố định, đỉnh RAM < 202 MB.
  - Bảo tồn nguyên vẹn 100% bằng chứng và nhật ký sự cố các lần chạy trước (Runs 001, 002).
  - Mọi artifact từ G4, Phase 2 đến G10 đều được ký băm mật mã học SHA-256 (`verify` -> PASS).
- **Khai báo AI hỗ trợ (AI Assistance Disclosure):**
  - Trợ lý AI (Codex & Antigravity) hỗ trợ rà soát unit tests, runner CLI và định dạng tài liệu. Sinh viên tự xây dựng mô hình toán, xác thực dữ liệu và chịu trách nhiệm học thuật hoàn toàn.
- **Kết luận:** Đề tài đã giải quyết trọn vẹn bài toán tối ưu hóa chi phí có ràng buộc: từ bài toán công nghiệp $\rightarrow$ mô hình toán học $\rightarrow$ hệ thống cơ sở chuẩn tắc G4 $\rightarrow$ giải thuật tối ưu hóa Bayes Phase 2 $\rightarrow$ nghiệm thu thực nghiệm độc lập Gate G10 với mức tiết kiệm chi phí vượt trội **92.62%**.
