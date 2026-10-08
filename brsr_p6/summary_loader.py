"""Load what the year-on-year summary needs: the LATEST filing, and (when it exists) the filing of the year before.

The comparison itself only needs the latest filing, because every filing carries last year's figures in its previous-year column.
The previous year's own filing is optional: when NSE has it and it can be read, it lets the summary notice figures the company
restated; when it is missing or damaged, the summary still works and says so.  The latest filing is essential: without it there
is nothing to summarise, so that is an error (and an error page).
"""

from dataclasses import dataclass

from brsr_p6.company_lookup import Company
from brsr_p6.downloader import DEFAULT_CACHE_DIR, DEFAULT_RAW_DIR, download_filings
from brsr_p6.errors import UnparseableFiling
from brsr_p6.filings import select_filing
from brsr_p6.fiscal_year import EARLIEST_START_YEAR, parse_fiscal_year, previous_fiscal_year
from brsr_p6.models import Principle6Report
from brsr_p6.nse_client import NseClient
from brsr_p6.trend_loader import read_year


@dataclass
class SummaryInputs:
    company: Company
    latest: Principle6Report
    previous: Principle6Report | None     # last year's OWN filing, when NSE has it and it could be read
    previous_note: str = ""               # why `previous` is None ("" when it is there)


def load_summary_inputs(company_query, fy=None, raw_dir=DEFAULT_RAW_DIR, cache_dir=DEFAULT_CACHE_DIR,
                        client: NseClient | None = None, progress=print) -> SummaryInputs:
    """The latest filing (or the one for `fy`) and last year's filing.  Raises an error when the latest one cannot be used."""
    wanted = parse_fiscal_year(fy) if fy else None                  # a bad year fails here, before any request to NSE
    chosen = {}

    def pick(records):
        """Runs after NSE's list is known: the latest year is the newest filing unless the user named a year."""
        latest = select_filing(records, wanted).fy if wanted else records[-1].fy     # an unknown year lists the years NSE has
        chosen["latest"] = latest
        return previous_fiscal_year(latest), latest

    download = download_filings(company_query, raw_dir=raw_dir, cache_dir=cache_dir, client=client, progress=progress, pick=pick)
    company, latest_fy = download.company, chosen["latest"]
    by_year = {item.record.fy: item for item in download.downloads}

    latest = read_year(latest_fy, by_year[latest_fy], company)
    if latest.report is None:
        raise UnparseableFiling(f"The FY {latest_fy} filing of {company.name} could not be used: {latest.problem}")

    before_fy = previous_fiscal_year(latest_fy)
    previous, note = None, ""
    if int(before_fy[:4]) < EARLIEST_START_YEAR:
        note = f"BRSR reporting began with FY {EARLIEST_START_YEAR}-{(EARLIEST_START_YEAR + 1) % 100:02d}, so there is no report for FY {before_fy}."
    elif before_fy not in by_year:
        note = f"NSE has no BRSR filing of its own for FY {before_fy}."
    else:
        entry = read_year(before_fy, by_year[before_fy], company)
        previous = entry.report
        if previous is None:
            note = f"The FY {before_fy} filing could not be read ({entry.problem})"
    return SummaryInputs(company, latest.report, previous, note)
