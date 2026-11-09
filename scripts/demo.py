"""
Dự án: Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS (UCI 421)
Học phần: Nhập môn Tối ưu hóa — Trường Đại học Văn Lang
Tác giả: Huỳnh Phúc
Mục đích: Script demo thuyết trình và kiểm tra nghiệm thu nhanh (5-7 phút bảo vệ)
Nguyên tắc: Đọc kết quả đã nghiệm thu (READ-ONLY), KHÔNG fit lại mô hình, KHÔNG truy cập Test.
"""

import sys
import os
import json
import argparse

sys.stdout.reconfigure(encoding="utf-8")

def print_banner():
    print("=" * 80)
    print("  ĐỒ ÁN NHẬP MÔN TỐI ƯU HÓA — BẢO TRÌ DỰ ĐOÁN SCANIA APS (UCI #421)")
    print("  Quy trình Demo & Báo cáo Thuyết trình Bảo vệ Cá nhân (5–7 Phút)")
    print("=" * 80)

def step_1_problem_formulation():
    print("\n[PHẦN 1] BÀI TOÁN & MÔ HÌNH HÓA TOÁN HỌC TỐI ƯU CÓ RÀNG BUỘC")
    print("-" * 80)
    print("• Bối cảnh: Đội xe tải Scania, phát hiện sớm hư hỏng hệ thống khí nén (APS).")
    print("• Bộ dữ liệu: UCI #421 (60.000 Train/Validation, 16.000 Test, 170 cảm biến).")
    print("• Hàm mục tiêu phi đối xứng (IDA 2016 Benchmark):")
    print("    min f(theta, tau) = 10 * FP(theta, tau) + 500 * FN(theta, tau)")
    print("    Trong đó: FP tốn 10 đơn vị (kiểm tra thừa), FN tốn 500 đơn vị (chết máy dọc đường).")
    print("• Ràng buộc công suất xưởng (Maintenance Capacity Constraint):")
    print("    M(theta, tau) = TP + FP <= K = floor(N / 10)")
    print("    - Trên Validation (N = 12.000): K = 1.200 lượt xe.")
    print("    - Trên Official Test (N = 16.000): K = 1.600 lượt xe.")

def step_2_baselines():
    print("\n[PHẦN 2] HỆ THỐNG ĐƯỜNG CƠ SỞ (G4 BASELINES TRÊN 12.000 MẪU VALIDATION)")
    print("-" * 80)
    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    print("  | Mã | Mô hình              | Ngưỡng  |  TP |  FP | FN |   Chi phí | Xe vào M | Trạng thái|")
    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    print("  | B0 | Majority Dummy (a=0) |   N/A   |   0 |   0 |200 | 100.000|       0 | Khả thi   |")
    print("  | B1 | Decision Stump       |  0.0196 | 160 | 253 | 40 |  22.530|     413 | Khả thi   |")
    print("  | B2 | Logistic Regression  |  0.0196 | 186 | 323 | 14 |  10.230|     509 | Khả thi   |")
    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    print("  -> Mốc chi phí chuẩn tắc của G4: C*(G4) = 10.230 đơn vị (Mô hình B2).")

def step_3_phase2_optimization():
    print("\n[PHẦN 3] TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RANDOM FOREST + OPTUNA TPE)")
    print("-" * 80)
    print("• Không gian tìm kiếm: n_estimators [20..60], max_depth [4..12], max_features [0.25..0.50].")
    print("• Ngân sách thực nghiệm: 20 trials tuần tự, 1 native thread, trần thời gian 900s.")
    print("• Quét ngưỡng vector hóa (Threshold tuning): 101 điểm từ 0.00 đến 1.00 trên Validation.")
    print("\n• CHÍNH SÁCH TỐI ƯU KHẢ THI QUAN SÁT ĐƯỢC (TRIAL 16):")
    print("    - Siêu tham số: n_estimators=50, max_depth=10, min_samples_split=10, max_features=0.427")
    print("    - Ngưỡng tối ưu: tau* = 0.323244")
    print("    - Kết quả Validation: TP=195/200 (Recall 97.50%), FP=383, FN=5 (chỉ lọt 5 xe chết máy)")
    print("    - Tổng chi phí: 10 * 383 + 500 * 5 = 6.330 đơn vị chi phí benchmark")
    print("    - Năng lực xưởng: M = 578 <= 1.200 (Khả thi, xưởng còn dư 622 chỗ)")
    print("    - Hiệu quả: Tiết kiệm 93.67% vs B0 (100k), cắt giảm thêm 38.12% vs B2 (10.230).")
    print("• Độ nhạy ngưỡng (Sensitivity): Vùng lân cận [0.20, 0.35] có chi phí ổn định [6.330, 7.000].")

