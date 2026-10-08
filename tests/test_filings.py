"""Tests for brsr_p6/filings.py (the sample mirrors the real NSE answer for Tata Steel)."""

import json
from datetime import date, datetime, timedelta

import pytest

from brsr_p6.errors import NoFilingFound, NSEUnavailable
from brsr_p6.filings import clean_url, list_filings, missing_years, parse_listing, select_filing

XML = "https://nsearchives.nseindia.com/corporate/xbrl/"
PDF = "https://nsearchives.nseindia.com/corporate/"


def row(fy_from, submitted, xbrl="a.xml", pdf="a.pdf", revised="-", name="Tata Steel Limited"):
    return {
        "symbol": "TATASTEEL", "companyName": name, "fyFrom": fy_from, "fyTo": fy_from + 1,
        "submissionDate": submitted, "revisionDate": revised,
        "xbrlFile": XML + xbrl if xbrl else "", "attachmentFile": PDF + pdf if pdf else "",
    }


TATA_PAYLOAD = {
    "data": [
        row(2025, "03-Jun-2026", "y2526.xml", "y2526.pdf"),
        row(2024, "24-Jun-2025", "y2425.xml", "y2425.pdf"),
        row(2023, "24-Jun-2024", "y2324.xml", "y2324.pdf"),
        row(2022, "15-Jun-2023", "y2223.xml", "null"),  # NSE really sends a link ending in /null
    ]
}


def test_parse_listing_sorts_oldest_first_and_names_years():
    records = parse_listing(TATA_PAYLOAD, "TATASTEEL")
    assert [r.fy for r in records] == ["2022-23", "2023-24", "2024-25", "2025-26"]
    assert records[-1].xbrl_url == XML + "y2526.xml"
    assert records[-1].revision_date is None  # "-" means never revised


def test_a_null_pdf_link_becomes_none():
    records = parse_listing(TATA_PAYLOAD, "TATASTEEL")
    assert records[0].pdf_url is None
    assert records[1].pdf_url == PDF + "y2324.pdf"


@pytest.mark.parametrize("value", [None, "", "-", "null", "https://nsearchives.nseindia.com/corporate/null"])
def test_clean_url_rejects_placeholders(value):
    assert clean_url(value) is None


def test_duplicate_rows_for_one_year_keep_the_latest_revision():
    payload = {"data": [row(2024, "01-Jul-2025", "orig.xml"), row(2024, "01-Jul-2025", "revised.xml", revised="15-Sep-2025")]}
    (record,) = parse_listing(payload, "X")
    assert record.xbrl_url.endswith("revised.xml")
    assert record.revision_date == "15-Sep-2025"


def test_rows_without_a_usable_year_are_skipped():
    payload = {"data": [{"symbol": "X", "fyFrom": None}, row(2024, "01-Jul-2025")]}
    assert len(parse_listing(payload, "X")) == 1


@pytest.mark.parametrize("payload", [None, [], {}, {"data": "oops"}, "<html>blocked</html>"])
def test_unexpected_payload_is_reported_as_nse_problem(payload):
    with pytest.raises(NSEUnavailable):
        parse_listing(payload, "X")


def test_select_filing_finds_the_year():
    records = parse_listing(TATA_PAYLOAD, "TATASTEEL")
    assert select_filing(records, "2023-24").xbrl_url.endswith("y2324.xml")


def test_select_filing_names_the_years_that_do_exist():
    records = parse_listing(TATA_PAYLOAD, "TATASTEEL")
    with pytest.raises(NoFilingFound) as excinfo:
        select_filing(records, "2021-22")
    message = str(excinfo.value)
    assert "FY 2021-22" in message and "FY 2022-23" in message and "Tata Steel Limited" in message


def test_missing_years_reports_gaps_from_fy_2021_22():
    assert missing_years(parse_listing(TATA_PAYLOAD, "TATASTEEL")) == ["2021-22"]
    assert missing_years([]) == []


class CountingClient:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get_json(self, url, params=None):
        self.calls.append(params)
        return self.payload


