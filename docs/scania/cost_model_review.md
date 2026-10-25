# SC-G1-C — Cost model, constraints và đặc tả kiểm thử

Ngày: **2026-10-25 (Asia/Saigon)**. Đây là thiết kế tài liệu, chưa có source/tests Scania được viết hoặc chạy. Quyền và trạng thái D/P/A/L theo [decision register](decision_register.md); chỉ D04/D05 là objective/unit/capacity đã duyệt, các API/edge cases/metric conventions phía dưới thuộc **P02/P08, CHỜ DUYỆT**.

## 1. Ma trận benchmark và đại số — D04

Định nghĩa y1=pos APS, y0=neg ngoài APS; a1=dự đoán dương/đề xuất kiểm tra APS. Theo phê duyệt chủ dự án và [mô tả benchmark UCI 421](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks):

| Nhãn thật | a=0 | a=1 |
|---|---|---|
| y=0 | TN:0 | FP:10 |
| y=1 | FN:500 | TP:0 |

```text
C_APS = Σ[10*(1-y_i)*a_i + 500*y_i*(1-a_i)] = 10*FP + 500*FN
N=TP+FP+FN+TN; M=TP+FP; P=TP+FN
C_APS = 10*M + 500*P - 510*TP
C_B0 = 500*P
absolute_saving = C_B0 - C_APS = 510*TP - 10*M
```

Chỉ dùng10/500 theo benchmark, không parameter tuning/sensitivity trong G1–G4. Không cộng PM cost vào mọi a1, không thêm residual η; không thể thay bằng cost AI4I với C_PM10,C_F500,η1 vì TP khi đó vẫn tốn10. Giữ nguyên code/công thức AI4I, đề xuất hàm APS riêng khi được giao. Không chuyển cost units thành tiền thực hoặc coi TP cost0 là chứng cứ kiểm tra APS không tốn nguồn lực trong thực tế.

Nếu p là xác suất đúng, expected benchmark cost là `Σ[10*(1-p_i)*a_i+500*p_i*(1-a_i)]`, ngưỡng hòa vốn không capacity là10/510. Đây chỉ suy diễn lý thuyết; **không** thay objective observed Validation, không là threshold baseline đã duyệt hoặc bằng chứng p calibrated. API expected-cost không là deliverable bắt buộc G3/G4, chưa được giao code/run.

## 2. Ví dụ tính tay — fixture tổng hợp, không kết quả Scania

Fixture E1: N20, hai hàng dương ở vị trí1/2,18 hàng âm; K=floor20/10=2 theo mức 10%. Với batch này:

| Policy minh họa (không phải model fit) | TP | FP | FN | TN | M | C_APS | Saving | Feasible theo batch đề xuất |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| a0 mọi hàng (B0) |0|0|2|18|0|1000|0| true |
| Chọn hai hàng dương |2|0|0|18|2|0|1000| true |
| Chọn một dương, một âm |1|1|1|17|2|510|490| true |
| Chọn hai hàng âm |0|2|2|16|2|1020|-20| true |
| Chọn hai dương và một âm |2|1|0|17|3|10|990| false, excess1,rate0.05 |

Những actions minh họa nhìn y chỉ phục vụ unit tests; **không** là policy chọn bằng oracle trong thực nghiệm. Hàng cost10 vi phạm capacity không được thắng feasible ranking dù cost thấp. Số học chứng minh cost và feasibility là hai khía cạnh riêng, không sửa cost/penalty để che vi phạm.

Fixture E2: N10, P=0, một action trên hàng âm → FP1,C10,C_B0=0,saving=-10; K1 nên feasible. Saving% phải null/ZERO_REFERENCE_COST theo P08; recall null/NO_POSITIVES. Không bỏ batch P=0 khỏi cost hoặc gán recall thành0/1 tùy ý.

Fixture E3: N10, K1, p=1 trên hai hàng → mọi τ∈[0,1] chọn ít nhất hai, không threshold feasible cho h đó. B0 a0 vẫn báo riêng. N9 có K0, không làm tròn lên. N=0 bị reject theo P02, không báo cost/N hoặc rates.

## 3. Hợp đồng API đề xuất — chưa triển khai

Các tên dưới đây là đặc tả, không phải hàm hiện có. Namespace dự kiến `src/scania/`, chỉ tạo khi task code/quyền được giao.

