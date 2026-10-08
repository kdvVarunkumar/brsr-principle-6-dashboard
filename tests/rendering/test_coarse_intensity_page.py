"""The rounded-too-coarsely rule as a reader sees it, on the dashboard page and in the SEBI tab."""

from dashboard_samples import blank_report, put
from html_checks import assert_well_formed

from brsr_p6.rendering.render import render_page

COARSE = ("Filed as 0.0000000004, which has only one digit of precision. It is rounded too coarsely to compare with another year: "
          "the real figure could be much higher or lower.")


def coarse_report():
    report = blank_report("ICICI Bank Limited")
    put(report, "E8.total", 756.32, 334.61, unit="tonnes")
    put(report, "X.waste_rupee", 4e-10, 2e-10, unit="tonnes per ₹", warnings=[COARSE], extra=True)
    return report


def test_the_dashboard_card_says_too_coarse_not_doubtful_and_gives_no_percentage():
    html = render_page(coarse_report())
    assert_well_formed(html)
    assert "Too coarse to compare." in html and "Filed with one digit of precision, so too coarse to compare with another year." in html
    assert "100% higher" not in html and "100% more" not in html                          # the claim that was never true


def test_the_sebi_tab_still_shows_the_figure_as_filed_with_the_note():
    html = render_page(coarse_report())
    assert "rounded too coarsely to compare with another year" in html                    # the footnote under the table
