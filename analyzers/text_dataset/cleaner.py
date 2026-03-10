# ============================================================
# analyzers/text_dataset/cleaner.py — Text Dataset Cleaning
# ============================================================
# WHAT: Cleaning functions specifically for text+label datasets.
# WHY:  Text data has unique cleaning needs: removing noisy chars,
#        stripping HTML, fixing labels, removing short text, etc.
# USED BY: analyzers/text_dataset/ui.py → clean_text_dataset().
# ============================================================

import re
import pandas as pd


def remove_missing_text(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Remove rows where the text column is empty or NaN."""
    s = df[text_col].astype("string")
    mask = s.notna() & (s.str.strip() != "") & (s.str.strip() != "<NA>")
    return df[mask].reset_index(drop=True)


def remove_duplicate_text(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Remove rows with duplicate text, keeping first occurrence."""
    return df.drop_duplicates(subset=[text_col]).reset_index(drop=True)


def remove_short_text(df: pd.DataFrame, text_col: str, min_len: int = 3) -> pd.DataFrame:
    """Remove rows where text has fewer than min_len characters."""
    mask = df[text_col].astype("string").str.strip().str.len() >= min_len
    return df[mask].reset_index(drop=True)


def strip_text_whitespace(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Trim leading/trailing whitespace from the text column."""
    df = df.copy()
    df[text_col] = df[text_col].astype("string").str.strip()
    return df


def clean_noisy_text(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Remove HTML tags, URLs, and excessive special characters from text."""
    df = df.copy()

    def clean(val):
        if pd.isna(val):
            return val
        s = str(val)
        s = re.sub(r"<[^>]+>", " ", s)        # Remove HTML tags
        s = re.sub(r"https?://\S+", "", s)     # Remove URLs
        s = re.sub(r"\s+", " ", s).strip()     # Collapse multiple spaces
        return s

    df[text_col] = df[text_col].apply(clean)
    return df


def lowercase_text(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """Convert text column to lowercase."""
    df = df.copy()
    df[text_col] = df[text_col].astype("string").str.lower()
    return df


def remove_invalid_labels(df: pd.DataFrame, label_col: str, valid_labels: list[str]) -> pd.DataFrame:
    """Keep only rows with valid labels."""
    return df[df[label_col].isin(valid_labels)].reset_index(drop=True)


def remove_missing_labels(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """Remove rows where label is empty or NaN."""
    s = df[label_col].astype("string")
    mask = s.notna() & (s.str.strip() != "") & (s.str.strip() != "<NA>")
    return df[mask].reset_index(drop=True)


def strip_label_whitespace(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    """Trim whitespace from the label column."""
    df = df.copy()
    df[label_col] = df[label_col].astype("string").str.strip()
    return df


# ---- Main entry point ----

def clean_text_dataset(
    df: pd.DataFrame,
    options: dict,
    text_col: str | None = None,
    label_col: str | None = None,
    valid_labels: list[str] | None = None,
) -> pd.DataFrame:
    """Apply selected cleaning ops for a text dataset."""
    cleaned = df.copy()

    if text_col:
        if options.get("strip_text_whitespace"):
            cleaned = strip_text_whitespace(cleaned, text_col)
        if options.get("remove_missing_text"):
            cleaned = remove_missing_text(cleaned, text_col)
        if options.get("remove_duplicate_text"):
            cleaned = remove_duplicate_text(cleaned, text_col)
        if options.get("remove_short_text"):
            cleaned = remove_short_text(cleaned, text_col)
        if options.get("clean_noisy_text"):
            cleaned = clean_noisy_text(cleaned, text_col)
        if options.get("lowercase_text"):
            cleaned = lowercase_text(cleaned, text_col)

    if label_col:
        if options.get("strip_label_whitespace"):
            cleaned = strip_label_whitespace(cleaned, label_col)
        if options.get("remove_missing_labels"):
            cleaned = remove_missing_labels(cleaned, label_col)
        if options.get("remove_invalid_labels") and valid_labels:
            cleaned = remove_invalid_labels(cleaned, label_col, valid_labels)

    return cleaned
