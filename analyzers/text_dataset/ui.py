# ============================================================
# analyzers/text_dataset/ui.py — Streamlit UI for Text Analyzer
# ============================================================
# WHAT: The full Streamlit page for analyzing text+label datasets.
# WHY:  Separate from the data quality UI because text datasets
#        have different controls (noisy text, label validation, etc.)
# USED BY: app.py routes here when user picks "Text Dataset Analyzer".
# ============================================================

import io
import streamlit as st
import pandas as pd

from core.file_helpers import load_file
from analyzers.text_dataset.analyzer import analyze_text_dataset
from analyzers.text_dataset.cleaner import clean_text_dataset
from analyzers.text_dataset.reporter import (
    chart_quality_gauge, build_issue_table, chart_issue_breakdown,
    chart_label_distribution, chart_text_length_histogram, build_summary_table,
)


def render():
    """Render the Text Dataset Analyzer page."""

    st.header("Text Dataset Analyzer")
    st.markdown("Upload a **text+label dataset** (CSV/Excel/JSON/TSV) to analyze text quality and label consistency.")

    # ---- Sidebar ----
    with st.sidebar:
        st.subheader("Settings")
        valid_labels_input = st.text_input(
            "Valid labels (comma-separated, optional)",
            placeholder="e.g. greeting, loan_due_date, loan_close",
            key="txt_valid_labels",
        )
        valid_labels = [l.strip() for l in valid_labels_input.split(",") if l.strip()] if valid_labels_input else None

    # ---- Upload ----
    uploaded = st.file_uploader(
        "Choose a text dataset file",
        type=["csv", "xlsx", "xls", "json", "tsv", "txt"],
        key="txt_file",
    )
    if not uploaded:
        st.info("Upload a file above to start analyzing.")
        return

    # ---- Load ----
    with st.spinner("Loading..."):
        df, file_format, error = load_file(uploaded)
    if error:
        st.error(f"{error}")
        return
    if df is None or df.empty:
        st.warning("File is empty.")
        return

    # ---- Analyze ----
    with st.spinner("Analyzing text dataset..."):
        results = analyze_text_dataset(df, valid_labels)

    if results.get("error"):
        st.error(results["error"])
        return

    text_col = results["text_column"]
    label_col = results["label_column"]

    # ---- Metrics ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{results['total_rows']:,}")
    c2.metric("Text Column", text_col or "—")
    c3.metric("Label Column", label_col or "—")
    c4.metric("Quality Score", f"{results['quality_score']}%")
    st.divider()

    # ---- Preview ----
    st.subheader("Dataset Preview")
    st.dataframe(df.head(10), use_container_width=True)
    st.divider()

    # ---- Quality gauge ----
    st.subheader("Quality Score")
    st.pyplot(chart_quality_gauge(results["quality_score"]))
    st.divider()

    # ---- Issue table ----
    st.subheader("Issue Summary")
    st.dataframe(build_issue_table(results), use_container_width=True, hide_index=True)
    ch = chart_issue_breakdown(results)
    if ch:
        st.pyplot(ch)
    st.divider()

    # ---- Charts ----
    st.subheader("Visualizations")
    col1, col2 = st.columns(2)
    with col1:
        lc = chart_label_distribution(results)
        if lc:
            st.pyplot(lc)
        else:
            st.info("No label column detected.")
    with col2:
        if text_col:
            st.pyplot(chart_text_length_histogram(df, text_col))
    st.divider()

    # ---- Text length stats ----
    if results.get("text_length_stats"):
        st.subheader("Text Length Statistics")
        ts = results["text_length_stats"]
        a, b, c_, d_ = st.columns(4)
        a.metric("Min", ts.get("min", "-"))
        b.metric("Max", ts.get("max", "-"))
        c_.metric("Mean", ts.get("mean", "-"))
        d_.metric("Median", ts.get("median", "-"))
        st.divider()

    # ---- Detailed bad rows ----
    st.subheader("Detailed Issue Rows")

    with st.expander(f"Missing Text ({results.get('missing_text_count', 0)})"):
        r = results.get("missing_text_rows", pd.DataFrame())
        st.dataframe(r, use_container_width=True) if not r.empty else st.write("None.")

    with st.expander(f"Duplicate Text ({results.get('duplicate_text_count', 0)})"):
        r = results.get("duplicate_text_rows", pd.DataFrame())
        st.dataframe(r, use_container_width=True) if not r.empty else st.write("None.")

    with st.expander(f"Short Text ({results.get('short_text_count', 0)})"):
        r = results.get("short_text_rows", pd.DataFrame())
        st.dataframe(r, use_container_width=True) if not r.empty else st.write("None.")

    with st.expander(f"Noisy Text ({results.get('noisy_text_count', 0)})"):
        r = results.get("noisy_text_rows", pd.DataFrame())
        st.dataframe(r, use_container_width=True) if not r.empty else st.write("None.")

    if label_col:
        with st.expander(f"Missing Labels ({results.get('missing_label_count', 0)})"):
            r = results.get("missing_label_rows", pd.DataFrame())
            st.dataframe(r, use_container_width=True) if not r.empty else st.write("None.")

        if results.get("invalid_label_rows") is not None:
            inv = results["invalid_label_rows"]
            with st.expander(f"Invalid Labels ({len(inv)})"):
                st.dataframe(inv, use_container_width=True) if not inv.empty else st.write("None.")
    st.divider()

    # ---- Cleaning ----
    st.subheader("Clean Text Dataset")
    o1, o2 = st.columns(2)
    with o1:
        st.markdown("**Text Cleaning**")
        ow = st.checkbox("Strip text whitespace", value=True, key="txt_ws")
        om = st.checkbox("Remove missing text", value=True, key="txt_miss")
        od = st.checkbox("Remove duplicate text", key="txt_dup")
        os_ = st.checkbox("Remove short text (<3)", key="txt_short")
        on = st.checkbox("Clean noisy text (HTML, URLs)", key="txt_noise")
        ol = st.checkbox("Lowercase text", key="txt_lower")
    with o2:
        st.markdown("**Label Cleaning**")
        olw = st.checkbox("Strip label whitespace", value=True, key="txt_lbl_ws")
        oml = st.checkbox("Remove missing labels", key="txt_miss_lbl")
        oil = st.checkbox("Remove invalid labels", disabled=not valid_labels, key="txt_inv_lbl")

    opts = {
        "strip_text_whitespace": ow, "remove_missing_text": om, "remove_duplicate_text": od,
        "remove_short_text": os_, "clean_noisy_text": on, "lowercase_text": ol,
        "strip_label_whitespace": olw, "remove_missing_labels": oml, "remove_invalid_labels": oil,
    }

    if st.button("Clean Text Dataset", type="primary", use_container_width=True, key="txt_clean_btn"):
        with st.spinner("Cleaning..."):
            cleaned = clean_text_dataset(df, opts, text_col, label_col, valid_labels)
        st.session_state["txt_cleaned"] = cleaned
        st.success(f"Rows: {len(df)} → {len(cleaned)} ({len(df)-len(cleaned)} removed)")

    if "txt_cleaned" in st.session_state:
        cleaned = st.session_state["txt_cleaned"]
        st.divider()
        st.subheader("Cleaned Preview")
        st.dataframe(cleaned.head(20), use_container_width=True)
        st.divider()
        st.subheader("Download")
        d1, d2 = st.columns(2)
        with d1:
            buf = io.StringIO()
            cleaned.to_csv(buf, index=False)
            st.download_button("Download Cleaned Dataset (CSV)", buf.getvalue(), "cleaned_text_dataset.csv", "text/csv", use_container_width=True, key="txt_dl_clean")
        with d2:
            report = build_summary_table(uploaded.name, results)
            rbuf = io.StringIO()
            report.to_csv(rbuf, index=False)
            st.download_button("Download Quality Report (CSV)", rbuf.getvalue(), "text_quality_report.csv", "text/csv", use_container_width=True, key="txt_dl_report")
