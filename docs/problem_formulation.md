# W1-G1-C — Review mô hình hóa bài toán tối ưu

Ngày review: 2026-10-21 (Asia/Saigon). Trạng thái: **bản đề xuất trình chủ dự án; A1–A6 chưa được duyệt**.

## 1. Phạm vi và bằng chứng kích hoạt

Chỉ dẫn của chủ dự án trong chat ngày 2026-10-21: “Tôi phê duyệt A7 – Kích hoạt nhiệm vụ W1-G1-C thuộc Tuần 1”, yêu cầu review và đề xuất A1–A6, chưa triển khai cost model, train ML hoặc chạy tối ưu. Phê duyệt này kích hoạt đúng task review, không bao gồm sửa file chung, tích hợp nhánh hay kích hoạt Antigravity.

Đã xác minh trước khi làm việc:

| Mục | Kết quả thực tế |
|---|---|
| Worktree | `D:/Năm 3/HK1_2026/Nhập môn tối ưu hóa/baitaplon/worktrees/codex` |
| Branch | `agents/codex` |
| Remote fetch/push | `https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization.git` |
| HEAD nguồn | `053d031fecf4042c920aa08d424672a948872710` |
| Git status ban đầu | Sạch; theo dõi `origin/agents/codex` |

Tài liệu đã đọc: [AGENTS](../AGENTS.md), [prompt Codex](WEEK1_CODEX.md), [spec](PROJECT_SPEC.md), [task board](TASK_BOARD.md), toàn bộ [roadmap](ROADMAP.md), hướng dẫn dữ liệu và bootstrap handoff. Chỉ tạo hai file thuộc W1-G1-C: tài liệu này và [cost model review](cost_model_review.md). Mọi lựa chọn thiết kế dưới đây đều chờ duyệt, kể cả khi được ghi là khuyến nghị.

## 2. Đơn vị quan sát, dữ liệu và giới hạn diễn giải — A1/A5

Đề xuất coi mỗi hàng là một **quan sát trạng thái vận hành**, có nhãn nhị phân `y_i`, được chấm trong một kỳ giả lập. Không suy ra mỗi hàng là một máy độc lập, một ngày, một chu kỳ hay một quyết định lặp lại trên cùng máy. `N` là số hàng của tập đang đánh giá; capacity áp dụng trên chính tập đó. Tổng chi phí cộng theo hàng đòi hỏi không cộng trùng cùng một tổn thất hoặc cùng một lần bảo trì; nếu cần quản lý theo máy/thời gian phải thiết kế lại đơn vị và dữ liệu trước khi code.

Metadata [UCI AI4I](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), kiểm tra ngày review, mô tả dữ liệu tổng hợp, 10.000 hàng, 6 feature và cách sinh nhiệt độ bằng random walk. Đây là thông tin nguồn; chưa tải CSV, xác minh schema local hay kiểm tra độc lập giữa các hàng. Suy luận của review: random split có thể trộn các trạng thái gần nhau; cần review thứ tự trước khi chốt A5, không coi random split là bằng chứng dự báo tương lai.

Đầu vào dự kiến theo spec: `Type`, `Air temperature [K]`, `Process temperature [K]`, `Rotational speed [rpm]`, `Torque [Nm]`, `Tool wear [min]`. Target: `Machine failure`. Loại target, `UID`/`UDI`, `Product ID`, `TWF/HDF/PWF/OSF/RNF` khỏi feature. ID chỉ phục vụ truy vết/split; tên cột thực tế phải được nhiệm vụ dữ liệu xác nhận.

Dataset không cung cấp các cặp kết quả nếu bảo trì/không bảo trì trên cùng quan sát để xác định tác động can thiệp cho bài toán này. Không ước lượng được hiệu quả `η`, chi phí thực, thời gian báo trước lỗi hoặc tiết kiệm tiền thật từ formulation này. Nhãn lỗi quan sát không biến thành nhãn sau can thiệp khi gán `a_i=1`.

## 3. Biến quyết định và miền — A4

Trích công thức từ `ROADMAP.md`, phần II.2–II.3:

```text
x = (h, τ),     h ∈ H,     τ ∈ [0,1]
p_i(h) = xác suất lớp Machine failure = 1 từ pipeline fit trên train
a_i(h,τ) = 1[p_i(h) >= τ]
```

`h` là cấu hình ML/pipeline đã được duyệt; `H` là search space hữu hạn/hỗn hợp cần khóa. `p_i` phải hữu hạn trong `[0,1]`. Trọng số mô hình học từ train không phải các biến tự do được chọn bằng nhãn validation. `a_i` được suy ra từ policy; **không phải N biến nhị phân được chọn độc lập bằng cách nhìn y**. Seed, split và kịch bản kinh tế là điều kiện thí nghiệm, không phải biến tối ưu để chọn kết quả đẹp.

Với `h` cố định, bài toán chỉ còn tìm `τ`; cost theo `τ` là hàm bậc thang, không cần giả định khả vi/lồi. Với nhiều `h`, đây là tìm kiếm trên các pipeline học từ train, đánh giá trên validation, có rủi ro quá khớp validation khi thử nhiều cấu hình.

Đề xuất A4: dùng tối ưu `τ` ở `h` cố định làm mốc/ablation; phương pháp chính vẫn tìm `h,τ` như roadmap. Hai phạm vi phải được đặt tên riêng, không gọi tối ưu `τ` là HPO.

## 4. Objective đề xuất và điều kiện kinh tế — A1/A2

Trích nguyên công thức roadmap II.3 dưới dạng văn bản:

```text
min_(h,τ) C_obs(h,τ)
  = Σ_i [C_PM * a_i(h,τ) + C_F * y_i * (1 - η * a_i(h,τ))]
```

Thêm hậu tố `obs` để phân biệt cách chấm, không thay đổi công thức nguồn. Dùng nhãn validation để chọn policy; test chỉ được chấm sau khi khóa nghiệm và được cho phép.

| Đại lượng | Ý nghĩa đề xuất | Miền/đơn vị cần duyệt |
|---|---|---|
| `C_PM` | Chi phí cho mỗi hành động, kể cả hành động trên hàng không lỗi | Hữu hạn, `>=0`; đơn vị chi phí mô phỏng/hành động |
| `C_F` | Tổn thất đầy đủ của một hàng có lỗi khi không can thiệp | Hữu hạn, `>=0`; cùng đơn vị chi phí/sự cố |
| `η` | Phần tổn thất giả định được tránh ở hàng lỗi được chọn | Hữu hạn, `[0,1]`; không có đơn vị |
| `C_obs` | Chi phí bảo trì cộng tổn thất còn lại trên N hàng | Đơn vị chi phí mô phỏng |
| `C_obs/N` | Chi phí trung bình, chỉ với `N>0` | Chi phí mô phỏng/quan sát |

Không chọn `C_PM`, `C_F`, `η`, đơn vị tiền hoặc kịch bản số ở task này. Chi phí bảo trì và tổn thất còn lại **được cộng**: ở `y=1,a=1` vẫn có `C_PM + (1-η)C_F`. Nếu `C_PM` đã bao gồm sửa chữa/tổn thất mà `C_F` cũng tính, có nguy cơ cộng trùng; chủ dự án cần duyệt ranh giới hai khoản.

Suy ra đại số từ công thức đề xuất, đặt `M=Σa_i`, `P=Σy_i`, `TP=Σy_i*a_i`:

```text
C_obs = C_PM*M + C_F*P - η*C_F*TP
C_B0  = C_F*P
C_B0 - C_obs = η*C_F*TP - C_PM*M
C_exp = Σ_i [C_PM*a_i + C_F*p_i*(1-η*a_i)]
```

`C_obs` dùng sự kiện y quan sát nhưng vẫn là **chi phí mô phỏng**, không phải hóa đơn thực tế. `C_exp` là ước tính theo mô hình xác suất, không được thay mục tiêu validation mà không có quyết định mới. So sánh `C_exp` giữa các h có thể thưởng cho xác suất bị dự đoán thấp thay vì policy tốt; vì thế đề xuất chỉ dùng nó như chẩn đoán, ghi riêng khỏi objective.

Với xác suất đúng, không có capacity và `η*C_F>0`, lợi ích kỳ vọng của một hành động là `η*C_F*p_i-C_PM`. Ngưỡng hòa vốn là `C_PM/(η*C_F)`; đây là suy luận lý thuyết, không phải ngưỡng đã chọn, không thay tìm kiếm validation. Nếu tỷ lệ vượt 1 hoặc `η*C_F=0`, cần xử lý riêng; không chia cho 0. Nếu `C_PM>=η*C_F`, không hành động nào giảm `C_obs` so với B0; bằng nhau có thể hòa. Nếu `C_PM=C_F=0`, mọi policy bằng chi phí. Các ca suy biến là lý do phải review kịch bản trước thực nghiệm.

## 5. Constraints, ties và miền khả thi — A3

Roadmap II.4 đưa ví dụ `Σa_i <= floor(0.1N)` và tùy chọn `Recall>=R_min`. Spec §5 tổng quát thành:

```text
K = floor(b*N),     b ∈ [0,1]
M = Σa_i <= K
P > 0: recall = TP/P
Nếu bật recall constraint: recall >= R_min,   R_min ∈ [0,1]
```

`0.1` là ví dụ nguồn; chưa có b được duyệt. Đây là **capacity số hành động**, không phải giới hạn tiền. Không thay bằng penalty hay ngân sách tiền. Chi phí vẫn được tính và log cho policy vi phạm, nhưng policy đó không được chọn làm nghiệm tốt nhất khả thi.

Đề xuất báo riêng `capacity_excess=max(0,M-K)` (hành động), `capacity_excess_rate=capacity_excess/N`, `recall_shortfall=max(0,R_min-recall)` (tỷ lệ, khi bật và xác định). Không cộng lượng vi phạm khác đơn vị thành một số thiếu định nghĩa. `constraint_violation` là cấu trúc chứa các thành phần; `feasible` và danh sách lý do là trường riêng. Chi tiết trạng thái lỗi dữ liệu/recall không xác định nằm trong cost review §4.

### 5.1. Tập ngưỡng ứng viên đề xuất

Với mỗi h và vector p validation cố định, thử `T(p)={0,1} ∪ unique(p_i)`, sắp xếp và có thể bỏ lần chấm trùng vector a nhưng giữ ánh xạ ngưỡng trong log. Đây là tập **đề xuất chờ A3/A4**, chưa chạy. Nó phủ mọi vector hành động do `>=` và `τ∈[0,1]` tạo ra: nếu tồn tại giá trị p nhỏ nhất không dưới τ thì chọn giá trị đó cho cùng vector; nếu không tồn tại thì `τ=1` biểu diễn vector rỗng khi `max(p)<1`.

Giữ nguyên comparator `>=`: mọi hàng có cùng p ở ngưỡng được chọn cùng nhau. Không phá ties bằng y, ID, random, `epsilon`, top-k hoặc `nextafter`. Vì thế có thể còn capacity trống mà không thể chọn thêm một phần nhóm ties. Nếu policy cùng chi phí, đề xuất ưu tiên M nhỏ hơn, sau đó τ lớn hơn trong cùng h; giữa h dùng thứ tự cấu hình cố định được ghi trước, không dùng test. Quy tắc hòa này cũng cần A4 duyệt.

### 5.2. Biên và B0

| Tình huống | Hệ quả theo công thức nguồn | Đề xuất xử lý chờ duyệt |
|---|---|---|
| `τ=0`, kể cả p=0 | Chọn mọi hàng; M=N | Chấm capacity bình thường |
| `τ=1` | Chỉ chọn hàng p=1 | Không coi đây là B0 |
| Có p=1 và `K < count(p=1)` | Mọi τ trong miền vi phạm capacity cho h này | Báo h không có ngưỡng khả thi; không suy rộng sang mọi h |
| `max(p)<1` | `τ=1` chọn rỗng | Capacity-only có nghiệm cho h đó |
| B0 | Vector a toàn 0 do policy riêng | Luôn capacity-feasible với N>0; có thể vi phạm recall |
| N nhỏ, `b*N<1` | K=0 | Không làm tròn lên để cho phép bảo trì |
| N=0 | Cost trung bình và rates không xác định | Đề xuất từ chối tập đánh giá rỗng |
| P=0 | Recall không xác định | Báo null + lý do; không mặc định thành 0 hay 1 |

