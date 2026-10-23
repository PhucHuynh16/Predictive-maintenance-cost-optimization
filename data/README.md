# Dữ liệu — nguồn và provenance

## Nguồn dữ liệu

- [AI4I 2020 Predictive Maintenance Dataset — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).
- DOI/citation: *AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository.* [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C).
- Metadata UCI kiểm tra ngày 2026-10-21: synthetic, 10.000 quan sát, 6 feature, file `ai4i2020.csv`, giấy phép [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Metadata báo không missing; phải kiểm chứng trên file thật trong nhiệm vụ dữ liệu.
- Ở thời điểm bootstrap chưa có CSV/hash; trạng thái hiện hành sau W1-G2-A được ghi bên dưới. Chưa có split chính thức.

## Provenance W1 đã đối chiếu ngày 2026-10-23

Antigravity đã tải raw và kiểm tra local ngày **2026-10-21**. Sản phẩm W1-G2-A đã merge qua [PR #5](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization/pull/5), có trên `main` tại `d6d0bb95520cb46ccf4888cbd8aa86bf2d7b212f`.

| Metadata | Giá trị / nguồn chứng cứ |
|---|---|
| URL tải được báo cáo | `https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip` — [EDA findings §1](../docs/eda_findings.md) |
| Thời điểm tải được báo cáo | 2026-10-21 07:31:29 UTC = 14:31:29 Asia/Saigon |
| CSV local | `data/raw/ai4i2020.csv`; 522.048 bytes |
| SHA-256 CSV | `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e` |
| Bằng chứng CSV | Hash/kích thước khớp giữa report, dictionary và output đã lưu ở cell `execution_count=2` của [notebook](../notebooks/01_eda.ipynb) |
| Schema/missing | Output cell 3: 10.000 hàng, 14 cột, 0 null; gồm 6 features, 2 ID, target và 5 nhãn phụ |
| Nhận diện phiên bản | Nguồn không nêu số phiên bản riêng của bản tải; ghi DOI và SHA-256 để nhận diện bytes |

Đây là metadata **đã đối chiếu giữa các sản phẩm đã merge**, không phải lần tái tải/tái hash raw độc lập của Codex. Notebook so sánh hash với hằng số được ghi trong code; không phải checksum có chữ ký do UCI công bố. Không chuyển nhận định “khớp bản phát hành UCI” trong báo cáo thành bằng chứng xác thực độc lập chưa có. Codex không có raw local trong worktree này, chưa chạy lại schema/missing/duplicates; không đọc/sửa worktree Antigravity.

Raw CSV/ZIP vẫn là dữ liệu local của Antigravity, không được commit. Đã kiểm tra `git ls-tree -r --name-only origin/main data` chỉ có `data/README.md`; quy tắc ignore áp dụng cho `data/raw/ai4i2020.csv`. Không chép dữ liệu sang GitHub hoặc sinh split trong nhiệm vụ checkpoint.

EDA đã xem toàn bộ nhãn; phép đếm duplicate sau bỏ ID vẫn chứa target/nhãn phụ, chưa xác minh riêng sáu features. [Review A5](../docs/experimental_protocol.md) trình giới hạn exposure, phụ thuộc UDI và chính sách kiểm tra duplicate trước khi được giao G3. Không gọi test tương lai là hoàn toàn chưa bị xem xét.

## Hướng dẫn khi nhiệm vụ dữ liệu được chủ dự án kích hoạt

1. Mở trang UCI, dùng Download, giải nén vào `data/raw/ai4i2020.csv`. Không tải từ mirror chưa xác minh; không ghi đè raw có sẵn.
2. Ghi URL tải thực tế/DOI, ngày giờ và múi giờ, tên file, SHA-256, số hàng/cột thực đọc được, schema và phiên bản/citation/license. Nếu nguồn không có số phiên bản, ghi rõ không công bố; nhận diện bản tải bằng hash.
3. Đề xuất bổ sung metadata vào tài liệu chung này để chủ dự án duyệt; báo kết quả chi tiết trong `docs/eda_findings.md` thuộc Antigravity. Không tự ghi là đã tải nếu mới xem metadata.
4. Kiểm tra nhãn `Machine failure`, missing, duplicates và leakage; xác minh `UID`/`UDI`, `Product ID`, `TWF/HDF/PWF/OSF/RNF`. Nhãn phụ/ID không thuộc input baseline. Không dựa vào thiếu/trùng/outlier để sửa dữ liệu ngầm.
5. Trước EDA dùng để chọn feature/mô hình, chốt scope train/validation và split theo protocol đã duyệt; giữ test kín. Không dùng toàn bộ nhãn test cho quyết định phát triển.
6. Codex tạo bản processed/split bằng pipeline có seed và metadata khi được giao; raw được giữ nguyên.

Ví dụ lệnh hash PowerShell sau khi có file:

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath .\data\raw\ai4i2020.csv
```

Toàn bộ dữ liệu local dưới `data/` ngoài README bị `.gitignore` bỏ qua. Chỉ tài liệu nguồn/citation được commit trong bootstrap; chia sẻ lại dữ liệu cần kiểm tra điều kiện giấy phép và chủ dự án chấp nhận phạm vi public.

## Giới hạn

AI4I không có chi phí bảo trì thực tế, dữ liệu can thiệp hoặc horizon dự báo lỗi được xác nhận cho bài toán này. `C_PM`, `C_F`, `η` và tiết kiệm là giả định/kết quả mô phỏng; chưa có giá trị được duyệt. Giấy phép dataset không thay cho giấy phép mã nguồn repository.