def step_4_official_test_g10():
    print("\n[PHẦN 4] ĐÁNH GIÁ ĐỘC LẬP TẬP OFFICIAL TEST (GATE G10 — RUN 003)")
    print("-" * 80)
    print("• Quy trình: Khóa chính sách Trial 16, refit đúng 1 lần trên Train 48k, zero tuning trên Test.")
    print("• Quy mô Test: 16.000 mẫu độc lập (375 ca hỏng APS 2.34%, 15.625 ca âm tính 97.66%).")
    print("\n  +-------------------------------+-------------------+-----------------------+")
    print("  | Tiêu chí đo đạc               | Mặc định B0 (Test)| Official Test (G10)   |")
    print("  +-------------------------------+-------------------+-----------------------+")
    print("  | True Positives (TP)           |                 0 |                   357 |")
    print("  | False Positives (FP)          |                 0 |                   484 |")
    print("  | False Negatives (FN)          |               375 |                    18 |")
    print("  | True Negatives (TN)           |            15.625 |                15.141 |")
    print("  | Recall (Độ nhạy)              |             0.00% |     95.20% (357/375)  |")
    print("  | Precision (Độ chính xác)      |               N/A |     42.45% (357/841)  |")
    print("  | Specificity (Độ đặc hiệu)     |           100.00% |     96.90% (15.1k/15.6k)|")
    print("  | ROC-AUC / PR-AUC              |               N/A |       0.9861 / 0.7495 |")
    print("  | Chi phí kiểm tra (10 * FP)    |                 0 |                 4.840 |")
    print("  | Chi phí sự cố (500 * FN)      |           187.500 |                 9.000 |")
    print("  | TỔNG CHI PHÍ BENCHMARK        |           187.500 |                13.840 |")
    print("  | Mức tiết kiệm chi phí         |    0.00% (Chuẩn)  |   92.62% (-173.660 đv)|")
    print("  | Số xe vào xưởng (M <= 1.600)  |                 0 |        841 (DƯ 759 CHỖ)|")
    print("  | Trạng thái ràng buộc          |          FEASIBLE |     FEASIBLE (KHẢ THI)|")
    print("  +-------------------------------+-------------------+-----------------------+")
    print("\n• MINH BẠCH HỌC THUẬT & PHÂN BIỆT THỰC ĐỊA:")
    print("  1. Truy cập Test ở Runs 001/002: Tệp test CSV được nạp vào RAM nhưng tiến trình dừng ngay")
    print("     tại chốt kiểm tra preprocessor; tuyệt đối không có dự đoán hay tinh chỉnh nào.")
    print("  2. Benchmark vs Thực tế: Chi phí 13.840 tính theo chuẩn benchmark tĩnh IDA 2016 (10*FP+500*FN).")
    print("     Triển khai thực tế trên đội xe cần bổ sung điều độ động, phụ tùng và chi phí thợ.")

