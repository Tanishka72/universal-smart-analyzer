# ============================================================
# analyzers/text_dataset/analyzer.py — Text Dataset Analysis
# ============================================================
# WHAT: Specialized analyzer for text+label datasets.
#        Detects missing text, missing labels, duplicate text,
#        short text, noisy text, invalid labels, and more.
# WHY:  Text datasets have unique problems (empty strings, short
#        words, noisy characters) that generic checks miss.
# USED BY: analyzers/text_dataset/ui.py calls analyze_text_dataset().
# ============================================================

import re
import pandas as pd
from core.utils import has_extra_whitespace, calculate_quality_score


def _find_column(df: pd.DataFrame, keywords: set[str]) -> str | None:
    """Find the first column whose name matches any keyword."""
    for col in df.columns:
        if str(col).lower().strip() in keywords:
            return col
    return None


def _detect_noisy_text(series: pd.Series) -> pd.Series:
    """Flag rows with noisy text: too many special chars, URLs, HTML tags, etc."""
    def is_noisy(val):
        if pd.isna(val):
            return False
        s = str(val)
        # Check for HTML tags
        if re.search(r"<[^>]+>", s):
            return True
        # Check for URLs
        if re.search(r"https?://\S+", s):
            return True
        # Check if more than 40% of chars are non-alphanumeric (excl. spaces)
        alpha_count = sum(c.isalnum() or c.isspace() for c in s)
        if len(s) > 5 and alpha_count / len(s) < 0.6:
            return True
        return False
    return series.apply(is_noisy)


def analyze_text_dataset(
    df: pd.DataFrame,
    valid_labels: list[str] | None = None,
) -> dict:
    """Run all text-dataset-specific checks.
    Returns a results dict with issue counts, bad rows, and stats."""

    total_rows, total_cols = df.shape
    results = {"total_rows": total_rows, "total_columns": total_cols}

    # ---- Find text and label columns ----
    text_col = _find_column(df, {
        "text", "sentence", "message", "comment", "review", "description",
        "content", "body", "question", "answer", "query", "utterance",
        "input", "output", "prompt", "response", "transcript",
    })
    if not text_col:
        obj_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        text_col = obj_cols[0] if obj_cols else None

    label_col = _find_column(df, {
        "label", "class", "category", "tag", "target", "intent",
        "sentiment", "emotion", "classification",
    })

    results["text_column"] = text_col
    results["label_column"] = label_col

    if not text_col:
        results["error"] = "No text column found in the dataset."
        results["quality_score"] = 0
        return results

    text_series = df[text_col].astype("string")

    # ---- Missing text ----
    empty_mask = text_series.isna() | (text_series.str.strip() == "") | (text_series.str.strip() == "<NA>")
    results["missing_text_count"] = int(empty_mask.sum())
    results["missing_text_rows"] = df[empty_mask]

    # ---- Duplicate text ----
    dup_mask = text_series.duplicated(keep=False) & text_series.notna()
    results["duplicate_text_count"] = int(text_series.duplicated().sum())
    results["duplicate_text_rows"] = df[dup_mask]

    # ---- Short text (<3 chars) ----
    lengths = text_series.str.strip().str.len().fillna(0)
    short_mask = (lengths < 3) & (~empty_mask)
    results["short_text_count"] = int(short_mask.sum())
    results["short_text_rows"] = df[short_mask]

    # ---- Extra whitespace ----
    ws_mask = text_series.apply(has_extra_whitespace).fillna(False)
    results["whitespace_text_count"] = int(ws_mask.sum())

    # ---- Noisy text ----
    noise_mask = _detect_noisy_text(text_series)
    results["noisy_text_count"] = int(noise_mask.sum())
    results["noisy_text_rows"] = df[noise_mask]

    # ---- Text length stats ----
    clean_lens = text_series.str.strip().str.len().dropna()
    if not clean_lens.empty:
        results["text_length_stats"] = {
            "min": int(clean_lens.min()), "max": int(clean_lens.max()),
            "mean": round(float(clean_lens.mean()), 1),
            "median": round(float(clean_lens.median()), 1),
        }

    # ---- Label analysis (if label column exists) ----
    if label_col:
        label_series = df[label_col].astype("string")

        miss_lbl = label_series.isna() | (label_series.str.strip() == "") | (label_series.str.strip() == "<NA>")
        results["missing_label_count"] = int(miss_lbl.sum())
        results["missing_label_rows"] = df[miss_lbl]
        results["label_distribution"] = label_series.value_counts().to_dict()

        if valid_labels:
            inv_mask = ~label_series.isin(valid_labels) & ~miss_lbl
            results["invalid_label_count"] = int(inv_mask.sum())
            results["invalid_label_rows"] = df[inv_mask]
        else:
            results["invalid_label_count"] = 0
    else:
        results["missing_label_count"] = 0
        results["invalid_label_count"] = 0

    # ---- Quality score ----
    issues = {
        "missing_text": results["missing_text_count"],
        "duplicate_text": results["duplicate_text_count"],
        "short_text": results["short_text_count"],
        "noisy_text": results["noisy_text_count"],
        "whitespace": results["whitespace_text_count"],
        "missing_labels": results["missing_label_count"],
        "invalid_labels": results["invalid_label_count"],
    }
    results["issue_counts"] = issues
    results["quality_score"] = calculate_quality_score(total_rows, max(total_cols, 1), issues)

    return results
