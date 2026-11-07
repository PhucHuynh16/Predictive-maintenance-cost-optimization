# BÁO CÁO ĐỀ TÀI CUỐI KỲ: TỐI ƯU HÓA CHI PHÍ BẢO TRÌ DỰ ĐOÁN HỆ THỐNG KHÍ NÉN TRÊN XE TẢI NẶNG SCANIA APS (UCI 421)

**Môn học:** Nhập môn Tối ưu hóa  
**Học kỳ:** HK1 / Năm học 2026–2027  
**Giảng viên hướng dẫn:** Bộ môn Toán - Khoa học Dữ liệu  
**Tác giả thực hiện:** Nhóm nghiên cứu Scania APS Cost Optimization  
**Mã nguồn & Repository:** `PhucHuynh16/Predictive-maintenance-cost-optimization`  
**Dữ liệu nghiên cứu:** UCI Machine Learning Repository — Dataset #421: *APS Failure at Scania Trucks*  

---

## TÓM TẮT ĐỀ TÀI (ABSTRACT)

Bảo trì dự đoán (Predictive Maintenance - PdM) trong ngành vận tải hạng nặng đóng vai trò sống còn trong việc giảm thiểu thời gian xe dừng hoạt động đột xuất (unscheduled downtime) và tối ưu hóa ngân sách bảo dưỡng. Đề tài tập trung giải quyết bài toán tối ưu hóa chi phí vận hành phi đối xứng trên hệ thống khí nén (Air Pressure System - APS) của xe tải hạng nặng Scania dựa trên tập dữ liệu chuẩn UCI 421 (gồm 60.000 mẫu huấn luyện và 16.000 mẫu kiểm thử với 170 thuộc tính kỹ thuật ẩn danh).

Điểm mấu chốt của bài toán nằm ở sự bất đối xứng cực lớn về mặt kinh tế: chi phí bỏ sót hư hỏng hệ thống APS dẫn đến sự cố dọc đường (False Negative - FN) là 500 đơn vị chi phí, trong khi chi phí kiểm tra định kỳ không cần thiết tại xưởng (False Positive - FP) chỉ là 10 đơn vị chi phí (tỷ lệ $50:1$). Đồng thời, hệ thống vận hành thực tế chịu **ràng buộc năng lực xưởng bảo dưỡng** nghiêm ngặt: tổng số lượng xe được phân bổ kiểm tra dự phòng tại mỗi chu kỳ bảo dưỡng không được vượt quá 10% quy mô đội xe ($M \le \lfloor N/10 \rfloor$).

Đề tài thiết lập một quy trình thực nghiệm khoa học, nghiêm ngặt và có khả năng tái lập 100%:
1. Khóa phân chia dữ liệu Train (48.000 mẫu) / Validation (12.000 mẫu) và **niêm phong tuyệt đối tập Official Test** (16.000 mẫu) cho đến giai đoạn đánh giá cuối cùng.
2. Thiết lập đường cơ sở (Baselines): Mô hình đa số B0 (Majority Dummy), Cây quyết định gốc B1 (Decision Stump depth=1), và Hồi quy Logistic chuẩn hóa B2 (Logistic Regression L-BFGS).
3. Đề xuất mô hình Rừng ngẫu nhiên (Random Forest) kết hợp thuật toán tối ưu hóa siêu tham số và ngưỡng Bayesian Tree-structured Parzen Estimator (Optuna TPE) nhằm tìm kiếm điểm cực tiểu toàn cục của hàm chi phí trong không gian nghiệm khả thi của ràng buộc năng lực xưởng.

---

## 1. GIỚI THIỆU & ĐẶT VẤN ĐỀ

### 1.1. Bối cảnh công nghiệp
Hệ thống khí nén (Air Pressure System - APS) trên xe tải hạng nặng chịu trách nhiệm điều khiển phanh khí nén, hệ thống treo và hỗ trợ ly hợp. Hư hỏng bất ngờ của hệ thống APS khi xe đang vận hành trên đường cao tốc không chỉ gây nguy hiểm nghiêm trọng về an toàn giao thông mà còn dẫn đến chi phí kéo xe, chậm giao hàng và tổn thất thương mại cực kỳ đắt đỏ.

### 1.2. Thách thức kỹ thuật
- **Mất cân bằng dữ liệu cực đoan:** Tỷ lệ hư hỏng APS thực tế chỉ chiếm khoảng 1.67% (1.000 ca hỏng / 60.000 xe trong tập Train chính thức).
- **Thiếu dữ liệu diện rộng (Missing Data):** Hầu hết các cảm biến đều có giá trị khuyết thiếu do hạn chế phần cứng hoặc thời gian đọc cảm biến khác nhau, đòi hỏi chiến lược tiền xử lý không gây rò rỉ dữ liệu (data leakage).
- **Hàm chi phí phi đối xứng nghiêm ngặt:** Đánh đổi giữa việc cảnh báo sớm (chấp nhận FP để giảm FN) nhưng phải tuân thủ trần năng lực xưởng sửa chữa.

