"""
Dự án: Tối ưu hóa chi phí bảo trì dự đoán hệ thống khí nén xe tải Scania APS (UCI 421)
Học phần: Nhập môn Tối ưu hóa — Khoa Công nghệ Thông tin, Trường Đại học Văn Lang
Sinh viên thực hiện: Huỳnh Phúc (MSSV: 2474802010314)
Mục đích: Script demo bảo vệ đồ án cá nhân (5–7 phút) và kiểm tra tính toàn vẹn kết quả đã nghiệm thu.
Nguyên tắc vận hành:
  - CHẾ ĐỘ ĐỌC KẾT QUẢ LƯU TRỮ (STRICTLY READ-ONLY, SAVED-RESULTS PRESENTATION).
  - KHÔNG huấn luyện mô hình mới, KHÔNG chạy lại tối ưu hóa, KHÔNG đọc dữ liệu Official Test,
    và KHÔNG thực hiện suy luận trực tiếp (live inference) trên dữ liệu mới.
  - Mọi số liệu thực nghiệm được nạp trực tiếp từ các tệp cấu hình và kết quả JSON/CSV gốc,
    kèm kiểm định chéo tính nhất quán toán học và kiểm tra mã băm toàn vẹn SHA-256.
"""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent

# Cấu hình khóa của bài toán tối ưu Phase 2 & Gate G10
PHASE2_CONFIG_PATH = BASE_DIR / "configs" / "scania" / "phase2_optimization.json"
G10_CONFIG_PATH = BASE_DIR / "configs" / "scania" / "g10_evaluation.json"

# Thư mục các lượt thực nghiệm đã nghiệm thu
G4_RUN_DIR = BASE_DIR / "results" / "scania_aps" / "g4" / "scania_g4_b2_real_002"
PHASE2_RUN_DIR = BASE_DIR / "results" / "scania_aps" / "phase2" / "scania_phase2_rf_optuna_002"
G10_RUN_DIR = BASE_DIR / "results" / "scania_aps" / "g10" / "scania_g10_official_test_003"

# Các tệp dữ liệu thực nghiệm cốt lõi
G4_METRICS_PATH = G4_RUN_DIR / "baseline_metrics.json"
G4_SUMMARY_PATH = G4_RUN_DIR / "run_summary.json"
G4_CHECKSUMS_PATH = G4_RUN_DIR / "checksums.json"

PHASE2_BEST_POLICY_PATH = PHASE2_RUN_DIR / "best_policy.json"
PHASE2_STUDY_PATH = PHASE2_RUN_DIR / "optuna_study.json"
PHASE2_SUMMARY_PATH = PHASE2_RUN_DIR / "run_summary.json"
PHASE2_TRIAL16_PATH = PHASE2_RUN_DIR / "durable_fits" / "trial_016_result.json"
PHASE2_CHECKSUMS_PATH = PHASE2_RUN_DIR / "checksums.json"

G10_TEST_METRICS_PATH = G10_RUN_DIR / "test_metrics.json"
G10_CM_CSV_PATH = G10_RUN_DIR / "confusion_matrix_test.csv"
G10_VAL_GUARD_PATH = G10_RUN_DIR / "validation_guard_metrics.json"
G10_BEST_POLICY_PATH = G10_RUN_DIR / "best_policy.json"
G10_SUMMARY_PATH = G10_RUN_DIR / "run_summary.json"
G10_MANIFEST_PATH = G10_RUN_DIR / "stable_manifest.json"

# Đồ thị tối ưu hóa thực nghiệm
FIG_CONVERGENCE = BASE_DIR / "figures" / "optimization" / "optimization_convergence.png"
FIG_TRADEOFF = BASE_DIR / "figures" / "optimization" / "cost_vs_capacity_tradeoff.png"


class DemoIntegrityError(RuntimeError):
    """Ngoại lệ phát sinh khi thiếu tệp, hỏng dữ liệu hoặc sai lệch kiểm định nhất quán."""


def sha256_lf_normalized(file_path: Path) -> str:
    """Tính mã băm SHA-256 chuẩn hóa dòng LF để kiểm tra tính toàn vẹn tệp."""
    if not file_path.is_file():
        raise DemoIntegrityError(f"Thiếu tệp bắt buộc khi tính SHA-256: {file_path}")
    raw_bytes = file_path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw_bytes).hexdigest()


def load_json_artifact(file_path: Path, description: str) -> Dict[str, Any]:
    """Đọc tệp JSON với thông báo lỗi rõ ràng nếu thiếu hoặc hỏng định dạng."""
    if not file_path.is_file():
        raise DemoIntegrityError(
            f"[THIẾU ARTIFACT] Không tìm thấy {description} tại đường dẫn: {file_path}"
        )
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise DemoIntegrityError(
            f"[HỎNG ĐỊNH DẠNG JSON] Không thể phân tích {description} ({file_path}): {exc}"
        ) from exc
    if not isinstance(data, dict) or not data:
        raise DemoIntegrityError(
            f"[DỮ LIỆU RỖNG/KHÔNG HỢP LỆ] {description} ({file_path}) không phải object JSON hợp lệ."
        )
    return data


def load_csv_artifact(file_path: Path, description: str) -> List[Dict[str, str]]:
    """Đọc tệp CSV với thông báo lỗi rõ ràng nếu thiếu hoặc rỗng."""
    if not file_path.is_file():
        raise DemoIntegrityError(
            f"[THIẾU ARTIFACT] Không tìm thấy {description} tại đường dẫn: {file_path}"
        )
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
    except Exception as exc:
        raise DemoIntegrityError(
            f"[HỎNG ĐỊNH DẠNG CSV] Không thể đọc {description} ({file_path}): {exc}"
        ) from exc
    if not rows:
        raise DemoIntegrityError(f"[CSV RỖNG] {description} ({file_path}) không có dòng dữ liệu nào.")
    return rows


