# ============================================================
# analyzers/data_quality/reporter.py — Charts & Report Tables
# ============================================================
# WHAT: Turns raw analysis results into pretty tables and charts.
# WHY:  Raw dicts are not user-friendly. This builds visual output
#        that looks great in the Streamlit UI and in downloaded CSVs.
# USED BY: analyzers/data_quality/ui.py calls these to display results.
# ============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")  # Non-interactive backend for Streamlit


def build_summary_table(filename: str, file_format: str, type_label: str, results: dict) -> pd.DataFrame:
    """One-row summary table — this is the downloadable quality report."""
    ic = results.get("issue_counts", {})
    summary = {
        "File Name": filename,
        "File Format": file_format,
        "Detected Type": type_label,
        "Total Rows": results["total_rows"],
        "Total Columns": results["total_columns"],
        "Quality Score": results.get("quality_score", 0),
        "Missing Values": ic.get("missing_values", 0),
        "Duplicate Rows": ic.get("duplicate_rows", 0),
        "Empty Rows": ic.get("empty_rows", 0),
        "Extra Whitespace": ic.get("extra_whitespace", 0),
    }
    if "text" in results:
        summary["Empty Text"] = ic.get("empty_text", 0)
        summary["Short Text"] = ic.get("short_text", 0)
    if "labels" in results:
        summary["Missing Labels"] = ic.get("missing_labels", 0)
        summary["Invalid Labels"] = ic.get("invalid_labels", 0)
    if "numeric" in results:
        summary["Outliers"] = ic.get("outliers", 0)
    return pd.DataFrame([summary])


def build_issue_details_table(results: dict) -> pd.DataFrame:
    """Table with one row per issue type: count, %, severity."""
    ic = results.get("issue_counts", {})
    total = max(1, results["total_rows"])
    rows = []
    for name, count in ic.items():
        pct = round(count / total * 100, 2)
        severity = "— None" if count == 0 else ("Low" if pct < 5 else ("Medium" if pct < 20 else "High"))
        rows.append({"Issue": name.replace("_", " ").title(), "Count": count, "% of Rows": pct, "Severity": severity})
    return pd.DataFrame(rows)


def build_column_info_table(results: dict) -> pd.DataFrame:
    g = results.get("generic", {})
    rows = []
    for col in g.get("column_dtypes", {}):
        rows.append({
            "Column": col,
            "Data Type": g["column_dtypes"].get(col, ""),
            "Missing": g["missing_per_column"].get(col, 0),
            "Null %": g["null_pct_per_column"].get(col, 0),
            "Unique Values": g["unique_counts"].get(col, 0),
        })
    return pd.DataFrame(rows)


# ---- Charts (matplotlib) ----

def chart_quality_gauge(score: float) -> plt.Figure:
    """Semi-circle gauge showing quality score 0-100."""
    import numpy as np

    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw={"projection": "polar"})

    # Map score to angle (pi to 0 → left to right)
    theta = np.pi * (1 - score / 100)
    color = "#2ecc71" if score >= 80 else ("#f39c12" if score >= 50 else "#e74c3c")

    # Background arc
    bg_angles = np.linspace(0, np.pi, 100)
    ax.fill_between(bg_angles, 0, 1, color="#eee", alpha=0.5)

    # Score arc
    score_angles = np.linspace(np.pi, theta, 100)
    ax.fill_between(score_angles, 0, 1, color=color, alpha=0.7)

    # Needle
    ax.plot([theta, theta], [0, 0.85], color="#333", linewidth=2)
    ax.scatter([theta], [0.85], color="#333", s=30, zorder=5)

    ax.set_ylim(0, 1)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title(f"Data Quality Score: {score}%", fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    return fig


def chart_missing_values(results: dict) -> plt.Figure | None:
    data = {c: v for c, v in results["generic"]["missing_per_column"].items() if v > 0}
    if not data:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(list(data.keys()), list(data.values()), color="#e74c3c", edgecolor="white")
    ax.set_title("Missing Values per Column", fontsize=13, fontweight="bold")
    ax.set_ylabel("Missing Count")
    ax.tick_params(axis="x", rotation=45)
    for bar, val in zip(bars, data.values()):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(val), ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    return fig


def chart_null_percentage(results: dict) -> plt.Figure | None:
    data = results["generic"]["null_pct_per_column"]
    if all(v == 0 for v in data.values()):
        return None
    s = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
    fig, ax = plt.subplots(figsize=(8, max(3, len(s) * 0.4)))
    colors = ["#e74c3c" if v > 20 else "#f39c12" if v > 5 else "#2ecc71" for v in s.values()]
    ax.barh(list(s.keys()), list(s.values()), color=colors, edgecolor="white")
    ax.set_title("Null % per Column", fontsize=13, fontweight="bold")
    ax.set_xlabel("Null %")
    plt.tight_layout()
    return fig


def chart_label_distribution(results: dict) -> plt.Figure | None:
    dist = results.get("labels", {}).get("label_distribution", {})
    if not dist:
        return None
    col = results["labels"].get("label_column", "label")
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.pie(list(dist.values()), labels=list(dist.keys()), autopct="%1.1f%%",
           startangle=90, colors=plt.cm.Set3.colors)
    ax.set_title(f"Label Distribution ({col})", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


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
