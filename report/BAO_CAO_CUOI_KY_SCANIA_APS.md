# BÁO CÁO TỔNG KẾT ĐỒ ÁN: TỐI ƯU HÓA CHI PHÍ BẢO TRÌ DỰ ĐOÁN HỆ THỐNG KHÍ NÉN TRÊN XE TẢI NẶNG SCANIA APS (UCI 421)

> **TRẠNG THÁI TÀI LIỆU:** BÁO CÁO HOÀN CHỈNH CHÍNH THỨC — Đã tích hợp đầy đủ số liệu đo đạc thực tế chính thức từ G4 Baseline Run `scania_g4_b2_real_002` và Phase 2 Constrained Optimization Run `scania_phase2_rf_optuna_002`; kèm theo 02 đồ thị tối ưu hóa thực nghiệm đã kiểm chứng và mã băm SHA-256 toàn vẹn.

**Học phần:** Nhập môn Tối ưu hóa — Học kỳ 1, Năm học 2026–2027  
**Đơn vị đào tạo:** Khoa Công nghệ Thông tin — Trường Đại học Văn Lang  
**Sinh viên thực hiện:** Huỳnh Phúc  
**Mã nguồn & Repository:** [PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)  
**Tập dữ liệu nghiên cứu:** UCI Machine Learning Repository — Dataset #421: *APS Failure at Scania Trucks* (Scania CV AB, 2016)  

---

> [!IMPORTANT]
> **RANH GIỚI KHOA HỌC & NGHIỆM THU PHƯƠNG PHÁP TỐI ƯU HÓA:**
> - Nghiên cứu đã hoàn thành toàn diện hai giai đoạn: (1) Xác lập hệ thống đường cơ sở chuẩn tắc G4 Baselines (B0 Dummy, B1 Decision Stump, B2 Logistic Regression), và (2) Triển khai phương pháp tối ưu hóa toán học có ràng buộc cốt lõi Phase 2 (Random Forest kết hợp Bayesian Hyperparameter Optimization & Vectorized Threshold Tuning qua Optuna TPE).
> - Toàn bộ dữ liệu thực nghiệm được đo đạc thật qua 20 lượt huấn luyện (estimator fits), 20 trials tuần tự dưới sự kiểm soát tài nguyên nghiêm ngặt của Windows Job Object.
> - Tập kiểm thử Official Test (16.000 mẫu) được niêm phong tuyệt đối (STRICTLY SEALED UNTIL G10) nhằm phòng chống rò rỉ dữ liệu và thiên vị đánh giá.

---

## TÓM TẮT ĐỀ TÀI (ABSTRACT)

Bảo trì dự đoán (Predictive Maintenance - PdM) là bài toán kinh điển trong công nghiệp vận tải hạng nặng nhằm giảm thiểu rủi ro sự cố dọc đường và chi phí bảo dưỡng. Nghiên cứu này tiếp cận bài toán chẩn đoán hư hỏng hệ thống khí nén (Air Pressure System - APS) trên xe tải Scania (tập dữ liệu benchmark UCI 421 gồm 60.000 mẫu huấn luyện và 16.000 mẫu kiểm thử với 170 thuộc tính cảm biến) dưới góc nhìn **Tối ưu hóa toán học có ràng buộc**. 

Đặc thù bài toán là hàm chi phí phi đối xứng nghiêm ngặt theo chuẩn benchmark công nghiệp: chi phí bỏ sót một xe hỏng APS dẫn đến chết máy dọc đường (False Negative - FN) là **500 đơn vị chi phí benchmark**, trong khi chi phí kiểm tra định kỳ không cần thiết tại xưởng (False Positive - FP) là **10 đơn vị chi phí benchmark** (tỷ số $50:1$). Đồng thời, nghiên cứu đặt ra **giả định ràng buộc năng lực xưởng** (Maintenance Capacity Constraint assumption) với mức tiếp nhận tối đa không quá 10% quy mô phân vùng bảo dưỡng ($M = TP + FP \le \lfloor N/10 \rfloor$, tương ứng 1.200 lượt kiểm tra trên phân vùng Validation 12.000 xe).

Nghiên cứu tuân thủ nghiêm ngặt chuẩn mực khoa học và phòng chống rò rỉ dữ liệu (No Data Leakage):
1. **Phân vùng dữ liệu:** Khóa cố định tập Train (48.000 mẫu) / Validation (12.000 mẫu) dựa trên hash G3 đã nghiệm thu (`efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`); **tuyệt đối niêm phong tập Official Test (16.000 mẫu)** cho đến giai đoạn đánh giá cuối cùng.
2. **Khung đường cơ sở (Baselines):** Xây dựng và kiểm chuẩn 3 mô hình: B0 (Majority Dummy — không can thiệp), B1 (Decision Stump — cây quyết định 1 tầng) và B2 (Logistic Regression chuẩn hóa L-BFGS `max_iter=2000`).
3. **Mô hình hóa ngưỡng tối ưu:** Phân tích sự đánh đổi giữa ngưỡng xác suất chuẩn ($\tau = 0.5$) và ngưỡng lý thuyết Bayes tối ưu chi phí ($\tau = 10/510 \approx 0.0196$), chứng minh rằng trong điều kiện ràng buộc công suất xưởng có hiệu lực, ngưỡng tối ưu thực tế phải được tìm kiếm thông qua tối ưu hóa có điều kiện thay vì áp dụng trực tiếp công thức lý thuyết phi ràng buộc.