def require_keys(obj: Dict[str, Any], keys: List[str], context: str) -> None:
    """Đảm bảo đủ các trường bắt buộc trong dictionary."""
    missing = [k for k in keys if k not in obj]
    if missing:
        raise DemoIntegrityError(f"[THIẾU TRƯỜNG DỮ LIỆU] {context} thiếu các khóa: {missing}")


def validate_policy_metrics(
    metrics: Dict[str, Any],
    cost_fp_unit: int,
    cost_fn_unit: int,
    context: str,
) -> None:
    """Kiểm định nhất quán toán học giữa ma trận nhầm lẫn, hàm chi phí và ràng buộc công suất."""
    req = [
        "TP", "FP", "FN", "TN", "N", "P", "M", "K",
        "cost_fp", "cost_fn", "total_cost", "reference_cost",
        "absolute_saving", "saving_pct", "feasible", "policy_status",
    ]
    require_keys(metrics, req, context)

    tp = int(metrics["TP"])
    fp = int(metrics["FP"])
    fn = int(metrics["FN"])
    tn = int(metrics["TN"])
    n = int(metrics["N"])
    p = int(metrics["P"])
    m = int(metrics["M"])
    k = int(metrics["K"])

    if any(x < 0 for x in (tp, fp, fn, tn, n, p, m, k)):
        raise DemoIntegrityError(f"[SAI LỆCH SỐ HỌC] {context}: tồn tại giá trị đếm âm.")
    if tp + fn != p:
        raise DemoIntegrityError(f"[SAI MA TRẬN NHẦM LẪN] {context}: TP+FN ({tp+fn}) != P ({p}).")
    if tn + fp != n - p:
        raise DemoIntegrityError(f"[SAI MA TRẬN NHẦM LẪN] {context}: TN+FP ({tn+fp}) != N-P ({n-p}).")
    if tp + fp != m:
        raise DemoIntegrityError(f"[SAI LƯỢT BẢO TRÌ] {context}: TP+FP ({tp+fp}) != M ({m}).")
    if tp + fp + fn + tn != n:
        raise DemoIntegrityError(f"[SAI TỔNG MẪU] {context}: TP+FP+FN+TN != N ({n}).")

    expected_k = n // 10
    if k != expected_k:
        raise DemoIntegrityError(
            f"[SAI NGƯỠNG CÔNG SUẤT] {context}: K ({k}) != floor(N/10) ({expected_k})."
        )
    expected_feasible = m <= k
    actual_feasible = bool(metrics["feasible"])
    expected_status = "FEASIBLE" if expected_feasible else "INFEASIBLE"
    if actual_feasible != expected_feasible or metrics["policy_status"] != expected_status:
        raise DemoIntegrityError(
            f"[SAI TRẠNG THÁI KHẢ THI] {context}: M={m}, K={k}, feasible={actual_feasible}, status={metrics['policy_status']}."
        )

    exp_cost_fp = cost_fp_unit * fp
    exp_cost_fn = cost_fn_unit * fn
    exp_total_cost = exp_cost_fp + exp_cost_fn
    if int(metrics["cost_fp"]) != exp_cost_fp or int(metrics["cost_fn"]) != exp_cost_fn:
        raise DemoIntegrityError(f"[SAI CHI PHÍ THÀNH PHẦN] {context}: cost_fp/cost_fn không khớp công thức.")
    if int(metrics["total_cost"]) != exp_total_cost:
        raise DemoIntegrityError(
            f"[SAI HÀM MỤC TIÊU] {context}: total_cost ({metrics['total_cost']}) != {cost_fp_unit}*FP + {cost_fn_unit}*FN ({exp_total_cost})."
        )

    exp_ref_cost = cost_fn_unit * p
    exp_abs_saving = exp_ref_cost - exp_total_cost
    if int(metrics["reference_cost"]) != exp_ref_cost:
        raise DemoIntegrityError(f"[SAI CHI PHÍ THAM CHIẾU B0] {context}: {metrics['reference_cost']} != {exp_ref_cost}.")
    if int(metrics["absolute_saving"]) != exp_abs_saving:
        raise DemoIntegrityError(f"[SAI MỨC TIẾT KIỆM TUYỆT ĐỐI] {context}: {metrics['absolute_saving']} != {exp_abs_saving}.")

    if exp_ref_cost > 0:
        exp_pct = 100.0 * exp_abs_saving / exp_ref_cost
        if abs(float(metrics["saving_pct"]) - exp_pct) > 0.01:
            raise DemoIntegrityError(
                f"[SAI TỶ LỆ TIẾT KIỆM] {context}: saving_pct={metrics['saving_pct']} lệch so với {exp_pct:.4f}."
            )


def verify_manifest_group(
    run_dir: Path, manifest_path: Path, group_label: str
) -> Tuple[bool, List[Tuple[str, str, str]]]:
    """Kiểm tra mã băm SHA-256 của toàn bộ artifact trong một manifest/checksums."""
    manifest = load_json_artifact(manifest_path, f"Manifest {group_label}")
    records: List[Tuple[str, str, str]] = []
    all_ok = True
    for rel_name, expected_sha in sorted(manifest.items()):
        target = run_dir / rel_name
        if not target.is_file():
            records.append((rel_name, "MISSING", ""))
            all_ok = False
            continue
        actual_sha = sha256_lf_normalized(target)
        status = "PASS" if actual_sha == expected_sha else "MISMATCH"
        if status != "PASS":
            all_ok = False
        records.append((rel_name, status, actual_sha))
    return all_ok, records


def load_and_validate_all_evidence() -> Dict[str, Any]:
    """Nạp toàn bộ bằng chứng thực nghiệm và kiểm định tính nhất quán liên tệp."""
    phase2_cfg = load_json_artifact(PHASE2_CONFIG_PATH, "Cấu hình Phase 2")
    g10_cfg = load_json_artifact(G10_CONFIG_PATH, "Cấu hình Gate G10")

    require_keys(phase2_cfg, ["search_space", "budget", "objective", "constraint", "resources"], "phase2_optimization.json")
    cost_fp_unit = int(phase2_cfg["objective"]["cost_fp"])
    cost_fn_unit = int(phase2_cfg["objective"]["cost_fn"])

    # 1. Nạp và kiểm tra G4 Baselines
    g4_metrics = load_json_artifact(G4_METRICS_PATH, "G4 Baseline Metrics")
    g4_summary = load_json_artifact(G4_SUMMARY_PATH, "G4 Run Summary")
    require_keys(g4_metrics, ["rows", "run_id"], "G4 Baseline Metrics")
    g4_rows = g4_metrics["rows"]
    if not isinstance(g4_rows, list) or len(g4_rows) < 5:
        raise DemoIntegrityError("[SAI DỮ LIỆU G4] baseline_metrics.json phải chứa đủ 5 dòng chính sách cơ sở.")
    for idx, r in enumerate(g4_rows):
        validate_policy_metrics(r, cost_fp_unit, cost_fn_unit, f"G4 Row #{idx} ({r.get('baseline_id')}/{r.get('role')})")

    b0_val = next((r for r in g4_rows if r.get("baseline_id") == "B0"), None)
    b1_sec = next((r for r in g4_rows if r.get("baseline_id") == "B1" and r.get("role") == "SECONDARY"), None)
    b2_pri = next((r for r in g4_rows if r.get("baseline_id") == "B2" and r.get("role") == "PRIMARY"), None)
    b2_sec = next((r for r in g4_rows if r.get("baseline_id") == "B2" and r.get("role") == "SECONDARY"), None)
    if not all([b0_val, b1_sec, b2_pri, b2_sec]):
        raise DemoIntegrityError("[THIẾU CHÍNH SÁCH G4] Không tìm thấy đủ B0, B1, B2 trong baseline_metrics.json.")

    # 2. Nạp và kiểm tra Phase 2 Constrained Optimization
    p2_best = load_json_artifact(PHASE2_BEST_POLICY_PATH, "Phase 2 Best Policy")
    p2_study = load_json_artifact(PHASE2_STUDY_PATH, "Phase 2 Optuna Study")
    p2_summary = load_json_artifact(PHASE2_SUMMARY_PATH, "Phase 2 Run Summary")
    p2_trial16 = load_json_artifact(PHASE2_TRIAL16_PATH, "Phase 2 Trial 16 Durable Result")

    validate_policy_metrics(p2_best, cost_fp_unit, cost_fn_unit, "Phase 2 Best Policy")
    require_keys(p2_study, ["n_trials_completed", "best_trial", "trials"], "Phase 2 Optuna Study")
    trials = p2_study["trials"]
    if len(trials) != int(p2_study["n_trials_completed"]):
        raise DemoIntegrityError("[SAI SỐ TRIAL PHASE 2] Số lượng trials trong optuna_study.json không khớp n_trials_completed.")

    feasible_trials = [t for t in trials if t.get("status") == "FEASIBLE" and t.get("best_policy")]
    if not feasible_trials:
        raise DemoIntegrityError("[KHÔNG CÓ TRIAL KHẢ THI] optuna_study.json không có trial khả thi nào.")
    best_from_study = min(
        feasible_trials,
        key=lambda t: (
            int(t["best_policy"]["total_cost"]),
            int(t["best_policy"]["M"]),
            -float(t["best_policy"]["threshold"]),
        ),
    )
    if int(best_from_study["best_policy"]["total_cost"]) != int(p2_best["total_cost"]):
        raise DemoIntegrityError("[MÂU THUẪN NGHIỆM TỐI ƯU] best_policy.json không khớp nghiệm khả thi nhỏ nhất trong optuna_study.json.")
    if best_from_study.get("trial_number") != p2_trial16.get("trial_number"):
        raise DemoIntegrityError("[MÂU THUẪN TRIAL TỐT NHẤT] Số thứ tự trial tốt nhất không khớp tệp durable trial_016_result.json.")

    # Kiểm tra đường cong ngưỡng 101 điểm của chính sách tốt nhất
    tc = p2_best.get("threshold_curve", [])
    if not isinstance(tc, list) or len(tc) != 101:
        raise DemoIntegrityError("[SAI ĐƯỜNG CONG NGƯỠNG] threshold_curve trong best_policy.json phải có đúng 101 điểm.")
    for pt in tc:
        require_keys(pt, ["threshold", "M", "cost", "TP", "FP", "FN", "feasible"], "Điểm trên threshold_curve")
        if int(pt["TP"]) + int(pt["FP"]) != int(pt["M"]):
            raise DemoIntegrityError(f"[SAI ĐƯỜNG CONG NGƯỠNG] tau={pt['threshold']}: TP+FP != M.")
        if cost_fp_unit * int(pt["FP"]) + cost_fn_unit * int(pt["FN"]) != int(pt["cost"]):
            raise DemoIntegrityError(f"[SAI ĐƯỜNG CONG NGƯỠNG] tau={pt['threshold']}: công thức chi phí không khớp.")
        if bool(pt["feasible"]) != (int(pt["M"]) <= int(p2_best["K"])):
            raise DemoIntegrityError(f"[SAI ĐƯỜNG CONG NGƯỠNG] tau={pt['threshold']}: trạng thái khả thi không khớp M <= K.")

    # 3. Nạp và kiểm tra Gate G10 Official Test
    g10_test = load_json_artifact(G10_TEST_METRICS_PATH, "Gate G10 Test Metrics")
    g10_val_guard = load_json_artifact(G10_VAL_GUARD_PATH, "Gate G10 Validation Guard Metrics")
    g10_policy = load_json_artifact(G10_BEST_POLICY_PATH, "Gate G10 Best Policy Record")
    g10_summary = load_json_artifact(G10_SUMMARY_PATH, "Gate G10 Run Summary")
    g10_cm_rows = load_csv_artifact(G10_CM_CSV_PATH, "Gate G10 Confusion Matrix CSV")

    validate_policy_metrics(g10_val_guard, cost_fp_unit, cost_fn_unit, "Gate G10 Validation Guard")
    validate_policy_metrics(g10_test, cost_fp_unit, cost_fn_unit, "Gate G10 Official Test")

    # Đối chiếu chính sách đóng băng giữa Phase 2 và Gate G10
    for key in ("TP", "FP", "FN", "TN", "M", "total_cost"):
        if int(g10_val_guard[key]) != int(p2_best[key]):
            raise DemoIntegrityError(
                f"[LỆCH VALIDATION GUARD] Chỉ số {key} giữa Phase 2 ({p2_best[key]}) và G10 Guard ({g10_val_guard[key]}) không khớp."
            )
    if abs(float(g10_test["threshold"]) - float(p2_best["threshold"])) > 1e-12:
        raise DemoIntegrityError("[LỆCH NGƯỠNG ĐÓNG BĂNG] Ngưỡng đánh giá Test khác ngưỡng đã khóa từ Phase 2.")

    g10_src_params = g10_policy.get("source_policy", {}).get("hyperparameters", {})
    p2_rf_params = p2_trial16.get("rf_params", {})
    for hp_key, hp_val in p2_rf_params.items():
        if hp_key not in g10_src_params or abs(float(g10_src_params[hp_key]) - float(hp_val)) > 1e-12:
            raise DemoIntegrityError(f"[LỆCH SIÊU THAM SỐ ĐÓNG BĂNG] Tham số {hp_key} không khớp giữa Phase 2 và G10.")

    # Đối chiếu ma trận nhầm lẫn CSV với test_metrics.json
    cm_map = {r.get("actual", "").strip(): r for r in g10_cm_rows}
    require_keys(cm_map, ["neg", "pos", "total"], "confusion_matrix_test.csv")
    if (
        int(cm_map["neg"]["pred_neg"]) != int(g10_test["TN"])
        or int(cm_map["neg"]["pred_pos"]) != int(g10_test["FP"])
        or int(cm_map["pos"]["pred_neg"]) != int(g10_test["FN"])
        or int(cm_map["pos"]["pred_pos"]) != int(g10_test["TP"])
        or int(cm_map["total"]["pred_pos"]) != int(g10_test["M"])
        or int(cm_map["total"]["total"]) != int(g10_test["N"])
    ):
        raise DemoIntegrityError(
            "[MÂU THUẪN CSV/JSON] Số liệu trong confusion_matrix_test.csv không khớp test_metrics.json."
        )

    # Kiểm tra sự tồn tại của 2 đồ thị bắt buộc
    if not FIG_CONVERGENCE.is_file() or FIG_CONVERGENCE.stat().st_size == 0:
        raise DemoIntegrityError(f"[THIẾU ĐỒ THỊ] Không tìm thấy đồ thị hội tụ hợp lệ tại: {FIG_CONVERGENCE}")
    if not FIG_TRADEOFF.is_file() or FIG_TRADEOFF.stat().st_size == 0:
        raise DemoIntegrityError(f"[THIẾU ĐỒ THỊ] Không tìm thấy đồ thị đánh đổi hợp lệ tại: {FIG_TRADEOFF}")

    return {
        "phase2_cfg": phase2_cfg,
        "g10_cfg": g10_cfg,
        "cost_fp_unit": cost_fp_unit,
        "cost_fn_unit": cost_fn_unit,
        "g4_rows": g4_rows,
        "g4_summary": g4_summary,
        "b0_val": b0_val,
        "b1_sec": b1_sec,
        "b2_pri": b2_pri,
        "b2_sec": b2_sec,
        "p2_best": p2_best,
        "p2_study": p2_study,
        "p2_summary": p2_summary,
        "p2_trial_best": p2_trial16,
        "g10_test": g10_test,
        "g10_val_guard": g10_val_guard,
        "g10_policy": g10_policy,
        "g10_summary": g10_summary,
        "g10_cm_rows": g10_cm_rows,
    }


def verify_all_artifact_checksums(verbose: bool = True) -> bool:
    """Xác minh mã băm SHA-256 toàn vẹn trên cả 3 giai đoạn thực nghiệm G4, Phase 2 và Gate G10."""
    if verbose:
        print("\n[PHẦN 5] KIỂM TRA TÍNH TOÀN VẸN BẰNG MÃ BĂM SHA-256 (READ-ONLY INTEGRITY CHECK)")
        print("-" * 86)
        print("• Lưu ý kỹ thuật: SHA-256 là hàm băm mật mã dùng để kiểm chứng tính toàn vẹn tệp")
        print("  (integrity checksum), không phải chữ ký số khóa công khai (digital signature).")

    suites = [
        ("G4 Baselines (scania_g4_b2_real_002)", G4_RUN_DIR, G4_CHECKSUMS_PATH),
        ("Phase 2 Optuna TPE (scania_phase2_rf_optuna_002)", PHASE2_RUN_DIR, PHASE2_CHECKSUMS_PATH),
        ("Gate G10 Official Test (scania_g10_official_test_003)", G10_RUN_DIR, G10_MANIFEST_PATH),
    ]

    overall_ok = True
    total_checked = 0

    for label, run_dir, manifest_path in suites:
        ok, records = verify_manifest_group(run_dir, manifest_path, label)
        total_checked += len(records)
        if not ok:
            overall_ok = False
        if verbose:
            state_txt = "PASS" if ok else "FAIL"
            print(f"\n• [{state_txt}] {label} — {len(records)} artifacts:")
            for fname, st, actual_hash in records:
                short_h = f"{actual_hash[:16]}..." if actual_hash else "N/A"
                print(f"    [{st:<8}] {fname:<36} SHA-256: {short_h}")

    if verbose:
        if overall_ok:
            print(f"\n  >>> KẾT LUẬN: {total_checked}/{total_checked} ARTIFACTS KHỚP MÃ BĂM SHA-256 VÀ KIỂM ĐỊNH TOÁN HỌC <<<")
        else:
            print("\n  >>> LỖI TOÀN VẸN: PHÁT HIỆN TỆP BỊ THIẾU HOẶC SAI LỆCH MÃ BĂM SHA-256! <<<")

    return overall_ok


