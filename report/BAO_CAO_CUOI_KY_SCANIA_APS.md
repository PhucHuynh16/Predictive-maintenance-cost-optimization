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
> - Nghiên cứu đã hoàn thành toàn diện ba giai đoạn học thuật: (1) Xác lập hệ thống đường cơ sở chuẩn tắc G4 Baselines (B0, B1, B2), (2) Triển khai phương pháp tối ưu hóa toán học có ràng buộc cốt lõi Phase 2 (Random Forest kết hợp Bayesian Hyperparameter Optimization & Vectorized Threshold Tuning qua Optuna TPE), và (3) Đánh giá độc lập chính thức tại Gate G10 trên toàn bộ 16.000 mẫu tập Official Test.
> - Toàn bộ dữ liệu thực nghiệm được đo đạc thật qua 20 lượt huấn luyện Optuna và 1 lượt refit đánh giá độc lập dưới sự kiểm soát tài nguyên nghiêm ngặt của Windows Job Object.
> - Tập kiểm thử Official Test (16.000 mẫu) được giữ niêm phong tuyệt đối cho đến Gate G10, thực thi zero tuning, zero data leakage, đạt mức tiết kiệm chi phí **92.62%** và thỏa mãn 100% ràng buộc công suất xưởng.

---

## TÓM TẮT ĐỀ TÀI (ABSTRACT)

Bảo trì dự đoán (Predictive Maintenance - PdM) là bài toán kinh điển trong công nghiệp vận tải hạng nặng nhằm giảm thiểu rủi ro sự cố dọc đường và chi phí bảo dưỡng. Nghiên cứu này tiếp cận bài toán chẩn đoán hư hỏng hệ thống khí nén (Air Pressure System - APS) trên xe tải Scania (tập dữ liệu benchmark UCI 421 gồm 60.000 mẫu huấn luyện và 16.000 mẫu kiểm thử với 170 thuộc tính cảm biến) dưới góc nhìn **Tối ưu hóa toán học có ràng buộc**. 

Đặc thù bài toán là hàm chi phí phi đối xứng nghiêm ngặt theo chuẩn benchmark công nghiệp: chi phí bỏ sót một xe hỏng APS dẫn đến chết máy dọc đường (False Negative - FN) là **500 đơn vị chi phí benchmark**, trong khi chi phí kiểm tra định kỳ không cần thiết tại xưởng (False Positive - FP) là **10 đơn vị chi phí benchmark** (tỷ số $50:1$). Đồng thời, nghiên cứu đặt ra **giả định ràng buộc năng lực xưởng** (Maintenance Capacity Constraint assumption) với mức tiếp nhận tối đa không quá 10% quy mô phân vùng bảo dưỡng ($M = TP + FP \le \lfloor N/10 \rfloor$, tương ứng 1.200 lượt xe trên tập Validation 12.000 xe và 1.600 lượt xe trên tập Official Test 16.000 xe).

Nghiên cứu tuân thủ nghiêm ngặt chuẩn mực khoa học và phòng chống rò rỉ dữ liệu (No Data Leakage):
1. **Phân vùng dữ liệu:** Khóa cố định tập Train (48.000 mẫu) / Validation (12.000 mẫu) dựa trên hash G3 đã nghiệm thu (`efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`); niêm phong tập Official Test (16.000 mẫu) đến Gate G10.
2. **Khung đường cơ sở (Baselines):** Xây dựng và kiểm chuẩn 3 mô hình: B0 (Majority Dummy — không can thiệp), B1 (Decision Stump — cây quyết định 1 tầng) và B2 (Logistic Regression chuẩn hóa L-BFGS `max_iter=2000`).
3. **Mô hình hóa ngưỡng tối ưu:** Phân tích sự đánh đổi giữa ngưỡng xác suất chuẩn ($\tau = 0.5$) và ngưỡng lý thuyết Bayes tối ưu chi phí ($\tau = 10/510 \approx 0.0196$), chứng minh rằng trong điều kiện ràng buộc công suất xưởng có hiệu lực, ngưỡng tối ưu thực tế phải được tìm kiếm thông qua tối ưu hóa có điều kiện.
4. **Nghiệm thu thực nghiệm Official Test (Gate G10):** Chính sách tối ưu đóng băng từ Trial 16 ($\tau^* = 0.323244$) khi kiểm thử trên 16.000 mẫu Official Test độc lập đạt tổng chi phí **13.840 đơn vị**, tiết kiệm **92.62%** chi phí so với không can thiệp (187.500 đơn vị), phát hiện đúng 357/375 ca lỗi ($Recall = 95.20\%$, $Precision = 42.45\%$), và kiểm soát số xe vào xưởng ở mức 841 xe ($5.26\% \le K = 1.600$), thỏa mãn trọn vẹn ràng buộc công suất.

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

