# W2-G4-C — bàn giao baseline Validation

Ngày 2026-10-23, Asia/Saigon. **READY FOR G4 REVIEW: YES** theo phạm vi giao; chờ chủ dự án review/nghiệm thu, không tự chuyển TASK_BOARD hoặc merge PR. Không coi phần cost/constraints tối thiểu này là hoàn tất G6.

## Quyền và nguồn

Chủ dự án kích hoạt “NHIỆM VỤ CHÍNH THỨC W2-G4-C — XÂY DỰNG VÀ ĐÁNH GIÁ BASELINE”, attachment `79973113-bec8-4c4f-b46c-226c89755294/Văn bản đã dán.txt`, ngày 2026-10-23. Phê duyệt riêng mã nguồn/tests được liệt kê, `configs/baselines.yaml`, `results/baseline_metrics.csv`, `results/w2_g4/**`; không cho sửa tài liệu chung khác. A3/A6 đã duyệt qua PR #10. Đã xác minh PR #8/#9/#10 merged; nhánh `codex/w2-g4-baselines` tạo từ `origin/main` tại `ff434b15a1310e139338334f26d6a17f3778d9ce`.

Commit nguồn thực sự chạy: `0779f9464f37696b1aa443d956e0318264a7417e` (mã/config/tests được commit trước chạy). Các commit sau chỉ bàn giao logs/review; `source_files_match_commit=true` trong cả hai run. Không sửa G3, requirements, README, PROJECT_SPEC, TASK_BOARD hoặc sản phẩm/worktree Antigravity.

## Kết quả thật

Train 6000; chỉ chấm Validation 2000 quan sát, P=68, K=200. Cost units mô phỏng theo A2, không phải tiền thật. B1 wear>=200 phút, B2 p>=0.5, không tuning/calibration/refit Train+Val. Dữ liệu/log số chính xác ở [CSV](../baseline_metrics.csv) và [run gốc](runs/g4_primary/run.json).

| Policy | Cost | Cost/N | Saving tuyệt đối | Saving % | M / rate | Excess / rate | Feasible |
|---|---:|---:|---:|---:|---|---|---|
| B0 | 1360 | 0.6800 | 0 | 0 | 0 / 0% | 0 / 0% | true |
| B1 | 1022 | 0.5110 | 338 | 24.852941% | 174 / 8.70% | 0 / 0% | true |
| B2 | 1169 | 0.5845 | 191 | 14.044118% | 17 / 0.85% | 0 / 0% | true |

| Policy | TP | FP | FN | TN | Precision | Recall | F1 | AP | ROC-AUC | Brier |
|---|---:|---:|---:|---:|---|---:|---:|---|---|---|
| B0 | 0 | 0 | 68 | 1932 | null / NO_PREDICTED_POSITIVES | 0 | 0 | null | null | null |
| B1 | 32 | 142 | 36 | 1790 | 0.183908 | 0.470588 | 0.264463 | null | null | null |
| B2 | 13 | 4 | 55 | 1928 | 0.764706 | 0.191176 | 0.305882 | 0.405414 | 0.879164 | 0.025295 |

AP là `average_precision_score` non-interpolated, không diện tích hình thang PR. B0/B1 không có probability model: cả AP/ROC-AUC/Brier là JSON null, reason `NO_PROBABILITY_MODEL`. CSV dùng ô trống và cột reason; JSON là nguồn kiểu null. Không dựng xác suất giả.

Runtime run gốc: B0 0.000593s; B1 0.002077s; B2 0.190940s, trong đó fit 0.159475s và predict 0.006687s. Runtime B2 gồm kiểm chứng lại preprocessing/metrics, fit đã gồm preprocessing Train. Toàn runner 9.418446s gồm kiểm tra môi trường, tests, hash, I/O và chấm baseline; không chỉ thời gian ML. Runtime không là hash tái lập bất biến. Đây là thời gian đo tại máy này, không benchmark công bằng với P chưa triển khai.

Feasible ranking theo cost: B1, B2, B0. Đây chỉ là ba baseline cố định trên Validation, không suy ra B1 tốt nhất tổng quát hoặc P tốt hơn baseline. Baseline infeasible được kiểm tra bằng fixture; không phát sinh trên dữ liệu thật lần này.

## Kiểm chứng cost, capacity và chống leakage

- Bốn ca tính tay (y,a)=(0,0),(0,1),(1,0),(1,1) lần lượt 0,1,20,5. Fixture hỗn hợp cộng 26; kiểm tra η=0/1 và tính cộng. Số thật được đối chiếu độc lập bằng `C=M+20P-16TP`: B0=1360, B1=174+1360-512=1022, B2=17+1360-208=1169. Saving luôn là C_B0-C, cho phép âm; C_B0=0 -> null/ZERO_REFERENCE_COST.
- Capacity dùng N//10 đúng floor(N/10), không floating floor hoặc top-k. Tests gồm N=1/9/10/19/20/29/2000, excess đúng đơn vị, giữ action vi phạm nguyên trạng.
- Threshold endpoints, exact ties/nextafter, candidates {0,1}∪unique(p), no-feasible và tie-break theo minimum toàn bộ/tolerance1e-9/M/τ/H đều được kiểm thử tổng hợp. Không quét threshold thật ở G4; H cụ thể chưa được lựa chọn hoặc đăng ký để search.
- N=0/input sai báo EvaluationInputError (ERROR input), tách khỏi feasibility=false. P=0 vẫn chấm cost/capacity; metrics null/reason theo A6. Tests bao gồm một lớp, không predicted positives, F1 mẫu số 0, invalid score, saving dương/âm/0.
- B2 dùng chính builder preprocessing G3, OHE Type unknown ignore + StandardScaler numeric; fit đúng một lần trên Train. Hash mảng transformed Train/Validation khớp G3. Tests có sentinel feature/categorical unseen để phát hiện scaler/encoder fit nhầm Validation, spy số lần fit, không nhận y_validation, tái lập p, ConvergenceWarning và nonfinite output phải FAILED, không retry.
- Loader chỉ đọc hai CSV development sau khi kiểm chứng hash; kiểm tra số hàng, whitelist, target binary, ordered UDI hash và disjoint Train/Validation. Không mở split_ids.json hoặc test.csv. Audit hook của run thật chỉ ghi bốn file dưới data/: raw bytes (hash, không parse), manifest, train.csv, validation.csv. Đây là rào truy cập Python cho entry point này, không phải sandbox bảo mật cho mọi công cụ ngoài tiến trình. Fixture Test sentinel bị chặn trước đọc.
- **132 PASS / 0 FAIL / 0 ERROR / 0 SKIP** trước mỗi lần chạy baseline: 89 ca G4 mới, 43 ca G3 hồi quy. [Unit log](runs/g4_primary/unit_tests.json), [JUnit](runs/g4_primary/tests.xml), stdout/stderr được lưu cả hai run. Fail injection trong fixture là test đạt, không phải thất bại baseline thật. Cổng tests thất bại sẽ ngăn mở dữ liệu/chạy baseline.

## Hash, môi trường và tái lập

| Thành phần | SHA-256 |
|---|---|
| Raw UCI | dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e |
| G3 manifest | 6dd33ba68c5a4d5d18b8db1fbe4d6f57f8dbfe667d96fe21d6d61bf62cf64522 |
| Train ordered UDI | 45f20d18308b53ace240dc55b0af55812509fe5af4bfed76494396d31536b99d |
| Validation ordered UDI | 3783ff7b44647e94aba4a9c8f15332a0a3e1b5c16c0e5e5b71d094ea7318eeb9 |
| Config G4 | 0619254fb9c1b6ec050cb369ff3eb25655214d189d5ba880698cd3c23802d684 |
| Stable result (cả hai run) | 34235eb56bff359763c820bca27fd400814c60cf8c00f798d3dc8def762eaf62 |
| B2 Validation p | 8ed7485a2d579c87384777393b665281c6fbe7e4a7bd1babc7d26f1cf18c49fb |

