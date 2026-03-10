# ============================================================
# analyzers/text_dataset/reporter.py — Text Dataset Reports
# ============================================================
# WHAT: Charts and tables specifically for text+label datasets.
# USED BY: analyzers/text_dataset/ui.py displays these.
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")


def chart_quality_gauge(score: float) -> plt.Figure:
    """Semi-circle gauge showing quality score 0-100."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={"projection": "polar"})
    theta = np.pi * (1 - score / 100)
    color = "#2ecc71" if score >= 80 else ("#f39c12" if score >= 50 else "#e74c3c")

    bg_angles = np.linspace(0, np.pi, 100)
    ax.fill_between(bg_angles, 0, 1, color="#eee", alpha=0.5)

    score_angles = np.linspace(np.pi, theta, 100)
    ax.fill_between(score_angles, 0, 1, color=color, alpha=0.7)

    ax.plot([theta, theta], [0, 0.85], color="#333", linewidth=2)
    ax.scatter([theta], [0.85], color="#333", s=30, zorder=5)

    ax.set_ylim(0, 1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title(f"Text Dataset Quality Score: {score}%", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig


def build_issue_table(results: dict) -> pd.DataFrame:
    ic = results.get("issue_counts", {})
    total = max(1, results["total_rows"])
    rows = []
    for name, count in ic.items():
        pct = round(count / total * 100, 2)
        severity = "— None" if count == 0 else ("Low" if pct < 5 else ("Medium" if pct < 20 else "High"))
        rows.append({"Issue": name.replace("_", " ").title(), "Count": count, "% of Rows": pct, "Severity": severity})
    return pd.DataFrame(rows)


def chart_issue_breakdown(results: dict) -> plt.Figure | None:
    data = {k.replace("_", " ").title(): v for k, v in results.get("issue_counts", {}).items() if v > 0}
    if not data:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(list(data.keys()), list(data.values()), color="#e67e22", edgecolor="white")
    ax.set_title("Issue Breakdown", fontsize=13, fontweight="bold")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45)
    for bar, val in zip(bars, data.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    return fig


def chart_label_distribution(results: dict) -> plt.Figure | None:
    dist = results.get("label_distribution")
    if not dist:
        return None
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(list(dist.values()), labels=list(dist.keys()), autopct="%1.1f%%",
           startangle=90, colors=plt.cm.Set3.colors)
    ax.set_title("Label Distribution", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


def chart_text_length_histogram(df: pd.DataFrame, text_col: str) -> plt.Figure:
    lengths = df[text_col].astype("string").str.strip().str.len().dropna()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(lengths, bins=30, color="#3498db", edgecolor="white")
    ax.set_title("Text Length Distribution", fontsize=13, fontweight="bold")
    ax.set_xlabel("Text Length (chars)")
    ax.set_ylabel("Count")
    plt.tight_layout()
    return fig


def build_summary_table(filename: str, results: dict) -> pd.DataFrame:
    ic = results.get("issue_counts", {})
    summary = {
        "File Name": filename,
        "Total Rows": results["total_rows"],
        "Total Columns": results["total_columns"],
        "Text Column": results.get("text_column", ""),
        "Label Column": results.get("label_column", ""),
        "Quality Score": results.get("quality_score", 0),
    }
    summary.update({k.replace("_", " ").title(): v for k, v in ic.items()})
    return pd.DataFrame([summary])
