"""Turn a Principle6Report into exactly what the SEBI page shows.

The HTML template should only PRINT things.  All the decisions ("which footnote number does this warning get?",
"what text goes in an empty cell?") are made here, in plain Python, so the template stays short and easy to read.

Output shape (all plain objects):
    SebiView
      .sections        [SectionView(title, questions=[QuestionView, ...])]
      .extras          TableView or None     (items newer filings have that the 2021 form does not)
    QuestionView       one SEBI question: number, official text, and one of: table / answer+details / list / facilities
    TableView          rows with a current-year cell and a previous-year cell, plus footnotes
"""

from dataclasses import dataclass, field

from brsr_p6.core.formatting import format_number_html
from brsr_p6.core.models import Status
from brsr_p6.core.sebi_template import QUESTIONS
from brsr_p6.views.trace_view import tooltip

NOT_REPORTED = "Not reported"
NOTHING_TO_SAY = {"Not found in the filing."}   # a note that would only repeat "Not reported" on every empty row


# ----------------------------------------------------------------------------------------------- building blocks
@dataclass
class CellView:
    text: object                  # what to print in the cell (a plain string or safe HTML)
    unit: str = ""
    missing: bool = False         # True -> the cell is "Not reported"
    tags: list = field(default_factory=list)    # "calculated" / "converted": shown as small labels
    notes: list = field(default_factory=list)   # footnote numbers of harmless notes
    warns: list = field(default_factory=list)   # footnote numbers of warnings
    trace: str = ""               # hover text: the filing's element(s) this value was read from ("" when there is nothing to trace)


@dataclass
class RowView:
    label: str
    header: bool = False          # a heading line inside the table
    unit: str = ""                # for tables that have a Unit column
    current: CellView = None
    previous: CellView = None


@dataclass
class TableView:
    rows: list
    unit_column: str = ""         # heading of the Unit column ("" = this table has none)
    footnotes: list = field(default_factory=list)   # [(number, "note" or "warning", text)]


@dataclass
class ListView:
    columns: list
    rows: list                    # each row: list of (text, muted) pairs
    note: str = ""


@dataclass
class FacilityView:
    name: str
    nature: str
    table: TableView


@dataclass
class QuestionView:
    id: str
    section: str
    number: int
    text: str
    kind: str
    table: TableView = None
    answer: CellView = None       # yes/no, text and number questions
    details: str = None
    listing: ListView = None      # (not called "list": that would hide Python's own list)
    facilities: list = field(default_factory=list)
    assurance: str = ""           # "Yes (KPMG ...)" / "Not reported"
    has_assurance: bool = False
    remark: str = ""


@dataclass
class SectionView:
    title: str
    questions: list


@dataclass
class SebiView:
    sections: list
    extras: TableView = None


class Footnotes:
    """Hands out footnote numbers; the same message always gets the same number inside one question."""

    def __init__(self):
        self.items = []   # [(kind, text)]

    def number(self, kind, text):
        if (kind, text) not in self.items:
            self.items.append((kind, text))
        return self.items.index((kind, text)) + 1

    def as_list(self):
        return [(n, kind, text) for n, (kind, text) in enumerate(self.items, start=1)]


# ----------------------------------------------------------------------------------------------- cells
def cell_view(cell, footnotes):
    """One Cell -> what to print."""
    view = CellView(text=NOT_REPORTED, missing=True)
    if cell.status != Status.NOT_REPORTED:
        view.missing = False
        view.unit = cell.unit
        view.text = cell.value if isinstance(cell.value, str) else format_number_html(cell.value)
        view.trace = tooltip(cell)
        if cell.status in (Status.CALCULATED, Status.CONVERTED):
            view.tags.append(cell.status.value)
    if cell.note and cell.note not in NOTHING_TO_SAY:
        view.notes.append(footnotes.number("note", cell.note))
    for warning in cell.warnings:
        view.warns.append(footnotes.number("warning", warning))
    return view


def _table(rows, footnotes, unit_column=""):
    return TableView(rows, unit_column, footnotes.as_list())


def _value_rows(template_rows, metrics, footnotes, unit_column):
    rows = []
    for template_row in template_rows:
        if template_row.header:
            rows.append(RowView(template_row.label, header=True))
            continue
        metric = metrics[template_row.key]
        current = cell_view(metric.current, footnotes)
        previous = cell_view(metric.previous, footnotes)
        unit = ""
        if unit_column:   # the unit moves into its own column, as in SEBI's form
            unit = metric.current.unit or metric.previous.unit
            current.unit = previous.unit = ""
        rows.append(RowView(template_row.label, unit=unit, current=current, previous=previous))
    return rows


# ----------------------------------------------------------------------------------------------- questions
def build_sebi_view(report):
    sections = []
    for question in QUESTIONS:
        view = _question_view(report, question)
        if not sections or sections[-1].title != question.section:
            sections.append(SectionView(question.section, []))
        sections[-1].questions.append(view)
    return SebiView(sections, _extras_view(report))


def _question_view(report, question):
    view = QuestionView(question.id, question.section, question.number, question.text, question.kind, remark=question.remark)
    footnotes = Footnotes()

    if question.kind == "table":
        rows = _value_rows(question.rows, report.metrics, footnotes, question.unit_column)
        view.table = _table(rows, footnotes, question.unit_column)

    elif question.kind in ("yes_no", "text", "number"):
        answer_key = {"yes_no": ".answer", "number": ".value"}.get(question.kind)
        if answer_key:   # a text-only question has no short answer, only details
            view.answer = cell_view(report.metrics[question.id + answer_key].current, footnotes)
        if question.kind != "number":
            details = report.metrics[question.id + ".details"].current
            view.details = details.value if details.status != Status.NOT_REPORTED else None   # None = "Not reported"
        view.table = TableView([], "", footnotes.as_list())   # footnotes (if any) go under the answer

    elif question.kind == "list":
        view.listing = _list_view(report.tables[question.id])

    elif question.kind == "facilities":
        for facility in report.facilities:
            facility_notes = Footnotes()
            rows = _value_rows(question.rows, facility.metrics, facility_notes, "")
            view.facilities.append(FacilityView(facility.name, facility.nature, _table(rows, facility_notes)))

    if question.assurance:
        view.has_assurance = True
        assurance = report.assurance.get(question.id)
        if assurance and assurance.carried_out != "Not reported":
            view.assurance = assurance.carried_out + (f": {assurance.agency}" if assurance.agency else "")
        else:
            view.assurance = NOT_REPORTED
    return view


def _list_view(table):
    muted_words = (NOT_REPORTED, "Not in the structured filing")
    rows = [[(text, text in muted_words) for text in row] for row in table.rows]
    return ListView(table.columns, rows, table.note)


def _extras_view(report):
    if not report.extras:
        return None
    footnotes = Footnotes()
    rows = []
    for metric in report.extras.values():
        rows.append(RowView(metric.label, current=cell_view(metric.current, footnotes), previous=cell_view(metric.previous, footnotes)))
    return _table(rows, footnotes)