| API dự kiến | Đầu vào/đầu ra và giới hạn |
|---|---|
| `observed_aps_cost(y, actions)` | Hai vector1D cùng N>0, binary, đúng order/IDs từ caller; trả components10FP/500FN và total. Không mặc định η, C_PM hoặc tham số economic AI4I |
| `capacity_report(actions)` | N>0,binary; N,M,K=N//10,maintenance_rate,excess/rate,feasible. Không nhận y/recall để sửa capacity |
| `actions_from_probabilities(p, tau)` | p1D finite[0,1],τfinite[0,1]; exact `>=`; không clip/round/repair/top-k |
| `threshold_candidates(p)` / `select_candidate(rows, registered_h_order)` | Quy tắc P02 tại [formulation §4–5](problem_formulation.md); chưa dùng để tune fixed baselines G4 |
| `evaluate_aps_policy(y, actions, scores=None)` | Cost/constraints/confusion/metric/saving; score là xác suất lớp1 thật hoặc absent, không fake p từ actions. Runner có baseline ID/probability capability để B0 không bị gắn scores giả |

Input contract P02/P08: reject empty/mismatch/2D/nonbinary labels hoặc actions; p ngoài[0,1]/NaN/Inf, τ ngoài miền/nonfinite; không coerce chuỗi nhãn lỗi thành0 hoặc boolean thay scalar τ. Label mapping pos/neg do parser P01, không để evaluator tự đoán token. Counts/cost dùng số nguyên đủ rộng, overflow/nonfinite result là ERROR; không chấp nhận Inf làm ứng viên thắng. Missing được phép trong X theo P05, **không** trong y/actions/p.

Caller phải xác minh sample IDs/hash/order trước truyền mảng; cùng shape không chứng minh đúng alignment. Evaluator không tự tải raw/split/Test và không biết partition chỉ từ mảng. Orchestration/guard/protocol phải ràng buộc Validation/Test boundary, không tuyên bố API metrics một mình bảo đảm không leakage.

Trạng thái đề xuất: lỗi input/run=`ERROR` hoặc `FAILED` có reason/type trong log; vi phạm dữ liệu/audit gate=`BLOCKED`; policy hợp lệ vượt K là row `INFEASIBLE` với metrics nguyên trạng, không phải parse error. No-feasible trong selection trả best=null/status riêng; không đổi failed thành pruned hay thay B0 ngầm. N=0 không được đi vào tổng hợp như một policy feasible có cost0.

## 4. Metrics và null/reason — P08

| Metric | Giá trị khi xác định | Null/reason đề xuất |
|---|---|---|
| total_cost |10FP+500FN, hai components có riêng | Không null nếu input hợp lệ; lỗi thì fail rõ |
| cost_per_observation |C/N | N=0 reject trước, không chia0 |
| maintenance_rate |M/N | N=0 reject; excess=max(0,M-K),excess_rate=excess/N; log cả M,K |
| Precision |TP/M khi M>0 | M=0:null/NO_PREDICTED_POSITIVES |
| Recall |TP/P khi P>0 | P=0:null/NO_POSITIVES |
| F1 |2TP/(P+M) khi P+M>0 | CảP/M=0:null/NO_TRUE_OR_PREDICTED_POSITIVES; chỉ một số0 thì F1=0 |
| Average Precision |`average_precision_score(y,p,pos_label=1)`, non-interpolated | Có score và P=0:null/NO_POSITIVES; P=N→1 với score hợp lệ |
| ROC-AUC |`roc_auc_score(y,p)` khi có hai lớp | Có score nhưng P=0/P=N:null/SINGLE_CLASS |
| Brier score |mean((p-y)^2) khi có score hợp lệ | Không tự null vì y một lớp; invalid p là ERROR |
| absolute_saving |C_B0-C, có thể âm/0 | Luôn có với input hợp lệ |
| saving_pct |100*(C_B0-C)/C_B0 khi C_B0>0 | C_B0=0:null/ZERO_REFERENCE_COST, vẫn báo absolute |

Nếu phương pháp không có probability model (B0), **cả AP/ROC-AUC/Brier null/NO_PROBABILITY_MODEL**, ưu tiên reason này thay việc giả p rồi áp single-class rule. B1 stump/B2 LR đề xuất có score class1 thật nên được chấm probability metrics; không áp rule B1 AI4I sang B1 Scania. B1/B2 p hợp lệ nhưng coarse/miscalibrated vẫn báo nguyên trạng; Brier không đủ để kết luận calibration tốt.

Metric classification dùng actions theo threshold đã khóa; ranking/probability metrics dùng score liên tục, không dùng actions hay `.predict` thay p. Không gọi AP là diện tích hình thang PR. Mỗi null có JSON `null` và reason, CSV ô trống + reason; không biến undefined thành0 khi tổng hợp/mean. AP/P=N convention và mọi exception ở đây là đề xuất cụ thể chờ duyệt Scania, không phải dùng defaults thư viện rồi nhận là quyết định chủ dự án.

Runtime đề xuất tách preprocessing fit/transform, estimator fit/predict, metrics và runner total (bao gồm tests/hash/I/O khi có); ghi đơn vị seconds/cách đo, machine/thread/version. Không fake0 cho fit chưa chạy; B0 không fit có thể ghi0 với reason NOT_APPLICABLE. Mọi baseline giữ row kể cả infeasible/FAILED; chỉ rank các row hợp lệ feasible theo observed Validation cost. P chưa triển khai thì không kết luận P tốt hơn baseline.

