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
class Origin:
    """Where a value came from in the filing: the XBRL element, the year it covers and the text exactly as written in the file.

    This is the end of the trace "number on the page -> SEBI row -> this -> the NSE file", so a reader can open the XML and find it."""

    element: str           # the XBRL element (tag) name, e.g. "TotalEnergyConsumed"
    raw: str               # the value as written in the file, e.g. "375373200" (for several rows added up: their sum)
    unit: str = ""         # the unit id as written in the file, e.g. "Gigajoule" ("" when the filing gives none)
    period_end: str = ""   # last day of the period the value covers, e.g. "2024-03-31"
    rows: int = 1          # more than 1: that many row-labelled facts of this element were added up (`raw` is their sum)


@dataclass
class Cell:
    """One value for one financial year, i.e. one cell of a SEBI table."""

    value: object = None   # a number, a piece of text, or None when there is nothing
    unit: str = ""         # the unit shown to the reader, e.g. "GJ"
    status: Status = Status.NOT_REPORTED
    as_filed: str = ""     # exactly what the filing said, e.g. "64 MtCO2e"
    note: str = ""         # harmless explanation, e.g. "Sum of renewable and non-renewable electricity"
    warnings: list = field(default_factory=list)  # reasons to doubt the value
    origin: list = field(default_factory=list)    # [Origin]: the filing's own element(s) behind this value (empty when not reported)
    looked_for: list = field(default_factory=list)  # [element names] we searched for when the filing had nothing (empty: it has no field)


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
    elements: list = field(default_factory=list)   # the filing's own elements the rows were read from (no rows: the ones we looked for)


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
    elements: list = field(default_factory=list)   # the filing's own elements the answer and the agency were read from


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
    source_file: str = ""   # the XBRL file's name
    source_url: str = ""    # where NSE publishes that file (an https link; "" when unknown)
    pdf_url: str = ""       # NSE's PDF version of the same filing ("" when NSE has none)
    metrics: dict = field(default_factory=dict)      # key -> Metric (the SEBI tables' numeric/yes-no/text rows)
    extras: dict = field(default_factory=dict)       # key -> Metric (items newer filings have but the 2021 template does not)
    tables: dict = field(default_factory=dict)       # key -> ListTable
    facilities: list = field(default_factory=list)   # list of Facility
    assurance: dict = field(default_factory=dict)    # question id -> Assurance
    warnings: list = field(default_factory=list)     # problems with the filing as a whole
