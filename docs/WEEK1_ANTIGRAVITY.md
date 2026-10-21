# Prompt Antigravity — tuần 1 (đã chuẩn bị, chưa gửi)

Chủ dự án mở worktree Antigravity, kiểm tra branch, rồi chủ động gửi prompt bên dưới. Việc có file này không có nghĩa Antigravity đã nhận việc. Task W1-G2-A khởi động phần kiểm tra nguồn/dữ liệu và chuẩn bị EDA; phần proposal W1-G1-A chờ formulation được duyệt.

## Prompt để giao việc

Bạn là Antigravity hỗ trợ đồ án cá nhân “Tối ưu chi phí bảo trì dự đoán bằng Machine Learning”. Chỉ thực hiện các phần tuần 1 được chủ dự án kích hoạt trong prompt này; không train ML hoặc chạy thuật toán tối ưu.

1. Đọc `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/ROADMAP.md`, `docs/TASK_BOARD.md` và `data/README.md`. Xác minh bạn đang ở `agents/antigravity` trong đúng worktree; kiểm tra Git status trước khi sửa.
2. Kiểm tra nguồn UCI AI4I 2020, DOI/license, phân biệt metadata nguồn với kiểm tra CSV thực tế. Khi chủ dự án cho bắt đầu nhiệm vụ dữ liệu, tải raw local bị ignore; ghi URL/ngày giờ/hash/schema và không ghi đè bản dữ liệu có sẵn. Không sửa `data/README.md` khi chưa được duyệt; đưa đề xuất metadata trong báo cáo của bạn.
3. Chuẩn bị `docs/data_dictionary.md`: tên cột thực tế, dtype, đơn vị, vai trò feature/target/ID, miền giá trị quan sát được khi có dữ liệu, missing và lý do giữ/loại. Đánh dấu `Machine failure`, năm nhãn phụ và ID; không mặc nhiên coi CSV khớp metadata.
4. Ghi kiểm tra nhãn, missing, duplicate, outlier và leakage vào `docs/eda_findings.md`. Kiểm tra quan hệ nhãn phụ với target để phát hiện bất nhất, không tự sửa nhãn. Ghi nguồn số liệu, lệnh/code và hash.
5. Chuẩn bị `notebooks/01_eda.ipynb` gồm phần nguồn, scope dữ liệu, schema, QA, imbalance, histogram/boxplot/correlation và kết luận leakage. Notebook chưa chạy thì ghi rõ chưa chạy; không điền output giả. Trước phân tích được dùng để chọn feature/mô hình, cần protocol/split do chủ dự án duyệt và development split từ Codex; phần phụ thuộc giữ ở kế hoạch nếu chưa sẵn sàng. Không mở nhãn test để định hướng phát triển.
6. Biểu đồ được tạo thật vào `figures/eda/` khi có dữ liệu được phép; lưu code, dataset/split hash, seed và môi trường. Không sửa `src/` của Codex, `results/` hoặc file chung. Đề cương/pipeline chỉ hoàn thiện sau khi formulation được chấp nhận.
7. Bàn giao danh sách file, kiểm tra thực chạy/chưa chạy, phát hiện leakage, vấn đề cần chủ dự án quyết định và đề xuất trạng thái task. Commit riêng trong branch nếu được giao, không tự merge/main.

## Nghiệm thu dự kiến

- Dictionary và QA có bằng chứng, không có kết quả giả.
- Notebook phân biệt dữ liệu được phép, metadata và kết quả kiểm tra thật; không dùng test để tuning.
- Tất cả file sửa nằm trong phạm vi Antigravity; thay đổi tài liệu chung chỉ là đề xuất.
- Không tuyên bố đã hoàn thành EDA/đề cương khi còn dependency chưa được duyệt.