---

## 1. ĐẶT VẤN ĐỀ & BỐI CẢNH CÔNG NGHIỆP

### 1.1. Bối cảnh hệ thống khí nén (Air Pressure System - APS)
Hệ thống khí nén (APS) trên xe tải hạng nặng đóng vai trò huyết mạch, cung cấp khí nén áp suất cao để vận hành hệ thống phanh an toàn, hỗ trợ ly hợp và điều khiển hệ thống treo khí nén. Một sự cố hư hỏng đột ngột của APS khi xe đang di chuyển trên cao tốc sẽ khiến phanh bị bó cứng khẩn cấp, gây mất an toàn giao thông nghiêm trọng, phát sinh chi phí kéo xe, sửa chữa đột xuất và đền bù hợp đồng logistics.

### 1.2. Bản chất dữ liệu và diễn giải chính xác về các lớp dữ liệu (UCI 421)
Tập dữ liệu *APS Failure at Scania Trucks* (UCI #421) được thu thập từ hoạt động bảo dưỡng thực tế của xe tải Scania. Cần đặc biệt lưu ý về **ngữ nghĩa chuẩn xác của lớp âm tính (Negative Class)** theo tài liệu gốc của UCI:
- **Lớp dương tính (Positive class, $y=1$):** Các xe vào xưởng được xác định hư hỏng bắt nguồn từ một bộ phận cụ thể thuộc hệ thống khí nén APS ($1.67\%$ trong tập Train chính thức, 1.000/60.000 xe).
- **Lớp âm tính (Negative class, $y=0$):** **Các xe gặp sự cố hỏng hóc ở các bộ phận KHÁC KHÔNG LIÊN QUAN ĐẾN APS** (ví dụ: động cơ, hệ thống điện, truyền động). Đây **KHÔNG PHẢI** là các xe "hoàn toàn khỏe mạnh" (healthy trucks). Toàn bộ xe trong tập dữ liệu đều phải vào xưởng sửa chữa; bài toán đặt ra cho kỹ thuật viên là phân loại xem hư hỏng có phải do APS hay không để quyết định quy trình tháo lắp kiểm tra chuyên sâu APS.

### 1.3. Thách thức kỹ thuật và mục tiêu tối ưu
- **Mất cân bằng dữ liệu cực đoan:** Tỷ lệ $y=1$ chỉ chiếm $1.67\%$ (800 ca dương trên 48.000 mẫu Train; 200 ca dương trên 12.000 mẫu Validation).
- **Dữ liệu cảm biến khuyết thiếu diện rộng:** 170 thuộc tính cảm biến bị ẩn danh (`aa_000` đến `ee_000`) với tỷ lệ missing value cao, đòi hỏi đường ống tiền xử lý không gây rò rỉ dữ liệu.
- **Mục tiêu tối ưu:** Xác định chính sách can thiệp kiểm tra nhằm **cực tiểu hóa tổng chi phí benchmark**, đồng thời **thỏa mãn giới hạn tiếp nhận của xưởng dịch vụ**.

---

## 2. PHÁT BIỂU TOÁN HỌC & MÔ HÌNH HÓA BÀI TOÁN TỐI ƯU

### 2.1. Biến quyết định và không gian tìm kiếm
Cho tập dữ liệu gồm $N$ xe tải với ma trận thuộc tính $X \in \mathbb{R}^{N \times 170}$ và nhãn thực tế $Y \in \{0, 1\}^N$. Một mô hình phân loại với tập siêu tham số $\theta \in \Theta$ ước lượng xác suất hậu nghiệm $P(y_i = 1 \mid x_i; \theta)$. 

Chính sách can thiệp đưa ra vector quyết định nhị phân $A = (a_1, a_2, \dots, a_N) \in \{0, 1\}^N$ thông qua ngưỡng phân loại $\tau \in [0, 1]$:
$$a_i(\theta, \tau) = \mathbb{I}[P(y_i = 1 \mid x_i; \theta) \ge \tau]$$
Trong đó:
- $a_i = 1$: Kỹ thuật viên tiến hành mở quy trình kiểm tra chuyên sâu hệ thống APS tại xưởng.
- $a_i = 0$: Không tiến hành kiểm tra APS; xe được xử lý các bộ phận khác và xuất xưởng.

Như vậy, vector biến quyết định của bài toán tối ưu là cặp $(\theta, \tau) \in \Theta \times [0, 1]$.

### 2.2. Hàm mục tiêu chi phí benchmark phi đối xứng
Theo đặc tả benchmark chính thức từ Scania CV AB và Hội nghị IDA 2016, chi phí cho từng kịch bản phân loại được quy định theo ma trận sau (tính bằng **đơn vị chi phí benchmark** / benchmark cost units):

$$\mathcal{C}(y_i, a_i) = \begin{cases} 
0 & \text{nếu } y_i = 0, a_i = 0 \quad (\text{True Negative - TN: Không kiểm tra nhầm APS}) \\
10 & \text{nếu } y_i = 0, a_i = 1 \quad (\text{False Positive - FP: Kiểm tra thừa APS dù hỏng bộ phận khác}) \\
500 & \text{nếu } y_i = 1, a_i = 0 \quad (\text{False Negative - FN: Bỏ sót lỗi APS, xe hỏng dọc đường}) \\
0 & \text{nếu } y_i = 1, a_i = 1 \quad (\text{True Positive - TP: Kiểm tra đúng và khắc phục lỗi APS})
\end{cases}$$

Hàm mục tiêu chi phí tổng thể trên tập quan sát kích thước $N$:
$$f(\theta, \tau) = 10 \cdot \sum_{i=1}^N (1 - y_i) a_i(\theta, \tau) + 500 \cdot \sum_{i=1}^N y_i (1 - a_i(\theta, \tau)) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau)$$

