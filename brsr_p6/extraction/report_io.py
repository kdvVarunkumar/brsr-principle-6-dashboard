"""Save a Principle6Report as a JSON file, so other steps (and you) can read the clean data without re-reading the XML."""

import json
from dataclasses import asdict
from pathlib import Path

from brsr_p6.core.paths import DEFAULT_PARSED_DIR, safe_name


def save_report(report, parsed_dir: Path = DEFAULT_PARSED_DIR) -> Path:
    """Write data/parsed/<SYMBOL>/<FY>.json and return its path."""
    path = parsed_dir / safe_name(report.symbol) / f"{report.fy}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    # asdict turns the dataclasses (and the Status enum, which is a string) into plain dictionaries and text.
    path.write_text(json.dumps(asdict(report), indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return path
