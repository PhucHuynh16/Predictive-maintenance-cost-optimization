# BÁO CÁO KẾT QUẢ KIỂM TRA DỮ LIỆU & EDA — AI4I 2020

- **Nhiệm vụ:** W1-G2-A (Tuần 1 – Giai đoạn 2)
- **Tác giả phụ trách:** Antigravity (theo phân quyền `AGENTS.md`)
- **Ngày thực hiện:** 2026-10-21 (Asia/Saigon)
- **Môi trường thực thi:** Python 3.14.3 (Windows 64-bit), `pandas 3.0.2`, `numpy 2.4.4`, `scipy 1.17.1`, `scikit-learn 1.9.0`, `matplotlib 3.10.9`, `seaborn 0.13.2`.
- **Trạng thái:** Hoàn thành kiểm tra dữ liệu raw local, xác thực provenance và sinh biểu đồ EDA. Chưa mở nhãn test để tuning (tuân thủ protocol).

---

## 1. Nguồn Gốc Dữ Liệu & Provenance

### 1.1. Thông tin nguồn và tải về
- **Tên tập dữ liệu:** AI4I 2020 Predictive Maintenance Dataset
- **Nguồn:** UCI Machine Learning Repository
- **DOI:** [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C)
- **URL tải thực tế:** `https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip`
- **Thời điểm tải về:** 2026-10-21 07:31:29 UTC (14:31:29 Asia/Saigon).
- **Giấy phép bản quyền:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
- **Bài báo gốc tham chiếu:** Stephan Matzka, *"Explainable Artificial Intelligence for Predictive Maintenance Applications"*, 2020 Third International Conference on Artificial Intelligence for Industries (AI4I), 2020, pp. 69-74.

### 1.2. Xác thực tính toàn vẹn (Cryptographic Hashes)
- Tệp nén zip tải về: `ai4i2020.zip`
  - Kích thước: **522,170 bytes**
  - SHA-256: `f601f14294bcf190f9d720676b7f0aea46a26cde9ab8ebc7b4f8174d9d26b252`
- Tệp CSV giải nén: `data/raw/ai4i2020.csv`
  - Kích thước: **522,048 bytes**
  - SHA-256: `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`

Lệnh PowerShell kiểm tra:
```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\data\raw\ai4i2020.csv
```

---

## 2. Kiểm Tra Schema, Missing Values & Duplicates

1. **Kích thước quan sát được:**
   - 10,000 dòng dữ liệu, 14 cột.
2. **Giá trị khuyết thiếu (Missing / NaN / Inf):**
   - Đếm số lượng null trên toàn bộ 14 cột: **0 giá trị missing** (100% đầy đủ).
   - Không phát hiện giá trị chuỗi rỗng (`""`), `NaN`, hay giá trị vô cực (`inf`).
3. **Trùng lặp (Duplicates):**
   - Trùng lặp hoàn toàn 14 cột: **0 dòng**.
   - Trùng lặp trên tập đặc trưng (bỏ qua `UDI` và `Product ID`): **0 dòng**.
4. **Kiểm tra tính đơn nhất của định danh:**
   - Cột `UDI`: Đủ 10,000 giá trị nguyên liên tục từ 1 đến 10,000.
   - Cột `Product ID`: Đủ 10,000 giá trị duy nhất (unique). Ký tự đầu tiên của `Product ID` (`L`, `M`, `H`) khớp chính xác 100% với giá trị cột `Type`.

---

## 3. Khảo Sát Nhãn Mục Tiêu & 5 Chế Độ Hỏng Hóc Phụ

### 3.1. Phân bố nhãn mục tiêu (`Machine failure`)
- Lớp 0 (Bình thường / Không hỏng): **9,661 quan sát (96.61%)**
- Lớp 1 (Hỏng hóc máy): **339 quan sát (3.39%)**
- Tỷ lệ mất cân bằng: xấp xỉ **28.5 : 1**. Đây là bài toán mất cân bằng lớp nghiêm trọng (Severe Imbalance).

