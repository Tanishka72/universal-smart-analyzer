# ============================================================
# analyzers/data_quality/cleaner.py — Data Cleaning Functions
# ============================================================
# WHAT: Each function does ONE cleaning job (trim, dedupe, fill…).
#        The user picks which ones to run from the UI.
# WHY:  After the analyzer finds problems, the cleaner FIXES them.
# USED BY: analyzers/data_quality/ui.py passes user choices to
#          clean_dataset() which applies them in order.
# ============================================================

import pandas as pd
from core.utils import standardize_column_name


def trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype("string").str.strip()
    return df


def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [standardize_column_name(c) for c in df.columns]
    return df


def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates().reset_index(drop=True)


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    to_drop = []
    cols = df.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if cols[j] not in to_drop and df[cols[i]].equals(df[cols[j]]):
                to_drop.append(cols[j])
    return df.drop(columns=to_drop)


def drop_missing_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna().reset_index(drop=True)


def fill_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            df[col] = df[col].fillna("Unknown")
    return df


def remove_invalid_labels(df: pd.DataFrame, label_col: str, valid_labels: list[str]) -> pd.DataFrame:
    return df[df[label_col].isin(valid_labels)].reset_index(drop=True)


def remove_short_text(df: pd.DataFrame, text_col: str, min_length: int = 3) -> pd.DataFrame:
    mask = df[text_col].astype("string").str.strip().str.len() >= min_length
    return df[mask].reset_index(drop=True)


def convert_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            converted = pd.to_numeric(df[col], errors="coerce")
            if converted.notna().sum() / max(1, df[col].notna().sum()) >= 0.7:
                df[col] = converted
        except Exception:
            pass
    return df


def standardize_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["object"]).columns:
        try:
            sample = df[col].dropna().head(50)
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().sum() / max(1, len(sample)) >= 0.7:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        except Exception:
            pass
    return df


def lowercase_text(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    df = df.copy()
    df[text_col] = df[text_col].astype("string").str.lower()
    return df


def drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all").reset_index(drop=True)


# ---- Main entry point ----

def clean_dataset(
    df: pd.DataFrame,
    options: dict,
    text_col: str | None = None,
    label_col: str | None = None,
    valid_labels: list[str] | None = None,
) -> pd.DataFrame:
    """Apply selected cleaning operations in logical order.
    `options` is a dict of {option_name: True/False} from the UI."""
    cleaned = df.copy()

    if options.get("drop_empty_rows"):
        cleaned = drop_empty_rows(cleaned)
    if options.get("trim_whitespace"):
        cleaned = trim_whitespace(cleaned)
    if options.get("standardize_columns"):
        old_cols = cleaned.columns.tolist()
        cleaned = standardize_columns(cleaned)
        col_map = dict(zip(old_cols, cleaned.columns.tolist()))
        text_col = col_map.get(text_col, text_col) if text_col else None
        label_col = col_map.get(label_col, label_col) if label_col else None
    if options.get("remove_duplicate_rows"):
        cleaned = remove_duplicate_rows(cleaned)
    if options.get("remove_duplicate_columns"):
        cleaned = remove_duplicate_columns(cleaned)
    if options.get("drop_missing_rows"):
        cleaned = drop_missing_rows(cleaned)
    if options.get("fill_missing_values"):
        cleaned = fill_missing_values(cleaned)
    if options.get("remove_invalid_labels") and label_col and valid_labels:
        cleaned = remove_invalid_labels(cleaned, label_col, valid_labels)
    if options.get("remove_short_text") and text_col and text_col in cleaned.columns:
        cleaned = remove_short_text(cleaned, text_col)
    if options.get("convert_numeric"):
        cleaned = convert_numeric_columns(cleaned)
    if options.get("standardize_dates"):
        cleaned = standardize_dates(cleaned)
    if options.get("lowercase_text") and text_col and text_col in cleaned.columns:
        cleaned = lowercase_text(cleaned, text_col)

    return cleaned
