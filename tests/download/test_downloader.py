"""End-to-end tests of the download flow with a fake NSE (company search + filing list + files), all offline."""

import json

import pytest

from brsr_p6.core.errors import AmbiguousCompany, FileNotAvailable, NoFilingFound, UnknownCompany, UnsupportedYear
from brsr_p6.download.company_lookup import SEARCH_URL
from brsr_p6.download.downloader import download_filings

XML = "https://nsearchives.nseindia.com/corporate/xbrl/"
PDF = "https://nsearchives.nseindia.com/corporate/"

SEARCH_ANSWER = [{"companyName": "Tata Steel Limited", "symbol": "TATASTEEL", "series": "EQ", "segment": "in equity"}]


def row(fy_from, xbrl, pdf):
    return {
        "symbol": "TATASTEEL", "companyName": "Tata Steel Limited", "fyFrom": fy_from, "fyTo": fy_from + 1,
        "submissionDate": "24-Jun-2025", "revisionDate": "-", "xbrlFile": XML + xbrl, "attachmentFile": PDF + pdf,
    }


LISTING_ANSWER = {"data": [row(2023, "b.xml", "b.pdf"), row(2022, "a.xml", "null"), row(2024, "c.xml", "c.pdf")]}


class FakeNse:
    """Stands in for NseClient: same two methods, but answers from memory and writes tiny files."""

    def __init__(self, search=SEARCH_ANSWER, listing=LISTING_ANSWER, missing_files=()):
        self.search, self.listing, self.missing_files = search, listing, set(missing_files)
        self.api_calls, self.downloads = [], []

    @property
    def request_count(self):
        return len(self.api_calls) + len(self.downloads)

    def get_json(self, url, params=None):
        self.api_calls.append(url)
        return self.search if url == SEARCH_URL else self.listing

    def download(self, url, dest, kind):
        self.downloads.append(url)
        if url.rsplit("/", 1)[-1] in self.missing_files:
            raise FileNotAvailable("gone")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"<?xml?>" if kind == "xml" else b"%PDF")
        return 1234


