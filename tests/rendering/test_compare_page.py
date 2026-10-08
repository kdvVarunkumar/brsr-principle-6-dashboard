"""Tests for the comparison page (templates/compare.html): its parts, its escaping, and its file name."""

import re

from dashboard_samples import SCALE_SLIP, blank_report, put
from html_checks import assert_well_formed

from brsr_p6.rendering.render import compare_page_path, render_compare_page, write_compare_page


def company(name, symbol, boundary="Standalone basis"):
    report = blank_report(name)
    report.symbol, report.boundary, report.source_file = symbol, boundary, f"{symbol}.xml"
    return report


def pair():
    a, b = company("Alpha Steel Limited", "ALPHA"), company("Beta Software Limited", "BETA")
    put(a, "E1.total", 1_000_000, 0)
    put(b, "E1.total", 10_000, 0)
    put(a, "E1.intensity", 3e-07, None, unit="GJ per ₹")
    put(b, "E1.intensity", 1e-07, None, unit="GJ per ₹")
    return a, b


def test_the_page_is_well_formed_and_names_both_companies_and_the_year():
    html = render_compare_page(*pair())
    assert_well_formed(html)
    assert "<title>Alpha Steel Limited vs Beta Software Limited: BRSR Principle 6 compared, FY 2023-24</title>" in html
    assert "Alpha Steel <span class=\"vs\">vs</span> Beta Software" in html and "Financial year 2023-24, the same year for both companies" in html


def test_a_reader_gets_the_answer_first_then_the_filings_then_the_rules_then_the_tables():
    html = render_compare_page(*pair())
    positions = [html.index(part) for part in ("Which company does better", "The two filings", "How we compare fairly", 'class="cmptable"')]
    assert positions == sorted(positions)


def test_a_total_row_says_it_is_not_ranked_and_a_fair_row_names_the_winner():
    html = render_compare_page(*pair())
    total = re.search(r'<tr class="size">.*?Total energy used.*?</tr>', html, re.S).group(0)
    assert "a total: shown for size, not ranked" in total and "Depends on size" in total and 'class="fig  win"' not in total and " win" not in total
    fair = re.search(r'<tr class="fair">.*?Energy for every ₹ 1 crore of sales.*?</tr>', html, re.S).group(0)
    assert "✔ Beta Software is lower" in fair and fair.count(" win") == 1


def test_a_figure_that_was_not_reported_says_so_in_words():
    a, b = pair()
    html = render_compare_page(a, b)
    assert html.count("Not reported") > 10 and 'class="fig missing"' in html


def test_a_doubtful_figure_is_marked_and_its_note_is_printed_under_the_company_it_belongs_to():
    a, b = pair()
    put(a, "E6.scope1", 64, 0, unit="tCO2e", warnings=[SCALE_SLIP])
    put(a, "E6.scope2", 5, 0, unit="tCO2e", warnings=[SCALE_SLIP])
    html = render_compare_page(a, b)
    assert 'class="warn"' in html and "Notes on the figures" in html
    notes = html[html.index("Notes on the figures"):]
    assert notes.index("Alpha Steel") < notes.index("1,000,000 times too small") and "Beta Software</h3>" not in notes


def test_a_page_without_any_note_has_no_notes_section():
    assert "Notes on the figures" not in render_compare_page(*pair())


def test_a_different_reporting_basis_is_flagged_near_the_top():
    a, b = pair()
    b.boundary = "Consolidated basis"
    html = render_compare_page(a, b)
    assert "Different reporting basis:" in html and html.index("Different reporting basis:") < html.index("How we compare fairly")
    assert "Different reporting basis:" not in render_compare_page(*pair())


def test_only_a_real_https_source_address_becomes_a_link():
    a, b = pair()
    a.source_url, b.source_url = "https://nse.example/alpha.xml", "javascript:alert(1)"
    html = render_compare_page(a, b)
    assert 'href="https://nse.example/alpha.xml" rel="noopener noreferrer"' in html
    assert "javascript:" not in html.replace("\n", " ").split("href=")[-1] and 'href="javascript' not in html


def test_text_from_a_filing_can_never_inject_html():
    evil = "<script>alert(1)</script>"
    a, b = pair()
    a.company_name = f"Alpha {evil} Limited"
    a.boundary = evil
    html = render_compare_page(a, b)
    assert evil not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_the_page_needs_no_script_of_its_own():
    assert "<script" not in render_compare_page(*pair())


def test_the_file_is_named_after_both_symbols_and_the_year_and_cannot_overwrite_a_report(tmp_path):
    a, b = pair()
    assert compare_page_path(a, b, tmp_path).name == "ALPHA_vs_BETA_2023-24.html"
    a.symbol = "M&M"
    assert compare_page_path(a, b, tmp_path).name == "M_M_vs_BETA_2023-24.html"
    path = write_compare_page(a, b, tmp_path / "new_folder")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("<!doctype html>")
