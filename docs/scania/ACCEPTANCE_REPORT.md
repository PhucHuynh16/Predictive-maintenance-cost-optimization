# BÁO CÁO NGHIỆM THU TỔNG KẾT & BÀN GIAO ĐỒ ÁN (`ACCEPTANCE_REPORT.md`)

- **Đề tài:** Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS (UCI #421)
- **Học phần:** Nhập môn Tối ưu hóa — Khoa Công nghệ Thông tin, Trường Đại học Văn Lang
- **Sinh viên thực hiện:** Huỳnh Phúc (MSSV: 2474802010314)
- **Repository:** [https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)
- **Nhánh làm việc:** `antigravity/sc-final-deliverables` (Commit cơ sở trước rà soát cuối: `a44f9281fc4b53052dfdbcae4a9b9142f85beee1`)
- **Ngày lập báo cáo:** `2026-11-24`

---

## 1. CHÍNH SÁCH TỐI ƯU ĐÃ ĐÓNG BĂNG & KẾT QUẢ THỰC NGHIỆM GỐC

Toàn bộ kết quả thực nghiệm gốc tại G3, G4, Phase 2 và Gate G10 được giữ nguyên 100%, không huấn luyện thêm mô hình, không chạy thêm Optuna và không truy cập lại tập Official Test:

- **Mô hình & Siêu tham số đóng băng (Phase 2 Optuna Trial #16 [0-indexed], tức lượt thử thứ 17/20):**
  - `estimator`: `RandomForestClassifier`
  - `n_estimators = 50`, `max_depth = 10`, `min_samples_split = 10`, `max_features = 0.4268663927182804`
  - Tham số cố định: `class_weight = "balanced"`, `random_state = 42`, `n_jobs = 1`, `bootstrap = True`
  - Ngưỡng xác suất đóng băng: `tau* = 0.3232440937634324` (`a_i = I(p_i >= tau*)`)

| Giai đoạn & Lượt chạy gốc | Phân vùng ($N$) | $TP$ | $FP$ | $FN$ | $TN$ | Tổng chi phí ($10\cdot FP + 500\cdot FN$) | Lượt xe vào xưởng ($M \le K$) | So sánh tham chiếu |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **G4 B0 (Majority Dummy)** (`scania_g4_b2_real_002`) | Validation ($12.000$) | $0$ | $0$ | $200$ | $11.800$ | **$100.000$** | $0 / 1.200$ (`FEASIBLE`) | Mốc không kiểm tra ($0,00\%$) |
| **G4 B1 (Decision Stump, $\tau=0.0196$)** | Validation ($12.000$) | $160$ | $253$ | $40$ | $11.547$ | **$22.530$** | $413 / 1.200$ (`FEASIBLE`) | $-77,47\%$ so với B0 |
| **G4 B2 (Logistic Regression, $\tau=0.0196$)** | Validation ($12.000$) | $186$ | $323$ | $14$ | $11.477$ | **$10.230$** | $509 / 1.200$ (`FEASIBLE`) | Baseline tốt nhất G4 ($-89,77\%$) |
| **Phase 2 RF + Optuna TPE (Trial 16)** (`scania_phase2_rf_optuna_002`) | Validation ($12.000$) | $195$ | $383$ | $5$ | $11.417$ | **$6.330$** | $578 / 1.200$ (`FEASIBLE`) | **$-93,67\%$ so với B0; $-38,12\%$ so với B2** |
| **Gate G10 Official Test** (`scania_g10_official_test_003`) | Official Test ($16.000$) | $357$ | $484$ | $18$ | $15.141$ | **$13.840$** | $841 / 1.600$ (`FEASIBLE`) | **$-92,62\%$ so với B0 Test ($187.500$)** |

---

## 2. TỔNG HỢP CÁC KHIẾM KHUYẾT ĐÃ KHẮC PHỤC TRONG ĐỢT RÀ SOÁT CUỐI

1. **Đính chính độ nhạy ngưỡng quyết định (Mục 4.1):**
   - Đã loại bỏ hoàn toàn nhận định sai trước đây cho rằng mọi ngưỡng $\tau < 0.10$ đều vi phạm trần công suất xưởng.
   - Trích xuất trực tiếp từ `threshold_curve` của Trial 16 (`results/scania_aps/phase2/scania_phase2_rf_optuna_002/best_policy.json` và `durable_fits/trial_016_result.json`): tại $\tau = 0.04$ có $M = 1.314 > 1.200$ (`INFEASIBLE`), nhưng từ $\tau = 0.05$ ($M = 1.195 \le 1.200$, chi phí $11.480$) và $\tau = 0.09$ ($M = 955 \le 1.200$, chi phí $9.080$) chính sách **đã khả thi**. Trong đoạn $\tau \in [0.20, 0.32]$, chi phí duy trì ở vùng thấp $[6.350, 7.050]$; cực tiểu quan sát được đạt $6.330$ tại $\tau^* = 0.323244$; từ $\tau \ge 0.33$, chi phí tăng dốc ($7.290 \to 8.230 \to 8.670$).
2. **Đồng bộ miền tìm kiếm siêu tham số và cơ chế chọn ngưỡng (Mục 4.2):**
   - Đã sửa chính xác khoảng tìm kiếm `max_features` thành `$[0.20, 0.50]$` (cùng `n_estimators` $\in \{20,30,40,50,60\}$, `max_depth` $\in [4,12]$, `min_samples_split` $\in [2,10]$) khớp tuyệt đối với `configs/scania/phase2_optimization.json` và `src/scania/phase2_optimization.py`.
   - Đã phân biệt rõ: bước tối ưu ngưỡng thực tế duyệt chính xác tập ứng viên xác suất duy nhất $T(p) = \{0, 1\} \cup \text{unique}(p_{\text{val}})$ không cần huấn luyện lại mô hình, còn lưới đều 101 điểm (`0.00..1.00`) chỉ dùng để vẽ đường cong đánh đổi. Không tuyên bố nghiệm tìm được là tối ưu toàn cục.
3. **Chuyển `scripts/demo.py` sang nạp động hoàn toàn từ artifacts & kiểm định chéo (Mục 4.3):**
   - Xóa bỏ các hằng số thực nghiệm gán cứng trong đầu ra trình chiếu; nạp trực tiếp từ `phase2_optimization.json`, `baseline_metrics.json`, `best_policy.json`, `run_summary.json`, `validation_guard_metrics.json`, `test_metrics.json` và `confusion_matrix_test.csv`.
   - Bổ sung bộ kiểm định toán học tự động (`TP + FP + FN + TN = N`, `Cost = 10*FP + 500*FN`, `M = TP + FP <= K`, khớp ma trận nhầm lẫn CSV và bộ tham số đóng băng) cùng kiểm tra mã băm SHA-256 trên 32/32 artifacts; trả mã thoát `1` ngay khi thiếu hoặc hỏng dữ liệu.
4. **Chuẩn hóa tài liệu, đường dẫn và thuật ngữ SHA-256 (Mục 4.4 & Mục 5):**
   - Thay thế cách gọi sai "chữ ký số mật mã học SHA-256" bằng thuật ngữ chính xác **"mã băm kiểm tra toàn vẹn SHA-256 (integrity checksum)"** trên toàn bộ `README.md`, `data/README.md`, `docs/`, báo cáo và slide.
   - Gắn nhãn `[BẢN CHỤP LỊCH SỬ — HISTORICAL SNAPSHOT]` cho các tài liệu kiểm toán cũ (`docs/scania/academic_compliance_matrix.md`, `SCANIA_PORTFOLIO_README.md`) và lập mới `docs/scania/FINAL_COMPLIANCE_MATRIX.md`.
   - Biên soạn lại và xuất mới `report/BAO_CAO_CUOI_KY_SCANIA_APS.{md,docx,pdf}` (**8 trang nội dung chính + 1 trang Phụ lục = 9 trang**) và `slides/SLIDES_THUYET_TRINH_SCANIA_APS.{md,pptx,pdf}` (**8 slides**), khắc phục triệt để lỗi hiển thị mã LaTeX thô và ô ký tự trống `□`, kiểm tra trực quan từng trang PDF.

---

## 3. KIỂM KÊ TRUNG THỰC HIỆN TRẠNG DỮ LIỆU, PREPROCESSOR, CHECKPOINT & LOCKFILES (MỤC 6)

Bảng dưới đây ghi nhận chính xác trạng thái tồn tại thực tế trên máy cục bộ, trong Git repository và trong gói bàn giao độc lập `nghiemthu`:

| Nhóm thành phần | Đường dẫn chính xác (tương đối từ gốc dự án) | Hiện có tại Worktree cục bộ? | Đưa vào Git / Gói `nghiemthu`? | Mục đích & Phương án khôi phục khi thiếu |
|---|---|:---:|:---:|---|
| **1. Dữ liệu gốc UCI #421** | `data/raw/scania_aps/aps+failure+at+scania+trucks.zip` (`56.618.034 B`, SHA-256: `5504d040...`)<br>`data/raw/scania_aps/aps_failure_training_set.csv` (`44.669.194 B`, SHA-256: `bb484302...`)<br>`data/raw/scania_aps/aps_failure_description.txt` (`4.874 B`) | **CÓ** | **KHÔNG** (bị chặn bởi `.gitignore`) | Dữ liệu thô từ UCI #421 (~101 MB). Tệp `aps_failure_test_set.csv` vẫn giữ nguyên trong `.zip`. Khôi phục tự động bằng lệnh `python scripts/run_scania_acquire.py`. |
| **2. Dữ liệu Train/Val đã tiền xử lý G3** | `data/processed/scania_aps/official_split.json` (`4.969.510 B`)<br>`data/processed/scania_aps/official_20261029_04/membership.npz` (`541.018 B`)<br>`.../tree_train.npy` (`65.280.128 B`), `tree_validation.npy` (`16.320.128 B`)<br>`.../lr_train.npy` (`65.280.128 B`), `lr_validation.npy` (`16.320.128 B`) | **CÓ** | **KHÔNG** (bị chặn bởi `.gitignore`) | Ma trận đặc trưng `float64` đã tách phân tầng 80/20 (`48.000 / 12.000`) cho cây quyết định và Logistic Regression (~168 MB). Khôi phục bằng lệnh `python scripts/run_scania_pipeline.py --run-id recreate_local_g3`. |
| **3. Đối tượng tiền xử lý đã fit (`joblib`)** | `data/processed/scania_aps/official_20261029_04/tree_preprocessor.joblib` (`3.624 B`)<br>`data/processed/scania_aps/official_20261029_04/lr_preprocessor.joblib` (`8.065 B`) | **CÓ** | **KHÔNG** (nằm trong `data/processed/` bị ignore) | Lưu vector trung vị (`SimpleImputer`) và tham số chuẩn hóa (`StandardScaler`) học từ tập Train 48k. Sinh lại xác định 100% khi chạy `scripts/run_scania_pipeline.py`. |
| **4. Trọng số mô hình đã huấn luyện (Model Checkpoints)** | *(Không có tệp `rf_model.joblib` / `*.pkl` cho Random Forest hay B1/B2)* | **KHÔNG TỒN TẠI** | **KHÔNG TỒN TẠI** | Thiết kế Phase 2 & G10 chỉ lưu siêu tham số + ngưỡng JSON và dùng cơ chế `DETERMINISTIC_TRAIN_REFIT_EVALUATION` (~31 giây refit trên Train 48k với `seed=42`, khớp 100% Validation Guard). Nếu cần suy luận trực tiếp trên dữ liệu mới, cần chạy 1 bước refit từ `configs/scania/g10_evaluation.json` + dữ liệu G3 rồi `joblib.dump()`. |
| **5. Tệp khóa phiên bản thư viện (Lockfiles)** | `requirements.txt`<br>`configs/scania/g3_requirements.lock.txt` (15 gói khóa `==`)<br>`configs/scania/phase2_requirements.lock.txt` (33 gói khóa `==` trên Python `3.11.9`) | **CÓ** | **CÓ** (đầy đủ trong Git & `nghiemthu`) | Phục vụ tái lập chính xác môi trường Python `3.11.9` (`scikit-learn==1.9.1`, `optuna==5.0.0`, `numpy==2.4.6`, `scipy==1.17.1`). |
| **6. Artifacts kết quả thực nghiệm gốc** | `results/scania_aps/{g2_audit,g3,g4,phase2,g10}/**` | **CÓ** | **CÓ** (đầy đủ trong Git & `nghiemthu`) | Toàn bộ JSON/CSV/checksums của các lượt chạy thành công và các lượt chạy lỗi lịch sử; đủ để chạy ngay **Chế độ A (Demo Read-Only)** không cần tải dữ liệu thô. |

---

## 4. BẰNG CHỨNG KIỂM THỬ ĐỘC LẬP TẠI `nghiemthu` VÀ WORKTREE (MỤC 7)

### 4.1. Thực thi tại Worktree phát triển (`worktrees/antigravity`)
| Lệnh thực thi | Mã thoát | Kết quả ghi nhận |
|---|:---:|---|
| `python -m pytest tests/scania/test_cost_model.py tests/scania/test_constraints.py tests/scania/test_evaluation.py tests/scania/test_baselines.py tests/scania/test_pipeline.py tests/scania/test_phase2_optimization.py tests/scania/test_g10_evaluation.py -v` | `0` | **`134 passed in 116.58s`** (`0 failed`) |
| `python scripts/run_scania_g10.py verify` | `0` | `[PASS] All 9 artifacts verified against stable manifest.` |

### 4.2. Thực thi độc lập trực tiếp từ thư mục gói bàn giao `<project_root>/nghiemthu`
| Hạng mục kiểm tra | Lệnh chạy tại `cwd = ...\nghiemthu` | Mã thoát | Kết quả ghi nhận |
|---|---|:---:|---|
| Demo đầy đủ | `python scripts/demo.py` | `0` | In đầy đủ 5 phần + gợi ý thuyết trình 5–7 phút từ JSON/CSV gốc |
| Demo tóm tắt bảng | `python scripts/demo.py --summary` | `0` | In chính xác bảng G4, Phase 2 (kèm độ nhạy $\tau$) và Gate G10 |
| Demo xác minh SHA-256 | `python scripts/demo.py --verify` | `0` | `32/32 ARTIFACTS KHỚP MÃ BĂM SHA-256 VÀ KIỂM ĐỊNH TOÁN HỌC` |
| Demo dàn ý bảo vệ | `python scripts/demo.py --notes` | `0` | In dàn ý thuyết trình 4 chặng trong khung 5–7 phút |
| Kiểm chứng G10 | `python scripts/run_scania_g10.py verify` | `0` | `[PASS] All 9 artifacts verified against stable manifest.` |
| Kiểm chứng G4 & Phase 2 | `verify_run('.../scania_g4_b2_real_002')` & `verify_phase2_run('.../001', '.../002')` | `0` | `G4_AND_PHASE2_ARTIFACTS_VERIFIED_PASS` |
| Unit tests độc lập (ngoài Git) | `python -B -m pytest tests/scania/{test_cost_model,test_constraints,test_evaluation,test_baselines,test_pipeline,test_g10_evaluation}.py -k "not test_official_test_unsealed_fails_without_authorization and not test_synthetic_end_to_end_pipeline" -v` | `0` | **`104 passed in 2.8s`** *(2 ca loại trừ do gọi `git rev-parse HEAD` cần thư mục `.git/`, đã pass trong bộ 134 ca tại worktree)* |

### 4.3. Kiểm thử âm tính (Negative Tests) trên bản sao tạm cô lập ngoài `nghiemthu`
| Kịch bản giả lập lỗi (trên thư mục tạm cô lập, đã xóa sau test) | Lệnh kiểm tra | Mã thoát | Thông báo lỗi thu được trên `stderr` |
|---|---|:---:|---|
| **Negative Test 1 — Thiếu tệp bắt buộc:** Xóa `results/scania_aps/g10/scania_g10_official_test_003/test_metrics.json` | `python scripts/demo.py` & `python scripts/demo.py --verify` | **`1`** | `[DEMO DỪNG DO LỖI TOÀN VẸN DỮ LIỆU] [THIẾU ARTIFACT] Không tìm thấy Gate G10 Test Metrics...` |
| **Negative Test 2 — Sửa sai số liệu:** Đổi `total_cost` từ `13840` thành `9999` trong `test_metrics.json` | `python scripts/demo.py` & `python scripts/demo.py --verify` | **`1`** | `[DEMO DỪNG DO LỖI TOÀN VẸN DỮ LIỆU] [SAI HÀM MỤC TIÊU] Gate G10 Official Test: total_cost (9999) != 10*FP + 500*FN (13840).` |
| **Negative Test 3 — Can thiệp log văn bản (toán học không đổi):** Thêm dòng lạ vào `scania_phase2_rf_optuna_002/execution.txt` | `python scripts/demo.py --verify` | **`1`** | Phát hiện `MISMATCH` mã băm SHA-256 và dừng với mã lỗi `1` |

---

## 5. CÁC HẠN CHẾ CÒN TỒN TẠI & ĐIỂM LƯU Ý MINH BẠCH

1. **Thực nghiệm một hạt giống (`seed = 42`):** Chưa chạy lặp đa hạt giống (`mean ± std`) cho thuật toán ngẫu nhiên (Random Forest + Optuna TPE) do giới hạn ngân sách thực thi đã khóa.
2. **Khoảng cách baseline G4 vs Phase 2:** Hệ thống G4 gồm B0, B1, B2 ở ngưỡng cố định (`2 fits`), chưa tách riêng một baseline `RandomForestClassifier` cấu hình mặc định cùng cơ chế quét ngưỡng ứng viên.
3. **Không có tệp `.joblib` trọng số mô hình Random Forest:** Bản demo trình chiếu kết quả thực nghiệm đã lưu (`Mode A`), không thực hiện suy luận trực tiếp (`Mode C`) nếu chưa chạy lại bước refit trên tập Train G3.
4. **Chuỗi đường dẫn máy cục bộ trong log lịch sử `results/`:** Tất cả tài liệu biên soạn mới (`README.md`, `report/`, `slides/`, `docs/`, `scripts/demo.py`) đã khử đường dẫn cá nhân và không chứa bất kỳ khóa bí mật/token nào. Tuy nhiên, một số tệp JSON nhật ký thực nghiệm gốc trong `results/scania_aps/**` (`allowlist.json`, `task_config.json`, `failure_diagnostics.json`) lưu đường dẫn tuyệt đối lúc chạy worker; các tệp này **được giữ nguyên không chỉnh sửa** để bảo toàn mã băm SHA-256 trong `checksums.json` / `stable_manifest.json` theo đúng quy định không sửa bằng chứng lịch sử (Mục 2 Chỉ thị).
5. **Chưa kiểm chứng cài đặt trắng hoàn toàn (`NOT VERIFIED`):** Chưa kiểm tra `pip install` từ đầu trên một máy ảo trắng tách biệt hoàn toàn với máy phát triển.
6. **Lịch sử Git thực tế:** Bắt đầu từ `2026-10-21` (khảo sát AI4I tuần đầu, chuyển sang Scania APS ngày `2026-10-25`) với hơn 45 commits thực chất, không kéo dài đủ 5 tuần lịch độc lập trên một dataset duy nhất; tuyệt đối không tạo commit giả lùi ngày.

---

## 6. KẾ HOẠCH CHUẨN BỊ PHÁT HÀNH GITHUB PORTFOLIO (`v1.0`) — CHỜ CHỦ DỰ ÁN PHÊ DUYỆT RIÊNG

Tuân thủ nghiêm ngặt Mục 8 Chỉ thị (*không tự ý merge vào `main`, không tạo repo mới, không tạo Release khi chưa có lệnh phê duyệt riêng của Chủ dự án*), kế hoạch xuất bản đề xuất gồm 4 bước dành cho Chủ dự án:

1. **Rà soát nhánh bàn giao:** Kiểm tra commit cuối trên nhánh `antigravity/sc-final-deliverables`, đối chiếu `README.md` (hiển thị trực tiếp 2 hình tối ưu hóa), `report/BAO_CAO_CUOI_KY_SCANIA_APS.pdf`, `slides/SLIDES_THUYET_TRINH_SCANIA_APS.pdf` và `docs/scania/FINAL_COMPLIANCE_MATRIX.md`.
2. **Tích hợp vào nhánh `main`:** Tạo và phê duyệt Pull Request từ `antigravity/sc-final-deliverables` sang `main` theo hình thức *Merge commit* (không squash/rebase xóa lịch sử) để bảo toàn chuỗi commit xác thực của G2, G3, G4, Phase 2 và G10.
3. **Cấu hình giao diện GitHub Portfolio:**
   - **About Description:** `Constrained Predictive Maintenance Cost Optimization on Scania APS Trucks (UCI #421) using Random Forest, Optuna TPE & Exact Threshold Search — Introduction to Optimization Coursework.`
   - **Topics:** `optimization`, `predictive-maintenance`, `cost-sensitive-learning`, `optuna`, `random-forest`, `scania-aps`, `constrained-optimization`, `python`.
4. **Phát hành phiên bản khóa nộp bài (`Release v1.0`):** Tạo Git tag `v1.0` trên commit merge `main`, đính kèm trực tiếp `BAO_CAO_CUOI_KY_SCANIA_APS.pdf`, `SLIDES_THUYET_TRINH_SCANIA_APS.pdf` và gói nén `nghiemthu.zip` kèm mã băm SHA-256 trong phần mô tả Release.

---

## 7. KẾT LUẬN ĐỀ XUẤT NGHIỆM THU (EVIDENCE-BASED VERDICT)

- **Phân loại trạng thái đề xuất:** **`CONDITIONALLY READY`**
- **Căn cứ thực증 cho mức `CONDITIONALLY READY`:**
  1. Toàn bộ sản phẩm học thuật cốt lõi (mô hình toán học, mã nguồn tối ưu có ràng buộc, kết quả thực nghiệm G4/Phase 2/G10 khớp 32/32 mã băm SHA-256, báo cáo 8 trang chính + 1 trang phụ lục, 8 slides thuyết trình, `scripts/demo.py` đọc động dữ liệu thật và gói độc lập `nghiemthu` + `nghiemthu.zip`) đã hoàn thiện đầy đủ, vượt qua toàn bộ bài kiểm thử dương tính và âm tính mà không có bất kỳ hạng mục `FAIL` nào.
  2. Trạng thái được giữ ở mức **`CONDITIONALLY READY`** (thay vì tự tuyên bố hoàn tất tuyệt đối) vì: (a) thao tác merge vào `main`, cấu hình About/Topics và phát hành tag `v1.0` trên GitHub đang chờ phê duyệt riêng của Chủ dự án; (b) Chủ dự án cần xác nhận chấp thuận các giới hạn học thuật đã công bố minh bạch (single-seed `seed=42`, không lưu `.joblib` checkpoint của RF, và việc giữ nguyên chuỗi đường dẫn máy trong log lịch sử `results/**` để bảo toàn SHA-256).