def run(tmp_path, client, **kwargs):
    quiet = kwargs.pop("progress", lambda message: None)
    return download_filings("Tata Steel", raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache", client=client, progress=quiet, **kwargs)


def test_downloads_every_year_into_symbol_and_year_folders(tmp_path):
    report = run(tmp_path, FakeNse())
    assert report.company.symbol == "TATASTEEL"
    assert [d.record.fy for d in report.downloads] == ["2022-23", "2023-24", "2024-25"]
    for fy, name in [("2022-23", "a.xml"), ("2023-24", "b.xml"), ("2024-25", "c.xml")]:
        assert (tmp_path / "raw" / "TATASTEEL" / fy / name).exists()
        note = json.loads((tmp_path / "raw" / "TATASTEEL" / fy / "filing.json").read_text(encoding="utf-8"))
        assert note["fy"] == fy and note["xbrl_url"].endswith(name)
    assert report.missing_years == ["2021-22"]
    assert all(d.xml_status == "downloaded" for d in report.downloads)


def test_second_run_makes_no_requests_at_all(tmp_path):
    first = FakeNse()
    run(tmp_path, first)
    second = FakeNse()
    report = run(tmp_path, second)
    assert second.api_calls == [] and second.downloads == []  # search, listing and files all came from disk
    assert report.requests_made == 0
    assert all(d.xml_status == "cached" for d in report.downloads)


def test_single_year(tmp_path):
    client = FakeNse()
    report = run(tmp_path, client, fy="FY2023-24")
    assert [d.record.fy for d in report.downloads] == ["2023-24"]
    assert client.downloads == [XML + "b.xml"]
    assert report.missing_years == []


def test_year_before_2021_22_is_rejected_before_any_request(tmp_path):
    client = FakeNse()
    with pytest.raises(UnsupportedYear):
        run(tmp_path, client, fy="2019-20")
    assert client.api_calls == [] and client.downloads == []


def test_year_nse_does_not_have_names_the_available_years(tmp_path):
    with pytest.raises(NoFilingFound) as excinfo:
        run(tmp_path, FakeNse(), fy="2021-22")
    assert "FY 2022-23" in str(excinfo.value)


def test_pdf_is_only_downloaded_on_request_and_null_links_are_reported(tmp_path):
    without = run(tmp_path, FakeNse())
    assert all(d.pdf_status == "" for d in without.downloads)

    client = FakeNse()
    report = run(tmp_path, client, include_pdf=True)
    by_fy = {d.record.fy: d for d in report.downloads}
    assert by_fy["2022-23"].pdf_status == "missing" and by_fy["2022-23"].notes
    assert by_fy["2023-24"].pdf_status == "downloaded"
    assert (tmp_path / "raw" / "TATASTEEL" / "2023-24" / "b.pdf").exists()


def test_one_missing_file_does_not_stop_the_other_years(tmp_path):
    report = run(tmp_path, FakeNse(missing_files={"b.xml"}))
    status = {d.record.fy: d.xml_status for d in report.downloads}
    assert status == {"2022-23": "downloaded", "2023-24": "missing", "2024-25": "downloaded"}


def test_company_without_filings(tmp_path):
    with pytest.raises(NoFilingFound) as excinfo:
        run(tmp_path, FakeNse(listing={"data": []}))
    assert "top 1,000" in str(excinfo.value)


def test_unknown_and_ambiguous_companies(tmp_path):
    with pytest.raises(UnknownCompany):
        run(tmp_path, FakeNse(search=[]))
    many = [
        {"companyName": "Tata Power Company Limited", "symbol": "TATAPOWER", "series": "EQ", "segment": "in equity"},
        {"companyName": "Tata Motors Limited", "symbol": "TATAMOTORS", "series": "EQ", "segment": "in equity"},
    ]
    with pytest.raises(AmbiguousCompany):
        run(tmp_path / "other", FakeNse(search=many))


def test_manually_downloaded_file_is_reused(tmp_path):
    """The assignment allows hand-downloaded filings: a file already in the right folder is not fetched again."""
    manual = tmp_path / "raw" / "TATASTEEL" / "2023-24"
    manual.mkdir(parents=True)
    (manual / "b.xml").write_bytes(b"<?xml?> my own copy")
    client = FakeNse()
    run(tmp_path, client, fy="2023-24")
    assert client.downloads == []
    assert (manual / "b.xml").read_bytes() == b"<?xml?> my own copy"


def test_pick_chooses_the_years_after_the_list_of_filings_is_known(tmp_path):
    """The summary does not know the newest year until NSE has answered, so the years are chosen by a function that sees the list."""
    seen = []

    def pick(records):
        seen.append([r.fy for r in records])
        return "2023-24", records[-1].fy

    client = FakeNse()
    report = run(tmp_path, client, pick=pick)
    assert seen == [["2022-23", "2023-24", "2024-25"]]
    assert [d.record.fy for d in report.downloads] == ["2023-24", "2024-25"] and client.downloads == [XML + "b.xml", XML + "c.xml"]


def test_first_and_last_keep_only_the_years_in_between_and_the_report_still_lists_every_filing(tmp_path):
    client = FakeNse()
    report = run(tmp_path, client, first="2023-24", last="2023-24")
    assert [d.record.fy for d in report.downloads] == ["2023-24"] and client.downloads == [XML + "b.xml"]
    assert [r.fy for r in report.records] == ["2022-23", "2023-24", "2024-25"]               # what NSE has, for flagging missing years
    assert [d.record.fy for d in run(tmp_path, FakeNse(), first="2023-24").downloads] == ["2023-24", "2024-25"]
    assert [d.record.fy for d in run(tmp_path, FakeNse(), last="2022-23").downloads] == ["2022-23"]
