# BẢNG ĐỐI CHIẾU TUÂN THỦ HỌC THUẬT (ACADEMIC COMPLIANCE AUDIT MATRIX)

**Đề tài:** Tối ưu hóa Chi phí Bảo trì Dự đoán Hệ thống Khí nén trên Xe tải nặng Scania (UCI 421)  
**Môn học:** Nhập môn Tối ưu hóa — Trường Đại học Văn Lang  
**Thời điểm đối chiếu:** 2026-11-08  
**Văn bản quy chiếu có thẩm quyền:**
1. `DE_BAI_TAP_LON_CA_NHAN_5_TUAN_GITHUB_PORTFOLIO.pdf` (Đề bài tập lớn cá nhân 5 tuần)
2. `HUONG_DAN_PHAM_VI_DE_BAI_TAP_LON_GITHUB_PORTFOLIO.pdf` (Hướng dẫn phạm vi đề bài tập lớn)

> [!IMPORTANT]
> **NGUYÊN TẮC ĐÁNH GIÁ & ĐỊNH NGHĨA RANH GIỚI KHOA HỌC:**
> 1. **Không đánh giá đạt (`PASS`) chỉ dựa trên unit tests:** Kết quả vượt qua 271 unit tests chỉ chứng minh mã nguồn không có lỗi logic/cú pháp trên dữ liệu giả lập, không thay thế được bằng chứng thực nghiệm thật.
> 2. **Việc hoàn thành G4 Baselines KHÔNG hoàn thành yêu cầu phương pháp tối ưu:** Các mô hình cơ sở G4 (B0, B1, B2) chỉ đóng vai trò mốc tham chiếu so sánh (benchmark: chi phí 10,230). Phương pháp tối ưu cốt lõi bắt buộc theo đề cương (Random Forest kết hợp Bayesian Hyperparameter Optimization & Threshold Tuning qua Optuna TPE) là một hạng mục nghiên cứu độc lập (Phase 2), cần được cấp quyền, thực thi và lưu trữ lịch sử tìm kiếm (search history) riêng biệt.
> 3. **Phân định rõ 4 trạng thái:**
>    - `PASS`: Đã có bằng chứng độc lập, đầy đủ, hoàn tất trong repository.
>    - `PARTIAL`: Đã hoàn thành một phần (khung lý thuyết/thiết kế/bản thảo draft/đo đạc baseline), đang chờ thực nghiệm tối ưu thật hoặc phê duyệt tích hợp.
>    - `NOT EXECUTED`: Chưa thực thi trên dữ liệu thực tế.
>    - `FAIL`: Không đáp ứng yêu cầu.
> 4. **Tổng số hạng mục phải khớp tuyệt đối:** Tổng số hạng mục của từng trạng thái phải bằng đúng tổng số dòng trong bảng đối chiếu (12 PASS + 7 PARTIAL + 3 NOT EXECUTED + 0 FAIL = 22 dòng); tuyệt đối không báo cáo số tổng mâu thuẫn với từng hàng.

---

## 1. BẢNG MA TRẬN ĐỐI CHIẾU CHI TIẾT (22 TIÊU CHÍ)

| STT | Văn bản & Mục quy chiếu | Yêu cầu học thuật chuẩn | Bằng chứng thực tế trong Repository | Trạng thái | Yêu cầu khắc phục / Hành động tiếp theo | Mức ưu tiên |
|:---:|---|---|---|:---:|---|:---:|
| **1** | `DE_BAI` Mục 1 & 2<br>`HUONG_DAN` Mục 1 | **Tư duy tối ưu cốt lõi:** Chuỗi logic Bài toán $\rightarrow$ Mô hình hóa $\rightarrow$ Baseline $\rightarrow$ Thuật toán tối ưu $\rightarrow$ Thực nghiệm $\rightarrow$ Đánh giá $\rightarrow$ Quyết định. | Đã xây dựng đầy đủ khung mô hình toán học và hoàn thành đo đạc baseline Gate B2; mắt xích tối ưu hóa chính đang chuẩn bị thực thi. | **PARTIAL** | Hoàn thành Phase 2 (RF + Optuna TPE) để khép kín chuỗi logic tối ưu hoàn chỉnh từ baseline đến nghiệm tối ưu. | P1 |
| **2** | `DE_BAI` Mục 2<br>`HUONG_DAN` Mục 1 | **Problem Statement:** Mô tả bối cảnh công nghiệp, dữ liệu đầu vào, mục tiêu thực tế và câu hỏi cần trả lời. | Trình bày tại Phần 1 `report/BAO_CAO_CUOI_KY_SCANIA_APS.md`, Mục 1.1–1.3 `docs/scania/problem_formulation.md`. | **PASS** | Đã chuẩn hóa: Hệ thống khí nén (APS) trên xe tải nặng Scania; diễn giải đúng lớp âm tính ($y=0$ là hỏng hóc các bộ phận khác ngoài APS). | P2 |
| **3** | `DE_BAI` Mục 2 & 3<br>`HUONG_DAN` Mục 1 | **Problem Formulation:**<br>- Vector biến quyết định $x$<br>- Hàm mục tiêu $f(x)$ cần min/max<br>- Ràng buộc $g_i(x) \le 0$ / trade-off<br>- Miền khả thi $\Omega$. | - $x = (\theta, \tau)$: siêu tham số mô hình và ngưỡng phân loại $\tau \in [0, 1]$.<br>- $f(x) = 10 \cdot FP + 500 \cdot FN$ [đơn vị chi phí benchmark].<br>- Ràng buộc: $M = TP + FP \le K = \lfloor N/10 \rfloor$ (1200 xe trên Validation).<br>- Minh chứng code: `src/scania/cost_model.py`, `src/scania/constraints.py`. | **PASS** | Chi phí định lượng bằng "đơn vị chi phí benchmark" (cost units), không dùng tiền tệ; công suất 10% là giả định kịch bản tối ưu của đề tài. | P2 |
| **4** | `DE_BAI` Mục 2 & 3<br>`HUONG_DAN` Mục 2 & 4 | **Baseline:** Ít nhất 01 baseline hợp lý, không cố ý để ở cấu hình bất lợi. | Thiết lập 3 baselines chuẩn tắc tại `src/scania/baselines.py` và `configs/scania/g4_baselines.json`:<br>- B0: Majority Dummy ($a_i = 0$, chi phí 100,000).<br>- B1: Decision Stump (`max_depth=1`).<br>- B2: Logistic Regression (`max_iter=2000`, `solver='lbfgs'`).<br>Đã đo đạc thực tế tại Gate B2 run `scania_g4_b2_real_002` trên 12.000 mẫu Validation. | **PASS** | Hoàn thành đo đạc thực nghiệm thật: B2 tại $\tau = 10/510$ đạt chi phí 10,230 (tiết kiệm +89.77% vs B0, $M=509 \le 1200$). | P2 |
| **5** | `DE_BAI` Mục 2 & 3<br>`HUONG_DAN` Mục 2, 4, 6 | **Phương pháp tối ưu chính:** Ít nhất 01 phương pháp chính; giải thích nguyên lý, tham số và lý do chọn. | Đề xuất Random Forest kết hợp Bayesian Hyperparameter Optimization & Threshold Tuning qua Optuna TPE (Phase 2). Đã kiểm thử cơ chế điều phối qua smoke test. | **NOT EXECUTED** | **Chưa thực thi bất kỳ trial tối ưu hóa nào trên dữ liệu thật.** Việc chạy G4 baselines không thay thế phương pháp tối ưu này. | P0 |
| **6** | `DE_BAI` Mục 2, 3, 7<br>`HUONG_DAN` Mục 7 | **Thiết kế thực nghiệm công bằng:** Cùng dữ liệu, cùng preprocessing, cùng split, cùng metric, cùng budget dừng. | - Dữ liệu G3 cố định: `results/scania_aps/g3/official_20261029_04/stable_manifest.json` (`efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`).<br>- Split: 48k Train / 12k Validation.<br>- Preprocessing fit duy nhất trên Train: `data/processed/scania_aps/official_20261029_04/`. | **PASS** | Đã xác minh tính toàn vẹn và khớp từng hàng với tập Train gốc qua `test_EX04`. | P2 |
| **7** | `DE_BAI` Mục 2, 7, 9<br>`HUONG_DAN` Mục 7 | **Chống rò rỉ dữ liệu (No Data Leakage):** Tuyệt đối không dùng Test set để tuning hay chọn mô hình. | - Official Test Set (16.000 mẫu) được niêm phong tuyệt đối: **SEALED UNTIL G10**.<br>- I/O Guard (`install_executor_io_guard`) chặn đứng mọi truy cập tới `aps_failure_test_set.csv` và file nén (`test_EX01`, `test_EX21`). | **PASS** | Đảm bảo tính toàn vẹn học thuật cao nhất: Test set chưa từng bị đọc trong bất kỳ thử nghiệm nào. | P2 |
| **8** | `DE_BAI` Mục 1, 4, 7<br>`HUONG_DAN` Mục 7 | **Logging & Tái lập:** Lưu lịch sử chạy, cấu hình, hạt giống (seed), đo runtime và kiểm tra nghiệm. | - Quản lý thực nghiệm qua Windows Job Object (`max_native_threads=1`, `max_ram_mb=2048`, `max_wall_seconds=120`).<br>- Lượt chạy thật `scania_g4_b2_real_002` lưu đầy đủ 11 artifacts (JSON, CSV, SHA-256 checksums, telemetry) được kiểm chứng mật mã tự động.<br>- Run `001` không thành công được lưu giữ nguyên vẹn. | **PARTIAL** | Logging mô hình cơ sở G4 hoàn tất; lịch sử tìm kiếm (search history) của Optuna TPE (Phase 2) đang chờ thực thi. | P0 |
| **9** | `DE_BAI` Mục 2, 4, 5<br>`HUONG_DAN` Mục 4 | **Kết quả trực quan:** Có bảng số liệu, ít nhất 02 hình/đồ thị liên quan đến hội tụ, search history, Pareto hoặc trade-off. | Hiện chỉ có 6 biểu đồ EDA mô tả dữ liệu ban đầu tại `figures/eda/` (01–06). Chưa có đồ thị hội tụ (convergence curve) hay đánh đổi (trade-off curve) từ kết quả tối ưu thật. | **NOT EXECUTED** | Bắt buộc phải sinh ít nhất 02 đồ thị từ kết quả tối ưu thật: (1) Đường cong đánh đổi Chi phí vs Năng lực xưởng tại các ngưỡng $\tau$, (2) So sánh chi phí giữa baseline và mô hình tối ưu. | P0 |
| **10** | `DE_BAI` Mục 1, 2, 7<br>`HUONG_DAN` Mục 10 | **Ra quyết định cuối cùng:** Chọn nghiệm/cấu hình nào, giải thích bằng số liệu; nêu hạn chế và điều kiện áp dụng. | Khung phân tích đã xây dựng tại Mục 7 `report/BAO_CAO_CUOI_KY_SCANIA_APS.md` và Slide 7 `slides/SLIDES_THUYET_TRINH_SCANIA_APS.md`. | **NOT EXECUTED** | Cần số liệu từ các trial tối ưu hóa Phase 2 để so sánh với baseline 10,230 trước khi ra quyết định lựa chọn nghiệm cuối cùng. | P0 |
| **11** | `DE_BAI` Mục 3.1, 5.1<br>`HUONG_DAN` Mục 5.1 | **Dữ liệu chuẩn & Điểm cộng (+0.25đ):** Dataset công bố/benchmark có nguồn rõ ràng, citation, xử lý đúng. | UCI Machine Learning Repository Dataset #421 (*APS Failure at Scania Trucks*), Scania CV AB (2016). Đã trích dẫn đầy đủ tại `data/README.md` và `docs/scania/data_dictionary.md`. | **PASS** | Đủ điều kiện được xem xét điểm cộng theo tiêu chí chấm của rubric (eligible for consideration under rubric criteria). | P2 |
| **12** | `DE_BAI` Mục 4 & 6<br>`HUONG_DAN` Mục 8 | **Lịch sử phát triển dự án:** Có tối thiểu 5 mốc commit có ý nghĩa, phản ánh đúng tiến trình phát triển. | Repository có tiến trình phát triển tập trung từ 21/10/2026, trải qua chuỗi mốc kỹ thuật chuyên sâu G1–G10 qua các PR #1, #3, #4, #5, #14, #16, #18, #19, #20. | **PASS** | Tiến trình phát triển minh bạch, không upload dự án bằng 1 commit duy nhất. | P2 |
| **13** | `DE_BAI` Mục 5 & 7 | **Báo cáo chuyên nghiệp:** 8–12 trang (Word/PDF), đủ 7 mục bắt buộc theo Mục 7. | Bản thảo chi tiết tại `report/BAO_CAO_CUOI_KY_SCANIA_APS.md` đã cập nhật đầy đủ số liệu đo đạc thực tế từ run 002 (đủ 7 mục bắt buộc). | **PARTIAL** | Đã cập nhật kết quả đo thật; cần biên dịch/xuất sang định dạng PDF/Word chính thức và kiểm chứng trực quan trước giờ nộp. | P1 |
| **14** | `DE_BAI` Mục 5 & 6<br>`HUONG_DAN` Mục 8 | **Mã nguồn & Tái lập:** Chạy từ đầu đến cuối, tách bạch module, không lỗi import, có seed cố định. | Hệ thống module tại `src/scania/`, bộ 271 unit tests PASS, runner Gate B2 chạy thành công trên dữ liệu thực tế. | **PARTIAL** | Quy trình chạy end-to-end từ raw data $\to$ G3 $\to$ G4 baseline $\to$ Optuna optimization $\to$ kết quả/hình ảnh cần hoàn thiện mắt xích Optuna. | P1 |
| **15** | `DE_BAI` Mục 4 & 5 | **File kết quả (CSV/JSON):** Lưu trữ kết quả các run/trial, không chỉ chụp màn hình. | - Kết quả G4 baselines lưu đầy đủ dạng máy đọc tại `results/scania_aps/g4/scania_g4_b2_real_002/baseline_metrics.csv` và `baseline_metrics.json`.<br>- Kết quả đã được xuất bản minh bạch tại `docs/results_analysis.md`. | **PARTIAL** | File kết quả G4 baselines hoàn tất; file kết quả chi tiết từng trial của thuật toán tối ưu Optuna (Phase 2) đang chờ thực thi. | P0 |
| **16** | `DE_BAI` Mục 5, 6, 8<br>`HUONG_DAN` Mục 8 | **README Portfolio:** Bắt buộc có: Problem, Optimization Formulation, Dataset, Method, Key Results, How to Run, Repository Structure, Limitations. | Đã dự thảo đầy đủ 10 mục chuẩn hóa và cập nhật số liệu đo thật run 002 tại `docs/scania/SCANIA_PORTFOLIO_README.md`. | **PARTIAL** | Đã cập nhật số liệu đo thật; chờ Chủ dự án phê duyệt để tích hợp vào file chung `README.md` ở gốc repository. | P1 |
| **17** | `DE_BAI` Mục 4 & 5 | **Slide thuyết trình:** 05–08 Slide hỗ trợ bảo vệ, demo 5–7 phút tập trung vào tối ưu. | Đã soạn thảo đề cương đúng **07 slides** tại `slides/SLIDES_THUYET_TRINH_SCANIA_APS.md` và cập nhật bảng số liệu đo thật run 002. | **PARTIAL** | Đã cập nhật số liệu đo thật; cần xuất file trình chiếu PPTX/PDF chính thức và kiểm chứng trực quan trước khi báo cáo. | P1 |
| **18** | `DE_BAI` Mục 6 | **Cấu trúc Repository:** Tách rõ `src/`, `results/`, `figures/`, `report/`, `.gitignore`; không file rác/checkpoint. | Cấu trúc phân tách rõ ràng: `src/`, `notebooks/`, `results/`, `figures/`, `report/`, `slides/`, `configs/`, `data/`. | **PASS** | Đã kiểm tra `.gitignore` không để lọt raw data hay checkpoint tạm. | P2 |
| **19** | `DE_BAI` Mục 5, 6, 8<br>`HUONG_DAN` Mục 8 | **Môi trường & Dependency:** Có `requirements.txt`, Python version (3.11), seed cố định. | - Python 3.11.9.<br>- Dependencies khóa tại `configs/scania/g3_requirements.lock.txt`.<br>- Seed = 42 cố định. | **PASS** | Môi trường và thư viện được khóa chặt chẽ. | P2 |
| **20** | `DE_BAI` Mục 5, 6 | **Dữ liệu & Bảo mật:** Không commit dữ liệu nhạy cảm, API key, credential, raw data lớn. | Đã quét và khử sạch PII, raw data ZIP/CSV nằm trong `.gitignore`, kết quả công bố không chứa đường dẫn máy nội bộ. | **PASS** | Không có thông tin nhạy cảm nào tồn tại trên public repository. | P2 |
| **21** | `DE_BAI` Mục 10 | **Khai báo AI hỗ trợ (AI Assistance Disclosure):** Nêu rõ công cụ AI đã dùng và phần sinh viên tự kiểm chứng. | Đã bổ sung mục "Khai báo công cụ hỗ trợ AI" trong Báo cáo (Mục 8), Slide (Slide 7) và Portfolio README (Mục 9.2). | **PASS** | Đáp ứng đầy đủ quy chế liêm chính học thuật của nhà trường. | P2 |
| **22** | `HUONG_DAN` Mục 3 | **Phạm vi XANH (Khuyến nghị):** 01 dataset, 01 bài toán rõ, 01 baseline + 01-2 phương pháp, 20-50 trials, chạy trong vài phút đến vài giờ. | Đề tài Scania APS tuân thủ chuẩn XANH: 1 dataset UCI 421, bài toán tối ưu chi phí phi đối xứng có ràng buộc, 3 baselines + 1 phương pháp chính (RF + Optuna TPE). | **PASS** | Thiết kế phạm vi đề tài khoa học, vừa sức và sâu về mặt toán học. | P2 |

