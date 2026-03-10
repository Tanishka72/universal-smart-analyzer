# ============================================================
# app.py — Main Entry Point (Streamlit Router)
# ============================================================
# WHAT: This is the file you run: `streamlit run app.py`
#        It shows a sidebar menu where the user picks an analyzer,
#        then routes to the correct UI page.
#
# HOW IT WORKS:
#   1. User opens the app in their browser
#   2. They see a sidebar with 2 analyzer options
#   3. They pick one (e.g. "Data Quality Analyzer")
#   4. app.py calls that analyzer's render() function
#   5. The render() function builds the entire page for that analyzer
#
# ARCHITECTURE — How to add a NEW analyzer later:
#   1. Create a new folder: analyzers/my_new_analyzer/
#   2. Add __init__.py, analyzer.py, ui.py (with a render() function)
#   3. Register it in core/router.py
#   That's it — the routing handles the rest!
# ============================================================

import streamlit as st
from core.router import ANALYZERS


# ---- Page Config ----
st.set_page_config(
    page_title="Universal Smart Analyzer Platform",
    page_icon="https://img.icons8.com/ios-filled/50/bar-chart.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Sidebar: App Title + Analyzer Selection ----
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0'>Universal Smart Analyzer</h2>", unsafe_allow_html=True)
    st.caption("Choose an analyzer from below:")
    selected = st.radio(
        "Select Analyzer",
        list(ANALYZERS.keys()),
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown(
        """
        <style>
        .credit-badge {
            user-select: none;
            -webkit-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            pointer-events: none;
            text-align: center;
            font-size: 0.80em;
            color: #888;
            padding: 8px 0;
            letter-spacing: 0.5px;
        }
        .credit-badge span {
            display: inline-block;
        }
        </style>
        <div class="credit-badge">
            Built by<br>
            <span style="font-weight:600;font-size:1.15em;color:#555;">
                T&#8203;a&#8203;n&#8203;i&#8203;s&#8203;h&#8203;k&#8203;a
                S&#8203;h&#8203;a&#8203;r&#8203;m&#8203;a
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Route to the selected analyzer ----
ANALYZERS[selected]()

# ---- Footer ----
st.divider()
st.markdown(
    "<div style='text-align:center;color:gray;font-size:0.85em'>"
    "Universal Smart Analyzer Platform &mdash; Built with Streamlit, Pandas &amp; Matplotlib"
    "</div>",
    unsafe_allow_html=True,
)
