# ============================================================
# analyzers/data_quality/ui.py — Streamlit UI for Data Quality
# ============================================================
# WHAT: Builds the entire Streamlit page for the Data Quality
#        Analyzer: upload → preview → analysis → cleaning → download.
# WHY:  Keeping UI code separate from logic keeps things organized.
#        The main app.py just calls render() to show this page.
# USED BY: app.py routes to this when user picks "Data Quality".
# ============================================================

import io
import streamlit as st
import pandas as pd

from core.file_helpers import load_file, SUPPORTED_FORMATS
from analyzers.data_quality.detector import detect_dataset_type
from analyzers.data_quality.analyzer import analyze_quality
from analyzers.data_quality.cleaner import clean_dataset
from analyzers.data_quality.reporter import (
    build_summary_table, build_issue_details_table, build_column_info_table,
    chart_quality_gauge, chart_missing_values, chart_null_percentage,
    chart_label_distribution, chart_issue_breakdown,
)


def render():
    """Render the full Data Quality Analyzer page."""

    st.header("Data Quality Analyzer")
    st.markdown("Upload a **CSV, Excel, JSON, TSV, or TXT** file to analyze its quality.")

    # ---- Sidebar settings ----
    with st.sidebar:
        st.subheader("Settings")
        valid_labels_input = st.text_input(
            "Valid labels (comma-separated, optional)",
            placeholder="e.g. positive, negative, neutral",
            help="If your dataset has a label column, list expected labels here.",
            key="dq_valid_labels",
        )
        valid_labels = [l.strip() for l in valid_labels_input.split(",") if l.strip()] if valid_labels_input else None

        st.markdown(
            "**Quality Score Formula:**\n\n"
            "```\nscore = 100 − (issues / total_cells) × 100\n```"
        )

    # ---- File upload ----
    uploaded = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx", "xls", "json", "tsv", "txt"],
        help="Supported: " + ", ".join(SUPPORTED_FORMATS.keys()),
        key="dq_file",
    )
    if not uploaded:
        st.info("Upload a file above to start analyzing.")
        return

    # ---- Load ----
    with st.spinner("Loading file..."):
        df, file_format, error = load_file(uploaded)
    if error:
        st.error(f"{error}")
        return
    if df is None or df.empty:
        st.warning("File is empty or could not be parsed.")
        return

    # ---- Detect & Analyze ----
    type_key, type_label, col_counts = detect_dataset_type(df)
    with st.spinner("Analyzing..."):
        results = analyze_quality(df, type_key, valid_labels)

    # ---- Metrics row ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{results['total_rows']:,}")
    c2.metric("Columns", f"{results['total_columns']:,}")
    c3.metric("Format", file_format)
    c4.metric("Quality Score", f"{results['quality_score']}%")
    st.divider()

    # ---- Detected type ----
    st.subheader("Detected Dataset Type")
    st.success(f"**{type_label}**")
    with st.expander("Column category breakdown"):
        st.dataframe(pd.DataFrame([col_counts], index=["Count"]).T.rename(columns={"Count": "Columns"}), use_container_width=True)
    st.divider()

    # ---- Preview ----
    st.subheader("Dataset Preview")
    st.dataframe(df.head(st.slider("Preview rows", 5, min(100, len(df)), 10, key="dq_preview")), use_container_width=True)
    st.divider()

    # ---- Quality gauge ----
    st.subheader("Quality Score")
    st.pyplot(chart_quality_gauge(results["quality_score"]))
    st.divider()

    # ---- Issue summary table ----
    st.subheader("Issue Summary")
    st.dataframe(build_issue_details_table(results), use_container_width=True, hide_index=True)
    ch = chart_issue_breakdown(results)
    if ch:
        st.pyplot(ch)
    st.divider()

    # ---- Column info ----
    st.subheader("Column Details")
    st.dataframe(build_column_info_table(results), use_container_width=True, hide_index=True)
    st.divider()

    # ---- Charts ----
    st.subheader("Visualizations")
    ch1, ch2 = st.columns(2)
    with ch1:
        mc = chart_missing_values(results)
        st.pyplot(mc) if mc else st.info("No missing values — great!")
    with ch2:
        nc = chart_null_percentage(results)
        st.pyplot(nc) if nc else st.info("No nulls to display.")
    lc = chart_label_distribution(results)
    if lc:
        st.pyplot(lc)
    st.divider()

    # ---- Detailed bad rows ----
    st.subheader("Detailed Issue Rows")
    generic = results.get("generic", {})
    text_r = results.get("text", {})
    label_r = results.get("labels", {})
    numeric_r = results.get("numeric", {})
    date_r = results.get("dates", {})

    with st.expander(f"Duplicate Rows ({generic.get('duplicate_row_count', 0)})"):
        d = generic.get("duplicate_rows", pd.DataFrame())
        st.dataframe(d, use_container_width=True) if not d.empty else st.write("None.")

    if generic.get("inconsistent_column_names"):
        with st.expander(f"Inconsistent Column Names ({len(generic['inconsistent_column_names'])})"):
            for c in generic["inconsistent_column_names"]:
                st.write(f"• `{c}`")

    if generic.get("constant_columns"):
        with st.expander(f"Constant Columns ({len(generic['constant_columns'])})"):
            for c in generic["constant_columns"]:
                st.write(f"• `{c}`")

    if text_r:
        with st.expander(f"Empty Text ({text_r.get('empty_text_count', 0)})"):
            e = text_r.get("empty_text_rows", pd.DataFrame())
            st.dataframe(e, use_container_width=True) if not e.empty else st.write("None.")
        with st.expander(f"Short Text ({text_r.get('short_text_count', 0)})"):
            s = text_r.get("short_text_rows", pd.DataFrame())
            st.dataframe(s, use_container_width=True) if not s.empty else st.write("None.")
        if text_r.get("text_length_stats"):
            with st.expander("Text Length Stats"):
                ts = text_r["text_length_stats"]
                a, b, c_, d_ = st.columns(4)
                a.metric("Min", ts.get("min", "-"))
                b.metric("Max", ts.get("max", "-"))
                c_.metric("Mean", ts.get("mean", "-"))
                d_.metric("Median", ts.get("median", "-"))

    if label_r.get("invalid_label_rows") is not None:
        inv = label_r["invalid_label_rows"]
        with st.expander(f"Invalid Labels ({len(inv)})"):
            st.dataframe(inv, use_container_width=True) if not inv.empty else st.write("None.")

    if numeric_r.get("outliers"):
        with st.expander(f"Outliers ({sum(v['count'] for v in numeric_r['outliers'].values())})"):
            for col, info in numeric_r["outliers"].items():
                st.write(f"• **{col}**: {info['count']} outliers ({info['lower_bound']}–{info['upper_bound']})")

    if date_r.get("date_issues"):
        with st.expander("Date Issues"):
            for col, info in date_r["date_issues"].items():
                st.write(f"**{col}**: invalid={info['invalid_dates']}, duplicates={info['duplicate_timestamps']}, nulls={info['null_timestamps']}")
    st.divider()

    # ---- Cleaning ----
    st.subheader("Clean Your Dataset")
    text_col = text_r.get("text_column")
    label_col = label_r.get("label_column")

    o1, o2, o3 = st.columns(3)
    with o1:
        st.markdown("**General**")
        ot = st.checkbox("Trim whitespace", value=True, key="dq_trim")
        os_ = st.checkbox("Standardize column names", key="dq_std_col")
        odr = st.checkbox("Remove duplicate rows", value=True, key="dq_dup_row")
        odc = st.checkbox("Remove duplicate columns", key="dq_dup_col")
    with o2:
        st.markdown("**Missing Data**")
        ode = st.checkbox("Drop empty rows", value=True, key="dq_drop_empty")
        odm = st.checkbox("Drop rows with any missing", key="dq_drop_miss")
        ofm = st.checkbox("Fill missing (median/Unknown)", key="dq_fill")
    with o3:
        st.markdown("**Advanced**")
        oil = st.checkbox("Remove invalid labels", disabled=not valid_labels, key="dq_inv_lbl")
        ost_ = st.checkbox("Remove short text (<3)", disabled=not text_col, key="dq_short")
        ocn = st.checkbox("Convert numeric columns", key="dq_conv_num")
        osd = st.checkbox("Standardize dates", key="dq_std_date")
        olc = st.checkbox("Lowercase text", disabled=not text_col, key="dq_lower")

    opts = {
        "trim_whitespace": ot, "standardize_columns": os_, "remove_duplicate_rows": odr,
        "remove_duplicate_columns": odc, "drop_empty_rows": ode, "drop_missing_rows": odm,
        "fill_missing_values": ofm, "remove_invalid_labels": oil, "remove_short_text": ost_,
        "convert_numeric": ocn, "standardize_dates": osd, "lowercase_text": olc,
    }

    if st.button("Clean Dataset", type="primary", use_container_width=True, key="dq_clean_btn"):
        with st.spinner("Cleaning..."):
            cleaned = clean_dataset(df, opts, text_col, label_col, valid_labels)
        st.session_state["dq_cleaned"] = cleaned
        st.success(f"Rows: {len(df)} → {len(cleaned)} ({len(df)-len(cleaned)} removed)")

    if "dq_cleaned" in st.session_state:
        cleaned = st.session_state["dq_cleaned"]
        st.divider()
        st.subheader("Cleaned Dataset Preview")
        st.dataframe(cleaned.head(20), use_container_width=True)
        st.divider()

        st.subheader("Download Results")
        d1, d2 = st.columns(2)
        with d1:
            buf = io.StringIO()
            cleaned.to_csv(buf, index=False)
            st.download_button("Download Cleaned Dataset (CSV)", buf.getvalue(), "cleaned_dataset.csv", "text/csv", use_container_width=True, key="dq_dl_clean")
        with d2:
            report = build_summary_table(uploaded.name, file_format, type_label, results)
            rbuf = io.StringIO()
            report.to_csv(rbuf, index=False)
            st.download_button("Download Quality Report (CSV)", rbuf.getvalue(), "quality_report.csv", "text/csv", use_container_width=True, key="dq_dl_report")
