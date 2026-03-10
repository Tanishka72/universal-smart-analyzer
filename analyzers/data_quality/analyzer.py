# ============================================================
# analyzers/data_quality/analyzer.py — Quality Analysis Engine
# ============================================================
# WHAT: The BRAIN of the Data Quality Analyzer.  It examines every
#        row and column to find problems: missing values, duplicates,
#        outliers, extra spaces, invalid labels, wrong dtypes, etc.
# WHY:  Before you clean data, you need to KNOW what's wrong.
# USED BY: analyzers/data_quality/ui.py calls analyze_quality()
#          and then passes results to the reporter for display.
# ============================================================

import numpy as np
import pandas as pd
from core.utils import has_extra_whitespace, is_likely_date_column, calculate_quality_score


# ---- Generic checks (run on ALL datasets) ----

def _analyze_generic(df: pd.DataFrame) -> dict:
    """Checks that apply to every tabular dataset."""
    total_rows = len(df)
    results = {}

    # Missing values
    missing_per_col = df.isnull().sum()
    results["missing_per_column"] = missing_per_col.to_dict()
    results["null_pct_per_column"] = (missing_per_col / max(1, total_rows) * 100).round(2).to_dict()
    results["missing_total"] = int(missing_per_col.sum())

    # Duplicate rows
    dup_mask = df.duplicated(keep=False)
    results["duplicate_row_count"] = int(df.duplicated().sum())
    results["duplicate_rows"] = df[dup_mask]

    # Duplicate columns (same data, different name)
    dup_col_pairs = []
    cols = df.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if df[cols[i]].equals(df[cols[j]]):
                dup_col_pairs.append((cols[i], cols[j]))
    results["duplicate_column_pairs"] = dup_col_pairs

    # Empty rows (all NaN)
    results["empty_row_count"] = int(df.isnull().all(axis=1).sum())

    # Extra whitespace in string columns
    ws_count = 0
    for col in df.select_dtypes(include=["object", "string"]).columns:
        ws_count += int(df[col].apply(has_extra_whitespace).sum())
    results["extra_whitespace_count"] = ws_count

    # Inconsistent column names
    results["inconsistent_column_names"] = [
        c for c in df.columns if str(c) != str(c).strip() or "  " in str(c) or str(c) != str(c).lower()
    ]

    # Unique counts & constant columns
    results["unique_counts"] = {c: int(df[c].nunique()) for c in df.columns}
    results["constant_columns"] = [c for c, n in results["unique_counts"].items() if n <= 1]

    # High-cardinality categorical columns
    high_card = []
    for col in df.select_dtypes(include=["object", "string"]).columns:
        n = df[col].nunique()
        if total_rows > 0 and n / total_rows > 0.5 and n > 20:
            high_card.append((col, n))
    results["high_cardinality_columns"] = high_card

    # Column dtypes
    results["column_dtypes"] = {c: str(df[c].dtype) for c in df.columns}

    return results


# ---- Text-specific checks ----

def _analyze_text(df: pd.DataFrame) -> dict:
    """Extra checks for text columns: empty text, short text, etc."""
    results = {}
    text_cols = [c for c in df.columns if str(c).lower() in {
        "text", "sentence", "message", "comment", "review", "description",
        "content", "body", "title", "question", "answer", "query",
        "utterance", "input", "output", "prompt", "response", "transcript",
    }]
    if not text_cols:
        obj_cols = df.select_dtypes(include=["object", "string"]).columns.tolist()
        text_cols = obj_cols[:1]
    if not text_cols:
        return results

    text_col = text_cols[0]
    series = df[text_col].astype("string")
    results["text_column"] = text_col

    empty_mask = series.isna() | (series.str.strip() == "") | (series.str.strip() == "<NA>")
    results["empty_text_count"] = int(empty_mask.sum())
    results["empty_text_rows"] = df[empty_mask]

    lengths = series.str.strip().str.len().fillna(0)
    short_mask = (lengths < 3) & (~empty_mask)
    results["short_text_count"] = int(short_mask.sum())
    results["short_text_rows"] = df[short_mask]

    results["duplicate_text_count"] = int(series.duplicated().sum())
    results["text_whitespace_count"] = int(series.apply(has_extra_whitespace).fillna(False).sum())

    clean_lengths = series.str.strip().str.len().dropna()
    if not clean_lengths.empty:
        results["text_length_stats"] = {
            "min": int(clean_lengths.min()), "max": int(clean_lengths.max()),
            "mean": round(float(clean_lengths.mean()), 1),
            "median": round(float(clean_lengths.median()), 1),
        }
    return results


