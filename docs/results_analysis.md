# BÁO CÁO PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM G4 BASELINES (SCANIA APS UCI 421)

**Dự án:** Predictive Maintenance Cost Optimization — Scania APS Trucks (UCI 421)  
**Phân vùng dữ liệu:** Validation 12.000 mẫu (200 ca dương tính $y=1$, 11.800 ca âm tính $y=0$)  
**Giao thức G3:** Khóa cố định theo manifest digest `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`  
**Giao thức G4:** Fail-closed baseline gate (B0, B1, B2)  
**Tập Official Test (16.000 mẫu):** **ĐÃ ĐƯỢC MỞ VÀ ĐÁNH GIÁ ĐỘC LẬP TẠI G10 (Run `scania_g10_official_test_003`, Tiết kiệm 92.62% chi phí)**  
**Trạng thái nghiệm thu:** Đã nghiệm thu toàn diện G4 Baselines, Phase 2 Constrained Optimization, và G10 Official Test Evaluation bằng chữ ký băm SHA-256.

---

## 1. TỔNG QUAN PHÂN BIỆT RANH GIỚI KHOA HỌC

1. **Kết quả đo đạc trên phân vùng Validation (Validation Policy Results):**
   - Số liệu trong báo cáo này được đo đạc trực tiếp trên 12.000 mẫu Validation tĩnh lịch sử từ bộ dữ liệu UCI 421 sau khi huấn luyện trên 48.000 mẫu Train.
   - Đây là sự mô phỏng chính sách (policy simulation) nhằm phục vụ so sánh khách quan giữa các mô hình đường cơ sở và làm mốc đối chiếu cho thuật toán tối ưu hóa.
   - **Ranh giới học thuật:** Kết quả trên tập Validation này phản ánh hiệu năng nội bộ của quy trình thử nghiệm, phân biệt rõ với bước nghiệm thu độc lập cuối cùng của môn học và chưa bao gồm đánh giá trên tập Official Test (vốn được niêm phong tới G10).
2. **Quy định về tỷ lệ tiết kiệm chi phí (`saving_pct`):**
   - Mức tiết kiệm chi phí so với đường cơ sở mặc định B0 ($100.000$ đơn vị chi phí) được định lượng theo giá trị dương:
     - Chính sách P3 (B1 tại $\tau = 0.0196$): Tiết kiệm **$77.47\%$** chi phí benchmark.
     - Chính sách P4 (B2 tại $\tau = 0.5000$): Tiết kiệm **$64.02\%$** chi phí benchmark.
     - Chính sách P5 (B2 tại $\tau = 0.0196$): Tiết kiệm **$89.77\%$** chi phí benchmark.

---

## 2. BẢNG SỐ LIỆU ĐO ĐẠC CHÍNH THỨC 5 CHÍNH SÁCH VALIDATION

Số liệu trích xuất trực tiếp từ artifact đã niêm phong `results/scania_aps/g4/scania_g4_b2_real_002/baseline_metrics.json` và `baseline_metrics.csv`:

| Chính sách | Mô hình | Cấu hình | Ngưỡng $\tau$ | TP | FP | TN | FN | Precision | Recall | F1 | ROC-AUC | PR-AUC | Tổng chi phí benchmark | Chi phí / xe | Số xe vào xưởng ($M$) | Ràng buộc ($M \le 1200$) | Mức tiết kiệm vs B0 |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | **B0** | Majority Dummy | N/A | 0 | 0 | 11.800 | 200 | N/A | 0.00% | 0.0000 | N/A | N/A | **100.000** | 8.333 | 0 | **FEASIBLE** | 0.00% (Mốc chuẩn) |
| **P2** | **B1** | Decision Stump | 0.5000 | 0 | 0 | 11.800 | 200 | N/A | 0.00% | 0.0000 | 0.8893 | 0.3133 | **100.000** | 8.333 | 0 | **FEASIBLE** | 0.00% |
| **P3** | **B1** | Decision Stump | 0.0196 | 160 | 253 | 11.547 | 40 | 38.74% | 80.00% | 0.5220 | 0.8893 | 0.3133 | **22.530** | 1.878 | 413 | **FEASIBLE** | **77.47%** |
| **P4** | **B2** | Logistic Regression | 0.5000 | 129 | 48 | 11.752 | 71 | 72.88% | 64.50% | 0.6844 | 0.9825 | 0.7558 | **35.980** | 2.998 | 177 | **FEASIBLE** | **64.02%** |
| **P5** | **B2** | Logistic Regression | 0.0196 | 186 | 323 | 11.477 | 14 | 36.54% | 93.00% | 0.5247 | 0.9825 | 0.7558 | **10.230** | 0.853 | 509 | **FEASIBLE** | **89.77%** |

*Ghi chú công thức chi phí:* $\text{Cost} = 10 \cdot FP + 500 \cdot FN$ [đơn vị chi phí benchmark].

---

## 3. PHÂN TÍCH KHOA HỌC & ĐÁNH GIÁ CHÍNH SÁCH

### 3.1. So sánh đánh đổi giữa Ngưỡng Chuẩn ($\tau = 0.5$) và Ngưỡng Bayes Lý thuyết ($\tau = 10/510 \approx 0.0196$)
- **Tại $\tau = 0.5000$:**
  - Mô hình B1 dự đoán toàn bộ xác suất dưới $0.5$ do cấu trúc cây 1 tầng không gán lá nào có xác suất $> 0.5$, dẫn đến hành vi tương đương B0 ($TP=0, FN=200, \text{Cost}=100.000$).
  - Mô hình B2 có độ chính xác rất cao ($Precision = 72.88\%$, chỉ 48 ca kiểm tra thừa), nhưng bỏ sót tới 71 ca hư hỏng nặng ($FN=71$), khiến chi phí sự cố dọc đường chiếm tới $35.500 / 35.980$ ($98.7\%$).
- **Tại $\tau = 10/510 \approx 0.0196$:**
  - Cả hai mô hình đều giảm chi phí đột phá: B1 giảm $77.47\%$, B2 giảm $89.77\%$.
  - Mô hình B2 chỉ để lọt 14 ca hư hỏng ($Recall = 93.0\%$), ngăn chặn $186/200$ ca chết máy dọc đường, đánh đổi lại bằng 323 lượt kiểm tra thừa tại xưởng ($FP=323 \times 10 = 3.230$).

### 3.2. Đánh giá tính khả thi theo Ràng buộc Năng lực Xưởng ($M \le 1200$)
- Giới hạn kịch bản công suất tối đa trên phân vùng Validation là $K = \lfloor 12000 / 10 \rfloor = 1.200$ lượt xe.
- Số lượng xe cần đưa vào kiểm tra thực tế:
  - B1 tại $\tau = 0.0196$: $M = 160 + 253 = 413$ xe ($3.44\%$ quy mô tập dữ liệu, dư công suất $787$ xe).
  - B2 tại $\tau = 0.0196$: $M = 186 + 323 = 509$ xe ($4.24\%$ quy mô tập dữ liệu, dư công suất $691$ xe).
- **Kết luận khả thi:** Cả 5 chính sách đều đạt trạng thái **FEASIBLE** ($M \le 1200$). Trên tập Validation Scania, việc hạ ngưỡng xuống mức lý thuyết Bayes $\tau = 0.0196$ không làm vi phạm giới hạn tiếp nhận của xưởng bảo dưỡng.

---

## 4. ĐO LƯỜNG TÀI NGUYÊN & TÍNH TÁI LẬP (REPRODUCIBILITY TELEMETRY)

