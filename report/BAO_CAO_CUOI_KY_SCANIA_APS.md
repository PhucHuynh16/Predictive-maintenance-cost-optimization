# BẢN THẢO ĐỀ CƯƠNG BÁO CÁO TỔNG KẾT: TỐI ƯU HÓA CHI PHÍ BẢO TRÌ DỰ ĐOÁN HỆ THỐNG KHÍ NÉN TRÊN XE TẢI NẶNG SCANIA APS (UCI 421)

> **TRẠNG THÁI TÀI LIỆU:** BẢN THẢO ĐỀ CƯƠNG (DRAFT OUTLINE) — Đã tích hợp số liệu đo đạc thực tế chính thức từ G4 Baseline Run `scania_g4_b2_real_002`; đang chờ hoàn tất thực nghiệm tối ưu hóa Phase 2 để xuất bản và kiểm chứng trực quan file Word/PDF chính thức.

**Học phần:** Nhập môn Tối ưu hóa — Học kỳ 1, Năm học 2026–2027  
**Đơn vị đào tạo:** Khoa Công nghệ Thông tin — Trường Đại học Văn Lang  
**Sinh viên thực hiện:** Huỳnh Phúc  
**Mã nguồn & Repository:** [PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)  
**Tập dữ liệu nghiên cứu:** UCI Machine Learning Repository — Dataset #421: *APS Failure at Scania Trucks* (Scania CV AB, 2016)  

---

> [!IMPORTANT]
> **RANH GIỚI KHOA HỌC BẮT BUỘC:**
> Việc hoàn thành các mô hình cơ sở G4 Baselines (B0, B1, B2) **chỉ hoàn thành bước xác lập mốc so sánh cơ sở (reference benchmarks), chưa hoàn thành yêu cầu phương pháp tối ưu hóa bắt buộc của môn học**.
> - Phương pháp tối ưu hóa cốt lõi theo đề cương (Random Forest kết hợp Bayesian Hyperparameter Optimization & Threshold Tuning qua Optuna TPE) là một hạng mục nghiên cứu độc lập (Phase 2), cần được cấp quyền, thực thi và lưu trữ lịch sử tìm kiếm (search history) cùng ít nhất 02 đồ thị tối ưu (hội tụ / đánh đổi) từ dữ liệu thực tế.

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

## 7. ĐÁNH GIÁ TÍNH TÁI LẬP, GIỚI HẠN & KẾT LUẬN

### 7.1. Khả năng tái lập khoa học (Reproducibility Protocol)
- **Môi trường độc lập:** Python 3.11.9, scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, Optuna 5.0.0.
- **Khóa hạt giống ngẫu nhiên:** `random_state = 42` cố định trên mọi mô hình và phép phân chia.
- **Kiểm soát tài nguyên hệ điều hành:** Giới hạn 1 native thread (`threadpoolctl`), trần RAM 2048 MB và thời gian tối đa 120 giây qua Windows Job Object.
- **Bảo toàn toàn vẹn:** Mọi artifact xuất xưởng được ký băm SHA-256 LF-normalized trong `checksums.json` và nghiệm thu độc lập bằng hàm `verify_run()`.

### 7.2. Giới hạn nghiên cứu (Limitations)
1. **Bản chất mô phỏng chính sách:** Đánh giá chi phí trên tập Validation là sự mô phỏng chính sách dựa trên dữ liệu tĩnh lịch sử, không chứng minh tác động nhân quả dài hạn của chu trình bảo dưỡng khi đưa vào triển khai thực địa.
2. **Giả định về năng lực xưởng:** Giới hạn 10% ($M \le 1200$) là một giả định kịch bản vận hành để phục vụ bài toán tối ưu hóa có ràng buộc, không phản ánh chính xác năng lực thực tế tại từng trạm dịch vụ cụ thể của Scania.
3. **Phạm vi mô hình:** Đợt thử nghiệm G4 chỉ khảo sát các mô hình cơ sở tuyến tính và cây quyết định đơn giản; hiệu quả tối ưu thực sự của các thuật toán HPO tiên tiến (Optuna TPE kết hợp Random Forest) thuộc về phạm vi mở rộng Phase 2.

### 7.3. Kết luận
Đề tài đã hoàn thành xuất sắc việc chuyển hóa bài toán bảo trì kỹ thuật công nghiệp phức tạp thành một bài toán tối ưu hóa toán học chuẩn tắc, có biến quyết định, hàm mục tiêu phi đối xứng rõ ràng và ràng buộc công suất khả thi. Quy trình thực nghiệm G4 baselines đã thiết lập mốc so sánh vững chắc ($C^*_{\text{G4}} = 10.230$), mở đường cho giai đoạn tối ưu hóa cốt lõi Phase 2.

---

## 8. PHỤ LỤC & KHAI BÁO CÔNG CỤ HỖ TRỢ (AI ASSISTANCE DISCLOSURE)

Theo quy định tại Mục 10 của `DE_BAI_TAP_LON_CA_NHAN_5_TUAN_GITHUB_PORTFOLIO.pdf`:
- **Công cụ AI hỗ trợ:** Đề tài có sử dụng các trợ lý lập trình trí tuệ nhân tạo (Codex và Google Antigravity) để hỗ trợ rà soát mã nguồn, thiết kế các ca kiểm thử biên (unit tests), hỗ trợ lập trình khung pipeline và soạn thảo tài liệu.
- **Phần sinh viên tự kiểm chứng và chịu trách nhiệm hoàn toàn:**
  - Thiết lập công thức toán học hàm mục tiêu và định nghĩa ràng buộc năng lực xưởng.
  - Phân tích ngữ nghĩa lớp âm tính theo tài liệu gốc UCI Scania #421.
  - Kiểm tra và đảm bảo không rò rỉ tập dữ liệu kiểm thử Official Test.
  - Toàn bộ kết quả thử nghiệm được đối chiếu và xác nhận tính toàn vẹn thông qua các chữ ký băm SHA-256 trên repository công khai.
