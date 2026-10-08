"""Tests for brsr_p6/views/summary_view.py: which figures make the 3 best and 3 worst, and what is honestly left out."""

from dashboard_samples import SCALE_SLIP, blank_report, put
from summary_samples import demo_report, last_years_own_report

from brsr_p6.analysis.comparison import IMPROVED, WORSE
from brsr_p6.views.dashboard_cards import build_card
from brsr_p6.views.metric_info import METRICS
from brsr_p6.views.summary_view import DEFINITION, TOP, build_summary_view


def ids(entries):
    return [e.card.id for e in entries]


# ------------------------------------------------------------------------------------------------ the ranking
def test_the_three_biggest_improvements_and_setbacks_are_picked_best_first():
    view = build_summary_view(demo_report())
    assert ids(view.best) == ["waste_total", "air_voc", "renewable_share"]
    assert ids(view.worst) == ["air_sox", "ghg_intensity", "air_nox"]               # PM ties with NOx and is fourth
    assert [e.rank for e in view.best] == [1, 2, 3] and [e.rank for e in view.worst] == [1, 2, 3]
    assert TOP == 3 and all(e.card.verdict == IMPROVED for e in view.best) and all(e.card.verdict == WORSE for e in view.worst)


def test_a_share_is_ranked_by_percentage_points_not_by_percent():
    """10 % -> 25 % is +150 % but 15 points: ranked in percent it would beat a real two-thirds fall in waste."""
    view = build_summary_view(demo_report())
    assert ids(view.best)[0] == "waste_total" and ids(view.best)[2] == "renewable_share"
    assert view.best[2].headline == "Energy from renewable sources went up from 10.0% to 25.0%."
    assert [r.change for r in view.table if r.title == "Energy from renewable sources"] == ["▲ 15.0 points"]


def test_a_per_sales_figure_is_ranked_instead_of_its_total_and_the_total_is_left_out_with_that_reason():
    view = build_summary_view(demo_report())
    in_table = [row.title for row in view.table]
    assert "Total energy used" not in in_table and "Energy for every ₹ 1 crore of sales" in in_table
    reason = next(item.reason for item in view.left_out if item.title == "Total energy used")
    assert "fairer measure" in reason and "it was 25.0% more than last year" in reason         # the total's own story is not hidden


def test_the_total_is_shown_as_context_under_its_per_sales_figure():
    view = build_summary_view(demo_report())
    ghg = next(e for e in view.worst if e.card.id == "ghg_intensity")
    energy = next(row for row in view.table if row.title == "Energy for every ₹ 1 crore of sales")
    assert energy.shown is False                                                       # fourth best: in the table only
    assert ghg.notes == [] or all("For comparison" in note for note in ghg.notes)      # no total reported here: nothing to compare


def test_the_counts_and_the_story_add_up():
    view = build_summary_view(demo_report())
    assert (view.improved, view.same_count, view.worse) == (4, 0, 4) and len(view.table) == 8
    assert "We compared 8 figures for Test Company between FY 2022-23 and FY 2023-24: 4 improved, 0 stayed about the same and 4 got worse." in view.story
    assert "Biggest improvement: Waste produced was 66.7% less than last year." in view.story
    assert "Biggest setback: SOx (sulphur oxides) was 45.7% more than last year." in view.story


def test_fewer_than_three_is_said_plainly_and_more_than_three_says_how_many_there_were():
    view = build_summary_view(demo_report())
    assert view.best_note == "These are the 3 biggest of the 4 figures that improved."
    assert view.worst_note == "These are the 3 biggest of the 4 figures that got worse."
    r = blank_report()
    put(r, "E5.voc", 10, 20, unit="tonnes")
    few = build_summary_view(r)
    assert few.best_note == "Only 1 figure improved." and few.worst_note == "Nothing got worse by more than the “about the same” margin."


def test_each_entry_says_what_changed_and_which_way_is_better():
    view = build_summary_view(demo_report())
    sox = view.worst[0]
    assert sox.headline == "SOx (sulphur oxides) was 45.7% more than last year."
    assert sox.lines == ["Last year: 46,000 tonnes. This year: 67,000 tonnes.", "Lower is better here, so this is a step backwards."]
    assert view.best[0].lines[1] == "Lower is better here, so this is an improvement."
    assert view.best[2].lines[1] == "Higher is better here, so this is an improvement."


# ------------------------------------------------------------------------------------------------ "about the same"
def test_a_change_inside_the_margin_is_not_ranked_but_listed_with_both_years():
    r = demo_report()
    put(r, "E5.nox", 10_050, 10_000, unit="tonnes")                                    # +0.5 %
    view = build_summary_view(r)
    assert "air_nox" not in ids(view.worst)
    assert any(text.startswith("NOx (nitrogen oxides): 10,000 tonnes last year, 10,050 tonnes this year.") for text in view.same)
    assert view.same_count == 1 and any(row.title == "NOx (nitrogen oxides)" and row.chip_text == "≈ About the same" for row in view.table)


def test_a_same_figure_whose_total_moved_more_carries_the_totals_story():
    r = blank_report()
    put(r, "E1.intensity", 1.001e-05, 1.0e-05, unit="GJ per ₹")
    put(r, "E1.total", 600, 400)
    view = build_summary_view(r)
    assert len(view.same) == 1 and view.same[0].endswith("For comparison, total energy used was 50.0% more than last year.")


def test_zero_in_both_years_is_left_out_and_not_called_a_comparison():
    r = blank_report()
    put(r, "E5.voc", 0, 0, unit="tonnes")
    view = build_summary_view(r)
    assert view.same_count == 0 and not any(row.title.startswith("VOC") for row in view.table)
    assert any(item.title.startswith("VOC") and "0 in both years" in item.reason for item in view.left_out)


# ------------------------------------------------------------------------------------------------ what is left out, and why
def test_a_zero_last_year_is_left_out_because_a_percentage_cannot_be_worked_out():
    r = demo_report()
    put(r, "E3.withdrawal_total", 100, 0, unit="kL")
    view = build_summary_view(r)
    reason = next(item.reason for item in view.left_out if item.title == "Water taken in")
    assert "Last year's figure was 0" in reason


def test_a_doubtful_figure_is_never_ranked_even_if_it_would_top_the_list():
    r = demo_report()
    put(r, "E5.sox", 67_000, 4_600, unit="tonnes", warnings=[SCALE_SLIP])             # +1,357 % would be first
    view = build_summary_view(r)
    assert "air_sox" not in ids(view.worst) and not any(row.title.startswith("SOx") for row in view.table)
    assert any(item.title.startswith("SOx") for item in view.left_out)


def test_a_figure_the_company_did_not_report_is_left_out_not_shown_as_zero():
    view = build_summary_view(demo_report())
    assert any(item.title == "Water taken in" for item in view.left_out)
    assert all(row.before not in ("0", "") and row.now not in ("0", "") for row in view.table)


def test_every_headline_figure_is_either_ranked_or_listed_as_left_out():
    """Waste per sales has no card at all in an edition without it, so it is not counted; everything else must appear once."""
    report = demo_report()
    view = build_summary_view(report)
    assert len(view.table) + len(view.left_out) == sum(1 for info in METRICS if info.headline and build_card(report, info) is not None)


def test_nothing_comparable_gives_an_honest_page_not_a_crash():
    view = build_summary_view(blank_report())
    assert view.best == [] and view.worst == [] and view.table == [] and view.left_out
    assert view.story.startswith("None of Test Company's figures can be compared between FY 2022-23 and FY 2023-24")
    assert view.best_note == "Nothing improved by more than the “about the same” margin."


# ------------------------------------------------------------------------------------------------ the definition of "better"
def test_the_definition_of_better_is_stated_with_the_real_margins():
    text = " ".join(build_summary_view(demo_report()).definition)
    for needle in ("own figures for last year", "Lower is better", "Higher is better", "smaller than 1%", "0.5 of a percentage point",
                   "percentage points", "instead of the total", "same filing"):
        assert needle in text, needle
    assert len(DEFINITION) == 6


# ------------------------------------------------------------------------------------------------ last year's own filing
def test_a_figure_last_year_filed_differently_is_flagged_as_restated():
    view = build_summary_view(demo_report(), last_years_own_report(40_000))
    sox = view.worst[0]
    assert sox.notes == ["Last year's own report gave 40,000 tonnes for this; this year's filing restates it as 46,000 tonnes. "
                         "The comparison uses the newer figure."]
    assert "restated since" in view.source_note and "SOx (sulphur oxides)" in view.source_note


def test_a_consistent_last_year_report_says_nothing_was_restated():
    view = build_summary_view(demo_report(), last_years_own_report(46_000))
    assert all(not any("restates" in note for note in e.notes) for e in view.best + view.worst)
    assert view.source_note.endswith("Last year's own report was also checked: none of the figures shown was restated.")


def test_without_last_years_own_report_the_note_says_why_and_the_comparison_still_works():
    view = build_summary_view(demo_report(), None, "NSE has no BRSR filing of its own for FY 2022-23.")
    assert ids(view.worst) == ["air_sox", "ghg_intensity", "air_nox"]                  # the previous-year column is enough
    assert "previous-year column of the FY 2023-24 filing" in view.source_note
    assert "NSE has no BRSR filing of its own for FY 2022-23." in view.source_note
    assert view.source_note.endswith("That column is the company's own figure for last year.")
