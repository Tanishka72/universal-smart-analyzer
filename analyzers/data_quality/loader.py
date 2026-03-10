# ============================================================
# analyzers/data_quality/loader.py — Data Quality File Loader
# ============================================================
# WHAT: Thin wrapper around core/file_helpers.py for the Data
#        Quality Analyzer. Re-exports load_file and format info.
# WHY:  Keeps imports inside data_quality/ self-contained while
#        sharing the actual loading logic in core/.
# ============================================================

from core.file_helpers import load_file, detect_file_format, SUPPORTED_FORMATS

__all__ = ["load_file", "detect_file_format", "SUPPORTED_FORMATS"]
