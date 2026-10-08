"""Make the year-on-year summaries and multi-year trends the home page offers, from the filings already on disk.  No internet.

The home page has a "Year-on-year" and a "Multi-year trend" button for every company.  `flow.py summary` and `flow.py trends` make those pages (and
download what they need); this makes the ones that are still missing for the companies of a folder, from the saved filings only.

Two rules keep it honest:
  - It never overwrites a page that exists: `flow.py summary` and `flow.py trends` know more (for example that NSE really has no filing for a year).
  - It never guesses.  A summary whose previous-year filing is not saved here says so on the page (it still compares with the previous-year
    column of the newer filing, as every summary does), and a trend covers only years in a row that are all saved.
"""

from collections import defaultdict
from pathlib import Path

from brsr_p6.analysis.trend_model import YearEntry, build_trend
from brsr_p6.core.fiscal_year import previous_fiscal_year
from brsr_p6.core.paths import safe_name
from brsr_p6.rendering.render import summary_page_name, write_summary_page, write_trend_page
from brsr_p6.workflows.compare import report_keys
from brsr_p6.workflows.pipeline import load_saved_report
from brsr_p6.workflows.summary_loader import before_brsr, before_brsr_note


def _no_previous_note(before_fy):
    """Why the summary has no filing of last year's own (the filing is not on this computer; we cannot say NSE has none)."""
    if before_brsr(before_fy):
        return before_brsr_note(before_fy)
    return f"The FY {before_fy} filing is not saved on this computer, so this page could not check whether last year's figures were restated."


def generate_missing_summaries(folder, loader=load_saved_report):
    """Write <SYMBOL>_summary_<FY>.html for every report page of the folder that has no summary yet.  Returns how many."""
    folder = Path(folder)
    made = 0
    for symbol, fy in report_keys(folder):
        if (folder / summary_page_name(symbol, fy)).exists():
            continue
        report = loader(symbol, fy)
        if report is None:                                             # a page without its filing on disk is skipped
            continue
        previous = None if before_brsr(report.previous_fy) else loader(symbol, report.previous_fy)
        write_summary_page(report, previous, "" if previous else _no_previous_note(report.previous_fy), folder)
        made += 1
    return made


def _latest_run(years):
    """The newest years that follow each other without a gap, oldest first: ['2021-22', '2023-24', '2024-25'] -> ['2023-24', '2024-25']."""
    run = [years[-1]]
    for fy in reversed(years[:-1]):
        if previous_fiscal_year(run[0]) != fy:
            break
        run.insert(0, fy)
    return run


def generate_missing_trends(folder, loader=load_saved_report):
    """Write a trend page for every company of the folder that has none yet and has at least two years in a row saved.  Returns how many."""
    folder = Path(folder)
    years = defaultdict(list)
    for symbol, fy in report_keys(folder):
        years[symbol].append(fy)
    made = 0
    for symbol, fys in sorted(years.items()):
        if len(fys) < 2 or any(folder.glob(f"{safe_name(symbol)}_trend_*.html")):
            continue
        reports = {fy: loader(symbol, fy) for fy in sorted(fys)}
        saved = [fy for fy, report in reports.items() if report is not None]
        if len(saved) < 2:
            continue
        run = _latest_run(saved)
        if len(run) < 2:
            continue
        entries = [YearEntry(fy, reports[fy]) for fy in run]
        write_trend_page(build_trend(entries[-1].report.company_name, symbol, entries), folder)
        made += 1
    return made
