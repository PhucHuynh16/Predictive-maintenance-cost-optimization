# Dữ Liệu — Nguồn Gốc, Mã Băm Toàn Vẹn & Quy Trình Tiền Xử Lý (Scania APS UCI #421)

Tài liệu này mô tả nguồn gốc dữ liệu, mã băm kiểm tra toàn vẹn SHA-256, phân vùng dữ liệu G3 và cách tái tạo dữ liệu cho đề tài **Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS** (Học phần: Nhập môn Tối ưu hóa — Trường Đại học Văn Lang).

---

## 1. NGUỒN GỐC DỮ LIỆU & BẢN QUYỀN SỬ DỤNG

- **Tên tập dữ liệu:** *APS Failure at Scania Trucks*
- **Kho lưu trữ công khai:** UCI Machine Learning Repository (Mã định danh: **#421**)
- **Đơn vị công bố:** Scania CV AB (Södertälje, Thụy Điển) — IDA 2016 Industrial Challenge
- **DOI:** [10.24432/C51S51](https://doi.org/10.24432/C51S51)
- **URL chính thức:** [https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks)
- **Giấy phép sử dụng:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))

---

## 2. MÃ BĂM KIỂM TRA TOÀN VẸN SHA-256 (PROVENANCE CHECKSUMS)

Tệp nén phân phối từ UCI (`https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip`) và các tệp thành phần có kích thước và mã băm SHA-256 chuẩn như sau:

| Tệp dữ liệu | Kích thước (bytes) | Mã băm toàn vẹn SHA-256 | Vai trò |
|---|:---:|---|---|
| `aps+failure+at+scania+trucks.zip` | 56.618.034 | `5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89` | Tệp nén gốc tải từ UCI |
| `aps_failure_training_set.csv` | 44.669.194 | `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da` | Tập phát triển gốc (60.000 mẫu, 171 cột) |
| `aps_failure_test_set.csv` | 11.905.772 | `c56ab8aa32a0f670f5e7144bf0d53c7a7ea50549c7f66a8770281eb2ba2629b3` | Tập Official Test gốc (16.000 mẫu, 171 cột — nằm trong ZIP) |
| `aps_failure_description.txt` | 4.874 | `57b1eb3c551a678ffc1c8112e5b34c566dd16457642563f58aeb3ca65beeb820` | Tài liệu mô tả thuộc tính gốc từ Scania |

*(Lưu ý kỹ thuật: SHA-256 được sử dụng làm mã băm kiểm tra tính toàn vẹn dữ liệu — integrity checksum, không phải chữ ký số khóa công khai).*

---

## 3. PHÂN VÙNG DỮ LIỆU KHÓA CỐ ĐỊNH (GIAO THỨC G3)

### 3.1. Phân vùng phát triển (60.000 mẫu từ `aps_failure_training_set.csv`)
- **Train (`48.000` mẫu):** $800$ mẫu `pos` ($y=1$, $1.67\%$) và $47.200$ mẫu `neg` ($y=0$, $98.33\%$). Chỉ dùng tập Train này để `fit` bộ điền khuyết trung vị, bộ chuẩn hóa và các mô hình phân loại.
- **Validation (`12.000` mẫu):** $200$ mẫu `pos` ($1.67\%$) và $11.800$ mẫu `neg` ($98.33\%$). Tách phân tầng (`stratified`, `seed = 42`), rời nhau hoàn toàn với Train ($\text{Train} \cap \text{Validation} = \emptyset$). Dùng để so sánh G4 Baselines và chọn siêu tham số/ngưỡng trong Phase 2.
- **Mã băm đối tượng G3 (`stable_digest`):** `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb` (lưu tại [`results/scania_aps/g3/official_20261029_04/stable_manifest.json`](../results/scania_aps/g3/official_20261029_04/stable_manifest.json)).

### 3.2. Phân vùng kiểm thử độc lập (`aps_failure_test_set.csv` — 16.000 mẫu)
- Gồm $375$ mẫu `pos` ($2.34\%$) và $15.625$ mẫu `neg` ($97.66\%$).
- Không giải nén ra thư mục làm việc trong giai đoạn G3/G4/Phase 2. Chỉ được đọc trực tiếp từ tệp ZIP trong bộ nhớ tại **Gate G10 Run 003** để đánh giá độc lập một lần duy nhất với chính sách đã khóa từ Trial 16.
- *Công bố minh bạch:* Trong hai lượt chạy lỗi kỹ thuật trước đó (`scania_g10_official_test_001` và `002`), tệp CSV Test đã được đọc vào bộ nhớ trước khi tiến trình dừng tại chốt kiểm tra đường dẫn/import của `tree_preprocessor.joblib`; không có dự đoán hay điều chỉnh tham số nào diễn ra.

