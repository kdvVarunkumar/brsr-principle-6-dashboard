"""Tests for brsr_p6/analysis/comparison.py: the better / worse / same / can't-tell rules."""

import pytest

from brsr_p6.analysis.comparison import CONTEXT, CONTEXT_ONLY, HIGHER, IMPROVED, LOWER, SAME, UNSURE, WORSE, compare, has_number, trust_of
from brsr_p6.analysis.warning_kinds import CHECK, DOUBTFUL, OK
from brsr_p6.core.models import Cell, Status

SCALE_SLIP = "Scope 1+2 emissions look about 1,000,000 times too small for this company's energy use (1.1e-07 tonnes per GJ)."
ZERO_MEANING = "A reported 0 can mean 'none', or 'not measured / not material'. The filing does not say which."


def number(value, unit="GJ", warnings=()):
    return Cell(value, unit, Status.REPORTED, warnings=list(warnings))


MISSING = Cell()


def test_lower_energy_is_an_improvement_when_lower_is_better():
    result = compare(number(46.42), number(47.36), LOWER)
    assert (result.verdict, result.arrow, result.change) == (IMPROVED, "▼", "2.0% lower than last year")


def test_higher_water_use_is_worse_when_lower_is_better():
    result = compare(number(20.41), number(20.05), LOWER)
    assert (result.verdict, result.arrow, result.change) == (WORSE, "▲", "1.8% higher than last year")


def test_higher_is_better_flips_the_verdict():
    assert compare(number(10), number(8), HIGHER).verdict == IMPROVED
    assert compare(number(8), number(10), HIGHER).verdict == WORSE


def test_within_one_percent_is_about_the_same_but_still_points_the_way():
    result = compare(number(99.3), number(100), LOWER)
    assert (result.verdict, result.arrow, result.change) == (SAME, "▼", "0.70% lower than last year")
    assert compare(number(98.9), number(100), LOWER).verdict == IMPROVED      # 1.1 % is a real change


def test_shares_are_compared_in_percentage_points():
    same = compare(number(1.471, "%"), number(1.416, "%"), HIGHER, "share")
    assert (same.verdict, same.arrow, same.change) == (SAME, "▲", "0.06 percentage points above last year")
    assert compare(number(60, "%"), number(55, "%"), HIGHER, "share").verdict == IMPROVED


def test_the_size_of_the_change_is_kept_as_a_number_for_ranking():
    """Amounts keep the change in percent, shares in percentage points: the summary page ranks by these."""
    assert compare(number(75), number(100), LOWER).amount == pytest.approx(-25.0)
    assert compare(number(25, "%"), number(10, "%"), HIGHER, "share").amount == pytest.approx(15.0)            # +150 % would be misleading
    assert compare(number(100), number(100), LOWER).amount == 0.0
    assert compare(number(0, "tonnes"), number(0, "tonnes"), LOWER).amount is None                             # 0 -> 0 has no size: not ranked
    assert compare(number(5, "tonnes"), number(0, "tonnes"), LOWER).amount is None                             # a zero base has no percentage
    assert compare(MISSING, number(3), LOWER).amount is None


def test_a_neutral_metric_shows_the_change_but_gives_no_verdict():
    assert compare(number(3.46), number(3.34), CONTEXT).verdict == CONTEXT_ONLY
    assert compare(number(3.34), number(3.34), CONTEXT).verdict == SAME


def test_zero_in_both_years_is_no_change():
    result = compare(number(0, "tonnes"), number(0, "tonnes"), LOWER)
    assert (result.verdict, result.arrow, result.change) == (SAME, "", "No change: 0 in both years")


def test_rising_from_zero_is_not_called_worse_because_last_years_zero_may_mean_not_measured():
    """HDFC Bank reports 0 water last year and 21 lakh kL this year: a false 'Got worse' would be a guess."""
    result = compare(number(5, "tonnes"), number(0, "tonnes"), LOWER)
    assert result.verdict == UNSURE and "was 0" in result.reason and result.arrow == ""


def test_falling_to_zero_is_still_compared():
    result = compare(number(0, "tonnes"), number(7_784, "tonnes"), LOWER)
    assert (result.verdict, result.change) == (IMPROVED, "100% lower than last year")


