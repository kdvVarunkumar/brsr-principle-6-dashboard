"""Tests for brsr_p6/render.py: the finished HTML page."""

from pathlib import Path

import pytest
from html_checks import assert_well_formed
from markupsafe import escape
from xbrl_samples import both_years, fact, write_xbrl

from brsr_p6.extractor import build_report
from brsr_p6.render import render_page, write_page
from brsr_p6.sebi_template import QUESTIONS
from brsr_p6.xbrl_reader import read_filing


def report_for(tmp_path, facts=""):
    return build_report(read_filing(write_xbrl(tmp_path, facts)), "Test Company Limited", "TEST", "2023-24")


def test_page_is_well_formed_html(tmp_path):
    assert_well_formed(render_page(report_for(tmp_path)))


def test_every_official_question_and_row_label_appears_in_sebi_order(tmp_path):
    """The Phase 5 promise: put the page next to SEBI's form and every question and row is there, in the same order."""
    html = render_page(report_for(tmp_path))
    cursor = 0
    for q in QUESTIONS:
        position = html.find(str(escape(q.text)), cursor)
        assert position >= cursor, f"question {q.id} is missing or out of order"
        cursor = position
        if q.kind == "list":
            for column in q.columns:
                assert html.find(str(escape(column)), cursor) >= 0, f"{q.id}: column '{column}' missing"
        for row in q.rows:
            if q.kind == "facilities":
                continue  # facility tables only appear when the company lists a facility
            position = html.find(str(escape(row.label)), cursor)
            assert position >= cursor, f"{q.id}: row '{row.label}' is missing or out of order"
            cursor = position


def test_empty_cells_say_not_reported(tmp_path):
    html = render_page(report_for(tmp_path))
    assert html.count("Not reported") > 50          # a filing with almost nothing in it: every row says so


def test_the_page_has_both_tabs_and_names_the_company(tmp_path):
    html = render_page(report_for(tmp_path))
    assert 'id="view-sebi"' in html and 'id="view-dashboard"' in html
    assert "Test Company Limited" in html and "FY 2023-24" in html and "FY 2022-23" in html


def test_the_dashboard_is_the_first_and_default_tab(tmp_path):
    html = render_page(report_for(tmp_path))
    assert html.index('id="view-dashboard"') < html.index('id="view-sebi"')
    assert 'id="view-dashboard" checked' in html and 'id="view-sebi" checked' not in html
    assert html.index('class="panel panel-dashboard"') < html.index('class="panel panel-sebi"')


def test_the_dashboard_has_every_section_a_reader_needs(tmp_path):
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 4000, "Gigajoule")
             + both_years("NOx", 27, 24, "Kilotonne"))
    html = render_page(report_for(tmp_path, facts))
    for text in ("How is Test Company doing on the environment?", "Energy", "Climate: greenhouse gases", "Water", "Air quality", "Waste",
                 "Nature and safeguards", "Can I trust these numbers?", "Plain-English glossary", "Lower is better",
                 "What it is:", "Why it matters:", "Fine print", "only compares the company with"):
        assert text in html, text
    assert '<span class="v num">27,000</span><span class="u">tonnes</span>' in html        # 27 kilotonnes became 27,000 tonnes ...
    assert "▲ 12.5% higher than last year" in html and "✖ Got worse" in html            # ... and 27 against 24 is a real rise


def test_the_dashboard_never_shows_a_missing_figure_as_zero(tmp_path):
    html = render_page(report_for(tmp_path))                  # a filing with nothing in it
    assert "Not reported" in html and "? Can’t compare" in html
    assert 'class="v num">0<' not in html                     # no card shows a bare 0 for something that was never filed


def test_the_dashboard_cannot_be_used_to_inject_html_either(tmp_path):
    evil = "&lt;script&gt;alert(1)&lt;/script&gt;"
    facts = fact("DetailsOfProjectRelatedToReducingGreenHouseGasEmissionExplanatoryTextBlock", evil)
    html = render_page(report_for(tmp_path, facts))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_marks_and_footnotes_appear(tmp_path):
    facts = (both_years("TotalElectricityConsumptionFromRenewableSources", 100, 80, "Gigajoule")
             + both_years("TotalElectricityConsumptionFromNonRenewableSources", 900, 700, "Gigajoule")
             + both_years("PersistentOrganicPollutants", 0, 0, "Kilotonne"))
    html = render_page(report_for(tmp_path, facts))
    assert "tag-calculated" in html and ">calc.<" in html          # calculated electricity is labelled
    assert "tag-converted" in html                                  # kilotonnes were converted
    assert "⚠ Doubtful:" in html                                    # the zero pollutant got a caveat
    assert 'id="fn-E5-' in html                                     # footnotes are linkable


def test_text_from_a_filing_can_never_inject_html(tmp_path):
    evil = "&lt;script&gt;alert(1)&lt;/script&gt;"       # as stored inside the XML file
    facts = fact("DetailsOfProjectRelatedToReducingGreenHouseGasEmissionExplanatoryTextBlock", evil)
    html = render_page(report_for(tmp_path, facts))
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_boundary_and_edition_are_shown(tmp_path):
    html = render_page(report_for(tmp_path, fact("ReportingBoundary", "Consolidated basis")))
    assert "Consolidated basis" in html and "together with its subsidiaries" in html
    assert "2024-04-30" in html


def test_write_page_creates_the_file(tmp_path):
    path = write_page(report_for(tmp_path), output_dir=tmp_path / "out")
    assert path.name == "TEST_2023-24.html" and path.read_text(encoding="utf-8").startswith("<!doctype html>")


# ----------------------------------------------------------------------------- real filings (skipped when the data is absent)
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def real_page(symbol, fy):
    files = sorted((RAW / symbol / fy).glob("*.xml"))
    if not files:
        pytest.skip(f"{symbol} FY {fy} is not downloaded")
    return render_page(build_report(read_filing(files[0]), symbol, symbol, fy))


def test_real_tata_steel_page():
    html = real_page("TATASTEEL", "2025-26")
    assert_well_formed(html)
    assert "2,47,98,900.25" in html                      # electricity (A), Indian digit grouping
    assert "Standalone basis" in html and "tag-calculated" in html
    assert "typed in millions" in html                   # the scale warning on Scope 1 + 2
    assert "Joda East" in html                           # a row of the sensitive-areas table
    assert "Facility 1." in html                         # the water-stress block


def test_every_downloaded_filing_renders_to_well_formed_html():
    files = sorted(RAW.glob("*/*/*.xml"))
    if not files:
        pytest.skip("no filings downloaded")
    for xml in files:
        symbol, fy = xml.parts[-3], xml.parts[-2]
        assert_well_formed(render_page(build_report(read_filing(xml), symbol, symbol, fy)))
