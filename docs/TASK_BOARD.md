# TASK BOARD — 10 giai đoạn trong 5 tuần

Ngày chuẩn bị: 2026-10-21. **Cập nhật checkpoint: 2026-10-23 (Asia/Saigon)**. Đã đối chiếu `origin/main` tại `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f` và Issue #2: PR #1/#3/#4/#5 đã merge. Tên giai đoạn và thời điểm bám `ROADMAP.md`; G2 bắt đầu tuần 1 và hoàn thiện tuần 2. Trạng thái dưới đây không tự khởi chạy nhiệm vụ mới.

Trạng thái: `DONE_MERGED` = sản phẩm đã merge theo phạm vi được nghiệm thu; `MERGED_WITH_LIMITATIONS` = sản phẩm đã merge nhưng còn giới hạn phương pháp phải xử lý trước task phụ thuộc; `READY_FOR_ASSIGNMENT` = chỉ đã có prompt; `BLOCKED_APPROVAL` = đợi chủ dự án duyệt; `PLANNED` = giai đoạn tương lai. Mọi task có dependency ngầm là được chủ dự án kích hoạt. Merge sản phẩm không đồng nghĩa mọi kiểm thử/giao thức đã đạt.

**Bằng chứng cho phép sửa file chung:** chỉ dẫn chat ngày 2026-10-23 “NHIỆM VỤ: ĐÓNG CHECKPOINT TUẦN 1 VÀ RÀ SOÁT A5 TRƯỚC G3”: chủ dự án xác nhận PR #1/#3/#4/#5 đã merge, cho phép cập nhật trạng thái thực tế trong `docs/TASK_BOARD.md`, `README.md` và `data/README.md` chỉ cho provenance đã xác minh; cho phép commit/push, tạo PR riêng và báo cáo Issue #2. Không cấp quyền sửa PROJECT_SPEC/quyết định A1–A7, triển khai G3/G4, train ML hoặc merge PR. Bản review thuộc Codex được ghi tại `docs/experimental_protocol.md`, không có code pipeline.

File trong cột phạm vi là quyền dự kiến của task sau khi được kích hoạt, không cấp quyền sửa file chung. `configs/**`, `data/README.md`, README và các tài liệu chung chỉ sửa sau phê duyệt riêng. Read-only dependencies không cho phép sửa sản phẩm của AI kia.

| Task ID / tuần / giai đoạn | Mô tả | AI phụ trách | File được phép thay đổi | Dependencies | Trạng thái | Tiêu chí nghiệm thu |
|---|---|---|---|---|---|---|
| W1-G1-C / W1 / G1: Phân tích và mô hình hóa | Review decision variables, objective, constraints; thiết kế API cost model và bảng test tính tay | Codex | `docs/problem_formulation.md`, `docs/cost_model_review.md` | Đọc spec và roadmap; chủ dự án kích hoạt prompt Codex | DONE_MERGED | PR #3 đã merge; review và 40 ca kiểm tra dự kiến có trên main. Spec hiện hành ở PR #1; chưa có cost code/tests thực thi |
| W1-G1-A / W1 / G1 | Đề cương và sơ đồ pipeline dựa trên formulation được chủ dự án chấp nhận | Antigravity | `docs/project_proposal.md`, `figures/pipeline.*` | W1-G1-C; phê duyệt formulation | DONE_MERGED | PR #4 đã merge: đề cương rút gọn và pipeline Mermaid, phân biệt quyết định đã duyệt/chờ duyệt, cổng test riêng G10 |
| W1-G2-A / W1–2 / G2: Thu thập, kiểm tra và hiểu dữ liệu | Kiểm tra nguồn AI4I, provenance, schema/nhãn, missing/duplicates/leakage, dictionary; EDA notebook | Antigravity | `docs/data_dictionary.md`, `docs/eda_findings.md`, `notebooks/01_eda.ipynb`, `figures/eda/**`; `data/raw/**` local bị ignore | Chủ dự án đã giao; A5 trước bước phát triển/split; metadata chung theo phê duyệt checkpoint | MERGED_WITH_LIMITATIONS | PR #5 đã merge đủ 10 file; raw/EDA kiểm tra local theo báo cáo Antigravity. Chưa xác minh duplicate riêng sáu X; EDA toàn nhãn có exposure; không xác nhận đã đạt tiêu chí development-only EDA |
| W2-G3-C / W2 / G3: Tiền xử lý và giao thức đánh giá | Data pipeline, split cố định, preprocessing và chống leakage | Codex | `src/data.py`, `src/preprocessing.py`, `tests/test_data_pipeline.py`, `docs/experimental_protocol.md`; `data/processed/**` local | W1-G2-A; chốt A5 bổ sung sau review; giao task riêng; quyền config/split metadata chung | BLOCKED_APPROVAL | Chưa triển khai. Review trước G3 có tại experimental_protocol; sau duyệt mới tạo split disjoint/tái lập, cô lập test khỏi development và fit trên train |
| W2-G4-C / W2 / G4: Baseline | Chuẩn bị/chạy B0/B1/B2 bằng cost/constraints đã duyệt | Codex | `src/baselines.py`, `src/cost_model.py`, `src/constraints.py`, `src/evaluation.py`, `scripts/run_baselines.py`, `tests/test_cost_model.py`, `tests/test_constraints.py`, `results/baseline_metrics.csv` | W2-G3-C; A1–A3/A6 duyệt; phần cost tối thiểu và test phải đạt trước baseline | PLANNED | Cùng split/cost; baseline vi phạm được đánh dấu; logs/config/seed/commit thật; không chờ tới W3 mới định nghĩa cách chấm |
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
| Repository public + README khung | Đạt; repository GitHub và README hiện có | README checkpoint đang trình PR riêng; chủ dự án quyết định merge |
| Formulation 1–2 trang, giải thích x/objective/constraints/baselines | Đạt nội dung; PR #3 có hai bản review chi tiết, PR #4 có đề cương rút gọn | Hai review lịch sử chưa là code; số trang in không được Codex render/đo trong lượt này |
| Pipeline | Đạt sản phẩm thiết kế; `figures/pipeline.mmd` trong PR #4 | Không chứng minh pipeline thực thi đã đạt |
| Kế hoạch 5 tuần | Đạt; ROADMAP và bảng nhiệm vụ hiện có | ROADMAP giữ nguyên; không lấy mọi ví dụ làm cấu hình đã duyệt |
| Nguồn dữ liệu, raw local và EDA | Đã tích hợp sản phẩm W1-G2-A qua PR #5; report/dictionary/notebook và 6 hình | Codex đối chiếu source/output đã lưu, không chạy lại raw; exposure và duplicate sáu X còn mở |
| Môi trường Python 3.11 | Kết quả thực chạy ghi ở mục môi trường bên dưới | Môi trường EDA Antigravity là 3.14.3; chưa tái chạy notebook trên 3.11 |

