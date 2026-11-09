# Dữ liệu — Nguồn Gốc, Provenance & Quy Trình Xử Lý (Scania APS UCI #421)

Tài liệu này mô tả chi tiết nguồn gốc dữ liệu, chứng nhận tính toàn vẹn mật mã học, phân vùng dữ liệu và quy trình tiền xử lý chuẩn tắc cho đề tài **Tối ưu hóa chi phí bảo trì dự đoán trên tập dữ liệu xe tải Scania APS** (Học phần: Nhập môn Tối ưu hóa — Đại học Văn Lang).

---

## 1. NGUỒN GỐC DỮ LIỆU & BẢN QUYỀN

- **Tên tập dữ liệu:** *APS Failure at Scania Trucks*
- **Kho lưu trữ:** UCI Machine Learning Repository (Mã định danh: **#421**)
- **Đơn vị thu thập & đóng góp:** Scania CV AB (Södertälje, Thụy Điển) phối hợp cùng IDA 2016 (Industrial Challenge).
- **DOI định danh:** [10.24432/C51S51](https://doi.org/10.24432/C51S51)
- **URL chính thức:** [https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks)
- **Giấy phép sử dụng:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)) / Điều khoản Scania CV AB.
- **Bản chất kỹ thuật:** Dữ liệu cảm biến vận hành thực tế của đội xe tải hạng nặng Scania trong hoạt động vận tải hàng ngày, phục vụ chẩn đoán hư hỏng hệ thống khí nén (Air Pressure System - APS).

---

## 2. PROVENANCE & CHỨNG NHẬN TÍNH TOÀN VẸN TỆP NHỊ PHÂN

Dữ liệu được tải trực tiếp từ cổng phân phối chính thức của UCI và được kiểm định toàn vẹn bằng chữ ký băm SHA-256:

- **Tệp lưu trữ chính thức:** `https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip`

| Tệp dữ liệu | Kích thước (bytes) | Mã băm SHA-256 | Vai trò & Trạng thái |
|---|:---:|---|---|
| `aps+failure+at+scania+trucks.zip` | 56.618.034 | `5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89` | Tệp nén gốc từ UCI |
| `aps_failure_training_set.csv` | 44.669.194 | `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da` | Dữ liệu huấn luyện gốc (60.000 mẫu, 171 cột) |
| `aps_failure_test_set.csv` | 11.905.772 | `c56ab8aa32a0f670f5e7144bf0d53c7a7ea50549c7f66a8770281eb2ba2629b3` | Dữ liệu kiểm thử chính thức (16.000 mẫu, 171 cột) |
| `aps_failure_description.txt` | 4.874 | `57b1eb3c551a678ffc1c8112e5b34c566dd16457642563f58aeb3ca65beeb820` | Tài liệu đặc tả thuộc tính từ tác giả |

---

## 3. PHÂN VÙNG DỮ LIỆU ĐÃ KHÓA (G3 PROTOCOL)

Nhằm ngăn chặn triệt để hiện tượng rò rỉ dữ liệu (data leakage) và thiên lệch lựa chọn (selection bias), dữ liệu được phân chia theo giao thức G3 đã được kiểm định độc lập:

### 3.1. Phân vùng Huấn luyện & Đánh giá nội bộ (Gốc 60.000 mẫu)
- **Tập Train (48.000 mẫu):** 800 ca dương tính ($y=1, 1.67\%$) và 47.200 ca âm tính ($y=0, 98.33\%$). Dùng độc quyền để fit tiền xử lý (Imputer, Scaler) và huấn luyện mô hình.
- **Tập Validation (12.000 mẫu):** 200 ca dương tính ($y=1, 1.67\%$) và 11.800 ca âm tính ($y=0, 98.33\%$). Dùng độc quyền để tìm kiếm siêu tham số và quét ngưỡng quyết định trong Phase 2.
- **Ranh giới:** Hai phân vùng phân tầng (stratified) hoàn toàn tách biệt: $\text{Train} \cap \text{Validation} = \emptyset$.
- **Mã băm G3 Stable Manifest:** `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`.

