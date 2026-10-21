"""Module cung cấp các hàm trực quan hóa dữ liệu và kết quả thực nghiệm.

Phạm vi quản lý: Antigravity.
Quy tắc:
- Mọi biểu đồ được tạo ra từ dữ liệu thật, không sinh kết quả giả.
- Hỗ trợ lưu biểu đồ độ phân giải cao (DPI 300) vào thư mục figures/.
"""

from typing import List, Optional
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def set_plot_style() -> None:
    """Thiết lập style hiển thị chuẩn cho đồ thị."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams.update({
        "figure.autolayout": True,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 300,
    })


def plot_target_and_subfailures(df: pd.DataFrame, save_path: Optional[str] = None) -> plt.Figure:
    """Vẽ phân bố của Machine failure (mất cân bằng) và 5 nhãn hỏng hóc phụ."""
    set_plot_style()
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # 1. Target distribution
    target_counts = df["Machine failure"].value_counts().sort_index()
    labels = ["Không hỏng (0)", "Hỏng hóc (1)"]
    colors = ["#2b5c8f", "#d95f02"]
    axes[0].bar(labels, target_counts.values, color=colors, width=0.5, edgecolor="black", linewidth=0.8)
    axes[0].set_title("Phân bố nhãn mục tiêu (Machine failure)")
    axes[0].set_ylabel("Số lượng quan sát")
    for i, v in enumerate(target_counts.values):
        pct = (v / len(df)) * 100
        axes[0].text(i, v + 120, f"{v:,}\n({pct:.2f}%)", ha="center", fontweight="bold", fontsize=10)
    axes[0].set_ylim(0, 11000)

    # 2. Sub-failure modes
    sub_cols = ["TWF", "HDF", "PWF", "OSF", "RNF"]
    sub_counts = [int(df[c].sum()) for c in sub_cols]
    sub_names = [
        f"TWF (Tool Wear)\n[n={df['TWF'].sum()}]",
        f"HDF (Heat Diss.)\n[n={df['HDF'].sum()}]",
        f"PWF (Power)\n[n={df['PWF'].sum()}]",
        f"OSF (Overstrain)\n[n={df['OSF'].sum()}]",
        f"RNF (Random)\n[n={df['RNF'].sum()}]",
    ]
    sns.barplot(
        x=sub_names,
        y=sub_counts,
        hue=sub_names,
        legend=False,
        ax=axes[1],
        palette="flare",
        edgecolor="black",
        linewidth=0.8,
    )
    axes[1].set_title("Tần suất xuất hiện của 5 dạng hỏng hóc độc lập")
    axes[1].set_ylabel("Số quan sát xảy ra hỏng")
    axes[1].set_xlabel("Chế độ hỏng hóc")
    for i, v in enumerate(sub_counts):
        axes[1].text(i, v + 3, str(v), ha="center", fontweight="bold", fontsize=10)
    axes[1].set_ylim(0, max(sub_counts) + 20)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_numerical_distributions(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Vẽ histogram kèm KDE cho các biến liên tục."""
    set_plot_style()
    if features is None:
        features = [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
        ]

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    axes = axes.flatten()

    for idx, col in enumerate(features):
        ax = axes[idx]
        sns.histplot(df[col], kde=True, ax=ax, color="#1f77b4", bins=30, edgecolor="black", linewidth=0.5)
        ax.set_title(f"Phân phối: {col}")
        ax.set_xlabel(col)
        ax.set_ylabel("Tần số")

    # Slot cuối cùng vẽ phân bố phân loại Type
    ax_last = axes[len(features)]
    type_counts = df["Type"].value_counts()
    sns.barplot(
        x=type_counts.index,
        y=type_counts.values,
        hue=type_counts.index,
        legend=False,
        ax=ax_last,
        palette="Blues_r",
        edgecolor="black",
    )
    ax_last.set_title("Phân bố đặc trưng phân loại: Type (Chất lượng sản phẩm)")
    ax_last.set_xlabel("Loại sản phẩm (L=Low, M=Medium, H=High)")
    ax_last.set_ylabel("Số lượng")
    for i, v in enumerate(type_counts.values):
        ax_last.text(i, v + 100, f"{v:,} ({(v/len(df))*100:.1f}%)", ha="center", fontweight="bold")
    ax_last.set_ylim(0, 7000)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_boxplots_by_target(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    target_col: str = "Machine failure",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Vẽ boxplot cho từng biến số học phân tầng theo nhãn Machine failure."""
    set_plot_style()
    if features is None:
        features = [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
        ]

    fig, axes = plt.subplots(1, 5, figsize=(18, 5))

    plot_df = df.copy()
    plot_df["Target_Label"] = plot_df[target_col].map({0: "Không hỏng (0)", 1: "Hỏng (1)"})
    palette = {"Không hỏng (0)": "#4575b4", "Hỏng (1)": "#d73027"}

    for idx, col in enumerate(features):
        ax = axes[idx]
        sns.boxplot(
            data=plot_df,
            x="Target_Label",
            y=col,
            hue="Target_Label",
            legend=False,
            ax=ax,
            palette=palette,
            width=0.45,
            fliersize=3,
        )
        ax.set_title(col, fontsize=11, fontweight="bold")
        ax.set_xlabel("Trạng thái máy")
        ax.set_ylabel("")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_correlation_matrix(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Vẽ ma trận tương quan Pearson giữa các đặc trưng và nhãn mục tiêu."""
    set_plot_style()
    if features is None:
        features = [
            "Air temperature [K]",
            "Process temperature [K]",
            "Rotational speed [rpm]",
            "Torque [Nm]",
            "Tool wear [min]",
            "Machine failure",
        ]

    corr = df[features].corr(method="pearson")

    fig, ax = plt.subplots(figsize=(8, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(
        corr,
        mask=mask,
        annot=True,
        fmt=".3f",
        cmap="coolwarm",
        center=0,
        square=True,
        linewidths=0.8,
        cbar_kws={"shrink": 0.8, "label": "Hệ số tương quan Pearson"},
        ax=ax,
    )
    ax.set_title("Ma trận tương quan Pearson giữa các đặc trưng số học & Target", pad=15)

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_physical_mechanisms(df: pd.DataFrame, save_path: Optional[str] = None) -> plt.Figure:
    """Vẽ các ranh giới cơ chế vật lý sinh ra sự cố (PWF, HDF, OSF)."""
    set_plot_style()
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 1. PWF: Power = Torque * (Speed * 2 * pi / 60)
    ax0 = axes[0]
    sns.scatterplot(
        x=df["Rotational speed [rpm]"],
        y=df["Torque [Nm]"],
        hue=df["PWF"].map({0: "Bình thường", 1: "Lỗi nguồn (PWF)"}),
        palette={"Bình thường": "#9ecae1", "Lỗi nguồn (PWF)": "#de2d26"},
        alpha=0.7,
        s=20,
        ax=ax0,
    )
    ax0.set_title("Cơ chế PWF: Công suất ngoài dải [3500W, 9000W]")
    ax0.set_xlabel("Rotational speed [rpm]")
    ax0.set_ylabel("Torque [Nm]")

    # 2. HDF: Temp difference < 8.6 K & Speed < 1380 rpm
    temp_diff = df["Process temperature [K]"] - df["Air temperature [K]"]
    ax1 = axes[1]
    sns.scatterplot(
        x=df["Rotational speed [rpm]"],
        y=temp_diff,
        hue=df["HDF"].map({0: "Bình thường", 1: "Lỗi tản nhiệt (HDF)"}),
        palette={"Bình thường": "#9ecae1", "Lỗi tản nhiệt (HDF)": "#fc8d59"},
        alpha=0.7,
        s=20,
        ax=ax1,
    )
    ax1.axhline(8.6, color="red", linestyle="--", linewidth=1.2, label="Ngưỡng ΔT = 8.6 K")
    ax1.axvline(1380, color="blue", linestyle="--", linewidth=1.2, label="Ngưỡng Vận tốc = 1380 rpm")
    ax1.set_title("Cơ chế HDF: ΔT < 8.6 K & Vận tốc < 1380 rpm")
    ax1.set_xlabel("Rotational speed [rpm]")
    ax1.set_ylabel("Chênh lệch nhiệt độ ΔT [K]")
    ax1.legend(loc="upper right")

    # 3. OSF: Overstrain = Tool wear * Torque
    ax2 = axes[2]
    sns.scatterplot(
        x=df["Tool wear [min]"],
        y=df["Torque [Nm]"],
        hue=df["OSF"].map({0: "Bình thường", 1: "Lỗi quá tải (OSF)"}),
        palette={"Bình thường": "#9ecae1", "Lỗi quá tải (OSF)": "#756bb1"},
        alpha=0.7,
        s=20,
        ax=ax2,
    )
    ax2.set_title("Cơ chế OSF: Mài mòn x Mô-men xoắn vượt ngưỡng")
    ax2.set_xlabel("Tool wear [min]")
    ax2.set_ylabel("Torque [Nm]")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig


def plot_temporal_patterns(df: pd.DataFrame, save_path: Optional[str] = None) -> plt.Figure:
    """Vẽ xu hướng nhiệt độ và cụm lỗi HDF theo thứ tự chỉ số quan sát UDI."""
    set_plot_style()
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    # 1. Nhiệt độ môi trường và nhiệt độ quá trình theo chu kỳ
    axes[0].plot(df["UDI"], df["Air temperature [K]"], color="#1f77b4", linewidth=0.8, label="Air temperature [K]")
    axes[0].plot(df["UDI"], df["Process temperature [K]"], color="#ff7f0e", linewidth=0.8, alpha=0.8, label="Process temperature [K]")
    axes[0].set_ylabel("Nhiệt độ [K]")
    axes[0].set_title("Biến thiên nhiệt độ môi trường & quá trình theo thứ tự chỉ số quan sát UDI")
    axes[0].legend(loc="upper right")

    # 2. Vị trí xuất hiện của HDF và các lỗi khác
    hdf_indices = df[df["HDF"] == 1]["UDI"]
    other_fail_indices = df[(df["Machine failure"] == 1) & (df["HDF"] == 0)]["UDI"]
    axes[1].scatter(hdf_indices, [1] * len(hdf_indices), color="#d73027", s=30, label=f"HDF (Lỗi tản nhiệt, n={len(hdf_indices)})", marker="|")
    axes[1].scatter(other_fail_indices, [0.5] * len(other_fail_indices), color="#4575b4", s=20, alpha=0.6, label=f"Lỗi khác (n={len(other_fail_indices)})", marker="o")
    axes[1].axvspan(3000, 5000, color="orange", alpha=0.15, label="Cụm nhiệt độ cao & tập trung HDF (UDI 3000-5000)")
    axes[1].set_yticks([0.5, 1.0])
    axes[1].set_yticklabels(["Lỗi khác", "HDF"])
    axes[1].set_xlabel("Chỉ số quan sát (UDI: 1 đến 10,000)")
    axes[1].set_title("Vị trí xuất hiện sự cố: HDF tập trung tuyệt đối vào giai đoạn nhiệt độ cao (UDI 3000-5000)")
    axes[1].legend(loc="upper right")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
    return fig
