"""The data behind a multi-year trend page.  Pure logic: no files, no internet, so it is easy to test.

Every filing contains TWO years: its own ("current") and the one before ("previous").  That gives a trend page two useful tricks:

  * A year NSE has no filing for can still be shown, when the NEXT year's filing exists: that filing's previous-year column holds the
    company's own figures for it.  Such a column is marked "from the FY ... filing"; it is real data, never a guess or a zero.
  * A year's own figures can be checked against what the next filing says about the same year.  If they differ by more than rounding,
    the company RESTATED them.  We keep the figure as filed in its own year and flag the restatement.  If the two filings are on a
    different reporting basis (standalone vs consolidated) or the unit is not stated, the figures are not comparable and we say so
    instead of calling it a restatement.
"""

from dataclasses import dataclass, field

from brsr_p6.comparison import has_number
from brsr_p6.fiscal_year import next_fiscal_year
from brsr_p6.models import Cell
from brsr_p6.units import UNIT_NOT_STATED

RESTATEMENT_TOLERANCE = 0.005     # a later filing's figure must differ by more than 0.5 % to count (smaller gaps are rounding)

# where a year's figures come from
OWN, BORROWED, NONE = "own", "borrowed", "none"

# why a year has no figures of its own
NOT_FILED, NO_FILE, UNREADABLE, BUG = "not_filed", "no_file", "unreadable", "bug"


@dataclass
class YearEntry:
    """What the loader found for one financial year of the requested range."""

    fy: str
    report: object = None      # a Principle6Report, or None
    problem: str = ""          # when there is no report: why (a sentence for the reader)
    kind: str = ""             # NOT_FILED, NO_FILE, UNREADABLE or BUG


@dataclass
class YearColumn:
    """One column of the trend page."""

    fy: str
    source: str                # OWN, BORROWED or NONE
    report: object = None      # the report the figures are read from
    side: str = "current"      # "current" for OWN; "previous" for BORROWED (the next filing's previous-year column)
    basis: str = ""            # "standalone", "consolidated" or "unknown" ("" when there are no figures)
    boundary_text: str = ""    # the filing's own words, e.g. "Standalone basis"
    borrowed_from: str = ""    # BORROWED: the financial year of the filing the figures come from
    problem: str = ""          # why this year has no filing of its own
    kind: str = ""
    filed_on: str = ""
    edition: str = ""          # "legacy" (older SEBI layout) or "modern"


@dataclass
class TrendCell:
    """One figure in one year, with what the next filing says about it."""

    cell: Cell
    column: YearColumn
    restated_to: Cell | None = None     # the next filing's figure for this year, when it differs by more than rounding
    restated_in: str = ""               # the financial year of that next filing
    basis_differs: bool = False         # the next filing is on another basis, so the two figures cannot be compared


@dataclass
class Trend:
    company_name: str
    symbol: str
    columns: list = field(default_factory=list)      # YearColumn, oldest year first


# ------------------------------------------------------------------------------------------------ building the columns
def basis_of(boundary_text):
    """'Standalone basis' -> 'standalone'; 'Consolidated basis' -> 'consolidated'; anything else -> 'unknown'."""
    text = (boundary_text or "").lower()
    if "standalone" in text:
        return "standalone"
    if "consolidated" in text:
        return "consolidated"
    return "unknown"


def build_trend(company_name, symbol, entries):
    """Turn the loaded years (YearEntry, oldest first) into a Trend."""
    by_year = {entry.fy: entry for entry in entries}
    columns = []
    for entry in entries:
        if entry.report is not None:
            columns.append(_column(entry.fy, OWN, entry.report, "current"))
            continue
        later = by_year.get(next_fiscal_year(entry.fy))
        if later is not None and later.report is not None:        # the next filing knows this year too
            column = _column(entry.fy, BORROWED, later.report, "previous")
            column.borrowed_from = later.fy
        else:
            column = YearColumn(entry.fy, NONE)
        column.problem, column.kind = entry.problem, entry.kind
        columns.append(column)
    return Trend(company_name, symbol, columns)


def _column(fy, source, report, side):
    return YearColumn(fy, source, report, side, basis_of(report.boundary), report.boundary,
                      filed_on=report.submission_date, edition=report.family)


# ------------------------------------------------------------------------------------------------ one row across the years
def trend_cells(trend, getter, finish=None):
    """One TrendCell per year for one row of figures.

    `getter(report, side)` returns the Cell of that row for the "current" or "previous" side of a report.
    `finish(cell)` (optional) changes how a cell is shown, for example per Rs crore; it is applied last."""
    finish = finish or (lambda cell: cell)
    items = []
    for index, column in enumerate(trend.columns):
        cell = getter(column.report, column.side) if column.report is not None else Cell()
        item = TrendCell(cell, column)
        later = trend.columns[index + 1] if index + 1 < len(trend.columns) else None
        if column.source == OWN and later is not None and later.source == OWN:
            _check_against_the_next_filing(item, getter(later.report, "previous"), later)
        item.cell = finish(item.cell)
        if item.restated_to is not None:
            item.restated_to = finish(item.restated_to)
        items.append(item)
    return items


def _check_against_the_next_filing(item, later_cell, later_column):
    """Does the next filing give a different figure for this same year?"""
    mine = item.cell
    if not (has_number(mine) and has_number(later_cell)):
        return
    if mine.unit != later_cell.unit or mine.unit == UNIT_NOT_STATED:
        return                                   # a different or unknown unit: we cannot tell whether the figures are the same thing
    if relative_difference(mine.value, later_cell.value) <= RESTATEMENT_TOLERANCE:
        return                                   # the same figure (a small gap is rounding)
    if item.column.basis != later_column.basis:
        item.basis_differs = True                # the two filings describe different things (for example consolidated vs standalone)
        return
    item.restated_to, item.restated_in = later_cell, later_column.fy


def relative_difference(a, b):
    """How far apart two numbers are, as a share of the bigger one (0 = equal, 1 = completely different)."""
    biggest = max(abs(a), abs(b))
    return abs(a - b) / biggest if biggest else 0.0


# ------------------------------------------------------------------------------------------------ facts about the whole trend
def basis_changes(trend):
    """[(earlier year, later year, earlier basis text, later basis text), ...] where two neighbouring years differ in basis."""
    changes = []
    figured = [c for c in trend.columns if c.report is not None]
    for before, after in zip(figured, figured[1:]):
        if before.basis != after.basis:
            changes.append((before.fy, after.fy, before.boundary_text or "not stated", after.boundary_text or "not stated"))
    return changes