Dưới đây là dữ liệu thực nghiệm đo đạc chính thức từ 20 lượt huấn luyện thực tế trên phân vùng Validation (12.000 mẫu: 200 ca dương tính, 11.800 ca âm tính) trích xuất trực tiếp từ `results/scania_aps/phase2/scania_phase2_rf_optuna_002/trials_summary.csv`:

| Trial # | Chi phí | $M$ | Ngưỡng $\tau^*$ | TP | FP | FN | $n_{\text{est}}$ | depth | split | feat | Thời gian fit (s) | Trạng thái |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | 7.840 | 576 | 0.2588 | 192 | 384 | 8 | 30 | 12 | 8 | 0.380 | 18.80 | FEASIBLE |
| 1 | 7.790 | 724 | 0.4363 | 195 | 529 | 5 | 20 | 5 | 2 | 0.460 | 7.00 | FEASIBLE |
| 2 | 6.750 | 569 | 0.3154 | 194 | 375 | 6 | 50 | 10 | 2 | 0.491 | 34.68 | FEASIBLE |
| 3 | 7.880 | 682 | 0.5201 | 194 | 488 | 6 | 60 | 5 | 3 | 0.255 | 11.76 | FEASIBLE |
| 4 | 7.800 | 572 | 0.3978 | 192 | 380 | 8 | 30 | 8 | 5 | 0.287 | 10.13 | FEASIBLE |
| 5 | 7.310 | 625 | 0.5609 | 194 | 431 | 6 | 50 | 5 | 4 | 0.310 | 11.73 | FEASIBLE |
| 6 | 6.490 | 594 | 0.2417 | 195 | 399 | 5 | 40 | 11 | 3 | 0.354 | 21.62 | FEASIBLE |
| 7 | 7.520 | 697 | 0.5887 | 195 | 502 | 5 | 40 | 4 | 7 | 0.251 | 6.21 | FEASIBLE |
| 8 | 6.970 | 693 | 0.1801 | 196 | 497 | 4 | 20 | 12 | 10 | 0.443 | 14.61 | FEASIBLE |
| 9 | 7.540 | 699 | 0.5696 | 195 | 504 | 5 | 30 | 4 | 8 | 0.332 | 6.14 | FEASIBLE |
| 10 | 6.340 | 579 | 0.2408 | 195 | 384 | 5 | 60 | 12 | 7 | 0.433 | 71.20 | FEASIBLE |
| 11 | 6.790 | 675 | 0.1739 | 196 | 479 | 4 | 50 | 11 | 4 | 0.388 | 32.75 | FEASIBLE |
| 12 | 7.060 | 600 | 0.2261 | 194 | 406 | 6 | 60 | 12 | 7 | 0.435 | 44.51 | FEASIBLE |
| 13 | 6.880 | 633 | 0.2428 | 195 | 438 | 5 | 20 | 10 | 2 | 0.484 | 14.20 | FEASIBLE |
| 14 | 7.280 | 622 | 0.2200 | 194 | 428 | 6 | 40 | 12 | 6 | 0.500 | 32.49 | FEASIBLE |
| 15 | 6.890 | 634 | 0.3268 | 195 | 439 | 5 | 60 | 8 | 7 | 0.370 | 27.30 | FEASIBLE |
| **16** | **6.330** | **578** | **0.3232** | **195** | **383** | **5** | **50** | **10** | **10** | **0.427** | **38.61** | **FEASIBLE (BEST)** |
| 17 | 6.650 | 610 | 0.2858 | 195 | 415 | 5 | 60 | 10 | 8 | 0.441 | 70.21 | FEASIBLE |
| 18 | 7.070 | 652 | 0.2589 | 195 | 457 | 5 | 50 | 9 | 9 | 0.497 | 31.83 | FEASIBLE |
| 19 | 7.240 | 618 | 0.2392 | 194 | 424 | 6 | 50 | 11 | 10 | 0.440 | 33.46 | FEASIBLE |