### 3.2. Số lượng quan sát của 5 chế độ hỏng hóc độc lập
- `TWF` (Tool Wear Failure): **46 ca** (0.46%)
- `HDF` (Heat Dissipation Failure): **115 ca** (1.15%)
- `PWF` (Power Failure): **95 ca** (0.95%)
- `OSF` (Overstrain Failure): **98 ca** (0.98%)
- `RNF` (Random Failure): **19 ca** (0.19%)
- Tổng số lượt hỏng theo các chế độ: $46 + 115 + 95 + 98 + 19 = 373$ lượt.

### 3.3. Phát hiện bất nhất (Inconsistencies) then chốt giữa Target và Sub-failures

Bảng chéo giữa `Machine failure` và cờ "Có ít nhất một nhãn phụ bật" (`any_sub_failure`):

| `Machine failure` | `any_sub_failure = 0` | `any_sub_failure = 1` | Tổng |
|:---:|:---:|:---:|:---:|
| **0 (Không hỏng)** | 9,643 | **18** | 9,661 |
| **1 (Hỏng hóc)** | **9** | 330 | 339 |
| **Tổng** | 9,652 | 348 | 10,000 |

#### Chi tiết 2 điểm bất thường:
1. **Có 9 quan sát có `Machine failure == 1` nhưng tất cả 5 nhãn phụ đều bằng 0:**
   - Danh sách UDI: `[1438, 2750, 4045, 4685, 5537, 5942, 6479, 8507, 9016]`.
   - Phân tích: Theo bài báo gốc của Stephan Matzka, các quan sát này có thể phản ánh sự cố tổng hợp không rơi chính xác vào ngưỡng của 5 chế độ vật lý riêng biệt hoặc là nhiễu sinh ra trong kịch bản tổng hợp.
2. **Có 18 quan sát có `RNF == 1` nhưng `Machine failure == 0`:**
   - Trong 19 ca `RNF == 1` của toàn bộ tập dữ liệu, có tới **18 ca** có `Machine failure == 0`!
   - Chỉ duy nhất 1 ca (UDI `3612`) có `Machine failure == 1`, và ca này đồng thời có cả `TWF == 1`.
   - Phân tích: Thiết kế của bài toán mô phỏng xem RNF là sự cố ngẫu nhiên làm gián đoạn chu kỳ gia công (process abortion) và công cụ được thay thế, nhưng máy không bị hỏng hóc nghiêm trọng dẫn đến gắn cờ `Machine failure = 1`.
3. **Hiện tượng đa hỏng hóc (Multi-failure):**
   - 23 quan sát xảy ra 2 lỗi đồng thời (chủ yếu là $PWF + OSF$ hoặc $HDF + PWF$).
   - 1 quan sát xảy ra 3 lỗi đồng thời (UDI `5910`: $TWF + PWF + OSF$).

> [!IMPORTANT]
> **Quy định đạo đức dữ liệu:** Tuyệt đối **KHÔNG ĐƯỢC TỰ Ý SỬA NHÃN** của 9 dòng hay 18 dòng nói trên. Toàn bộ các dòng dữ liệu này là thuộc tính nguyên bản của tập dữ liệu chuẩn UCI AI4I 2020. Mọi can thiệp sửa nhãn sẽ phá vỡ tính tái lập và vi phạm quy tắc liêm chính học thuật.

---

## 4. Phân Tích Phân Phối Đặc Trưng & Outliers

### 4.1. Bảng thống kê mô tả các đặc trưng số học
| Đặc trưng | Mean | Std | Min | 25% | Median | 75% | Max | Skewness |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `Air temperature [K]` | 300.00 | 2.00 | 295.30 | 298.30 | 300.10 | 301.50 | 304.50 | +0.11 |
| `Process temperature [K]` | 310.01 | 1.48 | 305.70 | 308.80 | 310.10 | 311.10 | 313.80 | +0.02 |
| `Rotational speed [rpm]` | 1538.78 | 179.28 | 1168.00 | 1423.00 | 1503.00 | 1612.00 | 2886.00 | **+1.99** |
| `Torque [Nm]` | 39.99 | 9.97 | 3.80 | 33.20 | 40.10 | 46.80 | 76.60 | -0.01 |
| `Tool wear [min]` | 107.95 | 63.65 | 0.00 | 53.00 | 108.00 | 162.00 | 253.00 | +0.03 |

### 4.2. Phân bố loại sản phẩm (`Type`) và tỷ lệ hỏng
- Loại **L (Low quality)**: 6,000 mẫu (60.0%) — Số ca hỏng: 235 — Tỷ lệ hỏng: **3.92%**
- Loại **M (Medium quality)**: 2,997 mẫu (29.97%) — Số ca hỏng: 83 — Tỷ lệ hỏng: **2.77%**
- Loại **H (High quality)**: 1,003 mẫu (10.03%) — Số ca hỏng: 21 — Tỷ lệ hỏng: **2.09%**
- **Nhận xét:** Cấp chất lượng cao hơn có tỷ lệ hỏng thấp hơn rõ rệt theo thứ tự đơn điệu ($L > M > H$).

### 4.3. Phân tích ngoại lai (Outliers) & Ý nghĩa miền nghiệp vụ
- **`Rotational speed [rpm]`**:
  - Cận trên IQR: 1,895.5 rpm.
  - Số điểm ngoại lai: **418 điểm** (4.18% toàn tập, skewness = 1.99).
  - Tỷ lệ hỏng trong nhóm ngoại lai: **8.37%** (cao gấp gần 2.5 lần mức trung bình toàn tập 3.39%).
- **`Torque [Nm]`**:
  - Cận IQR: $[12.80\text{ Nm}, 67.20\text{ Nm}]$.
  - Số điểm ngoại lai: **64 điểm** (0.64% toàn tập).
  - Tỷ lệ hỏng trong nhóm ngoại lai: **90.625%** (58 ca hỏng trên 64 quan sát)!
- **Đánh giá quyết định:** Các điểm ngoại lai này là **biểu hiện vật lý trực tiếp của các tình trạng quá tải hoặc mất điều tốc**, dẫn tới hỏng hóc máy móc. Tuyệt đối **không được xóa bỏ hoặc clipping/cắt tỉa** các giá trị này trong pipeline tiền xử lý, vì làm vậy sẽ triệt tiêu tín hiệu dự báo mạnh nhất của mô hình.

---

## 5. Xác Thực Cơ Chế Vật Lý Sinh Dữ Liệu (Physics-Based Rules)

Chúng tôi đã lập trình kiểm chứng lại toàn bộ 3 quy tắc vật lý được công bố trong bài báo của Stephan Matzka trên 10,000 dòng dữ liệu:

1. **Cơ chế HDF (Lỗi tản nhiệt):**
   $$\Delta T = T_{process} - T_{air} < 8.6\text{ K} \quad \text{VÀ} \quad v_{rot} < 1380\text{ rpm}$$
   - Kết quả kiểm chứng: **Khớp chính xác 100.00%** (115/115 ca).
2. **Cơ chế PWF (Lỗi công suất):**
   $$P = \text{Torque} \times \left( v_{rot} \times \frac{2\pi}{60} \right) < 3500\text{ W} \quad \text{HOẶC} \quad > 9000\text{ W}$$
   - Kết quả kiểm chứng: **Khớp chính xác 100.00%** (95/95 ca).
3. **Cơ chế OSF (Lỗi quá tải ứng suất):**
   $$\text{Tool wear} \times \text{Torque} > \theta_{\text{Type}} \quad (\theta_L = 11,000, \theta_M = 12,000, \theta_H = 13,000)$$
   - Kết quả kiểm chứng: **Khớp chính xác 100.00%** (98/98 ca).

---

## 6. Phân Tích Rủi Ro Rò Rỉ Dữ Liệu (Data Leakage) & Khuyến Nghị Chia Tập

### 6.1. Rủi ro rò rỉ từ các nhãn hỏng hóc phụ (`TWF`, `HDF`, `PWF`, `OSF`, `RNF`)
- Các cột này là **nguyên nhân chi tiết sau khi sự cố đã xảy ra**, không bao giờ có sẵn tại thời điểm dự báo vận hành.
- Nếu đưa bất kỳ cột nào trong số 5 cột này vào mô hình phân loại `Machine failure`, mô hình sẽ đạt độ chính xác ảo (Target Leakage) nhưng vô giá trị trong triển khai thực tế.
- **Khuyến nghị:** Cấm tuyệt đối đưa 5 cột này vào tập đặc trưng đầu vào.