### 3.2. Tập Kiểm thử Độc lập Chính thức (Official Test — 16.000 mẫu)
- **Quy mô:** 16.000 mẫu kiểm thử hoàn toàn độc lập gồm 375 ca lỗi APS thực tế ($2.34\%$) và 15.625 ca âm tính ($97.66\%$).
- **Nguyên tắc niêm phong:** Được niêm phong độc lập trong suốt quá trình nghiên cứu baseline và tối ưu hóa Phase 2. Chỉ được giải phóng để đánh giá một lần duy nhất tại **Gate G10 Run 003** sau khi chính sách tối ưu (Random Forest Trial 16) đã được khóa cố định.
- **Minh bạch truy cập:** Ở hai lần chạy lỗi tiền kiểm tra G10 (`scania_g10_official_test_001` và `002`), tệp test CSV được đọc vào bộ nhớ, nhưng tiến trình bị dừng ngay lập tức tại chốt kiểm tra preprocessor trước khi bất kỳ suy diễn dự đoán hay tinh chỉnh nào diễn ra.

---

## 4. QUY TRÌNH TIỀN XỬ LÝ KHÔNG RÒ RỈ (STRICT TRAIN-ONLY FITTING)

1. **Kiểm tra Header & Định dạng số học:**
   - Dòng 1-20 của tệp gốc chứa chú thích bản quyền từ Scania; header thật bắt đầu từ dòng 21 (`class, aa_000, ...`).
   - 170 thuộc tính số học được ẩn danh theo họ chữ cái (`aa` đến `ee`), trong đó có 7 họ phân bố dạng histogram (`ag`, `ay`, `az`, `ba`, `cn`, `cs`, `ee`).
2. **Xử lý giá trị khuyết thiếu (Missing Values):**
   - Giá trị khuyết được ký hiệu bằng chuỗi `na`.
   - `SimpleImputer(strategy='median')` học giá trị trung vị duy nhất trên 48.000 mẫu Train, sau đó áp dụng phép biến đổi tĩnh (`transform`) lên Validation và Test.
3. **Chuẩn hóa thang đo (Feature Scaling):**
   - `StandardScaler()` tính toán giá trị trung bình $\mu$ và phương sai $\sigma$ duy nhất trên 48.000 mẫu Train, sau đó áp dụng tĩnh lên Validation và Test.
4. **Mã hóa nhãn mục tiêu (Target Encoding):**
   - `neg` (lỗi ở bộ phận khác ngoài APS) $\rightarrow 0$.
   - `pos` (hư hỏng thực tế tại hệ thống khí nén APS) $\rightarrow 1$.

---

## 5. HƯỚNG DẪN TẢI & TÁI LẬP DỮ LIỆU LOCAL

Toàn bộ dữ liệu thô và dữ liệu đã xử lý nằm trong `.gitignore` nhằm tuân thủ quy định không commit tệp nhị phân lớn lên GitHub. Để thiết lập lại dữ liệu local:

1. **Tải tệp nén từ UCI:**
   ```powershell
   Invoke-WebRequest -Uri "https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip" -OutFile "data/raw/aps_failure_at_scania_trucks.zip"
   ```
2. **Kiểm tra mã băm SHA-256:**
   ```powershell
   Get-FileHash -Algorithm SHA256 "data/raw/aps_failure_at_scania_trucks.zip"
   # Kỳ vọng: 5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89
   ```
3. **Giải nén:**
   Giải nén vào thư mục `data/raw/` để có `aps_failure_training_set.csv` và `aps_failure_test_set.csv`.
4. **Tạo dữ liệu phân vùng G3:**
   ```powershell
   python scripts/run_data_pipeline.py
   ```
   Lệnh trên sẽ sinh `data/processed/train.parquet` và `data/processed/validation.parquet` với phân tầng ngẫu nhiên cố định tại `seed = 42`.

---

## 6. LƯU Ý KHOA HỌC & GIỚI HẠN

1. **Ý nghĩa nhãn âm tính (`neg`):** Tài liệu Scania khẳng định lớp âm tính không phải là xe hoàn hảo, mà là các xe gặp sự cố ở các hệ thống khác (động cơ, điện, truyền động). Việc can thiệp kiểm tra nhầm ($FP$) gây tốn chi phí kiểm tra định kỳ không đáng có ($10$ đơn vị chi phí benchmark).
2. **Tính quy ước của chi phí benchmark:** Hàm mục tiêu $10 \cdot FP + 500 \cdot FN$ là quy ước chuẩn tắc tĩnh của bài toán benchmark IDA 2016, không phản ánh trực tiếp dòng tiền thực tế của doanh nghiệp. Vận hành thực địa cần tích hợp thêm mô hình điều độ động và chi phí phụ tùng.