### 7.3. Phân tích chính sách khả thi tốt nhất quan sát được (Trial 16)
Trong ngân sách 20 trials thực nghiệm được phê duyệt, thuật toán Optuna TPE đã tìm thấy chính sách khả thi tốt nhất quan sát được tại **Trial 16** với các thông số:
- **Bộ siêu tham số rừng ngẫu nhiên:** `n_estimators = 50`, `max_depth = 10`, `min_samples_split = 10`, `max_features = 0.426866`.
- **Ngưỡng quyết định can thiệp tối ưu:** $\tau^* = 0.323244$.
- **Ma trận nhầm lẫn đo đạc:**
  - $TP = 195$ (Phát hiện chính xác 195/200 xe hỏng APS thực tế, Recall đạt $97.50\%$).
  - $FP = 383$ (383 xe hỏng bộ phận khác bị kiểm tra thêm APS tại xưởng).
  - $FN = 5$ (Chỉ bỏ sót đúng 5 ca hỏng APS dẫn đến sự cố dọc đường).
  - $TN = 11.417$ (11.417 xe hỏng bộ phận khác được cho xuất xưởng an toàn).
- **Tổng chi phí benchmark quan sát được:**
  $$f^* = 10 \cdot 383 + 500 \cdot 5 = 3.830 + 2.500 = \mathbf{6.330} \text{ đơn vị chi phí benchmark}$$
- **Kiểm định ràng buộc công suất xưởng:**
  $$M^* = TP + FP = 195 + 383 = 578 \text{ xe} \le 1.200 \text{ xe} \quad (\text{Thỏa mãn ràng buộc khả thi, dư thừa năng lực tiếp nhận } 622 \text{ xe})$$

### 7.4. Phân tích trực quan hóa hai đồ thị tối ưu hóa thực nghiệm

#### Đồ thị 1: Lịch sử hội tụ của thuật toán tối ưu hóa (Optuna TPE Convergence History)
Đồ thị `figures/optimization/optimization_convergence.png` trực quan hóa tiến trình tìm kiếm của Optuna TPE qua 20 trials trên 2 khung nhìn:
- **Khung nhìn toàn cảnh (Global Perspective):** So sánh mức chi phí đạt được so với mốc trần không can thiệp B0 Majority Dummy ($100.000$) và mốc cơ sở B2 Logistic Regression ($10.230$). Toàn bộ 20/20 trials của Random Forest đều đạt chi phí thấp hơn đáng kể so với B2 (dao động từ $6.330$ đến $7.880$).
- **Khung nhìn chi tiết thu phóng (Zoomed Convergence):** Chi phí khả thi tốt nhất lũy tiến khởi đầu ở mức $7.840$ tại Trial 0, liên tục được cải thiện qua các mốc: $7.790$ (Trial 1), $6.750$ (Trial 2), $6.490$ (Trial 6), $6.340$ (Trial 10), và đạt mức chi phí thấp nhất **$6.330$** tại Trial 16.

