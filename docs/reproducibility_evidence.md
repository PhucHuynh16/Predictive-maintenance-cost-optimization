# BẰNG CHỨNG TÁI LẬP KHOA HỌC & DANH MỤC ARTIFACTS ĐÃ KIỂM CHỨNG (SCANIA APS UCI 421)

> **Dự án:** Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS (UCI 421)  
> **Học phần:** Nhập môn Tối ưu hóa — HK1, Năm học 2026–2027 (Đại học Văn Lang)  
> **Sinh viên:** Huỳnh Phúc  
> **Mã nguồn:** [GitHub PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)  
> **Trạng thái tập kiểm thử:** **Official Test (16.000 mẫu) ĐÃ ĐƯỢC ĐÁNH GIÁ ĐỘC LẬP TẠI G10 (Run `scania_g10_official_test_003`)** — Tiết kiệm **92.62%** chi phí, 0 lần tuning, thỏa mãn 100% ràng buộc.

---

## 1. MÔI TRƯỜNG THỰC THI & PHẦN CỨNG BẢO ĐẢM TÍNH TÁI LẬP

- **Hệ điều hành:** Microsoft Windows 11 Home (x64)
- **Phiên bản Python:** Python 3.11.9 (môi trường ảo độc lập `review_venv`)
- **Các thư viện cốt lõi:**
  - `scikit-learn`: 1.9.1
  - `optuna`: 5.0.0
  - `numpy`: 2.4.6
  - `scipy`: 1.17.1
  - `matplotlib`: 3.10.8
  - `reportlab`: 5.1.0
  - `python-docx`: 1.2.0
  - `python-pptx`: 1.0.2
- **Hạt giống ngẫu nhiên cố định (Fixed Seeds):**
  - Khóa `seed = 42` trên toàn bộ quy trình: phân chia Train/Validation, tiền xử lý, huấn luyện Random Forest và bộ lấy mẫu Optuna TPESampler.
- **Giới hạn tài nguyên hệ điều hành qua Windows Job Object:**
  - Luồng tính toán bản địa: `max_native_threads = 1` (kiểm soát qua `threadpoolctl`).
  - Trần bộ nhớ: `max_ram_mb = 2048 MB`.
  - Giới hạn thời gian (Wall-clock timeout): 900 giây.

---

## 2. DỮ LIỆU ĐÃ KHÓA & BẰNG CHỨNG G3 (DATA PROVENANCE)

- **Dataset:** UCI Machine Learning Repository #421 (*APS Failure at Scania Trucks*, Scania CV AB, 2016).
- **Mã băm G3 Stable Manifest:** `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`
- **Quy mô phân vùng:**
  - **Tập Train:** 48.000 mẫu ($800$ ca dương tính $1.67\%$, $47.200$ ca âm tính).
  - **Tập Validation:** 12.000 mẫu ($200$ ca dương tính $1.67\%$, $11.800$ ca âm tính).
  - Hai phân vùng hoàn toàn tách biệt: $\text{Train} \cap \text{Validation} = \emptyset$.
- **Tập Official Test (16.000 mẫu):**
  - Được giữ niêm phong độc lập trong suốt quá trình tối ưu hóa Phase 2; mở đánh giá độc lập duy nhất một lần tại Gate G10 (Run 003, zero tuning).
  - Minh bạch truy cập: Ở các lượt chạy thử nghiệm gián đoạn trước đó (Run 001/002), tệp CSV kiểm thử được đọc vào bộ nhớ nhưng tiến trình bị dừng ngay lập tức do cơ chế bảo vệ preprocessor trước khi có bất kỳ suy diễn dự đoán hay tinh chỉnh nào diễn ra.

---

## 3. BẢNG TỔNG HỢP KẾT QUẢ THỰC NGHIỆM ĐÃ XÁC THỰC

### 3.1. So sánh tổng quan qua các giai đoạn

| Tiêu chí | G4 B0: Majority Dummy | G4 B1: Decision Stump | G4 B2: Logistic Regression | Phase 2: Random Forest + Optuna TPE |
|---|:---:|:---:|:---:|:---:|
| **Run ID** | `scania_g4_b2_real_002` | `scania_g4_b2_real_002` | `scania_g4_b2_real_002` | `scania_phase2_rf_optuna_002` |
| **Ngưỡng quyết định $\tau$** | N/A | $0.0196$ | $0.0196$ | $\mathbf{0.3232}$ |
| **True Positives (TP)** | $0$ | $160$ | $186$ | $\mathbf{195}$ / 200 ($97.50\%$) |
| **False Positives (FP)** | $0$ | $253$ | $323$ | $383$ |
| **False Negatives (FN)** | $200$ | $40$ | $14$ | $\mathbf{5}$ |
| **True Negatives (TN)** | $11.800$ | $11.547$ | $11.477$ | $11.417$ |
| **Chi phí kiểm tra ($10 \times FP$)** | $0$ | $2.530$ | $3.230$ | $3.830$ |
| **Chi phí sự cố ($500 \times FN$)** | $100.000$ | $20.000$ | $7.000$ | $2.500$ |
| **Tổng chi phí benchmark** | **100.000** | **22.530** | **10.230** | $\mathbf{6.330}$ |
| **Số xe vào xưởng ($M \le 1200$)** | $0$ | $413$ | $509$ | **578** (Dư 622 chỗ) |
| **Trạng thái ràng buộc** | FEASIBLE | FEASIBLE | FEASIBLE | **FEASIBLE** |
| **Mức tiết kiệm vs B0 Dummy** | $0.00\%$ | $77.47\%$ | $89.77\%$ | $\mathbf{93.67\%}$ |
| **Mức giảm chi phí vs B2** | N/A | Tăng $+12.300$ | Mốc chuẩn G4 | **Giảm $-38.12\%$ ($-3.900$ đơn vị)** |

### 3.2. Kết quả nghiệm thu độc lập Gate G10 trên tập Official Test (Run 003)

| Tiêu chí | Đường cơ sở B0 (Không can thiệp) | Validation Guard (Trial 16) | **Official Test Độc lập (Run 003)** |
|---|:---:|:---:|:---:|
| **Quy mô mẫu ($N$)** | 16.000 | 12.000 | **16.000** |
| **Số ca lỗi APS thực tế ($P$)** | 375 | 200 | **375** ($2.34\%$) |
| **True Positives (TP)** | 0 | 195 | **357** |
| **False Positives (FP)** | 0 | 383 | **484** |
| **False Negatives (FN)** | 375 | 5 | **18** |
| **True Negatives (TN)** | 15.625 | 11.417 | **15.141** |
| **Độ nhạy (Recall)** | 0.00% | 97.50% | **95.20%** ($357/375$) |
| **Độ chính xác (Precision)** | N/A | 33.74% | **42.45%** ($357/841$) |
| **Độ đặc hiệu (Specificity)** | 100.00% | 96.75% | **96.90%** ($15.141/15.625$) |
| **F1-Score** | 0.0000 | 0.5013 | **0.5872** |
| **ROC-AUC / PR-AUC** | N/A | 0.9903 / 0.7059 | **0.9861 / 0.7495** |
| **Tổng chi phí benchmark** | **187.500** | **6.330** | **13.840** |
| **Lượt xe vào xưởng ($M \le 1600$)** | 0 | 578 | **841** (FEASIBLE, dư 759 chỗ) |
| **Mức tiết kiệm chi phí vs B0** | 0.00% (Mốc chuẩn) | 93.67% | **92.62%** (Tiết kiệm 173.660 đơn vị) |

> **Lưu ý khoa học về hàm chi phí benchmark:** Hàm mục tiêu $10 \cdot FP + 500 \cdot FN$ là quy ước chuẩn tắc tĩnh của bài toán benchmark Scania IDA 2016. Khi triển khai thực tế trên đội xe vận tải công nghiệp, các yếu tố biến động động như chi phí nhân công theo ca, tính sẵn có của phụ tùng thay thế, thời gian xe nằm xưởng (downtime), và chi phí cứu hộ đường dài theo cự ly sẽ cần được mô hình hóa bổ sung.

---

## 4. CHI TIẾT 20 TRIALS CỦA RUN `scania_phase2_rf_optuna_002`

Dữ liệu trích xuất từ file gốc `results/scania_aps/phase2/scania_phase2_rf_optuna_002/trials_summary.csv`:

