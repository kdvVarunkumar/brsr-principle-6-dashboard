"""Load the filings for a range of years.  The only part of the trend feature that touches files and the internet.

One call lists what NSE has, downloads the requested years politely (cached, 3 s apart), and reads each one.  A year that cannot be
used does NOT stop the others: it becomes a flagged entry with the specific reason (not filed, file missing, damaged file...), so
the trend page can show the problem instead of hiding the year.  Only problems with the whole request (unknown company, no
filings at all, NSE unreachable) raise an error, and those become an error page.
"""

from brsr_p6.downloader import DEFAULT_CACHE_DIR, DEFAULT_RAW_DIR, download_filings
from brsr_p6.errors import BrsrError, NoFilingFound, UnparseableFiling
from brsr_p6.extractor import build_report
from brsr_p6.fiscal_year import EARLIEST_START_YEAR, fiscal_years_between, format_fiscal_year, parse_fiscal_year
from brsr_p6.nse_client import NseClient
from brsr_p6.trend_model import BUG, NO_FILE, NOT_FILED, UNREADABLE, YearEntry
from brsr_p6.xbrl_reader import read_filing


def load_year_entries(company_query, fy_from=None, fy_to=None, raw_dir=DEFAULT_RAW_DIR, cache_dir=DEFAULT_CACHE_DIR,
                      client: NseClient | None = None, progress=print):
    """Returns (company, entries): one YearEntry per financial year from `fy_from` to `fy_to`, oldest first.

    Without `fy_from` the range starts at FY 2021-22 (the first BRSR year); without `fy_to` it ends at the newest filing NSE has."""
    first = parse_fiscal_year(fy_from) if fy_from else None
    last = parse_fiscal_year(fy_to) if fy_to else None
    if first and last:
        fiscal_years_between(first, last)                       # a bad range fails now, before any request to NSE

    download = download_filings(company_query, first=first, last=last, raw_dir=raw_dir, cache_dir=cache_dir, client=client,
                                progress=progress)
    company, records = download.company, download.records
    available = [r.fy for r in records]

    start = first or format_fiscal_year(EARLIEST_START_YEAR, EARLIEST_START_YEAR + 1)
    end = last or available[-1]                                # the newest filing NSE has
    if int(start[:4]) > int(end[:4]):                          # only possible when `last` was not given
        raise NoFilingFound(f"NSE has no BRSR filing for {company.name} from FY {start} onwards. Its newest filing is FY {end}.",
                            symbol=company.symbol, available=available)

    by_year = {item.record.fy: item for item in download.downloads}
    entries = []
    for fy in fiscal_years_between(start, end):
        item = by_year.get(fy)
        if item is None:
            entries.append(YearEntry(fy, problem="NSE has no BRSR filing for this year.", kind=NOT_FILED))
        else:
            entries.append(read_year(fy, item, company))

    if not any(entry.report for entry in entries):
        raise _nothing_usable(company, entries, available)
    return company, entries


def read_year(fy, item, company):
    """Read one downloaded filing.  Never raises: a problem becomes a flagged YearEntry."""
    if item.xml_path is None or not item.xml_path.exists():
        return YearEntry(fy, problem="NSE lists this filing, but its XBRL file is missing or no longer on NSE.", kind=NO_FILE)
    try:
        report = build_report(read_filing(item.xml_path), company.name, company.symbol, fy, record=item.record)
    except BrsrError as error:
        return YearEntry(fy, problem=str(error), kind=UNREADABLE)
    except Exception as error:                                  # a bug in one year must not hide the other years
        return YearEntry(fy, problem=f"Unexpected problem while reading this filing ({type(error).__name__}: {error}).", kind=BUG)
    return YearEntry(fy, report=report)


def _nothing_usable(company, entries, available):
    """The error for a request in which not a single year could be read."""
    unread = [entry for entry in entries if entry.kind != NOT_FILED]
    if unread:
        details = " ".join(f"FY {entry.fy}: {entry.problem}" for entry in unread)
        return UnparseableFiling(f"None of the filings in this range could be read for {company.name}. {details}")
    return NoFilingFound(f"NSE has no BRSR filing for {company.name} in FY {entries[0].fy} to FY {entries[-1].fy}. "
                         f"Filings available on NSE: {', '.join('FY ' + fy for fy in available)}.",
                         symbol=company.symbol, available=available)