#### Đồ thị 2: Đánh đổi Chi phí - Năng lực xưởng và đường cong quét ngưỡng (Cost vs Capacity Trade-off)
Đồ thị `figures/optimization/cost_vs_capacity_tradeoff.png` trực quan hóa không gian tìm kiếm giữa Chi phí benchmark và Số lượng xe kiểm tra ($M$):
- **Vùng khả thi (Feasible Domain):** Miền tiếp nhận của xưởng dịch vụ ($M \le 1.200$).
- **Đường quét ngưỡng thực nghiệm 101 điểm của Trial 16:**
  - Được tính toán bằng phương pháp vector hóa trên các dự báo xác suất cố định của Trial 16 với 101 điểm ngưỡng $\tau \in \{0.00, 0.01, \dots, 1.00\}$.
  - Khi $\tau < 0.05$: Số xe kiểm tra $M$ vượt ngưỡng $1.200$ (ví dụ: $\tau=0.04$ có $M=1.314$, $\tau=0.00$ có $M=12.000$), chính sách rơi vào vùng **Không khả thi (Infeasible)**.
  - Khi $\tau \ge 0.05$: Chính sách trở nên khả thi ($M \le 1.200$). Chi phí giảm dần khi $\tau$ tăng và đạt giá trị cực tiểu thực nghiệm tại $\mathbf{M = 578, \text{Cost} = 6.330}$ ứng với $\tau^* = 0.3232$.
  - Khi $\tau > 0.33$: Số ca bỏ sót $FN$ tăng dần làm chi phí tăng trở lại và đạt mức trần $100.000$ khi $\tau = 1.0$ ($M=0, FN=200$).
- **Ngôi sao cam:** Vị trí chính sách khả thi tốt nhất quan sát được tại Trial 16 ($M = 578, \text{Cost} = 6.330$).
- **Hình thoi xanh lục:** Vị trí mốc cơ sở G4 B2 Logistic Regression ($M = 509, \text{Cost} = 10.230$).
- **Phân bố 20 trials:** Toàn bộ 20 cấu hình đều nằm trọn trong vùng khả thi ($M \in [569, 724]$) với chi phí thấp hơn $B_2$.

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
- **Đánh giá độc lập Gate G10:** Sau khi hoàn tất Phase 2 và khóa chính sách tại Trial 16, tập dữ liệu Official Test 16.000 mẫu được mở niêm phong và đánh giá một lần duy nhất tại Gate G10 theo đúng phê duyệt của Chủ dự án.
- **Bảo tồn khoa học các lần chạy lỗi:** Lần chạy trước `scania_phase2_rf_optuna_001` bị timeout ở giây 300 và các lần chạy gián đoạn G10 (`scania_g10_official_test_001`, `002`) đều được lưu trữ nguyên vẹn tại `results/scania_aps/` kèm biên bản pháp y độc lập.

---

## 8. ĐÁNH GIÁ ĐỘC LẬP TRÊN TẬP OFFICIAL TEST (GATE G10)

### 8.1. Quy trình thực thi Gate G10
Để chứng minh năng lực tổng quát hóa thực sự và ngăn chặn triệt để hiện tượng thiên lệch lựa chọn (selection bias) khi tối ưu trên tập Validation, chính sách tốt nhất từ Phase 2 (Trial 16) được đưa vào quy trình kiểm thử độc lập tại Gate G10:
- **Chính sách đóng băng:** Random Forest ($n_{\text{est}}=50, \text{depth}=10, \text{split}=10, \text{feat}=0.426866, \text{class\_weight}=\text{'balanced'}$), ngưỡng quyết định $\tau^* = 0.3232440937634324$.
- **Ngân sách thực nghiệm:** Đúng 1 lần tái huấn luyện duy nhất trên 48.000 mẫu Train (`DETERMINISTIC_TRAIN_REFIT_EVALUATION`), 0 lần huấn luyện trên Test.
- **Validation Regression Guard:** Tái lập chính xác 100% các chỉ số mục tiêu trên tập Validation ($TP=195, FP=383, FN=5, TN=11.417, \text{Cost}=6.330, M=578$) trước khi mở dữ liệu Test.
- **Quy mô tập Official Test:** 16.000 mẫu hoàn toàn chưa từng xuất hiện trong quá trình huấn luyện hay tìm kiếm siêu tham số, gồm 375 ca lỗi APS thực tế ($2.34\%$) và 15.625 ca âm tính ($97.66\%$).
- **Ràng buộc công suất xưởng trên tập Test:** $K = \lfloor 16.000 / 10 \rfloor = 1.600$ xe.

### 8.2. Kết quả đo đạc thực tế trên tập Official Test (Run `scania_g10_official_test_003`)

