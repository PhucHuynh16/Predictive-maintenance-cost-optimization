# TỪ ĐIỂN DỮ LIỆU — AI4I 2020 PREDICTIVE MAINTENANCE DATASET

- **Đồ án:** Tối ưu chi phí bảo trì dự đoán bằng Machine Learning
- **Nhiệm vụ:** W1-G2-A (Tuần 1 – Giai đoạn 2)
- **Tác giả phụ trách:** Antigravity (theo phân quyền `AGENTS.md`)
- **Tệp dữ liệu thực tế:** `data/raw/ai4i2020.csv`
- **Mã băm SHA-256:** `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`
- **Kích thước file:** 522,048 bytes (10,000 dòng, 14 cột)

---

## 1. Đối chiếu giữa Metadata Nguồn (UCI) và Tệp CSV Thực Tế

Trang thông tin UCI Machine Learning Repository ghi nhận:
- Số quan sát: 10,000 dòng.
- Số lượng đặc trưng: 6 features.
- Missing values: None.

**Kiểm chứng thực tế trên tệp `ai4i2020.csv`:**
- Số dòng: Đúng 10,000 dòng (chỉ số UDI từ 1 đến 10,000). Không có dòng tiêu đề thừa hoặc thiếu.
- Số cột: **14 cột** (không phải 6 cột như mô tả ngắn của UCI). Trong đó gồm:
  - 2 cột định danh (`UDI`, `Product ID`).
  - 1 cột đặc trưng phân loại (`Type`).
  - 5 cột đặc trưng số học liên tục (`Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`).
  - 1 cột nhãn mục tiêu chính (`Machine failure`).
  - 5 cột nhãn phụ biểu diễn cơ chế hỏng hóc cụ thể (`TWF`, `HDF`, `PWF`, `OSF`, `RNF`).
- Missing values: 0 trên tất cả 14 cột.

---

## 2. Bảng Từ Điển Dữ Liệu Chi Tiết

