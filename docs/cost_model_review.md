# W1-G1-C — Thiết kế cost model và constraints để trình duyệt

Ngày: 2026-10-21 (Asia/Saigon). **Thiết kế tài liệu, chưa phải code hay quyết định A1–A6 đã duyệt.** Bằng chứng kích hoạt, xác minh workspace, nguồn commit và bảng phê duyệt nằm trong [problem formulation](problem_formulation.md). Task này chỉ tạo hai tài liệu review, không tạo file Python/test/config hoặc chạy dữ liệu.

## 1. Hai cách chấm chi phí và giả định

Theo `ROADMAP.md` II.3 và `PROJECT_SPEC.md` §4:

```text
c_obs(y,a) = C_PM*a + C_F*y*(1-η*a)
c_exp(p,a) = C_PM*a + C_F*p*(1-η*a)
```

`C_obs=Σc_obs` chấm một policy bằng nhãn validation và giả định kinh tế. `C_exp=Σc_exp` chấm bằng xác suất dự đoán; nó chỉ là kỳ vọng theo mô hình, đáng tin đến mức p biểu diễn đúng nguy cơ trước can thiệp và giả định η đúng. Không thay thế y bằng p trong objective một cách ngầm định; không coi cost observed là chi phí thực đã đo.

Tổng cost = chi phí PM cho mọi hành động + tổn thất còn lại ở hàng lỗi. Không trừ mất chi phí PM khi η=1, không chỉ tính PM trên true positive, không nhân toàn bộ cost với η. `η` được hiểu là mức giảm tổn thất kỳ vọng, không phải thao tác đổi ngẫu nhiên nhãn y hay tỷ lệ giảm recall. Công thức không mô hình hóa trì hoãn, chi phí cố định theo đợt, phụ tùng, nhiều loại lỗi, hành động gây hại hoặc tương tác giữa các hàng. Cần dữ liệu/giả định mới và phê duyệt trước khi thêm các thành phần đó.

Đề xuất miền: `C_PM,C_F` hữu hạn không âm, `η∈[0,1]`. Không điền giá trị kinh tế/đơn vị hay đặt default. Ranh giới chi phí phải tránh tính cùng thiệt hại vào cả PM và failure. AI4I là dữ liệu tổng hợp theo [UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset); bài toán này chưa có các cặp kết quả phản thực tế để suy ra η. Mọi tiết kiệm theo công thức đều là tiết kiệm mô phỏng có điều kiện.

## 2. Bảng tính tay bằng ký hiệu

**Toàn bộ bảng trong tài liệu là suy diễn ký hiệu hoặc ca minh họa tự dựng; không phải dữ liệu AI4I, kết quả chạy, hay giá trị kinh tế đã được duyệt.**

| y | a | c_obs | Giải thích |
|---:|---:|---|---|
| 0 | 0 | 0 | Không lỗi, không PM |
| 0 | 1 | C_PM | PM không tránh được tổn thất lỗi nào trong nhãn này |
| 1 | 0 | C_F | Bỏ sót lỗi |
| 1 | 1 | C_PM+(1-η)C_F | Trả PM và phần tổn thất còn lại |

| a | c_exp | Quan hệ |
|---:|---|---|
| 0 | p*C_F | Tổn thất kỳ vọng không PM |
| 1 | C_PM+(1-η)*p*C_F | PM và tổn thất kỳ vọng còn lại |

Ca ký hiệu hỗn hợp: `y=(0,1,1)`, `a=(1,0,1)` cho `M=2,P=2,TP=1`; maintenance cost `2*C_PM`, residual failure cost `(2-η)*C_F`, tổng `2*C_PM+(2-η)*C_F`. B0 trên cùng y tốn `2*C_F`; saving mô phỏng `η*C_F-2*C_PM`, có thể âm. Không giả định tối ưu luôn tốt hơn baseline.

Các đẳng thức dùng kiểm tra bằng tay sau khi được phép code:

