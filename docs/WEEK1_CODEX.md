# Prompt Codex — tuần 1 (đã chuẩn bị, chưa kích hoạt)

Chủ dự án mở worktree Codex, xác minh branch, rồi gửi prompt bên dưới. Bootstrap không tự chạy task này. Phạm vi tuần 1 là review và thiết kế; không tạo cost module/unit test thực thi trước khi công thức được phê duyệt.

## Prompt để giao việc

Bạn là Codex hỗ trợ đồ án cá nhân “Tối ưu chi phí bảo trì dự đoán bằng Machine Learning”. Thực hiện W1-G1-C ở mức review tài liệu, chuẩn bị thiết kế và đề nghị chủ dự án phê duyệt.

1. Đọc `AGENTS.md`, `docs/PROJECT_SPEC.md`, `docs/TASK_BOARD.md`, `docs/ROADMAP.md`. Xác minh `agents/codex` và đúng worktree, xem Git status. Không sửa file chung hoặc file Antigravity.
2. Viết `docs/problem_formulation.md` review đơn vị quan sát, `x=(h,τ)`, domain, chính sách `a_i=1[p_i>=τ]`, objective và constraints đề xuất. Trích rõ công thức từ roadmap; đề xuất sửa phải chờ chủ dự án, không tự coi là đã duyệt.
3. Viết `docs/cost_model_review.md`: phân biệt chi phí quan sát dùng `y_i` và chi phí kỳ vọng dùng `p_i`; phân tích giả định cộng chi phí một kỳ, hiệu quả η, tính không có phản thực tế của AI4I. Không chọn `C_PM`, `C_F`, η, b hoặc đơn vị tiền khi chưa duyệt.
4. Kiểm tra miền và biên: `τ=0/1`, xác suất 0/1, ties tại threshold, B0 không bảo trì không luôn biểu diễn được bằng τ=1, ngân sách `floor(b*N)`, N nhỏ/rỗng, no positives, infeasible recall/capacity. Nêu câu hỏi cần chủ dự án quyết định, không tự đổi comparator/domain/constraint.
5. Chuẩn bị **thiết kế** module `src/cost_model.py` và `src/constraints.py` trong tài liệu review: chữ ký hàm dự kiến, kiểu input/output, validation, đơn vị, feasibility/violation và test matrix. Không tạo file Python rỗng hay code thực thi ở task review.
6. Lập bảng ví dụ tính tay bằng ký hiệu và ca biên, hoặc minh họa số ghi rõ không phải giả định được duyệt/kết quả thật. Chỉ sau khi chủ dự án phê duyệt công thức và ngữ nghĩa mới được nhận task tiếp theo để viết `src/cost_model.py`, `src/constraints.py`, `tests/test_cost_model.py`, `tests/test_constraints.py`.
7. Review protocol đề xuất: split/seed, leakage, calibration train folds, validation tuning, test giữ kín; chỉ ra phụ thuộc cost tối thiểu trước baseline G4 dù G6 hoàn thiện ở tuần 3. Không chia/tải dữ liệu, train, chạy baseline hay tối ưu ở lượt review này.
8. Bàn giao phát hiện, bản thiết kế, đề nghị A1–A6, file đã sửa và kiểm tra đã chạy/chưa chạy. Nếu cần thay spec/config/board, chỉ đề xuất để chủ dự án duyệt. Không merge hoặc push main.

## Nghiệm thu dự kiến

- Có review formulation và thiết kế cost/constraints đọc được, nêu rõ các điểm chưa chốt.
- Bảng test dự kiến kiểm tra được bằng tay và phân biệt giả định với dữ liệu.
- Chưa có giá trị kinh tế/code cost model hoặc test thực thi chưa được duyệt.
- Không đọc test để tuning, không train/chạy tối ưu, không sửa file chung.
