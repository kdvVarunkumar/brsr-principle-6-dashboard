"""Turn a clean report into the plain dictionaries the React page and the chat assistant read.  Pure code: no network, no server."""

from dataclasses import asdict
from pathlib import Path

from brsr_p6.core.models import Principle6Report
from brsr_p6.core.paths import DEFAULT_RAW_DIR
from brsr_p6.views.dashboard_view import build_dashboard_view


def dashboard_to_dict(report: Principle6Report) -> dict:
    """The facts about the filing, plus the whole Dashboard exactly as views/dashboard_view.py decided it (sentences, verdicts, warnings, origins)."""
    return {
        "company_name": report.company_name,
        "symbol": report.symbol,
        "fy": report.fy,
        "previous_fy": report.previous_fy,
        "boundary": report.boundary,
        "submission_date": report.submission_date,
        "source_url": report.source_url,
        "dashboard": asdict(build_dashboard_view(report)),
    }


def available_filings(raw_dir: Path = DEFAULT_RAW_DIR) -> dict:
    """{symbol: [financial years]} for every filing already saved in data/raw/ (a folder holding an XML file counts)."""
    raw_dir = Path(raw_dir)
    if not raw_dir.exists():
        return {}
    found = {}
    for company in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        years = sorted(y.name for y in company.iterdir() if y.is_dir() and any(y.glob("*.xml")))
        if years:
            found[company.name] = years
    return found