## 5. Đặc tả unit tests G4 — chưa viết/chạy

| ID | Fixture/case | Oracle/tiêu chí pass tương lai |
|---|---|---|
| C01 | Bốn cặp y/a | TN=0,FP10,FN500,TP0 chính xác; TP không bị thu10 |
| C02 | E1 và một permutation chung y/a | Confusion/10FP/500FN/total/saving đúng bảng; cost không đổi theo permutation |
| C03 | Tách cùng actions/y thành hai phần | Cost cộng được; **không** cộng floor capacity từng phần thay floor toàn batch |
| C04 | a0, a1, perfect actions; P=0/P=N | B0=500P; a1=10(N-P); perfect0; không tự suy ra feasibility |
| C05 | Saving dương/âm/0/C_B0=0 | Giữ dấu, percent đúng100*, null/reason mẫu số0; E1/E2 làm oracle |
| C06 | N=0,wrong shape,nonbinary,NaN/Inf/scores ngoài miền | Reject ERROR có reason, không tạo INFEASIBLE thay lỗi |
| K01 | N1/9/10/19/11999/12000 | K0/0/1/1/1199/1200; excess/rate/feasibility đúng biên |
| K02 | Ties/p=0/p=1/τ=0/τ=1; nextafter gần0.5 | Exact comparator/không rounding; B0 khácτ1 khi cóp1; không tách ties |
| K03 | E3 và mọi candidate infeasible | best=null/NO_FEASIBLE_CANDIDATE/count/scope; không B0 substitution hoặc kết luận toànH |
| K04 | Feasible cost cao hơn infeasible; cost ties/h_order/arrival | Chỉ chọn feasible; tie against global minimum không chaining; M/τ/H deterministic |
| M01 | M=0/P=0/P=N/TP=0 cùng score/absent score | Từng null/reason/F1zero/AP1/Brier một lớp đúng §4; no fake p B0 |
| M02 | Score khác hard actions trên fixture xếp hạng biết trước | AP/ROC-AUC/Brier dùng score; estimator tên AP đúng; không trả PR trapezoid như AP |
| B01 | Stump score0.5/leaf constant/root-only/class index | p lớp1 và policy `>=` nhất quán, depth≤1, không dựa `.predict` tie; infeasible giữ actions |
| B02 | Spy fit và sentinel Validation; LR warnings/p invalid | Chỉ Train fit, không refit/CV/calibration; invalid/convergence FAILED, log warning/no retry |
| R01 | Mismatch IDs/hash/config/version/unit gate FAIL/no-Test sentinel | Chặn trước true run; log giữ nguyên, no Test read/transform/eval, không overwrite AI4I |
| R02 | Hai run cùng fixed config/seed/source | Stable digest input/output khớp ngoài timestamp/runtime; giữ cả failed/infeasible; không lựa run tốt nhất |

Đây là **16 nhóm test được thiết kế**, không phải 16 test PASS. Mỗi nhóm có thể thành nhiều test cases khi được giao; không dùng unit fixtures để tạo số liệu thực nghiệm. Phần data/split/preprocessing G3 có test matrix riêng ở [protocol §6](experimental_protocol.md). Cổng bắt buộc đề xuất: cost/constraints/input/metrics/leakage tests đạt **trước** chạy baseline Validation thật ở G4.

## 6. Provenance và điều kiện dừng

Mỗi run thật về sau cần dataset/protocol/cost-model IDs, source/config hashes/commit, ordered Train/Validation IDs hashes, schema/outputfeature digest, full params/seeds/versions/command/runtime/hardware, metrics/null reasons/cost components/M/K/excess/status/warnings và reproducibility log. Raw/IDs chi tiết/model lớn local ignored. G1 chưa tạo run/config/log data hoặc CSV Scania.

Trước code/run cần P02/P08 và params/missing/split liên quan được phê duyệt, audit findings được giải quyết, task/quyền riêng; lỗi formula/constraint/tests thì dừng true runs. Nếu có X duplicates/label conflicts/schema/missing chưa có contract thì dừng trước split/fit theo P03/P05; không sửa y/raw/drop rows hoặc đổi ratio/seed để vượt gate. Baseline infeasible không phải lý do tự thay τ hoặc adding top-k. Test bị xem ngoài scope phải báo exposure, không che bằng đổi split.

**READY FOR SCANIA G1 REVIEW: YES** cho phần cost/tests specification, chưa nghiệm thu hoặc mở code G3/G4. Không chạy test/model trong SC-G1-C. Nguồn API tham khảo metric: [AP](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), [Brier](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html); các convention cụ thể vẫn phải được chủ dự án duyệt, không do tài liệu API tự cấp quyền.