Dữ liệu đo đạc trực tiếp từ Windows Job Object và supervisor:
- **Số lượt fit thực tế (`real_estimator_fits`):** 2 lượt (B0=0, B1=1, B2=1; đúng ngân sách).
- **Đỉnh tiêu thụ RAM (`measured_peak_ram_mb`):** **201.90 MB** (Giới hạn: 2048 MB).
- **Kiểm soát luồng CPU:** Cố định 1 native thread (`threadpoolctl`).
- **Thời gian chi tiết:**
  - B0 dự báo: $0.00025$ giây.
  - B1 huấn luyện: $0.4397$ giây; dự báo: $0.0070$ giây.
  - B2 huấn luyện: $0.9775$ giây; dự báo: $0.0069$ giây.
  - Tổng thời gian fit mô hình: **$1.4171$ giây**.
  - Tổng thời gian toàn bộ tiến trình: **$6.06$ giây**.

---

## 5. BẢO TỒN DỮ LIỆU SỰ CỐ TIỀN KIỂM (RUN 001)

Theo nguyên tắc liêm chính học thuật, lần chạy thất bại tiền kiểm tra `scania_g4_b2_real_001` được bảo tồn nguyên trạng tại `results/scania_aps/g4/scania_g4_b2_real_001/`:
- **Nguyên nhân:** Lỗi `PackageNotFoundError` đối với `pytest` tại bước tiền kiểm tra môi trường supervisor (do lệnh gọi trỏ tới Python mặc định của hệ điều hành thay vì virtual environment).
- **Tình trạng fit:** 0 lượt fit thực hiện, Validation chưa chấm điểm, Official Test không bị xâm phạm.
- **Tệp chứng cứ lưu trữ:** `checksums.json`, `execution.txt`, `failure_diagnostics.json`, `run_summary.json`.

---

## 6. DANH MỤC & CHỮ KÝ BĂM SHA-256 CỦA CÁC ARTIFACT CHÍNH THỨC (RUN 002)

Toàn bộ 11 artifacts tại thư mục `results/scania_aps/g4/scania_g4_b2_real_002/` đã được kiểm chứng độc lập (`verify_run() == True`):

| Tên tệp artifact | Kích thước (bytes) | Chữ ký băm SHA-256 (LF-normalized) | Mô tả nội dung |
|---|:---:|---|---|
| `allowlist.json` | 1.059 | `ce4708b78b73bae08f087a40aa8336bca0ea01983298f2ab3219d7b265f059a5` | Danh mục đường dẫn dữ liệu được phép đọc |
| `baseline_metrics.csv` | 1.537 | `8ca68da003385f4389f8448a77f286b65ba7fb9d07a3a4a1b54558f6604d39fd` | Bảng số liệu chi tiết 5 dòng chính sách |
| `baseline_metrics.json` | 3.314 | `5eb264dadb9cd5f6605b5209283f8107a64f8e9878ce876f3c9d464c13ff9559` | Dữ liệu cấu trúc 5 chính sách và ma trận |
| `config.json` | 1.743 | `8b9cbbd2a14d23f256a677fc6a61eecf7dbf7c6261c78529670cbfddc00b88ad` | Cấu hình siêu tham số baselines |
| `environment.json` | 318 | `eaaa90e7f26a909578cee5810279a88e101326964a435fae416725cbdda7111b` | Môi trường hệ điều hành và thư viện khóa |
| `execution.txt` | 73 | `8e182c1077e4d5d94fd24d620341eec0a288483150343e3bea2606e36aa6519f` | Nhật ký thực thi hoàn tất thành công |
| `failure_diagnostics.json` | 14 | `4d7fb62d182e64d98296af95ffed7ef7a9b9c8c815c7466ac9fc4d953c021063` | Danh sách lỗi rỗng (`errors: []`) |
| `run_summary.json` | 3.932 | `af4a69aa3ca4350a86cb67b81f6ae5da5c9543f47e0d9e048e135cd05dd175f2` | Báo cáo tóm tắt thực nghiệm toàn diện |
| `stable_manifest.json` | 406 | `ab6fb33cb233c4329415c92de9cd3dfd0e474fae126a503f6e9fef6e32858b9e` | Niêm phong digest và ranh giới Test set |
| `task_config.json` | 1.668 | `6c536868f1a0d880669800bf2b5a97eefe403733d3f34e33e6b26dfc2dc0463a` | Cấu hình giao việc worker |
| `worker_result.json` | 6.354 | `f25fc7feea617b91593db5316f2e44fb20bb5081ae0a945dacb480ee558f7e03` | Kết quả chi tiết từ tiến trình con |