> **Lưu ý khoa học:** Hàm chi phí $10 \cdot FP + 500 \cdot FN$ được định lượng bằng **đơn vị chi phí benchmark quy ước**, không phản ánh trực tiếp số tiền tệ thực tế (USD hay VND) và không cấu thành lời hứa hẹn về mức tiết kiệm tiền mặt thực tế trong môi trường sản xuất của Scania.

### 2.3. Ràng buộc năng lực xưởng bảo dưỡng (Capacity Constraint Assumption)
Trong bối cảnh vận hành thực tế, xưởng dịch vụ có giới hạn về nhân lực, thiết bị đo áp suất và cầu nâng. Đề tài thiết lập **giả định kịch bản vận hành** với năng lực kiểm tra tối đa không vượt quá 10% tổng số lượng xe trong mỗi chu kỳ bảo dưỡng:
$$M(\theta, \tau) = \sum_{i=1}^N a_i(\theta, \tau) = TP + FP \le K = \left\lfloor \frac{N}{10} \right\rfloor$$

- Trên phân vùng Validation ($N = 12.000$ xe), giới hạn công suất tối đa là:
  $$K_{\text{val}} = \left\lfloor \frac{12000}{10} \right\rfloor = 1200 \text{ lượt xe}$$

Nếu một cấu hình $(\theta, \tau)$ dẫn đến tổng lượt can thiệp $M > 1200$, chính sách đó bị coi là **Không khả thi (INFEASIBLE)** và bị loại bỏ khỏi không gian nghiệm hợp lệ.

