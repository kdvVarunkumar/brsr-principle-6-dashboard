"""Tests for brsr_p6/analysis/trend_model.py: columns, borrowed years, restatements and basis changes."""

import pytest
from dashboard_samples import blank_report, put

from brsr_p6.analysis.trend_model import (BORROWED, NONE, NOT_FILED, OWN, UNREADABLE, YearEntry, basis_changes, basis_of, build_trend,
                                          relative_difference, trend_cells)
from brsr_p6.core.models import Cell, Status

UNKNOWN_UNIT = "(unit not stated)"


def report(fy, total=None, previous=None, boundary="Standalone basis", unit="GJ"):
    r = blank_report("Test Company Limited")
    r.fy, r.boundary, r.submission_date, r.family = fy, boundary, "01-Jul-2024", "modern"
    if total is not None:
        put(r, "E1.total", total, previous, unit=unit)
    return r


def getter(report_, side):
    metric = report_.metrics["E1.total"]
    return getattr(metric, side)


def values(items):
    return [item.cell.value for item in items]


# ------------------------------------------------------------------------------------------------ columns
def test_basis_is_read_from_the_filings_own_words():
    assert basis_of("Standalone basis") == "standalone" and basis_of("Consolidated basis") == "consolidated"
    assert basis_of("Not stated in the filing") == "unknown" and basis_of("") == "unknown"


def test_each_year_with_a_filing_becomes_an_own_column_in_order():
    trend = build_trend("T", "T", [YearEntry("2022-23", report("2022-23", 10, 8)), YearEntry("2023-24", report("2023-24", 12, 10))])
    assert [(c.fy, c.source, c.side) for c in trend.columns] == [("2022-23", OWN, "current"), ("2023-24", OWN, "current")]
    assert trend.columns[0].basis == "standalone" and trend.columns[0].filed_on == "01-Jul-2024"


def test_a_year_with_no_filing_borrows_the_previous_year_column_of_the_next_filing_and_says_so():
    missing = YearEntry("2021-22", problem="NSE has no BRSR filing for this year.", kind=NOT_FILED)
    trend = build_trend("T", "T", [missing, YearEntry("2022-23", report("2022-23", 10, 8, boundary="Consolidated basis"))])
    column = trend.columns[0]
    assert (column.source, column.side, column.borrowed_from, column.kind) == (BORROWED, "previous", "2022-23", NOT_FILED)
    assert column.basis == "consolidated" and "no BRSR filing" in column.problem
    assert values(trend_cells(trend, getter)) == [8, 10]                      # last year's column of the FY 2022-23 filing, then its own


def test_a_missing_year_with_no_later_filing_is_empty_never_zero():
    trend = build_trend("T", "T", [YearEntry("2022-23", report("2022-23", 10, 8)), YearEntry("2023-24", problem="x", kind=NOT_FILED)])
    last = trend.columns[1]
    assert (last.source, last.report) == (NONE, None)
    cell = trend_cells(trend, getter)[1].cell
    assert cell.status == Status.NOT_REPORTED and cell.value is None


def test_a_year_that_could_not_be_read_keeps_its_reason_and_can_still_be_borrowed():
    broken = YearEntry("2022-23", problem="x.xml is not valid XML", kind=UNREADABLE)
    trend = build_trend("T", "T", [broken, YearEntry("2023-24", report("2023-24", 12, 10))])
    column = trend.columns[0]
    assert (column.source, column.kind, column.problem) == (BORROWED, UNREADABLE, "x.xml is not valid XML")


# ------------------------------------------------------------------------------------------------ restatements
def two_years(first, second, **kwargs):
    """FY 2022-23 filing says `first`; the FY 2023-24 filing says `second` about FY 2022-23."""
    boundary_later = kwargs.pop("boundary_later", "Standalone basis")
    entries = [YearEntry("2022-23", report("2022-23", first, None, **kwargs)),
               YearEntry("2023-24", report("2023-24", 500, second, boundary=boundary_later, **{k: v for k, v in kwargs.items() if k == "unit"}))]
    return build_trend("T", "T", entries)