def print_banner() -> None:
    print("=" * 86)
    print("  ĐỒ ÁN NHẬP MÔN TỐI ƯU HÓA — BẢO TRÌ DỰ ĐOÁN SCANIA APS (UCI #421)")
    print("  Trình diễn kết quả thực nghiệm đã lưu & Kiểm tra toàn vẹn (5–7 phút bảo vệ)")
    print("  Chế độ: CHỈ ĐỌC KẾT QUẢ ĐÃ NGHIỆM THU (READ-ONLY, KHÔNG HUẤN LUYỆN/SUY LUẬN MỚI)")
    print("=" * 86)


def step_1_problem_formulation(ev: Dict[str, Any]) -> None:
    cfg = ev["phase2_cfg"]
    data_cfg = cfg["data"]
    c_fp = ev["cost_fp_unit"]
    c_fn = ev["cost_fn_unit"]
    n_train = int(data_cfg["train_samples"])
    n_val = int(data_cfg["validation_samples"])
    n_feat = int(data_cfg["features"])
    k_val = int(cfg["constraint"]["max_maintenance_units"])
    n_test = int(ev["g10_test"]["N"])
    k_test = int(ev["g10_test"]["K"])

    print("\n[PHẦN 1] BÀI TOÁN & MÔ HÌNH HÓA TOÁN HỌC TỐI ƯU CÓ RÀNG BUỘC")
    print("-" * 86)
    print("• Bối cảnh: Hỗ trợ quyết định kiểm tra hệ thống khí nén (APS) cho xe tải nặng Scania.")
    print(
        f"• Dữ liệu UCI #421: Phát triển {n_train + n_val:,} mẫu (Train {n_train:,} / Validation {n_val:,}), "
        f"Official Test {n_test:,} mẫu, {n_feat} thuộc tính số."
    )
    print("• Biến quyết định: x = (theta, tau), với siêu tham số Random Forest theta và ngưỡng tau in [0, 1].")
    print("• Hàm mục tiêu chi phí phi đối xứng (IDA 2016 Benchmark):")
    print(f"    min f(theta, tau) = {c_fp} * FP(theta, tau) + {c_fn} * FN(theta, tau)  [đơn vị chi phí benchmark]")
    print(f"    (FP = {c_fp}: kiểm tra APS thừa; FN = {c_fn}: bỏ sót lỗi APS, tỷ lệ phạt {c_fn // c_fp}:1)")
    print("• Ràng buộc công suất xưởng (giả định kịch bản tối đa 10% số quan sát):")
    print("    M(theta, tau) = TP + FP <= K = floor(N / 10)")
    print(f"    - Phân vùng Validation (N = {n_val:,}): K_val = {k_val:,} lượt xe.")
    print(f"    - Phân vùng Official Test (N = {n_test:,}): K_test = {k_test:,} lượt xe.")
    print("• Đường dẫn hai đồ thị tối ưu hóa thực nghiệm:")
    print(f"    1. Tiến trình tìm kiếm Optuna TPE: {FIG_CONVERGENCE.relative_to(BASE_DIR).as_posix()}")
    print(f"    2. Đánh đổi Chi phí & Công suất:   {FIG_TRADEOFF.relative_to(BASE_DIR).as_posix()}")


def step_2_baselines(ev: Dict[str, Any]) -> None:
    rows = ev["g4_rows"]
    b2_sec = ev["b2_sec"]
    n_val = int(b2_sec["N"])
    p_val = int(b2_sec["P"])
    k_val = int(b2_sec["K"])

    print(f"\n[PHẦN 2] HỆ THỐNG ĐƯỜNG CƠ SỞ G4 (VALIDATION: N = {n_val:,}, P = {p_val}, K = {k_val:,})")
    print("-" * 86)
    print("  +----+----------------------+----------+-----+-----+-----+---------+---------+-----------+")
    print("  | Mã | Mô hình              | Ngưỡng τ |  TP |  FP |  FN | Chi phí | Xe vào M| Trạng thái|")
    print("  +----+----------------------+----------+-----+-----+-----+---------+---------+-----------+")
    model_names = {
        "B0": "Majority Dummy (a=0)",
        "B1": "Decision Stump",
        "B2": "Logistic Regression",
    }
    for r in rows:
        bid = r["baseline_id"]
        tau_str = "   N/A  " if r["threshold"] is None else f"{float(r['threshold']):8.4f}"
        print(
            f"  | {bid:<2} | {model_names.get(bid, bid):<20} | {tau_str} | "
            f"{int(r['TP']):>3} | {int(r['FP']):>3} | {int(r['FN']):>3} | "
            f"{int(r['total_cost']):>7,} | {int(r['M']):>7,} | {r['policy_status']:<9} |"
        )
    print("  +----+----------------------+----------+-----+-----+-----+---------+---------+-----------+")
    print(
        f"  -> Mốc tham chiếu tốt nhất G4 trên Validation: B2 tại tau = {float(b2_sec['threshold']):.4f} "
        f"đạt chi phí {int(b2_sec['total_cost']):,} đơn vị (M = {int(b2_sec['M'])} <= {k_val:,})."
    )


def step_3_phase2_optimization(ev: Dict[str, Any]) -> None:
    cfg = ev["phase2_cfg"]
    sp = cfg["search_space"]
    budget = cfg["budget"]
    res = cfg["resources"]
    best_pol = ev["p2_best"]
    trial_best = ev["p2_trial_best"]
    p2_sum = ev["p2_summary"]
    b2_cost = int(ev["b2_sec"]["total_cost"])

    rf_params = trial_best["rf_params"]
    trial_num = int(trial_best["trial_number"])
    fit_idx = int(trial_best["fit_index"])
    tau_star = float(best_pol["threshold"])
    cost_star = int(best_pol["total_cost"])
    tp = int(best_pol["TP"])
    fp = int(best_pol["FP"])
    fn = int(best_pol["FN"])
    tn = int(best_pol["TN"])
    p_val = int(best_pol["P"])
    m_val = int(best_pol["M"])
    k_val = int(best_pol["K"])
    recall_pct = float(best_pol["recall"]) * 100.0
    saving_b0 = float(best_pol["saving_pct"])
    red_vs_b2 = 100.0 * (b2_cost - cost_star) / b2_cost

    print("\n[PHẦN 3] TỐI ƯU HÓA RÀNG BUỘC PHASE 2 (RANDOM FOREST + OPTUNA TPE — VALIDATION)")
    print("-" * 86)
    print(
        f"• Không gian tìm kiếm siêu tham số đã khóa ({PHASE2_CONFIG_PATH.relative_to(BASE_DIR).as_posix()}):\n"
        f"    - n_estimators in [{sp['n_estimators']['low']}, {sp['n_estimators']['high']}] (step {sp['n_estimators']['step']}), "
        f"max_depth in [{sp['max_depth']['low']}, {sp['max_depth']['high']}],\n"
        f"    - min_samples_split in [{sp['min_samples_split']['low']}, {sp['min_samples_split']['high']}], "
        f"max_features in [{sp['max_features']['low']:.2f}, {sp['max_features']['high']:.2f}]."
    )
    print(
        f"• Ngân sách & Tài nguyên: {budget['max_trials']} trials tuần tự ({p2_sum['completed_estimator_fits']} fits hoàn tất), "
        f"{res['max_native_threads']} luồng CPU, thời gian chạy {float(p2_sum['measured_wall_seconds']):.2f}s / trần {res['max_wall_seconds']}s, "
        f"đỉnh RAM {float(p2_sum['measured_peak_ram_mb']):.2f} MB / {res['max_ram_mb']} MB."
    )
    print(
        "• Cơ chế chọn ngưỡng tối ưu vs Lưới trực quan hóa:\n"
        "    - Tối ưu hóa ngưỡng thực tế: Đánh giá chính xác toàn bộ các giá trị xác suất dự báo duy nhất\n"
        "      trên tập Validation kèm hai đầu mút {0.0, 1.0} không cần huấn luyện lại mô hình.\n"
        "    - Lưới 101 điểm (0.00 đến 1.00, bước 0.01): Chỉ lưu kèm để vẽ đồ thị đánh đổi và phân tích độ nhạy."
    )
    print(
        f"\n• NGHIỆM KHẢ THI TỐT NHẤT QUAN SÁT ĐƯỢC TRONG {budget['max_trials']} TRIALS "
        f"(Optuna Trial #{trial_num} [0-indexed], lượt thử thứ {fit_idx}/20):"
    )
    print(
        f"    - Siêu tham số RF: n_estimators={rf_params['n_estimators']}, max_depth={rf_params['max_depth']}, "
        f"min_samples_split={rf_params['min_samples_split']}, max_features={float(rf_params['max_features']):.6f}"
    )
    print(f"    - Ngưỡng quyết định: tau* = {tau_star:.16f}")
    print(f"    - Kết quả Validation: TP={tp}/{p_val} (Recall {recall_pct:.2f}%), FP={fp}, FN={fn}, TN={tn:,}")
    print(
        f"    - Tổng chi phí: {ev['cost_fp_unit']}*{fp} + {ev['cost_fn_unit']}*{fn} = {cost_star:,} đơn vị "
        f"(tiết kiệm {saving_b0:.2f}% so với B0, giảm {red_vs_b2:.2f}% so với B2 [{b2_cost:,}])"
    )
    print(f"    - Công suất xưởng: M = {m_val} <= {k_val:,} (FEASIBLE, còn dư {k_val - m_val} lượt tiếp nhận)")

    tc = best_pol["threshold_curve"]
    sample_taus = [0.04, 0.05, 0.09, 0.20, 0.30, 0.32, 0.33, 0.34, 0.35, 0.50]
    selected_pts = [
        pt for pt in tc if any(abs(float(pt["threshold"]) - st) < 1e-6 for st in sample_taus)
    ]

    print("\n• ĐỘ NHẠY NGƯỠNG TRÊN LƯỚI 101 ĐIỂM CỦA TRIAL 16 (TRÍCH XUẤT TỪ best_policy.json):")
    print("  +----------+---------+-----+------+-----+--------+-------------+")
    print("  | Ngưỡng τ | Chi phí |  TP |  FP  |  FN |    M   | Khả thi M≤K |")
    print("  +----------+---------+-----+------+-----+--------+-------------+")
    inserted_star = False
    for pt in selected_pts:
        t_val = float(pt["threshold"])
        if not inserted_star and t_val > tau_star:
            print(
                f"  | *{tau_star:.4f} | {cost_star:>7,} | {tp:>3} | {fp:>4} | {fn:>3} | {m_val:>6,} | "
                f"{'FEASIBLE':<11} | <- Nghiệm chọn (exact candidate)"
            )
            inserted_star = True
        feas_str = "FEASIBLE" if pt["feasible"] else "INFEASIBLE"
        print(
            f"  |   {t_val:.2f}   | {int(pt['cost']):>7,} | {int(pt['TP']):>3} | {int(pt['FP']):>4} | "
            f"{int(pt['FN']):>3} | {int(pt['M']):>6,} | {feas_str:<11} |"
        )
    print("  +----------+---------+-----+------+-----+--------+-------------+")
    print("  => Nhận xét thực nghiệm từ đường cong ngưỡng:")
    print("     1. Ranh giới khả thi thực tế nằm giữa tau=0.04 (M=1,314 > 1,200, INFEASIBLE) và")
    print("        tau=0.05 (M=1,195 <= 1,200, FEASIBLE); các mức tau in [0.05, 0.09] vẫn khả thi.")
    print("     2. Trong đoạn tau in [0.20, 0.32], FN giữ ở mức 4–5 ca nên chi phí nằm trong [6,350; 7,050];")
    print("        ứng viên xác suất chính xác tau* = 0.323244 đạt chi phí thấp nhất quan sát được là 6,330.")
    print("     3. Từ tau >= 0.33, FN tăng từ 5 lên 7, 9, 10 ca (mỗi ca phạt 500) làm chi phí tăng dốc")
    print("        (7,290 -> 8,230 -> 8,670). Đây là nghiệm tốt nhất trong 20 trials, không tuyên bố tối ưu toàn cục.")


def step_4_official_test_g10(ev: Dict[str, Any]) -> None:
    tm = ev["g10_test"]
    vg = ev["g10_val_guard"]
    pol = ev["g10_policy"]
    tel = pol.get("execution_telemetry", {})

    tp = int(tm["TP"])
    fp = int(tm["FP"])
    fn = int(tm["FN"])
    tn = int(tm["TN"])
    n_test = int(tm["N"])
    p_test = int(tm["P"])
    m_test = int(tm["M"])
    k_test = int(tm["K"])
    cost_test = int(tm["total_cost"])
    ref_cost = int(tm["reference_cost"])
    saving_pct = float(tm["saving_pct"])

    print(f"\n[PHẦN 4] ĐÁNH GIÁ ĐỘC LẬP TRÊN OFFICIAL TEST (GATE G10: N = {n_test:,}, P = {p_test}, K = {k_test:,})")
    print("-" * 86)
    print(
        f"• Chế độ thực thi đã lưu: {pol.get('evaluation_mode')} "
        f"(1 lần refit xác định trên Train 48k [{float(tel.get('fit_duration_seconds', 0.0)):.2f}s],\n"
        f"  Validation Guard khớp chính xác Cost={int(vg['total_cost']):,}, M={int(vg['M'])}; "
        f"suy luận Test 1 lần [{float(tm.get('predict_seconds', 0.0)):.4f}s], 0 tinh chỉnh)."
    )
    print("\n  +-------------------------------+-------------------+-------------------+---------------------+")
    print("  | Chỉ số đánh giá               | Validation (12k)  | B0 Dummy (Test)   | Official Test (G10) |")
    print("  +-------------------------------+-------------------+-------------------+---------------------+")
    print(f"  | True Positives (TP)           | {int(vg['TP']):>17,} | {0:>17,} | {tp:>19,} |")
    print(f"  | False Positives (FP)          | {int(vg['FP']):>17,} | {0:>17,} | {fp:>19,} |")
    print(f"  | False Negatives (FN)          | {int(vg['FN']):>17,} | {p_test:>17,} | {fn:>19,} |")
    print(f"  | True Negatives (TN)           | {int(vg['TN']):>17,} | {n_test - p_test:>17,} | {tn:>19,} |")
    print(f"  | Recall (Độ nhạy)              | {float(vg['recall'])*100:>16.2f}% | {'0.00%':>17} | {float(tm['recall'])*100:>18.2f}% |")
    print(f"  | Precision (Độ chính xác)      | {float(vg['precision'])*100:>16.2f}% | {'N/A':>17} | {float(tm['precision'])*100:>18.2f}% |")
    print(f"  | Specificity (Độ đặc hiệu)     | {float(vg['specificity'])*100:>16.2f}% | {'100.00%':>17} | {float(tm['specificity'])*100:>18.2f}% |")
    print(f"  | ROC-AUC / PR-AUC              | {float(vg['roc_auc']):.4f} / {float(vg['pr_auc']):.4f}   | {'N/A':>17} |   {float(tm['roc_auc']):.4f} / {float(tm['pr_auc']):.4f} |")
    print(f"  | Chi phí kiểm tra (10 * FP)    | {int(vg['cost_fp']):>17,} | {0:>17,} | {int(tm['cost_fp']):>19,} |")
    print(f"  | Chi phí bỏ sót (500 * FN)     | {int(vg['cost_fn']):>17,} | {ref_cost:>17,} | {int(tm['cost_fn']):>19,} |")
    print(f"  | TỔNG CHI PHÍ BENCHMARK        | {int(vg['total_cost']):>17,} | {ref_cost:>17,} | {cost_test:>19,} |")
    print(f"  | Tiết kiệm so với B0           | {float(vg['saving_pct']):>16.2f}% | {'0.00%':>17} | {saving_pct:>18.2f}% |")
    val_cap_str = f"{int(vg['M'])}/{int(vg['K']):,}"
    b0_cap_str = f"0/{k_test:,}"
    test_cap_str = f"{m_test}/{k_test:,}"
    print(f"  | Lượt xe vào xưởng (M <= K)    | {val_cap_str:>17} | {b0_cap_str:>17} | {test_cap_str:>19} |")
    print(f"  | Trạng thái khả thi            | {vg['policy_status']:>17} | {'FEASIBLE':>17} | {tm['policy_status']:>19} |")
    print("  +-------------------------------+-------------------+-------------------+---------------------+")

    print("\n• Ma trận nhầm lẫn Official Test (đối chiếu khớp confusion_matrix_test.csv):")
    for r in ev["g10_cm_rows"]:
        print(
            f"    Thực tế {r['actual']:<5}: Dự đoán Âm={int(r['pred_neg']):>6,}, "
            f"Dự đoán Dương={int(r['pred_pos']):>5,} | Tổng={int(r['total']):>6,}"
        )

    print("\n• Ghi chú minh bạch học thuật & giới hạn áp dụng:")
    print("  1. Lịch sử G10 Runs 001/002: Tệp CSV Test đã được đọc vào bộ nhớ trước khi dừng tại bước kiểm tra")
    print("     preprocessor/import; không có dự đoán xác suất, chấm điểm hay điều chỉnh tham số nào diễn ra.")
    print("  2. Hạn chế thực nghiệm: Tối ưu hóa chạy trên 1 hạt giống cố định (seed=42), chưa đánh giá phương sai")
    print("     đa hạt giống; chi phí 10*FP + 500*FN và trần công suất 10% là mô hình benchmark tĩnh.")


