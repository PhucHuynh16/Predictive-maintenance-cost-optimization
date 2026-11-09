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

## 5. HƯỚNG DẪN TẢI, TÁI LẬP DỮ LIỆU & PHÂN ĐỊNH QUYỀN THỰC THI

Toàn bộ dữ liệu thô và dữ liệu mảng tiền xử lý nằm trong `.gitignore` nhằm tuân thủ quy định không commit tệp nhị phân lớn lên GitHub. Để tái lập môi trường dữ liệu:

### 5.1. Yêu cầu tiên quyết (Prerequisites)
- Hệ điều hành: Windows 10/11 hoặc Linux (Ubuntu 22.04+).
- Python: **Phiên bản 3.11.x** (đã kiểm định thực tế trên Python 3.11.9).
- Bộ nhớ RAM: Khuyến nghị tối thiểu 4 GB.
- Thư viện phụ thuộc: Cài đặt qua `pip install -r requirements.txt`.

### 5.2. Tải và giải nén tệp gốc UCI Scania APS
1. **Tạo thư mục và tải tệp nén chính thức từ UCI:**
   ```powershell
   New-Item -ItemType Directory -Force -Path "data/raw/scania_aps"
   Invoke-WebRequest -Uri "https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip" -OutFile "data/raw/scania_aps/aps+failure+at+scania+trucks.zip"
   ```
2. **Kiểm tra mã băm SHA-256 của tệp nén gốc:**
   ```powershell
   Get-FileHash -Algorithm SHA256 "data/raw/scania_aps/aps+failure+at+scania+trucks.zip"
   # Kỳ vọng: 5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89
   ```
3. **Giải nén dữ liệu huấn luyện:**
   Giải nén vào thư mục `data/raw/scania_aps/` để có `aps_failure_training_set.csv` (SHA-256: `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da`) và `aps_failure_description.txt` (SHA-256: `57b1eb3c551a678ffc1c8112e5b34c566dd16457642563f58aeb3ca65beeb820`).
   *Lưu ý: Tệp `aps_failure_test_set.csv` chỉ được đọc trong lượt chạy nghiệm thu Gate G10 đã được cấp phép.*

### 5.3. Phân vùng dữ liệu G3 & Tiền xử lý
Giao thức G3 phân tầng 60.000 dòng huấn luyện gốc thành 48.000 mẫu Train và 12.000 mẫu Validation được lưu trữ trong tệp phân vùng chuẩn:
- Tệp phân vùng: `data/processed/scania_aps/official_split.json` (Khớp mã băm `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb` trong G3 stable digest).
- Các mảng tiền xử lý và pipeline chuyển đổi được lưu trữ dưới định dạng NumPy (`.npy`) và Joblib (`tree_preprocessor.joblib`), fit hoàn toàn trên 48.000 mẫu Train.

### 5.4. Phân định quyền thực thi: Read-Only vs Execution có ủy quyền Owner
Để đảm bảo tính toàn vẹn học thuật và an toàn tài nguyên máy:
1. **Lệnh tái lập công khai (Read-Only / Verification — Không cần cấp phép):**
   - Chạy script demo nghiệm thu và speaker notes:
     ```powershell
     python scripts/demo.py
     python scripts/demo.py --summary
     ```
   - Xác thực toàn vẹn chữ ký số mật mã học SHA-256:
     ```powershell
     python scripts/demo.py --verify
     python scripts/run_scania_g10.py verify
     ```
   - Chạy toàn bộ 42 bài kiểm thử tự động (Unit Tests):
     ```powershell
     pytest tests/scania/test_phase2_optimization.py tests/scania/test_g10_evaluation.py -v
     ```
   - Tái tạo hai đồ thị tối ưu hóa từ dữ liệu nghiệm thu gốc:
     ```powershell
     python -m scripts.run_scania_phase2 generate-figures --run-id scania_phase2_rf_optuna_002
     ```
2. **Lệnh thực thi thực nghiệm thật (Yêu cầu ủy quyền mật mã của Chủ dự án - Owner Authorization):**
   - Các lệnh huấn luyện tối ưu hóa (`python scripts/run_scania_phase2.py execute`) và mở tập Test chính thức (`python scripts/run_scania_g10.py execute`) được bảo vệ bằng cơ chế xác thực chốt chặn hai lớp.
   - Các script này kiểm tra token ủy quyền GitHub Issue #17 được ký băm gắn chặt với commit Git HEAD và cấu hình run. Nếu không có file ủy quyền hợp lệ, tiến trình sẽ tự động từ chối chạy (fail-closed) để ngăn chặn việc train lại ngoài kế hoạch hoặc truy cập trái phép vào tập dữ liệu kiểm thử.

---

## 6. LƯU Ý KHOA HỌC & GIỚI HẠN

1. **Ý nghĩa nhãn âm tính (`neg`):** Tài liệu Scania khẳng định lớp âm tính không phải là xe hoàn hảo, mà là các xe gặp sự cố ở các hệ thống khác (động cơ, điện, truyền động). Việc can thiệp kiểm tra nhầm ($FP$) gây tốn chi phí kiểm tra định kỳ không đáng có ($10$ đơn vị chi phí benchmark).
2. **Tính quy ước của chi phí benchmark:** Hàm mục tiêu $10 \cdot FP + 500 \cdot FN$ là quy ước chuẩn tắc tĩnh của bài toán benchmark IDA 2016, không phản ánh trực tiếp dòng tiền thực tế của doanh nghiệp. Vận hành thực địa cần tích hợp thêm mô hình điều độ động và chi phí phụ tùng.
