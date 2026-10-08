"""Tests for brsr_p6/summary_loader.py with a fake NSE, all offline."""

import pytest
from nse_fakes import FakeNse

from brsr_p6.errors import InvalidFiscalYear, NoFilingFound, UnknownCompany, UnparseableFiling
from brsr_p6.summary_loader import load_summary_inputs


def load(tmp_path, client, fy=None):
    return load_summary_inputs("Test Company", fy, raw_dir=tmp_path / "raw", cache_dir=tmp_path / "cache", client=client,
                               progress=lambda message: None)


def test_without_a_year_the_latest_filing_is_found_by_itself_and_last_years_filing_is_loaded_too(tmp_path):
    client = FakeNse([2021, 2022, 2023])
    inputs = load(tmp_path, client)
    assert inputs.company.symbol == "TESTCO"
    assert (inputs.latest.fy, inputs.previous.fy, inputs.previous_note) == ("2023-24", "2022-23", "")
    assert len(client.downloads) == 2                                 # only these two years, not the whole history


def test_a_named_year_is_used_instead_of_the_newest(tmp_path):
    inputs = load(tmp_path, FakeNse([2021, 2022, 2023]), fy="FY2022-23")
    assert (inputs.latest.fy, inputs.previous.fy) == ("2022-23", "2021-22")


def test_a_missing_previous_filing_is_not_an_error_and_the_summary_says_why(tmp_path):
    """NSE has FY 2023-24 but not FY 2022-23: the previous-year column of the latest filing still allows the comparison."""
    inputs = load(tmp_path, FakeNse([2021, 2023]))
    assert inputs.latest.fy == "2023-24" and inputs.previous is None
    assert inputs.previous_note == "NSE has no BRSR filing of its own for FY 2022-23."


def test_the_first_brsr_year_has_no_year_before_it(tmp_path):
    inputs = load(tmp_path, FakeNse([2021]))
    assert inputs.latest.fy == "2021-22" and inputs.previous is None
    assert "BRSR reporting began with FY 2021-22, so there is no report for FY 2020-21." == inputs.previous_note


def test_a_damaged_previous_filing_is_noted_but_does_not_stop_the_summary(tmp_path):
    inputs = load(tmp_path, FakeNse([2022, 2023], files={"f2022.xml": b"junk"}))
    assert inputs.latest.fy == "2023-24" and inputs.previous is None
    assert inputs.previous_note.startswith("The FY 2022-23 filing could not be read (") and "f2022.xml" in inputs.previous_note


def test_a_damaged_latest_filing_is_an_error_because_there_is_nothing_to_summarise(tmp_path):
    with pytest.raises(UnparseableFiling) as problem:
        load(tmp_path, FakeNse([2022, 2023], files={"f2023.xml": b"junk"}))
    assert "The FY 2023-24 filing of Test Company Limited could not be used" in str(problem.value)


def test_a_year_nse_does_not_have_lists_the_years_it_does_have(tmp_path):
    with pytest.raises(NoFilingFound) as problem:
        load(tmp_path, FakeNse([2022, 2023]), fy="2025-26")
    assert problem.value.symbol == "TESTCO" and problem.value.available == ["2022-23", "2023-24"]


def test_a_bad_year_fails_before_any_request_and_an_unknown_company_is_an_error(tmp_path):
    client = FakeNse([2022])
    with pytest.raises(InvalidFiscalYear):
        load(tmp_path, client, fy="banana")
    assert client.api_calls == [] and client.downloads == []
    with pytest.raises(UnknownCompany):
        load(tmp_path, FakeNse([2022], search=[]))
