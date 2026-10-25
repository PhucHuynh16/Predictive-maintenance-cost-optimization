# SC-G2-A — Data Dictionary: APS Failure at Scania Trucks

Ngày lập: **2026-10-25 (Asia/Saigon)**  
Người thực hiện: **Antigravity (Data Audit Specialist)**  
Nhiệm vụ: **SC-G2-A (Giai đoạn G2 Kiểm toán nguồn)**  
Mã tham chiếu quyết định: **P01, P03, P10** trong `docs/scania/decision_register.md`  

---

## 1. Thông tin Tổng quan và Nguồn Dữ liệu

* **Tên tập dữ liệu:** APS Failure at Scania Trucks (UCI Machine Learning Repository ID: 421)
* **DOI chính thức:** [10.24432/C51S51](https://doi.org/10.24432/C51S51)
* **URL nguồn:** `https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks`
* **Tổ chức nguồn cấp:** Scania CV AB, Södertälje, Stockholm, Thụy Điển
* **Tác giả hiến tặng:** Tony Lindgren (tony@dsv.su.se) và Jonas Biteus (jonas.biteus@scania.com), tháng 9/2016
* **Giấy phép bản quyền:** Creative Commons Attribution 4.0 International (CC BY 4.0) & Scania CV AB GNU General Public License v3 (GPLv3)
* **Tệp Train được kiểm toán:** `aps_failure_training_set.csv` (44.669.194 bytes, SHA-256: `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da`)
* **Tệp Test:** `aps_failure_test_set.csv` (11.943.558 bytes) — Được niêm phong (sealed) bên trong tệp nén gốc `aps+failure+at+scania+trucks.zip` (SHA-256: `5504d0402f54faaf97ac0ca085a621645763f5cfea2eb29c592b057d43d4db89`), tuyệt đối không mở hoặc khảo sát trước G10.

## 2. Đặc tả Biến Mục tiêu (Target Variable)

Biến mục tiêu nằm ở cột đầu tiên (`index = 0`) mang tên `class`:

| Tên cột | Giá trị Raw Token | Ánh xạ Số học (`mapped_class`) | Ý nghĩa Kỹ thuật / Nghiệp vụ | Số lượng mẫu (Train 60.000) | Tỷ lệ (%) |
|---|---|---|---|---|---|
| `class` | `neg` | `0` | Xe gặp sự cố hoặc cần bảo dưỡng ở các bộ phận khác **không liên quan đến Hệ thống Khí nén (APS)** | 59.000 | 98,33% |
| `class` | `pos` | `1` | Xe gặp sự cố hỏng hóc xuất phát từ một linh kiện cụ thể của **Hệ thống Khí nén (Air Pressure System - APS)** | 1.000 | 1,67% |

> [!NOTE]
> Nhãn `neg=0` không đồng nghĩa xe hoàn toàn khỏe mạnh (healthy), mà chỉ biểu thị lỗi phát sinh ngoài hệ thống APS. Tỷ lệ mất cân bằng lớp là xấp xỉ **59 : 1** (Imbalance Ratio).

## 3. Cấu trúc Đặc trưng Vận hành (Operational Features Schema)

Toàn bộ 170 đặc trưng vận hành đều ở dạng số học (numerical), được Scania ẩn danh vì lý do bảo mật công nghệ. Cấu trúc gồm 2 nhóm chính:

1. **7 họ đặc trưng dạng Histogram (70 thuộc tính):** Đại diện cho phân bố tần suất tích lũy của cảm biến qua 10 ngưỡng điều kiện vận hành (bin 000 đến bin 009, với các điều kiện mở ở 2 đầu):
   - `ag_000` đến `ag_009` (10 bins)
   - `ay_000` đến `ay_009` (10 bins)
   - `az_000` đến `az_009` (10 bins)
   - `ba_000` đến `ba_009` (10 bins)
   - `cn_000` đến `cn_009` (10 bins)
   - `cs_000` đến `cs_009` (10 bins)
   - `ee_000` đến `ee_009` (10 bins)
2. **100 đặc trưng đếm số học đơn lẻ (Single Numerical Counters):** Ví dụ `aa_000`, `ac_000`, `ad_000`, ..., `eg_000`.

## 4. Hợp đồng Định danh Dòng nguồn (`source_row_id`)

Để truy vết nguồn dữ liệu mà không làm rò rỉ hoặc xáo trộn phân phối học máy, mỗi bản ghi được gắn một định danh nguồn không trùng lặp:
$$\text{source\_row\_id} = (\text{official\_train\_sha256}, \text{"train"}, \text{data\_row\_number})$$
* `official_train_sha256`: `bb484302e3a3a1c8ef5e1f0129c4dc7cbd58f350867f95b575461ca21ab6b9da`
* `official_partition_name`: `"train"`
* `data_row_number`: Chỉ số thứ tự 1-based của dòng dữ liệu sau dòng header (từ 1 đến 60.000).
* **Quy định bất khả xâm phạm:** `source_row_id` chỉ dùng để truy vết dữ liệu và đối chiếu phân chia tập Train/Validation tại G3; tuyệt đối không đưa vào ma trận đặc trưng $X$.

## 5. Bảng Từ điển 170 Thuộc tính Vận hành (Kiểm toán Thực tế Train 60.000)

| STT | Tên thuộc tính | Phân loại | Kiểu dữ liệu | Quan sát (`observed`) | Khuyết thiếu (`missing`) | Tỷ lệ thiếu (%) | Min | Max | Trung bình (`mean`) | Ghi chú kiểm toán |
|---:|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | `aa_000` | Counter | float64 | 60,000 | 0 | 0.00% | 0.0 | 2746564.0 | 59336.50 | 0% missing |
| 2 | `ab_000` | Counter | float64 | 13,671 | 46,329 | 77.22% | 0.0 | 204.0 | 0.71 | **Missing > 70%** |
| 3 | `ac_000` | Counter | float64 | 56,665 | 3,335 | 5.56% | 0.0 | 2130706796.0 | 356014263.03 | Bình thường |
| 4 | `ad_000` | Counter | float64 | 45,139 | 14,861 | 24.77% | 0.0 | 8584297742.0 | 190620.64 | Bình thường |
| 5 | `ae_000` | Counter | float64 | 57,500 | 2,500 | 4.17% | 0.0 | 21050.0 | 6.82 | Bình thường |
| 6 | `af_000` | Counter | float64 | 57,500 | 2,500 | 4.17% | 0.0 | 20070.0 | 11.01 | Bình thường |
| 7 | `ag_000` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 3376892.0 | 221.64 | Bình thường |
| 8 | `ag_001` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 4109372.0 | 975.72 | Bình thường |
| 9 | `ag_002` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 10552856.0 | 8606.01 | Bình thường |
| 10 | `ag_003` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 63402074.0 | 88591.28 | Bình thường |
| 11 | `ag_004` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 228830570.0 | 437096.63 | Bình thường |
| 12 | `ag_005` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 179187978.0 | 1108373.83 | Bình thường |
| 13 | `ag_006` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 94020666.0 | 1657817.89 | Bình thường |
| 14 | `ag_007` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 63346754.0 | 499309.80 | Bình thường |
| 15 | `ag_008` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 17702522.0 | 35569.89 | Bình thường |
| 16 | `ag_009` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 25198514.0 | 5114.75 | Bình thường |
| 17 | `ah_000` | Counter | float64 | 59,355 | 645 | 1.07% | 0.0 | 74247318.0 | 1809931.18 | Bình thường |
| 18 | `ai_000` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 16512852.0 | 9016.97 | Bình thường |
| 19 | `aj_000` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 5629340.0 | 1143.67 | Bình thường |
| 20 | `ak_000` | Counter | float64 | 55,600 | 4,400 | 7.33% | 0.0 | 10444924.0 | 979.49 | Bình thường |
| 21 | `al_000` | Counter | float64 | 59,358 | 642 | 1.07% | 0.0 | 34762578.0 | 59130.48 | Bình thường |
| 22 | `am_0` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 55903508.0 | 93281.33 | Bình thường |
| 23 | `an_000` | Counter | float64 | 59,358 | 642 | 1.07% | 0.0 | 140861830.0 | 3461037.04 | Bình thường |
| 24 | `ao_000` | Counter | float64 | 59,411 | 589 | 0.98% | 0.0 | 122201822.0 | 3002440.31 | Bình thường |
| 25 | `ap_000` | Counter | float64 | 59,358 | 642 | 1.07% | 0.0 | 77934944.0 | 1004159.56 | Bình thường |
| 26 | `aq_000` | Counter | float64 | 59,411 | 589 | 0.98% | 0.0 | 25562646.0 | 442404.46 | Bình thường |
| 27 | `ar_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 350.0 | 0.50 | Bình thường |
| 28 | `as_000` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 1655240.0 | 126.74 | Bình thường |
| 29 | `at_000` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 10400504.0 | 5072.05 | Bình thường |
| 30 | `au_000` | Counter | float64 | 59,371 | 629 | 1.05% | 0.0 | 2626676.0 | 230.58 | Bình thường |
| 31 | `av_000` | Counter | float64 | 57,500 | 2,500 | 4.17% | 0.0 | 794458.0 | 1117.83 | Bình thường |
| 32 | `ax_000` | Counter | float64 | 57,499 | 2,501 | 4.17% | 0.0 | 116652.0 | 374.33 | Bình thường |
| 33 | `ay_000` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 50553892.0 | 12211.65 | Bình thường |
| 34 | `ay_001` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 80525378.0 | 10190.12 | Bình thường |
| 35 | `ay_002` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 28474838.0 | 10975.00 | Bình thường |
| 36 | `ay_003` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 13945170.0 | 7225.78 | Bình thường |
| 37 | `ay_004` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 40028704.0 | 10566.00 | Bình thường |
| 38 | `ay_005` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 124948914.0 | 111979.11 | Bình thường |
| 39 | `ay_006` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 127680326.0 | 1078551.20 | Bình thường |
| 40 | `ay_007` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 489678156.0 | 1546032.36 | Bình thường |
| 41 | `ay_008` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 104566992.0 | 1051122.96 | Bình thường |
| 42 | `ay_009` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 18824656.0 | 1162.62 | Bình thường |
| 43 | `az_000` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 10124620.0 | 7849.61 | Bình thường |
| 44 | `az_001` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 4530258.0 | 4420.99 | Bình thường |
| 45 | `az_002` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 14217662.0 | 8066.08 | Bình thường |
| 46 | `az_003` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 45584242.0 | 87240.82 | Bình thường |
| 47 | `az_004` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 123047106.0 | 1476896.66 | Bình thường |
| 48 | `az_005` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 467832334.0 | 2135583.86 | Bình thường |
| 49 | `az_006` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 64589140.0 | 101894.26 | Bình thường |
| 50 | `az_007` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 39158218.0 | 17377.82 | Bình thường |
| 51 | `az_008` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 1947884.0 | 661.79 | Bình thường |
| 52 | `az_009` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 666148.0 | 42.07 | Bình thường |
| 53 | `ba_000` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 232871714.0 | 1399651.96 | Bình thường |
| 54 | `ba_001` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 116283282.0 | 894117.47 | Bình thường |
| 55 | `ba_002` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 55807388.0 | 413096.93 | Bình thường |
| 56 | `ba_003` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 36931418.0 | 274006.96 | Bình thường |
| 57 | `ba_004` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 25158556.0 | 204875.58 | Bình thường |
| 58 | `ba_005` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 19208664.0 | 188941.19 | Bình thường |
| 59 | `ba_006` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 18997660.0 | 210628.82 | Bình thường |
| 60 | `ba_007` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 14314086.0 | 185787.39 | Bình thường |
| 61 | `ba_008` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 31265984.0 | 35882.84 | Bình thường |
| 62 | `ba_009` | Histogram Bin | float64 | 59,312 | 688 | 1.15% | 0.0 | 43706408.0 | 35766.72 | Bình thường |
| 63 | `bb_000` | Counter | float64 | 59,355 | 645 | 1.07% | 0.0 | 192871534.0 | 4526177.19 | Bình thường |
| 64 | `bc_000` | Counter | float64 | 57,275 | 2,725 | 4.54% | 0.0 | 396952.0 | 569.53 | Bình thường |
| 65 | `bd_000` | Counter | float64 | 57,273 | 2,727 | 4.54% | 0.0 | 306452.0 | 921.78 | Bình thường |
| 66 | `be_000` | Counter | float64 | 57,497 | 2,503 | 4.17% | 0.0 | 810568.0 | 1372.65 | Bình thường |
| 67 | `bf_000` | Counter | float64 | 57,500 | 2,500 | 4.17% | 0.0 | 51050.0 | 74.88 | Bình thường |
| 68 | `bg_000` | Counter | float64 | 59,358 | 642 | 1.07% | 0.0 | 74247318.0 | 1809430.98 | Bình thường |
| 69 | `bh_000` | Counter | float64 | 59,358 | 642 | 1.07% | 0.0 | 3200582.0 | 57943.08 | Bình thường |
| 70 | `bi_000` | Counter | float64 | 59,411 | 589 | 0.98% | 0.0 | 44937496.0 | 492207.57 | Bình thường |
| 71 | `bj_000` | Counter | float64 | 59,411 | 589 | 0.98% | 0.0 | 45736316.0 | 510089.23 | Bình thường |
| 72 | `bk_000` | Counter | float64 | 36,966 | 23,034 | 38.39% | 0.0 | 1310700.0 | 280429.11 | Bình thường |
| 73 | `bl_000` | Counter | float64 | 32,723 | 27,277 | 45.46% | 0.0 | 1310700.0 | 321353.69 | Bình thường |
| 74 | `bm_000` | Counter | float64 | 20,451 | 39,549 | 65.92% | 0.0 | 1310700.0 | 399603.17 | Missing > 50% |
| 75 | `bn_000` | Counter | float64 | 15,991 | 44,009 | 73.35% | 0.0 | 1310700.0 | 463710.83 | **Missing > 70%** |
| 76 | `bo_000` | Counter | float64 | 13,667 | 46,333 | 77.22% | 0.0 | 1310700.0 | 513147.82 | **Missing > 70%** |
| 77 | `bp_000` | Counter | float64 | 12,260 | 47,740 | 79.57% | 0.0 | 1310700.0 | 551389.80 | **Missing > 70%** |
| 78 | `bq_000` | Counter | float64 | 11,278 | 48,722 | 81.20% | 0.0 | 1310700.0 | 582871.32 | **Missing > 80%** |
| 79 | `br_000` | Counter | float64 | 10,736 | 49,264 | 82.11% | 0.0 | 1310700.0 | 604886.61 | **Missing > 80%** |
| 80 | `bs_000` | Counter | float64 | 59,274 | 726 | 1.21% | 0.0 | 1037240.0 | 80360.55 | Bình thường |
| 81 | `bt_000` | Counter | float64 | 59,833 | 167 | 0.28% | 0.0 | 2746564.8 | 59416.50 | Bình thường |
| 82 | `bu_000` | Counter | float64 | 59,309 | 691 | 1.15% | 0.0 | 192871534.0 | 4515324.70 | Bình thường |
| 83 | `bv_000` | Counter | float64 | 59,309 | 691 | 1.15% | 0.0 | 192871534.0 | 4515325.29 | Bình thường |
| 84 | `bx_000` | Counter | float64 | 56,743 | 3,257 | 5.43% | 172.0 | 186353854.0 | 4112218.10 | Bình thường |
| 85 | `by_000` | Counter | float64 | 59,527 | 473 | 0.79% | 0.0 | 1002003.0 | 22028.93 | Bình thường |
| 86 | `bz_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 40542588.0 | 101960.84 | Bình thường |
| 87 | `ca_000` | Counter | float64 | 55,644 | 4,356 | 7.26% | 0.0 | 120956.0 | 39168.82 | Bình thường |
| 88 | `cb_000` | Counter | float64 | 59,274 | 726 | 1.21% | 0.0 | 1209520.0 | 405638.15 | Bình thường |
| 89 | `cc_000` | Counter | float64 | 56,745 | 3,255 | 5.42% | 0.0 | 148615188.0 | 3803443.56 | Bình thường |
| 90 | `cd_000` | Counter | float64 | 59,324 | 676 | 1.13% | 1209600.0 | 1209600.0 | 1209600.00 | **CONSTANT (Zero Variance)** |
| 91 | `ce_000` | Counter | float64 | 57,498 | 2,502 | 4.17% | 0.0 | 4908098.0 | 64343.56 | Bình thường |
| 92 | `cf_000` | Counter | float64 | 45,139 | 14,861 | 24.77% | 0.0 | 8584297736.0 | 190221.81 | Bình thường |
| 93 | `cg_000` | Counter | float64 | 45,139 | 14,861 | 24.77% | 0.0 | 21400.0 | 91.52 | Bình thường |
| 94 | `ch_000` | Counter | float64 | 45,139 | 14,861 | 24.77% | 0.0 | 2.0 | 0.00 | Bình thường |
| 95 | `ci_000` | Counter | float64 | 59,662 | 338 | 0.56% | 0.0 | 140986129.9 | 3481204.05 | Bình thường |
| 96 | `cj_000` | Counter | float64 | 59,662 | 338 | 0.56% | 0.0 | 60949671.4 | 102841.85 | Bình thường |
| 97 | `ck_000` | Counter | float64 | 59,662 | 338 | 0.56% | 0.0 | 55428669.1 | 714342.70 | Bình thường |
| 98 | `cl_000` | Counter | float64 | 50,447 | 9,553 | 15.92% | 0.0 | 130560.0 | 343.02 | Bình thường |
| 99 | `cm_000` | Counter | float64 | 50,123 | 9,877 | 16.46% | 0.0 | 73370.0 | 343.10 | Bình thường |
| 100 | `cn_000` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 6278490.0 | 2336.67 | Bình thường |
| 101 | `cn_001` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 14512994.0 | 21951.49 | Bình thường |
| 102 | `cn_002` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 58508606.0 | 161050.88 | Bình thường |
| 103 | `cn_003` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 94979324.0 | 531477.96 | Bình thường |
| 104 | `cn_004` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 169869316.0 | 1282835.14 | Bình thường |
| 105 | `cn_005` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 117815764.0 | 1341058.71 | Bình thường |
| 106 | `cn_006` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 72080406.0 | 410564.09 | Bình thường |
| 107 | `cn_007` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 33143734.0 | 64425.13 | Bình thường |
| 108 | `cn_008` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 7541716.0 | 19226.79 | Bình thường |
| 109 | `cn_009` | Histogram Bin | float64 | 59,313 | 687 | 1.15% | 0.0 | 36398374.0 | 7820.47 | Bình thường |
| 110 | `co_000` | Counter | float64 | 45,139 | 14,861 | 24.77% | 0.0 | 8584297742.0 | 190515.57 | Bình thường |
| 111 | `cp_000` | Counter | float64 | 57,276 | 2,724 | 4.54% | 0.0 | 496360.0 | 570.40 | Bình thường |
| 112 | `cq_000` | Counter | float64 | 59,309 | 691 | 1.15% | 0.0 | 192871534.0 | 4515325.18 | Bình thường |
| 113 | `cr_000` | Counter | float64 | 13,671 | 46,329 | 77.22% | 0.0 | 57450.0 | 37.06 | **Missing > 70%** |
| 114 | `cs_000` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 839240.0 | 5479.86 | Bình thường |
| 115 | `cs_001` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 438806.0 | 788.43 | Bình thường |
| 116 | `cs_002` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 46085940.0 | 238810.64 | Bình thường |
| 117 | `cs_003` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 42421854.0 | 355373.12 | Bình thường |
| 118 | `cs_004` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 74860628.0 | 444228.28 | Bình thường |
| 119 | `cs_005` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 379142116.0 | 2235386.66 | Bình thường |
| 120 | `cs_006` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 73741974.0 | 545774.18 | Bình thường |
| 121 | `cs_007` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 12884218.0 | 14771.42 | Bình thường |
| 122 | `cs_008` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 1584558.0 | 211.75 | Bình thường |
| 123 | `cs_009` | Histogram Bin | float64 | 59,331 | 669 | 1.11% | 0.0 | 44902992.0 | 779.20 | Bình thường |
| 124 | `ct_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 910366.0 | 749.09 | Bình thường |
| 125 | `cu_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 733688.0 | 1222.96 | Bình thường |
| 126 | `cv_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 81610510.0 | 1928824.89 | Bình thường |
| 127 | `cx_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 44105494.0 | 351510.24 | Bình thường |
| 128 | `cy_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 931472.0 | 274.18 | Bình thường |
| 129 | `cz_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 19156530.0 | 19374.29 | Bình thường |
| 130 | `da_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 21006.0 | 7.39 | Bình thường |
| 131 | `db_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 9636.0 | 13.42 | Bình thường |
| 132 | `dc_000` | Counter | float64 | 46,192 | 13,808 | 23.01% | 0.0 | 120759484.0 | 2200752.21 | Bình thường |
| 133 | `dd_000` | Counter | float64 | 57,497 | 2,503 | 4.17% | 0.0 | 445142.0 | 3123.96 | Bình thường |
| 134 | `de_000` | Counter | float64 | 57,276 | 2,724 | 4.54% | 0.0 | 176176.0 | 375.15 | Bình thường |
| 135 | `df_000` | Counter | float64 | 55,992 | 4,008 | 6.68% | 0.0 | 21613910.0 | 2718.64 | Bình thường |
| 136 | `dg_000` | Counter | float64 | 55,992 | 4,008 | 6.68% | 0.0 | 27064294.0 | 5609.96 | Bình thường |
| 137 | `dh_000` | Counter | float64 | 55,992 | 4,008 | 6.68% | 0.0 | 124700880.0 | 4707.07 | Bình thường |
| 138 | `di_000` | Counter | float64 | 55,994 | 4,006 | 6.68% | 0.0 | 22987424.0 | 37248.24 | Bình thường |
| 139 | `dj_000` | Counter | float64 | 55,993 | 4,007 | 6.68% | 0.0 | 726750.0 | 39.94 | Bình thường |
| 140 | `dk_000` | Counter | float64 | 55,993 | 4,007 | 6.68% | 0.0 | 5483574.0 | 1861.31 | Bình thường |
| 141 | `dl_000` | Counter | float64 | 55,992 | 4,008 | 6.68% | 0.0 | 103858120.0 | 28541.77 | Bình thường |
| 142 | `dm_000` | Counter | float64 | 55,991 | 4,009 | 6.68% | 0.0 | 23697916.0 | 7923.23 | Bình thường |
| 143 | `dn_000` | Counter | float64 | 59,309 | 691 | 1.15% | 0.0 | 2924584.0 | 33745.45 | Bình thường |
| 144 | `do_000` | Counter | float64 | 57,276 | 2,724 | 4.54% | 0.0 | 1874542.0 | 28507.85 | Bình thường |
| 145 | `dp_000` | Counter | float64 | 57,274 | 2,726 | 4.54% | 0.0 | 348118.0 | 6958.65 | Bình thường |
| 146 | `dq_000` | Counter | float64 | 57,274 | 2,726 | 4.54% | 0.0 | 6351872864.0 | 4529374.98 | Bình thường |
| 147 | `dr_000` | Counter | float64 | 57,274 | 2,726 | 4.54% | 0.0 | 50137662.0 | 203759.85 | Bình thường |
| 148 | `ds_000` | Counter | float64 | 57,273 | 2,727 | 4.54% | 0.0 | 4970962.0 | 89655.00 | Bình thường |
| 149 | `dt_000` | Counter | float64 | 57,273 | 2,727 | 4.54% | 0.0 | 656432.0 | 15403.35 | Bình thường |
| 150 | `du_000` | Counter | float64 | 57,274 | 2,726 | 4.54% | 0.0 | 460207620.0 | 4058711.62 | Bình thường |
| 151 | `dv_000` | Counter | float64 | 57,274 | 2,726 | 4.54% | 0.0 | 127034534.0 | 593834.98 | Bình thường |
| 152 | `dx_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 114288420.0 | 791208.48 | Bình thường |
| 153 | `dy_000` | Counter | float64 | 57,276 | 2,724 | 4.54% | 0.0 | 3793022.0 | 7780.35 | Bình thường |
| 154 | `dz_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 1414.0 | 0.22 | Bình thường |
| 155 | `ea_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 8506.0 | 1.57 | Bình thường |
| 156 | `eb_000` | Counter | float64 | 55,993 | 4,007 | 6.68% | 0.0 | 1322456920.0 | 9717093.23 | Bình thường |
| 157 | `ec_00` | Counter | float64 | 49,761 | 10,239 | 17.07% | 0.0 | 106020.2 | 1353.13 | Bình thường |
| 158 | `ed_000` | Counter | float64 | 50,447 | 9,553 | 15.92% | 0.0 | 82806.0 | 1452.16 | Bình thường |
| 159 | `ee_000` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 74984446.0 | 733404.21 | Bình thường |
| 160 | `ee_001` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 98224378.0 | 783874.59 | Bình thường |
| 161 | `ee_002` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 77933926.0 | 445489.73 | Bình thường |
| 162 | `ee_003` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 37758390.0 | 211126.45 | Bình thường |
| 163 | `ee_004` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 97152378.0 | 445734.31 | Bình thường |
| 164 | `ee_005` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 57435236.0 | 393946.20 | Bình thường |
| 165 | `ee_006` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 31607814.0 | 333058.24 | Bình thường |
| 166 | `ee_007` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 119580108.0 | 346271.43 | Bình thường |
| 167 | `ee_008` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 19267396.0 | 138729.98 | Bình thường |
| 168 | `ee_009` | Histogram Bin | float64 | 59,329 | 671 | 1.12% | 0.0 | 3810078.0 | 8388.91 | Bình thường |
| 169 | `ef_000` | Counter | float64 | 57,276 | 2,724 | 4.54% | 0.0 | 482.0 | 0.09 | Bình thường |
| 170 | `eg_000` | Counter | float64 | 57,277 | 2,723 | 4.54% | 0.0 | 1146.0 | 0.21 | Bình thường |