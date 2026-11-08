# Tối ưu hóa Chi phí Bảo trì Dự đoán Hệ thống Khí nén trên Xe tải nặng Scania (UCI 421)

[![Academic Project](https://img.shields.io/badge/Course-Introduction%20to%20Optimization-blue.svg)](https://www.vlu.edu.vn/)
[![Institution](https://img.shields.io/badge/University-Van%20Lang%20University-red.svg)](https://www.vlu.edu.vn/)
[![Dataset](https://img.shields.io/badge/UCI%20Benchmark-APS%20Failure%20at%20Scania%20Trucks%20%23421-green.svg)](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks)
[![Dataset License](https://img.shields.io/badge/Dataset%20License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python](https://img.shields.io/badge/Python-3.11.9-yellow.svg)](https://www.python.org/)

> **Đồ án cá nhân môn học:** Nhập môn Tối ưu hóa (Introduction to Optimization)  
> **Khoa:** Công nghệ Thông tin — Trường Đại học Văn Lang  
> **Sinh viên thực hiện:** Huỳnh Phúc  
> **Mã nguồn:** [GitHub Repository: PhucHuynh16/Predictive-maintenance-cost-optimization](https://github.com/PhucHuynh16/Predictive-maintenance-cost-optimization)  
>
> *Lưu ý quản trị:* Đây là **Bản dự thảo Portfolio README (Draft README)** dành riêng cho đề tài Scania APS, lưu tại `docs/scania/` để phục vụ đánh giá học thuật và chờ phê duyệt của Chủ dự án trước khi tích hợp vào `README.md` tại thư mục gốc repository.

---

> [!IMPORTANT]
> **RANH GIỚI KHOA HỌC VỀ PHƯƠNG PHÁP TỐI ƯU HÓA:**
> Việc vượt qua các unit tests hoặc thực thi xong các mô hình cơ sở G4 Baselines (B0, B1, B2) **KHÔNG hoàn thành yêu cầu phương pháp tối ưu hóa bắt buộc của học phần**.
> - G4 Baselines chỉ đóng vai trò cung cấp mốc so sánh cơ sở (reference benchmark).
> - Phương pháp tối ưu hóa cốt lõi theo đề tài (Random Forest kết hợp Bayesian Hyperparameter Optimization & Threshold Tuning qua Optuna TPE) là một hạng mục nghiên cứu độc lập (Phase 2), cần được cấp quyền, thực thi và lưu trữ lịch sử tìm kiếm (search history) cùng đồ thị hội tụ/đánh đổi riêng biệt.

---

## 1. ĐẶT VẤN ĐỀ & BỐI CẢNH CÔNG NGHIỆP

Hệ thống khí nén (Air Pressure System - APS) trên các dòng xe tải hạng nặng đóng vai trò đặc biệt quan trọng, cung cấp áp suất khí để điều khiển hệ thống phanh khí nén, cơ cấu trợ lực ly hợp và điều hòa áp suất gầm. Hư hỏng đột ngột của hệ thống APS khi xe đang vận hành trên tuyến vận tải đường dài dẫn đến nguy cơ bó phanh khẩn cấp, gây mất an toàn giao thông nghiêm trọng, làm ngưng trệ chuỗi cung ứng logistics và phát sinh chi phí kéo xe, sửa chữa khẩn cấp rất lớn.

### Ngữ nghĩa chuẩn xác về dữ liệu (UCI Dataset #421)
Tập dữ liệu chuẩn công nghiệp [APS Failure at Scania Trucks (UCI #421)](https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks) được công bố bởi Scania CV AB tại Hội nghị IDA 2016, bao gồm 60.000 bản ghi huấn luyện và 16.000 bản ghi kiểm thử với 170 thuộc tính cảm biến đo đạc từ các trạm dịch vụ.

Cần nhấn mạnh **ngữ nghĩa chính xác của hai lớp dữ liệu** theo tài liệu kỹ thuật gốc của UCI:
- **Lớp dương tính (Positive class, $y=1$):** Các xe vào xưởng dịch vụ được chẩn đoán chính xác là gặp sự cố do hư hỏng các thành phần thuộc hệ thống khí nén APS (chiếm tỷ lệ $1.67\%$ trong tập huấn luyện).
- **Lớp âm tính (Negative class, $y=0$):** **Các xe gặp sự cố hỏng hóc ở các bộ phận KHÁC KHÔNG THUỘC APS** (ví dụ: động cơ, hệ thống điện tử, hộp số). Đây **KHÔNG PHẢI** là các xe "hoàn toàn khỏe mạnh" (healthy trucks). Mọi xe trong bộ dữ liệu đều là xe cần sửa chữa; mục tiêu của hệ thống là phân loại chính xác xem xe có cần quy trình kiểm tra tháo lắp chuyên sâu APS hay không.

---

## 2. PHÁT BIỂU TOÁN HỌC & MÔ HÌNH HÓA TỐI ƯU CÓ RÀNG BUỘC

Bài toán được mô hình hóa thành một bài toán **Tối ưu hóa toán học có ràng buộc tài nguyên** với hàm mục tiêu chi phí phi đối xứng nghiêm ngặt.

### 2.1. Biến quyết định
Với mỗi quan sát xe $x_i \in \mathbb{R}^{170}$, mô hình phân loại ước lượng xác suất hậu nghiệm $P(y_i = 1 \mid x_i; \theta)$. Chính sách can thiệp đưa ra hành động nhị phân $a_i \in \{0, 1\}$ thông qua ngưỡng phân loại $\tau \in [0, 1]$:
$$a_i(\theta, \tau) = \mathbb{I}[P(y_i = 1 \mid x_i; \theta) \ge \tau]$$
- $a_i = 1$: Đưa xe vào luồng kiểm tra chuyên sâu hệ thống APS tại xưởng.
- $a_i = 0$: Không đưa vào luồng kiểm tra APS (xử lý các sự cố khác và xuất xưởng).

Không gian biến quyết định cần tìm là $(\theta, \tau) \in \Theta \times [0, 1]$.

### 2.2. Hàm mục tiêu chi phí benchmark phi đối xứng
Theo đặc tả của Scania CV AB, ma trận chi phí quy ước cho từng kết quả phân loại:
- **False Positive (FP):** Kiểm tra thừa khi xe hỏng bộ phận khác $\to$ Tốn thời gian kiểm tra tại xưởng: **$10$ đơn vị chi phí benchmark** (Cost Units).
- **False Negative (FN):** Bỏ sót lỗi APS dẫn đến xe chết máy dọc đường $\to$ Cứu hộ khẩn cấp: **$500$ đơn vị chi phí benchmark** (tỷ số phạt $50:1$).
- **True Positive (TP) & True Negative (TN):** Xử lý chính xác $\to$ **$0$ đơn vị chi phí benchmark**.

Hàm mục tiêu chi phí tổng thể trên phân vùng $N$ xe:
$$f(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \quad [\text{benchmark cost units}]$$

> **Lưu ý khoa học:** Hàm chi phí $10 \cdot FP + 500 \cdot FN$ được tính bằng **đơn vị chi phí benchmark chuẩn hóa**, không phải số tiền tệ thực tế (USD/VND) và không cấu thành cam kết lợi nhuận bằng tiền mặt trong sản xuất thực tế.

### 2.3. Ràng buộc năng lực bảo dưỡng (Maintenance Capacity Assumption)
Để mô phỏng giới hạn vận hành thực tế tại trạm dịch vụ (giới hạn về nhân lực chuyên gia APS và thiết bị đo áp suất), đề tài thiết lập **giả định kịch bản vận hành**:
$$M(\theta, \tau) = \sum_{i=1}^N a_i(\theta, \tau) = TP + FP \le K = \left\lfloor \frac{N}{10} \right\rfloor$$
- Trên phân vùng Validation ($N = 12.000$ mẫu): $K_{\text{val}} = \lfloor 12000 / 10 \rfloor = 1.200$ lượt xe.
- Chính sách có $M > 1200$ bị coi là **Không khả thi (INFEASIBLE)**.

### 2.4. Bài toán tối ưu hoàn chỉnh
$$\begin{aligned}
\min_{\theta \in \Theta, \, \tau \in [0, 1]} \quad & f(\theta, \tau) = 10 \cdot FP(\theta, \tau) + 500 \cdot FN(\theta, \tau) \\
\text{subject to} \quad & g(\theta, \tau) = TP(\theta, \tau) + FP(\theta, \tau) - 1200 \le 0
\end{aligned}$$

---

## 3. PHÂN TÍCH LÝ THUYẾT: NGƯỠNG TỶ LỆ CHI PHÍ BAYES

Theo lý thuyết quyết định Bayes (Bayesian Decision Theory), khi chi phí phi đối xứng và xác suất hậu nghiệm được hiệu chuẩn hoàn hảo, hành động $a=1$ tối ưu khi kỳ vọng chi phí can thiệp nhỏ hơn không can thiệp:
$$P(y=1 \mid x) \ge \tau^*_{\text{Bayes}} = \frac{C_{FP}}{C_{FP} + C_{FN}} = \frac{10}{10 + 500} = \frac{10}{510} \approx 0.0196078$$

> **Phân định khoa học cốt lõi:**
> 1. $\tau = 10/510$ là nghiệm tối ưu lý thuyết **TRONG ĐIỀU KIỆN KHÔNG CÓ RÀNG BUỘC CÔNG SUẤT ($M \le K$)**.
> 2. Khi áp dụng ràng buộc năng lực xưởng $M \le 1200$, việc hạ ngưỡng xuống $0.0196$ có thể kéo theo số lượng cảnh báo $M = TP + FP$ vượt ngưỡng $1.200$, làm phương án trở nên **vi phạm ràng buộc (INFEASIBLE)**.
> 3. Do đó, ngưỡng tối ưu thực tế phải được tìm kiếm thông qua quy trình tối ưu hóa có điều kiện trên phân vùng Validation.

---

## 4. GIAO THỨC DỮ LIỆU & PHÒNG CHỐNG RÒ RỈ (G3 / G4)

Dữ liệu được khóa cố định theo G3 stable manifest (`efe781b7e564073a2a764e70a41cfe5c3e8975d33cc38b0fa297ef09f51767bb`):

| Phân vùng | Số mẫu | Ca dương ($y=1$) | Tỷ lệ dương | Trạng thái bảo mật |
|---|:---:|:---:|:---:|---|
| **Train** | 48.000 | 800 | 1.67% | Mở phục vụ huấn luyện (fit imputer, scaler, estimators) |
| **Validation** | 12.000 | 200 | 1.67% | Mở phục vụ đánh giá chính sách và tìm ngưỡng $\tau$ |
| **Official Test** | 16.000 | — | — | **NIÊM PHONG TUYỆT ĐỐI (SEALED UNTIL G10)** |

### Quy tắc không rò rỉ dữ liệu (Strict Train-Only Fitting)
- Toàn bộ tham số tiền xử lý gồm trung vị (`SimpleImputer(strategy='median')`) và chuẩn hóa (`StandardScaler`) được tính toán duy nhất trên 48.000 mẫu Train.
- Tuyệt đối không fit tiền xử lý trên toàn bộ tập dữ liệu hoặc trên tập Validation/Test.
- Tập Official Test được bảo vệ bởi hook kiểm tra I/O cấp hệ thống; mọi nỗ lực truy cập vào test set trong giai đoạn G4 đều bị chặn và báo lỗi fail-closed.

---

## 5. MÔ HÌNH ĐƯỜNG CƠ SỞ (BASELINES — G4)

Hệ thống thiết lập 3 mô hình cơ sở nhằm cung cấp mốc tham chiếu so sánh (reference benchmarks):
1. **B0 (Majority Dummy):** Dự đoán $a_i = 0$ cho toàn bộ các quan sát (không can thiệp bảo dưỡng). Chi phí trần lý thuyết: $500 \times 200 = 100.000$ đơn vị chi phí.
2. **B1 (Decision Stump):** Cây quyết định độ sâu 1 (`DecisionTreeClassifier(max_depth=1, random_state=42)`).
3. **B2 (Logistic Regression):** Mô hình tuyến tính chuẩn tắc (`penalty='l2'`, `C=1.0`, `solver='lbfgs'`, `max_iter=2000`, `random_state=42`).

Mỗi mô hình học máy (B1, B2) được đánh giá tại 2 ngưỡng xác suất cố định:
- Ngưỡng chuẩn: $\tau = 0.5000$.
- Ngưỡng tỷ lệ chi phí Bayes lý thuyết: $\tau = 10/510 \approx 0.0196$.

---

## 6. KẾT QUẢ THỰC NGHIỆM ĐƯỜNG CƠ SỞ TRÊN VALIDATION (GATE B2 HOÀN TẤT)

Tuân thủ nguyên tắc liêm chính học thuật, đề tài phân biệt rõ 4 cấp độ dữ liệu:
- **Lý thuyết:** Công thức giải tích $\tau = 10/510 \approx 0.0196$ và chi phí trần B0 ($100.000$).
- **Kiểm thử tổng hợp (Synthetic):** Dữ liệu giả lập chạy kiểm thử tự động hệ thống điều phối, không đại diện cho xe Scania.
- **Thực nghiệm Validation thật (Real Scania):** Đã hoàn tất thực thi tại lượt chạy được cấp quyền `scania_g4_b2_real_002` trên 12.000 mẫu Validation.
- **Official Test thật:** Niêm phong tuyệt đối (Sealed until G10).

### Bảng kết quả thực nghiệm 5 chính sách cố định (`scania_g4_b2_real_002`)

| Chính sách | Mô hình | Ngưỡng $\tau$ | TP | FP | TN | FN | Chi phí benchmark | Số xe vào xưởng ($M$) | Trạng thái ($M \le 1200$) | Mức tiết kiệm vs B0 |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P1** | **B0:** Majority Dummy | N/A | 0 | 0 | 11.800 | 200 | **100.000** | $0$ | **Khả thi** | $0.00\%$ |
| **P2** | **B1:** Decision Stump | 0.5000 | 0 | 0 | 11.800 | 200 | **100.000** | $0$ | **Khả thi** | $0.00\%$ |
| **P3** | **B1:** Decision Stump | 0.0196 | 160 | 253 | 11.547 | 40 | **22.530** | $413$ | **Khả thi** | **+77.47%** |
| **P4** | **B2:** Logistic Regression | 0.5000 | 129 | 48 | 11.752 | 71 | **35.980** | $177$ | **Khả thi** | **+64.02%** |
| **P5** | **B2:** Logistic Regression | 0.0196 | 186 | 323 | 11.477 | 14 | **10.230** | $509$ | **Khả thi** | **+89.77%** |

### Nhận xét phân tích kết quả Gate B2
1. **Mô hình đường cơ sở tốt nhất:** Logistic Regression tại $\tau = 10/510 \approx 0.0196$ (P5) đạt chi phí **10.230 đơn vị chi phí benchmark**, giảm **+89.77%** chi phí so với mô hình mặc định B0 ($100.000$), phát hiện chính xác 186/200 ca lỗi APS (Recall 93.0%).
2. **Kiểm chứng tính khả thi của ràng buộc:** Số xe can thiệp kiểm tra $M = 509$ xe, hoàn toàn nằm trong giới hạn công suất tiếp nhận $K = 1.200$ xe ($42.42\%$ công suất cho phép).
3. **Hiệu năng thực thi & Tính tái lập:**
   - Thực thi đúng 2 lượt fit thực tế (`real_estimator_fits=2`: B1=1, B2=1, B0=0).
   - Thời gian fit: $1.417$ giây; tổng thời gian tiến trình: $6.06$ giây.
   - Mức chiếm dụng bộ nhớ đỉnh (Peak RAM): $201.90$ MB (thỏa mãn trần tài nguyên $2048$ MB).
   - Toàn bộ 11 artifacts kết quả tại `results/scania_aps/g4/scania_g4_b2_real_002/` được kiểm chứng toàn vẹn mật mã với `verify_run() == True`. Lượt chạy không thành công trước đó (`001`) được giữ nguyên vẹn để phục vụ thanh tra học thuật.

---

## 7. CẤU TRÚC THƯ MỤC REPOSITORY

```text
├── configs/
│   └── scania/
│       ├── g4_baselines.json        # Cấu hình siêu tham số và ngưỡng cho baselines
│       └── g3_requirements.lock.txt # Khóa phiên bản thư viện môi trường
├── data/
│   ├── README.md                    # Hướng dẫn dữ liệu và phân vùng
│   ├── raw/                         # Dữ liệu gốc (được gitignore bảo vệ)
│   └── processed/scania_aps/        # Phân vùng train/validation đã khóa G3
├── docs/
│   ├── scania/
│   │   ├── SCANIA_PORTFOLIO_README.md    # Dự thảo Portfolio README đề tài Scania
│   │   ├── academic_compliance_matrix.md # Bảng đối chiếu 22 tiêu chí học thuật
│   │   ├── problem_formulation.md        # Đặc tả toán học bài toán tối ưu
│   │   ├── cost_model_review.md          # Phân tích mô hình chi phí và ví dụ
│   │   └── experimental_protocol.md      # Giao thức thực nghiệm không rò rỉ
│   ├── ROADMAP.md                   # Lộ trình 10 giai đoạn
│   └── TASK_BOARD.md                # Bảng theo dõi tiến độ công việc
├── notebooks/
│   └── 01_eda.ipynb                 # Phân tích khám phá dữ liệu (EDA)
├── report/
│   └── BAO_CAO_CUOI_KY_SCANIA_APS.md # Dự thảo báo cáo tổng kết đồ án (8-12 trang)
├── slides/
│   └── SLIDES_THUYET_TRINH_SCANIA_APS.md # Dự thảo đề cương 7 slide thuyết trình
├── src/
│   └── scania/
│       ├── data_pipeline.py         # Pipeline nạp và tiền xử lý dữ liệu
│       ├── g4_baseline_runner.py    # Module thực thi các mô hình cơ sở
│       └── g4_b2_executor.py        # Bộ điều phối thực thi Gate B2 an toàn
├── tests/
│   └── scania/                      # Bộ kiểm thử 271 unit tests toàn diện
└── requirements.txt                 # Khai báo môi trường và thư viện
```

---

## 8. HƯỚNG DẪN CÀI ĐẶT & TÁI LẬP (REPRODUCIBILITY)

### 8.1. Khởi tạo môi trường
Yêu cầu Python 3.11.x:
```bash
# Tạo môi trường ảo độc lập
python -m venv .venv
source .venv/bin/activate  # Trên Linux/macOS
# .venv\Scripts\activate   # Trên Windows

# Cài đặt các gói phụ thuộc đã khóa
pip install -r requirements.txt
```

### 8.2. Chạy bộ kiểm thử tự động (271 Scania Tests)
```bash
pytest tests/scania/ -v
```

### 8.3. Thực thi thực nghiệm Gate B2 (Đã hoàn thành)
Lệnh thực thi chính thức qua CLI hỗ trợ đã thực hiện:
```bash
python -m scripts.run_scania_baselines gate-b2 --run-id scania_g4_b2_real_002
```
*Điều kiện tiên quyết:* Bộ điều phối yêu cầu tệp xác thực `configs/scania/authorizations/scania_g4_b2_real_002.json` chứa liên kết tham chiếu URL tới comment phê duyệt chính thức của Chủ dự án trên GitHub Issue #17.

---

## 9. GIỚI HẠN NGHIÊN CỨU & KHAI BÁO BẢN QUYỀN

### 9.1. Giới hạn nghiên cứu (Limitations)
1. **Bản chất mô phỏng chính sách:** Hàm chi phí được tính toán trên dữ liệu tĩnh lịch sử, không phản ánh tác động can thiệp bảo trì dài hạn trong môi trường động.
2. **Giả định ràng buộc năng lực:** Mức trần 10% ($M \le 1200$) là một giả định kịch bản thiết kế bài toán học thuật, không đại diện cho năng lực vận hành thực tế của các xưởng Scania.
3. **Phạm vi mô hình:** Đợt thử nghiệm G4 chỉ khảo sát các mô hình cơ sở tuyến tính và cây quyết định đơn giản; các mô hình tối ưu hóa tiên tiến (Random Forest + Optuna HPO) thuộc về Phase 2.

### 9.2. Phân định bản quyền & Giấy phép
- **Mã nguồn đồ án:** Dự án học thuật cá nhân phục vụ môn học Nhập môn Tối ưu hóa, Trường Đại học Văn Lang.
- **Tập dữ liệu nghiên cứu:** *APS Failure at Scania Trucks* (UCI Dataset #421), bản quyền thuộc Scania CV AB (2016), công bố theo giấy phép [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

### 9.3. Khai báo công cụ hỗ trợ (AI Assistance Disclosure)
Tuân thủ Mục 10 của Quy định bài tập lớn cá nhân:
- **Công cụ AI sử dụng:** Trợ lý AI (Codex và Google Antigravity) được sử dụng để hỗ trợ rà soát cú pháp mã nguồn, xây dựng các kịch bản kiểm thử biên (unit tests), hỗ trợ thiết kế cấu trúc thư mục và định dạng tài liệu.
- **Phần sinh viên tự thực hiện và chịu trách nhiệm toàn diện:**
  - Thiết lập mô hình toán học, định nghĩa biến quyết định, hàm mục tiêu và ràng buộc.
  - Phân tích ngữ nghĩa lớp dữ liệu theo tài liệu gốc Scania UCI #421.
  - Thiết kế và kiểm chứng giao thức phòng chống rò rỉ dữ liệu (niêm phong tập Test).
  - Trực tiếp nghiệm thu và chịu trách nhiệm về toàn bộ kết quả, báo cáo và bảo vệ đề tài.