| Trial | $n_{\text{est}}$ | depth | split | feat | Ngưỡng $\tau^*$ | Chi phí | $M \le 1200$ | TP | FP | FN | TN | Recall | Precision | Trạng thái |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | 30 | 12 | 8 | 0.380 | 0.2588 | 7.840 | 576 | 192 | 384 | 8 | 11.416 | 96.00% | 33.33% | FEASIBLE |
| 1 | 20 | 5 | 2 | 0.460 | 0.4363 | 7.790 | 724 | 195 | 529 | 5 | 11.271 | 97.50% | 26.93% | FEASIBLE |
| 2 | 50 | 10 | 2 | 0.491 | 0.3154 | 6.750 | 569 | 194 | 375 | 6 | 11.425 | 97.00% | 34.09% | FEASIBLE |
| 3 | 60 | 5 | 3 | 0.255 | 0.5201 | 7.880 | 682 | 194 | 488 | 6 | 11.312 | 97.00% | 28.45% | FEASIBLE |
| 4 | 30 | 8 | 5 | 0.287 | 0.3978 | 7.800 | 572 | 192 | 380 | 8 | 11.420 | 96.00% | 33.57% | FEASIBLE |
| 5 | 50 | 5 | 4 | 0.310 | 0.5609 | 7.310 | 625 | 194 | 431 | 6 | 11.369 | 97.00% | 31.04% | FEASIBLE |
| 6 | 40 | 11 | 3 | 0.354 | 0.2417 | 6.490 | 594 | 195 | 399 | 5 | 11.401 | 97.50% | 32.83% | FEASIBLE |
| 7 | 40 | 4 | 7 | 0.251 | 0.5887 | 7.520 | 697 | 195 | 502 | 5 | 11.298 | 97.50% | 27.98% | FEASIBLE |
| 8 | 20 | 12 | 10 | 0.443 | 0.1801 | 6.970 | 693 | 196 | 497 | 4 | 11.303 | 98.00% | 28.28% | FEASIBLE |
| 9 | 30 | 4 | 8 | 0.332 | 0.5696 | 7.540 | 699 | 195 | 504 | 5 | 11.296 | 97.50% | 27.90% | FEASIBLE |
| 10 | 60 | 12 | 7 | 0.433 | 0.2408 | 6.340 | 579 | 195 | 384 | 5 | 11.416 | 97.50% | 33.68% | FEASIBLE |
| 11 | 50 | 11 | 4 | 0.388 | 0.1739 | 6.790 | 675 | 196 | 479 | 4 | 11.321 | 98.00% | 29.04% | FEASIBLE |
| 12 | 60 | 12 | 7 | 0.435 | 0.2261 | 7.060 | 600 | 194 | 406 | 6 | 11.394 | 97.00% | 32.33% | FEASIBLE |
| 13 | 20 | 10 | 2 | 0.484 | 0.2428 | 6.880 | 633 | 195 | 438 | 5 | 11.362 | 97.50% | 30.81% | FEASIBLE |
| 14 | 40 | 12 | 6 | 0.500 | 0.2200 | 7.280 | 622 | 194 | 428 | 6 | 11.372 | 97.00% | 31.19% | FEASIBLE |
| 15 | 60 | 8 | 7 | 0.370 | 0.3268 | 6.890 | 634 | 195 | 439 | 5 | 11.361 | 97.50% | 30.76% | FEASIBLE |
| **16** | **50** | **10** | **10** | **0.427** | **0.3232** | **6.330** | **578** | **195** | **383** | **5** | **11.417** | **97.50%** | **33.74%** | **FEASIBLE (BEST)** |
| 17 | 60 | 10 | 8 | 0.441 | 0.2858 | 6.650 | 610 | 195 | 415 | 5 | 11.385 | 97.50% | 31.97% | FEASIBLE |
| 18 | 50 | 9 | 9 | 0.497 | 0.2589 | 7.070 | 652 | 195 | 457 | 5 | 11.343 | 97.50% | 29.91% | FEASIBLE |
| 19 | 50 | 11 | 10 | 0.440 | 0.2392 | 7.240 | 618 | 194 | 424 | 6 | 11.376 | 97.00% | 31.39% | FEASIBLE |

---

## 5. MÃ BĂM MẬT MÃ HỌC SHA-256 CỦA CÁC ARTIFACTS THỰC NGHIỆM

Toàn bộ 12 artifacts tại `results/scania_aps/phase2/scania_phase2_rf_optuna_002/` khớp chính xác chữ ký mã hóa SHA-256 LF-normalized:

```json
{
  "allowlist.json": "fccc31e9d1870c737e90637bb274d3860669f18473ea4a267fc72f6902fe9af5",
  "best_policy.json": "182771635c4217858b3e1dcdc3bf657b03c214f2f110d7b82f89b64cfeb8df9c",
  "config.json": "b7de45a559a3f8e6eec4fd363426f4dc54870090e3a02bc224863b4d34fd57e5",
  "environment.json": "36d260232a7921910660e89c34d4be66255cd97c26659f9c45d5eea81ef10733",
  "execution.txt": "971dfc6f267d90e3cf023b6a29c26ead266868b0344b1453a767e5dace497c36",
  "failure_diagnostics.json": "8120fe1b6e9aa232ce6f414343ef61c788a648d5e85a7fc84cf718240d54210a",
  "optuna_study.json": "6d96de1465e4ea9f99602ec7a0b19afe2eafe753f5cae62fa657b68305c92bf6",
  "run_summary.json": "3c9baf79369cdbb91d6f9cde6106ae7cc89780d44c4130b1111e0e6351a74e4b",
  "stable_manifest.json": "fba71cf80babcd45ec897e2dd2cb9d5c52aeabac96391ae568a82eef4097a6b7",
  "task_config.json": "e8268e61eb535d2ab8c15098b7f57738851f0710d41191c6bf9cd3172270750f",
  "trials_summary.csv": "cd8377a83241e600f48db89bbe13d3564de83c478a1447759bfd244a45f0269a",
  "worker_result.json": "bbd3631bf56dc8673aeb8ee52952c6b1fa625cbc67a05f057dc26eda174a4755"
}
```

### 5.2. Chữ ký băm mật mã học Gate G10 (Official Test Run 003)

Toàn bộ 9 artifacts tại `results/scania_aps/g10/scania_g10_official_test_003/` khớp chính xác chữ ký mã hóa SHA-256 LF-normalized:

```json
{
  "allowlist.json": "b4ca16e1e50d4f919e27b67ce1b3738300320b520688b806f09dc91135248ad5",
  "best_policy.json": "f950e08d55971d6ced163ae63e731ac090e5bb2999d5aa7b2febeb1eaf20e051",
  "confusion_matrix_test.csv": "2db1fef9f2895166b41072cd4c1bd43a7b026e95672ae94fc43925794e1b5a6a",
  "durable_fits/fit_001_COMPLETED.json": "c192b81ba3b537faa6f8a38cc1e1db346b3f39703531b9c6eba794239c7909aa",
  "durable_fits/fit_001_STARTED.json": "fc735bb54e2612ac22eeaa4340d00fa9a33908d421336cff2b0d981536cbcff7",
  "run_summary.json": "09f84ed4a1f787bbd28accac8da30596cc11d3ed04a83e36411dab5c38a70516",
  "task_config.json": "d7677777c5cc65966c668bcc8fbccc2e7e036e862b69c483a19cce54654a984c",
  "test_metrics.json": "53e06202f6d944944b2401fb593acc81cdd6a0b12ec20cb702ed37d45522bc1a",
  "validation_guard_metrics.json": "0c7310e0f94ef3d1ae200e1c31090aedfde59c5aefe710df2dc67d84a709b1c3"
}
```

---

## 6. HƯỚNG DẪN KIỂM CHỨNG & TÁI LẬP (REPRODUCTION COMMANDS)

### 6.1. Kiểm chứng chữ ký số và tính toàn vẹn của Run 002:
```powershell
python -c "
from src.scania.phase2_executor import verify_phase2_run
assert verify_phase2_run('results/scania_aps/phase2/scania_phase2_rf_optuna_002') == True
print('VERIFICATION SUCCESS: All 12 artifacts match SHA-256 checksums!')
"
```

### 6.2. Kiểm chứng tính toàn vẹn Gate G10 Official Test (Run 003):
```powershell
python scripts/run_scania_g10.py verify
```

### 6.3. Kiểm thử tự động bộ test suite (Phase 2 + G10):
```powershell
pytest tests/scania/test_phase2_optimization.py tests/scania/test_g10_evaluation.py -v
```

### 6.4. Tái tạo 02 đồ thị từ dữ liệu đã nghiệm thu:
```powershell
python -m scripts.run_scania_phase2 generate-figures --run-id scania_phase2_rf_optuna_002
```
Đồ thị đầu ra được lưu tại:
- `figures/optimization/optimization_convergence.png`
- `figures/optimization/cost_vs_capacity_tradeoff.png`