def step_5_verification():
    print("\n[PHẦN 5] XÁC THỰC CHỮ KÝ SỐ MẬT MÃ HỌC SHA-256 (READ-ONLY)")
    print("-" * 80)
    g10_manifest = "results/scania_aps/g10/scania_g10_official_test_003/stable_manifest.json"
    if os.path.exists(g10_manifest):
        with open(g10_manifest, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        print(f"• Tìm thấy Stable Manifest G10 ({len(manifest)} artifacts).")
        import hashlib
        all_pass = True
        base_dir = "results/scania_aps/g10/scania_g10_official_test_003"
        for fname, exp_hash in manifest.items():
            fpath = os.path.join(base_dir, fname)
            if not os.path.exists(fpath):
                print(f"  [MISSING] {fname}")
                all_pass = False
                continue
            with open(fpath, "rb") as f:
                c = f.read().replace(b"\r\n", b"\n")
            act_hash = hashlib.sha256(c).hexdigest()
            status = "PASS" if act_hash == exp_hash else "MISMATCH"
            if status != "PASS":
                all_pass = False
            print(f"  [{status}] {fname:<35} SHA-256: {act_hash[:16]}...")
        if all_pass:
            print("\n  >>> KẾT LUẬN: 100% ARTIFACTS GATE G10 ĐƯỢC XÁC THỰC CHÍNH HÃNG SHA-256 <<<")
    else:
        print("• Không tìm thấy stable manifest G10 tại đường dẫn dự kiến.")

def print_speaker_notes():
    print("\n" + "=" * 80)
    print("  KỊCH BẢN & SPEAKER NOTES BẢO VỆ 5–7 PHÚT (DÀNH CHO SINH VIÊN)")
    print("=" * 80)
    print("""
1. Phút 0:00 - 1:00 | Mở đầu & Bài toán (Slide 1, 2)
   - Kính thưa Hội đồng, em xin trình bày đồ án 'Tối ưu hóa chi phí bảo trì dự đoán xe tải Scania APS'.
   - Đặc thù: Chi phí phi đối xứng nghiêm ngặt 50:1 (FN=500, FP=10). Nếu dùng ngưỡng chuẩn 0.5,
     mô hình bỏ sót nhiều xe hỏng, gây thiệt hại lớn. Nhưng nếu hạ ngưỡng xuống Bayes (0.0196),
     số xe vào xưởng có thể bùng nổ, làm tê liệt trạm bảo dưỡng.
   - Do đó, bài toán được mô hình hóa: Cực tiểu hóa chi phí có ràng buộc công suất xưởng M <= 10% tổng xe.

2. Phút 1:00 - 2:00 | Giao thức dữ liệu & Baseline (Slide 3, 4, 5)
   - Dữ liệu: UCI #421, phân vùng nghiêm ngặt Train 48k / Val 12k; Test 16k niêm phong độc lập.
   - Baseline G4: Thiết lập B0 (không can thiệp, mất 100.000 chi phí), B1 (cây 1 tầng, 22.530),
     và B2 (Logistic Regression, 10.230 đơn vị chi phí).
   - Mốc chuẩn đối sánh cho thuật toán tối ưu là B2 = 10.230 đơn vị.

3. Phút 2:00 - 4:00 | Thuật toán tối ưu Phase 2 & Phân tích Đánh đổi (Slide 6, 7)
   - Phương pháp: Random Forest kết hợp Bayesian Optimization (Optuna TPE) và quét ngưỡng 101 điểm.
   - Kết quả: Tại Trial 16, tìm được cấu hình tốt nhất với tau* = 0.3232, chi phí chỉ 6.330 đơn vị.
   - Tiết kiệm 93.67% chi phí so với B0, và giảm tiếp 38.12% so với baseline tốt nhất B2.
   - Ràng buộc công suất hoàn toàn thỏa mãn: M = 578 <= 1.200 (xưởng còn dư 622 chỗ).
   - Phân tích độ nhạy: Vùng ngưỡng [0.20, 0.35] có lòng chảo chi phí bằng phẳng, rất an toàn khi vận hành.

4. Phút 4:00 - 5:30 | Nghiệm thu Official Test Gate G10 & Tính Tái Lập (Slide 8)
   - Nghiệm thu độc lập: Khi áp dụng lên 16.000 xe tập Official Test hoàn toàn mới, mô hình đạt:
     + Recall 95.20% (bắt đúng 357/375 ca lỗi).
     + Precision 42.45%, Specificity 96.90%.
     + Chi phí chỉ 13.840 đơn vị, tiết kiệm 92.62% chi phí (tiết kiệm 173.660 đơn vị).
     + Số xe vào xưởng: M = 841 <= 1.600 xe (thỏa mãn trọn vẹn ràng buộc).
   - Liêm chính học thuật: Mọi artifacts đều được ký băm SHA-256, không có rò rỉ dữ liệu.
   - Em xin kết thúc phần trình bày và sẵn sàng trả lời câu hỏi của Quý Thầy Cô.
""")

def main():
    parser = argparse.ArgumentParser(description="Demo bảo vệ đồ án Tối ưu hóa Scania APS")
    parser.add_argument("--summary", action="store_true", help="Chỉ in bảng tóm tắt kết quả")
    parser.add_argument("--verify", action="store_true", help="Chỉ chạy kiểm chứng chữ ký băm")
    parser.add_argument("--notes", action="store_true", help="Chỉ in kịch bản và speaker notes 5-7 phút")
    args = parser.parse_args()

    if args.summary:
        print_banner()
        step_2_baselines()
        step_3_phase2_optimization()
        step_4_official_test_g10()
        return

    if args.verify:
        print_banner()
        step_5_verification()
        return

    if args.notes:
        print_speaker_notes()
        return

    # Default: Full interactive defense presentation
    print_banner()
    step_1_problem_formulation()
    step_2_baselines()
    step_3_phase2_optimization()
    step_4_official_test_g10()
    step_5_verification()
    print_speaker_notes()

if __name__ == "__main__":
    main()