def print_speaker_notes(ev: Dict[str, Any]) -> None:
    b2_cost = int(ev["b2_sec"]["total_cost"])
    p2_best = ev["p2_best"]
    tm = ev["g10_test"]
    tau_star = float(p2_best["threshold"])
    val_cost = int(p2_best["total_cost"])
    val_m = int(p2_best["M"])
    test_cost = int(tm["total_cost"])
    test_m = int(tm["M"])
    test_saving = float(tm["saving_pct"])
    test_recall = float(tm["recall"]) * 100.0

    print("\n" + "=" * 86)
    print("  GỢI Ý DÀN Ý THUYẾT TRÌNH & BẢO VỆ ĐỒ ÁN CÁ NHÂN (5–7 PHÚT)")
    print("=" * 86)
    print(
        f"""1. Phút 0:00 – 1:00 | Đặt vấn đề & Mô hình hóa tối ưu (Slide 1–3)
   - Bài toán chẩn đoán lỗi hệ thống khí nén APS xe tải Scania (UCI #421) có tỷ lệ phạt bất đối xứng 50:1
     (bỏ sót lỗi FN tốn 500 đơn vị; kiểm tra thừa FP tốn 10 đơn vị).
   - Biến quyết định gồm siêu tham số Random Forest theta và ngưỡng xác suất tau in [0, 1].
   - Hàm mục tiêu min (10*FP + 500*FN) chịu ràng buộc công suất xưởng M = TP + FP <= floor(N/10).

2. Phút 1:00 – 2:15 | Giao thức dữ liệu & Đường cơ sở G4 (Slide 4–6)
   - Dữ liệu phát triển 60.000 mẫu tách phân tầng thành Train 48.000 và Validation 12.000 (seed=42);
     tiền xử lý chỉ fit trên Train để tránh rò rỉ dữ liệu.
   - Trên tập Validation, mô hình cơ sở tốt nhất là Logistic Regression (B2) tại ngưỡng lý thuyết Bayes
     tau = 10/510 ≈ 0.0196, đạt chi phí {b2_cost:,} đơn vị (M = {int(ev['b2_sec']['M'])} <= 1.200).

3. Phút 2:15 – 4:15 | Tối ưu hóa Phase 2 & Phân tích đánh đổi, độ nhạy (Slide 7)
   - Chạy 20 trials Optuna TPE (max_features in [0.20, 0.50], n_estimators in [20, 60], max_depth in [4, 12],
     min_samples_split in [2, 10]); mỗi trial đánh giá toàn bộ ngưỡng ứng viên xác suất duy nhất trên Validation.
   - Nghiệm khả thi tốt nhất quan sát được ở Trial 16 (tau* = {tau_star:.4f}) đạt chi phí {val_cost:,} đơn vị,
     M = {val_m} <= 1.200, giảm 38.12% chi phí so với B2 ({b2_cost:,}).
   - Trên lưới 101 điểm của Trial 16: chỉ tau <= 0.04 mới vượt trần 1.200 xe (tau=0.04 có M=1.314; tau=0.05
     có M=1.195 đã khả thi); vùng [0.20, 0.32] giữ chi phí [6.350; 7.050], còn từ tau >= 0.33 chi phí tăng dốc
     (7.290 -> 8.230 -> 8.670) do số ca bỏ sót FN tăng.

4. Phút 4:15 – 6:00 | Đánh giá độc lập Official Test (Gate G10) & Hạn chế nghiên cứu (Slide 8)
   - Khóa cấu hình Trial 16, refit xác định 1 lần trên Train 48k (kiểm tra khớp lại kết quả Validation) và
     đánh giá 1 lần trên 16.000 mẫu Official Test: đạt chi phí {test_cost:,} đơn vị, tiết kiệm {test_saving:.2f}%
     so với B0 (187.500), Recall đạt {test_recall:.2f}% (357/375 ca lỗi), M = {test_m} <= 1.600.
   - Nêu rõ giới hạn: thực nghiệm dùng 1 seed cố định (seed=42), chưa tách riêng baseline Random Forest mặc định,
     không lưu file mô hình .joblib nên bản demo trình bày kết quả thực nghiệm đã lưu và kiểm tra mã băm SHA-256."""
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Demo đọc kết quả thực nghiệm đã lưu và kiểm tra tính toàn vẹn (Scania APS UCI 421)"
    )
    parser.add_argument("--summary", action="store_true", help="Chỉ hiển thị tóm tắt số liệu từ JSON/CSV")
    parser.add_argument("--verify", action="store_true", help="Kiểm tra tính nhất quán toán học và mã băm SHA-256")
    parser.add_argument("--notes", action="store_true", help="Hiển thị dàn ý thuyết trình bảo vệ 5–7 phút")
    args = parser.parse_args()

    try:
        ev = load_and_validate_all_evidence()
        if args.verify:
            print_banner()
            ok = verify_all_artifact_checksums(verbose=True)
            return 0 if ok else 1

        if args.notes:
            ok = verify_all_artifact_checksums(verbose=False)
            if not ok:
                raise DemoIntegrityError("Phát hiện sai lệch mã băm SHA-256 trong các tệp kết quả gốc.")
            print_speaker_notes(ev)
            return 0

        if args.summary:
            ok = verify_all_artifact_checksums(verbose=False)
            if not ok:
                raise DemoIntegrityError("Phát hiện sai lệch mã băm SHA-256 trong các tệp kết quả gốc.")
            print_banner()
            step_2_baselines(ev)
            step_3_phase2_optimization(ev)
            step_4_official_test_g10(ev)
            return 0

        print_banner()
        step_1_problem_formulation(ev)
        step_2_baselines(ev)
        step_3_phase2_optimization(ev)
        step_4_official_test_g10(ev)
        ok = verify_all_artifact_checksums(verbose=True)
        if not ok:
            return 1
        print_speaker_notes(ev)
        return 0

    except DemoIntegrityError as exc:
        print(f"\n[DEMO DỪNG DO LỖI TOÀN VẸN DỮ LIỆU]\n{exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\n[LỖI KHÔNG MONG ĐỢI TRONG DEMO]\n{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