---

## 2. TỔNG HỢP TRẠNG THÁI CHÍNH XÁC & ĐÁNH GIÁ SẴN SÀNG

Đối chiếu số liệu tổng hợp khớp 100% với từng dòng trong bảng:

| Phân loại trạng thái | Số lượng tiêu chí | Tỷ lệ (%) | Các tiêu chí thành phần |
|---|:---:|:---:|---|
| **ĐẠT (PASS)** | **12** | **54.5%** | Mục 2, 3, 4, 6, 7, 11, 12, 18, 19, 20, 21, 22 |
| **MỘT PHẦN / BẢN THẢO (PARTIAL)** | **7** | **31.8%** | Mục 1 (tư duy logic), 8 (logging), 13 (báo cáo draft), 14 (tái lập end-to-end), 15 (file kết quả CSV/JSON), 16 (README draft), 17 (slides draft) |
| **CHƯA THỰC THI (NOT EXECUTED)** | **3** | **13.6%** | Mục 5 (phương pháp tối ưu chính), 9 (đồ thị tối ưu), 10 (quyết định số liệu) |
| **KHÔNG ĐẠT (FAIL)** | **0** | **0.0%** | Không có hạng mục nào vi phạm hoặc bị từ chối |
| **TỔNG CỘNG** | **22** | **100.0%** | Khớp chính xác 12 + 7 + 3 + 0 = 22 dòng |