| Tiêu chí đo đạc | Mặc định B0 (Không can thiệp) | Validation Guard (12.000 mẫu) | **Official Test Độc lập (16.000 mẫu)** |
|---|:---:|:---:|:---:|
| **Quy mô mẫu ($N$)** | 16.000 | 12.000 | **16.000** |
| **Số ca lỗi APS thực tế ($P$)** | 375 | 200 | **375** ($2.34\%$) |
| **True Positives (TP)** | 0 | 195 | **357** |
| **False Positives (FP)** | 0 | 383 | **484** |
| **False Negatives (FN)** | 375 | 5 | **18** |
| **True Negatives (TN)** | 15.625 | 11.417 | **15.141** |
| **Độ nhạy (Recall)** | 0.00% | 97.50% | **95.20%** ($357 / 375$) |
| **Độ chính xác (Precision)** | N/A | 33.74% | **42.45%** ($357 / 841$) |
| **Độ đặc hiệu (Specificity)** | 100.00% | 96.75% | **96.90%** ($15.141 / 15.625$) |
| **F1-Score** | 0.0000 | 0.5013 | **0.5872** |
| **ROC-AUC** | N/A | 0.9903 | **0.9861** |
| **PR-AUC** | N/A | 0.7059 | **0.7495** |
| **Chi phí kiểm tra ($10 \times FP$)** | 0 | 3.830 | **4.840** |
| **Chi phí sự cố dọc đường ($500 \times FN$)** | 187.500 | 2.500 | **9.000** |
| **Tổng chi phí benchmark** | **187.500** | **6.330** | **13.840** |
| **Chi phí trung bình / xe** | 11.719 | 0.528 | **0.865** |
| **Lượt xe vào xưởng ($M = TP + FP$)** | 0 | 578 | **841** (Giới hạn $K = 1.600$) |
| **Tỷ lệ bảo dưỡng ($M / N$)** | 0.00% | 4.82% | **5.26%** |
| **Trạng thái ràng buộc** | FEASIBLE | FEASIBLE | **FEASIBLE (Dư 759 chỗ)** |
| **Mức tiết kiệm chi phí vs B0** | 0.00% (Mốc chuẩn) | 93.67% | **92.62%** (Tiết kiệm 173.660 đơn vị) |

### 8.3. Thảo luận khoa học về năng lực tổng quát hóa
1. **Khả năng khái quát hóa bền vững:** Kết quả trên tập Official Test cho thấy tổng chi phí chỉ là **13.840 đơn vị benchmark**, tiết kiệm tới **92.62%** so với việc không có hệ thống bảo trì dự đoán ($187.500$ đơn vị chi phí).
2. **Kiểm soát tuyệt đối tổn thất nghiêm trọng:** Mô hình bắt trúng $357 / 375$ ca hư hỏng thực tế ($Recall = 95.20\%$), chỉ lọt 18 trường hợp trong 16.000 xe.
3. **Độ chuẩn xác được cải thiện trên dữ liệu thực:** Precision đạt **42.45%** (cao hơn mức 33.74% trên Validation), đồng thời độ đặc hiệu duy trì ở mức cao **96.90%**, cho thấy mô hình không bị dự đoán phóng đại bừa bãi.
4. **Bảo toàn ràng buộc công suất xưởng:** Tổng số lượt xe cần đưa vào kiểm tra thực tế là 841 xe ($5.26\%$), hoàn toàn nằm trong giới hạn trần $K = 1.600$ xe ($10\%$). Xưởng dịch vụ còn dư 759 chỗ tiếp nhận, không bao giờ rơi vào trạng thái quá tải.

---

## 9. ĐÁNH GIÁ TÍNH TÁI LẬP, GIỚI HẠN & KẾT LUẬN