- B0: `C_obs=C_F*P`.
- Chọn mọi hàng: `C_obs=N*C_PM+(1-η)*C_F*P`.
- `η=0`: `C_obs=C_PM*M+C_F*P`; PM không giảm tổn thất.
- `η=1`: hàng y=1,a=1 tốn đúng C_PM; `C_obs=C_PM*M+C_F*FN`.
- `C_F=0`: `C_obs=C_PM*M`; `C_PM=0` không có nghĩa là được miễn capacity.
- `p=y` theo từng hàng: C_exp=C_obs cho cùng a. `p=0/1` luôn là đầu vào hợp lệ; không clip ra khỏi biên.
- Tăng η với cùng y,a và C_F>=0 không tăng cost. Cộng cost hai phần rời nhau bằng cost toàn tập; capacity phải tính theo N toàn tập nếu đó là một batch, không cộng floor của từng phần.

## 3. Thiết kế API dự kiến — src/cost_model.py

Các chữ ký sau chỉ là đặc tả trong Markdown. Không có implementation/stub/type definition thực thi. Đề xuất các hàm thuần, không fit model, không đọc dataset, không tự nạp config, không viết log và không xem split/test. Caller chịu trách nhiệm quyền truy cập dữ liệu và provenance.

```text
CostParameters(c_pm: float, c_f: float, eta: float, unit: str)

observed_cost(
    y: BinaryVector, actions: BinaryVector, *, costs: CostParameters
) -> CostBreakdown

expected_cost(
    probabilities: ProbabilityVector, actions: BinaryVector, *, costs: CostParameters
) -> CostBreakdown
```

`BinaryVector`: mảng một chiều bool hoặc số nguyên 0/1. `ProbabilityVector`: mảng số thực một chiều hữu hạn trong `[0,1]`, cùng độ dài/order với actions. Float labels, chuỗi, mảng hai chiều và broadcast ngầm bị từ chối theo đề xuất strict API. Không tự đổi nhãn `{−1,1}` thành `{0,1}`. Caller phải lấy đúng cột probability lớp 1 theo class mapping, không mặc định cột cuối nếu thiếu kiểm tra.

`CostParameters` bất biến, mọi trường bắt buộc; unit là chuỗi không rỗng, phải thống nhất trong cả thí nghiệm. Bool không được nhận thay cho tham số số thực. Cần từ chối NaN/Inf, âm hoặc η ngoài miền. Chỉ hỗ trợ một bộ cost hằng cho toàn batch trong phiên bản đầu; không broadcast vector cost hoặc sample weights chưa được duyệt.

`CostBreakdown` đề xuất:

| Trường | Kiểu/đơn vị | Ý nghĩa |
|---|---|---|
| `cost_basis` | `observed_labels` hoặc `predicted_probabilities` | Không trộn hai loại kết quả |
| `per_observation` | vector float, đơn vị cost | Cùng thứ tự input |
| `maintenance_cost` | float, cost | C_PM*M |
| `residual_failure_cost` | float, cost | Tổng tổn thất còn lại theo y hoặc p |
| `total_cost` | float, cost | Tổng hai khoản trên |
| `cost_per_observation` | float, cost/hàng | total_cost/N, với N>0 |
| `n_observations`, `n_maintenance` | int | N và M |
| `maintenance_rate` | float `[0,1]` | M/N |
| `unit` | str | Nhận nguyên từ bộ tham số |

Không trả `feasible` từ cost function: một policy infeasible vẫn có cost hữu hạn có thể chẩn đoán. Không dùng `Inf` hoặc penalty tráo thành cost thật. Từ chối N=0, shape/order không khớp theo contract; order sai chỉ phát hiện được khi caller kiểm tra IDs, không thể suy ra từ hai mảng cùng chiều dài. Kiểm tra đầu ra hữu hạn để phát hiện overflow tổng dù từng tham số hữu hạn; không clip hay thay bằng 0. Không làm tròn cost từng hàng; tolerance kiểm thử số thực chỉ dùng so sánh số học, không làm thay threshold/capacity.

## 4. Thiết kế API dự kiến — src/constraints.py

```text
threshold_actions(probabilities: ProbabilityVector, *, threshold: float) -> BinaryVector

threshold_candidates(probabilities: ProbabilityVector) -> OrderedThresholds

capacity_limit(n_observations: int, *, budget_fraction: Decimal) -> int

evaluate_constraints(
    actions: BinaryVector, *, budget_fraction: Decimal,
    y: BinaryVector | None, recall_min: float | None
) -> ConstraintReport
```

`threshold` hữu hạn trong `[0,1]`, comparator cố định `>=` sau khi được duyệt; `threshold_candidates` trả `{0,1}∪unique(p)` theo thứ tự, không dùng y. B0 cấp trực tiếp vector toàn 0, không đi qua threshold. Đặc tả candidate thuộc constraints để kiểm chứng tập policy; orchestration/search của G7 gọi lại, không tạo thuật toán train trong module này.

Đề xuất budget fraction kiểu Decimal hữu hạn trong `[0,1]`, đọc từ biểu diễn thập phân chính xác trong config khi config được duyệt. Tính K bằng floor chính xác của `b*N`; tránh float có thể đẩy tích ngay sát số nguyên xuống sai một hành động. Caller không được tạo Decimal từ float nhị phân rồi coi là đúng số thập phân gốc. `n_observations` là int dương, không phải bool; N của constraints suy ra từ actions. Không thêm epsilon để làm candidate vi phạm thành khả thi. `recall_min=None` tắt constraint, khác với bật `recall_min=0`; nếu bật phải có y hợp lệ, cùng N, và recall_min hữu hạn trong `[0,1]`.

`ConstraintReport` đề xuất:

| Trường | Đặc tả |
|---|---|
| `n_observations`, `n_maintenance`, `capacity_limit` | N, M, K dạng int |
| `maintenance_rate`, `capacity_ok` | M/N, M<=K |
| `n_positives`, `true_positives`, `recall` | null nếu không có y; recall null nếu P=0 |
| `recall_enabled`, `recall_ok` | bool; recall_ok=null khi tắt hoặc recall không xác định |
| `constraint_violation` | Các trường `capacity_excess`, `capacity_excess_rate`, `recall_shortfall`; shortfall=null khi tắt/không xác định |
| `feasible` | bool: chỉ true nếu mọi constraint bật đều xác định và đạt |
| `status` | `FEASIBLE`, `INFEASIBLE` hoặc `UNDEFINED_CONSTRAINT` |
| `reasons` | Danh sách mã ổn định, có thể có nhiều lý do cùng lúc |

Đề xuất mã lý do: `CAPACITY_EXCEEDED`, `RECALL_BELOW_MIN`, `NO_POSITIVES_FOR_RECALL`. Khi tắt recall, P=0 không ảnh hưởng feasibility capacity; vẫn báo recall=null nếu y có mặt. Khi bật recall mà P=0, trả `UNDEFINED_CONSTRAINT`, feasible=false, shortfall=null; không nói đó là vi phạm số học 1 hoặc 0. Nếu đồng thời capacity vi phạm, giữ cả hai lý do.

Đầu vào không hợp lệ (N=0, mismatch, nhãn không nhị phân, probability ngoài miền, NaN/Inf, b/threshold sai, recall bật thiếu y) gây lỗi validation có thông điệp/trường rõ, không tạo `ConstraintReport` infeasible giả. Caller ghi run `failed` và lỗi; các report hợp lệ nhưng vi phạm được log `infeasible`; undefined ghi lý do riêng. `pruned` chỉ dùng khi thật sự bị cơ chế dừng sớm đã duyệt, không đổi nhãn run thất bại thành pruned.

Cost/constraints không tự chọn best. G7 phải lọc feasible trước khi cập nhật best-so-far; nếu chưa có thì best cost=null. Giữ cả report/cost của candidate infeasible, không xóa khỏi log. Nếu mọi candidate h đã thử bị loại, trả `NO_FEASIBLE_CANDIDATE` cùng phạm vi tìm, không tự thay B0 vào miền h,τ.

