# ============================================================
# analyzers/data_quality/detector.py — Dataset Type Detection
# ============================================================
# WHAT: Looks at your data and guesses what KIND of dataset it is.
# WHY:  Different types need different quality checks.
#        A text dataset needs "short text" checks, while a numeric
#        dataset needs "outlier" checks. Detecting the type first
#        lets the analyzer run the RIGHT checks automatically.
# USED BY: analyzers/data_quality/ui.py calls detect_dataset_type()
#          after the file is loaded.
# ============================================================

import pandas as pd
from core.utils import is_likely_date_column, is_likely_numeric_column


DATASET_TYPES = {
    "labeled_text": "Labeled Text Classification Dataset",
    "nlp_text": "NLP Text Dataset",
    "time_series": "Time Series Dataset",
    "numeric": "Numeric Dataset",
    "media_metadata": "Media Metadata Dataset",
    "mixed": "Mixed Dataset",
    "general": "General Tabular Dataset",
}

# Keywords that hint at column purpose
TEXT_KEYWORDS = {
    "text", "sentence", "message", "comment", "review", "description",
    "content", "body", "title", "question", "answer", "query", "utterance",
    "input", "output", "prompt", "response", "transcript", "summary",
}
LABEL_KEYWORDS = {
    "label", "class", "category", "tag", "target", "intent",
    "sentiment", "emotion", "type", "group", "classification",
}
DATE_KEYWORDS = {
    "date", "time", "timestamp", "datetime", "created", "updated",
    "created_at", "updated_at", "start", "end", "year", "month", "day",
}
MEDIA_KEYWORDS = {
    "image", "image_path", "audio", "audio_path", "video", "video_path",
    "file", "file_path", "path", "url", "uri", "filename",
}


def _count_column_categories(df: pd.DataFrame) -> dict:
    """Count how many columns match each category.
    This 'votes' on what type the dataset is."""
    counts = {"text": 0, "label": 0, "date": 0, "media": 0, "numeric": 0, "other": 0}

    for col in df.columns:
        col_lower = str(col).lower().strip()
        dtype = df[col].dtype

        if col_lower in TEXT_KEYWORDS or any(k in col_lower for k in TEXT_KEYWORDS):
            counts["text"] += 1
        elif col_lower in LABEL_KEYWORDS or any(k in col_lower for k in LABEL_KEYWORDS):
            counts["label"] += 1
        elif col_lower in DATE_KEYWORDS or any(k in col_lower for k in DATE_KEYWORDS):
            counts["date"] += 1
        elif col_lower in MEDIA_KEYWORDS or any(k in col_lower for k in MEDIA_KEYWORDS):
            counts["media"] += 1
        elif pd.api.types.is_numeric_dtype(dtype):
            counts["numeric"] += 1
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            counts["date"] += 1
        elif dtype == "object" and is_likely_date_column(df[col]):
            counts["date"] += 1
        elif dtype == "object" and is_likely_numeric_column(df[col]):
            counts["numeric"] += 1
        else:
            counts["other"] += 1

    return counts


def detect_dataset_type(df: pd.DataFrame) -> tuple[str, str, dict]:
    """Detect dataset type. Returns (type_key, type_label, column_counts)."""
    counts = _count_column_categories(df)
    total_cols = len(df.columns)

    if counts["text"] >= 1 and counts["label"] >= 1:
        return "labeled_text", DATASET_TYPES["labeled_text"], counts
    if counts["media"] >= 1 and (counts["label"] >= 1 or counts["text"] >= 1):
        return "media_metadata", DATASET_TYPES["media_metadata"], counts
    if counts["text"] >= 1:
        return "nlp_text", DATASET_TYPES["nlp_text"], counts
    if counts["date"] >= 1 and counts["numeric"] >= 1:
        return "time_series", DATASET_TYPES["time_series"], counts
    if total_cols > 0 and counts["numeric"] / total_cols >= 0.7:
        return "numeric", DATASET_TYPES["numeric"], counts
    if counts["numeric"] >= 1 and (counts["text"] >= 1 or counts["other"] >= 2):
        return "mixed", DATASET_TYPES["mixed"], counts

    return "general", DATASET_TYPES["general"], counts