---

## 2. PHÁT BIỂU TOÁN HỌC & MÔ HÌNH HÀM MỤC TIÊU

### 2.1. Không gian bài toán
Cho tập quan sát $X = \{x_i\}_{i=1}^N \subset \mathbb{R}^d$ ($d=170$) và nhãn thực tế $Y = \{y_i\}_{i=1}^N \subset \{0, 1\}$, trong đó:
- $y_i = 1$ (positive): Xe thực sự bị lỗi hệ thống APS.
- $y_i = 0$ (negative): Xe hoạt động bình thường hoặc lỗi không thuộc APS.

Một chính sách bảo dưỡng đưa ra hành động can thiệp $A = \{a_i\}_{i=1}^N \subset \{0, 1\}$:
- $a_i = 1$: Đưa xe vào xưởng kiểm tra APS.
- $a_i = 0$: Cho phép xe tiếp tục vận hành.

### 2.2. Ma trận chi phí kinh tế (Cost Matrix)
Chi phí phát sinh cho từng trường hợp $(y, a)$ được định nghĩa theo bảng chi phí chuẩn của chuẩn Scania benchmark:

$$\mathcal{C}(y, a) = \begin{cases} 0 & \text{nếu } y=0, a=0 \text{ (True Negative - TN)} \\ 10 & \text{nếu } y=0, a=1 \text{ (False Positive - FP, chi phí kiểm tra tại xưởng)} \\ 500 & \text{nếu } y=1, a=0 \text{ (False Negative - FN, chi phí cứu hộ & sự cố APS)} \\ 0 & \text{nếu } y=1, a=1 \text{ (True Positive - TP, sửa chữa đúng bệnh)} \end{cases}$$

Tổng chi phí bảo dưỡng trên toàn bộ tập dữ liệu kích thước $N$:

$$\text{Total Cost} = 10 \cdot \sum_{i=1}^N (1 - y_i) a_i + 500 \cdot \sum_{i=1}^N y_i (1 - a_i) = 10 \cdot FP + 500 \cdot FN$$

### 2.3. Ràng buộc năng lực bảo dưỡng (Capacity Constraint)
Trong một chu kỳ bảo dưỡng nhất định, trạm dịch vụ có năng lực tiếp nhận tối đa $K$ lượt xe, được xác định bằng 10% quy mô phân vùng:

$$K = \left\lfloor \frac{N}{10} \right\rfloor$$

Tổng số hành động can thiệp $M = \sum_{i=1}^N a_i = TP + FP$ phải thỏa mãn:

$$M \le K \iff TP + FP \le \left\lfloor \frac{N}{10} \right\rfloor$$

Nếu $M > K$, chính sách bảo dưỡng bị coi là **Không khả thi (INFEASIBLE)** trong vận hành thực tế.