## 5. Metric và phép so sánh đề xuất — A6

Định nghĩa `TP=Σy*a`, `FP=Σ(1-y)*a`, `FN=Σy*(1-a)`, `TN=Σ(1-y)*(1-a)` để metric action không lẫn metric dự đoán xác suất. Recall action không phải tỷ lệ sự cố thật đã tránh; residual loss đã được mô phỏng bằng η riêng.

| Trường hợp | Quy ước trình duyệt |
|---|---|
| Recall, P=0 | null với reason `NO_POSITIVES`; hard constraint xử lý như §4 |
| Precision, M=0 | null với reason `NO_ACTIONS` |
| F1 | `2TP/(2TP+FP+FN)`; chỉ null nếu mẫu số bằng 0; có FN hoặc FP nhưng TP=0 thì F1=0 |
| ROC-AUC chỉ một lớp y | null với reason `SINGLE_CLASS` |
| AP khi P=0 | null với reason `NO_POSITIVES`, không phụ thuộc default thư viện |
| AP khi toàn positive | 1 theo định nghĩa AP chuẩn cho tập không rỗng; ghi rõ tập một lớp |
| Brier | mean((p-y)^2) nếu có p hợp lệ, N>0; không diễn giải riêng nó là chất lượng calibration |
| B0/B1 không có mô hình p | AUC/AP/Brier=null, reason `NO_PROBABILITY_MODEL` |
| Saving tuyệt đối | `C_B0-C_policy`, cùng tập, cùng unit/scenario; có thể âm |
| Saving tỷ lệ | Chỉ tính khi C_B0>0; nếu C_B0=0 trả null với reason `ZERO_BASELINE_COST` |
| N=0 | Reject evaluation batch; không báo cost/hàng hoặc feasibility đẹp |
| Mô hình/policy vi phạm | Vẫn báo cost/metric; loại khỏi xếp hạng feasible; không top-k sửa kết quả |