---

## 4. QUY TRÌNH TIỀN XỬ LÝ KHÔNG RÒ RỈ (TRAIN-ONLY PREPROCESSING)

1. **Đọc dữ liệu & kiểm tra schema (`src/scania/data.py`):** Bỏ qua phần lời dẫn đầu tệp, kiểm tra đúng header dòng 21 (`class` + $170$ cột số từ `aa_000` đến `ee_000`), chuyển chuỗi `na` thành `NaN`, mã hóa `neg -> 0`, `pos -> 1`.
2. **Nhánh mô hình cây (`tree_preprocessor.joblib`):** Kiểm tra hợp đồng 170 đặc trưng (`FeatureContract`) + `SimpleImputer(strategy="median")` học trung vị trên $48.000$ mẫu Train, sau đó `transform` sang `tree_train.npy` và `tree_validation.npy`.
3. **Nhánh Logistic Regression (`lr_preprocessor.joblib`):** Bổ sung thêm `StandardScaler()` học trung bình và độ lệch chuẩn trên $48.000$ mẫu Train, xuất `lr_train.npy` và `lr_validation.npy`.

---

## 5. HƯỚNG DẪN TẢI DỮ LIỆU & CÁC CHẾ ĐỘ CHẠY LẠI

Theo quy định bảo mật và dung lượng kho Git, toàn bộ thư mục `data/raw/**` và `data/processed/**` nằm trong `.gitignore` (không đính kèm trong kho mã nguồn công khai hay gói ZIP nghiệm thu gọn nhẹ).

### 5.1. Chế độ A — Chạy Demo & Kiểm tra kết quả đã lưu (Không cần tải dữ liệu thô)
Người chấm có thể chạy ngay từ thư mục gốc dự án hoặc thư mục `nghiemthu`:
```powershell
python scripts/demo.py
python scripts/demo.py --summary
python scripts/demo.py --verify
python scripts/demo.py --notes
python scripts/run_scania_g10.py verify
```

### 5.2. Chế độ B — Tái lập bước tải dữ liệu và tiền xử lý G3 (Yêu cầu kho Git sạch & Python 3.11)
Nếu muốn tự tải lại dữ liệu gốc từ UCI và sinh lại các mảng tiền xử lý `.npy` cùng `.joblib`:
```powershell
# Cách 1: Dùng script thu thập dữ liệu chính thức của dự án (chỉ giải nén tập Train & mô tả, giữ nguyên Test trong ZIP)
python scripts/run_scania_acquire.py

# Cách 2: Tải thủ công bằng PowerShell và kiểm tra mã băm SHA-256
New-Item -ItemType Directory -Force -Path "data/raw/scania_aps"
Invoke-WebRequest -Uri "https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip" -OutFile "data/raw/scania_aps/aps+failure+at+scania+trucks.zip"
Get-FileHash -Algorithm SHA256 "data/raw/scania_aps/aps+failure+at+scania+trucks.zip"
# Kỳ vọng: 5504D0402F54FAAF97AC0CA085A621645763F5CFEA2EB29C592B057D43D4DB89

# Sinh lại phân vùng official_split.json, mảng .npy và preprocessor .joblib (khớp stable_digest G3)
python scripts/run_scania_pipeline.py --run-id g3_recheck_local --expect-stable efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb
```
*Lưu ý về quyền chạy thực nghiệm thật:* Các script `run_scania_baselines.py gate-b2`, `run_scania_phase2.py execute` và `run_scania_g10.py execute` có chốt chặn kiểm tra hồ sơ phê duyệt của Chủ dự án (gắn với commit SHA và bình luận trên GitHub Issue #17) nhằm bảo vệ tính nguyên vẹn của kết quả lịch sử. Người dùng độc lập có thể chạy chế độ kiểm thử tổng hợp (`python -m scripts.run_scania_phase2 synthetic --trials 3` và `python scripts/run_scania_g10.py synthetic`) mà không cần phê duyệt.
