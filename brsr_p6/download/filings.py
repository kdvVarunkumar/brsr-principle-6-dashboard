"""Ask NSE which BRSR filings a company has, and choose the right one for a financial year.

What we learned about NSE's listing API in Phase 1 (see context.md section 4a):
  * It returns one row per company per financial year; a revised filing REPLACES the original row.
  * It only shows the last 365 days unless we pass from_date / to_date (DD-MM-YYYY).
  * The file links (xbrlFile, attachmentFile) must be taken from the response, never guessed.
    The PDF link is sometimes literally ".../null", so the PDF is optional.
"""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from brsr_p6.core.errors import NoFilingFound, NSEUnavailable
from brsr_p6.core.fiscal_year import EARLIEST_START_YEAR, format_fiscal_year

LISTING_URL = "https://www.nseindia.com/api/corporate-bussiness-sustainabilitiy"
LISTING_MAX_AGE = timedelta(hours=24)  # how long a saved listing is trusted before asking NSE again


@dataclass(frozen=True)
class FilingRecord:
    symbol: str
    company_name: str
    fy: str  # canonical, e.g. "2025-26"
    fy_from: int
    fy_to: int
    submission_date: str  # as NSE prints it, e.g. "03-Jun-2026"
    revision_date: str | None  # None if the filing was never revised
    xbrl_url: str | None
    pdf_url: str | None


def clean_url(value) -> str | None:
    """NSE sometimes sends '', '-' or '.../corporate/null' instead of a real link."""
    if not value or not isinstance(value, str):
        return None
    value = value.strip()
    if value in ("-", "null") or value.rstrip("/").lower().endswith("/null"):
        return None
    return value


def parse_listing(payload, symbol: str) -> list:
    """Turn NSE's JSON into a list of FilingRecord (one per financial year, newest revision wins)."""
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise NSEUnavailable("NSE returned an unexpected answer for the filing list. Try again later.")

    best = {}  # fy -> (sort_key, record)
    for row in payload["data"]:
        try:
            fy_from, fy_to = int(row["fyFrom"]), int(row["fyTo"])
        except (KeyError, TypeError, ValueError):
            continue  # a row without a usable financial year cannot be used
        revision = row.get("revisionDate")
        record = FilingRecord(
            symbol=row.get("symbol") or symbol,
            company_name=row.get("companyName") or symbol,
            fy=format_fiscal_year(fy_from, fy_to),
            fy_from=fy_from,
            fy_to=fy_to,
            submission_date=row.get("submissionDate") or "",
            revision_date=None if revision in (None, "", "-") else revision,
            xbrl_url=clean_url(row.get("xbrlFile")),
            pdf_url=clean_url(row.get("attachmentFile")),
        )
        # If NSE ever sent two rows for one year, keep the most recently revised/submitted one.
        sort_key = (_parse_date(record.revision_date), _parse_date(record.submission_date))
        if record.fy not in best or sort_key > best[record.fy][0]:
            best[record.fy] = (sort_key, record)

    return sorted((rec for _, rec in best.values()), key=lambda r: r.fy_from)


def list_filings(client, symbol: str, cache_dir: Path | None = None, refresh: bool = False, today: date | None = None, notify=None):
    """All BRSR filings NSE has for `symbol` (FY 2021-22 onwards). Cached for 24 h in <cache_dir>/filings_index.json.

    If the saved list is older than 24 h and NSE cannot be reached, the older list is used instead of failing, and `notify`
    (a function taking one sentence) is told.  With `refresh=True` the user explicitly wants NSE's latest answer, so a
    failure is reported instead.
    """
    today = today or date.today()
    cache_file = cache_dir / "filings_index.json" if cache_dir else None

    saved = _read_saved_listing(cache_file)                 # (when it was fetched, NSE's answer) or None
    if saved and not refresh and datetime.now() - saved[0] < LISTING_MAX_AGE:
        return parse_listing(saved[1], symbol)

    try:
        payload = client.get_json(
            LISTING_URL,
            params={
                "index": "equities",
                "symbol": symbol,
                "from_date": f"01-04-{EARLIEST_START_YEAR}",
                "to_date": today.strftime("%d-%m-%Y"),
            },
        )
        parse_listing(payload, symbol)  # validate the shape BEFORE saving it
    except NSEUnavailable:
        if saved is None or refresh:
            raise
        if notify:
            notify(f"NSE could not be reached, so the filing list saved on {saved[0]:%d-%b-%Y} is used (it may be out of date).")
        return parse_listing(saved[1], symbol)

    if cache_file:
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(
            json.dumps({"fetched_at": datetime.now().isoformat(timespec="seconds"), "payload": payload}, indent=1),
            encoding="utf-8",
        )
    return parse_listing(payload, symbol)


def _read_saved_listing(cache_file):
    """What we saved last time: (datetime fetched, payload), or None when there is no usable saved copy."""
    if not cache_file or not cache_file.exists():
        return None
    try:
        saved = json.loads(cache_file.read_text(encoding="utf-8"))
        return datetime.fromisoformat(saved["fetched_at"]), saved["payload"]
    except (ValueError, KeyError, TypeError):
        return None                                         # unreadable cache: treat it as not there


def select_filing(records: list, fy: str) -> FilingRecord:
    """The filing for financial year `fy`, or a NoFilingFound that tells the user which years DO exist."""
    for record in records:
        if record.fy == fy:
            return record
    available = ", ".join(f"FY {r.fy}" for r in records) or "none"
    name = records[0].company_name if records else "this company"
    raise NoFilingFound(
        f"NSE has no BRSR filing for {name} for FY {fy}. Filings available on NSE: {available}.",
        symbol=records[0].symbol if records else "",
        available=[r.fy for r in records],
    )


def missing_years(records: list) -> list:
    """Financial years from FY 2021-22 up to the newest filing that NSE has no filing for."""
    if not records:
        return []
    have = {r.fy_from for r in records}
    newest = max(have)
    return [format_fiscal_year(y, y + 1) for y in range(EARLIEST_START_YEAR, newest + 1) if y not in have]


def _parse_date(text):
    """'03-Jun-2026' -> a date (None if missing/unreadable), so dates can be compared."""
    try:
        return datetime.strptime(text, "%d-%b-%Y").date()
    except (TypeError, ValueError):
        return date.min