Khuyến nghị **giữ nguyên miền `x=(h,τ)`**, B0 là baseline độc lập. Nếu toàn bộ candidate đã thử không khả thi, trả `NO_FEASIBLE_CANDIDATE` với phạm vi h đã thử, không gán B0 thành nghiệm của miền này. Tìm kiếm h chưa vét hết H không chứng minh toàn bài toán vô nghiệm. Phương án khác là mở rộng policy space bằng nhánh `no_maintenance`; việc này đổi miền quyết định, cần phê duyệt riêng. Không tự thêm `τ>1` hoặc đổi `>=` sang `>`.

### 5.3. Recall và điều kiện bất khả thi

Khuyến nghị vòng đầu **chỉ dùng capacity**, báo recall như metric; bật hard recall constraint chỉ sau khi chủ dự án chọn `R_min` và duyệt cách xử lý P=0. Nếu bật với P>0, cần ít nhất `ceil(R_min*P)` hàng lỗi được chọn; `K<ceil(R_min*P)` là chứng cứ bất khả thi kể cả khi chọn a tự do. Điều kiện ngược lại chưa đủ cho threshold policy vì thứ hạng và ties có thể ngăn đạt recall trong K. Kiểm tra toàn bộ T(p) mới kết luận cho h cố định. Nếu P=0 và recall constraint bật, đề xuất trạng thái `UNDEFINED_CONSTRAINT`, không nhận làm nghiệm khả thi và không tự coi constraint được miễn.

Capacity được kiểm tra lại trên mỗi tập. Threshold đã khóa ở validation không đảm bảo capacity trên test hay dữ liệu mới; nếu vi phạm thì báo nguyên trạng, không điều chỉnh theo test. Muốn bảo đảm capacity theo batch cần một policy khác được duyệt trước.

## 6. Protocol đề xuất để duyệt A5

