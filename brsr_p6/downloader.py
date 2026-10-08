"""Put the pieces together: company text -> symbol -> filing list -> files saved under data/raw/.

Folder layout (one folder per company, one per financial year):
    data/raw/RELIANCE/filings_index.json      <- NSE's listing for the company (cache, 24 h)
    data/raw/RELIANCE/2023-24/<file>.xml      <- the XBRL filing (the file we parse later)
    data/raw/RELIANCE/2023-24/filing.json     <- small note: dates and links of this filing
    data/raw/RELIANCE/2023-24/<file>.pdf      <- only with --with-pdf
Anything already on disk is reused, so a second run makes (almost) no requests to NSE.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from brsr_p6.company_lookup import Company, resolve_company
from brsr_p6.errors import FileNotAvailable, NoFilingFound
from brsr_p6.filings import FilingRecord, list_filings, missing_years, select_filing
from brsr_p6.fiscal_year import parse_fiscal_year
from brsr_p6.nse_client import NseClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # the folder that contains main.py (works from any cwd)
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_CACHE_DIR = PROJECT_ROOT / "data" / "cache"


@dataclass
class FilingDownload:
    record: FilingRecord
    xml_path: Path | None = None
    pdf_path: Path | None = None
    xml_status: str = ""  # "downloaded", "cached" or "missing"
    pdf_status: str = ""  # "downloaded", "cached", "missing" or "" (not requested)
    notes: list = field(default_factory=list)


@dataclass
class DownloadReport:
    company: Company
    downloads: list
    missing_years: list
    requests_made: int = 0  # how many requests this run really sent to NSE (0 = everything came from disk)
    records: list = field(default_factory=list)  # every filing NSE lists for the company (not only the ones downloaded)


def safe_name(text: str) -> str:
    """Make a string safe to use as a folder name (e.g. 'M&M' -> 'M_M')."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", text)


def download_filings(
    company_query: str,
    fy: str | None = None,
    include_pdf: bool = False,
    refresh: bool = False,
    raw_dir: Path = DEFAULT_RAW_DIR,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    client: NseClient | None = None,
    progress=print,
    first: str | None = None,
    last: str | None = None,
) -> DownloadReport:
    """Download the BRSR filing(s) of a company. `fy=None` means every year NSE has (FY 2021-22 onwards).

    `first` / `last` (for example "2022-23") keep only the filings from that year / up to that year: used by the trend page."""
    # 1) Validate the cheap things first, so a typo never costs a request to NSE.
    wanted_fy = parse_fiscal_year(fy) if fy else None
    client = client or NseClient()

    # 2) Company text -> NSE symbol.
    company = resolve_company(company_query, client, cache_path=cache_dir / "company_search.json")
    progress(f"Company: {company.name} ({company.symbol})")

    # 3) What does NSE have for this company?
    company_dir = raw_dir / safe_name(company.symbol)
    records = list_filings(client, company.symbol, cache_dir=company_dir, refresh=refresh, notify=progress)
    if not records:
        raise NoFilingFound(
            f"NSE lists no BRSR filings for {company.name} ({company.symbol}). Only the top 1,000 listed companies "
            "have to file a BRSR (and only from FY 2021-22 onwards).",
            symbol=company.symbol,
        )
    progress("NSE has BRSR filings for: " + ", ".join(f"FY {r.fy}" for r in records))

    # 4) Which of them do we want?
    if wanted_fy:
        targets = [select_filing(records, wanted_fy)]
    else:
        targets = [r for r in records if (first is None or r.fy_from >= int(first[:4])) and (last is None or r.fy_from <= int(last[:4]))]

    # 5) Save them.
    downloads = []
    for number, record in enumerate(targets, start=1):
        progress(f"[{number}/{len(targets)}] FY {record.fy}")
        downloads.append(_download_one(client, record, company_dir, include_pdf, progress))

    return DownloadReport(
        company=company,
        downloads=downloads,
        missing_years=[] if wanted_fy else missing_years(records),
        requests_made=getattr(client, "request_count", 0),
        records=records,
    )


def _download_one(client, record: FilingRecord, company_dir: Path, include_pdf: bool, progress) -> FilingDownload:
    fy_dir = company_dir / record.fy
    result = FilingDownload(record=record)

    if record.xbrl_url:
        result.xml_path = fy_dir / safe_name(record.xbrl_url.rsplit("/", 1)[-1])
        result.xml_status = _fetch_file(client, record.xbrl_url, result.xml_path, "xml", progress)
    else:
        result.xml_status = "missing"
        result.notes.append("NSE lists no XBRL (XML) file for this filing.")

    if include_pdf:
        if record.pdf_url:
            result.pdf_path = fy_dir / safe_name(record.pdf_url.rsplit("/", 1)[-1])
            result.pdf_status = _fetch_file(client, record.pdf_url, result.pdf_path, "pdf", progress)
        else:
            result.pdf_status = "missing"
            result.notes.append("NSE's PDF link for this filing is empty/invalid, so no PDF was downloaded.")

    # A small note next to the files, so later steps know dates and links without asking NSE again.
    fy_dir.mkdir(parents=True, exist_ok=True)
    (fy_dir / "filing.json").write_text(json.dumps(asdict(record), indent=1), encoding="utf-8")
    return result


def _fetch_file(client, url: str, dest: Path, kind: str, progress) -> str:
    if dest.exists() and dest.stat().st_size > 0:
        progress(f"    {kind.upper()}: already on disk, skipped ({dest.name})")
        return "cached"
    try:
        size = client.download(url, dest, kind)
    except FileNotAvailable as exc:  # only this file is gone: record it and carry on with the other years
        progress(f"    {kind.upper()}: not available ({exc})")
        return "missing"
    progress(f"    {kind.upper()}: downloaded {size / 1_048_576:.2f} MB -> {dest.name}")
    return "downloaded"