# ---- Label-specific checks ----

def _analyze_labels(df: pd.DataFrame, valid_labels: list[str] | None = None) -> dict:
    """Checks for label columns: missing, invalid, distribution."""
    results = {}
    label_cols = [c for c in df.columns if str(c).lower() in {
        "label", "class", "category", "tag", "target", "intent",
        "sentiment", "emotion", "type", "classification",
    }]
    if not label_cols:
        return results

    label_col = label_cols[0]
    series = df[label_col].astype("string")
    results["label_column"] = label_col

    missing_mask = series.isna() | (series.str.strip() == "") | (series.str.strip() == "<NA>")
    results["missing_label_count"] = int(missing_mask.sum())
    results["label_distribution"] = series.value_counts().to_dict()

    if valid_labels:
        invalid_mask = ~series.isin(valid_labels) & ~missing_mask
        results["invalid_label_count"] = int(invalid_mask.sum())
        results["invalid_label_rows"] = df[invalid_mask]
    else:
        counts = series.value_counts()
        results["rare_labels"] = counts[counts == 1].index.tolist()
        results["invalid_label_count"] = 0

    return results


# ---- Numeric-specific checks ----

def _analyze_numeric(df: pd.DataFrame) -> dict:
    """Checks for numeric columns: outliers (IQR), negatives, stats."""
    results = {}
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if not num_cols:
        return results

    outlier_info = {}
    for col in num_cols:
        s = df[col].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((s < lower) | (s > upper)).sum())
        if count > 0:
            outlier_info[col] = {"count": count, "lower_bound": round(float(lower), 2), "upper_bound": round(float(upper), 2)}
    results["outliers"] = outlier_info

    neg_info = {}
    for col in num_cols:
        n = int((df[col] < 0).sum())
        if n > 0:
            neg_info[col] = n
    results["negative_values"] = neg_info
    results["numeric_stats"] = df[num_cols].describe().to_dict()
    return results


# ---- Date-specific checks ----

def _analyze_dates(df: pd.DataFrame) -> dict:
    """Checks for date columns: invalid, duplicates, nulls."""
    results = {}
    date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
    for col in df.select_dtypes(include=["object"]).columns:
        if is_likely_date_column(df[col]):
            date_cols.append(col)
    if not date_cols:
        return results

    date_issues = {}
    for col in date_cols:
        parsed = pd.to_datetime(df[col], errors="coerce")
        invalid = max(0, int(parsed.isna().sum() - df[col].isna().sum()))
        date_issues[col] = {
            "invalid_dates": invalid,
            "duplicate_timestamps": int(parsed.dropna().duplicated().sum()),
            "null_timestamps": int(df[col].isna().sum()),
        }
    results["date_issues"] = date_issues
    return results


# ---- Main entry point ----

def analyze_quality(df: pd.DataFrame, dataset_type: str, valid_labels: list[str] | None = None) -> dict:
    """Run all relevant checks. Returns a results dict with issue_counts and quality_score."""
    total_rows, total_cols = df.shape
    results = {"total_rows": total_rows, "total_columns": total_cols}

    results["generic"] = _analyze_generic(df)

    if dataset_type in ("labeled_text", "nlp_text", "media_metadata", "mixed", "general"):
        results["text"] = _analyze_text(df)
    if dataset_type in ("labeled_text", "media_metadata", "general"):
        results["labels"] = _analyze_labels(df, valid_labels)
    if dataset_type in ("numeric", "time_series", "mixed", "general"):
        results["numeric"] = _analyze_numeric(df)
    if dataset_type in ("time_series", "mixed", "general"):
        results["dates"] = _analyze_dates(df)

    # Build issue counts for quality score
    ic = {
        "missing_values": results["generic"]["missing_total"],
        "duplicate_rows": results["generic"]["duplicate_row_count"],
        "empty_rows": results["generic"]["empty_row_count"],
        "extra_whitespace": results["generic"]["extra_whitespace_count"],
    }
    if "text" in results:
        ic["empty_text"] = results["text"].get("empty_text_count", 0)
        ic["short_text"] = results["text"].get("short_text_count", 0)
    if "labels" in results:
        ic["missing_labels"] = results["labels"].get("missing_label_count", 0)
        ic["invalid_labels"] = results["labels"].get("invalid_label_count", 0)
    if "numeric" in results:
        ic["outliers"] = sum(v["count"] for v in results["numeric"].get("outliers", {}).values())

    results["issue_counts"] = ic
    results["quality_score"] = calculate_quality_score(total_rows, total_cols, ic)
    return results
