"""The sample pages in samples/ (a deliverable of the assignment), made by ONE command:  python make_samples.py

A handful of companies chosen to show the dashboard in different situations, plus a few error pages.  Everything is made
by the same code that `main.py` uses.  Report pages are rebuilt from the filings already on disk when possible (no internet);
a filing that is not on disk is downloaded first (politely, and cached).  The error pages are made by really triggering the
errors with offline inputs, so they show exactly what a user would see.
"""

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from brsr_p6.analysis.trend_model import NOT_FILED, YearEntry, build_trend
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.fiscal_year import fiscal_years_between, parse_fiscal_year, previous_fiscal_year
from brsr_p6.core.paths import DEFAULT_RAW_DIR, SAMPLES_DIR, safe_name
from brsr_p6.download.company_lookup import pick_company
from brsr_p6.download.filings import parse_listing, select_filing
from brsr_p6.extraction.report_io import save_report
from brsr_p6.parsing.xbrl_reader import read_filing
from brsr_p6.rendering.render import (HUB_FILE_NAME, error_page_path, trend_page_name, write_compare_page, write_error_page, write_page, write_summary_page,
                                      write_trend_page)
from brsr_p6.views.error_view import build_error_view
from brsr_p6.views.hub_view import SAMPLES_TITLE
from brsr_p6.workflows.compare import generate_comparison_page
from brsr_p6.workflows.hub import generate_hub
from brsr_p6.workflows.pipeline import generate_page, generate_summary_page, generate_trend_page, load_saved_report


@dataclass(frozen=True)
class SampleCompany:
    symbol: str      # the NSE symbol: how the filing is found on disk
    company: str     # what a user would type
    fy: str
    shows: str       # one sentence for samples/README.md


@dataclass(frozen=True)
class SampleTrend:
    symbol: str
    company: str
    fy_from: str
    fy_to: str
    shows: str
    not_filed: tuple = ()     # years in the range that NSE really has no filing for (so they are flagged, not downloaded)


@dataclass(frozen=True)
class SampleSummary:
    symbol: str
    company: str
    fy: str
    shows: str
    previous_note: str = ""   # set only when NSE really has no filing for the year before (so last year's own report is not looked for)


@dataclass(frozen=True)
class SampleComparison:
    symbol_a: str
    company_a: str
    symbol_b: str
    company_b: str
    fy: str
    shows: str


@dataclass(frozen=True)
class SampleError:
    company: str     # what the user "typed"
    fy: str
    shows: str
    trigger: object  # a function that raises the error (offline)
    tool: str = "main"       # the command whose error it is: "main", "trends" or "summary"


SAMPLE_COMPANIES = (
    SampleCompany("TATASTEEL", "Tata Steel", "2025-26",
                  "Heavy industry (steel). The company's emissions are typed in the wrong scale: shown as filed, warned, never compared."),
    SampleCompany("RELIANCE", "Reliance", "2023-24",
                  "A large conglomerate and the cleanest example: almost every card has a better / worse verdict."),
    SampleCompany("WIPRO", "Wipro", "2025-26",
                  "IT services. Energy is filed in megajoules and shown in GJ, marked 'unit changed by us'."),
    SampleCompany("INFY", "Infosys", "2021-22",
                  "IT services, older filing layout: a damaged file that had to be cleaned, monthly air figures, energy with no unit."),
    SampleCompany("HDFCBANK", "HDFC Bank", "2022-23",
                  "A bank (sparse data), older layout: many 'Not reported' and 'reported as 0', and the page still stays honest."),
)


SAMPLE_TRENDS = (
    SampleTrend("TATASTEEL", "Tata Steel", "2021-22", "2025-26",
                "Five years with everything the trend page handles: FY 2021-22 is not on NSE (shown from the next filing's previous-year column), "
                "the basis changes from consolidated to standalone, a later filing restates figures, and the emissions are mis-scaled.",
                not_filed=("2021-22",)),
    SampleTrend("WIPRO", "Wipro", "2023-24", "2025-26",
                "The reporting basis flips from year to year (standalone, consolidated, consolidated), so only years on the same basis are compared."),
    SampleTrend("RELIANCE", "Reliance", "2021-22", "2023-24",
                "A company on one basis throughout. FY 2021-22 is not on NSE, and FY 2022-23 uses the older SEBI layout with no energy unit.",
                not_filed=("2021-22",)),
)


