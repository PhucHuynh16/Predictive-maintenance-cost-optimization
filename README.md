# Tối ưu chi phí bảo trì dự đoán bằng Machine Learning

Đồ án cá nhân môn **Nhập môn tối ưu hóa**, thực hiện trong **5 tuần / 10 giai đoạn** với sự hỗ trợ của Codex và Antigravity.

## Mục tiêu

Sử dụng xác suất hỏng hóc từ Machine Learning để lựa chọn chính sách bảo trì nhằm giảm **chi phí mô phỏng**, có kiểm tra ràng buộc nguồn lực và so sánh với baseline.

Dataset: [AI4I 2020 — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), dữ liệu tổng hợp gồm 10.000 quan sát.

Chi phí và hiệu quả bảo trì là giả định mô phỏng đã được phê duyệt trong phạm vi [PROJECT_SPEC](docs/PROJECT_SPEC.md); không phải dữ liệu chi phí thực tế hay bằng chứng tiết kiệm tại nhà máy.

## Trạng thái

Cập nhật ngày **2026-10-23 (Asia/Saigon)**: **đạt checkpoint sản phẩm W1** theo ROADMAP (repository public, README, formulation, đề cương, pipeline và kế hoạch 5 tuần). Đã xác minh PR [#1](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/1), [#3](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/3), [#4](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/4), [#5](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/5) đã merge vào `main`; mốc đối chiếu `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f`.

| Sản phẩm đã tích hợp | Bằng chứng | Giới hạn |
|---|---|---|
| W1-G1-C: formulation, cost/constraints review, thiết kế API và 40 ca kiểm tra dự kiến | PR #3; spec quyết định hiện hành ở PR #1 | Bảng test là thiết kế, chưa có cost code/unit tests thực thi |
| W1-G1-A: đề cương và pipeline Mermaid | PR #4 | Là thiết kế phương pháp, chưa phải pipeline đã chạy |
| W1-G2-A: dictionary, EDA report, notebook có output, 6 hình và module visualization | PR #5 | Antigravity đã chạy EDA trên Python 3.14.3; Codex chỉ đối chiếu source/output, chưa chạy lại raw/notebook |

Raw đã được Antigravity tải và kiểm tra local ngày 2026-10-21; **không commit CSV/ZIP lên GitHub**. [Provenance](data/README.md) ghi rõ nguồn chứng cứ. Chưa có split chính thức, preprocessing, baseline metrics, huấn luyện ML hay optimization; hình EDA không phải kết quả tối ưu.

**Cổng G3 vẫn đóng:** A5 được duyệt một phần, cần chốt phụ thuộc hàng, duplicate, exposure từ EDA toàn dữ liệu và protocol chi tiết. [Bản rà soát A5](docs/experimental_protocol.md) chỉ là đề xuất. Checkpoint W1 không cấp quyền G3/G4 hoặc mở test; PR quản lý checkpoint này còn chờ chủ dự án duyệt/merge.

Hai AI làm việc trên nhánh/worktree riêng; chỉ chủ dự án phê duyệt thay đổi file chung, công thức và việc tích hợp vào `main`.

## Tài liệu

- [Lộ trình gốc: 10 giai đoạn / 5 tuần](docs/ROADMAP.md), được sao chép nguyên văn từ tài liệu chủ dự án cung cấp.
- [Quy tắc cho hai AI](AGENTS.md).
- [Đặc tả: quyết định đã duyệt và chi tiết còn chờ](docs/PROJECT_SPEC.md).
- [Bảng nhiệm vụ](docs/TASK_BOARD.md).
- [Formulation review lịch sử](docs/problem_formulation.md) và [cost model review](docs/cost_model_review.md).
- [Đề cương](docs/project_proposal.md) và [pipeline Mermaid](figures/pipeline.mmd).
- [Data dictionary](docs/data_dictionary.md), [EDA findings](docs/eda_findings.md) và [notebook EDA](notebooks/01_eda.ipynb).
- [Rà soát A5 trước G3 — đề xuất chờ duyệt](docs/experimental_protocol.md).
- [Prompt Antigravity tuần 1](docs/WEEK1_ANTIGRAVITY.md).
- [Prompt Codex tuần 1](docs/WEEK1_CODEX.md).
- [Nguồn và cách quản lý dữ liệu](data/README.md).
- [Bàn giao và kiểm tra Git](docs/BOOTSTRAP_HANDOFF.md).

## Cấu trúc

```text
configs/     cấu hình được phê duyệt
data/        hướng dẫn dữ liệu; raw/processed được Git bỏ qua
docs/        lộ trình, đặc tả, nhiệm vụ và bàn giao
notebooks/   EDA và phân tích do Antigravity phụ trách
src/         pipeline, ML, cost model, constraints và optimization
scripts/     entry point thực nghiệm/tái lập; demo có phân quyền riêng
tests/       kiểm thử của Codex sau phê duyệt công thức
results/     logs và kết quả thực nghiệm thật, có nguồn gốc
figures/     biểu đồ do Antigravity tạo từ dữ liệu/logs được phép
report/      báo cáo
slides/      thuyết trình
```

Các thư mục chưa có sản phẩm dùng `.gitkeep`. Source hiện có `src/visualization.py` và notebook EDA của Antigravity; các module pipeline/ML/cost/optimization chưa được triển khai.

## Môi trường Codex

Python mục tiêu **3.11**. Kết quả kiểm tra ngày 2026-10-23 và các lệnh thực sự đã chạy được ghi ở [TASK_BOARD](docs/TASK_BOARD.md#kiem-tra-moi-truong-codex). `requirements.txt` vẫn là manifest chưa khóa version; không thay đổi file này trong nhiệm vụ checkpoint. Chưa có lệnh tái lập thực nghiệm ML để chạy.

Mỗi AI dùng `.venv` riêng trong worktree của mình. Lệnh chuẩn bị môi trường từ đúng worktree:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu alias `py` không chạy, dùng đường dẫn Python 3.11 thật trên máy; ví dụ máy khởi tạo:

```powershell
& 'C:\Users\Huỳnh Phúc\AppData\Local\Python\pythoncore-3.11-64\python.exe' -X utf8 -m venv .venv
```

Đường dẫn trên đã chạy được Python 3.11.9 trong phiên kiểm tra; alias `py`/`python` qua WindowsApps không chạy được. `-X utf8` tránh lỗi encoding khi in đường dẫn tiếng Việt. Đề nghị khóa dependency trong nhiệm vụ riêng có phê duyệt file chung sau khi kiểm chứng cài đặt. Demo Streamlit chỉ là tùy chọn về sau, chưa thêm dependency.

## Giới hạn nghiên cứu

Tối ưu chi phí trên nhãn validation là đánh giá chính sách mô phỏng, không chứng minh tác động nhân quả của bảo trì. EDA ban đầu đã xem toàn bộ dataset và nhãn; không thể tuyên bố các hàng test tương lai hoàn toàn chưa từng bị xem xét. Việc cô lập test sau này chỉ ngăn tiếp tục sử dụng trong development. Random split, nếu được chấp thuận sau review, đánh giá nội suy trên cùng bộ dữ liệu tổng hợp có phụ thuộc, không chứng minh tổng quát hóa theo thời gian/nhà máy mới. Các thông số đã duyệt nằm trong đặc tả; ví dụ khác trong lộ trình không tự trở thành cấu hình.

Các trạng thái bootstrap trong `AGENTS.md`, prompt, `BOOTSTRAP_HANDOFF.md` và một số đoạn lịch sử của spec/review phản ánh lúc viết. Bằng chứng merge và chỉ dẫn quản lý checkpoint ngày 2026-10-23 được ghi tại TASK_BOARD; lượt này không sửa các tài liệu lịch sử hoặc quyết định A1–A7.
