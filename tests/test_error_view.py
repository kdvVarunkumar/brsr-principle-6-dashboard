"""Tests for brsr_p6/error_view.py and the error page (templates/error.html)."""

import pytest
from html_checks import assert_well_formed

from brsr_p6.company_lookup import Company
from brsr_p6.error_view import ERROR_INFO, build_error_view
from brsr_p6.errors import (AmbiguousCompany, BrsrError, FileNotAvailable, InvalidFiscalYear, NoFilingFound, NSEUnavailable,
                            UnknownCompany, UnparseableFiling, UnsupportedYear)
from brsr_p6.render import error_page_path, render_error_page, write_error_page

ALL_ERRORS = [InvalidFiscalYear, UnsupportedYear, UnknownCompany, NoFilingFound, NSEUnavailable, UnparseableFiling, FileNotAvailable]


@pytest.mark.parametrize("error_class", ALL_ERRORS)
def test_every_kind_of_error_has_its_own_title_message_and_hints(error_class):
    view = build_error_view(error_class("The specific sentence."), "Some Company", "2023-24")
    assert view.message == "The specific sentence."                    # exactly what the program raised
    assert view.title and view.kind and view.hints and view.technical is False
    assert view.title != ERROR_INFO[BrsrError].title                   # none of them falls back to the generic text


def test_the_error_table_covers_every_error_class_in_errors_py():
    import brsr_p6.errors as errors
    classes = {c for c in vars(errors).values() if isinstance(c, type) and issubclass(c, BrsrError)}
    assert classes <= set(ERROR_INFO)


def test_a_new_kind_of_error_still_gets_a_sensible_page():
    class SomethingNew(BrsrError):
        pass

    view = build_error_view(SomethingNew("A brand new problem."), "X", "2023-24")
    assert view.title == "We could not make this report" and view.message == "A brand new problem."


def test_what_the_user_typed_is_shown():
    view = build_error_view(UnknownCompany("No match."), "Xyzzy Quux", "2023-24")
    assert view.asked == "Company: Xyzzy Quux · Financial year: 2023-24"
    assert build_error_view(UnknownCompany("No match."), "", "").asked == ""


def test_an_ambiguous_company_lists_each_candidate_with_a_command_ready_to_run():
    error = AmbiguousCompany("'Tata' matches several companies.", [Company("TATASTEEL", "Tata Steel Limited"), Company("TCS", "Tata Consultancy Services Limited")])
    view = build_error_view(error, "Tata", "2024-25")
    assert [o.label for o in view.options] == ["Tata Steel Limited (TATASTEEL)", "Tata Consultancy Services Limited (TCS)"]
    assert view.options[0].command == 'python main.py --company "TATASTEEL" --fy 2024-25'
    assert view.options_title.startswith("Companies that match")


def test_suggested_commands_always_use_a_real_year_even_when_the_typed_one_was_garbage():
    error = AmbiguousCompany("Several.", [Company("TCS", "TCS")])
    assert build_error_view(error, "Tata", "banana").options[0].command == 'python main.py --company "TCS" --fy 2023-24'


def test_a_missing_year_offers_the_years_nse_does_have():
    error = NoFilingFound("NSE has no BRSR filing for Tata Steel Limited for FY 2021-22.", symbol="TATASTEEL", available=["2022-23", "2023-24"])
    view = build_error_view(error, "Tata Steel", "2021-22")
    assert [(o.label, o.command) for o in view.options] == [
        ("FY 2022-23", 'python main.py --company "TATASTEEL" --fy 2022-23'), ("FY 2023-24", 'python main.py --company "TATASTEEL" --fy 2023-24')]


def test_a_company_with_no_filings_at_all_gets_hints_but_no_year_list():
    view = build_error_view(NoFilingFound("NSE lists no BRSR filings for Sakuma.", symbol="SAKUMA"), "Sakuma", "2023-24")
    assert view.options == [] and any("top 1,000" in hint for hint in view.hints)


def test_an_unreachable_nse_says_what_still_works():
    view = build_error_view(NSEUnavailable("Could not get the page."), "Reliance", "2023-24")
    assert any("internet" in hint for hint in view.hints) and any("downloaded before" in hint for hint in view.hints)


def test_a_damaged_file_says_nothing_is_guessed():
    view = build_error_view(UnparseableFiling("x.xml is not valid XML (line 3)."), "Infosys", "2021-22")
    assert any("rather than guess" in hint for hint in view.hints) and view.kind == "Filing could not be read"


def test_an_unexpected_bug_is_labelled_as_one_and_names_the_exception():
    view = build_error_view(KeyError("E1.total"), "Infosys", "2021-22")
    assert view.technical is True and view.title == "Something unexpected went wrong"
    assert view.message == "KeyError: 'E1.total'" and any("--debug" in hint for hint in view.hints)


# ------------------------------------------------------------------------------------------------ the page
def test_the_error_page_is_well_formed_and_says_it_is_not_a_report():
    html = render_error_page(build_error_view(UnknownCompany("No NSE-listed company matches 'Xyzzy'."), "Xyzzy", "2023-24"))
    assert_well_formed(html)
    assert "We could not make this report" in html and "We could not find that company on NSE" in html
    assert 'role="alert"' in html and "No numbers were guessed" in html
    assert 'id="view-dashboard"' not in html and ">SEBI-format report<" not in html      # no report tabs on an error page


def test_the_page_prints_the_commands_to_copy():
    error = NoFilingFound("No filing.", symbol="TATASTEEL", available=["2022-23"])
    html = render_error_page(build_error_view(error, "Tata Steel", "2021-22"))
    assert "Financial years NSE has for this company" in html and "--fy 2022-23" in html and "<code>" in html


def test_text_typed_by_the_user_cannot_inject_html_into_the_error_page():
    evil = "<script>alert(1)</script>"
    html = render_error_page(build_error_view(UnknownCompany(f"No match for '{evil}'."), evil, evil))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_error_pages_have_their_own_file_names_so_they_never_overwrite_a_report(tmp_path):
    path = error_page_path("Tata Steel", "2021-22", tmp_path)
    assert path.name == "error_Tata_Steel_2021-22.html"
    assert error_page_path("M&M", "FY2023/24", tmp_path).name == "error_M_M_FY2023_24.html"
    assert error_page_path("", "", tmp_path).name == "error_unknown_year.html"
    assert len(error_page_path("x" * 300, "2023-24", tmp_path).name) < 80


def test_write_error_page_creates_the_folder_and_the_file(tmp_path):
    view = build_error_view(UnknownCompany("No match."), "Xyzzy", "2023-24")
    path = write_error_page(view, "Xyzzy", "2023-24", tmp_path / "new_folder")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("<!doctype html>")


# ------------------------------------------------------------------------------------------------ trend commands (trends.py)
def test_an_invalid_year_range_has_its_own_page():
    from brsr_p6.errors import InvalidYearRange
    view = build_error_view(InvalidYearRange("The start year FY 2024-25 is after the end year FY 2022-23."), "Reliance", "2024-25 to 2022-23", trends=True)
    assert view.title == "That range of years cannot be used" and any("--from 2021-22 --to 2025-26" in h for h in view.hints)


def test_suggested_commands_use_trends_py_when_a_trend_request_failed():
    ambiguous = AmbiguousCompany("Several.", [Company("TCS", "Tata Consultancy Services Limited")])
    assert build_error_view(ambiguous, "Tata", "2021-22 to 2025-26", trends=True).options[0].command == 'python trends.py --company "TCS"'
    none_in_range = NoFilingFound("No filing in range.", symbol="TATASTEEL", available=["2022-23", "2023-24", "2025-26"])
    option = build_error_view(none_in_range, "Tata Steel", "2018-19 to 2019-20", trends=True).options[0]
    assert option.label == "FY 2022-23 to FY 2025-26"
    assert option.command == 'python trends.py --company "TATASTEEL" --from 2022-23 --to 2025-26'
    # ... and main.py as before for a one-year request
    assert build_error_view(none_in_range, "Tata Steel", "2021-22").options[0].command == 'python main.py --company "TATASTEEL" --fy 2022-23'
