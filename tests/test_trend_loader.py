"""Tests for brsr_p6/trend_loader.py with a fake NSE (company search + filing list + files), all offline."""

import pytest
from nse_fakes import XML, FakeNse

from brsr_p6 import trend_loader
from brsr_p6.errors import InvalidFiscalYear, InvalidYearRange, NoFilingFound, UnknownCompany, UnparseableFiling
from brsr_p6.trend_loader import load_year_entries
from brsr_p6.trend_model import BUG, NO_FILE, NOT_FILED, UNREADABLE

def load(tmp_path, client, fy_from=None, fy_to=None):
    return load_year_entries("Test Company", fy_from, fy_to, raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache", client=client,
                             progress=lambda message: None)


def fys(entries):
    return [e.fy for e in entries]


def test_every_year_in_the_range_becomes_an_entry_and_a_missing_one_is_flagged(tmp_path):
    client = FakeNse([2022, 2024])                                              # NSE has FY 2022-23 and FY 2024-25 only
    company, entries = load(tmp_path, client, "2022-23", "2024-25")
    assert company.symbol == "TESTCO" and fys(entries) == ["2022-23", "2023-24", "2024-25"]
    assert [bool(e.report) for e in entries] == [True, False, True]
    assert (entries[1].kind, entries[1].problem) == (NOT_FILED, "NSE has no BRSR filing for this year.")
    assert entries[0].report.fy == "2022-23" and entries[0].report.company_name == "Test Company Limited"


def test_without_a_range_it_runs_from_fy_2021_22_to_the_newest_filing(tmp_path):
    _, entries = load(tmp_path, FakeNse([2022, 2023]))
    assert fys(entries) == ["2021-22", "2022-23", "2023-24"] and entries[0].kind == NOT_FILED


def test_only_the_years_in_the_range_are_downloaded(tmp_path):
    client = FakeNse([2021, 2022, 2023, 2024])
    load(tmp_path, client, "2022-23", "2023-24")
    assert client.downloads == [f"{XML}f2022.xml", f"{XML}f2023.xml"]


def test_years_after_the_newest_filing_are_flagged_not_invented(tmp_path):
    _, entries = load(tmp_path, FakeNse([2022]), "2022-23", "2024-25")
    assert [e.kind for e in entries] == ["", NOT_FILED, NOT_FILED]


def test_one_damaged_file_does_not_stop_the_other_years(tmp_path):
    client = FakeNse([2022, 2023, 2024], files={"f2023.xml": b"<xbrl><not closed>"})
    _, entries = load(tmp_path, client, "2022-23", "2024-25")
    assert [bool(e.report) for e in entries] == [True, False, True]
    assert entries[1].kind == UNREADABLE and "f2023.xml" in entries[1].problem


def test_a_file_that_nse_lists_but_no_longer_has_is_flagged_for_that_year_only(tmp_path):
    _, entries = load(tmp_path, FakeNse([2022, 2023], gone=["f2022.xml"]), "2022-23", "2023-24")
    assert entries[0].kind == NO_FILE and entries[1].report is not None


def test_a_bug_while_reading_one_year_is_contained_and_described(tmp_path, monkeypatch):
    real = trend_loader.build_report

    def fussy(filing, name, symbol, fy, record=None):
        if fy == "2023-24":
            raise KeyError("E1.total")
        return real(filing, name, symbol, fy, record=record)

    monkeypatch.setattr(trend_loader, "build_report", fussy)
    _, entries = load(tmp_path, FakeNse([2022, 2023]), "2022-23", "2023-24")
    assert entries[0].report is not None and entries[1].kind == BUG and "KeyError" in entries[1].problem


def test_when_no_year_can_be_read_the_whole_request_fails_with_every_reason(tmp_path):
    client = FakeNse([2022, 2023], files={"f2022.xml": b"junk", "f2023.xml": b"junk"})
    with pytest.raises(UnparseableFiling) as problem:
        load(tmp_path, client, "2022-23", "2023-24")
    assert "FY 2022-23" in str(problem.value) and "FY 2023-24" in str(problem.value)


def test_a_range_with_no_filing_at_all_lists_what_nse_does_have(tmp_path):
    with pytest.raises(NoFilingFound) as problem:
        load(tmp_path, FakeNse([2024]), "2021-22", "2022-23")
    assert problem.value.symbol == "TESTCO" and problem.value.available == ["2024-25"]


def test_a_start_year_after_the_newest_filing_is_explained(tmp_path):
    with pytest.raises(NoFilingFound) as problem:
        load(tmp_path, FakeNse([2022]), fy_from="2025-26")
    assert "newest filing is FY 2022-23" in str(problem.value)


def test_a_bad_range_fails_before_any_request_to_nse(tmp_path):
    client = FakeNse([2022])
    with pytest.raises(InvalidYearRange):
        load(tmp_path, client, "2024-25", "2022-23")
    with pytest.raises(InvalidFiscalYear):
        load(tmp_path, client, "banana", "2022-23")
    assert client.api_calls == [] and client.downloads == []


def test_an_unknown_company_is_an_error_not_an_empty_page(tmp_path):
    with pytest.raises(UnknownCompany):
        load(tmp_path, FakeNse([2022], search=[]))