Đề xuất dùng `average_precision` thay tên PR-AUC mơ hồ, theo [định nghĩa scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Với Brier, [hướng dẫn calibration](https://scikit-learn.org/stable/modules/calibration.html) nêu score còn phản ánh phân biệt/độ bất định; cần calibration curve nếu phân tích hiệu chuẩn. Quy ước null phải được wrapper chủ động áp dụng và log reason, không để warning hoặc giá trị default khác nhau giữa baseline.

## 6. Test matrix dự kiến sau phê duyệt

Các ca này là đặc tả cho `tests/test_cost_model.py`, `tests/test_constraints.py` ở task tương lai, **chưa tạo hay chạy test**. Mọi con số p/y/a/b/τ/R ở bảng chỉ là dữ liệu minh họa cho test; không phải tham số thí nghiệm được chọn.

| ID | Ca tính tay/đầu vào minh họa | Kỳ vọng để đối chiếu |
|---|---|---|
| C01 | Bốn cặp (y,a) ở §2 | Đúng cả 4 hạng, không bỏ residual khi η<1 |
| C02 | y=(0,1,1), a=(1,0,1) | Cost=2*C_PM+(2-η)*C_F; M=2, TP=1 |
| C03 | Mọi a=0; mọi a=1 | Khớp hai đẳng thức §2 |
| C04 | η=0 và η=1 trên cùng batch | Đúng biên; η tăng không tăng cost |
| C05 | C_PM=0; C_F=0; cả hai=0 | Không chia 0; cost đúng, capacity vẫn độc lập |
| C06 | p=0 và p=1; sau đó p=y | Expected theo bảng; khi p=y trùng observed |
| C07 | C_PM>=η*C_F | Không policy nào giảm C_obs so B0; hòa có thể tồn tại |
| C08 | Chia batch thành hai phần, giữ order | Tổng component/per-row/tổng cost nhất quán; không sửa input |
| C09 | Một hoán vị chung của y,a,p | Tổng cost/constraints không đổi; per-row theo hoán vị |
| T01 | p=(0,0.5,1), τ=0 | a=(1,1,1), kể cả p=0 |
| T02 | Cùng p, τ=1 | a=(0,0,1); khác B0=(0,0,0) |
| T03 | p=(0.5,0.5,0.2), τ=0.5 | a=(1,1,0); ties không bị tách |
| T04 | p toàn 0; p toàn 1; chỉ một phần tử | Candidate endpoints hợp lệ; policy rỗng chỉ có khi miền biểu diễn được |
| T05 | p=(0,0.5,1) | T={0,0.5,1}; vector lần lượt 111,011,001; không có 000 |
| T06 | p=(0,0.5,0.5) | T={0,0.5,1}; vector 111,011,000; giữ nhóm ties |
| K01 | N=3, b=0.5 chính xác | K=1; M=1 đạt, M=2 excess=1 và rate=1/3 |
| K02 | N=1, b=0.1 chính xác | K=0; một action vi phạm, không làm tròn lên |
| K03 | b=0; b=1 | K=0; K=N; xét M tương ứng |
| K04 | N=100, b=0.29 dạng Decimal | K=29 chính xác; không thành 28 do float |
| K05 | p=(1,1,0.2), N=3, b=0.5 | K=1, mọi τ chọn ít nhất 2; h này không có ngưỡng khả thi; B0 capacity-feasible riêng |
| K06 | p=(0.8,0.8,0.2), N=3, b=0.5 | K=1; không thể chọn đúng một hàng bằng threshold; policy rỗng ở τ=1 vẫn khả thi |
| K07 | N=2, b=0.5; chia hai batch N=1 | K toàn tập=1, nhưng tổng floor từng phần=0; phải áp dụng đúng đơn vị batch |
| R01 | y=(1,1,0), a=(1,0,0), R_min=0.75 | Recall=0.5, shortfall=0.25; ghi capacity riêng |
| R02 | P=2, R_min=0.75, K=1 | Cần ceil(1.5)=2 TP>K; bất khả thi kể cả a tự do |
| R03 | y=(0,1), p=(0.9,0.8), K=1, R_min=1 | K đủ đếm TP nhưng threshold chọn top1 là negative; không có policy threshold đạt cả hai |
| R04 | y toàn 0; recall constraint tắt/bật | Tắt: capacity quyết định; bật: undefined, không feasible |
| R05 | P>0, R_min=0 và 1; recall đúng bằng ngưỡng | 0 chấp nhận mọi recall xác định; 1 cần bắt đủ; equality được chấp nhận |
| R06 | M>K đồng thời recall<R_min | Giữ cả hai violation và reasons; không cộng đơn vị khác nhau |
| V01 | N=0, mismatch, 2D, nhãn 2/−1/float | Reject input theo strict contract, không infeasible giả |
| V02 | p/τ/b/R_min ngoài miền; NaN/Inf | Reject; p=0/1 và τ=0/1 vẫn hợp lệ |
| V03 | Cost âm/NaN/Inf; η ngoài miền; unit rỗng | Reject, không auto-default |
| V04 | Recall bật mà thiếu y; y/a thứ tự sai | Thiếu y reject; caller kiểm tra ID/order trước gọi API |
| V05 | Tham số bool giả số; Decimal tạo sai từ float | Từ chối kiểu sai; parser phải giữ số thập phân gốc |
| V06 | Từng số hữu hạn nhưng tổng overflow | Lỗi số học được ghi failed, không cost=Inf được chọn |
| M01 | P=0/M=0; y một lớp | Null/reason đúng §5; không tùy tiện ép thành 0/1 |
| M02 | TP=0,FN>0 hoặc FP>0; tất cả TP=FP=FN=0 | F1 lần lượt 0 hoặc null |
| M03 | C_B0=0; saving âm; B0/B1 thiếu p | Không chia 0; giữ saving âm; probability metrics null |
| S01 | Candidate chi phí thấp nhất vi phạm; candidate khác khả thi | Best chỉ chọn feasible; vẫn giữ log candidate vi phạm |
| S02 | Mọi candidate đã thử không khả thi | Best=null, NO_FEASIBLE_CANDIDATE kèm phạm vi tìm; không tự gán B0 |
| S03 | Hai candidate cùng cost, khác M/τ | Dùng quy tắc hòa đã được A4 duyệt, không dùng test |

Test đại số/ca ký hiệu chỉ chuyển thành test số khi chủ dự án đã duyệt công thức/ngữ nghĩa và giao task code. Bộ tham số số trong unit test phải được ghi rõ là fixture kiểm thử, không được dùng làm default cấu hình thực nghiệm.

## 7. Điều kiện mở triển khai và dữ liệu tái lập

Trước cost/constraints tối thiểu cho G4: cần A1–A3 và A6 đủ cụ thể, các trường cost/unit/b/recall đã chốt, API/edge cases được chấp nhận, task triển khai được kích hoạt. B1/B2 còn cần A5 và pipeline/split đã kiểm chứng. A4 cần hoàn tất trước G7; không lấy việc duyệt A1–A3 làm lệnh train/tối ưu.

Một run thật về sau phải lưu: run/scenario/policy ID; commit nguồn sạch và phiên bản cấu hình/hash; dataset SHA-256, split IDs/hash; feature schema; dependency/Python versions; seeds tách vai trò; tham số cost/unit/b/recall; h/threshold/comparator; lệnh chạy; runtime; cost basis/components; metrics/null reasons; capacity/recall violations; candidate counts; status và lỗi. Lưu cả failed/pruned/infeasible, không chỉ best. Việc bảo vệ test nằm ở orchestration/protocol, không thể được đảm bảo chỉ từ API nhận mảng.

G4 cần cost model tối thiểu và unit tests trước khi báo cost baseline; G6 hoàn thiện sau. `configs/**`, requirements, board, spec và metadata dùng chung chỉ cập nhật sau phê duyệt phạm vi riêng. Không tạo config tạm với chi phí mặc định để vượt dependency.

## 8. Bàn giao và kiểm tra lượt review

- Đã xác minh worktree/branch/remote và status sạch trước sửa; đã đọc tài liệu bắt buộc, đối chiếu nguồn UCI và tài liệu calibration/AP chính thức (truy cập 2026-10-21).
- Đã review objective, decision variables/domain, constraints, expected/observed cost, giả định cộng một kỳ/η, ca biên, API và test matrix. Bảng A1–A6 và điểm cần điều phối nằm ở problem formulation §8–§9.
- Không tải/đọc CSV hoặc test set; không chia dữ liệu, cài dependencies, train/calibrate, chạy baseline/tối ưu; không tạo source/test/config/log/hình kết quả.
- Đã kiểm tra liên kết Markdown local, cặp code fences và whitespace của cả hai file: không có link hỏng, fence lẻ hoặc trailing whitespace. `git diff --check` trả 0; hai file mới còn untracked nên được kiểm tra nội dung riêng. Kiểm tra `git diff --no-index --check` so với NUL chỉ báo file mới khác rỗng (exit 1) và cảnh báo chuẩn hóa LF/CRLF, không có chẩn đoán lỗi whitespace. Đã xác nhận đúng hai file mới, không có thay đổi tracked/staged và bảng có 40 ca kiểm tra dự kiến.
- Unit tests và thực nghiệm chưa chạy vì task hiện tại là review; không có kết quả định lượng thực nghiệm. Hai tài liệu để ở working tree cho chủ dự án review, chưa tạo commit mới; HEAD nguồn vẫn là `053d031fecf4042c920aa08d424672a948872710`.
- Chỉ đề xuất nghiệm thu W1-G1-C; chưa cập nhật task board hay tự xác nhận Done. Không merge, rebase, push hoặc thao tác trên worktree khác. HEAD nguồn đã ghi trong problem formulation; commit bàn giao (nếu có) phải được báo bằng SHA thực tế trong chat.