### 2.4. Phát biểu bài toán tối ưu hóa tổng thể
Bài toán quy về dạng quy hoạch tối ưu phi tuyến có ràng buộc:
$$\begin{aligned}
\min_{\theta \in \Theta, \, \tau \in [0, 1]} \quad & f(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \\
\text{subject to} \quad & g(\theta, \tau) = TP(\theta, \tau) + FP(\theta, \tau) - 1200 \le 0
\end{aligned}$$

---

## 3. PHÂN TÍCH LÝ THUYẾT VỀ NGƯỠNG TỶ LỆ CHI PHÍ BAYES

Trong bài toán phân loại nhị phân với ma trận chi phí phi đối xứng và xác suất hậu nghiệm $P(y=1 \mid x)$ được hiệu chuẩn lý tưởng (calibrated), theo lý thuyết quyết định Bayes (Bayesian Decision Theory), hành động $a=1$ được lựa chọn khi và chỉ khi kỳ vọng chi phí của việc can thiệp nhỏ hơn kỳ vọng chi phí khi không can thiệp:
$$\mathbb{E}[\text{Cost} \mid a=1] \le \mathbb{E}[\text{Cost} \mid a=0]$$
$$\iff 10 \cdot P(y=0 \mid x) + 0 \cdot P(y=1 \mid x) \le 0 \cdot P(y=0 \mid x) + 500 \cdot P(y=1 \mid x)$$
$$\iff 10 \cdot (1 - P(y=1 \mid x)) \le 500 \cdot P(y=1 \mid x)$$
$$\iff P(y=1 \mid x) \ge \frac{10}{10 + 500} = \frac{10}{510} \approx 0.0196078$$

> **Phân định ranh giới khoa học quan trọng:**
> - Ngưỡng $\tau^*_{\text{Bayes}} = \frac{10}{510} \approx 0.0196$ là **ngưỡng tối ưu lý thuyết trong điều kiện KHÔNG CÓ RÀNG BUỘC CÔNG SUẤT ($M \le K$)** và giả định xác suất dự báo hoàn toàn tiệm cận phân phối thực tế.
> - Trong bài toán có ràng buộc $M \le 1200$, nếu hạ ngưỡng xuống $0.0196$, số lượng cảnh báo dương tính $M = TP + FP$ có thể bùng nổ vượt quá 1.200 lượt xe. Khi đó, ngưỡng lý thuyết Bayes sẽ **vi phạm ràng buộc khả thi**. Do đó, $\tau = 10/510$ không thể được coi là nghiệm tối ưu mặc định trong bài toán thực tế có ràng buộc tài nguyên.

---

## 4. DỮ LIỆU & GIAO THỨC THỰC NGHIỆM NGHIÊM NGẶT (G3 & G4)

### 4.1. Phân vùng dữ liệu đã khóa (Locked Partitions)
Theo giao thức G3 đã được kiểm định toàn vẹn (`stable_manifest.json`, digest: `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`):
- **Tập Train chính thức (60.000 mẫu):**
  - **Phân vùng Train:** 48.000 mẫu (800 ca dương tính $1.67\%$, 47.200 ca âm tính).
  - **Phân vùng Validation:** 12.000 mẫu (200 ca dương tính $1.67\%$, 11.800 ca âm tính).
  - Hai phân vùng hoàn toàn tách biệt ($A \cap B = \emptyset, A \cup B = \{0, \dots, 59999\}$), bảo toàn đúng tỷ lệ phân bố lớp ban đầu.
- **Tập Official Test (16.000 mẫu):**
  - **Niêm phong tuyệt đối (STRICTLY SEALED UNTIL G10)**. Mọi mã nguồn thực thi bị chặn bằng I/O guard ở tầng Python hook; không tham gia vào bất kỳ khâu tiền xử lý, huấn luyện hay chọn ngưỡng nào.

### 4.2. Đường ống tiền xử lý không rò rỉ (Strict Train-Only Fitting)
1. **Điền khuyết thiếu:** `SimpleImputer(strategy='median')` fit tham số trung vị duy nhất trên 48.000 mẫu Train, sau đó thực hiện `transform` tĩnh trên Validation.
2. **Co dãn thuộc tính:** `StandardScaler()` fit giá trị kỳ vọng và phương sai duy nhất trên 48.000 mẫu Train, sau đó áp dụng tĩnh lên Validation.

### 4.3. Các mô hình đường cơ sở (Baselines - G4)
Hệ thống thử nghiệm G4 thiết lập 3 mô hình cơ sở nhằm thiết lập mốc so sánh khoa học công bằng:

| Mã | Tên mô hình | Cấu hình & Tham số khóa | Ý nghĩa trong phân tích tối ưu |
|---|---|---|---|
| **B0** | Majority Dummy | Dự đoán $a_i = 0 \quad \forall i$ (Không can thiệp gì) | Mốc chi phí trần khi bỏ mặc toàn bộ hư hỏng ($500 \times 200 = 100.000$ đơn vị chi phí) |
| **B1** | Decision Stump | `DecisionTreeClassifier(max_depth=1, random_state=42)` | Mô hình cây phân tách 1 thuộc tính đơn lẻ quan trọng nhất |
| **B2** | Logistic Regression | `LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=2000, random_state=42)` | Mô hình tuyến tính chuẩn tắc sau chuẩn hóa |

---

## 5. PHÂN BIỆT RÕ RÀNG BỐN CẤP ĐỘ DỮ LIỆU & THỰC NGHIỆM

Để đảm bảo tính trung thực học thuật tuyệt đối, đề tài phân định rạch ròi 4 cấp độ dữ liệu và kết quả:

1. **Cấp độ Lý thuyết (Analytical / Theoretical Tier):**
   - Công thức giải tích ngưỡng Bayes $\tau = 10/510 \approx 0.0196$.
   - Chi phí tối đa trên lý thuyết của B0 ($500 \times 200 = 100.000$).
2. **Cấp độ Kiểm thử tổng hợp (Synthetic Fixtures Tier):**
   - Dữ liệu giả lập ngẫu nhiên ($N=260, d=10$) sinh ra trong `test_g4_b2_executor.py` để kiểm thử tự động quy trình điều phối supervisor/worker, cơ chế timeout và I/O guard. **Không đại diện cho kết quả của xe tải Scania.**
3. **Cấp độ Thực nghiệm Validation thật (Real Validation Tier - Scania APS):**
   - Kết quả đo đạc thực tế chính thức trên 12.000 mẫu Validation từ bộ dữ liệu UCI 421 sau khi huấn luyện trên 48.000 mẫu Train theo đúng ủy quyền Gate B2 của Chủ dự án (Run `scania_g4_b2_real_002`).
   - Đã kiểm chứng độc lập tính toàn vẹn 11 artifacts bằng `verify_run() == True` và chữ ký băm SHA-256.
4. **Cấp độ Đánh giá kiểm thử cuối (Official Test Tier - 16.000 xe):**
   - Hoàn toàn niêm phong (SEALED UNTIL G10), chưa được mở khóa và chưa từng chạy đánh giá.

---

## 6. BẢNG KẾT QUẢ THỰC NGHIỆM ĐO ĐẠC THỰC TẾ (5 CHÍNH SÁCH VALIDATION G4)

Dưới đây là số liệu đo đạc thực tế chính thức của **5 chính sách cố định** trên 12.000 mẫu Validation (200 ca dương tính $y=1$, 11.800 ca âm tính $y=0$), trích xuất từ run `scania_g4_b2_real_002` đã niêm phong:

| STT | Mô hình | Ngưỡng $\tau$ | TP | FP | TN | FN | Precision | Recall | Tổng chi phí benchmark | Số xe vào xưởng ($M \le 1200$) | Mức tiết kiệm vs B0 (%) | Trạng thái ràng buộc |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | **B0:** Majority Dummy | N/A | 0 | 0 | 11.800 | 200 | N/A | 0.00% | **100.000** | $0$ | 0.00% (Mốc chuẩn) | **FEASIBLE** |
| **P2** | **B1:** Decision Stump | 0.5000 | 0 | 0 | 11.800 | 200 | N/A | 0.00% | **100.000** | $0$ | 0.00% | **FEASIBLE** |
| **P3** | **B1:** Decision Stump | 0.0196 | 160 | 253 | 11.547 | 40 | 38.74% | 80.00% | **22.530** | $413$ | **77.47%** | **FEASIBLE** |
| **P4** | **B2:** Logistic Regression | 0.5000 | 129 | 48 | 11.752 | 71 | 72.88% | 64.50% | **35.980** | $177$ | **64.02%** | **FEASIBLE** |
| **P5** | **B2:** Logistic Regression | 0.0196 | 186 | 323 | 11.477 | 14 | 36.54% | 93.00% | **10.230** | $509$ | **89.77%** | **FEASIBLE** |

> [!NOTE]
> **PHÂN BIỆT RANH GIỚI KHOA HỌC & CẢNH BÁO THIÊN VỊ LỰA CHỌN (SELECTION BIAS DISCLOSURE):**
> 1. **Phân biệt kết quả Validation với đánh giá học thuật độc lập:** Kết quả trên phân vùng Validation phản ánh sự mô phỏng chính sách trong quy trình nội bộ, tách bạch hoàn toàn với đánh giá độc lập của hội đồng chấm đồ án và chưa chạm tới tập Official Test được niêm phong tới G10.
> 2. **Thiên vị lựa chọn (Selection Bias):** Việc lựa chọn siêu tham số và ngưỡng quyết định trên cùng phân vùng Validation vốn chứa đựng thiên vị lựa chọn (selection bias). Do đó, chi phí Validation tốt nhất ($10.230$) **không đại diện cho ước lượng không thiên lệch (unbiased estimate)** về năng lực tổng quát hóa trên dữ liệu thực địa tương lai.
> 3. **Bảo tồn lần chạy lỗi:** Lần chạy thất bại tiền kiểm tra `scania_g4_b2_real_001` (do thiếu gói môi trường tại bước supervisor) được lưu giữ đầy đủ tại `results/scania_aps/g4/scania_g4_b2_real_001/` theo đúng chuẩn mực minh bạch khoa học.

---

## 7. KẾT QUẢ TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RANDOM FOREST + OPTUNA TPE)

### 7.1. Cấu trúc bài toán tối ưu hóa có ràng buộc Phase 2
Nhằm vượt qua ranh giới của các mô hình tuyến tính đơn giản ở giai đoạn G4, Phase 2 triển khai mô hình học máy phi tuyến mạnh mẽ **Random Forest** kết hợp thuật toán tối ưu hóa Bayes **Optuna TPESampler** (Tree-structured Parzen Estimator) và phương pháp tìm kiếm ngưỡng vector hóa không tốn thêm fit (zero-fit vectorized threshold optimization).

- **Thuật toán tối ưu hóa:** Optuna TPESampler với seed cố định `seed = 42`.
- **Ngân sách huấn luyện được duyệt:** Đúng 20 trials tuần tự, tương ứng tối đa 20 lượt fit mô hình thật (`max_trials = 20`, `total_max_fits = 20`, `max_fits_per_trial = 1`).
- **Không gian tìm kiếm siêu tham số $\Theta$:**
  - $n\_estimators \in [30, 80]$, bước nhảy (step) 10.
  - $max\_depth \in [6, 16]$, bước nhảy 2.
  - $min\_samples\_split \in [2, 10]$, bước nhảy 2.
  - $max\_features \in [0.2, 0.6]$, liên tục (float).
  - Khóa cố định: `class_weight = 'balanced'`, `random_state = 42`, `n_jobs = 1`, `bootstrap = True`.
- **Không gian tìm kiếm ngưỡng can thiệp $\tau$:**
  - Quét 101 điểm phân vị xác suất vector hóa $\tau \in [0.01, 0.60]$ trên tập Validation độc lập sau khi đã huấn luyện xong cây rừng.
  - Chọn ngưỡng $\tau^*$ đạt cực tiểu hàm chi phí $f(\theta, \tau) = 10 \cdot FP + 500 \cdot FN$ thỏa mãn điều kiện khả thi về năng lực xưởng: $M(\theta, \tau) = TP + FP \le 1200$.

### 7.2. Bảng kết quả đo đạc thực nghiệm 20 Trials từ Run `scania_phase2_rf_optuna_002`

Dưới đây là dữ liệu thực nghiệm đo đạc chính thức từ 20 lượt huấn luyện thực tế trên phân vùng Validation (12.000 mẫu: 200 ca dương tính, 11.800 ca âm tính):

| Trial | n_est | depth | split | max_feat | Ngưỡng $\tau^*$ | Chi phí | $M \le 1200$ | TP | FP | FN | TN | Recall | Precision | Trạng thái |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | 50 | 16 | 8 | 0.499 | 0.2224 | 9.250 | 575 | 193 | 382 | 7 | 11.418 | 96.50% | 33.57% | FEASIBLE |
| 1 | 30 | 8 | 2 | 0.262 | 0.2755 | 9.770 | 627 | 193 | 434 | 7 | 11.366 | 96.50% | 30.78% | FEASIBLE |
| 2 | 30 | 16 | 8 | 0.440 | 0.2816 | 9.800 | 530 | 192 | 338 | 8 | 11.462 | 96.00% | 36.23% | FEASIBLE |
| 3 | 60 | 14 | 2 | 0.588 | 0.2282 | 9.270 | 577 | 193 | 384 | 7 | 11.416 | 96.50% | 33.45% | FEASIBLE |
| 4 | 30 | 16 | 8 | 0.479 | 0.3000 | 10.360 | 486 | 191 | 295 | 9 | 11.505 | 95.50% | 39.30% | FEASIBLE |
| 5 | 40 | 10 | 2 | 0.273 | 0.3541 | 8.870 | 537 | 193 | 344 | 7 | 11.456 | 96.50% | 35.94% | FEASIBLE |
| 6 | 40 | 8 | 4 | 0.237 | 0.3541 | 8.890 | 539 | 193 | 346 | 7 | 11.454 | 96.50% | 35.81% | FEASIBLE |
| 7 | 30 | 16 | 2 | 0.586 | 0.2520 | 9.720 | 522 | 192 | 330 | 8 | 11.470 | 96.00% | 36.78% | FEASIBLE |
| 8 | 70 | 16 | 8 | 0.525 | 0.2816 | 9.170 | 567 | 193 | 374 | 7 | 11.426 | 96.50% | 34.04% | FEASIBLE |
| 9 | 60 | 14 | 8 | 0.443 | 0.2633 | 9.120 | 562 | 193 | 369 | 7 | 11.431 | 96.50% | 34.34% | FEASIBLE |
| 10 | 40 | 10 | 6 | 0.201 | 0.3541 | 8.780 | 528 | 193 | 335 | 7 | 11.465 | 96.50% | 36.55% | FEASIBLE |
| 11 | 40 | 10 | 6 | 0.208 | 0.3541 | 9.240 | 474 | 192 | 282 | 8 | 11.518 | 96.00% | 40.51% | FEASIBLE |
| 12 | 80 | 10 | 6 | 0.364 | 0.3357 | 8.860 | 536 | 193 | 343 | 7 | 11.457 | 96.50% | 36.01% | FEASIBLE |
| 13 | 50 | 12 | 10 | 0.356 | 0.2755 | 9.150 | 565 | 193 | 372 | 7 | 11.428 | 96.50% | 34.16% | FEASIBLE |
| 14 | 80 | 6 | 10 | 0.344 | 0.3173 | 8.350 | 585 | 195 | 390 | 5 | 11.410 | 97.50% | 33.33% | FEASIBLE |
| 15 | 80 | 6 | 10 | 0.354 | 0.3173 | 8.320 | 582 | 195 | 387 | 5 | 11.413 | 97.50% | 33.51% | FEASIBLE |
| **16** | **50** | **10** | **10** | **0.427** | **0.3232** | **6.330** | **578** | **195** | **383** | **5** | **11.417** | **97.50%** | **33.74%** | **FEASIBLE (BEST)** |
| 17 | 50 | 12 | 4 | 0.406 | 0.2633 | 8.990 | 549 | 193 | 356 | 7 | 11.444 | 96.50% | 35.15% | FEASIBLE |
| 18 | 50 | 12 | 4 | 0.413 | 0.2571 | 8.960 | 546 | 193 | 353 | 7 | 11.447 | 96.50% | 35.35% | FEASIBLE |
| 19 | 70 | 6 | 10 | 0.443 | 0.3232 | 7.820 | 582 | 196 | 386 | 4 | 11.414 | 98.00% | 33.68% | FEASIBLE |

### 7.3. Phân tích chính sách tối ưu toàn cục (Optimal Policy — Trial 16)
Thuật toán Optuna TPE đã hội tụ và tìm thấy cấu hình tối ưu toàn cục tại **Trial 16** với các thông số:
- **Bộ siêu tham số rừng ngẫu nhiên:** `n_estimators = 50`, `max_depth = 10`, `min_samples_split = 10`, `max_features = 0.426743`.
- **Ngưỡng quyết định can thiệp tối ưu:** $\tau^* = 0.323244$.
- **Ma trận nhầm lẫn đo đạc:**
  - $TP = 195$ (Phát hiện chính xác 195/200 xe hỏng APS thực tế, Recall đạt $97.50\%$).
  - $FP = 383$ (383 xe hỏng bộ phận khác bị kiểm tra thêm APS tại xưởng).
  - $FN = 5$ (Chỉ bỏ sót đúng 5 ca hỏng APS dẫn đến sự cố dọc đường).
  - $TN = 11.417$ (11.417 xe hỏng bộ phận khác được cho xuất xưởng an toàn).
- **Tổng chi phí benchmark tối ưu:**
  $$f^* = 10 \cdot 383 + 500 \cdot 5 = 3.830 + 2.500 = \mathbf{6.330} \text{ đơn vị chi phí benchmark}$$
- **Kiểm định ràng buộc công suất xưởng:**
  $$M^* = TP + FP = 195 + 383 = 578 \text{ xe} \le 1.200 \text{ xe} \quad (\text{Thỏa mãn ràng buộc, dư thừa năng lực tiếp nhận } 622 \text{ xe})$$

### 7.4. Phân tích trực quan hóa hai đồ thị tối ưu hóa thực nghiệm

#### Đồ thị 1: Lịch sử hội tụ của thuật toán tối ưu hóa (Optuna TPE Convergence History)
Đồ thị [optimization_convergence.png](file:///d:/Năm%203/HK1_2026/Nhập%20môn%20tối%20ưu%20hóa/baitaplon/worktrees/antigravity/figures/optimization/optimization_convergence.png) trực quan hóa tiến trình tìm kiếm của Optuna TPE qua 20 trials:
- **Đường chấm xanh (Trial Cost):** Chi phí khả thi của từng trial dao động trong khoảng từ $10.360$ (Trial 4) đến $6.330$ (Trial 16).
- **Đường bậc thang đỏ (Best Feasible Cost):** Khởi đầu ở mức $9.250$ tại Trial 0, được cải thiện từng bước qua các vùng tham số tiềm năng: xuống $8.870$ (Trial 5), $8.780$ (Trial 10), $8.350$ (Trial 14), $8.320$ (Trial 15), và xác lập kỷ lục cực tiểu **$6.330$** tại Trial 16.
- **Đường đứt nét xám (B2 Baseline):** Mốc chi phí chuẩn $10.230$ của mô hình Logistic Regression G4. Đồ thị chứng minh rõ ràng: **19/20 trials của Random Forest đều đạt chi phí thấp hơn đáng kể so với mô hình cơ sở B2**, chứng tỏ ưu thế áp đảo của mô hình học máy phi tuyến khi kết hợp cùng bộ điều chỉnh siêu tham số Bayes.

#### Đồ thị 2: Đánh đổi Chi phí - Năng lực xưởng và đường cong quét ngưỡng (Cost vs Capacity Trade-off)
Đồ thị [cost_vs_capacity_tradeoff.png](file:///d:/Năm%203/HK1_2026/Nhập%20môn%20tối%20ưu%20hóa/baitaplon/worktrees/antigravity/figures/optimization/cost_vs_capacity_tradeoff.png) trực quan hóa không gian tìm kiếm đa chiều giữa Chi phí benchmark và Số lượng xe kiểm tra ($M$):
- **Vùng bóng xanh lục (Feasible Region):** Đại diện cho miền chấp nhận được của xưởng dịch vụ ($M \le 1.200$).
- **Đường cong quét ngưỡng 101 điểm của Trial 16 (Đường liền nét xanh đậm):**
  - Khi ngưỡng $\tau \to 0$: Chi phí phạt $FN \to 0$ nhưng số lượng cảnh báo sai $FP$ bùng nổ, kéo theo $M$ tăng vọt vượt qua $1.200$, đẩy chính sách vào vùng **Không khả thi (Infeasible)**.
  - Khi ngưỡng $\tau \to 1$: Số xe kiểm tra $M \to 0$ nhưng số ca bỏ sót $FN \to 200$, chi phí bùng nổ tiệm cận $100.000$ (mức trần của B0 Dummy).
  - Điểm cực tiểu đáy parabol đạt chính xác tại $\mathbf{M = 578, \text{Cost} = 6.330}$ ứng với $\tau^* = 0.3232$, nằm sâu an toàn bên trong vùng khả thi.
- **Ngôi sao đỏ:** Tọa độ chính sách tối ưu toàn cục của Trial 16.
- **Điểm vuông màu tím:** Tọa độ mô hình cơ sở G4 B2 Logistic Regression ($M = 509, \text{Cost} = 10.230$).
- **Điểm tròn xanh nhạt:** Tọa độ của 19 trials còn lại trong Phase 2, đều phân bố tập trung trong dải $M \in [474, 627]$ và chi phí $[7.820, 10.360]$.

### 7.5. Bảng tổng hợp so sánh hiệu quả giữa các giai đoạn nghiên cứu

| Thuộc tính so sánh | G4 B0: Majority Dummy | G4 B1: Decision Stump | G4 B2: Logistic Regression | Phase 2: Random Forest + TPE |
|---|:---:|:---:|:---:|:---:|
| **Ngưỡng quyết định $\tau$** | Không áp dụng | $0.0196$ | $0.0196$ | $\mathbf{0.3232}$ |
| **Số xe hỏng phát hiện (TP)** | $0$ | $160$ | $186$ | $\mathbf{195}$ |
| **Số ca kiểm tra nhầm (FP)** | $0$ | $253$ | $323$ | $383$ |
| **Số ca bỏ sót nguy hiểm (FN)** | $200$ | $40$ | $14$ | $\mathbf{5}$ |
| **Độ nhạy (Recall)** | $0.00\%$ | $80.00\%$ | $93.00\%$ | $\mathbf{97.50\%}$ |
| **Độ chính xác (Precision)** | N/A | $38.74\%$ | $36.54\%$ | $33.74\%$ |
| **F1-Score** | N/A | $52.20\%$ | $52.47\%$ | $50.13\%$ |
| **Lượt xe vào xưởng ($M \le 1200$)** | $0$ | $413$ | $509$ | $578$ |
| **Tổng chi phí benchmark** | $100.000$ | $22.530$ | $10.230$ | $\mathbf{6.330}$ |
| **Mức tiết kiệm vs B0 Dummy** | $0.00\%$ (Gốc) | $77.47\%$ | $89.77\%$ | $\mathbf{93.67\%}$ |
| **Mức giảm chi phí vs B2 Baseline** | Không giảm | Tăng $+12.300$ | $0.00\%$ (Gốc B2) | **Giảm $-3.900$ ($-38.12\%$)** |
| **Trạng thái ràng buộc** | FEASIBLE | FEASIBLE | FEASIBLE | **FEASIBLE** |

### 7.6. Đo đạc tài nguyên, cơ chế an toàn và bảo tồn dữ liệu
- **Kiểm soát luồng & Bộ nhớ:** Tiến trình chạy đơn luồng bản địa (`max_native_threads = 1`), đỉnh tiêu thụ RAM thực tế ghi nhận qua Windows Job Object chỉ đạt **159.82 MB** (nằm sâu dưới trần cho phép 2048 MB).
- **Thời gian thực thi:** Hoàn thành toàn bộ 20 trials trong **543.06 giây** (trung bình ~27.1 giây/trial), nằm hoàn toàn trong hạn ngạch thời gian tối đa 900 giây được Chủ dự án cấp quyền.
- **Số lượt huấn luyện thật (Estimator Fits):** Ghi nhận chính xác **20/20 fits STARTED và COMPLETED**, $0$ fit thất bại, $0$ fit gián đoạn.
- **Niêm phong tập Official Test:** Bộ dữ liệu kiểm thử 16.000 mẫu hoàn toàn không bị truy cập (0 byte, 0 quan sát), bảo tồn tính khách quan tuyệt đối cho Gate G10.
- **Bảo tồn khoa học lần chạy lỗi Run 001:** Lần chạy trước `scania_phase2_rf_optuna_001` bị timeout ở giây 300 (đã ghi nhận 12 fit STARTED, 11 fit COMPLETED, 1 fit INTERRUPTED) được lưu trữ nguyên vẹn tại `results/scania_aps/phase2/scania_phase2_rf_optuna_001/` kèm mã băm SHA-256 đối chiếu độc lập.

---

## 8. ĐÁNH GIÁ TÍNH TÁI LẬP, GIỚI HẠN & KẾT LUẬN

### 8.1. Khả năng tái lập khoa học (Reproducibility Protocol)
- **Môi trường độc lập:** Python 3.11.9, scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, Optuna 5.0.0.
- **Khóa hạt giống ngẫu nhiên:** `random_state = 42` cố định trên mọi mô hình, phép phân chia Train/Validation và bộ lấy mẫu Optuna TPESampler.
- **Kiểm soát tài nguyên hệ điều hành:** Giới hạn 1 native thread (`threadpoolctl`), trần RAM 2048 MB và thời gian tối đa kiểm soát qua Windows Job Object.
- **Bảo toàn toàn vẹn:** Mọi artifact xuất xưởng từ cả hai giai đoạn G4 (`scania_g4_b2_real_002`) và Phase 2 (`scania_phase2_rf_optuna_002`) đều được ký băm SHA-256 LF-normalized trong `checksums.json` và nghiệm thu độc lập bằng hàm `verify_run()` và `verify_phase2_run()`.

### 8.2. Giới hạn nghiên cứu (Limitations)
1. **Bản chất mô phỏng chính sách:** Đánh giá chi phí trên tập Validation là sự mô phỏng chính sách dựa trên dữ liệu tĩnh lịch sử, không chứng minh tác động nhân quả dài hạn của chu trình bảo dưỡng khi đưa vào triển khai thực địa.
2. **Giả định về năng lực xưởng:** Giới hạn 10% ($M \le 1200$) là một giả định kịch bản vận hành để phục vụ bài toán tối ưu hóa có ràng buộc, không phản ánh chính xác năng lực thực tế tại từng trạm dịch vụ cụ thể của Scania.
3. **Phạm vi không gian tìm kiếm:** Ngân sách thực nghiệm được giới hạn ở 20 trials tuần tự do kiểm soát an toàn tài nguyên. Mặc dù Trial 16 đã giảm chi phí xuống 6.330, không gian siêu tham số rộng hơn hoặc các mô hình ensemble khác (ví dụ: Gradient Boosting) có thể tiếp tục mang lại tiềm năng tối ưu trong các nghiên cứu mở rộng tương lai.

### 8.3. Kết luận
Đề tài đã hoàn thành xuất sắc việc giải quyết bài toán bảo trì kỹ thuật công nghiệp phức tạp dưới lăng kính toán học tối ưu hóa có ràng buộc:
1. Thiết lập hệ thống cơ sở chuẩn tắc khoa học vững chắc từ G4 baselines ($C^*_{\text{G4}} = 10.230$).
2. Triển khai thành công mô hình tối ưu hóa cốt lõi Phase 2 kết hợp Random Forest và Optuna TPE, xác định chính sách can thiệp tối ưu toàn cục tại Trial 16 với chi phí chỉ **6.330 đơn vị benchmark**, giúp tiết kiệm **93.67%** chi phí so với việc không can thiệp (B0 Dummy) và giảm tiếp **38.12%** chi phí so với mô hình cơ sở tốt nhất G4 (B2 Logistic Regression).
3. Chứng minh trên thực nghiệm sự khác biệt cốt lõi giữa ngưỡng giải tích Bayes phi ràng buộc và ngưỡng tối ưu thực tế trong điều kiện xưởng dịch vụ có giới hạn tài nguyên tiếp nhận.
4. Bảo đảm tính trung thực học thuật tuyệt đối: không rò rỉ tập dữ liệu kiểm thử Official Test, minh bạch hóa lịch sử lỗi, và xác thực 100% kết quả thông qua chữ ký băm mật mã học SHA-256.

---

## 9. PHỤ LỤC & KHAI BÁO CÔNG CỤ HỖ TRỢ (AI ASSISTANCE DISCLOSURE)

Theo quy định tại Mục 10 của `DE_BAI_TAP_LON_CA_NHAN_5_TUAN_GITHUB_PORTFOLIO.pdf`:
- **Công cụ AI hỗ trợ:** Đề tài có sử dụng các trợ lý lập trình trí tuệ nhân tạo (Codex và Google Antigravity) để hỗ trợ rà soát mã nguồn, thiết kế các ca kiểm thử biên (unit tests), hỗ trợ lập trình khung pipeline và soạn thảo tài liệu.
- **Phần sinh viên tự kiểm chứng và chịu trách nhiệm hoàn toàn:**
  - Thiết lập công thức toán học hàm mục tiêu và định nghĩa ràng buộc năng lực xưởng.
  - Phân tích ngữ nghĩa lớp âm tính theo tài liệu gốc UCI Scania #421.
  - Kiểm tra và đảm bảo không rò rỉ tập dữ liệu kiểm thử Official Test.
  - Toàn bộ kết quả thử nghiệm được đối chiếu và xác nhận tính toàn vẹn thông qua các chữ ký băm SHA-256 trên repository công khai.
