"""The shapes of our clean data. Everything after "reading a filing" uses these classes.

The idea: one number on the page is a `Cell`. It never travels alone: it carries its unit, how we got it
(`status`), exactly what the filing said (`as_filed`), and any warnings. That is how we keep the promise
"never invent numbers; say so when something is missing, converted or doubtful".
"""

from dataclasses import dataclass, field
from enum import Enum


class Status(str, Enum):
    REPORTED = "reported"          # the filing gave this value (we may only have tidied the unit's spelling)
    NOT_REPORTED = "not_reported"  # the filing has nothing for this item
    CALCULATED = "calculated"      # we built it by adding reported numbers together
    CONVERTED = "converted"        # reported, but we changed the unit or scale (the original is in `as_filed`)


@dataclass
class Cell:
    """One value for one financial year, i.e. one cell of a SEBI table."""

    value: object = None   # a number, a piece of text, or None when there is nothing
    unit: str = ""         # the unit shown to the reader, e.g. "GJ"
    status: Status = Status.NOT_REPORTED
    as_filed: str = ""     # exactly what the filing said, e.g. "64 MtCO2e"
    note: str = ""         # harmless explanation, e.g. "Sum of renewable and non-renewable electricity"
    warnings: list = field(default_factory=list)  # reasons to doubt the value


@dataclass
class Metric:
    """One row of a SEBI table: a label plus the current-year and previous-year cells."""

    key: str     # stable id such as "E1.electricity" (the SEBI view and the dashboard both look rows up by it)
    label: str
    current: Cell = field(default_factory=Cell)
    previous: Cell = field(default_factory=Cell)


@dataclass
class ListTable:
    """A table whose rows are written out one by one (sensitive areas, EIAs, initiatives)."""

    key: str
    columns: list
    rows: list              # each row is a list of text, one entry per column
    note: str = ""


@dataclass
class Facility:
    """One facility located in an area of water stress (Leadership question 3)."""

    name: str
    nature: str
    metrics: dict           # same row keys as the water rows, each a Metric


@dataclass
class Assurance:
    """The 'independent assessment / assurance' note under a table."""

    carried_out: str = "Not reported"   # "Yes", "No" or "Not reported"
    agency: str = ""


@dataclass
class Principle6Report:
    """Everything we know about one company's Principle 6 for one financial year."""

    company_name: str
    symbol: str
    fy: str                 # "2023-24"
    previous_fy: str        # "2022-23"
    boundary: str = ""      # "Standalone basis" / "Consolidated basis" (as the filing says)
    taxonomy_release: str = ""   # the edition of SEBI's XBRL form, e.g. "2024-04-30"
    family: str = ""        # "legacy" (before 2024-04-30) or "modern"
    submission_date: str = ""
    revision_date: str = ""
    source_file: str = ""
    metrics: dict = field(default_factory=dict)      # key -> Metric (the SEBI tables' numeric/yes-no/text rows)
    extras: dict = field(default_factory=dict)       # key -> Metric (items newer filings have but the 2021 template does not)
    tables: dict = field(default_factory=dict)       # key -> ListTable
    facilities: list = field(default_factory=list)   # list of Facility
    assurance: dict = field(default_factory=dict)    # question id -> Assurance
    warnings: list = field(default_factory=list)     # problems with the filing as a whole
