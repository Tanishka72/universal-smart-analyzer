# ============================================================
# core/router.py — Analyzer Routing Logic
# ============================================================
# WHAT: Maps analyzer names to their render() functions.
#        app.py uses this to dynamically show the selected page.
# WHY:  Separating routing from the main file keeps app.py clean.
#        To add a new analyzer, just register it here.
# ============================================================

from analyzers.data_quality import ui as data_quality_ui
from analyzers.text_dataset import ui as text_dataset_ui

# Each key is a sidebar label; each value is a render() function.
ANALYZERS = {
    "Data Quality Analyzer": data_quality_ui.render,
    "Text Dataset Analyzer": text_dataset_ui.render,
}
