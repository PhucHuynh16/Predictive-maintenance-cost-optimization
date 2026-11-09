"""Phase 2 Visualization: Convergence and Cost vs Capacity Trade-off curves.

Scope: Antigravity.
Artifacts:
1. figures/optimization/optimization_convergence.png: Optuna TPE trial convergence vs B0 and B2.
2. figures/optimization/cost_vs_capacity_tradeoff.png: Benchmark Cost vs Maintenance Capacity M.
"""
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def set_plot_style() -> None:
    """Set standardized styling for academic optimization plots."""
    plt.rcParams.update({
        "figure.autolayout": True,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 300,
    })


def plot_phase2_optimization_convergence(
    trials_records: List[Dict[str, Any]],
    baseline_b2_cost: float = 10230.0,
    baseline_b0_cost: float = 100000.0,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Optuna TPE convergence curve over trials compared to B2 and B0 baselines.

    Uses a 2-panel academic layout:
    - Left panel: Global perspective showing baseline B0 (100,000) vs B2 (10,230) vs Phase 2 trials.
    - Right panel: Detailed convergence zoomed into [5,500 - 11,000] showing trial progression and step-down curve.
    """
    set_plot_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1, 1.3]})

    trial_numbers = [t["trial_number"] + 1 for t in trials_records]
    costs = [t["objective_value"] for t in trials_records]
    feasible_flags = [t.get("status") == "FEASIBLE" for t in trials_records]

    # Cumulative minimum
    cum_min = []
    current_min = float("inf")
    for c, feas in zip(costs, feasible_flags):
        if feas and c < current_min:
            current_min = c
        cum_min.append(current_min if current_min != float("inf") else c)

    # --- PANEL 1: GLOBAL PERSPECTIVE ---
    ax1.axhline(baseline_b0_cost, color="#7f7f7f", linestyle=":", linewidth=1.5,
                label=f"B0 Majority Dummy ({int(baseline_b0_cost):,})")
    ax1.axhline(baseline_b2_cost, color="#2ca02c", linestyle="--", linewidth=1.6,
                label=f"B2 Logistic Regression ({int(baseline_b2_cost):,})")
    ax1.plot(trial_numbers, cum_min, color="#1f77b4", linewidth=2.0,
             label="Chính sách tốt nhất lũy tiến")
    ax1.scatter(trial_numbers, costs, color="#1f77b4", s=35, alpha=0.7)

    ax1.set_title("Toàn cảnh chi phí (So với B0 Dummy)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Số thứ tự Trial (1–20)", fontsize=10)
    ax1.set_ylabel("Tổng chi phí benchmark", fontsize=10)
    ax1.set_ylim(-2000, 108000)
    ax1.set_xticks(range(2, len(trial_numbers) + 1, 2))
    ax1.legend(loc="upper right", frameon=True, fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    # --- PANEL 2: ZOOMED CONVERGENCE DETAIL ---
    ax2.axhline(baseline_b2_cost, color="#2ca02c", linestyle="--", linewidth=1.8,
                label=f"B2 Logistic Regression: {int(baseline_b2_cost):,}")

    # Plot trials scatter
    ax2.scatter([num for num, feas in zip(trial_numbers, feasible_flags) if feas],
                [c for c, feas in zip(costs, feasible_flags) if feas],
                color="#1f77b4", s=55, alpha=0.8, zorder=4,
                label="Trial khả thi (Feasible Trial)")

    # Plot step-down convergence curve
    ax2.step(trial_numbers, cum_min, where="post", color="#d62728", linewidth=2.4, zorder=5,
             label="Chi phí khả thi tốt nhất lũy tiến (Best So Far)")

    # Highlight milestones
    best_overall_cost = min(cum_min)
    best_trial_idx = cum_min.index(best_overall_cost) + 1
    ax2.scatter([best_trial_idx], [best_overall_cost], color="#ff7f0e", s=180, marker="*",
                edgecolors="black", linewidth=1.2, zorder=6,
                label=f"Chính sách tốt nhất quan sát được (Trial {best_trial_idx}: {int(best_overall_cost):,})")

    ax2.annotate(f"Trial {best_trial_idx}: Cost = {int(best_overall_cost):,}\n(-38.12% vs B2)",
                 xy=(best_trial_idx, best_overall_cost), xytext=(best_trial_idx - 5, best_overall_cost + 800),
                 arrowprops=dict(facecolor="black", shrink=0.08, width=1.0, headwidth=6),
                 fontsize=9, fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#fff2cc", ec="#d6b656", lw=1))

    ax2.set_title("Tiến trình hội tụ Optuna TPE (Chi tiết thu phóng)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Số thứ tự Trial (1 đến 20)", fontsize=10)
    ax2.set_ylabel("Chi phí benchmark (10*FP + 500*FN)", fontsize=10)
    ax2.set_ylim(5500, 11000)
    ax2.set_xticks(range(1, len(trial_numbers) + 1))
    ax2.legend(loc="upper right", frameon=True, fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_phase2_cost_vs_capacity_tradeoff(
    trials_records: List[Dict[str, Any]],
    best_trial: Optional[Dict[str, Any]] = None,
    capacity_limit: int = 1200,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot Benchmark Cost vs Maintenance Capacity M across optimization configurations and genuine threshold sweep."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    best_bp = best_trial.get("best_policy") if best_trial else None

    # 1. Plot genuine threshold trade-off curve from saved threshold_curve observations
    if best_bp and "threshold_curve" in best_bp:
        tc = best_bp["threshold_curve"]
        feas_tc = sorted([pt for pt in tc if pt.get("feasible")], key=lambda pt: pt["M"])
        if feas_tc:
            ax.plot([pt["M"] for pt in feas_tc], [pt["cost"] for pt in feas_tc],
                    color="#1f77b4", linewidth=2.2, linestyle="-", zorder=3,
                    label="Đường quét ngưỡng thực nghiệm 101 điểm τ ∈ [0, 1] (Trial 16)")

    # 2. Scatter of all trial policies (M vs Cost across 20 trials)
    m_values = []
    costs = []
    labels = []
    for t in trials_records:
        bp = t.get("best_policy")
        if bp and bp.get("M") is not None:
            m_values.append(bp["M"])
            costs.append(bp["total_cost"])
            labels.append(t["trial_number"] + 1)

    if m_values:
        scatter = ax.scatter(m_values, costs, c=labels, cmap="YlGnBu", s=70, edgecolors="black", linewidth=0.8,
                             alpha=0.9, zorder=4, label="Chính sách tối ưu từng trial (20 Optuna Trials)")
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Thứ tự Trial (1–20)")

    # 3. Mark capacity limit & feasible region
    ax.axvline(capacity_limit, color="#d62728", linestyle="--", linewidth=1.8,
               label=f"Giới hạn năng lực xưởng K = {capacity_limit} xe (10% N_val)")
    ax.axvspan(0, capacity_limit, color="#2ca02c", alpha=0.08, label="Vùng khả thi (Feasible Domain: M ≤ 1200)")

    # 4. Mark Best Selected Policy
    if best_bp and best_bp.get("M") is not None:
        ax.scatter([best_bp["M"]], [best_bp["total_cost"]], color="#ff7f0e", s=220, marker="*",
                   edgecolors="black", linewidth=1.4, zorder=6,
                   label=f"Chính sách khả thi tốt nhất quan sát được (Trial 16: M={best_bp['M']}, Cost={best_bp['total_cost']:,}, τ*={best_bp['threshold']:.4f})")

    # 5. Reference B2 baseline point (M=509, Cost=10230)
    ax.scatter([509], [10230], color="#2ca02c", s=130, marker="D", edgecolors="black", linewidth=1.2,
               zorder=5, label="Mốc cơ sở B2 Logistic Regression (M=509, Cost=10,230)")

    ax.set_title("Đánh đổi giữa Chi phí Benchmark và Năng lực tiếp nhận của Xưởng (M = TP + FP)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Số lượt xe đưa vào kiểm tra APS (M = TP + FP)", fontsize=11)
    ax.set_ylabel("Tổng chi phí benchmark (Cost = 10*FP + 500*FN)", fontsize=11)
    ax.set_xlim(-30, 1350)
    ax.legend(loc="upper right", frameon=True, fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig
