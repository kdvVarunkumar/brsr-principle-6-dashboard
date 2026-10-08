"""Tests for brsr_p6/views/compare_view.py: two companies, one year, compared FAIRLY (totals shown but never ranked)."""

from dashboard_samples import NO_UNIT, SCALE_SLIP, blank_report, put

from brsr_p6.views.compare_view import DEFINITION, build_compare_view

COARSE = ("The FY 2023-24 figure was filed as 0.0000000004, which has only one digit of precision. It is rounded too coarsely to compare "
          "with another year: the real figure could be much higher or lower.")


def company(name, symbol, boundary="Standalone basis"):
    report = blank_report(name)
    report.symbol, report.boundary, report.source_file = symbol, boundary, f"{symbol}.xml"
    return report


def pair():
    return company("Alpha Steel Limited", "ALPHA"), company("Beta Software Limited", "BETA")


def rows(view):
    return {row.title: row for topic in view.topics for row in topic.rows}


# ------------------------------------------------------------------------------------------------ fairness: totals vs per-sales figures
def test_a_total_is_shown_but_never_ranked_while_the_per_sales_figure_gets_the_verdict():
    a, b = pair()
    put(a, "E1.total", 1_000_000, 0)
    put(b, "E1.total", 10_000, 0)
    put(a, "E1.intensity", 3e-07, None, unit="GJ per ₹")
    put(b, "E1.intensity", 1e-07, None, unit="GJ per ₹")
    found = rows(build_compare_view(a, b))
    total, per_sales = found["Total energy used"], found["Energy for every ₹ 1 crore of sales"]
    assert (total.fair, total.result.winner, total.result.chip_text) == (False, "", "Depends on size")
    assert total.result.detail == "Alpha Steel's figure is 100 times Beta Software's"
    assert (per_sales.fair, per_sales.result.winner, per_sales.result.chip_text) == (True, "b", "✔ Beta Software is lower")
    assert per_sales.result.detail == "Alpha Steel's figure is 3 times Beta Software's"        # "3 times", not "200% higher", for a big gap


def test_a_share_is_compared_in_percentage_points_and_higher_is_better():
    a, b = pair()
    for report, recovered, disposed in ((a, 90, 10), (b, 50, 50)):
        put(report, "E8.recovered_total", recovered, 0, unit="tonnes")
        put(report, "E8.disposed_total", disposed, 0, unit="tonnes")
    row = rows(build_compare_view(a, b))["Waste recycled or reused"]
    assert (row.a.text, row.b.text, row.a.unit) == ("90.0", "50.0", "% of waste handled")
    assert (row.result.winner, row.result.chip_text) == ("a", "✔ Alpha Steel is higher")
    assert row.result.detail.startswith("Alpha Steel is 40") and "percentage points above Beta Software" in row.result.detail


def test_figures_within_the_margin_are_about_the_same():
    a, b = pair()
    put(a, "E3.intensity", 1.000e-06, None, unit="kL per ₹")
    put(b, "E3.intensity", 1.005e-06, None, unit="kL per ₹")
    result = rows(build_compare_view(a, b))["Water for every ₹ 1 crore of sales"].result
    assert (result.winner, result.chip_text) == ("same", "≈ About the same")


# ------------------------------------------------------------------------------------------------ one company did not report
def test_a_figure_one_company_did_not_report_is_said_so_never_shown_as_zero_and_not_compared():
    a, b = pair()
    put(a, "E5.nox", 100, 0, unit="tonnes")
    row = rows(build_compare_view(a, b))["NOx (nitrogen oxides)"]
    assert (row.b.text, row.b.css) == ("Not reported", "missing") and row.a.text == "100"
    assert (row.result.chip_text, row.result.detail) == ("? Not compared", "Beta Software did not report this.")


def test_a_per_sales_figure_one_company_did_not_report_says_who():
    a, b = pair()
    put(b, "E3.intensity", 1e-06, None, unit="kL per ₹")
    result = rows(build_compare_view(a, b))["Water for every ₹ 1 crore of sales"].result
    assert (result.chip_text, result.detail, result.winner) == ("? Can’t compare", "Alpha Steel did not report this.", "")
    assert rows(build_compare_view(*pair()))["Water for every ₹ 1 crore of sales"].result.detail == "Neither company reported this."


# ------------------------------------------------------------------------------------------------ units
def test_different_units_are_not_compared_and_the_units_are_named():
    a, b = pair()
    put(a, "E1.total", 1000, 0, unit="GJ")
    put(b, "E1.total", 500, 0, unit="(unit not stated)", warnings=[NO_UNIT])
    put(a, "E1.intensity", 1e-07, None, unit="GJ per ₹")
    put(b, "E1.intensity", 1e-07, None, unit="(unit not stated)", warnings=[NO_UNIT])
    found = rows(build_compare_view(a, b))
    assert "state different units (GJ and (unit not stated))" in found["Total energy used"].result.detail
    assert found["Energy for every ₹ 1 crore of sales"].result.chip_text == "? Can’t compare"
    assert "different units" in found["Energy for every ₹ 1 crore of sales"].result.detail


def test_both_numbers_of_a_row_share_one_scale_so_they_can_be_read_across():
    a, b = pair()
    put(a, "E1.total", 623_812_739, 0)
    put(b, "E1.total", 12_000_000, 0)
    row = rows(build_compare_view(a, b))["Total energy used"]
    assert (row.a.text, row.b.text, row.a.unit, row.b.unit) == ("62.38", "1.2", "crore GJ", "crore GJ")


def test_a_real_figure_is_never_shown_as_zero_because_of_a_shared_scale():
    """18,782,249 tonnes next to 7,932 tonnes: '1.88 crore' beside '0 crore' would hide the small one, so full numbers are used."""
    a, b = pair()
    put(a, "E8.total", 18_782_249, 0, unit="tonnes")
    put(b, "E8.total", 7_932, 0, unit="tonnes")
    row = rows(build_compare_view(a, b))["Waste produced"]
    assert (row.a.text, row.b.text, row.a.unit, row.b.unit) == ("1,87,82,249", "7,932", "tonnes", "tonnes")


# ------------------------------------------------------------------------------------------------ doubtful and coarse figures
def test_a_doubtful_figure_is_shown_as_filed_with_its_note_and_not_compared():
    a, b = pair()
    for report in (a, b):
        put(report, "E6.scope1", 64, 0, unit="tCO2e", warnings=[SCALE_SLIP] if report is a else ())
        put(report, "E6.scope2", 5, 0, unit="tCO2e", warnings=[SCALE_SLIP] if report is a else ())
    view = build_compare_view(a, b)
    row = rows(view)["Greenhouse gases released (Scope 1 + 2)"]
    assert (row.a.css, row.a.warned, row.b.css) == ("doubtful", True, "") and row.result.detail == "Not compared: a figure looks doubtful."
    assert view.notes_a == [("Greenhouse gases released (Scope 1 + 2)", SCALE_SLIP)] and view.notes_b == []


def test_an_intensity_rounded_to_one_digit_is_not_compared_with_another_company():
    a, b = pair()
    put(a, "E3.intensity", 4e-10, None, unit="kL per ₹", warnings=[COARSE])
    put(b, "E3.intensity", 2e-10, None, unit="kL per ₹")
    result = rows(build_compare_view(a, b))["Water for every ₹ 1 crore of sales"].result
    assert result.chip_text == "? Can’t compare" and result.detail == "Filed with one digit of precision, so too coarse to compare with another company."


# ------------------------------------------------------------------------------------------------ the page's words
def test_the_scoreboard_counts_only_the_fair_measures_and_the_story_says_so():
    a, b = pair()
    put(a, "E1.total", 1_000_000, 0)
    put(b, "E1.total", 10_000, 0)                                          # a total: never counted
    put(a, "E1.intensity", 3e-07, None, unit="GJ per ₹")
    put(b, "E1.intensity", 1e-07, None, unit="GJ per ₹")
    view = build_compare_view(a, b)
    assert (view.a_better, view.b_better, view.same, view.unsure) == (0, 1, 0, len([r for t in view.topics for r in t.rows if r.fair]) - 1)
    assert view.story.startswith("We compared Alpha Steel and Beta Software for FY 2023-24 on ") and view.story.endswith("Totals are shown for size but not ranked.")
    assert "Beta Software is better on 1" in view.story


def test_nothing_comparable_gives_an_honest_story():
    view = build_compare_view(*pair())
    assert view.a_better == view.b_better == view.same == 0 and view.story.startswith("None of the ")


def test_a_different_reporting_basis_is_warned_about():
    a, b = company("Alpha Steel Limited", "ALPHA"), company("Beta Software Limited", "BETA", "Consolidated basis")
    note = build_compare_view(a, b).basis_note
    assert "Alpha Steel reports on a standalone basis and Beta Software on a consolidated basis" in note and "Totals are not like-for-like" in note


def test_the_same_basis_needs_no_warning_and_an_unstated_basis_is_said():
    assert build_compare_view(*pair()).basis_note == ""
    unstated = company("Beta Software Limited", "BETA", "Not stated in the filing")
    assert "Beta Software does not state whether its figures are standalone or consolidated" in build_compare_view(company("Alpha Steel Limited", "ALPHA"), unstated).basis_note


def test_the_filing_facts_of_both_companies_are_on_the_page():
    a, b = pair()
    a.source_url, a.submission_date = "https://nse.example/alpha.xml", "03-Jun-2026"
    view = build_compare_view(a, b)
    assert (view.a.short, view.a.symbol, view.a.filed, view.a.source_url) == ("Alpha Steel", "ALPHA", "03-Jun-2026", "https://nse.example/alpha.xml")
    assert view.b.filed == "date not available" and view.fy == "2023-24"


def test_an_item_neither_filings_edition_has_is_left_out_but_one_that_either_has_is_kept():
    a, b = pair()
    assert "Waste for every ₹ 1 crore of sales" not in rows(build_compare_view(a, b))
    put(a, "X.waste_rupee", 1e-08, None, unit="tonnes per ₹", extra=True)
    assert "Waste for every ₹ 1 crore of sales" in rows(build_compare_view(a, b))


def test_every_rule_of_fairness_is_stated_in_words():
    text = " ".join(DEFINITION)
    for needle in ("same financial year", "depend on how big", "not ranked", "lower for energy", "one standard unit", "never as 0", "benchmark"):
        assert needle in text, needle