def test_a_change_that_rounds_to_nothing_is_no_change():
    assert compare(number(99.9996, "%"), number(100, "%"), HIGHER, "share").change == "No change from last year"
    result = compare(number(1_000_000.0), number(1_000_000.04), LOWER)
    assert (result.verdict, result.arrow, result.change) == (SAME, "", "No change from last year")


@pytest.mark.parametrize("current, previous, reason", [
    (MISSING, number(5), "No figure for this year."),
    (number(5), MISSING, "No figure for last year."),
    (MISSING, MISSING, "No figure for either year."),
    (number(5, "GJ"), number(5, "(unit not stated)"), "The two years use different units."),
])
def test_missing_or_mismatched_figures_are_never_compared(current, previous, reason):
    result = compare(current, previous, LOWER)
    assert result.verdict == UNSURE and result.reason == reason and result.arrow == ""


COARSE = ("Filed as 0.0000000004, which has only one digit of precision. It is rounded too coarsely to compare with another year: "
          "the real figure could be much higher or lower.")


def test_a_figure_rounded_to_one_digit_is_not_compared_and_the_reason_says_so():
    """ICICI Bank's waste intensity, 0.0000000002 -> 0.0000000004, must not be reported as 'exactly 100% more'."""
    result = compare(number(4e-10, "tonnes per ₹", [COARSE]), number(2e-10, "tonnes per ₹", [COARSE]), LOWER)
    assert result.verdict == UNSURE and result.trust == DOUBTFUL and result.amount is None
    assert result.reason == "Filed with one digit of precision, so too coarse to compare with another year."


def test_when_a_figure_has_another_doubt_too_the_general_reason_is_used():
    other = "The rows above add up to 6,958,071.00 but the filing's own total is 6,826,744.00."
    result = compare(number(4e-10, "tonnes per ₹", [COARSE, other]), number(2e-10, "tonnes per ₹"), LOWER)
    assert result.verdict == UNSURE and result.reason == "The figure looks doubtful, so we do not compare it."


def test_a_doubtful_figure_is_never_compared_even_when_both_years_look_fine():
    result = compare(number(64, "tCO2e", [SCALE_SLIP]), number(61, "tCO2e", [SCALE_SLIP]), LOWER)
    assert (result.verdict, result.trust) == (UNSURE, DOUBTFUL) and "doubtful" in result.reason


def test_a_figure_that_only_needs_a_check_is_still_compared_and_the_trust_says_so():
    result = compare(number(5, "tonnes", [ZERO_MEANING]), number(8, "tonnes"), LOWER)
    assert (result.verdict, result.trust) == (IMPROVED, CHECK)


def test_trust_and_has_number_helpers():
    assert trust_of(number(1), number(2)) == OK
    assert trust_of(number(1, warnings=[ZERO_MEANING]), number(2)) == CHECK
    assert has_number(number(0)) and not has_number(MISSING) and not has_number(Cell("Yes", "", Status.REPORTED))


# ------------------------------------------------------------------------------------------------ the words for the older year (trend page)
def test_the_older_year_can_be_called_by_its_name():
    result = compare(number(120), number(100), LOWER, earlier="FY 2023-24")
    assert (result.verdict, result.change) == (WORSE, "20.0% higher than FY 2023-24")
    assert compare(number(1.5, "%"), number(1.0, "%"), HIGHER, "share", earlier="FY 2023-24").change == "0.50 percentage points above FY 2023-24"
    assert compare(number(100), number(100), LOWER, earlier="FY 2023-24").change == "No change from FY 2023-24"


def test_the_reasons_name_the_older_year_too_and_the_default_wording_is_unchanged():
    assert compare(number(5), MISSING, LOWER, earlier="FY 2023-24").reason == "No figure for FY 2023-24."
    assert compare(number(5), number(0), LOWER, earlier="FY 2023-24").reason == "FY 2023-24's figure was 0, so a percentage change cannot be worked out."
    assert compare(number(5), number(0), LOWER).reason == "Last year's figure was 0, so a percentage change cannot be worked out."
    assert compare(number(5), MISSING, LOWER).reason == "No figure for last year."
