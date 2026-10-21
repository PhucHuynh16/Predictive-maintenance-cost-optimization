# Quy định làm việc cho Codex và Antigravity

## Phạm vi hiện tại

Checkpoint này chỉ khởi tạo repository, tài liệu, hai nhánh và worktree; chuẩn bị prompt tuần 1. Không train mô hình, chạy tối ưu, triển khai toàn bộ lộ trình hoặc tự kích hoạt AI khác. Việc chủ dự án yêu cầu tạo bộ tài liệu lần đầu là phê duyệt cho thao tác khởi tạo này, không phải phê duyệt công thức hay nhiệm vụ triển khai tiếp theo.

Đọc `docs/PROJECT_SPEC.md`, `docs/TASK_BOARD.md`, `docs/ROADMAP.md` và prompt của mình trước khi bắt đầu. Lộ trình được giữ nguyên làm tài liệu nguồn; ví dụ số trong đó không phải tham số đã được duyệt. Nếu tài liệu mâu thuẫn, ghi rõ điểm cần chủ dự án quyết định, không âm thầm sửa.

## Phân quyền file

| Chủ sở hữu | Phạm vi được sửa khi nhiệm vụ tương ứng được kích hoạt |
|---|---|
| Antigravity | `notebooks/**`, `figures/**`, `report/**`, `slides/**`; `docs/data_dictionary.md`, `docs/eda_findings.md`, `docs/project_proposal.md`, `docs/results_analysis.md`; `src/visualization.py`; `scripts/demo.py` |
| Codex | `src/**` trừ `src/visualization.py`; `tests/**`; `scripts/**` trừ `scripts/demo.py`; `results/**` trừ `.gitkeep`; `docs/problem_formulation.md`, `docs/cost_model_review.md`, `docs/experimental_protocol.md`, `docs/reproducibility.md` |
| Chung — chủ dự án phê duyệt trước | `README.md`, `AGENTS.md`, `requirements.txt`, `.gitignore`, `.gitattributes`, toàn bộ `configs/**`, `data/README.md`, `docs/ROADMAP.md`, `docs/PROJECT_SPEC.md`, `docs/TASK_BOARD.md`, `docs/WEEK1_ANTIGRAVITY.md`, `docs/WEEK1_CODEX.md`, `docs/BOOTSTRAP_HANDOFF.md`, các `.gitkeep` và mọi file chưa được phân quyền |

Antigravity phụ trách EDA, notebook, kiểm tra dữ liệu, trực quan hóa, tài liệu/báo cáo, slide và demo giao diện. Codex phụ trách data pipeline, baseline, ML, objective, constraints, optimization, unit tests và experimental runs. Antigravity đọc kết quả của Codex để vẽ hình nhưng không sửa log; Codex cung cấp yêu cầu thay đổi hình/notebook bằng đề xuất cho chủ dự án.

`data/raw/` và `data/processed/` là dữ liệu local bị ignore. Antigravity có thể tải bản raw khi nhiệm vụ dữ liệu được kích hoạt; Codex chỉ sinh bản processed bằng pipeline được giao. Không ghi đè raw hay split của AI kia. Metadata chung cần chủ dự án duyệt.

## Quy tắc bắt buộc

1. Không tự ý sửa file do AI khác phụ trách. Cần thay đổi thì nêu file, lý do và đề xuất để chủ dự án phê duyệt/giao đúng AI.
2. Không tự ý thay đổi công thức tối ưu, domain, constraint hoặc giả định kinh tế. Chỉ review bản đề xuất; chưa code cost model/tests trước khi chủ dự án duyệt công thức và ngữ nghĩa.
3. Không dùng test để tuning threshold, hyperparameter, preprocessing, calibration, feature selection, chọn thuật toán hoặc chọn kịch bản. Fit preprocessing chỉ trên train; calibration dùng train folds. Chỉ đánh giá test cuối khi mô hình/chính sách đã được khóa và chủ dự án cho phép.
4. Không tạo số liệu, log, hình kết quả, notebook output hay tuyên bố thực nghiệm giả. Ví dụ tính tay phải gắn nhãn minh họa.
5. Mọi kết quả thật phải có code, commit nguồn, config, seed, split IDs/hash, dataset hash, dependency versions, lệnh chạy, log và runtime để tái lập. Ghi cả failed/pruned/infeasible runs; không sửa log để đẹp kết quả.
6. Không tự ý merge, rebase tích hợp, push trực tiếp lên `main`, force-push hoặc xóa nhánh. Ngoại lệ chỉ là các thao tác khởi tạo main được chủ dự án yêu cầu trong nhiệm vụ bootstrap hiện tại. Sau đó việc tích hợp do chủ dự án quyết định.
7. File chung phải được chủ dự án phê duyệt trước khi thay đổi. Ghi bằng chứng duyệt trong nhiệm vụ/PR: phạm vi file, quyết định, ngày và tham chiếu chỉ dẫn; không tự điền trạng thái đã duyệt.
8. Không xóa hay ghi đè nội dung có sẵn. Không commit dữ liệu nhạy cảm, API keys, raw data hoặc artifact lớn. `.gitignore` không thay thế bước kiểm tra staged diff.
9. Chỉ sửa file nằm trong phạm vi task đang được giao; dependency chưa hoàn tất/phê duyệt thì dừng phần phụ thuộc. Không tự chuyển task sang Done khi chưa có bằng chứng nghiệm thu.
10. Trước/sau mỗi lượt: `git status --short --branch`, kiểm tra đúng worktree/branch; trước commit dùng `git diff --check` và xem `git diff --cached`. Báo cáo file, kiểm tra đã chạy/chưa chạy, commit SHA và điểm cần chủ dự án quyết định.

## Nhánh và worktree

- Antigravity: `agents/antigravity`, worktree riêng `../worktrees/antigravity` tính từ repository chính.
- Codex: `agents/codex`, worktree riêng `../worktrees/codex`.
- Hai nhánh bắt đầu từ cùng commit bootstrap trên `main`; không làm việc trực tiếp trong checkout `main`.
- Không dùng chung `.venv`; không sửa checkout/worktree của AI kia.
- Task board là file chung: AI báo cáo đề xuất trạng thái, chỉ cập nhật sau khi chủ dự án duyệt.
- Prompt tuần 1 mới được chuẩn bị, chưa gửi cho Antigravity và chưa tự bắt đầu công việc phụ thuộc.