Python 3.11.9 AMD64 Windows, môi trường riêng `.venv` của Codex. NumPy2.4.6, pandas3.1.0, SciPy1.17.1, scikit-learn1.9.1, joblib1.6.0, PyYAML6.0.3 khớp G3; pytest9.1.1. `pip check` exit0 ở mỗi run, không cài/thay dependencies. LR đúng A6-b, n_iter=22, không cảnh báo. [Metadata](runs/g4_primary/run.json) lưu full params, versions mọi distribution, source hashes, seed42, lệnh và runtimes; không có hàng raw, ID lists, probability vectors hoặc nhãn Test public.

Lệnh đã chạy (sau commit nguồn):

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_baselines.py --run-id g4_primary --publish
.venv/Scripts/python.exe -X utf8 scripts/run_baselines.py --run-id g4_reproduce
```

Chạy lại phải dùng run-id mới, không `--publish` nếu summary đã có. Runner không overwrite artifacts/log cũ. Nếu clone mới thiếu split local: chủ dự án đã cho tái lập qua pipeline G3, đúng versions/config/seed/order, rồi đối chiếu manifest trước tiếp tục; không thử nhiều split/seed. Lần này có sẵn split nên không chạy lại splitter. G3 raw/split/model arrays vẫn chỉ local bị ignore.

[Run tái lập](runs/g4_reproduce/run.json) có cùng stable result/p/actions/metrics; tổng runtime9.763750s. Kiểm tra sau run đối chiếu đẳng thức cost, capacity, các cờ cấm và hash ở [reproducibility_check.json](reproducibility_check.json). Không chọn run có kết quả thuận lợi: giữ cả hai, CSV tổng là run gốc, runtime được báo nguyên trạng.

Tài liệu API chính thức đã đối chiếu: [LR1.9.1](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html), [Average Precision](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Cấu hình L2 dùng l1_ratio=0 theo A6-b, không truyền penalty deprecated; không thay quyết định dự án theo ví dụ thư viện.

## Lỗi, giới hạn và điều kiện trước G5

Không phát sinh lỗi baseline thật hoặc ConvergenceWarning ở hai run. Các test failure/score invalid là fixture chủ ý. LF/CRLF warning khi stage là quy tắc Git trên Windows, không sửa .gitattributes. Log được giữ nguyên, không retry solver/C/threshold.

EDA trước khóa protocol đã xem toàn nhãn; nhiệt độ phụ thuộc mạnh theo UDI. Kết quả chỉ đo nội suy cùng dữ liệu tổng hợp, không chứng minh tổng quát hóa theo thời gian/máy/nhà máy hoặc hiệu quả can thiệp/tiết kiệm tiền thật. Không gọi Test hoàn toàn chưa từng được xem xét. G4 không đọc file, transform, đánh giá hoặc chọn theo Test; không triển khai P, RF/calibration G5, G6 mở rộng, Optuna G7 hoặc sensitivity.

Trước G5: chủ dự án review/nghiệm thu G4 và merge PR; giao W3-G5-C riêng với quyền config/log và tiêu chí nghiệm thu; khóa cấu hình RF ngoài miền search và chi tiết còn thiếu thuộc A4 theo phạm vi giai đoạn. A5.6 đã chốt sigmoid/5 stratified train folds/shuffle42/ensemble=False, cần triển khai preprocessing/model đúng từng fold và tests tương ứng; dữ liệu không đáp ứng thì dừng trình lại. Không tự đổi B2 hoặc refit Train+Validation. Search H/order/budget chi tiết cần chốt trước tối ưu; Test chỉ được mở G10 sau khóa đủ thành phần và quyền riêng.
