# Tối ưu chi phí bảo trì dự đoán bằng Machine Learning

Đồ án cá nhân môn **Nhập môn tối ưu hóa**, thực hiện trong **5 tuần / 10 giai đoạn** với sự hỗ trợ của Codex và Antigravity.

## Mục tiêu

Sử dụng xác suất hỏng hóc từ Machine Learning để lựa chọn chính sách bảo trì nhằm giảm **chi phí mô phỏng**, có kiểm tra ràng buộc nguồn lực và so sánh với baseline.

Dataset dự kiến: [AI4I 2020 — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).

AI4I là dữ liệu tổng hợp; các chi phí và hiệu quả bảo trì là giả định mô phỏng cần được chủ dự án phê duyệt, không phải dữ liệu chi phí thực tế hay bằng chứng tiết kiệm tại nhà máy.

## Trạng thái

Đang khởi tạo repository và chuẩn bị nhiệm vụ tuần 1. Chưa tải dataset, chưa huấn luyện mô hình, chưa chạy tối ưu và chưa có kết quả thực nghiệm.

Hai AI làm việc trên nhánh/worktree riêng; chỉ chủ dự án phê duyệt thay đổi file chung, công thức và việc tích hợp vào `main`.

## Tài liệu

- [Lộ trình gốc: 10 giai đoạn / 5 tuần](docs/ROADMAP.md), được sao chép nguyên văn từ tài liệu chủ dự án cung cấp.
- [Quy tắc cho hai AI](AGENTS.md).
- [Đặc tả và các quyết định chờ phê duyệt](docs/PROJECT_SPEC.md).
- [Bảng nhiệm vụ](docs/TASK_BOARD.md).
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

Các thư mục chưa có sản phẩm dùng `.gitkeep`; chưa tạo module Python hay notebook giả.

## Môi trường dự kiến

Python **3.11**; máy khởi tạo đã kiểm tra được Python **3.11.9** bằng đường dẫn trực tiếp. `requirements.txt` là danh sách dependency ban đầu, **chưa phải lockfile và chưa được kiểm chứng bằng cài đặt**. Chưa có mô hình, kết quả hoặc lệnh tái lập thực nghiệm để chạy ở checkpoint này.

Mỗi AI dùng `.venv` riêng trong worktree của mình. Khi chủ dự án bắt đầu tuần 1, từ đúng worktree:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Nếu alias `py` không chạy, dùng đường dẫn Python 3.11 thật trên máy; ví dụ máy khởi tạo:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.11-64\python.exe" -m venv .venv
```

Chưa tạo venv hoặc cài package trong bước khởi tạo. Sau khi cài đặt được kiểm chứng, đề nghị chủ dự án duyệt bản dependency có version cố định để phục vụ tái lập. Demo Streamlit chỉ là tùy chọn về sau, chưa thêm dependency.

## Giới hạn nghiên cứu

Tối ưu chi phí trên nhãn validation là đánh giá chính sách mô phỏng, không chứng minh tác động nhân quả của bảo trì. Test được giữ kín đến khi khóa mô hình/chính sách. Mọi thông số ví dụ trong lộ trình vẫn là đề xuất; xem danh sách quyết định trong đặc tả.
