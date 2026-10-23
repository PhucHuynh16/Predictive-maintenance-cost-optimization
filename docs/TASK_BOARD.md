# TASK BOARD — 10 giai đoạn trong 5 tuần

Ngày chuẩn bị: 2026-10-21. **Cập nhật ghi nhận A3/A6: 2026-10-23 (Asia/Saigon)**. Đã fetch/xác minh PR #9 merge vào origin/main tại `5459d78b17857b6a5562ac0e75ab5357f6e8d33b`; A3-a–g/A6-a–g đã được chủ dự án phê duyệt trong chat sau merge, G4 WAITING_ASSIGNMENT. Mốc checkpoint G3 trước đó tại `9f3634118c2201ea21f8992c1fc059aff5bbed8d`: PR #8 đã merge (2026-10-23 14:57:42 UTC), sau PR #7 và các PR checkpoint W1. Trạng thái hiện hành ở bảng nhiệm vụ và mục Checkpoint G3 bên dưới; các snapshot W1/A5 được giữ làm lịch sử. Mốc checkpoint W1 trước đó là `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f`. Đã đọc Issue #2. Tên giai đoạn/thời điểm bám `ROADMAP.md`; trạng thái dưới đây không tự khởi chạy nhiệm vụ mới.

Trạng thái: `DONE_MERGED` = sản phẩm đã merge theo phạm vi được nghiệm thu; `MERGED_WITH_LIMITATIONS` = sản phẩm đã merge nhưng còn giới hạn phương pháp phải xử lý trước task phụ thuộc; `READY_FOR_ASSIGNMENT` = chỉ đã có prompt; `BLOCKED_APPROVAL` = đợi quyết định; `WAITING_ASSIGNMENT` = quy tắc liên quan đã duyệt nhưng chưa giao task/quyền thực thi; `PLANNED` = giai đoạn tương lai. Merge sản phẩm/phê duyệt quy tắc không đồng nghĩa kiểm thử đã đạt hoặc task đã bắt đầu.

