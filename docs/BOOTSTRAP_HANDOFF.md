# Hướng dẫn bàn giao bootstrap

Ngày: 2026-10-21 (Asia/Saigon). Phạm vi là tạo tài liệu, cấu trúc Git, nhánh/worktree và prompt; không hoàn thành toàn bộ tuần 1 hay đồ án. Báo cáo xác minh cuối có SHA và kết quả thực tế nằm cạnh repository tại `../BOOTSTRAP_VERIFICATION.md` sau khi các bước kiểm tra kết thúc.

## Đường dẫn trên máy khởi tạo

```text
Repository chính / main:
D:\Năm 3\HK1_2026\Nhập môn tối ưu hóa\baitaplon\Predictive-maintenance-cost-optimization

Antigravity / agents/antigravity:
D:\Năm 3\HK1_2026\Nhập môn tối ưu hóa\baitaplon\worktrees\antigravity

Codex / agents/codex:
D:\Năm 3\HK1_2026\Nhập môn tối ưu hóa\baitaplon\worktrees\codex
```

Hai worktree là thư mục ngang cấp với repository chính trong workspace cho phép ghi, không nằm bên trong nhau. Git worktree cần repository chính còn tồn tại; không di chuyển/xóa thủ công `.git` hoặc worktree.

## Kiểm tra thực tế sau bootstrap

Tại repository chính:

```powershell
git status --short --branch
git remote -v
git branch -vv
git worktree list --porcelain
git log --oneline --decorate -5
git ls-remote --symref origin HEAD refs/heads/main refs/heads/agents/antigravity refs/heads/agents/codex
git rev-parse main agents/antigravity agents/codex origin/main origin/agents/antigravity origin/agents/codex
```

Tiêu chí: main và hai nhánh agent cùng commit bootstrap cuối; ba refs GitHub khớp SHA local; HEAD remote là main; từng worktree đúng branch và sạch; không có merge. Báo cáo xác minh cuối ghi kết quả thật, không suy ra push thành công từ việc chỉ tạo branch local.

## Bắt đầu với Antigravity

1. Chủ động mở ứng dụng Antigravity và dùng chức năng mở thư mục/workspace để chọn **worktree Antigravity** ở trên.
2. Trong terminal của thư mục đó, chạy `git status --short --branch` và `git branch --show-current`; phải là `agents/antigravity`. Đọc `AGENTS.md`.
3. Chuẩn bị `.venv` riêng theo README khi bắt đầu; dependencies hiện chưa cài/khóa version trong bootstrap.
4. Chủ dự án gửi nội dung `docs/WEEK1_ANTIGRAVITY.md` để kích hoạt nhiệm vụ. Bootstrap chưa mở ứng dụng, gửi prompt hay xác nhận Antigravity đã nhận việc.

## Bắt đầu với Codex

1. Mở **worktree Codex đã tạo sẵn** làm thư mục làm việc của phiên Codex. Không chọn checkout main hoặc tạo thêm worktree từ trạng thái khác.
2. Trong terminal của phiên, chạy `git status --short --branch` và `git branch --show-current`; phải là `agents/codex`. Đọc `AGENTS.md`.
3. Chủ dự án gửi nội dung `docs/WEEK1_CODEX.md` để bắt đầu review; chưa triển khai cost model/tests cho đến khi duyệt công thức.
4. Dùng `.venv` riêng nếu cài môi trường theo README. Python 3.11.9 chạy bằng đường dẫn trực tiếp trên máy khởi tạo; alias `py.exe` đã gặp lỗi truy cập trong môi trường kiểm tra.

Không tự khởi chạy hai AI từ tài liệu này. Khi giao task, chủ dự án xác nhận phạm vi/approval cần thiết. Hai AI không sửa file của nhau, không tự merge/main.

## Cần chủ dự án quyết định tiếp

- A1–A6 trong spec: ngữ nghĩa, công thức/chi phí/η, constraints, baseline, algorithm/search budget, dữ liệu/split/protocol.
- Khi nào kích hoạt prompt tuần 1 và thay đổi file chung nào được duyệt.
- Việc cài môi trường/khóa dependency versions và giấy phép mã nguồn.
- Việc tích hợp nhánh và đánh giá test cuối ở các giai đoạn sau.

Lộ trình nguồn được copy nguyên văn và hash kiểm tra; ví dụ trong đó không được coi là config đã duyệt. Không copy các PDF môn học hay tài liệu ngoài scope lên repository public trong bước này.
