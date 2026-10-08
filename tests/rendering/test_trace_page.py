"""Tests for the trace as it appears on the page: the NSE link, the hover text, the cards' Fine print and "Where every number comes from"."""

from dashboard_samples import blank_report
from html_checks import assert_well_formed
from summary_samples import demo_report

from brsr_p6.core.models import Cell, Origin, Status
from brsr_p6.rendering.render import render_page, render_summary_page

CURRENT, PREVIOUS = "2024-03-31", "2023-03-31"
URL = "https://nsearchives.nseindia.com/corporate/xbrl/f.xml"
TOTAL = "TotalEnergyConsumedFromRenewableAndNonRenewableSources"


def traced_report(source_url=URL, pdf_url="https://nsearchives.nseindia.com/corporate/f.pdf"):
    report = blank_report()
    report.source_file, report.source_url, report.pdf_url = "f.xml", source_url, pdf_url
    metric = report.metrics["E1.total"]
    metric.current = Cell(5000, "GJ", Status.REPORTED, "5000 Gigajoule", origin=[Origin(TOTAL, "5000", "Gigajoule", CURRENT)])
    metric.previous = Cell(4000, "GJ", Status.REPORTED, "4000 Gigajoule", origin=[Origin(TOTAL, "4000", "Gigajoule", PREVIOUS)])
    return report


# ------------------------------------------------------------------------------------------------ the link to the filing
def test_the_page_links_to_the_filing_on_nse_in_the_header_and_in_the_trace_section():
    html = render_page(traced_report())
    assert_well_formed(html)
    assert html.count(f'<a href="{URL}" rel="noopener noreferrer" target="_blank">f.xml</a>') == 2        # the header and the trace section
    assert 'href="https://nsearchives.nseindia.com/corporate/f.pdf"' in html


def test_without_a_link_the_file_name_is_still_named_and_nothing_is_made_clickable():
    html = render_page(traced_report(source_url="", pdf_url=""))
    assert "href=\"https://nsearchives" not in html and "(no link available)" in html and "f.xml" in html


def test_a_link_that_is_not_https_is_never_made_clickable():
    html = render_page(traced_report(source_url="javascript:alert(1)", pdf_url="http://insecure.example/f.pdf"))
    assert "javascript:" not in html and "insecure.example" not in html


# ------------------------------------------------------------------------------------------------ the three places a trace shows
def test_a_number_in_the_sebi_tab_shows_its_element_on_hover():
    html = render_page(traced_report())
    assert f'title="From the filing: {TOTAL} = 5000 Gigajoule"' in html


def test_a_dashboard_cards_fine_print_names_the_element_for_both_years():
    html = render_page(traced_report())
    assert "Where it is in the filing:" in html
    assert f"FY 2023-24: {TOTAL} = 5000 Gigajoule" in html and f"FY 2022-23: {TOTAL} = 4000 Gigajoule" in html


def test_the_trace_section_lists_the_row_with_its_status_and_the_text_as_filed():
    html = render_page(traced_report())
    section = html[html.index('id="trace"'):]
    assert "Where every number comes from" in section and 'id="trace-E1"' in section
    assert "5,000 GJ" in section and "Reported by the company" in section and f"{TOTAL} = 5000 Gigajoule" in section


def test_a_row_the_filing_does_not_have_says_what_was_looked_for_and_never_shows_a_value():
    report = traced_report()
    report.metrics["E5.sox"].current = Cell(note="Not found in the filing.", looked_for=["SOx"])
    html = render_page(report)
    assert "Not found in the filing. Elements looked for: SOx." in html[html.index('id="trace"'):]


def test_the_year_on_year_summary_cards_carry_the_trace_too():
    report = demo_report()                                  # SOx rose from 46,000 to 67,000 tonnes: it is the biggest setback
    sox = report.metrics["E5.sox"]
    sox.current.origin = [Origin("SOx", "67000", "Tonne", CURRENT)]
    sox.previous.origin = [Origin("SOx", "46000", "Tonne", PREVIOUS)]
    html = render_summary_page(report)
    assert_well_formed(html)
    assert "FY 2023-24: SOx = 67000 Tonne" in html and "FY 2022-23: SOx = 46000 Tonne" in html


# ------------------------------------------------------------------------------------------------ text from a filing cannot break the page
def test_filing_text_in_the_trace_cannot_inject_html():
    evil = "<script>alert(1)</script>"
    report = traced_report()
    report.metrics["E1.total"].current.origin = [Origin(evil, evil, evil, CURRENT)]
    report.metrics["E5.nox"].current = Cell(note=evil, looked_for=[evil])
    html = render_page(report)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert_well_formed(html)