| STT | Tên cột thực tế trong CSV | Dtype | Đơn vị | Vai trò | Miền giá trị quan sát | Missing | Quyết định trong ML | Lý do nghiệp vụ / Kỹ thuật |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| 1 | `UDI` | `int64` | Thứ tự | ID | $[1, 10000]$ (10,000 unique) | 0 | **LOẠI BỎ** | Chỉ số dòng tuần tự; đưa vào mô hình gây rò rỉ hoặc tương quan giả với chu kỳ nhiệt. |
| 2 | `Product ID` | `object` (str) | Mã hiệu | ID | 10,000 unique (bắt đầu bằng L, M, H + 5 chữ số) | 0 | **LOẠI BỎ** | Mã định danh riêng của từng sản phẩm. Chữ cái đầu phản ánh cột `Type`, phần số là bộ đếm. |
| 3 | `Type` | `object` (str) | Phân loại | Feature | L: 6,000 (60.0%)<br>M: 2,997 (30.0%)<br>H: 1,003 (10.0%) | 0 | **GIỮ LẠI** | Cấp chất lượng biến thể sản phẩm (Low/Medium/High). Tỷ lệ hỏng khác biệt rõ rệt ($L > M > H$). Cần mã hóa (One-hot hoặc Ordinal). |
| 4 | `Air temperature [K]` | `float64` | Kelvin ($K$) | Feature | Min: 295.3, Max: 304.5<br>Mean: 300.0, Median: 300.1<br>Std: 2.00 | 0 | **GIỮ LẠI** | Nhiệt độ không khí xung quanh máy. Biến đầu vào vật lý chuẩn hóa. |
| 5 | `Process temperature [K]` | `float64` | Kelvin ($K$) | Feature | Min: 305.7, Max: 313.8<br>Mean: 310.0, Median: 310.1<br>Std: 1.48 | 0 | **GIỮ LẠI** | Nhiệt độ quá trình gia công. Tương quan mạnh với nhiệt độ không khí ($r=0.876$). |
| 6 | `Rotational speed [rpm]` | `int64` | Vòng/phút | Feature | Min: 1168, Max: 2886<br>Mean: 1538.8, Median: 1503.0<br>Std: 179.3, Skew: +1.99 | 0 | **GIỮ LẠI** | Tốc độ quay của trục chính. Có độ lệch dương mạnh và 418 điểm ngoại lai phía trên (liên quan trực tiếp đến lỗi quá tốc/nguồn). |
| 7 | `Torque [Nm]` | `float64` | Newton-mét ($Nm$) | Feature | Min: 3.8, Max: 76.6<br>Mean: 40.0, Median: 40.1<br>Std: 9.97, Skew: -0.01 | 0 | **GIỮ LẠI** | Mô-men xoắn chịu tải. Tương quan nghịch mạnh với vận tốc quay ($r=-0.875$). 64 điểm ngoại lai có 90.6% tỷ lệ hỏng. |
| 8 | `Tool wear [min]` | `int64` | Phút | Feature | Min: 0, Max: 253<br>Mean: 108.0, Median: 108.0<br>Std: 63.65, Skew: +0.03 | 0 | **GIỮ LẠI** | Thời gian mòn dụng cụ tích lũy khi gia công. Là biến điều kiện quan trọng cho bảo trì phòng ngừa. |
| 9 | `Machine failure` | `int64` | Nhị phân | **TARGET** | 0: 9,661 (96.61%)<br>1: 339 (3.39%) | 0 | **TARGET CHÍNH** | Nhãn mục tiêu bài toán phân loại nhị phân ($y_i \in \{0, 1\}$). Biểu thị trạng thái máy hỏng trong chu kỳ quan sát. |
| 10 | `TWF` | `int64` | Nhị phân | Sub-target | 0: 9,954<br>1: 46 (0.46%) | 0 | **LOẠI BỎ KHỎI FEATURES** | *Tool Wear Failure*: Lỗi mòn dụng cụ. Đây là chế độ hỏng cụ thể, chỉ được biết sau khi máy hỏng. Đưa vào làm feature gây rò rỉ nhãn 100%. |
| 11 | `HDF` | `int64` | Nhị phân | Sub-target | 0: 9,885<br>1: 115 (1.15%) | 0 | **LOẠI BỎ KHỎI FEATURES** | *Heat Dissipation Failure*: Lỗi tản nhiệt kém. Tuyệt đối không đưa vào feature đầu vào. |
| 12 | `PWF` | `int64` | Nhị phân | Sub-target | 0: 9,905<br>1: 95 (0.95%) | 0 | **LOẠI BỎ KHỎI FEATURES** | *Power Failure*: Lỗi công suất ngoài dải an toàn. Tuyệt đối không đưa vào feature đầu vào. |
| 13 | `OSF` | `int64` | Nhị phân | Sub-target | 0: 9,902<br>1: 98 (0.98%) | 0 | **LOẠI BỎ KHỎI FEATURES** | *Overstrain Failure*: Lỗi quá tải ứng suất. Tuyệt đối không đưa vào feature đầu vào. |
| 14 | `RNF` | `int64` | Nhị phân | Sub-target | 0: 9,981<br>1: 19 (0.19%) | 0 | **LOẠI BỎ KHỎI FEATURES** | *Random Failure*: Lỗi ngẫu nhiên (xác suất 0.1%). 18/19 ca có `RNF=1` nhưng `Machine failure=0`. Không đưa vào feature. |

---

## 3. Tổng Hợp Phạm Vi Đặc Trưng Cho Data Pipeline (Codex - G3)

1. **Tập đặc trưng đầu vào cơ sở (6 features):**
   - Phân loại: `Type` (1 biến phân loại, 3 mức L, M, H).
   - Số học: `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`.

2. **Các đặc trưng phái sinh vật lý đề xuất cho Feature Engineering:**
   - $\Delta T = \text{Process temperature [K]} - \text{Air temperature [K]}$ (Chênh lệch nhiệt độ tản nhiệt).
   - $P = \text{Torque [Nm]} \times \left( \text{Rotational speed [rpm]} \times \frac{2\pi}{60} \right)$ (Công suất cơ học, Watt).
   - $\text{Overstrain} = \text{Tool wear [min]} \times \text{Torque [Nm]}$ (Ứng suất mài mòn tích lũy, $min \cdot Nm$).

3. **Cấm tuyệt đối đưa vào đặc trưng đầu vào:**
   - Cấm `UDI`, `Product ID` (Rò rỉ thứ tự mô phỏng và định danh).
   - Cấm `TWF`, `HDF`, `PWF`, `OSF`, `RNF` (Target leakage trực tiếp).
