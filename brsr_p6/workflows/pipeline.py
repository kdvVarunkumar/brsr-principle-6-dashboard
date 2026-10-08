"""The whole job in one place:  company + financial year  ->  clean report  ->  HTML page.

The commands `flow.py` and `flow.py extract` call these functions, so the steps live in only one place.
"""

import json
from pathlib import Path

from brsr_p6.analysis.trend_model import build_trend
from brsr_p6.core.errors import NoFilingFound
from brsr_p6.core.fiscal_year import parse_fiscal_year
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR, DEFAULT_RAW_DIR, safe_name
from brsr_p6.download.downloader import download_filings
from brsr_p6.download.filings import FilingRecord
from brsr_p6.extraction.extractor import build_report
from brsr_p6.extraction.report_io import save_report
from brsr_p6.parsing.xbrl_reader import read_filing
from brsr_p6.rendering.render import write_page, write_summary_page, write_trend_page
from brsr_p6.workflows.summary_loader import load_summary_inputs
from brsr_p6.workflows.trend_loader import load_year_entries


def _silent(message):
    pass


def load_report(company, fy, progress=_silent):
    """Download the filing if needed, read it and clean it.  Returns (report, download_report)."""
    fy = parse_fiscal_year(fy)                                       # a bad year fails here, before any internet use
    download = download_filings(company, fy=fy, progress=progress)   # reuses files already on disk
    item = download.downloads[0]
    if item.xml_path is None or not item.xml_path.exists():
        raise NoFilingFound(f"NSE lists no readable XBRL file for {download.company.name} for FY {fy}, so no figures can be extracted.",
                            symbol=download.company.symbol)
    filing = read_filing(item.xml_path)
    report = build_report(filing, download.company.name, download.company.symbol, fy, record=item.record)
    return report, download


def load_saved_report(symbol, fy, raw_dir: Path = DEFAULT_RAW_DIR):
    """Build the report from a filing that is ALREADY on disk (data/raw/<SYMBOL>/<FY>/).  Never uses the internet.

    Returns None when the filing is not there.  `symbol` is the NSE symbol (for example "TATASTEEL"), not a company name.
    """
    folder = raw_dir / safe_name(symbol) / fy
    xml_files = sorted(folder.glob("*.xml"))
    if not xml_files:
        return None
    note = folder / "filing.json"                         # written by the downloader: company name, dates, links
    record = FilingRecord(**json.loads(note.read_text(encoding="utf-8"))) if note.exists() else None
    name = record.company_name if record else symbol
    return build_report(read_filing(xml_files[0]), name, symbol, fy, record=record)


def generate_page(company, fy, output_dir=DEFAULT_OUTPUT_DIR, progress=_silent):
    """Produce the HTML page.  Returns (path_of_the_page, report).  The clean data is also saved as JSON in data/parsed/."""
    report, _ = load_report(company, fy, progress)
    save_report(report)
    return write_page(report, output_dir), report


def load_trend(company, fy_from=None, fy_to=None, progress=_silent):
    """The multi-year Trend of a company: downloads what is needed (politely, cached) and reads every year in the range."""
    found, entries = load_year_entries(company, fy_from, fy_to, progress=progress)
    return build_trend(found.name, found.symbol, entries)


def generate_trend_page(company, fy_from=None, fy_to=None, output_dir=DEFAULT_OUTPUT_DIR, progress=_silent):
    """Produce the multi-year trend page.  Returns (path_of_the_page, trend)."""
    trend = load_trend(company, fy_from, fy_to, progress)
    return write_trend_page(trend, output_dir), trend


def generate_summary_page(company, fy=None, output_dir=DEFAULT_OUTPUT_DIR, progress=_silent):
    """Produce the year-on-year summary page (the latest year unless `fy` is given).  Returns (path_of_the_page, report)."""
    inputs = load_summary_inputs(company, fy, progress=progress)
    return write_summary_page(inputs.latest, inputs.previous, inputs.previous_note, output_dir), inputs.latest
