"""Tests for brsr_p6/workflows/compare.py: loading two companies for one year, and a comparison for every pair in a folder.  All offline."""

import pytest
from dashboard_samples import blank_report

from brsr_p6.core.errors import InvalidFiscalYear, NoFilingFound, SameCompany
from brsr_p6.workflows import compare
from brsr_p6.workflows.compare import generate_all_comparisons, generate_comparison_page, load_pair, report_keys


def report(symbol, fy="2023-24", name=None):
    made = blank_report(name or f"{symbol.title()} Limited")
    made.symbol, made.fy = symbol, fy
    return made


@pytest.fixture
def fake_loader(monkeypatch):
    """Replace the downloading loader: ask for a company, get its report, and remember what was asked (so a test can see no internet was used)."""
    asked = []

    def load_report(company, fy, progress=None):
        asked.append((company, fy))
        if company == "Nobody":
            raise NoFilingFound("NSE has no BRSR filing for Nobody Limited for FY 2023-24.", symbol="NOBODY")
        return report(company.upper().replace(" ", ""), fy), None

    monkeypatch.setattr(compare, "load_report", load_report)
    return asked


def write_report_page(folder, name):
    (folder / name).write_text("<!doctype html><title>x</title><p>x</p>", encoding="utf-8")


# ------------------------------------------------------------------------------------------------ load_pair
def test_both_companies_are_loaded_for_the_same_year(fake_loader):
    a, b = load_pair("Tata Steel", "Wipro", "FY2025-26")
    assert (a.symbol, b.symbol, a.fy, b.fy) == ("TATASTEEL", "WIPRO", "2025-26", "2025-26")
    assert fake_loader == [("Tata Steel", "2025-26"), ("Wipro", "2025-26")]


def test_the_same_company_twice_is_refused_before_any_download(fake_loader):
    with pytest.raises(SameCompany) as problem:
        load_pair("Wipro", " WIPRO ", "2025-26")
    assert "same company" in str(problem.value) and fake_loader == []


def test_two_names_for_one_company_are_caught_once_the_symbol_is_known(fake_loader):
    """'Tata Steel' and 'TATASTEEL' look different but are one company: found out after the first lookup."""
    with pytest.raises(SameCompany) as problem:
        load_pair("Tata Steel", "TATASTEEL", "2025-26")
    assert "was given twice" in str(problem.value)


def test_a_bad_year_fails_before_any_download(fake_loader):
    with pytest.raises(InvalidFiscalYear):
        load_pair("Tata Steel", "Wipro", "banana")
    assert fake_loader == []


def test_a_company_nse_has_no_filing_for_stops_the_comparison_with_that_error(fake_loader):
    with pytest.raises(NoFilingFound):
        load_pair("Wipro", "Nobody", "2023-24")


def test_generate_comparison_page_writes_one_page_named_after_both_symbols(fake_loader, tmp_path):
    page, a, b = generate_comparison_page("Tata Steel", "Wipro", "2025-26", output_dir=tmp_path)
    assert page == tmp_path / "TATASTEEL_vs_WIPRO_2025-26.html" and page.exists()
    assert "<title>Tatasteel Limited vs Wipro Limited: BRSR Principle 6 compared, FY 2025-26</title>" in page.read_text(encoding="utf-8")
    assert (a.symbol, b.symbol) == ("TATASTEEL", "WIPRO")


# ------------------------------------------------------------------------------------------------ every pair in a folder
def test_only_report_pages_are_picked_out_of_a_folder(tmp_path):
    for name in ("TATASTEEL_2025-26.html", "WIPRO_2025-26.html", "M_M_2024-25.html", "TATASTEEL_summary_2025-26.html",
                 "TATASTEEL_trend_2021-22_to_2025-26.html", "TATASTEEL_vs_WIPRO_2025-26.html", "error_Xyzzy_2023-24.html", "index.html", "notes.html"):
        write_report_page(tmp_path, name)
    assert report_keys(tmp_path) == [("M_M", "2024-25"), ("TATASTEEL", "2025-26"), ("WIPRO", "2025-26")]


def test_a_comparison_is_made_for_every_pair_with_the_same_year(tmp_path):
    for name in ("A_2023-24.html", "B_2023-24.html", "C_2023-24.html", "A_2024-25.html", "B_2024-25.html", "D_2022-23.html"):
        write_report_page(tmp_path, name)
    made = generate_all_comparisons(tmp_path, loader=lambda symbol, fy: report(symbol, fy))
    assert made == 4                                                    # three pairs in 2023-24, one in 2024-25, none in 2022-23 (D is alone)
    assert sorted(p.name for p in tmp_path.glob("*_vs_*")) == ["A_vs_B_2023-24.html", "A_vs_B_2024-25.html", "A_vs_C_2023-24.html", "B_vs_C_2023-24.html"]


def test_a_company_is_never_compared_with_itself_or_across_years(tmp_path):
    for name in ("A_2023-24.html", "A_2024-25.html"):
        write_report_page(tmp_path, name)
    assert generate_all_comparisons(tmp_path, loader=lambda symbol, fy: report(symbol, fy)) == 0
    assert not list(tmp_path.glob("*_vs_*"))


def test_a_page_whose_filing_is_not_on_disk_is_skipped_not_guessed(tmp_path):
    for name in ("A_2023-24.html", "B_2023-24.html", "C_2023-24.html"):
        write_report_page(tmp_path, name)
    loader = lambda symbol, fy: None if symbol == "C" else report(symbol, fy)
    assert generate_all_comparisons(tmp_path, loader=loader) == 1
    assert [p.name for p in tmp_path.glob("*_vs_*")] == ["A_vs_B_2023-24.html"]


def test_running_it_again_makes_the_same_pages_and_never_compares_comparisons(tmp_path):
    for name in ("A_2023-24.html", "B_2023-24.html"):
        write_report_page(tmp_path, name)
    loader = lambda symbol, fy: report(symbol, fy)
    assert generate_all_comparisons(tmp_path, loader=loader) == 1
    first = (tmp_path / "A_vs_B_2023-24.html").read_text(encoding="utf-8")
    assert generate_all_comparisons(tmp_path, loader=loader) == 1
    assert (tmp_path / "A_vs_B_2023-24.html").read_text(encoding="utf-8") == first


def test_an_empty_or_missing_folder_has_nothing_to_compare(tmp_path):
    assert generate_all_comparisons(tmp_path, loader=lambda symbol, fy: report(symbol, fy)) == 0
    assert generate_all_comparisons(tmp_path / "missing", loader=lambda symbol, fy: report(symbol, fy)) == 0
