# BÁO CÁO PHÂN TÍCH KẾT QUẢ THỰC NGHIỆM G4 BASELINES (SCANIA APS UCI 421)

**Dự án:** Predictive Maintenance Cost Optimization — Scania APS Trucks (UCI 421)  
**Phân vùng dữ liệu:** Validation 12.000 mẫu (200 ca dương tính $y=1$, 11.800 ca âm tính $y=0$)  
**Giao thức G3:** Khóa cố định theo manifest digest `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`  
**Giao thức G4:** Fail-closed baseline gate (B0, B1, B2)  
**Tập Official Test (16.000 mẫu):** **NIÊM PHONG TUYỆT ĐỐI (SEALED UNTIL G10)**  
**Trạng thái nghiệm thu:** Đã được kiểm chứng độc lập bằng `verify_run()` và mã băm SHA-256 (Run `scania_g4_b2_real_002`)

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
