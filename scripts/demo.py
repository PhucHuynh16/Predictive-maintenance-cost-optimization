"""
Dự án: Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS (UCI 421)
Học phần: Nhập môn Tối ưu hóa — Trường Đại học Văn Lang
Tác giả: Nhóm Đồ án Tối ưu hóa — Huỳnh Phúc (MSSV: 2474802010314)
Mục đích: Script demo thuyết trình và kiểm tra nghiệm thu nhanh (5-7 phút bảo vệ)
Nguyên tắc: Đọc kết quả đã nghiệm thu từ artifacts (EVIDENCE-DRIVEN, READ-ONLY).
           KHÔNG fit lại mô hình, KHÔNG chạy tối ưu hóa lại, KHÔNG truy cập dữ liệu Test.
"""

import sys
import os
import json
import csv
import hashlib
import argparse
from pathlib import Path

# Đảm bảo mã hóa UTF-8 trên Windows PowerShell
sys.stdout.reconfigure(encoding="utf-8")

# Định nghĩa các đường dẫn artifact chính thức
BASE_DIR = Path(__file__).resolve().parent.parent
G4_BASELINE_PATH = BASE_DIR / "results" / "scania_aps" / "g4" / "scania_g4_b2_real_002" / "baseline_metrics.json"
PHASE2_BEST_POLICY_PATH = BASE_DIR / "results" / "scania_aps" / "phase2" / "scania_phase2_rf_optuna_002" / "best_policy.json"
PHASE2_TRIAL16_PATH = BASE_DIR / "results" / "scania_aps" / "phase2" / "scania_phase2_rf_optuna_002" / "durable_fits" / "trial_016_result.json"
G10_TEST_METRICS_PATH = BASE_DIR / "results" / "scania_aps" / "g10" / "scania_g10_official_test_003" / "test_metrics.json"
G10_CM_PATH = BASE_DIR / "results" / "scania_aps" / "g10" / "scania_g10_official_test_003" / "confusion_matrix_test.csv"
G10_MANIFEST_PATH = BASE_DIR / "results" / "scania_aps" / "g10" / "scania_g10_official_test_003" / "stable_manifest.json"

FIG_CONVERGENCE = BASE_DIR / "figures" / "optimization" / "optimization_convergence.png"
FIG_TRADEOFF = BASE_DIR / "figures" / "optimization" / "cost_vs_capacity_tradeoff.png"