---

## 7. MỐC ĐỐI CHIẾU CHO PHASE 2 (BENCHMARK THAM CHIẾU)

Mốc chi phí benchmark tốt nhất đạt được trong G4 là:
$$\mathbf{C^*_{\text{G4}} = 10.230 \quad [\text{Mô hình B2 (Logistic Regression), } \tau = 10/510]}$$
Đây là mốc chuẩn đối chiếu cho giai đoạn tối ưu hóa cốt lõi Phase 2 (Random Forest + Optuna TPE).
*Lưu ý khoa học:* Thuật toán tối ưu hóa Random Forest không bắt buộc phải đánh bại mốc 10.230 này để được chấp nhận về mặt học thuật; nếu không vượt qua, đề tài sẽ phân tích nguyên nhân khoa học và biện minh cho quyết định lựa chọn mô hình cuối cùng dựa trên bằng chứng thực tế.

---

## 8. KẾT QUẢ THỰC NGHIỆM TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RUN `scania_phase2_rf_optuna_002`)

### 8.1. Thông số xác thực run chính thức
- **Mã thực nghiệm (Target Run ID):** `scania_phase2_rf_optuna_002`
- **Căn cứ ủy quyền:** GitHub Issue #17 Comment ID `6720275906` (Chủ dự án PhucHuynh16 phê duyệt).
- **Mã commit HEAD:** `7a58c5b3e473cf4c8c1a677a2feed464e6bdc42b`
- **Mã băm cấu hình (Config SHA-256):** `df29dca49743a6d9e51bb5e0a08ec6b4b96e6527fc66192d45c8907032defc72`
- **Trạng thái thực thi:** `COMPLETE` (100% hoàn tất 20/20 trials, 0 lỗi, 0 gián đoạn).
- **Thời gian chạy thực tế:** `543.06` giây (nằm gọn trong trần 900 giây được phê duyệt).
- **Đỉnh tiêu thụ RAM:** `159.82` MB (nằm trong giới hạn 2048 MB).
- **Tập Official Test (16.000 mẫu):** **NIÊM PHONG TUYỆT ĐỐI (SEALED UNTIL G10)**.

### 8.2. So sánh chính sách khả thi tốt nhất quan sát được (Trial 16) với các đường cơ sở

| Tiêu chí / Mô hình | B0: Majority Dummy | B1: Decision Stump (P3) | B2: Logistic Regression (P5) | **Phase 2: Random Forest + Optuna (Trial 16)** |
|---|:---:|:---:|:---:|:---:|
| **Thuật toán / Chính sách** | Dự báo toàn bộ 0 | Cây 1 tầng ($\tau = 0.0196$) | Hồi quy Logistic ($\tau = 0.0196$) | **Random Forest ($\tau^* = 0.3232$)** |
| **Siêu tham số tối ưu** | N/A | Feature `aa_000` | $C=1.0, \text{penalty}=l2$ | **$n_{\text{est}}=50, \text{depth}=10, \text{split}=10, \text{feat}=0.427$** |
| **True Positives (TP)** | 0 | 160 | 186 | **195** / 200 ($Recall = 97.50\%$) |
| **False Positives (FP)** | 0 | 253 | 323 | **383** |
| **False Negatives (FN)** | 200 | 40 | 14 | **5** (Chỉ lọt 5 xe chết máy dọc đường) |
| **True Negatives (TN)** | 11.800 | 11.547 | 11.477 | **11.417** |
| **Chi phí kiểm tra xưởng ($10 \times FP$)** | 0 | 2.530 | 3.230 | **3.830** |
| **Chi phí sự cố dọc đường ($500 \times FN$)** | 100.000 | 20.000 | 7.000 | **2.500** |
| **Tổng chi phí benchmark** | **100.000** | **22.530** | **10.230** | **6.330** |
| **Chi phí trung bình / xe** | 8.333 | 1.878 | 0.853 | **0.528** |
| **Số xe vào xưởng ($M = TP + FP$)** | 0 | 413 | 509 | **578** (Giới hạn $K = 1.200$) |
| **Tính khả thi năng lực xưởng** | FEASIBLE | FEASIBLE | FEASIBLE | **FEASIBLE (Dư 622 chỗ trống)** |
| **Mức tiết kiệm chi phí vs B0** | 0.00% (Mốc chuẩn) | 77.47% | 89.77% | **93.67%** (Tiết kiệm 93.670 đơn vị) |
| **Cắt giảm chi phí thêm so với B2** | N/A | N/A | Mốc chuẩn G4 | **-38.12%** (Giảm thêm 3.900 đơn vị) |

### 8.3. Bảng tổng hợp chi tiết 20 Trials của Optuna TPE (Run 002)

| Trial # | Chi phí | $M$ | Ngưỡng $\tau^*$ | TP | FP | FN | $n_{\text{est}}$ | depth | split | feat | Thời gian fit (s) | Trạng thái |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | 7.840 | 576 | 0.2588 | 192 | 384 | 8 | 30 | 12 | 8 | 0.380 | 18.80 | FEASIBLE |
| 1 | 7.790 | 724 | 0.4363 | 195 | 529 | 5 | 20 | 5 | 2 | 0.460 | 7.00 | FEASIBLE |
| 2 | 6.750 | 569 | 0.3154 | 194 | 375 | 6 | 50 | 10 | 2 | 0.491 | 34.68 | FEASIBLE |
| 3 | 7.880 | 682 | 0.5201 | 194 | 488 | 6 | 60 | 5 | 3 | 0.255 | 11.76 | FEASIBLE |
| 4 | 7.800 | 572 | 0.3978 | 192 | 380 | 8 | 30 | 8 | 5 | 0.287 | 10.13 | FEASIBLE |
| 5 | 7.310 | 625 | 0.5609 | 194 | 431 | 6 | 50 | 5 | 4 | 0.310 | 11.73 | FEASIBLE |
| 6 | 6.490 | 594 | 0.2417 | 195 | 399 | 5 | 40 | 11 | 3 | 0.354 | 21.62 | FEASIBLE |
| 7 | 7.520 | 697 | 0.5887 | 195 | 502 | 5 | 40 | 4 | 7 | 0.251 | 6.21 | FEASIBLE |
| 8 | 6.970 | 693 | 0.1801 | 196 | 497 | 4 | 20 | 12 | 10 | 0.443 | 14.61 | FEASIBLE |
| 9 | 7.540 | 699 | 0.5696 | 195 | 504 | 5 | 30 | 4 | 8 | 0.332 | 6.14 | FEASIBLE |
| 10 | 6.340 | 579 | 0.2408 | 195 | 384 | 5 | 60 | 12 | 7 | 0.433 | 71.20 | FEASIBLE |
| 11 | 6.790 | 675 | 0.1739 | 196 | 479 | 4 | 50 | 11 | 4 | 0.388 | 32.75 | FEASIBLE |
| 12 | 7.060 | 600 | 0.2261 | 194 | 406 | 6 | 60 | 12 | 7 | 0.435 | 44.51 | FEASIBLE |
| 13 | 6.880 | 633 | 0.2428 | 195 | 438 | 5 | 20 | 10 | 2 | 0.484 | 14.20 | FEASIBLE |
| 14 | 7.280 | 622 | 0.2200 | 194 | 428 | 6 | 40 | 12 | 6 | 0.500 | 32.49 | FEASIBLE |
| 15 | 6.890 | 634 | 0.3268 | 195 | 439 | 5 | 60 | 8 | 7 | 0.370 | 27.30 | FEASIBLE |
| **16** | **6.330** | **578** | **0.3232** | **195** | **383** | **5** | **50** | **10** | **10** | **0.427** | **38.61** | **FEASIBLE (BEST)** |
| 17 | 6.650 | 610 | 0.2858 | 195 | 415 | 5 | 60 | 10 | 8 | 0.441 | 70.21 | FEASIBLE |
| 18 | 7.070 | 652 | 0.2589 | 195 | 457 | 5 | 50 | 9 | 9 | 0.497 | 31.83 | FEASIBLE |
| 19 | 7.240 | 618 | 0.2392 | 194 | 424 | 6 | 50 | 11 | 10 | 0.440 | 33.46 | FEASIBLE |

### 8.4. Đồ thị trực quan hóa thực nghiệm đã trích xuất
1. **Đường cong hội tụ tối ưu hóa:** `figures/optimization/optimization_convergence.png` — Minh họa trực quan 2 bảng: Toàn cảnh chi phí so với $B_0$ (100.000) và chi tiết quá trình hội tụ qua 20 trials, trong đó chi phí khả thi tốt nhất hạ dần từ 7.840 xuống 6.330 so với mốc cơ sở $B_2$ (10.230).
2. **Đường cong đánh đổi chi phí và năng lực xưởng:** `figures/optimization/cost_vs_capacity_tradeoff.png` — Minh họa đường quét thực nghiệm 101 điểm ngưỡng $\tau \in [0, 1]$ của Trial 16 (chính sách khả thi tốt nhất quan sát được) cùng phân bố của 20 trials trong vùng khả thi $M \le 1200$. Thể hiện rõ tính bất khả thi khi $\tau < 0.05$ ($M > 1200$) và điểm chi phí nhỏ nhất tại $\tau^* = 0.3232$.

### 8.5. Danh mục và mã băm SHA-256 các artifact chính thức (Run 002)
Toàn bộ 12 artifacts tại `results/scania_aps/phase2/scania_phase2_rf_optuna_002/` đã được xác thực mã hóa:
- `allowlist.json`: `fccc31e9d1870c737e90637bb274d3860669f18473ea4a267fc72f6902fe9af5`
- `best_policy.json`: `182771635c4217858b3e1dcdc3bf657b03c214f2f110d7b82f89b64cfeb8df9c`
- `config.json`: `b7de45a559a3f8e6eec4fd363426f4dc54870090e3a02bc224863b4d34fd57e5`
- `environment.json`: `36d260232a7921910660e89c34d4be66255cd97c26659f9c45d5eea81ef10733`
- `execution.txt`: `971dfc6f267d90e3cf023b6a29c26ead266868b0344b1453a767e5dace497c36`
- `failure_diagnostics.json`: `8120fe1b6e9aa232ce6f414343ef61c788a648d5e85a7fc84cf718240d54210a`
- `optuna_study.json`: `6d96de1465e4ea9f99602ec7a0b19afe2eafe753f5cae62fa657b68305c92bf6`
- `run_summary.json`: `3c9baf79369cdbb91d6f9cde6106ae7cc89780d44c4130b1111e0e6351a74e4b`
- `stable_manifest.json`: `fba71cf80babcd45ec897e2dd2cb9d5c52aeabac96391ae568a82eef4097a6b7`
- `task_config.json`: `e8268e61eb535d2ab8c15098b7f57738851f0710d41191c6bf9cd3172270750f`
- `trials_summary.csv`: `cd8377a83241e600f48db89bbe13d3564de83c478a1447759bfd244a45f0269a`
- `worker_result.json`: `bbd3631bf56dc8673aeb8ee52952c6b1fa625cbc67a05f057dc26eda174a4755`

---

## 9. KẾT QUẢ ĐÁNH GIÁ ĐỘC LẬP TRÊN TẬP KIỂM THỬ CHÍNH THỨC (GATE G10 — RUN `scania_g10_official_test_003`)