**Bằng chứng nhiệm vụ checkpoint trước (đã merge qua PR #6):** chỉ dẫn chat ngày 2026-10-23 “NHIỆM VỤ: ĐÓNG CHECKPOINT TUẦN 1 VÀ RÀ SOÁT A5 TRƯỚC G3” cho phép cập nhật TASK_BOARD, README và data/README trong phạm vi provenance; không cấp quyền PROJECT_SPEC hoặc triển khai. Quyền này chỉ áp dụng nhiệm vụ checkpoint trước, không phải phạm vi sửa file của lượt hiện tại.

**Bằng chứng nhiệm vụ ghi nhận A5 trước đây (snapshot PR #7):** văn bản chủ dự án “PHÊ DUYỆT CHÍNH THỨC A5 – DATASET VÀ EXPERIMENTAL PROTOCOL”, gửi trong chat ngày 2026-10-23, attachment `28ca3964-7860-4589-8d6c-ad9b1f10f831` (hash/chi tiết tại [PROJECT_SPEC §0](PROJECT_SPEC.md)). Chủ dự án phê duyệt A5.1–A5.7 và cho phép sửa riêng `docs/PROJECT_SPEC.md`, `docs/experimental_protocol.md`, `docs/TASK_BOARD.md`, branch/commit/push/PR riêng và báo cáo Issue #2. **Đây chưa phải lệnh triển khai W2-G3-C**; sau merge PR ghi nhận mới giao task và quyền config/metadata riêng. Không sửa A1–A4/A6, file khác hoặc sản phẩm/nhánh/worktree Antigravity; không tự merge, split, code pipeline, train, baseline/optimization hay mở Test.

**Quyền nhiệm vụ checkpoint trước (PR #9):** chỉ dẫn chat ngày 2026-10-23 “CẬP NHẬT CHECKPOINT G3 VÀ CHUẨN BỊ PHÊ DUYỆT A3/A6 TRƯỚC G4” xác nhận nghiệm thu G3/merge PR #8, cho phép sửa riêng `docs/TASK_BOARD.md`, commit/push/PR và báo cáo Issue #2. Các bảng A3/A6 dưới đây chỉ là đề xuất chờ quyết định chính thức; không sửa spec, quyết định A1–A7 hoặc kích hoạt G4.

**Phê duyệt chính thức ngày 2026-10-23 (Asia/Saigon):** chủ dự án gửi trong chat “PHÊ DUYỆT CHÍNH THỨC A3 VÀ A6 – CHUẨN BỊ GIAI ĐOẠN 4”, xác nhận PR #9 đã merge và phê duyệt nguyên văn A3-a–g/A6-a–g, bao gồm tham số, điều kiện dừng và ngoại lệ. Nguồn chuẩn chi tiết: [bảng gốc PR #9 tại commit 8a0f95a](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/blob/8a0f95aa4e0cc6176af12cb512315f440f1ef034/docs/TASK_BOARD.md); merge SHA `5459d78b17857b6a5562ac0e75ab5357f6e8d33b` đã xác minh trên origin/main. Quyền nhiệm vụ này chỉ sửa `docs/PROJECT_SPEC.md` và `docs/TASK_BOARD.md`, tạo branch/commit/push/PR riêng và báo cáo Issue #2. **“Đây là nhiệm vụ ghi nhận phê duyệt A3/A6, chưa phải lệnh triển khai W2-G4-C.”** Không sửa A1/A2/A4/A5 hoặc các quyết định khác; không tự merge. G3 đã nghiệm thu/merge qua PR #8; G4 chưa thực hiện và cần giao riêng sau khi PR ghi nhận này được merge.

File trong cột phạm vi là quyền dự kiến của task sau khi được kích hoạt, không cấp quyền sửa file chung. `configs/**`, `data/README.md`, README và các tài liệu chung chỉ sửa sau phê duyệt riêng. Read-only dependencies không cho phép sửa sản phẩm của AI kia.

| Task ID / tuần / giai đoạn | Mô tả | AI phụ trách | File được phép thay đổi | Dependencies | Trạng thái | Tiêu chí nghiệm thu |
|---|---|---|---|---|---|---|
| W1-G1-C / W1 / G1: Phân tích và mô hình hóa | Review decision variables, objective, constraints; thiết kế API cost model và bảng test tính tay | Codex | `docs/problem_formulation.md`, `docs/cost_model_review.md` | Đọc spec và roadmap; chủ dự án kích hoạt prompt Codex | DONE_MERGED | PR #3 đã merge; review và 40 ca kiểm tra dự kiến có trên main. Spec hiện hành ở PR #1; chưa có cost code/tests thực thi |
| W1-G1-A / W1 / G1 | Đề cương và sơ đồ pipeline dựa trên formulation được chủ dự án chấp nhận | Antigravity | `docs/project_proposal.md`, `figures/pipeline.*` | W1-G1-C; phê duyệt formulation | DONE_MERGED | PR #4 đã merge: đề cương rút gọn và pipeline Mermaid, phân biệt quyết định đã duyệt/chờ duyệt, cổng test riêng G10 |
| W1-G2-A / W1–2 / G2: Thu thập, kiểm tra và hiểu dữ liệu | Kiểm tra nguồn AI4I, provenance, schema/nhãn, missing/duplicates/leakage, dictionary; EDA notebook | Antigravity | `docs/data_dictionary.md`, `docs/eda_findings.md`, `notebooks/01_eda.ipynb`, `figures/eda/**`; `data/raw/**` local bị ignore | Chủ dự án đã giao; A5 trước bước phát triển/split; metadata chung theo phê duyệt checkpoint | MERGED_WITH_LIMITATIONS | PR #5 đã merge đủ 10 file; raw/EDA local theo báo cáo Antigravity. Exposure được chấp nhận/công khai theo A5.2, không bị xóa hồi tố; audit sáu X/phụ thuộc đã bổ sung qua G3/PR #8; exposure và giới hạn nội suy vẫn còn |
| W2-G3-C / W2 / G3: Tiền xử lý và giao thức đánh giá | Data pipeline, split cố định, preprocessing và chống leakage | Codex | `src/data.py`, `src/preprocessing.py`, `tests/test_data_pipeline.py`, `scripts/run_data_pipeline.py`, riêng `configs/data_pipeline.yaml`, `docs/experimental_protocol.md`, `results/w2_g3/**`; `data/processed/**` local | A5.1–A5.7; giao việc riêng W2-G3-C; chủ dự án nghiệm thu và xác nhận PR #8 merge | DONE_MERGED | PR #8 / merge `9f363411`; 43 tests PASS, pip check đạt; audit raw/sáu X/phụ thuộc, split 6000/2000/2000 tái lập, preprocessing Train-only; chi tiết và giới hạn ở Checkpoint G3 |
| W2-G4-C / W2 / G4: Baseline | Chuẩn bị/chạy B0/B1/B2 bằng cost/constraints đã duyệt | Codex | `src/baselines.py`, `src/cost_model.py`, `src/constraints.py`, `src/evaluation.py`, `scripts/run_baselines.py`, `tests/test_cost_model.py`, `tests/test_constraints.py`, `results/baseline_metrics.csv` | G3 đã nghiệm thu; A3-a–g/A6-a–g đã duyệt; merge PR ghi nhận này rồi giao nhiệm vụ/quyền G4 riêng; phần cost tối thiểu và test phải đạt trước baseline | WAITING_ASSIGNMENT | Cùng split/cost; baseline vi phạm được đánh dấu; logs/config/seed/commit thật; không chờ tới W3 mới định nghĩa cách chấm |
| W2-G4-A / W2 / G4 | Phân tích baseline trong notebook và biểu đồ | Antigravity | `notebooks/02_baselines.ipynb`, `figures/baselines/**` | W2-G4-C; chỉ đọc logs có nguồn gốc | PLANNED | Số liệu khớp logs, phân biệt feasible/infeasible, không sửa kết quả gốc |
| W3-G5-C / W3 / G5: ML và calibration | Mô hình xác suất Logistic Regression/Random Forest, calibration nếu cần | Codex | `src/models.py`, `src/calibration.py`, `src/evaluation.py`, `tests/test_models.py`, `results/model_metrics.csv`; model local bị ignore | W2-G3-C; baseline; protocol/calibration được duyệt | PLANNED | Probabilities hợp lệ; calibration chỉ train folds; validation metrics/runtime có provenance; chưa đọc test |
| W3-G6-C / W3 / G6: Cost và constraints | Hoàn thiện cost model, constraints và test sau bước tối thiểu W2 | Codex | `src/cost_model.py`, `src/constraints.py`, `tests/test_cost_model.py`, `tests/test_constraints.py`, `docs/cost_model_review.md` | W2-G4-C; A1–A3 đã duyệt, mọi thay đổi tiếp theo được duyệt | PLANNED | Unit tests có ví dụ tính tay, η/threshold/budget biên, zero positives, ties và infeasible; API và đơn vị nhất quán |
| W3-G7-C / W3 / G7: Tối ưu chính | Optuna TPE, threshold candidates; Random Search đối chứng nếu được duyệt | Codex | `src/optimization.py`, `scripts/run_optimization.py`, `tests/test_optimization.py`, `results/optimization_trials.csv` | W3-G5-C; W3-G6-C; A4 duyệt | PLANNED | Logs đầy đủ kể cả failed/pruned/infeasible; best-so-far khả thi; budget công bằng; không tuning test |
| W3-G7-A / W3 / G7 | Notebook tối ưu và biểu đồ hội tụ | Antigravity | `notebooks/03_optimization.ipynb`, `src/visualization.py`, `figures/convergence.*` | W3-G7-C; giao diện dữ liệu thống nhất qua chủ dự án | PLANNED | Hình sinh từ trial logs thật, hiển thị rõ cost/feasibility và axes/units |
| W4-G8-C / W4 / G8: Thực nghiệm và đối chiếu | Chạy so sánh, multi-seed, sensitivity, ablation | Codex | `scripts/run_experiments.py`, `src/evaluation.py`, `tests/test_evaluation.py`, `results/**` | G4–G7 đạt; scenarios/seeds/budgets được duyệt | PLANNED | Cùng protocol; mean/std và constraints; sensitivity phân biệt fixed-policy/reoptimization; có code/log/seed/commit |
| W4-G8-A / W4 / G8 | Tổng hợp phân tích, trade-off, limitations | Antigravity | `notebooks/04_results.ipynb`, `docs/results_analysis.md`, `src/visualization.py`, `figures/**` | W4-G8-C; chỉ đọc kết quả thật | PLANNED | Ít nhất 2 hình chính khớp log; không bỏ kết quả xấu; không khẳng định tiết kiệm tiền thật |
| W5-G9-A / W5 / G9: Demo, báo cáo, slide | Report, slides và demo nhẹ | Antigravity | `report/**`, `slides/**`, `scripts/demo.py`, `figures/**` | G8; kết quả test cuối từ W5-G10-C cho bản bàn giao cuối | PLANNED | Báo cáo 8–12 trang, 5–8 slide/demo 5–7 phút; phản ánh constraints, nguồn dữ liệu và chi phí mô phỏng |
| W5-G10-C / W5 / G10: Kiểm thử, tái lập và bàn giao | Khóa nghiệm, test cuối sau cho phép; kiểm thử và hướng dẫn reproduce | Codex | `tests/**`, `scripts/reproduce_results.py`, `docs/reproducibility.md`, `results/final_test_results.json` | G8 đạt; chủ dự án duyệt policy đã khóa và đánh giá test; dependency versions được duyệt | PLANNED | Test cuối không mở lại tuning; reproduce khớp logs; kiểm thử thực tế; báo cả kiểm tra thất bại/chưa chạy |
| W5-G10-A / W5 / G10 | Kiểm tra chéo hình/báo cáo/slide, chuẩn bị bảo vệ | Antigravity | `report/**`, `slides/**`, `docs/results_analysis.md` | W5-G9-A; W5-G10-C | PLANNED | Mọi bảng/hình có log nguồn; giới hạn rõ; đề xuất README/release trình chủ dự án; không tự merge/tag/release |

## Cổng phê duyệt và file chung

- Chủ dự án duyệt A1–A6 trong `PROJECT_SPEC.md` trước code/experimental runs liên quan. Prompt tuần 1 chỉ cho phép review và chuẩn bị tài liệu, không triển khai ngay dependency.
- G4 cần cost model tối thiểu trước khi có baseline; G6 hoàn thiện và kiểm tra sâu hơn. Đây là dependency kỹ thuật được nêu rõ để tránh báo chi phí baseline trước khi có hàm chi phí.
- Chủ dự án duyệt thay đổi README/config/requirements/board và quyết định tích hợp vào main. Hai AI đề xuất diff trong phạm vi được giao, không tự sửa file chung.
- Checkpoint sản phẩm W1 đã đạt theo bảng đối chiếu bên dưới; W2–W5 và release `v1.0` chưa hoàn tất. Việc đóng W1 không vượt cổng A5/G3 hoặc cho phép test cuối.

## Đối chiếu checkpoint W1

| Tiêu chí ROADMAP / bàn giao | Trạng thái và chứng cứ | Giới hạn |
|---|---|---|
| Repository public + README khung | Đạt; repository GitHub và README hiện có | README/checkpoint đã được tích hợp qua PR #6; lượt ghi nhận A5 không sửa README |
| Formulation 1–2 trang, giải thích x/objective/constraints/baselines | Đạt nội dung; PR #3 có hai bản review chi tiết, PR #4 có đề cương rút gọn | Hai review lịch sử chưa là code; số trang in không được Codex render/đo trong lượt này |
| Pipeline | Đạt sản phẩm thiết kế; `figures/pipeline.mmd` trong PR #4 | Không chứng minh pipeline thực thi đã đạt |
| Kế hoạch 5 tuần | Đạt; ROADMAP và bảng nhiệm vụ hiện có | ROADMAP giữ nguyên; không lấy mọi ví dụ làm cấu hình đã duyệt |
| Nguồn dữ liệu, raw local và EDA | Đã tích hợp sản phẩm W1-G2-A qua PR #5; report/dictionary/notebook và 6 hình | Exposure đã được chấp nhận nhưng vẫn là giới hạn; duplicate sáu X/phụ thuộc trước split chưa kiểm tra mới trong lượt ghi nhận |
| Môi trường Python 3.11 | Kết quả thực chạy ghi ở mục môi trường bên dưới | Môi trường EDA Antigravity là 3.14.3; chưa tái chạy notebook trên 3.11 |

**Kết luận lịch sử tại PR #7 (G3 đã được cập nhật ở checkpoint hiện hành):** checkpoint **sản phẩm W1** tại main `d6d0bb9` đã được ghi nhận, cập nhật quản lý tích hợp qua PR #6 tại `8529fe4`. A5.1–A5.7 nay đã được phê duyệt về quy tắc, nhưng audit/kiểm thử thực thi và G3 chưa hoàn tất. W1-G2-A giữ `MERGED_WITH_LIMITATIONS` vì exposure vẫn tồn tại và chưa có audit sáu X mới. PR ghi nhận A5 hiện tại còn chờ chủ dự án duyệt/merge; G3 chưa được giao.

## Lịch sử kiểm tra W1 / ghi nhận A5 (không phải trạng thái G3 hiện hành)

Các mục kiểm tra và bảng môi trường bên dưới ghi nhận lần đóng checkpoint W1/PR #6, **không phải chạy lại raw/môi trường trong lượt ghi nhận A5**. Lượt này chỉ kiểm tra tài liệu/Git và đối chiếu văn bản phê duyệt; chưa audit duplicate/phụ thuộc mới, tạo split hoặc triển khai pipeline.

- Đã fetch origin; đối chiếu GitHub `merged=true` và merge SHA của PR #1 `005b7da`, #3 `41ca766`, #4 `e362cbc`, #5 `d6d0bb9`; Issue #2 đã đọc, gồm báo cáo các AI và giới hạn còn chờ.
- Đã đọc/đối chiếu source/output notebook: 12 code cells có execution count; hash/kích thước ở cell 2; schema/null/duplicate toàn hàng và 12 cột ở cell 3; EDA theo target/UDI ở các cell sau. Đây là kiểm tra tĩnh, không tái chạy notebook hoặc xác minh mọi diễn giải vật lý trong report.
- Antigravity báo cáo đã chạy raw audit/EDA và sinh hình trên Python 3.14.3. Codex không biến kết quả báo cáo đó thành phép chạy mới trên Python 3.11. Chưa đo lại missing/inf/empty hoặc autocorrelation/duplicate sáu X trên raw.
- Chưa có/chưa chạy unit tests cost/constraints/pipeline, split chính thức, preprocessing fit, baseline, ML/calibration, optimization, sensitivity, multi-seed, test cuối hoặc reproduce toàn pipeline. 40 ca kiểm tra W1-G1-C chỉ là thiết kế.
- Metadata provenance trong data/README được đối chiếu report/dictionary/output notebook; không phải xác thực checksum độc lập từ UCI. `origin/main` chỉ track `data/README.md` dưới data, CSV/ZIP không nằm trong tree này; chưa audit toàn bộ lịch sử Git để kết luận không từng có raw.

<a id="kiem-tra-moi-truong-codex"></a>

## Kiểm tra môi trường Codex

Đã kiểm tra ngày **2026-10-23**, trong `worktrees/codex`, dùng `.venv` riêng được Git ignore; không sửa `requirements.txt` hoặc dùng môi trường Antigravity.

| Kiểm tra thực sự đã chạy | Kết quả |
|---|---|
| Python bằng đường dẫn thật | Python **3.11.9**, Windows AMD64; import `venv`/`ensurepip` đạt |
| Tạo `.venv` và gọi Python/pip trong đó | Đạt; `sys.prefix` trỏ đúng worktree Codex; pip **24.0** |
| Resolve manifest với `--dry-run --only-binary=:all:` | Đạt sau khi được phép truy cập mạng; có wheels phù hợp Python 3.11 Windows |
| Cài đủ `requirements.txt` vào venv | Đạt, pip exit 0; installation report ghi 116 distributions được cài (ngoài bootstrap tools) |
| Import 12 package chính | Đạt cả 12; version thực cài ở bảng dưới |
| `pip check` sau khi cài hoàn tất | Đạt, exit 0: `No broken requirements found.` |
| API calibration dự kiến | Khởi tạo `CalibratedClassifierCV(method='sigmoid', cv=StratifiedKFold(5, shuffle=True, random_state=42), ensemble=False)` với RF đạt; **không gọi fit**, không đọc dữ liệu |
| Raw/notebook/pipeline/unit tests | Chưa chạy lại raw/notebook; chưa có pipeline/tests thực thi; không train, calibration fit, tối ưu hoặc mở test |

| Package | Version đã cài và import thành công |
|---|---|
| numpy | 2.4.6 |
| pandas | 3.1.0 |
| scipy | 1.17.1 |
| scikit-learn | 1.9.1 |
| optuna | 5.0.0 |
| matplotlib | 3.11.2 |
| seaborn | 0.13.2 |
| joblib | 1.6.0 |
| PyYAML | 6.0.3 |
| pytest | 9.1.1 |
| jupyterlab | 4.6.4 |
| ipykernel | 7.4.0 |

Các lỗi/giới hạn quan sát được: alias WindowsApps `python`/`py` không truy cập được trong phiên này; đường dẫn Python thật chạy được. Lệnh in đường dẫn tiếng Việt ban đầu lỗi `cp1258`, được khắc phục bằng `-X utf8`. Resolve lần đầu trong sandbox lỗi DNS `getaddrinfo failed`, chưa nói lên tương thích package; resolve/cài với quyền mạng sau đó thành công. Một lần dò version khi pip còn đang cài báo thiếu metadata Optuna; sau khi cài hoàn tất, import/version cả 12 package đều đạt. Không coi `pip check` trong môi trường chưa cài xong là bằng chứng đủ.

Các lệnh chính đã chạy từ worktree Codex (log/report/freeze đều local bị ignore):

```powershell
& 'C:\Users\Huỳnh Phúc\AppData\Local\Python\pythoncore-3.11-64\python.exe' -X utf8 -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install --dry-run --only-binary=:all: --no-cache-dir --retries 0 --timeout 15 -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m pip install --only-binary=:all: --no-cache-dir --retries 0 --timeout 15 --report .venv/w1-install-report.json -r requirements.txt
.\.venv\Scripts\python.exe -X utf8 -m pip check
.\.venv\Scripts\python.exe -X utf8 -m pip freeze
```

Lưu thực tế: `.venv/w1-install.log`, `.venv/w1-install-report.json`, `.venv/w1-env-check.log`, `.venv/w1-freeze.txt`; không commit package/log/venv. Manifest đã dùng có SHA-256 `f98a129a19a45a32e25158702ab156a8dfb66b350c433e2e202579575d526d43`, không đổi so với base. Các version trên là snapshot đã kiểm tra, **chưa phải lockfile được phê duyệt**. Import/constructor thành công không chứng minh pipeline/ML đúng hoặc notebook Antigravity tái lập trên 3.11; cần khóa dependencies và kiểm tra tương ứng trong task sau, không mở training để kiểm thử ở lượt này.

## Snapshot A5 / cổng G3 tại PR #7 — đã được checkpoint G3 bên dưới cập nhật

Quy tắc và bảng đối chiếu **A5.1–A5.7 đã phê duyệt** ở [PROJECT_SPEC §9](PROJECT_SPEC.md) và [experimental_protocol §6–§8](experimental_protocol.md):

| Quyết định | Nội dung đã chốt | Trạng thái thực thi |
|---|---|---|
| A5.1 | AI4I, random split cho nội suy; không tuyên bố thời gian/máy mới/hiệu quả bảo trì thật; ghi nhận phụ thuộc UDI/nhiệt độ | Rà soát phụ thuộc trước split chưa chạy mới trong lượt này |
| A5.2 | Tiếp tục dù EDA toàn nhãn; công khai exposure; từ khóa protocol không Test selection/đổi split | Không gọi holdout hoàn toàn chưa được xem xét; không mở Test |
| A5.3 | Exact duplicate đúng sáu X; giữ raw/nhãn; trùng thì dừng, báo số lượng, trình group-disjoint riêng | Chưa audit sáu X; chưa duyệt group-disjoint cụ thể |
| A5.4 | UDI order; Test20% trước rồi Validation25% của phần80%; stratify target/random_state42 mỗi bước; IDs/hash/version/metadata | Chưa split; duplicate/phụ thuộc phải hoàn thành trước; bất thường cần đổi protocol thì trình lại |
| A5.5 | OHE Type ignore unknown; StandardScaler numeric LR; RF numeric giữ nguyên/không bắt buộc scaling; train-only fit, Val/Test transform; missing báo lỗi; không clipping/feature engineering/resampling/SMOTE/ID/nhãn phụ | Chưa code/fit preprocessing |
| A5.6 | RF sigmoid 5 stratified train folds shuffle=True seed42, ensemble=False tại G5; đúng ranh giới fold; không Val/Test fit calibrator; không refit Train+Val trước Test đầu | Chưa calibration/refit; dữ liệu không đáp ứng thì xin quyết định mới; **B2 chờ A6 trước G4** |
| A5.7 | Test G10 sau khóa model/preprocessing/hyperparameters/threshold/policy/scenarios/constraints/seeds/dependencies/metadata/protocol và phê duyệt riêng | Chưa có quyền đánh giá Test |

G3 ở trạng thái **WAITING_ASSIGNMENT**, không phải In Progress/Done. Sau khi PR ghi nhận A5 được merge, chủ dự án sẽ giao riêng **W2-G3-C** và quyền sửa config/metadata liên quan. Đầu vào raw/hashes và các điều kiện kiểm tra phải đáp ứng task đó; phát hiện duplicate hoặc bất thường cần đổi protocol thì dừng phần split để trình lại. Khóa dependencies theo quy trình trước thực nghiệm; môi trường đã cài không thay cho quyền sửa requirements/config. Không chạy audit/split/pipeline trong nhiệm vụ hiện tại.

A2–A4/A6 giữ nguyên, còn các chi tiết ở spec cần chốt trước G4–G7 tương ứng. B2 chưa chốt calibration/cấu hình đầy đủ chỉ nhờ A5; nhiệm vụ này không mở G4/G5 hay quyền Test cuối.

Các đoạn AGENTS/prompt/handoff và ghi chú cũ của spec còn nói bootstrap/chưa merge là snapshot lịch sử. Phần Giới hạn gốc của data/README còn ghi “chưa có giá trị được duyệt”, khác A2 hiện hành; file này/README ngoài phạm vi lượt A5, dùng PROJECT_SPEC làm nguồn quyết định. Các khuyến nghị trong EDA chỉ là quy tắc đã duyệt khi có quyết định chủ dự án tương ứng ở A5; không tự nhận feature engineering hoặc group-disjoint đã duyệt. Không sửa branch/worktree Antigravity.

## Checkpoint G3 hiện hành — đã nghiệm thu và merge

Chủ dự án xác nhận nghiệm thu G3 trong chỉ dẫn hiện tại. [PR #8](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/8) merged=true; merge SHA `9f3634118c2201ea21f8992c1fc059aff5bbed8d`, head `6f9a1b2723a1a465f744cbf71ccc1e12f89ce652`. Nguồn: [protocol §9.3](experimental_protocol.md), [báo cáo Issue #2](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/issues/2#issuecomment-6367482665) và log đã merge, được đọc lại trong nhiệm vụ này; không chạy lại audit/split/pytest.

| Tiêu chí | Bằng chứng nghiệm thu G3 | Giới hạn |
|---|---|---|
| Raw/provenance | UCI official ZIP; CSV 522048 bytes, SHA-256 `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`; 10000×14, không missing/nonfinite; [acquisition](../results/w2_g3/acquisition.json) | Hash khớp tham chiếu; raw local bị ignore, không commit |
| Duplicate sáu X | 0 nhóm, 0 hàng trong nhóm, 0 hàng dư; không dùng target/ID/nhãn phụ làm khóa | Không chứng minh các hàng độc lập hoặc không near-duplicate |
| Phụ thuộc trước split | ACF Air lag1/100 = 0.999359/0.960316; Process = 0.998466/0.892249; phù hợp random walk đã biết, không có phát hiện mới buộc đổi protocol | Không chứng minh IID, stationarity, thời gian/máy/nhà máy mới |
| Split A5.4 | Test20% trước, Validation25% của phần80%; seed42/stratify target cả hai bước; 6000/2000/2000, disjoint/bảo toàn IDs | Target chỉ dùng cơ học cho phân tầng; không khảo sát Test coverage hoặc chọn lại seed |
| Tái lập | `g3_reproduce`, `g3_verified`, `g3_submission` cùng manifest SHA-256 `6dd33ba68c5a4d5d18b8db1fbe4d6f57f8dbfe667d96fe21d6d61bf62cf64522`; [run bàn giao](../results/w2_g3/runs/g3_submission/run.json) có IDs hashes, config/source/dependencies/command/runtime | IDs, CSV, preprocessor/mảng thực tế chỉ local; không phải tái lập toàn G4–G10 |
| Preprocessing/leakage | Sáu X; OHE unknown ignore; LR scaler, RF passthrough; fit Train6000, transform Validation2000 | Test chưa transform/evaluate; không model/calibration fit; EDA toàn nhãn trước đó không thể xóa exposure |
| Tests/môi trường | [pytest log](../results/w2_g3/unit_tests_recheck.json): 43 PASS, 0 FAIL, fixture synthetic; Python3.11.9 / sklearn1.9.1 / pip check đạt; versions đầy đủ trong run log | Kết quả G3 đã chạy trước đây, không chạy lại trong task tài liệu; không có tests cost/baseline |
| Lần chạy bị chặn | [g3_primary](../results/w2_g3/runs/g3_primary/run.json) BLOCKED trước split do parser header BOM; fix `4f47134`, giữ bytes/hash raw và log cũ, kiểm thử/rerun đạt | Không bỏ lịch sử thất bại |

Lệnh G3 đã nghiệm thu: `.venv/Scripts/python.exe -X utf8 -m pytest tests/test_data_pipeline.py -q -p no:cacheprovider`; entry point `scripts/run_data_pipeline.py --run-id <tên-mới>`. Đây là lệnh tái lập tham chiếu, không được chạy trong task checkpoint này. G3 DONE_MERGED không đồng nghĩa toàn Tuần 2 hoặc G4 đã hoàn tất.

## A3/A6 — 14 quyết định đã phê duyệt, chưa triển khai G4

**Đã duyệt, giữ nguyên:** A3: `a=1[p>=τ]`, `τ∈[0,1]`, b=0.10, K=floor(bN), recall chỉ là metric, B0 riêng, giữ ties nguyên nhóm/không top-k, violation=infeasible. A6: B0 reactive, B1 fixed wear rule, B2 LR với τ=0.5, P RF+h/τ; cùng objective/capacity và báo baseline infeasible. A5 đã duyệt OHE/scaler/Train-only và RF sigmoid train-folds tại G5; **calibration B2 nay được chốt riêng theo A6-c: không post-calibration**.

**Toàn bộ 14 hàng dưới đây đã được chủ dự án PHÊ DUYỆT trong chỉ dẫn hiện tại**, giữ nguyên nội dung/giải thích của bảng gốc PR #9. Merge PR #9 trước đó chỉ ghi nhận đề xuất; phê duyệt chính thức đến từ văn bản chat theo bằng chứng ở đầu tài liệu. Ghi nhận phê duyệt không phải kết quả chạy G4. M=Σa, P=Σy, TP=Σay; không có trọng số mẫu.

| Quyết định A3 | Quy tắc đã phê duyệt | Lý do/phạm vi |
|---|---|---|
| A3-a Candidate thresholds | Với mỗi h, trên Validation: T={0,1}∪unique(p), sort/deduplicate exact, không rounding; quét mỗi candidate, dùng `>=`; khóa τ trước Test | Bao phủ các action vectors biểu diễn được trong [0,1]; không grid tùy ý hoặc τ>1; B0 vẫn riêng |
| A3-b N=0 / input sai | Reject evaluation N=0; shape sai, nhãn/actions không binary, p không finite/ngoài [0,1], cost/domain sai đều ERROR với reason; không repair/clip hay gán feasible=false cho lỗi input | Phân biệt lỗi với policy capacity-infeasible; không chia 0 |
| A3-c P=0 | Cost, M/K và feasibility vẫn tính bình thường; Recall=null, reason=NO_POSITIVES; áp dụng bảng A6 về metrics khác | Không biến recall thành constraint; không loại batch khỏi cost |
| A3-d Ties | Giữ nhóm exact bằng nhau, không tolerance trên p, không tách nhóm/top-k. τ=0 chọn tất cả; τ=1 vẫn chọn p=1 | Comparator/domain/ties đã duyệt; chỉ làm rõ cách so sánh số và biên |
| A3-e Capacity violation | K=floor(N/10) bằng số nguyên cho b=0.10; excess=max(0,M-K), excess_rate=excess/N; feasible iff excess=0; log cả M,K,excess và rate | Không sai số float ở floor; không penalty tùy ý, không sửa action |
| A3-f No-feasible | best=null, status=NO_FEASIBLE_CANDIDATE; log số candidates và phạm vi h đã xét. h riêng có count(p=1)>K không có τ feasible; không suy ra toàn H vô nghiệm; B0 báo riêng | Không âm thầm mở domain hoặc thay bằng B0 trong kết quả P |
| A3-g Tie-break | Chọn feasible trước; minimum observed cost trên Validation, rồi M nhỏ hơn, rồi τ lớn hơn trong cùng h, cuối cùng thứ tự h cố định đăng ký trước search (không theo arrival). Hòa cost iff chênh tuyệt đối ≤1e-9 cost units so với minimum toàn bộ, không gom dây chuyền | Tái lập, ưu tiên ít hành động; không dùng Test/metric phụ chọn thắng. Thứ tự H cần khóa khi A4 được chốt |

| Quyết định A6 | Quy tắc đã phê duyệt | Lý do/công bằng |
|---|---|---|
| A6-a B1 | `a=1[Tool wear [min]>=200]`, w=200 phút, cố định trước run; không fit/tune w | Heuristic đã nêu trong spec, chưa có chứng cứ hiệu quả; không dựa vào Test hoặc sửa ngưỡng để feasible |
| A6-b B2 LR | L2, C=1.0, solver=lbfgs, l1_ratio=0.0 (API1.9.1; không truyền penalty deprecated), dual=False, fit_intercept=True, tol=1e-4, max_iter=2000, class_weight=None, random_state=42, warm_start=False, verbose=0; n_jobs=None/intercept_scaling=1 là tham số API không tác dụng với lbfgs. Không sample_weight/CV/tuning; score=predict_proba lớp1, a=1[p>=0.5] | Một baseline cấu hình cố định; preprocessing A5.5 đã duyệt, chỉ fit Train. Seed ghi metadata dù lbfgs không dùng seed. ConvergenceWarning/nonfinite => FAILED, giữ log và xin quyết định, không tự retry solver/C |
| A6-c Calibration B2 | Không post-calibration; dùng xác suất LR trực tiếp; không fit calibrator hoặc refit Train+Val | Giữ baseline đơn giản, không chọn calibration bằng Validation/Test. RF sigmoid theo A5.6 vẫn áp dụng cho P tại G5; so sánh phản ánh toàn phương pháp, không quy hết lợi ích cho optimizer |
| A6-d PR-AUC estimator | Báo tên `average_precision` (AP non-interpolated), sklearn.average_precision_score(y,p,pos_label=1), không trapezoidal AUC; ROC-AUC từ cùng p. B2/P dùng score liên tục, không dùng actions; B0/B1 ranking/probability metrics=null reason=NO_PROBABILITY_MODEL | AP khác trapezoid PR area. B0/B1 chỉ là policy nên không bịa probability; vẫn báo đủ cost/action metrics cho cả bốn |
| A6-e Undefined metrics | Precision=TP/M nếu M>0, ngược lại null/NO_PREDICTED_POSITIVES; Recall=TP/P nếu P>0, ngược lại null/NO_POSITIVES; F1=2TP/(P+M) nếu P+M>0, ngược lại null/NO_TRUE_OR_PREDICTED_POSITIVES. ROC-AUC=null/SINGLE_CLASS nếu P=0 hoặc P=N; AP=null/NO_POSITIVES nếu P=0, AP=1 nếu P=N và có score hợp lệ. Brier=mean((p-y)^2) cho B2/P, vẫn hợp lệ nếu một lớp | Tính công thức rõ thay vì mặc định warning/0. F1=0 khi chỉ P hoặc M bằng0; null ghi JSON null, kèm reason, không thay bằng0 khi tổng hợp |
| A6-f Mẫu số saving=0 | Báo cost, cost/N và absolute saving=C_B0-C; saving_pct=null/ZERO_REFERENCE_COST nếu C_B0=0 | P=0 không thể báo % tiết kiệm có nghĩa; absolute saving có thể âm |
| A6-g Baseline infeasible | Giữ nguyên B1/B2 actions/τ, báo cost, classification metrics và excess như mọi policy; tách feasible ranking, không chọn best feasible từ chúng. B0 riêng luôn capacity-feasible khi N>0; nếu P không feasible thì báo tình trạng đó cạnh B0 | Không sửa baseline bằng top-k/retune; infeasible có thể cost thấp nhưng không là nghiệm đạt constraint |

Nguồn kỹ thuật (xem ngày 2026-10-23): [LR API](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [AP](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [F1](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html). Ở nhiệm vụ PR #9 đã đối chiếu signature/get_params và docstring trong sklearn1.9.1 local; chỉ import/đọc API, không fit hay mở dataset. Trong nhiệm vụ ghi nhận hiện tại chỉ đối chiếu tài liệu/Git và 14 hàng gốc; không chạy lại kiểm tra môi trường. Các quy ước null/failed/tolerance và giá trị baseline trong bảng nay đã được chủ dự án phê duyệt theo bằng chứng ở đầu tài liệu.

## Điều kiện bắt đầu W2-G4-C

**TRẠNG THÁI G4: WAITING_ASSIGNMENT; chưa thực hiện.** G3 đã nghiệm thu/merge; A3-a–g/A6-a–g đã duyệt, không còn chờ quyết định 14 hàng này. Sau khi PR ghi nhận hiện tại được merge, chủ dự án sẽ giao riêng W2-G4-C với quyền file/config/log và tiêu chí nghiệm thu cụ thể. Phê duyệt A3/A6 không tự kích hoạt G4. Trước chạy baseline, cost/constraints tối thiểu cùng unit tests phải đạt; dùng cùng split G3, objective A2, b/capacity và định nghĩa metrics đã khóa cho B0/B1/B2/P. Chỉ phát triển/chọn policy trên Train/Validation, không Test. P tối ưu có ngân sách khác baseline cố định: báo rõ lợi ích của toàn phương pháp; chưa tuyên bố đối chứng equal-budget hoặc tách tác dụng calibration/optimizer nếu chưa được giao ablation.

Miền H/thứ tự H/budget chi tiết A4 phải được chốt trước G5–G7/tối ưu tương ứng, không được phê duyệt thêm trong nhiệm vụ A3/A6. G4 cần fit LR tối thiểu chỉ khi được giao; nhiệm vụ tài liệu hiện tại không train, không baseline/cost code, không đánh giá Test. PROJECT_SPEC được cập nhật A3/A6 trong đúng phạm vi nhiệm vụ hiện tại; README/các file khác giữ nguyên snapshot; trạng thái quản lý G3 lấy theo xác nhận chủ dự án và PR #8, quyết định A1–A7 vẫn lấy từ spec cùng phê duyệt chat tương ứng.