### 6.2. Rủi ro rò rỉ từ chỉ số định danh (`UDI`, `Product ID`)
- `UDI` là chỉ số hàng tăng dần từ 1 đến 10,000.
- `Product ID` chứa hậu tố số tăng dần.
- **Khuyến nghị:** Cấm tuyệt đối sử dụng `UDI` và `Product ID` làm biến độc lập.

### 6.3. Rủi ro từ chu kỳ nhiệt & Cụm lỗi HDF theo thứ tự tuần tự
- Khi khảo sát chuỗi quan sát theo `UDI`:
  - `Air temperature` biến thiên tuần hoàn theo dạng sóng nhiệt mô phỏng nhiệt độ môi trường ngày/đêm hoặc mùa vụ.
  - Cụm nhiệt độ cao đỉnh điểm xuất hiện trong khoảng UDI từ 3000 đến 5000.
  - **108 trong tổng số 115 ca HDF nằm gọn trong khoảng UDI 4000–4999** (và 7 ca ở đoạn 3000–3999). Các khoảng UDI khác (0–2999 và 5000–10000) có **0 ca HDF**.
- **Cảnh báo nghiêm trọng đối với Data Splitting:**
  - Nếu chia tập theo thứ tự thời gian tuần tự (ví dụ: Train = 0–6000, Val = 6000–8000, Test = 8000–10000): Tập Test sẽ chứa **0 ca HDF nào**! Khi đó mô hình sẽ không được đánh giá khả năng phát hiện lỗi tản nhiệt trên tập test.
  - **Khuyến nghị cho Codex (Nhiệm vụ W2-G3-C):** Cần sử dụng **Stratified Random Split** (ví dụ tỷ lệ 60% Train, 20% Validation, 20% Test, phân tầng theo nhãn `Machine failure`, với seed cố định là 42) để đảm bảo phân bổ đều các chế độ lỗi trên cả 3 tập, đồng thời giữ bí mật tuyệt đối tập test cho đến giai đoạn đánh giá cuối cùng.

---

## 7. Danh Mục Biểu Đồ Đã Tạo Thực Tế

Toàn bộ biểu đồ đã được sinh từ dữ liệu thật và lưu tại thư mục `figures/eda/`:
1. `figures/eda/01_target_distribution.png`: Phân bố nhãn `Machine failure` (mất cân bằng) và tần suất 5 dạng hỏng hóc độc lập.
2. `figures/eda/02_feature_distributions.png`: Histogram kèm đường cong KDE của 5 biến liên tục và phân bố `Type`.
3. `figures/eda/03_feature_boxplots_by_failure.png`: Boxplot của 5 biến liên tục phân tầng theo `Machine failure` (0 vs 1).
4. `figures/eda/04_correlation_heatmap.png`: Ma trận hệ số tương quan Pearson giữa các đặc trưng số học và target.
5. `figures/eda/05_physical_failure_mechanisms.png`: Trực quan hóa ranh giới vật lý sinh ra sự cố (PWF, HDF, OSF).
6. `figures/eda/06_temporal_sequence_hdf_cluster.png`: Xu hướng nhiệt độ và cụm lỗi HDF tập trung theo thứ tự UDI.

---

## 8. Đề Xuất Bổ Sung Metadata Cho `data/README.md` (Chờ Chủ Dự Án Duyệt)

Dưới đây là phần đề xuất bổ sung vào `data/README.md` (không tự ý chỉnh sửa tệp chung):

```markdown
### Provenance tệp dữ liệu đã tải local
- Tệp raw: data/raw/ai4i2020.csv
- Kích thước: 522,048 bytes
- SHA-256: dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e
- Tệp nén gốc: data/raw/ai4i2020.zip (522,170 bytes, SHA-256: f601f14294bcf190f9d720676b7f0aea46a26cde9ab8ebc7b4f8174d9d26b252)
- Thời điểm tải: 2026-10-21 07:31:29 UTC
- Số lượng: 10,000 hàng, 14 cột, 0 missing values
- Xác thực hash: Đã kiểm tra trùng khớp với bản phát hành UCI AI4I 2020.
```