### 9.1. Thông số xác thực run chính thức Gate G10
- **Mã thực nghiệm (Target Run ID):** `scania_g10_official_test_003`
- **Căn cứ ủy quyền:** GitHub Issue #17 Comment ID `6730936638` (Chủ dự án PhucHuynh16 phê duyệt).
- **Mã commit HEAD:** `6dbc046c4a40bc11451db46664b91eae8b629d1e`
- **Mã băm cấu hình (Config SHA-256):** `ca85eb951ba425bf81f8b34de01498483c40d50b6ea295953acd58666dddf51c`
- **Chế độ đánh giá:** `DETERMINISTIC_TRAIN_REFIT_EVALUATION` (Đúng 1 lần huấn luyện tái lập trên 48.000 mẫu Train, 0 lần huấn luyện trên Test).
- **Validation Regression Guard:** **PASSED** (Tái lập bit-for-bit chính xác các chỉ số Trial 16: $TP=195, FP=383, FN=5, TN=11.417, \text{Cost}=6.330, M=578, \text{saving\_pct}=93.67\%$).
- **Thời gian huấn luyện refit:** `31.05` giây.
- **Thời gian suy luận Test:** `0.039` giây (cho toàn bộ 16.000 xe).
- **Quy mô tập Official Test:** 16.000 mẫu (375 ca dương tính $y=1$ chiếm 2.34%, 15.625 ca âm tính $y=0$ chiếm 97.66%).
- **Ràng buộc năng lực xưởng:** $K = 1.600$ xe (10% của 16.000 mẫu).

### 9.2. Bảng kết quả chính thức trên tập Official Test (So sánh Train-Validation-Test)

| Tiêu chí | Đường cơ sở B0 (Không can thiệp) | Validation Guard (Trial 16 — 12.000 mẫu) | **Official Test Độc lập (G10 — 16.000 mẫu)** |
|---|:---:|:---:|:---:|
| **Mô hình & Ngưỡng** | Mặc định lớp đa số | Random Forest ($\tau^* = 0.3232$) | **Random Forest ($\tau^* = 0.3232$, Frozen)** |
| **Quy mô mẫu ($N$)** | 16.000 | 12.000 | **16.000** |
| **Số ca lỗi thực tế ($P$)** | 375 | 200 | **375** (Tỷ lệ 2.34%) |
| **True Positives (TP)** | 0 | 195 | **357** |
| **False Positives (FP)** | 0 | 383 | **484** |
| **False Negatives (FN)** | 375 | 5 | **18** |
| **True Negatives (TN)** | 15.625 | 11.417 | **15.141** |
| **Recall (Độ nhạy)** | 0.00% | 97.50% | **95.20%** ($357 / 375$) |
| **Precision (Độ chuẩn xác)** | N/A | 33.74% | **42.45%** ($357 / 841$) |
| **Specificity (Độ đặc hiệu)** | 100.00% | 96.75% | **96.90%** ($15.141 / 15.625$) |
| **F1-Score** | 0.0000 | 0.5013 | **0.5872** |
| **ROC-AUC** | N/A | 0.9903 | **0.9861** |
| **PR-AUC** | N/A | 0.7059 | **0.7495** |
| **Chi phí kiểm tra ($10 \times FP$)** | 0 | 3.830 | **4.840** |
| **Chi phí chết máy ($500 \times FN$)** | 187.500 | 2.500 | **9.000** |
| **Tổng chi phí benchmark** | **187.500** | **6.330** | **13.840** |
| **Chi phí trung bình / xe** | 11.719 | 0.528 | **0.865** |
| **Số xe vào xưởng ($M = TP + FP$)** | 0 | 578 | **841** (Giới hạn $K = 1.600$) |
| **Tỷ lệ bảo dưỡng ($M / N$)** | 0.00% | 4.82% | **5.26%** |
| **Tính khả thi năng lực xưởng** | FEASIBLE | FEASIBLE | **FEASIBLE (Dư 759 chỗ trống)** |
| **Mức tiết kiệm chi phí vs B0** | 0.00% (Mốc chuẩn) | 93.67% | **92.62%** (Tiết kiệm 173.660 đơn vị) |

