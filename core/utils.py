# ============================================================
# core/utils.py — Shared Helper Functions
# ============================================================
# WHAT: Small reusable functions used across ALL analyzers.
# WHY:  Instead of copy-pasting the same code in 3 places,
#        we write it once here and import it everywhere.
# USED BY: analyzer modules, cleaner modules, reporter modules.
# ============================================================

import re
import pandas as pd


def safe_strip(value) -> str:
    """Remove leading/trailing whitespace from a value safely.
    Returns the original value if it's NaN/None."""
    if pd.isna(value):
        return value
    return str(value).strip()


def has_extra_whitespace(value) -> bool:
    """Check if a string has leading or trailing spaces.
    Example: '  hello ' → True, 'hello' → False."""
    if pd.isna(value):
        return False
    s = str(value)
    return s != s.strip()


def is_likely_date_column(series: pd.Series) -> bool:
    """Guess whether a column contains date values.
    We try to parse a sample — if 70%+ succeed, it's a date column."""
    sample = series.dropna().head(50)
    if sample.empty:
        return False
    try:
        parsed = pd.to_datetime(sample, errors="coerce")
        return parsed.notna().sum() / len(sample) >= 0.7
    except Exception:
        return False


def is_likely_numeric_column(series: pd.Series) -> bool:
    """Guess whether a string column actually holds numbers.
    Example: a column stored as text but containing '100', '200'."""
    sample = series.dropna().head(100)
    if sample.empty:
        return False
    try:
        converted = pd.to_numeric(sample, errors="coerce")
        return converted.notna().sum() / len(sample) >= 0.7
    except Exception:
        return False


def standardize_column_name(name: str) -> str:
    """Convert a column name to clean lowercase_underscore format.
    Example: '  First Name!! ' → 'first_name'."""
    name = str(name).strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def calculate_quality_score(total_rows: int, total_columns: int, issues: dict) -> float:
    """Calculate a quality score from 0 to 100.
    Formula: score = 100 − (issue_cells / total_cells) × 100.
    Each issue type contributes its count of affected rows."""
    if total_rows == 0 or total_columns == 0:
        return 0.0
    total_cells = total_rows * total_columns
    total_issue_count = sum(issues.values())
    score = max(0.0, 100.0 - (total_issue_count / total_cells) * 100.0)
    return round(score, 2)