### 9.1. Khả năng tái lập khoa học (Reproducibility Protocol)
- **Môi trường độc lập:** Python 3.11.9, scikit-learn 1.9.1, NumPy 2.4.6, SciPy 1.17.1, Optuna 5.0.0.
- **Khóa hạt giống ngẫu nhiên:** `random_state = 42` cố định trên mọi mô hình, phép phân chia Train/Validation và bộ lấy mẫu Optuna TPESampler.
- **Kiểm soát tài nguyên hệ điều hành:** Giới hạn 1 native thread (`threadpoolctl`), trần RAM 2048 MB và thời gian tối đa kiểm soát qua Windows Job Object.
- **Bảo toàn toàn vẹn:** Mọi artifact xuất xưởng từ cả ba giai đoạn G4 (`scania_g4_b2_real_002`), Phase 2 (`scania_phase2_rf_optuna_002`), và Gate G10 (`scania_g10_official_test_003`) đều được ký băm SHA-256 trong `checksums.json` / `stable_manifest.json` và nghiệm thu độc lập.

### 9.2. Giới hạn nghiên cứu (Limitations)
1. **Bản chất mô phỏng chính sách:** Đánh giá chi phí trên tập Validation và Test dựa trên dữ liệu tĩnh lịch sử, không mô hình hóa tương tác động của tài xế và quy trình phụ tùng thay thế thực địa.
2. **Giả định về năng lực xưởng:** Giới hạn 10% ($M \le 1200$ trên Validation, $M \le 1600$ trên Test) là một giả định kịch bản vận hành thực nghiệm để phục vụ bài toán tối ưu hóa có ràng buộc.
3. **Phạm vi không gian tìm kiếm:** Ngân sách thực nghiệm được giới hạn ở 20 trials tuần tự do kiểm soát an toàn tài nguyên.

### 9.3. Kết luận
Đề tài đã hoàn thành xuất sắc việc giải quyết bài toán bảo trì kỹ thuật công nghiệp phức tạp dưới lăng kính toán học tối ưu hóa có ràng buộc:
1. Thiết lập hệ thống cơ sở chuẩn tắc khoa học vững chắc từ G4 baselines ($C^*_{\text{G4}} = 10.230$).
2. Triển khai thành công mô hình tối ưu hóa cốt lõi Phase 2 kết hợp Random Forest và Optuna TPE, xác định chính sách can thiệp khả thi tốt nhất quan sát được tại Trial 16 trong 20 trials Optuna với chi phí Validation chỉ **6.330 đơn vị benchmark**, tiết kiệm **93.67%** chi phí.
3. Đánh giá độc lập thành công trên toàn bộ 16.000 mẫu tập Official Test tại Gate G10, đạt chi phí chỉ **13.840 đơn vị**, tiết kiệm **92.62%** chi phí so với mặc định, phát hiện 95.20% sự cố và hoàn toàn thỏa mãn ràng buộc năng lực xưởng ($M = 841 \le 1600$).
4. Bảo đảm tính trung thực học thuật tuyệt đối: không rò rỉ dữ liệu, minh bạch hóa lịch sử sự cố và xác thực 100% kết quả qua chữ ký mật mã học SHA-256.

---

## 10. PHỤ LỤC & KHAI BÁO CÔNG CỤ HỖ TRỢ (AI ASSISTANCE DISCLOSURE)

Theo quy định tại Mục 10 của `DE_BAI_TAP_LON_CA_NHAN_5_TUAN_GITHUB_PORTFOLIO.pdf`:
- **Công cụ AI hỗ trợ:** Đề tài có sử dụng các trợ lý lập trình trí tuệ nhân tạo (Codex và Google Antigravity) để hỗ trợ rà soát mã nguồn, thiết kế các ca kiểm thử biên (unit tests), hỗ trợ lập trình khung pipeline và soạn thảo tài liệu.
- **Phần sinh viên tự kiểm chứng và chịu trách nhiệm hoàn toàn:**
  - Thiết lập công thức toán học hàm mục tiêu và định nghĩa ràng buộc năng lực xưởng.
  - Phân tích ngữ nghĩa lớp âm tính theo tài liệu gốc UCI Scania #421.
  - Kiểm tra và đảm bảo không rò rỉ tập dữ liệu kiểm thử Official Test.
  - Toàn bộ kết quả thử nghiệm được đối chiếu và xác nhận tính toàn vẹn thông qua các chữ ký băm SHA-256 trên repository công khai.
