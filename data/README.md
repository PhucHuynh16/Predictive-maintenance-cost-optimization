# Dữ liệu — nguồn và provenance

## Nguồn dự kiến

- [AI4I 2020 Predictive Maintenance Dataset — UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset).
- DOI/citation: *AI4I 2020 Predictive Maintenance Dataset [Dataset]. (2020). UCI Machine Learning Repository.* [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C).
- Metadata UCI kiểm tra ngày 2026-10-21: synthetic, 10.000 quan sát, 6 feature, file `ai4i2020.csv`, giấy phép [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Metadata báo không missing; phải kiểm chứng trên file thật trong nhiệm vụ dữ liệu.
- **Bootstrap chưa tải hoặc phân tích CSV; chưa có hash, split hoặc kết quả kiểm tra local.**

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
