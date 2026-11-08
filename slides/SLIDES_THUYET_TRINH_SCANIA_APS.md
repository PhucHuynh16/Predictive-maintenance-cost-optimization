# SLIDES BÁO CÁO: TỐI ƯU HÓA CHI PHÍ BẢO TRÌ DỰ ĐOÁN XE TẢI NẶNG SCANIA APS (UCI 421)

---

## SLIDE 1: TIÊU ĐỀ ĐỀ TÀI
- **Đề tài:** Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén (APS) trên xe tải nặng Scania (UCI 421)
- **Môn học:** Nhập môn Tối ưu hóa — HK1/2026–2027
- **Học viên thực hiện:** Nhóm nghiên cứu Scania APS Cost Optimization
- **Mục tiêu:** Cực tiểu hóa tổng chi phí bảo dưỡng phi đối xứng dưới ràng buộc năng lực xưởng $M \le \lfloor N/10 \rfloor$.

---

## SLIDE 2: BỐI CẢNH & TÍNH CẤP THIẾT
- **Hệ thống khí nén (APS):** Cung cấp khí nén cho hệ thống phanh, ly hợp, hệ thống treo trên xe tải nặng.
- **Rủi ro vận hành:** Lỗi APS dọc đường gây chết máy, sự cố an toàn nghiêm trọng, chi phí cứu hộ và trễ hạn hợp đồng vận tải rất đắt.
- **Vấn đề dữ liệu:**
  - 60.000 mẫu xe trong tập huấn luyện.
  - Tỷ lệ lỗi cực hiếm: $1.67\%$ (1.000 xe hỏng / 60.000 xe).
  - 170 thuộc tính cảm biến bị ẩn danh với tỷ lệ khuyết thiếu cao.

---

## SLIDE 3: BÀI TOÁN TỐI ƯU HÓA CHI PHÍ PHI ĐỐI XỨNG
- **Ma trận chi phí:**
  - $C_{TN} = 0$: Xe tốt, không báo lỗi.
  - $C_{TP} = 0$: Xe hỏng, sửa chữa đúng bệnh kịp thời.
  - $C_{FP} = 10$: Xe tốt nhưng báo động nhầm $\rightarrow$ Chi phí kiểm tra định kỳ tại xưởng.
  - $C_{FN} = 500$: Xe hỏng nhưng bỏ sót $\rightarrow$ Xe chết máy dọc đường, chi phí cứu hộ khẩn cấp.
- **Tỷ lệ tổn thất:** $C_{FN} / C_{FP} = 500 / 10 = 50:1$.
- **Hàm mục tiêu:**
  $$\min \text{Total Cost} = 10 \cdot FP + 500 \cdot FN$$

---

## SLIDE 4: RÀNG BUỘC VẬN HÀNH THỰC TẾ
- **Giới hạn công suất xưởng sửa chữa:**
  - Xưởng chỉ tiếp nhận tối đa $10\%$ tổng quy mô đội xe trong mỗi chu kỳ bảo dưỡng:
    $$M = TP + FP \le \left\lfloor \frac{N}{10} \right\rfloor$$
  - Trên tập Validation ($N = 12.000$ mẫu): $K = \lfloor 12000 / 10 \rfloor = 1200$ lượt xe.
- **Hệ quả tối ưu hóa:**
  - Không thể hạ ngưỡng $\tau \to 0$ vô tội vạ để bắt hết FN vì sẽ làm bùng nổ FP và vi phạm trần công suất xưởng.

---

## SLIDE 5: GIAO THỨC DỮ LIỆU & BẢO TOÀN TÍNH KHOA HỌC (G3)
- **Tập Train chính thức (60.000 mẫu):**
  - Train: 48.000 mẫu ($800$ ca lỗi / $47.200$ ca bình thường).
  - Validation: 12.000 mẫu ($200$ ca lỗi / $11.800$ ca bình thường).
- **Nguyên tắc "No Data Leakage":**
  - Mọi phép điền trung vị (`SimpleImputer`) và chuẩn hóa (`StandardScaler`) chỉ fit trên tập Train.
- **Niêm phong Official Test (16.000 mẫu):**
  - Khóa kín tuyệt đối cho đến vòng đánh giá cuối cùng. Không dùng tuning.

---

## SLIDE 6: CÁC MÔ HÌNH ĐƯỜNG CƠ SỞ (BASELINES - G4)
- **B0 — Majority Dummy:** Dự đoán toàn bộ xe bình thường ($a_i = 0$).
  - Chi phí trần: $500 \times 200 = 100,000$ chi phí.
- **B1 — Decision Stump:** Cây quyết định độ sâu 1 tầng (`max_depth=1`).
- **B2 — Logistic Regression:** Hồi quy Logistic chuẩn hóa lbfgs (`max_iter=2000`).
- **Hai chiến lược ngưỡng:**
  - Ngưỡng xác suất tiêu chuẩn: $\tau = 0.5$.
  - Ngưỡng tỷ lệ chi phí Bayes: $\tau = \frac{10}{510} \approx 0.0196$.

---

## SLIDE 7: PHƯƠNG PHÁP ĐỀ XUẤT (G5)
- **Mô hình Random Forest:**
  - Nắm bắt tương quan phi tuyến giữa 170 cảm biến APS.
  - Cân bằng trọng số mẫu cho lớp thiểu số.
- **Tối ưu hóa siêu tham số & Ngưỡng Bayesian (Optuna TPE):**
  - Không gian tham số: `n_estimators`, `max_depth`, `min_samples_split`, `class_weight`.
  - Tối ưu hóa trực tiếp ngưỡng quyết định $\tau^*$.
  - Tích hợp hàm phạt vi phạm ràng buộc $M > 1200$.

---

## SLIDE 8: KẾT QUẢ THỰC NGHIỆM TRÊN TẬP VALIDATION
*(Cập nhật bảng số đo thực tế từ thực nghiệm)*
- So sánh Recall, Precision, False Negatives, False Positives.
- So sánh chi phí kinh tế và mức độ tiết kiệm chi phí so với B0.
- Đánh giá thỏa mãn ràng buộc năng lực xưởng ($M \le 1200$).

---

## SLIDE 9: TRỰC QUAN HÓA KẾT QUẢ
*(Cập nhật biểu đồ đường cong Precision-Recall, biểu đồ Pareto Chi phí vs Năng lực xưởng)*

---

## SLIDE 10: TÍNH TÁI LẬP & KIỂM SOÁT THỰC NGHIỆM
- Kiểm soát tiến trình bằng Windows Job Object (1 thread, 2048 MB RAM, 120s timeout).
- Chữ ký băm toàn vẹn SHA-256 cho toàn bộ artifacts đầu ra.
- 271/271 unit tests kiểm chứng tự động toàn diện.

---

## SLIDE 11: KẾT LUẬN & ĐÓNG GÓP
- Đưa ra giải pháp cân bằng tối ưu giữa việc phát hiện sớm lỗi nguy hiểm (FN) và chi phí kiểm tra định kỳ (FP).
- Tuân thủ chặt chẽ ràng buộc giới hạn vận hành công nghiệp của đội xe Scania.
- Cung cấp gói mã nguồn khoa học, minh bạch và có khả năng ứng dụng thực tế cao.