SAMPLE_SUMMARIES = (
    SampleSummary("TATASTEEL", "Tata Steel", "2025-26",
                  "A mixed year: one figure improved, three stayed about the same and four got worse. Last year's own report was checked "
                  "and nothing was restated."),
    SampleSummary("WIPRO", "Wipro", "2025-26",
                  "A year where all 9 figures that can be compared improved: the page shows the three biggest, says plainly that nothing got "
                  "worse, and still lists every figure."),
    SampleSummary("RELIANCE", "Reliance", "2022-23",
                  "NSE has no filing for FY 2021-22, so there is no report of last year's own: the comparison uses the previous-year column "
                  "of this filing, and the page says so.",
                  previous_note="NSE has no BRSR filing of its own for FY 2021-22."),
)


SAMPLE_COMPARISONS = (
    SampleComparison("TATASTEEL", "Tata Steel", "WIPRO", "Wipro", "2025-26",
                     "A steel maker against an IT firm: the totals differ by factors of hundreds, so only the per-rupee figures and the shares "
                     "are ranked. One reports standalone and the other consolidated (the page warns), and Tata Steel's emissions are shown but not "
                     "compared because they look mis-scaled."),
    SampleComparison("RELIANCE", "Reliance", "TATASTEEL", "Tata Steel", "2023-24",
                     "Two large companies on the same (standalone) basis: the fairest case, so most per-rupee rows get a verdict."),
    SampleComparison("HDFCBANK", "HDFC Bank", "RELIANCE", "Reliance", "2022-23",
                     "A bank against a conglomerate in the older filing layout: the bank's per-rupee figures have no stated unit and Reliance "
                     "filed its own as 0, so none of them is compared; only the two shares get a verdict."),
)


# ------------------------------------------------------------------------------------------------ the error examples
def _unknown_company():
    pick_company("Xyzzy Quux", [])                       # NSE's search found nothing


def _year_too_early():
    parse_fiscal_year("2019-20")


def _year_not_on_nse(symbol="TATASTEEL"):
    listing = DEFAULT_RAW_DIR / symbol / "filings_index.json"
    if not listing.exists():
        raise FileNotFoundError(f"data/raw/{symbol}/filings_index.json is not on disk")
    records = parse_listing(json.loads(listing.read_text(encoding="utf-8"))["payload"], symbol)
    select_filing(records, "2021-22")


def _summary_year_not_on_nse():
    _year_not_on_nse("RELIANCE")


def _years_the_wrong_way_round():
    fiscal_years_between("2025-26", "2021-22")


def _damaged_filing():
    """A file that starts like a real SEBI filing but is cut off in the middle, as a damaged download would be."""
    start = '<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:in-capmkt="http://www.sebi.gov.in/xbrl/2024-04-30/in-capmkt">'
    with tempfile.TemporaryDirectory() as folder:
        broken = Path(folder) / "BRSR_damaged_example.xml"
        broken.write_text(start + "\n<in-capmkt:TotalEnergyConsumed contextRef=\"DCYMain\">1234", encoding="utf-8")   # never closed
        read_filing(broken)