---

## 3. KẾT LUẬN SẴN SÀNG NỘP BÀI (SUBMISSION READINESS VERDICT)

> [!CAUTION]
> **KẾT LUẬN HIỆN TẠI: ĐÃ HOÀN TẤT GATE B2 BASELINES — CHUẨN BỊ THỰC THI TỐI ƯU HÓA CỐT LÕI (PHASE 2)**
>
> 1. **Cơ sở khoa học đã hoàn tất:**
>    - Toàn bộ nền tảng mô hình hóa toán học, giao thức thực nghiệm không rò rỉ, phân vùng dữ liệu G3 đã khóa (`efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`).
>    - **Gate B2 đã hoàn tất thành công (`scania_g4_b2_real_002`):** Đo đạc 5 chính sách trên 12.000 mẫu Validation; best baseline đạt chi phí **10.230** (tiết kiệm +89.77% vs B0); thỏa mãn ràng buộc công suất ($M = 509 \le 1200$). 11 artifacts được kiểm chứng toàn vẹn mật mã SHA-256.
> 2. **Các khoảng trống bắt buộc phải hoàn thành trước khi nộp bài (Remaining Blockers):**
>    - **Mandatory Optimization Method (Phase 2):** Thực thi thuật toán tối ưu cốt lõi (Random Forest kết hợp Bayesian HPO Optuna TPE) với ngân sách 20 trials trên Train 48k / Validation 12k để sinh lịch sử tìm kiếm và đánh giá so với mốc baseline 10,230.
>    - **Optimization Figures:** Sinh ít nhất 02 đồ thị từ kết quả tối ưu thật: (1) Đường cong hội tụ Optuna qua các trial, (2) Đường cong đánh đổi Chi phí vs Công suất tiếp nhận tại các ngưỡng $\tau$.
>    - **Quyết định nghiệm:** Phân tích số liệu và lựa chọn chính sách tối ưu cuối cùng, giải thích lý do toán học và đánh đổi kỹ thuật.
>    - **Xuất bản & Kiểm chứng trực quan:** Chuyển đổi báo cáo và slides sang Word/PDF và PPTX/PDF chính thức, kiểm chứng trực quan trước hạn nộp.
