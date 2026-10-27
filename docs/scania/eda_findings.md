# SC-G2-A — Báo cáo Kiểm toán Dữ liệu Nguồn Scania APS (EDA Findings)

**Ngày lập:** 2026-10-25 (Asia/Saigon)  
**Người thực hiện:** Antigravity (Data Audit Specialist)  
**Mã nhiệm vụ:** SC-G2-A  
**Phạm vi:** Kiểm toán tính toàn vẹn (integrity), cấu trúc file, nhãn, phân bố khuyết thiếu và trùng lặp trên tập Train chính thức 60.000 mẫu (`aps_failure_training_set.csv`).  
**Căn cứ phê duyệt:** Các đề xuất **P01, P03 và phần G2 của P10** được Chủ dự án phê duyệt theo tài liệu `docs/scania/decision_register.md` và `docs/scania/experimental_protocol.md` (sau khi merge PR #13 tại commit `6a184cc`).

---

## 1. Tuyên bố Tuân thủ & Giới hạn Nghiên cứu (Governance & Boundaries)

Để bảo đảm tính liêm chính khoa học và tuân thủ tuyệt đối quy định trong `AGENTS.md` cũng như các cổng nghiệm thu Scania:

1. **Phạm vi kiểm toán:** Nhiệm vụ SC-G2-A chỉ thực hiện kiểm toán tĩnh (audit) trên **tệp Huấn luyện chính thức 60.000 mẫu** (`aps_failure_training_set.csv`).
2. **Niêm phong tập Test (Test Set Sealed):** Tệp Kiểm tra chính thức 16.000 mẫu (`aps_failure_test_set.csv`) được giữ nguyên niêm phong bên trong tệp nén gốc tải từ UCI. Antigravity tuyệt đối **không giải nén, không mở, không parse, không phân tích nhãn hoặc tính toán phân phối thống kê** trên tập Test trước cổng G10.
3. **Chống rò rỉ dữ liệu (No Leakage):**
   * Trong giai đoạn G2, **không thực hiện phân chia Train/Validation**.
   * **Không fit imputer hoặc scaler** trên toàn bộ 60.000 mẫu.
   * **Không thực hiện lọc đặc trưng (feature selection)** dựa trên độ tương quan với nhãn trên toàn bộ 60.000 mẫu.
   * **Không huấn luyện hoặc điều chỉnh siêu tham số (tuning)** cho bất kỳ mô hình học máy nào.
4. **Bảo tồn dữ liệu gốc:** Không xóa dòng dữ liệu, không sửa nhãn, không gán nhãn đa số (majority vote), không tự ý nội suy (impute) dữ liệu thô.

---

## 2. Kiểm toán Nguồn cấp và Tính toàn vẹn Tệp dữ liệu (P01)

### 2.1. Nguồn cấp và Provenance
Dữ liệu được thu thập trực tiếp từ cổng lưu trữ chính thức của UCI Machine Learning Repository:
* **Tên bộ dữ liệu:** APS Failure at Scania Trucks (UCI ID: 421)
* **DOI:** [10.24432/C51S51](https://doi.org/10.24432/C51S51)
* **URL tải về:** `https://archive.ics.uci.edu/static/public/421/aps+failure+at+scania+trucks.zip`
* **Thời điểm tải (UTC):** `2026-10-25T08:37:03.366093+00:00`
* **Mã băm SHA-256 tệp nén gốc:** `5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89` (Dung lượng: 56.618.034 bytes).
* **Quy tắc trích xuất an toàn:** Chỉ trích xuất tệp mô tả `aps_failure_description.txt` và tệp huấn luyện `aps_failure_training_set.csv`. Tệp `aps_failure_test_set.csv` (11.943.558 bytes) được giữ nguyên trạng thái niêm phong bên trong archive.

### 2.2. Kiểm toán Cấu trúc Tệp Train (`aps_failure_training_set.csv`)
* **Dung lượng tệp raw:** Đúng **44.669.194 bytes**.
* **Mã băm SHA-256:** `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da`.
* **Phát hiện Preamble / Chú thích đầu tệp:**
  * Bằng thuật toán quét tự động phát hiện dòng chứa cột `class` (không hard-code số dòng bỏ qua), tệp có đúng **20 dòng chú thích đầu tệp** (từ dòng 1 đến dòng 20).
  * Nội dung 20 dòng chú thích bao gồm thông báo bản quyền Scania CV AB, điều khoản giấy phép GNU General Public License v3 (GPLv3) và đường kẻ phân cách `--------`.
* **Dòng Header:**
  * Xuất hiện chính xác tại **dòng 21** (chỉ số 0-based: 20).
  * Chứa đúng **171 cột** phân tách bằng dấu phẩy.
  * Cột đầu tiên mang tên `class` (Biến mục tiêu).
  * 170 cột tiếp theo là các thuộc tính vận hành ẩn danh: bắt đầu từ `aa_000`, `ab_000`, ..., và kết thúc bằng `ee_009`, `ef_000`, `eg_000`.
* **Cấu trúc dòng dữ liệu:**
  * Tổng số dòng dữ liệu thực tế sau header: Đúng **60.000 dòng**.
  * Số dòng dị dạng (malformed rows - thiếu/thừa cột): **0 dòng** (100% các dòng đều có đúng 171 trường dữ liệu).
* **Định danh Dòng nguồn (`source_row_id`):**
  * Đã thiết lập cơ chế định danh độc nhất cho mỗi dòng theo tuple:
    $$\text{source\_row\_id} = (\text{bb484302e3a3...}, \text{"train"}, \text{data\_row\_number})$$
  * `data_row_number` chạy tuần tự từ 1 đến 60.000 theo đúng thứ tự xuất hiện trong tệp nguồn.
  * **Trạng thái cổng P01:** **PASSED 100%**.

---

## 3. Kiểm toán Biến Mục tiêu (`class`)

Biến mục tiêu được kiểm toán trên toàn bộ 60.000 dòng dữ liệu:
* **Kiểm tra token raw:** Chỉ xuất hiện đúng 2 chuỗi ký tự hợp lệ: `"neg"` và `"pos"`. Không tồn tại bất kỳ token lạ, chuỗi rỗng (`""`), ký tự khoảng trắng thừa hoặc giá trị khuyết thiếu nào.
* **Phân bố nhãn thực tế:**
  * Nhãn `"neg"` (Lỗi ngoài APS): **59.000 mẫu** (chiếm **98,3333%**).
  * Nhãn `"pos"` (Lỗi linh kiện APS): **1.000 mẫu** (chiếm **1,6667%**).
* **Tỷ lệ mất cân bằng (Class Imbalance Ratio):** Đúng **59,00 : 1**.
* **Ý nghĩa kỹ thuật:**
  * Nhãn `neg` tương ứng với lớp số học `0`, đại diện cho xe gặp sự cố ở các hệ thống cơ khí/điện khác ngoài hệ thống khí nén.
  * Nhãn `pos` tương ứng với lớp số học `1`, đại diện cho xe bị hỏng hóc thực tế tại một bộ phận thuộc hệ thống khí nén (APS).
  * Tỷ lệ mẫu dương tính chỉ $1,67\%$ kết hợp với hàm phạt bất đối xứng $\text{Cost}_1 = 10$, $\text{Cost}_2 = 500$ (tỷ số phạt bỏ sót $\text{FN}/\text{FP} = 50 : 1$) đặt ra một **giả thuyết kỹ thuật cần kiểm chứng ở các giai đoạn sau**: với chi phí phạt FN gấp 50 lần FP, ngưỡng phân loại mặc định $0,5$ có nguy cơ không tối ưu về mặt chi phí kinh tế so với việc tối ưu hóa ngưỡng quyết định $\tau$, cần được đánh giá thực nghiệm chính thức tại G4.

---

## 4. Kiểm toán Giá trị Khuyết thiếu (Missingness Profiling)

Toàn bộ 170 cột thuộc tính vận hành số học ($170 \times 60.000 = 10.200.000$ ô dữ liệu) đã được phân tích chi tiết:
* **Token khuyết thiếu:** Ký hiệu khuyết thiếu duy nhất được xác nhận là chuỗi `"na"`. Không phát hiện bất kỳ token khuyết thiếu bất thường nào khác như `"null"`, `"None"`, `"NaN"`, `"-inf"`, `"inf"` hay `"? "`.
* **Tổng số ô khuyết thiếu:** **850.015 ô** (chiếm **8,3335%** trên tổng số 10.200.000 ô dữ liệu).
* **Tổng số ô quan sát được:** **9.349.985 ô** (chiếm **91,6665%**).

### 4.1. Phân bố khuyết thiếu theo Cột (Feature-wise Missingness)
* **Cột không có giá trị thiếu (0% missing):** Đúng **1 thuộc tính duy nhất**: `aa_000` (được quan sát đầy đủ trên cả 60.000 dòng).
* **Cột thiếu 100% (All-missing columns):** **0 thuộc tính** (tất cả 170 cột đều có ít nhất một số lượng quan sát giá trị số nhất định).
* **Các thuộc tính có tỷ lệ khuyết thiếu cực đoan:**
  * Thuộc tính có tỷ lệ thiếu $> 50\%$: **8 thuộc tính**.
  * Thuộc tính có tỷ lệ thiếu $> 70\%$: **7 thuộc tính**.
  * Thuộc tính có tỷ lệ thiếu $> 80\%$: **2 thuộc tính**.

Bảng thống kê 8 thuộc tính có tỷ lệ khuyết thiếu cao nhất:
| Tên thuộc tính | Phân loại | Số lượng thiếu (`na`) | Tỷ lệ thiếu (%) | Min quan sát | Max quan sát | Ghi chú |
|---|---|---:|---:|---:|---:|---|
| `br_000` | Counter | 49.264 | **82,11%** | 0.0 | 1.310.700.0 | Thiếu cao nhất |
| `bq_000` | Counter | 48.722 | **81,20%** | 0.0 | 1.310.700.0 | Chuỗi cảm biến B |
| `bp_000` | Counter | 47.740 | **79,57%** | 0.0 | 1.310.700.0 | Chuỗi cảm biến B |
| `bo_000` | Counter | 46.333 | **77,22%** | 0.0 | 1.310.700.0 | Chuỗi cảm biến B |
| `ab_000` | Counter | 46.329 | **77,22%** | 0.0 | 204.0 | Cảm biến A |
| `cr_000` | Counter | 46.329 | **77,22%** | 0.0 | 57.450.0 | Cảm biến C |
| `bn_000` | Counter | 44.009 | **73,35%** | 0.0 | 1.310.700.0 | Chuỗi cảm biến B |
| `bm_000` | Counter | 39.549 | **65,92%** | 0.0 | 1.310.700.0 | Chuỗi cảm biến B |

> [!NOTE]
> Nhóm 6 thuộc tính `bm_000`, `bn_000`, `bo_000`, `bp_000`, `bq_000`, `br_000` có cùng giá trị quan sát cực đại ($1.310.700,0$) và tỷ lệ missing tăng dần từ $65,92\%$ lên $82,11\%$. Vì toàn bộ thuộc tính đã bị Scania ẩn danh, sự liên quan về mặt vật lý hay cấu trúc cụm cảm biến chỉ là **giả thuyết thống kê chưa được xác minh**, không phải nhận định vật lý đã được kiểm chứng.

### 4.2. Phân bố khuyết thiếu theo Dòng (Row-wise Missingness)
* **Số dòng thiếu toàn bộ 170 thuộc tính:** **0 dòng** (không có bản ghi nào hoàn toàn rỗng).
* **Số thuộc tính thiếu ít nhất trên một dòng:** **0 thuộc tính** (tồn tại các bản ghi được đo lường hoàn chỉnh 170/170 đặc trưng).
* **Số thuộc tính thiếu nhiều nhất trên một dòng:** **168 thuộc tính** (tồn tại bản ghi bị khuyết thiếu 168/170 thuộc tính, chỉ quan sát được 2 đặc trưng duy nhất).

---

## 5. Phát hiện Thuộc tính Hằng số / Phương sai bằng 0 (Zero-Variance Audit)

Kiểm toán trên 170 thuộc tính số học phát hiện **đúng 1 thuộc tính có phương sai bằng 0 giữa các giá trị quan sát được**:
* **Tên thuộc tính:** `cd_000`
* **Giá trị quan sát:** Duy nhất một giá trị số **`1.209.600,0`** xuất hiện trên **59.324 dòng** (chiếm **98,87%** tập Train).
* **Số ô khuyết thiếu (`na`):** **676 ô** (chiếm **1,13%**).
* **Nhận xét kỹ thuật:** Đối với 59.324 quan sát có dữ liệu, thuộc tính này hoàn toàn không có độ biến thiên (zero variance). Con số `1.209.600` tình cờ bằng số giây trong 14 ngày ($14 \times 24 \times 3600$), tuy nhiên đây chỉ là **giả thuyết số học chưa xác minh**, hoàn toàn không có tài liệu kỹ thuật nào từ Scania xác nhận đây là chu kỳ quét hay watchdog timer. Về mặt học máy, thuộc tính này không mang lại phương sai phân tách cho các mô hình khi chỉ xét trên tập các giá trị quan sát được.

---

## 6. Kiểm toán Trùng lặp Exact-X và Xung đột Nhãn (Phê duyệt P03)

Quy trình kiểm toán trùng lặp tuân thủ nghiêm ngặt nguyên tắc được phê duyệt tại P03:
* **Không gian kiểm toán:** Toàn bộ ma trận $X$ gồm 170 thuộc tính số học được phân tích trước khi thực hiện bất kỳ bước điền khuyết (imputation) nào.
* **Biểu diễn chuẩn tắc (Canonical representation):** Mỗi ô dữ liệu được biểu diễn bằng giá trị số học thực (chính xác tuyệt đối, không làm tròn) kết hợp với mặt nạ khuyết thiếu (missing mask). Cột nhãn `class` và mã định danh `source_row_id` bị loại trừ hoàn toàn khỏi khóa so sánh.
* **Kết quả kiểm toán thực tế:**
  * **Tổng số mẫu đặc trưng duy nhất (Unique feature patterns):** Đúng **60.000 mẫu** trên tổng số 60.000 dòng ($100\%$).
  * **Số nhóm trùng lặp (Duplicate groups - kích thước $\ge 2$):** **0 nhóm**.
  * **Tổng số dòng trùng lặp:** **0 dòng**.
  * **Số dòng dư thừa (Surplus duplicate rows):** **0 dòng**.
  * **Số nhóm xung đột nhãn (Conflicting label groups - cùng exact-X nhưng khác nhãn):** **0 nhóm**.
* **Đánh giá Cổng P03:**
  $$\text{p03\_split\_gate\_status} = \mathbf{PASSED}$$
  Không phát hiện bất kỳ bản ghi trùng lặp exact-X hay xung đột nhãn nào trong tập Train 60.000 mẫu. Điều kiện `BLOCKED` đối với bước phân chia dữ liệu (split) **không bị kích hoạt**.

---

## 7. Kiểm toán Cấu trúc 7 Họ Đặc trưng dạng Histogram

Xác thực cấu trúc mô tả của UCI về 7 họ biến histogram (mỗi họ gồm 10 bins phân bố điều kiện vận hành từ bin `000` đến bin `009`, tổng cộng 70 thuộc tính):
1. Họ `ag`: gồm `ag_000` đến `ag_009` (10 bins)
2. Họ `ay`: gồm `ay_000` đến `ay_009` (10 bins)
3. Họ `az`: gồm `az_000` đến `az_009` (10 bins)
4. Họ `ba`: gồm `ba_000` đến `ba_009` (10 bins)
5. Họ `cn`: gồm `cn_000` đến `cn_009` (10 bins)
6. Họ `cs`: gồm `cs_000` đến `cs_009` (10 bins)
7. Họ `ee`: gồm `ee_000` đến `ee_009` (10 bins)

* Tổng số thuộc tính dạng Histogram: **70 thuộc tính**.
* Tổng số thuộc tính dạng Counter đơn lẻ: **100 thuộc tính**.
* Tổng cộng: Đúng **170 thuộc tính vận hành số học**.

---

## 8. Kiểm thử các Trường hợp Biên & Dị dạng Tổng hợp (Synthetic Edge-Case Tests)

Nhằm bảo đảm tính vững chắc của bộ parser và kiểm chứng khả năng bắt lỗi trước khi chuyển giao cho Codex, Antigravity đã thực hiện kiểm thử trên dữ liệu tổng hợp nhỏ độc lập (in-memory fixtures, không gây ô nhiễm tập dữ liệu Scania thật).

Toàn bộ các ca kiểm thử đều **gọi trực tiếp các hàm validator và parser cốt lõi** dùng chung cho tập dữ liệu Scania thật (`validate_binary_integrity`, `detect_bom_and_encoding`, `parse_and_validate_header`, `validate_target_token`, `validate_and_parse_numeric_cell`, `validate_source_row_id`, `parse_and_validate_row`, `audit_duplicates_and_conflicts`).

Bộ kiểm thử được chuẩn hóa thành **12 nhóm kiểm thử** với đúng **17 trường hợp kiểm thử con (sub-cases)**:

| Mã ca | Nhóm kiểm thử | Mô tả ca kiểm thử | Dữ liệu đầu vào (Input) | Kết quả mong đợi (Expected) | Kết quả thực tế (Actual) | Kết luận |
|---|---|---|---|---|---|:---:|
| 1.1 | 1. Header Presence & Format | Thiếu cột `class` trong dòng header | `'col_a,col_b\n1,2'` | `REJECTED_HEADER_MISSING` | `REJECTED_HEADER_MISSING` | **PASS** |
| 2.1 | 2. Schema & Column Width | Trùng lặp tên cột trong header | `'class,feat_a,feat_a'` | `REJECTED_DUPLICATE_COLUMN` | `REJECTED_DUPLICATE_COLUMN` | **PASS** |
| 2.2 | 2. Schema & Column Width | Dòng dữ liệu thiếu cột so với header | `['neg', '1.0']` (2 cột vs 3) | `REJECTED_ROW_WIDTH_MISMATCH` | `REJECTED_ROW_WIDTH_MISMATCH` | **PASS** |
| 3.1 | 3. Binary BOM & Encoding | Tiền tố Byte-Order Mark (BOM) lạ | `b'\xef\xbb\xbfclass,feat_a...'` | `REJECTED_BOM` | `REJECTED_BOM` | **PASS** |
| 3.2 | 3. Binary BOM & Encoding | Chuỗi byte ngoài chuẩn mã hóa UTF-8 | `b'class,feat_a\nneg,\xff\xfe1.0\n'` | `REJECTED_INVALID_ENCODING` | `REJECTED_INVALID_ENCODING` | **PASS** |
| 4.1 | 4. Missingness Token | Token thiếu lạ `'null'` ngoài `'na'` | `'null'` tại ô đặc trưng | `REJECTED_INVALID_TOKEN` | `REJECTED_INVALID_TOKEN` | **PASS** |
| 5.1 | 5. Target Label | Nhãn `'positive'` ngoài `'pos'`/`'neg'` | `'positive'` tại cột class | `REJECTED_INVALID_TARGET` | `REJECTED_INVALID_TARGET` | **PASS** |
| 6.1 | 6. Numeric & Finite Check | Giá trị chuỗi `'NaN'` | `'NaN'` tại ô đặc trưng | `REJECTED_NON_FINITE_TOKEN` | `REJECTED_NON_FINITE_TOKEN` | **PASS** |
| 6.2 | 6. Numeric & Finite Check | Giá trị dương vô cực `'inf'` | `'inf'` tại ô đặc trưng | `REJECTED_NON_FINITE_TOKEN` | `REJECTED_NON_FINITE_TOKEN` | **PASS** |
| 6.3 | 6. Numeric & Finite Check | Giá trị âm vô cực `'-inf'` | `'-inf'` tại ô đặc trưng | `REJECTED_NON_FINITE_TOKEN` | `REJECTED_NON_FINITE_TOKEN` | **PASS** |
| 6.4 | 6. Numeric & Finite Check | Chuỗi số thực dị dạng `'12.3.4'` | `'12.3.4'` tại ô đặc trưng | `REJECTED_FLOAT_PARSE_ERROR` | `REJECTED_FLOAT_PARSE_ERROR` | **PASS** |
| 7.1 | 7. Exact-X Duplicates (Same) | 2 dòng trùng lặp $X$ cùng nhãn `neg` | 2 dòng $X=(1.0, \text{na})$, target=neg | `BLOCKED_DUPLICATES_1` | `BLOCKED_DUPLICATES_1` | **PASS** |
| 8.1 | 8. Exact-X Duplicates (Conflict) | 2 dòng trùng lặp $X$ khác nhãn (neg vs pos) | 2 dòng $X=(1.0, \text{na})$, neg vs pos | `BLOCKED_CONFLICTS_1` | `BLOCKED_CONFLICTS_1` | **PASS** |
| 9.1 | 9. All-Missing Row Retention | Dòng thiếu toàn bộ 170 đặc trưng | `['neg', 'na', 'na']` | `ROW_PRESERVED_ALL_NA` | `ROW_PRESERVED_ALL_NA` | **PASS** |
| 10.1 | 10. Constant & All-Missing | Nhận diện cột hằng số và cột missing 100% | `feat_c=[5.0, 5.0]`, `feat_m=[na, na]` | `CONSTANT_AND_ALL_MISSING_PROFILED` | `CONSTANT_AND_ALL_MISSING_PROFILED` | **PASS** |
| 11.1 | 11. Source-Row ID Integrity | Cấu trúc tuple 1-based tăng đơn điệu | Dòng 1, 2, 3 với SHA và split | `SOURCE_ROW_IDS_VALIDATED` | `SOURCE_ROW_IDS_VALIDATED` | **PASS** |
| 12.1 | 12. Binary Checksum Mismatch | Tệp bị can thiệp sai lệch mã băm SHA-256 | `b'tampered bytes...'` với SHA Train thật | `REJECTED_HASH_MISMATCH` | `REJECTED_HASH_MISMATCH` | **PASS** |

> [!NOTE]
> - **Nguyên tắc đánh giá kiểm thử:** Đối với dữ liệu dị dạng hoặc sai mã băm (như Ca 12), việc hệ thống từ chối đúng quy cách (`actual_outcome == expected_outcome`) được tính là **PASS** của bài kiểm thử. Tuyệt đối không nhầm lẫn việc từ chối dữ liệu sai với việc bài kiểm thử bị hỏng.
> - **Cơ chế nghiệm thu nghiêm ngặt:** Toàn bộ 17 ca con đều nằm trong điều kiện nghiệm thu `assert all(t['conclusion'] == 'PASS')`, hoàn toàn không loại trừ Ca 12 hay bất kỳ ca nào.
> - **Xác minh cơ chế bắt lỗi của Harness (Negative Self-Verification):** Đã kiểm chứng độc lập một trường hợp giả lập lỗi (`actual != expected`) để chứng minh hệ thống gắn cờ `FAIL` thật sự khi có sai lệch ngoài dự kiến, không nuốt lỗi.

### 8.2. Kiểm thử Đơn vị Logic Cổng Kỹ thuật G2 (12 Unit Tests)

Để kiểm chứng toàn diện tính chính xác của hàm quyết định trạng thái `compute_g2_technical_gate_status()` trước mọi kịch bản biên và các trạng thái đầu vào dị dạng, một bộ kiểm thử đơn vị độc lập gồm **12 unit tests** đã được thực thi:

| Mã Test | Mô tả kịch bản kiểm thử | Trạng thái kỳ vọng | Trạng thái thực tế | Kết luận |
|---|---|---|---|:---:|
| **TG-01** | Tất cả điều kiện đạt chuẩn, P03 `PASSED`, nguồn và bằng chứng xác minh | `PASS` | `PASS` | **PASS** |
| **TG-02** | P03 `BLOCKED` khi mọi cổng kiểm toán khác đều đạt | `BLOCKED` | `BLOCKED` | **PASS** |
| **TG-03** | Kiểm tra toàn vẹn nhị phân P01 thất bại (`False`) | `FAIL` | `FAIL` | **PASS** |
| **TG-04** | Thiếu bằng chứng kiểm toán bắt buộc (`mandatory_checks_verified=False`) | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** |
| **TG-05** | Xung đột ưu tiên: vừa có lỗi bắt buộc vừa có P03 `BLOCKED` (`FAIL` ưu tiên) | `FAIL` | `FAIL` | **PASS** |
| **TG-06a**| P03 nhận trạng thái lạ không hợp lệ (`'UNKNOWN'`) | `FAIL` | `FAIL` | **PASS** |
| **TG-06b**| P03 nhận giá trị rỗng / `None` | `FAIL` | `FAIL` | **PASS** |
| **TG-06c**| P03 nhận chuỗi rỗng `''` | `FAIL` | `FAIL` | **PASS** |
| **TG-07** | Có bài kiểm thử biên không đạt (`synthetic_tests_pass=False`) | `FAIL` | `FAIL` | **PASS** |
| **TG-08** | Nguồn bắt buộc Train CSV chưa được xác minh live | `NOT_VERIFIED` | `NOT_VERIFIED` | **PASS** |
| **TG-09** | Cổng cấu trúc header schema thất bại (`False`) | `FAIL` | `FAIL` | **PASS** |
| **TG-10** | Cổng kiểm toán nhãn biến mục tiêu thất bại (`False`) | `FAIL` | `FAIL` | **PASS** |

*Tất cả 12 unit tests của Gate logic đều đạt **PASS 100%**, khẳng định quy tắc ưu tiên $\mathbf{FAIL} > \mathbf{BLOCKED} > \mathbf{NOT\_VERIFIED} > \mathbf{PASS}$ được thực thi nghiêm ngặt, không thể bị ghi đè ngầm.*

### 8.3. Kiểm thử Tích hợp Toàn diện Quy trình Kiểm toán (10 Integration Tests - F4)

Đáp ứng đầy đủ khuyến nghị F4 từ báo cáo Codex, bộ kiểm thử tích hợp thực chất này kiểm chứng toàn bộ chu trình $\text{Input} \rightarrow \text{Parser} \rightarrow \text{Audit} \rightarrow \text{Gate} \rightarrow \text{Artifact Export} \rightarrow \text{Final Status}$ trên fixtures tổng hợp độc lập (in-memory và temporary directory), sử dụng chung các hàm production (`compute_feature_profiles`, `export_run_artifacts`, `load_or_rebuild_runs_index`):

| Mã Test | Mô tả Kịch bản Kiểm thử Tích hợp | Trạng thái Kỳ vọng | Kết luận |
|:---:|---|:---:|:---:|
| **IT-01** | E2E Pipeline trên dữ liệu sạch $\rightarrow$ Trạng thái `PASS` & Xuất đủ 5 artifacts kèm `run_manifest.json` | `PASS` | **PASS** |
| **IT-02** | E2E Pipeline trên dữ liệu Duplicate cùng nhãn $\rightarrow$ Trạng thái `BLOCKED`, không crash, xuất đầy đủ 5 artifacts + manifest | `PASS` | **PASS** |
| **IT-03** | E2E Pipeline trên dữ liệu Xung đột nhãn $\rightarrow$ Trạng thái `BLOCKED`, không crash, xuất đầy đủ nhóm xung đột và ID dòng | `PASS` | **PASS** |
| **IT-04** | E2E Pipeline dữ liệu hỏng Schema / Token cấm $\rightarrow$ Bị từ chối dừng tại cổng, lưu bằng chứng `FAIL` thực tế vào artifact trên đĩa | `PASS` | **PASS** |
| **IT-05** | E2E Pipeline thiếu bằng chứng bắt buộc $\rightarrow$ Xuất bằng chứng run với trạng thái `NOT_VERIFIED` | `PASS` | **PASS** |
| **IT-06** | Run Preservation & Anti-Overwrite: Chạy Run A (`PASS`) và Run B (`BLOCKED`) lưu độc lập; cơ chế exclusive write (`mode_exclusive=True`) chặn đứng ghi đè ở cấp OS | `PASS` | **PASS** |
| **IT-07** | Atomic Safe Write: Giả lập lỗi ghi giữa chừng, tệp đích không bị hỏng, tệp tạm `.tmp` được dọn sạch | `PASS` | **PASS** |
| **IT-08** | Synthetic Feature Profiling Accuracy: Gọi hàm production `compute_feature_profiles` kiểm toán chính xác min, max, mean, missing rate và zero-variance trên nghiệm giải tích | `PASS` | **PASS** |
| **IT-09** | Negative Integration Harness Verification: Xác nhận harness phát hiện và báo lỗi thật khi có sai lệch giả lập | `PASS` | **PASS** |
| **IT-10** | Index Corruption Resilience & Auto-Rebuild: Giả lập `runs_index.json` bị hỏng cú pháp, kiểm chứng hệ thống tự động sao lưu tệp hỏng thành `.corrupted_<timestamp>` và tái dựng index chính xác từ các `run_manifest.json` hợp lệ trên đĩa | `PASS` | **PASS** |

*Tổng kết Integration Tests:* **10/10 tests đạt PASS 100%**.

### 8.4. Kiến trúc Bảo toàn Bằng chứng Lượt chạy (Run Preservation Architecture - F2 & F3)

- **Cấu trúc lưu trữ độc lập theo Run:** Mỗi lần thực thi notebook sinh ra một `run_id` duy nhất (ví dụ `run_20261026_123410_de3400`). Toàn bộ 5 artifacts của run đó cùng chứng chỉ hoàn tất `run_manifest.json` được lưu trữ bất biến tại thư mục `results/scania_aps/g2_audit/runs/<run_id>/`.
- **Cơ chế ghi file độc quyền (OS-Level Exclusive Creation):** Áp dụng cờ `open(..., 'x')` (`O_CREAT | O_EXCL`) cho các file trong thư mục run. Nếu file đã tồn tại, hệ điều hành lập tức ném lỗi `FileExistsError`, loại trừ hoàn toàn nguy cơ race condition hay vô tình ghi đè.
- **Chứng chỉ hoàn tất (Completion Marker - `run_manifest.json`):** Mỗi thư mục run hoàn tất đều chứa `run_manifest.json` ghi nhận `lifecycle_state` (`COMPLETE` hoặc `FAILED`), `final_gate_status`, timestamp UTC và mã băm SHA-256 của từng artifact trong run.
- **Mục lục lịch sử tự phục hồi (`runs_index.json`):** Ghi nhận có hệ thống thông tin mọi lượt chạy gồm `run_id`, timestamp UTC, thời gian đo thực tế (`train_audit_duration_seconds`), commit SHA, trạng thái worktree, trạng thái Cổng G2 và Cổng P03. Khi phát hiện tệp index bị hỏng, hệ thống tự động sao lưu sang `runs_index.json.corrupted_<timestamp>` và tự động tái dựng index từ các `run_manifest.json` có sẵn trên đĩa.
- **Cập nhật an toàn tệp hiển thị tại root:** Các tệp tại `results/scania_aps/g2_audit/` được cập nhật qua cơ chế thay thế nguyên tử (atomic write qua `.tmp` và `os.replace()`) để phục vụ CI/Reviewer truy cập nhanh mà không ảnh hưởng đến các run lịch sử.
- **Quy ước Line Ending (LF vs CRLF):** Tài liệu quy định rõ: Git blob chuẩn hóa xuống dòng LF; trên môi trường Windows làm việc cục bộ, tệp text có thể lưu CRLF. Mã băm SHA-256 đối chiếu nội dung chuẩn hóa (decoded content) là đồng nhất tuyệt đối.

### 8.5. Rà soát Riêng tư & Lịch sử Git (Privacy Audit - F5)

Đã tiến hành rà soát chuyên sâu toàn bộ các commit của PR #14 (`origin/main..HEAD`):
1. **Kiểm toán Bí mật & Thông tin Nhạy cảm cao:** Xác nhận **100% KHÔNG có API key, token, credentials, hay password nào** trong bất kỳ commit nào của PR.
2. **Các Commit từng chứa Đường dẫn Cá nhân Cục bộ:**
   - Commit `fde5004` (commit đầu tiên của PR) và `b9176c3`: Chứa đường dẫn máy cá nhân cục bộ (`D:\Năm 3\...`) trong `00_source_audit.ipynb` và `environment.json`.
   - Commit `e50afdf`: Chứa đường dẫn máy cá nhân trong notebook outputs.
   - Commit `2d8586b` và các commit tiếp theo: Đã khử sạch hoàn toàn, thay thế bằng `<workspace_root>`.
3. **Hiện trạng tại HEAD:** Tất cả các tệp tại HEAD commit **SẠCH 100%**, không chứa bất kỳ đường dẫn cá nhân nào.
4. **Quy định xử lý:** Tuân thủ quy định không force-push hay rewrite Git history của PR. Khi Chủ dự án nghiệm thu, tính năng **"Squash and merge"** của GitHub sẽ gộp PR thành 1 commit duy nhất sạch sẽ trên `main`. Nếu Chủ dự án muốn xóa sạch dấu vết trong ref PR cũ trên GitHub, cần sự can thiệp từ quản trị viên repository bằng công cụ chuyên dụng (`git-filter-repo`).

---

## 9. Các Phát hiện Bất thường cần Chủ dự án Quyết định trước SC-G3-C

Dựa trên kết quả kiểm toán thực nghiệm, Antigravity trình Chủ dự án 4 điểm kỹ thuật cần xem xét và ban hành quyết định trước khi giao Codex triển khai SC-G3-C (Data Pipeline):

1. **Quyết định đối với thuộc tính hằng số `cd_000`:**
   * *Hiện trạng:* `cd_000` có giá trị duy nhất $1.209.600,0$ trên toàn bộ 59.324 dòng quan sát được ($98,87\%$) và 676 dòng khuyết thiếu ($1,13\%$).
   * *Đề xuất P05 của Codex:* Giữ nguyên toàn bộ 170 cột, điền khuyết bằng `SimpleImputer(strategy='median')`. Khi điền median, 676 ô thiếu cũng sẽ nhận giá trị $1.209.600,0$, biến toàn bộ cột `cd_000` thành hằng số tuyệt đối với độ lệch chuẩn $\sigma = 0$.
   * *Kiến nghị Antigravity:* Cho phép giữ nguyên theo đề xuất P05 để đảm bảo tính ổn định về số chiều ma trận đặc trưng, nhưng cần kiểm tra cẩn trọng với các bộ chuẩn hóa như `StandardScaler` (tránh lỗi chia cho 0 hoặc sinh giá trị NaN/Warning).
2. **Quyết định đối với 8 cột có tỷ lệ khuyết thiếu cực đoan (> 50%):**
   * *Hiện trạng:* 8 cột có tỷ lệ missing từ $65,92\%$ đến $82,11\%$ (`br_000`, `bq_000`, `bp_000`, `bo_000`, `ab_000`, `cr_000`, `bn_000`, `bm_000`).
   * *Đề xuất P05 của Codex:* Không loại bỏ cột theo tỷ lệ missing (no column drop), giữ nguyên toàn bộ 170 biến và điền median.
   * *Kiến nghị Antigravity:* Đồng thuận giữ nguyên P05 ở cấu hình cơ sở (baseline) theo đúng định hướng S7 nhằm tránh rò rỉ thông tin trước khi kiểm thử trên tập Validation, không tự ý lọc cột ở G2.
3. **Quyết định đối với các dòng có tỷ lệ thiếu rất cao:**
   * *Hiện trạng:* Tồn tại các dòng dữ liệu bị khuyết thiếu tới 168/170 thuộc tính.
   * *Đề xuất P05 của Codex:* Giữ lại toàn bộ các dòng có nhãn hợp lệ, không xóa dòng (drop rows).
   * *Kiến nghị Antigravity:* Giữ nguyên chính sách không xóa dòng để bảo đảm quy mô dữ liệu chính xác 60.000 dòng phục vụ phân tầng stratified split 80/20.
4. **Phê duyệt phân chia dữ liệu (Stratified Split 80/20 - P04):**
   * Vì kết quả kiểm toán trùng lặp P03 đạt `PASSED` (0 duplicate, 0 conflict), điều kiện dừng phân chia không bị kích hoạt.
   * Kính đề nghị Chủ dự án chính thức phê duyệt phân chia Train 48.000 / Validation 12.000 theo phương án P04 (stratified split với seed 42) để Codex triển khai trong SC-G3-C.

---

## 10. Đánh giá Trạng thái Nghiệm thu & Sẵn sàng

* **Độ đầy đủ sản phẩm bàn giao G2 (Final Corrections):**
  * Đã xác thực provenance nguồn UCI 421, mã băm SHA-256 các tệp raw và niêm phong tập Test.
  * Đã kiểm toán 100% tệp Train 60.000 mẫu, phát hiện header tại dòng 21 (0-based index 20), xác nhận 1 cột `class` và 170 cột đặc trưng số học.
  * Đã lập Từ điển dữ liệu chi tiết 171 thuộc tính tại `docs/scania/data_dictionary.md` kèm ghi chú làm tròn, giới hạn float64 và ranh giới dữ liệu ẩn danh.
  * Đã xây dựng và kiểm chứng notebook chạy lại được tại `notebooks/scania/00_source_audit.ipynb` với bộ điều phối `ScaniaSourceAuditOrchestrator`, kiến trúc bảo toàn bằng chứng từng run, 17 ca kiểm thử biên, 12 unit tests cổng logic và 14 bài integration tests end-to-end (bao gồm kiểm thử xử lý thiếu tệp nguồn và tương thích phương thức báo lỗi).
  * Đã chuẩn hóa quy chuẩn băm SHA-256 đa nền tảng (`CANONICAL_LF_UTF8`), kiểm chứng tính tương đương 100% giữa Windows CRLF và Git LF blobs mà không làm thay đổi hay giả mạo dữ liệu.
  * Đã khử sạch hoàn toàn thông tin cá nhân/đường dẫn tuyệt đối trong outputs về `<workspace_root>` và `<temporary_test_dir>`.
  * Đã bổ sung provenance đầy đủ: `canonical_code_digest` (`ec2593b303c30f589283f83a6eda9ce8ca1fd3d5f1ccba7a2c90b3d9ca3e4224`), thuật toán băm code cells, lệnh thực thi, kernel, runtime và môi trường.
  * Đã tăng cường khả năng phục hồi tự động của `load_or_rebuild_runs_index` qua 8 kịch bản hỏng hóc, thiếu file, sai checksum và xung đột ID.
  * Đã lưu trữ toàn bộ logs, summary JSON, snapshot môi trường và từng run độc lập tại `results/scania_aps/g2_audit/**` và `results/scania_aps/g2_audit/runs/**`.
* **Cơ chế tính toán Cổng Kỹ thuật G2:**
  * Trạng thái cổng kỹ thuật được tính toán động theo quy tắc ưu tiên nghiêm ngặt: $\mathbf{FAIL} > \mathbf{BLOCKED} > \mathbf{NOT\_VERIFIED} > \mathbf{PASS}$.
  * Mọi kiểm toán toàn vẹn, schema, nhãn, missingness, histogram và toàn bộ 43 trường hợp kiểm thử (17 synthetic subcases + 12 gate logic tests + 14 integration tests) đều đạt 100% không có lỗi; cổng trùng lặp P03 đạt `PASSED` $\rightarrow$ Trạng thái Cổng Kỹ thuật đạt: **`PASS`**.
* **Trạng thái cổng nghiệm thu cuối cùng:**

```text
SC-G2-A FINAL CORRECTIONS: PASS
G2 AUDIT TECHNICAL GATES: PASS
RUN EVIDENCE INTEGRITY: PASS
GIT SNAPSHOT CHECKSUM VERIFICATION: PASS
READY FOR INDEPENDENT CODEX RE-REVIEW: YES
READY FOR SCANIA G3 EXECUTION: NO – PENDING OWNER ACCEPTANCE AND P04/P05 APPROVAL
```