SAMPLE_ERRORS = (
    SampleError("Xyzzy Quux", "2023-24", "A company name NSE does not know.", _unknown_company),
    SampleError("Reliance", "2019-20", "A financial year before BRSR reporting began (FY 2021-22).", _year_too_early),
    SampleError("Tata Steel", "2021-22", "A real company and a valid year, but NSE has no filing for it: lists the years it does have.",
                _year_not_on_nse),
    SampleError("Infosys", "2021-22", "A filing file on NSE that is damaged (here a deliberately broken file).", _damaged_filing),
    SampleError("Reliance", "2025-26 to 2021-22", "A trend request with the years the wrong way round (trends.py).", _years_the_wrong_way_round, tool="trends"),
    SampleError("Reliance", "2021-22", "A summary request (summary.py) for a year NSE has no filing for: the suggested commands use summary.py.",
                _summary_year_not_on_nse, tool="summary"),
)


# ------------------------------------------------------------------------------------------------ making the files
def make_samples(output_dir: Path = SAMPLES_DIR, progress=print) -> list:
    """Write every sample page and samples/README.md.  Returns the paths of the pages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_pages, error_pages = [], []

    for sample in SAMPLE_COMPANIES:
        report = load_saved_report(sample.symbol, sample.fy)
        if report is None:                               # not on disk yet: do what main.py does (download politely, then read)
            progress(f"{sample.company} {sample.fy}: not on disk, downloading ...")
            page, report = generate_page(sample.company, sample.fy, output_dir=output_dir)
        else:
            save_report(report)
            page = write_page(report, output_dir)
        progress(f"wrote {page.name}")
        report_pages.append((sample, page))

    trend_pages = []
    for sample in SAMPLE_TRENDS:
        page = _write_trend(sample, output_dir, progress)
        progress(f"wrote {page.name}")
        trend_pages.append((sample, page))

    summary_pages = []
    for sample in SAMPLE_SUMMARIES:
        page = _write_summary(sample, output_dir, progress)
        progress(f"wrote {page.name}")
        summary_pages.append((sample, page))

    comparison_pages = []
    for sample in SAMPLE_COMPARISONS:
        page = _write_comparison(sample, output_dir, progress)
        progress(f"wrote {page.name}")
        comparison_pages.append((sample, page))

    for example in SAMPLE_ERRORS:
        try:
            example.trigger()
        except BrsrError as error:
            page = write_error_page(build_error_view(error, example.company, example.fy, example.tool), example.company, example.fy, output_dir)
            progress(f"wrote {page.name}")
            error_pages.append((example, page))
        except FileNotFoundError as missing:             # the saved filing list for the example is not on disk: skip it, say so
            progress(f"skipped the example for {example.company} {example.fy}: {missing}")

    (output_dir / "README.md").write_text(_readme(report_pages, trend_pages, summary_pages, comparison_pages, error_pages), encoding="utf-8")
    pages = [page for _, page in report_pages + trend_pages + summary_pages + comparison_pages + error_pages]
    hub, _ = generate_hub(output_dir, embed=False, title=SAMPLES_TITLE)     # linked, not embedded: the pages are already in this folder
    progress(f"wrote {hub.name}")
    return pages + [hub]


def _summary_reports(sample):
    """(latest report, last year's own report or None, why it is None), all from disk; None when something needed is not on disk."""
    report = load_saved_report(sample.symbol, sample.fy)
    if report is None:
        return None
    if sample.previous_note:
        return report, None, sample.previous_note
    previous = load_saved_report(sample.symbol, previous_fiscal_year(sample.fy))
    return None if previous is None else (report, previous, "")


def _write_comparison(sample, output_dir, progress):
    """A comparison page built from the filings on disk; if one is not on disk, do what compare.py does (download politely, then read)."""
    report_a, report_b = load_saved_report(sample.symbol_a, sample.fy), load_saved_report(sample.symbol_b, sample.fy)
    if report_a is None or report_b is None:
        progress(f"{sample.company_a} / {sample.company_b} FY {sample.fy}: not on disk, downloading ...")
        page, _, _ = generate_comparison_page(sample.company_a, sample.company_b, sample.fy, output_dir=output_dir)
        return page
    return write_compare_page(report_a, report_b, output_dir)


def _write_summary(sample, output_dir, progress):
    """A summary page built from the filings on disk; if one is not on disk, do what summary.py does (download politely, then read)."""
    found = _summary_reports(sample)
    if found is None:
        progress(f"{sample.company} FY {sample.fy}: not on disk, downloading ...")
        page, _ = generate_summary_page(sample.company, sample.fy, output_dir=output_dir)
        return page
    return write_summary_page(*found, output_dir=output_dir)


def _write_trend(sample, output_dir, progress):
    """A trend page built from the filings on disk; a year that is neither on disk nor known to be unfiled makes it download first."""
    entries = []
    for fy in fiscal_years_between(sample.fy_from, sample.fy_to):
        report = load_saved_report(sample.symbol, fy)
        if report is None and fy not in sample.not_filed:
            progress(f"{sample.company} FY {fy}: not on disk, downloading ...")
            page, _ = generate_trend_page(sample.company, sample.fy_from, sample.fy_to, output_dir=output_dir)
            return page
        entries.append(YearEntry(fy, report) if report else YearEntry(fy, problem="NSE has no BRSR filing for this year.", kind=NOT_FILED))
    name = next(entry.report.company_name for entry in entries if entry.report)
    return write_trend_page(build_trend(name, sample.symbol, entries), output_dir)


def _readme(report_pages, trend_pages, summary_pages, comparison_pages, error_pages):
    lines = [
        "# Sample pages",
        "",
        "Open any file in a web browser. They are made by `python make_samples.py` (do not edit them by hand).",
        "",
        "**Easiest: open [index.html](index.html).** It puts every page below behind one dropdown and a search box (it opens the files in this folder).",
        "",
        "## Report pages (Dashboard tab first, SEBI-format report second)",
        "",
        "| File | Company and year | What it shows |",
        "|---|---|---|",
    ]
    lines += [f"| [{page.name}]({page.name}) | {s.company}, FY {s.fy} | {s.shows} |" for s, page in report_pages]
    lines += ["", "## Trend pages (one company over several years: `python trends.py ...`)", "",
              "| File | Company and years | What it shows |", "|---|---|---|"]
    lines += [f"| [{page.name}]({page.name}) | {s.company}, FY {s.fy_from} to FY {s.fy_to} | {s.shows} |" for s, page in trend_pages]
    lines += ["", "## Year-on-year summaries (the 3 biggest improvements and setbacks: `python summary.py ...`)", "",
              "| File | Company and year | What it shows |", "|---|---|---|"]
    lines += [f"| [{page.name}]({page.name}) | {s.company}, FY {s.fy} | {s.shows} |" for s, page in summary_pages]
    lines += ["", "## Company comparisons (two companies, one year: `python compare.py ...`)", "",
              "| File | Companies and year | What it shows |", "|---|---|---|"]
    lines += [f"| [{page.name}]({page.name}) | {s.company_a} vs {s.company_b}, FY {s.fy} | {s.shows} |" for s, page in comparison_pages]
    lines += ["", "## Error pages (what you see instead of a report when something goes wrong)", "",
              "| File | What was asked | What it shows |", "|---|---|---|"]
    lines += [f"| [{page.name}]({page.name}) | {e.company}, {e.fy} | {e.shows} |" for e, page in error_pages]
    return "\n".join(lines) + "\n"


def expected_files():
    """Names of the files make_samples() writes (for tests and the README)."""
    names = [f"{safe_name(s.symbol)}_{s.fy}.html" for s in SAMPLE_COMPANIES]
    names += [trend_page_name(s.symbol, s.fy_from, s.fy_to) for s in SAMPLE_TRENDS]
    names += [f"{safe_name(s.symbol)}_summary_{s.fy}.html" for s in SAMPLE_SUMMARIES]
    names += [f"{safe_name(s.symbol_a)}_vs_{safe_name(s.symbol_b)}_{s.fy}.html" for s in SAMPLE_COMPARISONS]
    names += [error_page_path(e.company, e.fy, Path()).name for e in SAMPLE_ERRORS]
    names.append(HUB_FILE_NAME)                      # the viewer that holds all of them
    return names
