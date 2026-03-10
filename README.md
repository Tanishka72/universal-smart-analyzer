# Universal Smart Analyzer Platform

A professional, modular Python + Streamlit web app for **dataset quality analysis and cleaning**. Upload any structured dataset, profile its structure, detect quality issues, clean it, and download the results.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

### Supported File Formats
- CSV
- Excel (.xlsx / .xls)
- JSON
- TSV
- TXT (tab or comma delimited)

### Data Quality Analyzer
- Auto-detects dataset type (text, numeric, time series, mixed, etc.)
- Detects: missing values, duplicate rows, duplicate columns, extra whitespace, outliers (IQR), invalid dates, wrong dtypes, constant columns, high-cardinality columns
- Quality score gauge (0–100) with matplotlib charts
- One-click cleaning with 12+ options
- Download cleaned dataset + quality report CSV

### Text Dataset Analyzer
- Detects text and label columns automatically
- Finds: missing text/labels, duplicate text, short text, noisy text (HTML, URLs), invalid labels
- Label distribution pie chart + text length histogram
- Text-specific cleaning: strip, de-noise, deduplicate, lowercase
- Download cleaned dataset + report

---

## Project Structure

```
universal-smart-analyzer/
├── app.py                              # Main entry point — run this!
├── requirements.txt                    # Python dependencies
├── README.md
│
├── core/                               # Shared modules
│   ├── __init__.py
│   ├── router.py                       # Analyzer routing logic
│   ├── utils.py                        # Helper functions
│   └── file_helpers.py                 # File format detection & loading
│
├── analyzers/                          # All analyzer modules
│   ├── __init__.py
│   ├── data_quality/                   # Data Quality Analyzer
│   │   ├── __init__.py
│   │   ├── loader.py                   # Re-exports file loading
│   │   ├── analyzer.py                 # Quality analysis engine
│   │   ├── cleaner.py                  # Cleaning functions
│   │   ├── detector.py                 # Dataset type detection
│   │   ├── reporter.py                 # Charts & report tables
│   │   └── ui.py                       # Streamlit UI page
│   └── text_dataset/                   # Text Dataset Analyzer
│       ├── __init__.py
│       ├── analyzer.py                 # Text-specific analysis
│       ├── cleaner.py                  # Text cleaning functions
│       ├── reporter.py                 # Text charts & tables
│       └── ui.py                       # Streamlit UI page
│
└── data/                               # Data directories
    ├── uploads/                        # Uploaded files (gitignored)
    ├── cleaned/                        # Cleaned outputs (gitignored)
    └── reports/                        # Generated reports (gitignored)
```

---

## Setup & Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the app

```bash
streamlit run app.py
```

Opens in your browser at `http://localhost:8501`.

### 3. Use it

1. Pick an analyzer from the sidebar (Data Quality / Text Dataset)
2. Upload your file (CSV, Excel, JSON, TSV, or TXT)
3. View dataset profile, quality score, issue details, and charts
4. Select cleaning options and clean the data
5. Download the cleaned dataset and quality report

---

## Quality Score Formula

```
quality_score = 100 − (total_issue_cells / total_cells) × 100
```

Where `total_cells = rows × columns`. Each issue type contributes its count. Score: **0** (worst) to **100** (perfect).

---

## How to Add a New Analyzer

1. Create a folder: `analyzers/my_analyzer/`
2. Add `__init__.py`, `analyzer.py`, and `ui.py` (with a `render()` function)
3. Register it in `core/router.py`:
   ```python
   from analyzers.my_analyzer import ui as my_analyzer_ui
   ANALYZERS["🆕 My Analyzer"] = my_analyzer_ui.render
   ```

---

## Libraries Used

| Library | Purpose |
|---------|---------|
| **Streamlit** | Web UI framework |
| **Pandas** | Data loading & manipulation |
| **openpyxl** | Excel file reading |
| **Matplotlib** | Charts & visualizations |

---

## License

MIT License — use freely for personal and commercial projects.