### 9.3. Nhận định khoa học về năng lực tổng quát hóa (Generalization Assessment)
1. **Khả năng tổng quát hóa xuất sắc:** Khi chuyển từ phân vùng Validation sang Official Test hoàn toàn độc lập, chính sách tối ưu vẫn duy trì mức cắt giảm chi phí ấn tượng **92.62%** (từ 187.500 đơn vị chi phí mặc định xuống chỉ còn 13.840 đơn vị chi phí).
2. **Bảo toàn tỷ lệ phát hiện hư hỏng (Recall 95.20%):** Ngăn chặn thành công 357 trên 375 sự cố chết máy dọc đường, chỉ lọt 18 trường hợp trong toàn bộ 16.000 xe.
3. **Cải thiện độ chuẩn xác (Precision tăng từ 33.74% lên 42.45%):** Do tỷ lệ mẫu dương tính trên tập Test thực tế (2.34%) cao hơn trên Train/Validation (1.67%), mật độ dự đoán đúng tăng lên mà không làm bùng nổ số lượng False Positives.
4. **Tuyệt đối thỏa mãn ràng buộc năng lực xưởng ($M = 841 \le 1600$):** Số lượng xe yêu cầu bảo dưỡng thực tế là 841 xe (5.26%), chỉ bằng hơn một nửa công suất tối đa cho phép của xưởng ($K = 1.600$), chứng minh tính khả thi thực tế cực kỳ vững chắc của chính sách.
5. **Minh bạch hóa các lần chạy trước:**
   - Run 001 (`scania_g10_official_test_001`): Chặn bởi I/O guard khi tải `tree_preprocessor.joblib`. Lưu giữ đầy đủ tại `results/scania_aps/g10/scania_g10_official_test_001/`.
   - Run 002 (`scania_g10_official_test_002`): Chặn bởi import guard `LATE_NUMERIC_IMPORT` khi unpickle `SimpleImputer`. Lưu giữ đầy đủ tại `results/scania_aps/g10/scania_g10_official_test_002/`.
   - Run 003 (`scania_g10_official_test_003`): Hoàn thành 100% đánh giá chính thức, được niêm phong mật mã học trong `stable_manifest.json`.

### 9.4. Danh mục và mã băm SHA-256 các artifact chính thức Gate G10 (Run 003)
Toàn bộ 9 artifacts tại `results/scania_aps/g10/scania_g10_official_test_003/` đã được kiểm chứng độc lập (`python scripts/run_scania_g10.py verify` -> PASS):
- `allowlist.json`: `b4ca16e1e50d4f919e27b67ce1b3738300320b520688b806f09dc91135248ad5`
- `best_policy.json`: `f950e08d55971d6ced163ae63e731ac090e5bb2999d5aa7b2febeb1eaf20e051`
- `confusion_matrix_test.csv`: `2db1fef9f2895166b41072cd4c1bd43a7b026e95672ae94fc43925794e1b5a6a`
- `durable_fits/fit_001_COMPLETED.json`: `c192b81ba3b537faa6f8a38cc1e1db346b3f39703531b9c6eba794239c7909aa`
- `durable_fits/fit_001_STARTED.json`: `fc735bb54e2612ac22eeaa4340d00fa9a33908d421336cff2b0d981536cbcff7`
- `run_summary.json`: `09f84ed4a1f787bbd28accac8da30596cc11d3ed04a83e36411dab5c38a70516`
- `task_config.json`: `d7677777c5cc65966c668bcc8fbccc2e7e036e862b69c483a19cce54654a984c`
- `test_metrics.json`: `53e06202f6d944944b2401fb593acc81cdd6a0b12ec20cb702ed37d45522bc1a`
- `validation_guard_metrics.json`: `0c7310e0f94ef3d1ae200e1c31090aedfde59c5aefe710df2dc67d84a709b1c3`
