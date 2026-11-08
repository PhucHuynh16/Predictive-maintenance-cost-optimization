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
    """Plot Optuna TPE convergence curve over trials compared to B2 and B0 baselines."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))

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

    # Plot baseline reference lines
    ax.axhline(baseline_b0_cost, color="#7f7f7f", linestyle=":", linewidth=1.5,
               label=f"B0 Majority Dummy (Cost = {int(baseline_b0_cost):,})")
    ax.axhline(baseline_b2_cost, color="#2ca02c", linestyle="--", linewidth=1.8,
               label=f"B2 Logistic Regression Best Baseline (Cost = {int(baseline_b2_cost):,})")

    # Plot trials
    ax.scatter([num for num, feas in zip(trial_numbers, feasible_flags) if feas],
               [c for c, feas in zip(costs, feasible_flags) if feas],
               color="#1f77b4", s=50, alpha=0.7, label="Trial khả thi (Feasible Trial)")
    ax.scatter([num for num, feas in zip(trial_numbers, feasible_flags) if not feas],
               [c for c, feas in zip(costs, feasible_flags) if not feas],
               color="#d62728", s=60, marker="x", label="Trial không khả thi (Infeasible)")

    # Plot convergence curve
    ax.step(trial_numbers, cum_min, where="post", color="#1f77b4", linewidth=2.2,
            label="Chi phí tốt nhất lũy tiến (Best So Far)")

    ax.set_title("Đường cong hội tụ tối ưu hóa siêu tham số (Optuna TPE: Random Forest)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Số thứ tự Trial (1 đến 20)", fontsize=11)
    ax.set_ylabel("Tổng chi phí benchmark (Cost = 10*FP + 500*FN)", fontsize=11)
    ax.set_xticks(range(1, len(trial_numbers) + 1))
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

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
    """Plot Benchmark Cost vs Maintenance Capacity M across optimization configurations."""
    set_plot_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Scatter of all trials (M vs Cost)
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
        scatter = ax.scatter(m_values, costs, c=labels, cmap="Blues", s=60, edgecolors="black", linewidth=0.8,
                             alpha=0.85, label="Các trial tối ưu hóa (Phase 2 Trials)")
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label("Thứ tự Trial")

    # Mark capacity limit
    ax.axvline(capacity_limit, color="#d62728", linestyle="--", linewidth=1.8,
               label=f"Giới hạn công suất xưởng K = {capacity_limit} xe (10% N_val)")
    ax.axvspan(0, capacity_limit, color="#2ca02c", alpha=0.08, label="Vùng khả thi (Feasible Domain: M <= 1200)")

    # Mark Best Selected Policy
    best_bp = best_trial.get("best_policy") if best_trial else None
    if best_bp and best_bp.get("M") is not None:
        ax.scatter([best_bp["M"]], [best_bp["total_cost"]], color="#ff7f0e", s=180, marker="*",
                   edgecolors="black", linewidth=1.2, zorder=5,
                   label=f"Nghiệm tối ưu được chọn (M={best_bp['M']}, Cost={best_bp['total_cost']:,}, τ={best_bp['threshold']:.4f})")

    # Reference B2 baseline point (M=509, Cost=10230)
    ax.scatter([509], [10230], color="#2ca02c", s=120, marker="D", edgecolors="black", linewidth=1.0,
               zorder=4, label="Mốc cơ sở B2 Logistic Regression (M=509, Cost=10,230)")

    ax.set_title("Đánh đổi giữa Chi phí Benchmark và Năng lực tiếp nhận của Xưởng (M = TP + FP)",
                 fontsize=13, fontweight="bold")
    ax.set_xlabel("Số lượt xe đưa vào kiểm tra APS (M = TP + FP)", fontsize=11)
    ax.set_ylabel("Tổng chi phí benchmark (Cost = 10*FP + 500*FN)", fontsize=11)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig
