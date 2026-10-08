"""Compare two companies for one financial year: load both filings, write one page.  The part of Extension 3 that reads files.

Also builds a comparison for EVERY pair of companies that have a report page for the same year in a folder (used by hub.py, so the
index page can offer "compare company A with company B in FY ...").  That reads only filings already on disk: no internet.
"""

import itertools
import re
from pathlib import Path

from brsr_p6.core.errors import SameCompany
from brsr_p6.core.fiscal_year import parse_fiscal_year
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.rendering.render import write_compare_page
from brsr_p6.views.hub_view import REPORTS, kind_of
from brsr_p6.workflows.pipeline import load_report, load_saved_report

_REPORT_FILE = re.compile(r"^(?P<symbol>.+)_(?P<fy>\d{4}-\d{2})\.html$")


def _silent(message):
    pass


def load_pair(company_a, company_b, fy, progress=_silent):
    """The two companies' reports for the same financial year (downloads what is missing, politely)."""
    fy = parse_fiscal_year(fy)                                            # a bad year fails here, before any internet use
    if company_a.strip().lower() == company_b.strip().lower():
        raise SameCompany(f"{company_a!r} and {company_b!r} are the same company. A comparison needs two different companies.")
    report_a, _ = load_report(company_a, fy, progress)
    report_b, _ = load_report(company_b, fy, progress)
    if report_a.symbol == report_b.symbol:
        raise SameCompany(f"{report_a.company_name} was given twice. A comparison needs two different companies.")
    return report_a, report_b


def generate_comparison_page(company_a, company_b, fy, output_dir=DEFAULT_OUTPUT_DIR, progress=_silent):
    """Produce the comparison page.  Returns (path_of_the_page, report_a, report_b)."""
    report_a, report_b = load_pair(company_a, company_b, fy, progress)
    return write_compare_page(report_a, report_b, output_dir), report_a, report_b


def report_keys(folder):
    """[(symbol, financial year)] of the report pages (not trends, summaries, comparisons or errors) in a folder."""
    keys = []
    for path in sorted(Path(folder).glob("*.html")):
        match = _REPORT_FILE.match(path.name)
        if match and kind_of(path.stem) == REPORTS:
            keys.append((match["symbol"], match["fy"]))
    return keys


def generate_all_comparisons(folder, loader=load_saved_report):
    """Write a comparison page for every pair of companies with a report page for the same year in `folder`.  Returns how many."""
    by_year = {}
    for symbol, fy in report_keys(folder):
        by_year.setdefault(fy, set()).add(symbol)
    made = 0
    for fy, symbols in sorted(by_year.items()):
        reports = [(symbol, loader(symbol, fy)) for symbol in sorted(symbols)]
        usable = [report for _, report in reports if report is not None]                  # a page without its filing on disk is skipped
        for report_a, report_b in itertools.combinations(usable, 2):
            write_compare_page(report_a, report_b, Path(folder))
            made += 1
    return made
