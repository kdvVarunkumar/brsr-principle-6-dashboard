"""Where things live on disk: every folder the program reads or writes is named here, once.

The project root is found from this file's own location (brsr_p6/core/paths.py, so two folders up is the folder that contains
flow.py), which means the program works from any current folder.  If this file ever moves, only `PROJECT_ROOT` has to change.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"          # filings downloaded from NSE
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "cache"      # small caches (company search answers)
DEFAULT_PARSED_DIR = PROJECT_ROOT / "data" / "parsed"    # the clean data of a report, as JSON
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"             # the HTML pages the commands write
SAMPLES_DIR = PROJECT_ROOT / "samples"                   # the committed sample pages


def safe_name(text: str) -> str:
    """Make a string safe to use as a folder name (e.g. 'M&M' -> 'M_M')."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", text)