def test_a_figure_the_next_filing_changes_is_flagged_as_restated_and_keeps_the_figure_as_filed():
    first = trend_cells(two_years(100.0, 140.0), getter)[0]
    assert first.cell.value == 100.0                                         # as filed in its own year
    assert (first.restated_to.value, first.restated_in, first.basis_differs) == (140.0, "2023-24", False)


def test_a_difference_smaller_than_rounding_is_not_a_restatement():
    assert trend_cells(two_years(6515.4, 6515.0), getter)[0].restated_to is None
    assert trend_cells(two_years(100.0, 100.4), getter)[0].restated_to is None        # 0.4 % is under the 0.5 % tolerance
    assert trend_cells(two_years(100.0, 100.6), getter)[0].restated_to is not None


def test_an_unchanged_figure_and_a_last_year_have_nothing_to_flag():
    items = trend_cells(two_years(100.0, 100.0), getter)
    assert [i.restated_to for i in items] == [None, None] and not any(i.basis_differs for i in items)


def test_figures_in_an_unknown_or_different_unit_are_never_called_restated():
    """Wipro FY 2022-23: energy with no unit, exactly 1,000 times the next filing's GJ. That is a unit question, not a restatement."""
    no_unit = trend_cells(two_years(721_130_435, 721_130.4, unit=UNKNOWN_UNIT), getter)[0]
    assert no_unit.restated_to is None and no_unit.basis_differs is False
    different = build_trend("T", "T", [YearEntry("2022-23", report("2022-23", 100, None, unit="GJ")),
                                       YearEntry("2023-24", report("2023-24", 500, 1.0, unit="kL"))])
    assert trend_cells(different, getter)[0].restated_to is None


def test_a_difference_across_a_change_of_basis_is_not_a_restatement_it_is_a_different_thing():
    """Tata Steel FY 2022-23 (consolidated) against the next filing's standalone figure for the same year."""
    item = trend_cells(two_years(857.0, 559.0, boundary="Consolidated basis", boundary_later="Standalone basis"), getter)[0]
    assert item.basis_differs is True and item.restated_to is None


def test_borrowed_columns_and_the_newest_year_are_never_checked_against_a_later_filing():
    trend = build_trend("T", "T", [YearEntry("2021-22", problem="x", kind=NOT_FILED), YearEntry("2022-23", report("2022-23", 10, 8)),
                                   YearEntry("2023-24", report("2023-24", 12, 99))])
    items = trend_cells(trend, getter)
    assert items[0].restated_to is None and items[2].restated_to is None
    assert items[1].restated_to is not None                                  # 10 in its own filing, 99 in the next one


def test_the_finish_step_changes_how_figures_are_shown_including_the_restated_one():
    items = trend_cells(two_years(100.0, 140.0), getter, finish=lambda c: Cell(c.value * 10, c.unit, c.status))
    assert items[0].cell.value == 1000.0 and items[0].restated_to.value == 1400.0


def test_a_row_the_filing_does_not_have_gives_empty_cells():
    trend = build_trend("T", "T", [YearEntry("2022-23", report("2022-23"))])
    assert trend_cells(trend, getter)[0].cell.status == Status.NOT_REPORTED


def test_relative_difference():
    assert relative_difference(100, 100) == 0 and relative_difference(0, 0) == 0
    assert relative_difference(100, 50) == pytest.approx(0.5) and relative_difference(0, 5) == 1


# ------------------------------------------------------------------------------------------------ basis changes
def test_a_change_of_basis_between_neighbouring_years_is_listed_once():
    entries = [YearEntry("2022-23", report("2022-23", 1, None, boundary="Consolidated basis")),
               YearEntry("2023-24", report("2023-24", 1, None)), YearEntry("2024-25", report("2024-25", 1, None))]
    assert basis_changes(build_trend("T", "T", entries)) == [("2022-23", "2023-24", "Consolidated basis", "Standalone basis")]


def test_no_change_when_every_year_has_the_same_basis_or_a_year_has_no_figures():
    entries = [YearEntry("2021-22", problem="x", kind=NOT_FILED), YearEntry("2022-23", report("2022-23", 1)), YearEntry("2023-24", report("2023-24", 1))]
    assert basis_changes(build_trend("T", "T", entries)) == []