def load_json_artifact(file_path: Path, description: str) -> dict:
    """Nạp artifact định dạng JSON với xử lý lỗi minh bạch."""
    if not file_path.exists():
        raise FileNotFoundError(f"[LỖI THIẾU ARTIFACT] Không tìm thấy tệp {description} tại: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"[LỖI ĐỌC ARTIFACT] Không thể đọc nội dung tệp {description} ({file_path}): {e}")


def load_csv_artifact(file_path: Path, description: str) -> list:
    """Nạp artifact định dạng CSV với xử lý lỗi minh bạch."""
    if not file_path.exists():
        raise FileNotFoundError(f"[LỖI THIẾU ARTIFACT] Không tìm thấy tệp {description} tại: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise RuntimeError(f"[LỖI ĐỌC ARTIFACT] Không thể đọc nội dung tệp {description} ({file_path}): {e}")


def print_banner():
    print("=" * 82)
    print("  ĐỒ ÁN NHẬP MÔN TỐI ƯU HÓA — BẢO TRÌ DỰ ĐOÁN SCANIA APS (UCI #421)")
    print("  Quy trình Demo & Báo cáo Thuyết trình Bảo vệ Cá nhân (5–7 Phút)")
    print("  Chế độ: ĐỌC DỮ LIỆU ĐÃ NGHIỆM THU (EVIDENCE-DRIVEN, STRICTLY READ-ONLY)")
    print("=" * 82)


def step_1_problem_formulation():
    print("\n[PHẦN 1] BÀI TOÁN & MÔ HÌNH HÓA TOÁN HỌC TỐI ƯU CÓ RÀNG BUỘC")
    print("-" * 82)
    print("• Bối cảnh: Đội xe tải hạng nặng Scania, phát hiện sớm hư hỏng hệ thống khí nén (APS).")
    print("• Bộ dữ liệu: UCI #421 (60.000 Train/Validation, 16.000 Official Test, 170 cảm biến).")
    print("• Hàm mục tiêu phi đối xứng (IDA 2016 Benchmark):")
    print("    min f(theta, tau) = 10 * FP(theta, tau) + 500 * FN(theta, tau)")
    print("    Trong đó: FP tốn 10 đơn vị (kiểm tra thừa), FN tốn 500 đơn vị (chết máy dọc đường).")
    print("• Ràng buộc công suất xưởng (Maintenance Capacity Constraint):")
    print("    M(theta, tau) = TP + FP <= K = floor(N / 10)")
    print("    - Trên Validation (N = 12.000): K = 1.200 lượt xe.")
    print("    - Trên Official Test (N = 16.000): K = 1.600 lượt xe.")
    print("• Hai đồ thị tối ưu hóa thực nghiệm chính thức:")
    rel_conv = FIG_CONVERGENCE.relative_to(BASE_DIR) if FIG_CONVERGENCE.is_relative_to(BASE_DIR) else FIG_CONVERGENCE
    rel_trade = FIG_TRADEOFF.relative_to(BASE_DIR) if FIG_TRADEOFF.is_relative_to(BASE_DIR) else FIG_TRADEOFF
    print(f"    1. Hội tụ Optuna TPE:       {rel_conv} (Tồn tại: {FIG_CONVERGENCE.exists()})")
    print(f"    2. Đánh đổi Chi phí & Xưởng: {rel_trade} (Tồn tại: {FIG_TRADEOFF.exists()})")


def step_2_baselines():
    print("\n[PHẦN 2] HỆ THỐNG ĐƯỜNG CƠ SỞ (G4 BASELINES TRÊN 12.000 MẪU VALIDATION)")
    print("-" * 82)
    g4_data = load_json_artifact(G4_BASELINE_PATH, "G4 Baseline Metrics")
    rows = g4_data.get("rows", [])

    # Trích xuất các cấu hình quan trọng
    b0 = next((r for r in rows if r.get("baseline_id") == "B0"), None)
    b1_secondary = next((r for r in rows if r.get("baseline_id") == "B1" and r.get("role") == "SECONDARY"), None)
    b2_secondary = next((r for r in rows if r.get("baseline_id") == "B2" and r.get("role") == "SECONDARY"), None)

    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    print("  | Mã | Mô hình              | Ngưỡng  |  TP |  FP | FN | Chi phí| Xe vào M| Trạng thái|")
    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    if b0:
        print(f"  | B0 | Majority Dummy (a=0) |   N/A   | {b0['TP']:>3} | {b0['FP']:>3} |{b0['FN']:>3} |{b0['total_cost']:>7,}| {b0['M']:>7} | {b0['policy_status']:<9} |")
    if b1_secondary:
        t_b1 = f"{b1_secondary['threshold']:.4f}"
        print(f"  | B1 | Decision Stump       | {t_b1:>7} | {b1_secondary['TP']:>3} | {b1_secondary['FP']:>3} | {b1_secondary['FN']:>2} |{b1_secondary['total_cost']:>7,}| {b1_secondary['M']:>7} | {b1_secondary['policy_status']:<9} |")
    if b2_secondary:
        t_b2 = f"{b2_secondary['threshold']:.4f}"
        print(f"  | B2 | Logistic Regression  | {t_b2:>7} | {b2_secondary['TP']:>3} | {b2_secondary['FP']:>3} | {b2_secondary['FN']:>2} |{b2_secondary['total_cost']:>7,}| {b2_secondary['M']:>7} | {b2_secondary['policy_status']:<9} |")
    print("  +----+----------------------+---------+-----+-----+----+--------+---------+-----------+")
    if b2_secondary:
        print(f"  -> Mốc chi phí chuẩn tắc của G4: C*(G4) = {b2_secondary['total_cost']:,} đơn vị (Mô hình B2, tau={b2_secondary['threshold']:.4f}).")


def step_3_phase2_optimization():
    print("\n[PHẦN 3] TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RANDOM FOREST + OPTUNA TPE)")
    print("-" * 82)
    best_policy = load_json_artifact(PHASE2_BEST_POLICY_PATH, "Phase 2 Best Policy")
    trial16 = load_json_artifact(PHASE2_TRIAL16_PATH, "Phase 2 Trial 16 Result")

    rf_params = trial16.get("rf_params", {})
    tau_star = best_policy["threshold"]
    cost_star = best_policy["total_cost"]
    tp = best_policy["TP"]
    fp = best_policy["FP"]
    fn = best_policy["FN"]
    m = best_policy["M"]
    k = best_policy["K"]
    recall = best_policy["recall"]
    saving_b0 = best_policy["saving_pct"]

    # So sánh với mốc B2 (10,230)
    cost_b2 = 10230
    red_b2 = ((cost_b2 - cost_star) / cost_b2) * 100

    print("• Không gian tìm kiếm: n_estimators [20..60], max_depth [4..12], max_features [0.25..0.50].")
    print("• Ngân sách thực nghiệm: 20 trials tuần tự, 1 native thread, trần thời gian 900s.")
    print("• Quét ngưỡng vector hóa (Threshold tuning): 101 điểm từ 0.00 đến 1.00 trên Validation.")
    print("\n• CHÍNH SÁCH TỐI ƯU KHẢ THI QUAN SÁT ĐƯỢC (TRIAL 16):")
    print(f"    - Siêu tham số RF: n_estimators={rf_params.get('n_estimators')}, max_depth={rf_params.get('max_depth')}, "
          f"min_samples_split={rf_params.get('min_samples_split')}, max_features={rf_params.get('max_features', 0):.4f}")
    print(f"    - Ngưỡng tối ưu:   tau* = {tau_star:.6f}")
    print(f"    - Kết quả Val:     TP={tp}/200 (Recall {recall*100:.2f}%), FP={fp}, FN={fn} (chỉ lọt 5 xe chết máy)")
    print(f"    - Tổng chi phí:    10 * {fp} + 500 * {fn} = {cost_star:,} đơn vị chi phí benchmark")
    print(f"    - Năng lực xưởng:  M = {m} <= {k} (Khả thi, xưởng còn dư {k - m} chỗ)")
    print(f"    - Hiệu quả:        Tiết kiệm {saving_b0:.2f}% vs B0 (100k), cắt giảm thêm {red_b2:.2f}% vs B2 (10.230).")

    # Phân tích độ nhạy thực nghiệm dựa trên đường cong 101 điểm thực
    tc = best_policy.get("threshold_curve", [])
    print("\n• ĐỘ NHẠY NGƯỠNG THỰC NGHIỆM (EVIDENCE FROM 101-POINT THRESHOLD CURVE):")
    sample_taus = [0.20, 0.22, 0.30, 0.32, 0.33, 0.34, 0.35, 0.40, 0.50]
    matched = []
    for pt in tc:
        for st in sample_taus:
            if abs(pt["threshold"] - st) < 1e-4:
                matched.append(pt)

    print("  +--------+--------+-----+----+----+--------+-----------+")
    print("  | Ngưỡng | Chi phí|  TP | FP | FN |    M   | Trạng thái|")
    print("  +--------+--------+-----+----+----+--------+-----------+")
    for p in matched:
        status = "Khả thi" if p.get("feasible") == 1 else "Vi phạm"
        print(f"  |  {p['threshold']:.2f}  | {p['cost']:>6,} | {p['TP']:>3} |{p['FP']:>3} | {p['FN']:>2} | {p['M']:>6} | {status:<9} |")
    print(f"  | *{tau_star:.2f}* |  6,330 | 195 |383 |  5 |    578 | Khả thi   | (Nghiệm tối ưu liên tục)")
    print("  +--------+--------+-----+----+----+--------+-----------+")
    print("  => KẾT LUẬN VỀ TÍNH PHI ĐỐI XỨNG CỦA HÀM CHI PHÍ:")
    print("     1. Trong vùng tau in [0.20, 0.32]: Số ca lọt FN ổn định cực thấp (4-5 ca), chi phí duy trì")
    print("        ổn định ở mức thấp [6.350, 7.050], đạt cực tiểu 6.330 tại tau* = 0.3232.")
    print("     2. Khi tau >= 0.33: Chi phí tăng rất dốc (7.290 tại 0.33, 8.230 tại 0.34, 8.670 tại 0.35)")
    print("        do mỗi ca bỏ sót FN bị phạt nặng +500 đơn vị (FN tăng từ 5 lên 7, 9, 10 ca).")
    print("        Do đó, KHÔNG có vùng lòng chảo phẳng trên toàn bộ [0.20, 0.35].")
    print("     3. Khi tau < 0.10: Báo động giả FP tăng mạnh khiến M > 1.200 (vi phạm công suất xưởng).")


def step_4_official_test_g10():
    print("\n[PHẦN 4] ĐÁNH GIÁ ĐỘC LẬP TẬP OFFICIAL TEST (GATE G10 — RUN 003)")
    print("-" * 82)
    test_metrics = load_json_artifact(G10_TEST_METRICS_PATH, "G10 Test Metrics")
    cm_rows = load_csv_artifact(G10_CM_PATH, "G10 Confusion Matrix CSV")

    tp = test_metrics["TP"]
    fp = test_metrics["FP"]
    fn = test_metrics["FN"]
    tn = test_metrics["TN"]
    n_test = test_metrics["N"]
    p_test = test_metrics["P"]
    m = test_metrics["M"]
    k = test_metrics["K"]
    cost = test_metrics["total_cost"]
    ref_cost = test_metrics["reference_cost"]
    saving_pct = test_metrics["saving_pct"]
    recall = test_metrics["recall"]
    precision = test_metrics["precision"]
    specificity = test_metrics["specificity"]
    roc_auc = test_metrics["roc_auc"]
    pr_auc = test_metrics["pr_auc"]

    print("• Quy trình: Khóa chính sách Trial 16, refit đúng 1 lần trên Train 48k, zero tuning trên Test.")
    print(f"• Quy mô Test: {n_test:,} mẫu độc lập ({p_test} ca hỏng APS {p_test/n_test*100:.2f}%, {tn+fp} ca âm tính {(tn+fp)/n_test*100:.2f}%).")
    print("\n  +-------------------------------+-------------------+-----------------------+")
    print("  | Tiêu chí đo đạc               | Mặc định B0 (Test)| Official Test (G10)   |")
    print("  +-------------------------------+-------------------+-----------------------+")
    print(f"  | True Positives (TP)           |                 0 |                 {tp:>5} |")
    print(f"  | False Positives (FP)          |                 0 |                 {fp:>5} |")
    print(f"  | False Negatives (FN)          |               {p_test:>3} |                 {fn:>5} |")
    print(f"  | True Negatives (TN)           |            {n_test - p_test:>6,} |              {tn:>8,} |")
    print(f"  | Recall (Độ nhạy)              |             0.00% |     {recall*100:>6.2f}% ({tp}/{p_test}) |")
    print(f"  | Precision (Độ chính xác)      |               N/A |     {precision*100:>6.2f}% ({tp}/{m}) |")
    print(f"  | Specificity (Độ đặc hiệu)     |           100.00% |     {specificity*100:>6.2f}% ({tn}/{tn+fp})|")
    print(f"  | ROC-AUC / PR-AUC              |               N/A |       {roc_auc:.4f} / {pr_auc:.4f} |")
    print(f"  | Chi phí kiểm tra (10 * FP)    |                 0 |               {test_metrics['cost_fp']:>7,} |")
    print(f"  | Chi phí sự cố (500 * FN)      |           {ref_cost:>7,} |               {test_metrics['cost_fn']:>7,} |")
    print(f"  | TỔNG CHI PHÍ BENCHMARK        |           {ref_cost:>7,} |              {cost:>8,} |")
    print(f"  | Mức tiết kiệm chi phí         |     0.00% (Chuẩn) |   {saving_pct:>6.2f}% (-{ref_cost - cost:,})|")
    print(f"  | Số xe vào xưởng (M <= 1.600)  |                 0 |      {m:>5} (DƯ {k - m} CHỖ)|")
    print(f"  | Trạng thái ràng buộc          |          FEASIBLE |     FEASIBLE (KHẢ THI)|")
    print("  +-------------------------------+-------------------+-----------------------+")

    # Hiển thị ma trận nhầm lẫn từ CSV
    print("\n• MA TRẬN NHẦM LẪN THỰC TẾ (CONFUSION MATRIX TEST):")
    for r in cm_rows:
        print(f"    Thực tế {r['actual']:<5}: Dự đoán Neg={r['pred_neg']:>5}, Dự đoán Pos={r['pred_pos']:>5} | Tổng={r['total']:>5}")

    print("\n• MINH BẠCH HỌC THUẬT & PHÂN BIỆT THỰC ĐỊA:")
    print("  1. Truy cập Test ở Runs 001/002: Tệp test CSV được nạp vào RAM nhưng tiến trình dừng ngay")
    print("     tại chốt kiểm tra preprocessor; tuyệt đối không có dự đoán hay tinh chỉnh nào.")
    print("  2. Benchmark vs Thực tế: Chi phí 13.840 tính theo chuẩn benchmark tĩnh IDA 2016 (10*FP+500*FN).")
    print("     Triển khai thực tế trên đội xe cần bổ sung điều độ động, phụ tùng và chi phí thợ.")


def step_5_verification() -> bool:
    print("\n[PHẦN 5] XÁC THỰC CHỮ KÝ SỐ MẬT MÃ HỌC SHA-256 (READ-ONLY)")
    print("-" * 82)
    manifest = load_json_artifact(G10_MANIFEST_PATH, "G10 Stable Manifest")
    print(f"• Tìm thấy Stable Manifest G10 ({len(manifest)} artifacts).")

    all_pass = True
    base_dir = G10_MANIFEST_PATH.parent
    for fname, exp_hash in manifest.items():
        fpath = base_dir / fname
        if not fpath.exists():
            print(f"  [MISSING] {fname}")
            all_pass = False
            continue
        try:
            with open(fpath, "rb") as f:
                c = f.read().replace(b"\r\n", b"\n")
            act_hash = hashlib.sha256(c).hexdigest()
            status = "PASS" if act_hash == exp_hash else "MISMATCH"
            if status != "PASS":
                all_pass = False
            print(f"  [{status}] {fname:<35} SHA-256: {act_hash[:16]}...")
        except Exception as e:
            print(f"  [ERROR]   {fname:<35} Lỗi: {e}")
            all_pass = False

    if all_pass:
        print("\n  >>> KẾT LUẬN: 100% ARTIFACTS GATE G10 ĐƯỢC XÁC THỰC CHÍNH HÃNG SHA-256 <<<")
    else:
        print("\n  >>> CẢNH BÁO: PHÁT HIỆN ARTIFACT BỊ THIẾU HOẶC SAI LỆCH MÃ BĂM SHA-256! <<<")

    return all_pass


def print_speaker_notes():
    print("\n" + "=" * 82)
    print("  KỊCH BẢN & SPEAKER NOTES BẢO VỆ 5–7 PHÚT (DÀNH CHO SINH VIÊN)")
    print("=" * 82)
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
   - Phân tích độ nhạy: Vùng ngưỡng [0.20, 0.32] duy trì chi phí thấp [6.350, 7.050] do FN chỉ 4-5 ca;
     tuy nhiên khi tau >= 0.33, chi phí tăng rất dốc do mỗi ca FN bị phạt 500 đơn vị (7.290 tại 0.33,
     8.230 tại 0.34, 8.670 tại 0.35).

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
    parser = argparse.ArgumentParser(description="Demo bảo vệ đồ án Tối ưu hóa Scania APS (Evidence-Driven)")
    parser.add_argument("--summary", action="store_true", help="Chỉ in bảng tóm tắt kết quả từ artifacts")
    parser.add_argument("--verify", action="store_true", help="Chỉ chạy kiểm chứng chữ ký băm mật mã học (SHA-256)")
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
        success = step_5_verification()
        if not success:
            sys.exit(1)
        return

    if args.notes:
        print_speaker_notes()
        return

    # Mặc định: Chạy toàn bộ luồng demo bảo vệ
    print_banner()
    step_1_problem_formulation()
    step_2_baselines()
    step_3_phase2_optimization()
    step_4_official_test_g10()
    success = step_5_verification()
    print_speaker_notes()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