**Kết luận:** đóng checkpoint **sản phẩm W1** tại main `d6d0bb9` theo các PR đã merge và chỉ dẫn chủ dự án ngày 2026-10-23; bản cập nhật quản lý này chờ duyệt PR. Không gọi toàn bộ giao thức A5/G2→G3, kiểm thử thực thi hay kết quả ML là hoàn tất. W1-G2-A đã bàn giao đủ file nhưng giữ trạng thái `MERGED_WITH_LIMITATIONS` để không che tiêu chí development-only EDA chưa đạt. G3 chưa được giao.

## Kiểm tra đã chạy và chưa chạy

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

## Cổng bắt đầu W2-G3-C và điểm cần chủ dự án chốt

Chi tiết/bằng chứng và lựa chọn A5 ở [experimental_protocol.md](experimental_protocol.md), **chỉ là đề xuất**:

1. Chấp nhận mục tiêu nội suy cùng dữ liệu tổng hợp có phụ thuộc nếu giữ random split, hoặc yêu cầu protocol khác cho mục tiêu theo thứ tự/thời gian.
2. Chấp nhận giới hạn exposure từ EDA toàn nhãn và cơ chế cô lập về sau, hoặc yêu cầu dữ liệu kiểm chứng độc lập mới; chia lại không tạo test hoàn toàn chưa được xem xét.
3. Audit duplicate đúng sáu X; giữ raw/nhãn; nếu có nhóm trùng thì dừng trước split và trình group-disjoint, không tự xóa hàng/đổi tỷ lệ.
4. Khóa thuật toán/thứ tự random stratified split, EDA scope, IDs/hash/versions/seeds; không thử nhiều split theo coverage nhãn phụ hoặc kết quả thuận lợi.
5. Chốt preprocessing G3, calibration train-fold/refit và cổng test cuối theo review; quyền config/metadata chung phải rõ. Môi trường đã cài không đồng nghĩa config đã được duyệt.
6. Chủ dự án giao riêng W2-G3-C sau các quyết định trên và đầu vào raw được cung cấp/xác minh hợp lệ trong worktree Codex. A2–A4/A6 còn chi tiết ở spec cần chốt trước task G4–G7 tương ứng; không mở G4 từ nhiệm vụ này.

Các đoạn spec/AGENTS/prompt/handoff còn nói bootstrap/chưa merge là snapshot lịch sử. Phần Giới hạn gốc của data/README còn ghi “chưa có giá trị được duyệt”, khác với A2 hiện hành; chỉ bổ sung provenance theo quyền được giao, giữ nguyên đoạn này và dùng PROJECT_SPEC làm nguồn quyết định. Không sửa spec/quyết định A1–A7 trong phạm vi hiện tại; dùng bằng chứng merge và chỉ dẫn ngày 2026-10-23 cho tiến độ. Khuyến nghị EDA về split/clipping/feature mới không tự là phê duyệt. Không sửa branch/worktree Antigravity.
