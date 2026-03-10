# ============================================================
# core/file_helpers.py — File Handling Helpers
# ============================================================
# WHAT: Utility functions for detecting file formats and loading
#        uploaded files into pandas DataFrames.
# WHY:  Both analyzers need to load files. Instead of duplicating
#        code, they share this single module.
# SUPPORTED: CSV, Excel (.xlsx/.xls), JSON, TSV, TXT (delimited)
# ============================================================

import io
import pandas as pd


SUPPORTED_FORMATS = {
    ".csv": "CSV",
    ".xlsx": "Excel",
    ".xls": "Excel",
    ".json": "JSON",
    ".tsv": "TSV",
    ".txt": "Text (tab/comma delimited)",
}


def detect_file_format(filename: str) -> str:
    """Return a human-readable format name based on file extension."""
    for ext, fmt in SUPPORTED_FORMATS.items():
        if filename.lower().endswith(ext):
            return fmt
    return "Unknown"


def load_file(uploaded_file) -> tuple[pd.DataFrame | None, str, str]:
    """Load an uploaded file into a DataFrame.

    Returns: (dataframe, format_name, error_message).
    On success error_message is empty; on failure dataframe is None.
    """
    filename = uploaded_file.name
    file_format = detect_file_format(filename)

    try:
        if file_format == "CSV":
            df = pd.read_csv(uploaded_file)

        elif file_format == "Excel":
            df = pd.read_excel(uploaded_file, engine="openpyxl")

        elif file_format == "JSON":
            content = uploaded_file.read().decode("utf-8")
            uploaded_file.seek(0)
            try:
                df = pd.read_json(io.StringIO(content))
            except ValueError:
                df = pd.read_json(io.StringIO(content), lines=True)

        elif file_format == "TSV":
            df = pd.read_csv(uploaded_file, sep="\t")

        elif file_format == "Text (tab/comma delimited)":
            content = uploaded_file.read().decode("utf-8")
            uploaded_file.seek(0)
            sep = "\t" if "\t" in content else ","
            df = pd.read_csv(io.StringIO(content), sep=sep)

        else:
            return None, file_format, f"Unsupported file format: {filename}"

        if df.empty:
            return df, file_format, "File loaded but contains no data."

        return df, file_format, ""

    except Exception as e:
        return None, file_format, f"Failed to load file: {str(e)}"
