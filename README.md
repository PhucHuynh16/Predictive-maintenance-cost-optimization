# Tối Ưu Hóa Chi Phí Bảo Trì Dự Đoán Hệ Thống Khí Nén Xe Tải Nặng Scania APS (UCI 421)

[![Academic Submission](https://img.shields.io/badge/Coursework-Introduction%20to%20Optimization-blue.svg)](#)
[![Python 3.11](https://img.shields.io/badge/python-3.11.9-blue.svg)](#)
[![Dataset](https://img.shields.io/badge/UCI-Scania%20APS%20%23421-orange.svg)](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks)
[![Status](https://img.shields.io/badge/Status-Final%20Submission%20Ready-brightgreen.svg)](#)
[![Official Test](https://img.shields.io/badge/Official%20Test-Evaluated%20(92.62%25%20Saving)-success.svg)](#)

Đồ án môn học **Nhập môn Tối ưu hóa** — Học kỳ 1, Năm học 2026–2027  
**Khoa Công nghệ Thông tin — Trường Đại học Văn Lang**  
**Sinh viên thực hiện:** Huỳnh Phúc  
**Mã nguồn Repository:** [PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)

---

## 1. TỔNG QUAN HỒ SƠ NỘP BÀI (FINAL SUBMISSION PACKAGE)

Toàn bộ các sản phẩm học thuật chính thức được đóng gói tại các đường dẫn sau:

| STT | Sản phẩm nộp bài | Định dạng | Quy mô / Trang | Đường dẫn tệp |
|:---:|---|:---:|:---:|---|
| 1 | **Báo cáo tổng kết đồ án (PDF)** | PDF | **9 trang** | [`report/BAO_CAO_CUOI_KY_SCANIA_APS.pdf`](report/BAO_CAO_CUOI_KY_SCANIA_APS.pdf) |
| 2 | **Báo cáo tổng kết đồ án (DOCX)** | Word | **9–10 trang** | [`report/BAO_CAO_CUOI_KY_SCANIA_APS.docx`](report/BAO_CAO_CUOI_KY_SCANIA_APS.docx) |
| 3 | **Slide thuyết trình bảo vệ (PDF)** | PDF | **8 slides** | [`slides/SLIDES_THUYET_TRINH_SCANIA_APS.pdf`](slides/SLIDES_THUYET_TRINH_SCANIA_APS.pdf) |
| 4 | **Slide thuyết trình bảo vệ (PPTX)** | PowerPoint | **8 slides** | [`slides/SLIDES_THUYET_TRINH_SCANIA_APS.pptx`](slides/SLIDES_THUYET_TRINH_SCANIA_APS.pptx) |
| 5 | **Đồ thị 1: Tiến trình hội tụ tối ưu** | PNG (300 DPI) | 2 bảng thu phóng | [`figures/optimization/optimization_convergence.png`](figures/optimization/optimization_convergence.png) |
| 6 | **Đồ thị 2: Đánh đổi Chi phí & Năng lực** | PNG (300 DPI) | Quét ngưỡng 101 điểm | [`figures/optimization/cost_vs_capacity_tradeoff.png`](figures/optimization/cost_vs_capacity_tradeoff.png) |
| 7 | **Bằng chứng tái lập khoa học** | Markdown | Đầy đủ mã băm SHA-256 | [`docs/reproducibility_evidence.md`](docs/reproducibility_evidence.md) |
| 8 | **Phân tích kết quả chuyên sâu** | Markdown | Chi tiết 20 trials | [`docs/results_analysis.md`](docs/results_analysis.md) |

---

## 2. TÓM TẮT BÀI TOÁN & KẾT QUẢ THỰC NGHIỆM ĐO ĐẠC

### 2.1. Phát biểu bài toán tối ưu hóa có ràng buộc
- **Bộ dữ liệu:** UCI Machine Learning Repository #421 (*APS Failure at Scania Trucks*, Scania CV AB, 2016).
  - Lớp dương ($y=1$): Xe vào xưởng hỏng do hệ thống khí nén APS ($1.67\%$).
  - Lớp âm ($y=0$): Xe vào xưởng do hỏng ở các **bộ phận KHÁC** ($98.33\%$).
- **Hàm mục tiêu chi phí benchmark phi đối xứng (IDA 2016):**
  $$\min_{\theta, \tau} \quad f(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \quad [\text{đơn vị chi phí benchmark}]$$
- **Ràng buộc công suất tiếp nhận của xưởng bảo dưỡng:**
  $$M(\theta, \tau) = TP + FP \le K = \left\lfloor \frac{N}{10} \right\rfloor = 1.200 \text{ lượt xe trên tập Validation } (N=12.000)$$

### 2.2. Bảng so sánh hiệu quả giữa các giai đoạn nghiên cứu

| Tiêu chí | G4 B0: Majority Dummy | G4 B1: Decision Stump | G4 B2: Logistic Regression | Phase 2: Random Forest + Optuna TPE |
|---|:---:|:---:|:---:|:---:|
| **Ngưỡng quyết định $\tau$** | N/A | $0.0196$ | $0.0196$ | $\mathbf{0.3232}$ |
| **True Positives (TP)** | $0$ | $160$ | $186$ | $\mathbf{195}$ / 200 ($Recall = 97.50\%$) |
| **False Positives (FP)** | $0$ | $253$ | $323$ | $383$ |
| **False Negatives (FN)** | $200$ | $40$ | $14$ | $\mathbf{5}$ (Chỉ lọt đúng 5 ca) |
| **Chi phí kiểm tra ($10 \times FP$)** | $0$ | $2.530$ | $3.230$ | $3.830$ |
| **Chi phí sự cố ($500 \times FN$)** | $100.000$ | $20.000$ | $7.000$ | $2.500$ |
| **Tổng chi phí benchmark** | **100.000** | **22.530** | **10.230** | $\mathbf{6.330}$ |
| **Số xe vào xưởng ($M \le 1200$)** | $0$ | $413$ | $509$ | **578** (Dư 622 chỗ) |
| **Trạng thái ràng buộc** | FEASIBLE | FEASIBLE | FEASIBLE | **FEASIBLE** |
| **Mức tiết kiệm vs B0 Dummy** | $0.00\%$ | $77.47\%$ | $89.77\%$ | $\mathbf{93.67\%}$ |
| **Mức giảm chi phí vs B2** | N/A | Tăng $+12.300$ | Mốc chuẩn G4 | **Giảm $-38.12\%$ ($-3.900$ đơn vị)** |

### 2.3. Kết quả đánh giá độc lập trên tập Official Test (Gate G10 — Run 003)

Sau khi đóng băng chính sách tối ưu tại Trial 16 ($\tau^* = 0.323244$, $K=1.600$), mô hình được đánh giá độc lập duy nhất một lần (single-pass, zero tuning) trên toàn bộ 16.000 mẫu tập Official Test theo đúng phê duyệt của Chủ dự án:

| Tiêu chí đánh giá | Đường cơ sở B0 (Mặc định) | Validation Guard (12.000 mẫu) | **Official Test Độc lập (16.000 mẫu)** |
|---|:---:|:---:|:---:|
| **Quy mô mẫu ($N$)** | 16.000 | 12.000 | **16.000** |
| **Số ca sự cố APS thực tế ($P$)** | 375 | 200 | **375** ($2.34\%$) |
| **True Positives (TP)** | 0 | 195 | **357** |
| **False Positives (FP)** | 0 | 383 | **484** |
| **False Negatives (FN)** | 375 | 5 | **18** |
| **True Negatives (TN)** | 15.625 | 11.417 | **15.141** |
| **Recall (Độ nhạy)** | 0.00% | 97.50% | **95.20%** ($357 / 375$) |
| **Precision (Độ chuẩn xác)** | N/A | 33.74% | **42.45%** ($357 / 841$) |
| **ROC-AUC / PR-AUC** | N/A | 0.9903 / 0.7059 | **0.9861 / 0.7495** |
| **Tổng chi phí benchmark** | **187.500** | **6.330** | **13.840** |
| **Chi phí trung bình / xe** | 11.719 | 0.528 | **0.865** |
| **Số xe vào xưởng ($M = TP + FP$)** | 0 | 578 | **841** (Giới hạn $K = 1.600$) |
| **Mức tiết kiệm chi phí vs B0** | 0.00% (Mốc chuẩn) | 93.67% | **92.62%** (Tiết kiệm 173.660 đơn vị) |

---

## 3. KHẢ NĂNG TÁI LẬP KHOA HỌC & KIỂM ĐỊNH

### 3.1. Xác thực tính toàn vẹn chữ ký số SHA-256 (Phase 2 Run 002)
```powershell
python -c "from src.scania.phase2_executor import verify_phase2_run; assert verify_phase2_run('results/scania_aps/phase2/scania_phase2_rf_optuna_002') == True; print('PASS: Run 002 verified!')"
```

### 3.2. Xác thực tính toàn vẹn chữ ký số Gate G10 (Official Test Run 003)
```powershell
python scripts/run_scania_g10.py verify
```

### 3.3. Chạy bộ kiểm thử tự động (Unit Tests)
```powershell
pytest tests/scania/test_phase2_optimization.py tests/scania/test_g10_evaluation.py -v
```

### 3.4. Tái tạo hai đồ thị thực nghiệm
```powershell
python -m scripts.run_scania_phase2 generate-figures --run-id scania_phase2_rf_optuna_002
```

---

## 4. RANH GIỚI KHOA HỌC & TÍNH TOÀN VẸN THỰC NGHIỆM

- **Đánh giá độc lập Official Test (16.000 mẫu):** Tập dữ liệu kiểm thử được giữ niêm phong tuyệt đối cho đến Gate G10. Việc đánh giá được thực hiện đúng 1 lần duy nhất với chính sách đóng băng, zero tuning, zero data leakage, đảm bảo tính khách quan khoa học 100%.
- **Bảo tồn các lần chạy sự cố:** Toàn bộ các lần chạy lỗi tiền kiểm tra G4 (`scania_g4_b2_real_001`), timeout Phase 2 (`scania_phase2_rf_optuna_001`), và sự cố I/O/import G10 (`scania_g10_official_test_001`, `002`) đều được lưu trữ đầy đủ kèm bản ghi pháp y `incident_forensic_note.json` theo chuẩn mực minh bạch khoa học.
- **Khai báo công cụ hỗ trợ AI:** Sử dụng Codex và Antigravity để hỗ trợ rà soát unit tests, runner script và định dạng tài liệu. Sinh viên tự xây dựng mô hình toán, kiểm chứng thực nghiệm và chịu trách nhiệm học thuật hoàn toàn.