### 2.4. Bài toán tối ưu hóa tổng thể
$$\begin{aligned}
\min_{\theta, \tau} \quad & J(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \\
\text{s.t.} \quad & M(\theta, \tau) \le \left\lfloor \frac{N}{10} \right\rfloor \\
& a_i = \mathbb{I}[P(y_i=1 \mid x_i; \theta) \ge \tau], \quad \forall i=1,\dots,N \\
& \tau \in (0, 1)
\end{aligned}$$

---

## 3. DỮ LIỆU & GIAO THỨC TIỀN XỬ LÝ (G3 DATASET)

### 3.1. Phân vùng dữ liệu đã khóa (Locked Partitions)
Theo giao thức G3 đã được nghiệm thu (Manifest hash: `efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`):
- **Official Train Set (60.000 mẫu):**
  - **Train partition:** 48.000 mẫu (800 ca dương tính, 47.200 ca âm tính - tỷ lệ $1.67\%$).
  - **Validation partition:** 12.000 mẫu (200 ca dương tính, 11.800 ca âm tính - tỷ lệ $1.67\%$).
  - Năng lực bảo dưỡng trên tập Validation: $K = \lfloor 12000 / 10 \rfloor = 1200$ lượt xe.
- **Official Test Set (16.000 mẫu):**
  - **Niêm phong tuyệt đối (STRICTLY SEALED UNTIL G10)**. Không được đọc, giải nén, tiền xử lý hay kiểm tra trước khi mô hình tối ưu hoàn tất.

### 3.2. Đường ống tiền xử lý không rò rỉ (Strict Train-Only Fitting)
Toàn bộ tham số thống kê (giá trị trung vị để điền khuyết thiếu `SimpleImputer(strategy='median')`, trung bình và độ lệch chuẩn để co dãn `StandardScaler()`) được tính toán **duy nhất trên 48.000 mẫu Train**. Sau đó áp dụng phép chuyển đổi tĩnh (transform-only) lên 12.000 mẫu Validation.

---

## 4. HỆ THỐNG MÔ HÌNH ĐƯỜNG CƠ SỞ (BASELINES - G4)

| Ký hiệu | Mô hình | Kiến trúc & Tham số khóa | Mục đích so sánh |
|---|---|---|---|
| **B0** | Majority Dummy Classifier | Dự đoán toàn bộ $a_i = 0$ (Không can thiệp gì) | Đo lường chi phí trần khi bỏ mặc rủi ro ($500 \times FN$) |
| **B1** | Decision Stump | `DecisionTreeClassifier(max_depth=1, random_state=42)` | Mô hình cây 1 tầng đơn giản nhất, kiểm tra độ phân tách của biến đơn |
| **B2** | Logistic Regression | `LogisticRegression(penalty='l2', C=1.0, solver='lbfgs', max_iter=2000, random_state=42)` | Mô hình tuyến tính chuẩn tắc sau tiền xử lý co dãn |

Các ngưỡng quyết định được đánh giá cho B1 và B2:
- Ngưỡng chuẩn xác suất: $\tau_1 = 0.5$ (Primary threshold).
- Ngưỡng tối ưu lý thuyết Bayes (Cost-ratio threshold):
  $$\tau_2 = \frac{C_{FP}}{C_{FP} + C_{FN}} = \frac{10}{10 + 500} = \frac{10}{510} \approx 0.0196078$$

---

## 5. MÔ HÌNH ĐỀ XUẤT: RANDOM FOREST & TỐI ƯU HÓA OPTUNA TPE (G5)

### 5.1. Kiến trúc Random Forest cho dữ liệu mất cân bằng
Sử dụng tổ hợp nhiều cây quyết định với cơ chế lấy mẫu ngẫu nhiên (Bagging) và chọn lọc ngẫu nhiên tập thuộc tính, giúp giảm phương sai và nắm bắt các quan hệ phi tuyến phức tạp giữa 170 cảm biến APS.

### 5.2. Không gian siêu tham số và tối ưu hóa Optuna TPE
Sử dụng thuật toán **Tree-structured Parzen Estimator (TPE)** của thư viện Optuna để tối ưu hóa đồng thời:
1. Số lượng cây (`n_estimators` $\in [50, 300]$).
2. Độ sâu tối đa (`max_depth` $\in [5, 25]$).
3. Trọng số lớp (`class_weight` $\in \{\text{'balanced'}, \text{'balanced_subsample'}, \dots\}$).
4. Ngưỡng quyết định hành động $\tau \in [0.01, 0.50]$.
Hàm mục tiêu của Optuna được phạt vô hạn nếu vi phạm ràng buộc $M > 1200$.

---

## 6. KẾT QUẢ THỰC NGHIỆM TRÊN TẬP VALIDATION (12.000 MẪU)

*(Mục này sẽ tự động cập nhật bảng kết quả thực tế ngay khi có sự phê duyệt Gate B2 và hoàn thành chạy thực nghiệm G4/G5).*

### 6.1. Bảng so sánh chi phí và tính khả thi

| Mô hình | Ngưỡng $\tau$ | TP | FP | TN | FN | Precision | Recall | Tổng chi phí | Ràng buộc ($M \le 1200$) | Trạng thái |
|---|---|---|---|---|---|---|---|---|---|---|
| B0: Majority Dummy | N/A | 0 | 0 | 11800 | 200 | 0.00% | 0.00% | 100,000 | $M = 0 \le 1200$ | Khả thi |
| B1: Stump | 0.500 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B1: Stump | 0.0196 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B2: Logistic Reg | 0.500 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| B2: Logistic Reg | 0.0196 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
| **Proposed: Random Forest** | $\tau^*$ | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | **Tối ưu** |

---

## 7. ĐÁNH GIÁ TÍNH KHẢ LẬP, GIỚI HẠN & KẾT LUẬN

### 7.1. Bằng chứng tái lập (Reproducibility)
- Toàn bộ thực nghiệm được điều khiển thông qua mã nguồn kiểm thử và kịch bản thực thi cố định seed = 42.
- Kiểm soát tài nguyên chặt chẽ: 1 native thread (`threadpoolctl`), trần bộ nhớ 2048 MB, giới hạn thời gian 120s bằng Windows Job Object.
- Toàn bộ artifact kết quả kèm chữ ký băm SHA-256 trong `checksums.json`.

### 7.2. Kết luận
Đề tài hoàn thành việc thiết lập khung tối ưu hóa chi phí bảo dưỡng khả thi về mặt kỹ thuật và thực tiễn công nghiệp trên tập dữ liệu xe tải Scania APS.
