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

from brsr_p6.company_lookup import pick_company
from brsr_p6.downloader import DEFAULT_RAW_DIR, PROJECT_ROOT, safe_name
from brsr_p6.error_view import build_error_view
from brsr_p6.errors import BrsrError
from brsr_p6.filings import parse_listing, select_filing
from brsr_p6.fiscal_year import parse_fiscal_year
from brsr_p6.pipeline import generate_page, load_saved_report
from brsr_p6.render import error_page_path, write_error_page, write_page
from brsr_p6.report_io import save_report
from brsr_p6.xbrl_reader import read_filing

SAMPLES_DIR = PROJECT_ROOT / "samples"


@dataclass(frozen=True)
class SampleCompany:
    symbol: str      # the NSE symbol: how the filing is found on disk
    company: str     # what a user would type
    fy: str
    shows: str       # one sentence for samples/README.md


@dataclass(frozen=True)
class SampleError:
    company: str     # what the user "typed"
    fy: str
    shows: str
    trigger: object  # a function that raises the error (offline)


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


# ------------------------------------------------------------------------------------------------ the error examples
def _unknown_company():
    pick_company("Xyzzy Quux", [])                       # NSE's search found nothing


def _year_too_early():
    parse_fiscal_year("2019-20")


def _year_not_on_nse():
    listing = DEFAULT_RAW_DIR / "TATASTEEL" / "filings_index.json"
    if not listing.exists():
        raise FileNotFoundError("data/raw/TATASTEEL/filings_index.json is not on disk")
    records = parse_listing(json.loads(listing.read_text(encoding="utf-8"))["payload"], "TATASTEEL")
    select_filing(records, "2021-22")


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

    for example in SAMPLE_ERRORS:
        try:
            example.trigger()
        except BrsrError as error:
            page = write_error_page(build_error_view(error, example.company, example.fy), example.company, example.fy, output_dir)
            progress(f"wrote {page.name}")
            error_pages.append((example, page))
        except FileNotFoundError as missing:             # the saved filing list for the example is not on disk: skip it, say so
            progress(f"skipped the example for {example.company} {example.fy}: {missing}")

    (output_dir / "README.md").write_text(_readme(report_pages, error_pages), encoding="utf-8")
    return [page for _, page in report_pages + error_pages]


def _readme(report_pages, error_pages):
    lines = [
        "# Sample pages",
        "",
        "Open any file in a web browser. They are made by `python make_samples.py` (do not edit them by hand).",
        "",
        "## Report pages (Dashboard tab first, SEBI-format report second)",
        "",
        "| File | Company and year | What it shows |",
        "|---|---|---|",
    ]
    lines += [f"| [{page.name}]({page.name}) | {s.company}, FY {s.fy} | {s.shows} |" for s, page in report_pages]
    lines += ["", "## Error pages (what you see instead of a report when something goes wrong)", "",
              "| File | What was asked | What it shows |", "|---|---|---|"]
    lines += [f"| [{page.name}]({page.name}) | {e.company}, {e.fy} | {e.shows} |" for e, page in error_pages]
    return "\n".join(lines) + "\n"


def expected_files():
    """Names of the files make_samples() writes (for tests and the README)."""
    names = [f"{safe_name(s.symbol)}_{s.fy}.html" for s in SAMPLE_COMPANIES]
    names += [error_page_path(e.company, e.fy, Path()).name for e in SAMPLE_ERRORS]
    return names