1. Antigravity kiểm tra nguồn/schema và rủi ro thứ tự trong task dữ liệu khi được kích hoạt. Chỉ kiểm tra toàn bộ dữ liệu ở mức integrity cần thiết để tạo split; không dùng phân bố/quan hệ feature–target của test để quyết định phương pháp. Codex chưa tải/chia dữ liệu ở lượt này.
2. Giữ đề xuất stratified train/validation/test 60/20/20, split seed 42 **có điều kiện**: phải chấp nhận phạm vi đánh giá nội suy trạng thái tổng hợp sau review phụ thuộc hàng. Nếu cần đánh giá theo thứ tự hoặc nhóm, trình một protocol thay thế trước khi chia; không suy ra thời gian/machine ID từ UID. Không thử nhiều split để chọn kết quả tốt.
3. Khóa feature list ở §2; không tự loại outlier/duplicate hoặc dùng ID làm feature. Nếu có duplicates/nhóm liên quan, quyết định cách tránh chồng lấn split trước khi phân tích phục vụ chọn mô hình. Lưu IDs, thứ tự, dataset SHA-256 và split hash.
4. Fit encoder/imputer/scaler, feature selection và model chỉ trên train. Nếu calibration được bật, mọi fit preprocessing/model trong CV phải nằm trong train-fold tương ứng, calibrator học từ dự đoán ngoài fold trong train. Không dùng validation để fit calibrator. Đây là cách áp dụng nguyên tắc tách dữ liệu fit classifier và calibration trong [hướng dẫn scikit-learn](https://scikit-learn.org/stable/modules/calibration.html).
5. Đề xuất so sánh không calibration với sigmoid calibration train-fold như một ablation được đăng ký trước; số fold, fold seed, cách xử lý train có quá ít positives phải duyệt trước fit. Validation chỉ chọn h, τ và lựa chọn calibration trong budget đã khóa. Không tự tăng số thử sau khi xem kết quả.
6. Khóa riêng `split_seed`, `model_seed`, `optimizer_seed`, `calibration_fold_seed`. Multi-seed ưu tiên giữ split cố định, thay model/optimizer seed theo danh sách duyệt trước; không chọn seed thắng. Nếu lặp split phải báo thành thiết kế riêng, không trộn hai nguồn biến thiên.
7. Validation được dùng để lựa chọn nên cost tốt nhất là ước lượng development có thiên lệch chọn; không gọi là đánh giá độc lập. Sensitivity đăng ký trước và tách đánh giá lại policy cố định với tối ưu lại. Không chọn kịch bản nhờ test.
8. Trước test: khóa pipeline đã fit, policy, comparator, threshold, cost scenarios, feature schema, metrics và provenance; xin chủ dự án cho phép đánh giá cuối. Khuyến nghị không refit trên train+validation ở lượt test đầu vì refit làm thay đổi p/capacity và cần protocol riêng. Test vi phạm hoặc không cải thiện vẫn phải báo, không quay lại tuning.

## 7. Baseline, metrics và thiết kế budget — A4/A6

| Phương pháp | Policy đề xuất | Quy tắc cần duyệt |
|---|---|---|
| B0 | a=0 độc lập với p, τ | Cùng cost/constraints; recall=0 nếu P>0 |
| B1 | `1[Tool wear >= w]`, w có đơn vị phút | Comparator chưa được roadmap chốt; đề xuất `>=`, chọn w trên validation bằng cùng cost/capacity; không chọn theo test |
| B2 | Logistic Regression, `1[p>=0.5]` | Pipeline/calibration cố định đăng ký trước; không sửa threshold khi vi phạm |
| P | Random Forest, tìm h và τ | Cùng dữ liệu/kịch bản; chỉ chọn candidate hợp lệ và khả thi |

Đề xuất candidate w cho B1: các mức wear của train và hai policy riêng all/none; số mức/cách chấm phải khóa trước xem validation. Policy all/none có mã riêng, không tạo một ngưỡng vô hạn giả. Lưu mọi candidate B1; B1 đã tune phải được mô tả là heuristic có lựa chọn validation. Nếu muốn B1 hoàn toàn cố định, chủ dự án cần chọn w cùng lý do trước chạy.

Đề xuất A4 khóa search-space bằng bảng: `n_estimators`, `max_depth`, `min_samples_leaf`; liệt kê mọi giá trị/miền và tham số giữ cố định, class weighting, calibration variant cùng quy tắc sampling. Chưa chốt giá trị hyperparameter hay budget trong review này. Chủ dự án chọn TPE chính, có/không Random Search, số lượt thử h `B_h`, danh sách seeds và giới hạn runtime trước thực nghiệm. Các số 30–50 trials/5 seeds trong roadmap không tự trở thành budget.

Với mỗi h, đề xuất quét cùng T(p) cho TPE và Random Search. Cùng `B_h` là số **attempts** kể cả failed/pruned/infeasible, cùng H, seed schedule, calibration và quy tắc dừng. Ghi cả số fit thực (kể cả calibration folds), số threshold candidate và số vector a thực chấm, thời gian fit/search/tổng. Số ngưỡng khác nhau giữa h vẫn có thể khác dù số trials bằng nhau; vì vậy không khẳng định bằng chi phí tính toán chỉ nhờ bằng trials. Nếu yêu cầu budget bằng số lần chấm policy hoặc wall-clock, phải duyệt cap và quy tắc dừng chung trước chạy. Khi bằng cost, dùng quy tắc hòa §5.1.

Metric đề xuất: tổng chi phí, chi phí/hàng, M, M/N, capacity/recall violations, feasibility, TP/FP/FN/TN, recall/precision/F1, average precision (AP), ROC-AUC, Brier, runtime và số attempts. Metric classification dùng a của policy, metric xác suất dùng p; không gán xác suất giả cho B0/B1 để tính AUC/Brier.

Đề xuất ghi `average_precision` đúng tên, thay vì ghi mơ hồ PR-AUC: [scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html) định nghĩa AP không nội suy và phân biệt với diện tích PR hình thang. Chưa đổi metric trong spec. Zero-denominator, single-class và saving tỷ lệ có mẫu số 0 theo cost review §5; mọi baseline vi phạm vẫn báo đầy đủ và tách khỏi xếp hạng feasible.

## 8. Điểm tài liệu cần chủ dự án quyết định, không sửa ngầm

| Tham chiếu | Điểm chưa thống nhất/phụ thuộc | Đề xuất trình chủ dự án |
|---|---|---|
| AGENTS phần phạm vi; tiêu đề prompt; spec A7; board W1-G1-C | Còn ghi bootstrap/chưa kích hoạt | Chỉ dẫn chat đã kích hoạt review; cập nhật ghi chú/task board sau khi duyệt, không coi toàn bộ A7 được mở |
| Roadmap II.4, IV.5 và VIII | 10%/các kịch bản số là ví dụ | Chủ dự án chọn b và kịch bản, giữ roadmap làm nguồn |
| Roadmap pipeline I.4 và checklist III.3 | Sơ đồ có tiền xử lý trước chia tập, có thể bị hiểu là fit toàn dữ liệu | Tách kiểm tra schema trước split khỏi fit preprocessing sau split; phê duyệt sửa sơ đồ khi giao đúng người |
| G2 EDA trước G3 split | EDA toàn dữ liệu có thể dùng test để lựa chọn | Duyệt A5, tạo development/test split trước EDA định hướng mô hình; điều phối task dữ liệu/pipeline qua chủ dự án |
| G4 baseline tuần 2, G6 cost tuần 3 | Không thể báo baseline cost trước hàm chấm đã kiểm thử | Theo board: đưa cost/constraints tối thiểu + tests vào W2-G4-C sau A1–A3/A6; G6 hoàn thiện sâu hơn |
| G4 Logistic Regression, G5 ML tuần 3 | B2 đã cần fit LR ở tuần 2 | Duyệt pipeline/fit LR tối thiểu trong G4; G5 phát triển RF/calibration; chưa mở task trong lượt này |
| Comparator B1 trong roadmap | “Vượt ngưỡng” chưa xác định `>` hay `>=` | Duyệt comparator và candidate w riêng trong A6 |
| Capacity và B0/τ=1 | Không luôn có vector rỗng trong miền threshold | Chọn cách giữ B0 riêng hoặc mở rộng miền bằng quyết định rõ ràng |

Các file chung có thể cần cập nhật sau: `docs/PROJECT_SPEC.md` (quyết định A1–A6), `docs/TASK_BOARD.md` (trạng thái/dependency), `configs/**` (tham số khóa), README và sơ đồ/prompt nếu cần. Đây là **đề xuất phạm vi**, chưa sửa và chưa được cấp quyền từ A7 hiện tại. Không sửa roadmap nguồn.

## 9. Gói phê duyệt A1–A6

Chủ dự án có thể duyệt từng hàng và ghi rõ phần còn treo. “Đồng ý review” không điền thay giá trị bắt buộc. Mỗi quyết định cần ngày, tham chiếu phiên bản tài liệu/commit, nội dung được chọn và phạm vi task/file được mở tiếp. Bảng dưới đây chưa phải bản ghi đã duyệt.

| ID | Khuyến nghị trình duyệt | Nội dung chủ dự án phải chốt |
|---|---|---|
| A1 | Quan sát trạng thái, mô phỏng một kỳ, cost cộng theo hàng, không khẳng định tác động thực | Xác nhận đơn vị quan sát, không cộng trùng, tên đơn vị chi phí và ranh giới PM/failure |
| A2 | Giữ objective observed theo roadmap; expected cost chỉ chẩn đoán; miền §4 | Điền `C_PM=___`, `C_F=___`, `η=___`, đơn vị `___`; bảng scenario chính/sensitivity và fixed-policy/reoptimization; không có default |
| A3 | Capacity số lượng; `>=`, τ∈[0,1], ties nguyên nhóm, T(p) đầy đủ, B0 riêng; vòng đầu recall là metric | Điền `b=___`; chọn recall off/on, nếu on `R_min=___`; duyệt N=0/P=0, violations và không có nghiệm; chốt có mở rộng miền không |
| A4 | τ-only làm mốc, h+τ là phương pháp chính; TPE, quét threshold đầy đủ; đối chứng theo budget công bằng | Chọn phạm vi chính, bảng H cụ thể, RF/pipeline cố định, calibration variants, `B_h=___`, seeds/runtime, Random Search có/không và quy tắc hòa |
| A5 | Feature whitelist, split cố định có điều kiện, train-fold calibration, validation tuning, test khóa | Chấp nhận/đổi 60/20/20 + seed 42 sau review thứ tự/nhóm; EDA scope, folds/seed, duplicate policy, calibration và quyền test cuối riêng |
| A6 | B0/B1/B2 cùng cost/constraints; không sửa policy vi phạm; AP có tên rõ; null khi metric không xác định | Comparator/candidate hoặc w cố định cho B1, LR/calibration protocol B2, metrics/edge cases và saving quy ước |

Mẫu nội dung phê duyệt bằng văn bản: `A<ID>; duyệt/điều chỉnh/chờ; lựa chọn và giá trị cụ thể; ngày; tham chiếu phiên bản; task/file mở tiếp`. Có thể duyệt ngữ nghĩa trước rồi bổ sung bảng kịch bản/search space; phần thiếu vẫn khóa việc chạy liên quan.

Sau nghiệm thu review, đề xuất chủ dự án ghi W1-G1-C “đã bàn giao, chờ nghiệm thu/phê duyệt” bằng cơ chế trạng thái do chủ dự án chọn; chưa tự chuyển Done. Task dữ liệu/proposal và task triển khai kế tiếp cần được giao riêng. Tài liệu [cost model review](cost_model_review.md) cung cấp API, test matrix và checklist kiểm chứng trước khi mở code.

---

## Phụ lục P0 — phân tích chuyển sang Scania APS (2026-10-25)

**Phần AI4I phía trên được giữ nguyên như review lịch sử.** Các nhận định “chưa duyệt/chưa triển khai” trong đó phản ánh ngày viết, không phủ nhận các phê duyệt/kết quả AI4I G1–G4 sau đó. Chủ dự án hiện phê duyệt Scania làm dataset chính, bảo tồn AI4I, và chỉ giao **Migration Impact Review P0**, chưa giao thực thi Scania G1/G2.

Quyền append phụ lục này và tạo [scania_migration_plan.md](scania_migration_plan.md) đến từ chỉ dẫn chat “PHÊ DUYỆT CHUYỂN ĐỔI DATASET – NHIỆM VỤ P0”, ngày 2026-10-25 (Asia/Saigon). Không sửa PROJECT_SPEC/TASK_BOARD/ROADMAP, code/tests/config hoặc dữ liệu. Main đã tích hợp PR #11 tại `cea27fb004fd2761c12d6a055d420c8b8c95bddb`; mọi kết quả AI4I giữ nguyên dataset/objective/provenance cũ, không tái gắn nhãn Scania.

### P0.1. Target, đơn vị và giới hạn

Nguồn dự kiến [APS Failure at Scania Trucks, UCI421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks), DOI [10.24432/C51S51](https://doi.org/10.24432/C51S51), đã đối chiếu metadata ngày 2026-10-25; **chưa tải/audit CSV**. Mapping đề xuất `pos→1`, `neg→0` phải khớp tokens thật. Neg là lỗi ngoài APS, không đồng nghĩa xe khỏe. Một hàng được chấm như một quan sát nguồn, không giả định timestamp, horizon dự báo hay xe độc lập. `a=1` là dự đoán dương/đề xuất kiểm tra APS; không chứng minh bảo trì đã tránh được lỗi.

### P0.2. Objective đã được chủ dự án phê duyệt cho Scania

```text
FP = Σ(1-y_i)*a_i; FN = Σy_i*(1-a_i)
C_APS = 10*FP + 500*FN
```

TN/TP có cost benchmark0, FP10, FN500. Đây là benchmark misclassification được nguồn mô tả, không phải hóa đơn doanh nghiệp hoặc mô hình can thiệp có η. **Không** thay objective AI4I bằng cách đặt C_PM=10,C_F=500,η=1: khi đó TP vẫn tốn10, sai công thức Scania. Biến đổi đại số đúng là `C_APS=10*M+500*P-510*TP`, với M=Σa và P=Σy. B0 toàn a0 có cost500P; saving là chênh so cùng B0/partition/cost model, có thể âm. Đề xuất tiếp tục null/reason khi mẫu số saving%=0.

Ví dụ tính tay cho test tương lai, **không phải kết quả Scania**: y=[0,1,1,0], a=[1,0,1,0] có FP1,FN1,TP1,TN1 nên cost510. Không so cost này hoặc cost Scania thật với1360/1022/1169 của AI4I như cùng objective/thang đo.

### P0.3. Decision space, capacity và dữ liệu

Đã duyệt: RF là mô hình chính; capacity tối đa10%; official Train60000 chia stratified thành48000/12000, seed42; official Test16000 giữ tới G10; missing/preprocessing Train-only; baseline B0/B1 DecisionStump/B2 LR; tests/provenance/tái lập bắt buộc.

Đề xuất cụ thể hóa Scania: `x=(h,τ)`, p lớp APS1, `a=1[p>=τ]`, τ∈[0,1], K=N//10 toàn partition, giữ exact ties/không top-k. Candidate thresholds, no-feasible, tie-break, metric null/reason và baseline infeasible cần ghi rõ phạm vi Scania trước code/chạy; không tự coi mọi chi tiết A3/A6 AI4I đã chuyển sang dataset mới. Official Test không nằm trong API split/fit hoặc EDA G1–G4. Chỉ chia official Train một lần80/20 theo source order khi audit đủ, không trộn hai file nguồn rồi chia60/20/20.

Capacity là giả định nguồn lực đồ án bổ sung vào benchmark cost, không phải constraint được UCI xác nhận cho vận hành xe tải. Các feature ẩn danh/missing cần schema/parser/imputer mới; không có cơ sở chuyển rule Tool wear>=200, Type/OHE, UDI hoặc cơ chế lỗi AI4I sang Scania. B1 stump là mô hình học trên Train, có probability score thật nếu thiết kế dùng predict_proba, khác heuristic AI4I không có probability model.

### P0.4. Chi tiết còn cần quyết định và trình tự

Các đề xuất T1–T10 trong [kế hoạch P0](scania_migration_plan.md) ghi rõ parser/hash/feature count, duplicate/conflicting-label stop gate, source-row IDs, missing toàn cột/hàng/median/indicators, full stump/LR params và comparator p=0.5, calibration/refit/weighting, metrics/feasibility, namespace/quyền và H/budget về sau. Không suy ra số predictor từ dòng “171 features” khi nguồn đồng thời mô tả171 attributes gồm class; audit mới xác nhận.

P0 đề nghị giữ nguyên mọi path/kết quả AI4I, tạo namespace Scania riêng; cập nhật file chung chỉ qua task được cấp quyền. Chủ dự án nghiệm thu P0 → giao Scania G1 để chốt formulation/protocol và G2 acquisition/audit → xử lý các điều kiện dừng → G3 split/preprocessing/tests → G4 cost/constraints tests PASS trước baseline thật. Antigravity nhận proposal/EDA/dictionary/figures Scania riêng khi được chủ dự án giao; Codex không tự sửa sản phẩm hoặc kích hoạt AI kia.

Chỉ đọc metadata không chứng minh Test hoàn toàn chưa được xem xét, dữ liệu độc lập hay đánh giá theo thời gian. Thiếu timestamp/group/horizon và nhãn neg ngoài APS phải được công khai; không tuyên bố tiết kiệm tiền thật hoặc hiệu quả can thiệp. P0 không tải/raw audit/split/fit/baseline/optimization/Test, không tạo kết quả Scania. Tiêu chí nghiệm thu, inventory hàm/file, risk/stop gates và trạng thái sẵn sàng giao G1/G2 ở [kế hoạch chi tiết](scania_migration_plan.md).