def test_listing_uses_nse_date_range_parameters(tmp_path):
    client = CountingClient(TATA_PAYLOAD)
    list_filings(client, "TATASTEEL", cache_dir=tmp_path, today=date(2026, 10, 8))
    assert client.calls[0] == {
        "index": "equities", "symbol": "TATASTEEL", "from_date": "01-04-2021", "to_date": "08-10-2026",
    }


def test_listing_is_cached_then_refreshed_on_request(tmp_path):
    client = CountingClient(TATA_PAYLOAD)
    list_filings(client, "TATASTEEL", cache_dir=tmp_path)
    list_filings(client, "TATASTEEL", cache_dir=tmp_path)
    assert len(client.calls) == 1  # second call served from filings_index.json
    list_filings(client, "TATASTEEL", cache_dir=tmp_path, refresh=True)
    assert len(client.calls) == 2


def test_stale_listing_cache_is_ignored(tmp_path):
    old = (datetime.now() - timedelta(hours=30)).isoformat(timespec="seconds")
    (tmp_path / "filings_index.json").write_text(json.dumps({"fetched_at": old, "payload": TATA_PAYLOAD}), encoding="utf-8")
    client = CountingClient(TATA_PAYLOAD)
    list_filings(client, "TATASTEEL", cache_dir=tmp_path)
    assert len(client.calls) == 1


def test_broken_answer_is_not_cached(tmp_path):
    client = CountingClient({"oops": 1})
    with pytest.raises(NSEUnavailable):
        list_filings(client, "TATASTEEL", cache_dir=tmp_path)
    assert not (tmp_path / "filings_index.json").exists()


class DownClient:
    """NSE cannot be reached."""

    def get_json(self, url, params=None):
        raise NSEUnavailable("no internet")


def save_listing(folder, hours_old):
    when = (datetime.now() - timedelta(hours=hours_old)).isoformat(timespec="seconds")
    (folder / "filings_index.json").write_text(json.dumps({"fetched_at": when, "payload": TATA_PAYLOAD}), encoding="utf-8")


def test_an_old_saved_list_is_used_when_nse_cannot_be_reached_and_the_user_is_told(tmp_path):
    save_listing(tmp_path, hours_old=30)
    told = []
    records = list_filings(DownClient(), "TATASTEEL", cache_dir=tmp_path, notify=told.append)
    assert [r.fy for r in records] == ["2022-23", "2023-24", "2024-25", "2025-26"]
    assert len(told) == 1 and "could not be reached" in told[0] and "may be out of date" in told[0]


def test_a_fresh_saved_list_needs_no_internet_and_says_nothing(tmp_path):
    save_listing(tmp_path, hours_old=1)
    told = []
    assert len(list_filings(DownClient(), "TATASTEEL", cache_dir=tmp_path, notify=told.append)) == 4
    assert told == []


def test_without_any_saved_list_an_unreachable_nse_is_an_error(tmp_path):
    with pytest.raises(NSEUnavailable):
        list_filings(DownClient(), "TATASTEEL", cache_dir=tmp_path)


def test_an_explicit_refresh_never_falls_back_to_old_data(tmp_path):
    save_listing(tmp_path, hours_old=30)
    with pytest.raises(NSEUnavailable):
        list_filings(DownClient(), "TATASTEEL", cache_dir=tmp_path, refresh=True)


def test_an_unreadable_saved_list_counts_as_no_saved_list(tmp_path):
    (tmp_path / "filings_index.json").write_text("{ not json", encoding="utf-8")
    with pytest.raises(NSEUnavailable):
        list_filings(DownClient(), "TATASTEEL", cache_dir=tmp_path)
    assert len(list_filings(CountingClient(TATA_PAYLOAD), "TATASTEEL", cache_dir=tmp_path)) == 4


def test_the_error_for_a_missing_year_carries_the_symbol_and_the_years_nse_has():
    records = parse_listing(TATA_PAYLOAD, "TATASTEEL")
    with pytest.raises(NoFilingFound) as excinfo:
        select_filing(records, "2021-22")
    assert excinfo.value.symbol == "TATASTEEL" and excinfo.value.available == ["2022-23", "2023-24", "2024-25", "2025-26"]
