"""The trace from a number on a page back to the filing: "never invent numbers, every figure must trace back to a filing".

The chain a reader can follow, one link at a time:
    a dashboard card  ->  its Fine print names the SEBI question and lists the filing's element(s)
    a SEBI table cell ->  hover it to see the same
    the last section of the SEBI tab ("Where every number comes from") -> every row: the value shown, how we got it, the element(s),
                         the year they cover and the text exactly as written in the filing, and a link to NSE's file.

All the wording is decided here; the template only prints it.  The facts come from `Cell.origin` (extraction/extractor.py), which a
test checks against the raw XML of every real filing on disk.
"""

import re
from dataclasses import dataclass, field

from brsr_p6.core.formatting import format_number
from brsr_p6.core.models import Status
from brsr_p6.core.sebi_template import QUESTIONS

MAX_TEXT = 90       # long answers (a paragraph of text) are shortened here; the full text is in the saved JSON and in the filing

STATUS_WORDS = {
    Status.REPORTED: "Reported by the company",
    Status.CALCULATED: "Calculated by us from reported figures",
    Status.CONVERTED: "Unit changed by us",
    Status.NOT_REPORTED: "Not reported",
}


# ------------------------------------------------------------------------------------------------ small pieces
def short(text, limit=MAX_TEXT):
    """One line of text, cut with an ellipsis when it is long."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def origin_text(origin):
    """'TotalEnergyConsumed = 375373200 Gigajoule': the element, and the value exactly as the filing wrote it."""
    unit = f" {origin.unit}" if origin.unit else ""
    rows = f" (the sum of {origin.rows} rows)" if origin.rows > 1 else ""
    return f"{origin.element} = {short(origin.raw)}{unit}{rows}"


def nothing_text(cell):
    """Why there is no value, in the filing's terms: what was looked for, or that the form has no field at all."""
    parts = [cell.note] if cell.note else ["Not found in the filing."]
    if cell.looked_for:
        parts.append("Elements looked for: " + ", ".join(cell.looked_for) + ".")
    return " ".join(parts)


def shown_text(cell):
    """What the SEBI tab shows for this cell, as plain text."""
    if cell.status == Status.NOT_REPORTED:
        return "Not reported"
    if isinstance(cell.value, str):
        return short(cell.value)
    return f"{format_number(cell.value)} {cell.unit}".strip()


def cell_lines(cell):
    """The element line(s) behind one cell ('' lines are never returned)."""
    if cell.status == Status.NOT_REPORTED:
        return [nothing_text(cell)]
    return [origin_text(origin) for origin in cell.origin]


def tooltip(cell):
    """The hover text for a number in the SEBI tab ('' when there is nothing to trace)."""
    if cell.status == Status.NOT_REPORTED or not cell.origin:
        return ""
    return "From the filing: " + "; ".join(origin_text(origin) for origin in cell.origin)


# ------------------------------------------------------------------------------------------------ a dashboard card
def figure_trace(report, metrics):
    """Lines for a card's Fine print: for each year, the filing's element(s) behind the figure.

    `metrics` is the Metric the card shows, or the several rows a calculated figure is built from (their elements are listed together)."""
    lines = []
    for side, year in (("current", report.fy), ("previous", report.previous_fy)):
        pieces = []
        for metric in metrics:
            cell = getattr(metric, side)
            pieces += [origin_text(origin) for origin in cell.origin]
        lines.append(f"FY {year}: " + ("; ".join(pieces) if pieces else "not in the filing"))
    return lines


# ------------------------------------------------------------------------------------------------ the full section
@dataclass
class TraceCell:
    shown: str                     # what the SEBI tab shows
    status: str                    # words: "Reported by the company"
    lines: list                    # the element line(s), or why there is nothing
    note: str = ""                 # how we got it, when that needs saying ("Sum of ...")
    missing: bool = False
    not_asked: bool = False        # the form asks this question for the current year only


@dataclass
class TraceRow:
    label: str
    current: TraceCell
    previous: TraceCell


@dataclass
class TraceQuestion:
    id: str
    title: str                     # "Essential 1"
    text: str                      # the start of SEBI's question
    rows: list = field(default_factory=list)
    remarks: list = field(default_factory=list)       # list tables and assurance: which elements they were read from


@dataclass
class TraceView:
    source_file: str
    source_url: str
    pdf_url: str
    filed: str
    edition: str
    boundary: str
    current_year: str
    previous_year: str
    questions: list
    extras: TraceQuestion = None


NOT_ASKED = TraceCell("", "", [], not_asked=True)


def trace_cell(cell):
    notes = cell.note if cell.status in (Status.CALCULATED, Status.CONVERTED) else ""
    return TraceCell(shown_text(cell), STATUS_WORDS[cell.status], cell_lines(cell), notes, missing=cell.status == Status.NOT_REPORTED)


def _row(label, metric, both_years=True):
    return TraceRow(label, trace_cell(metric.current), trace_cell(metric.previous) if both_years else NOT_ASKED)


def build_trace_view(report):
    questions = [_question(report, question) for question in QUESTIONS]
    extras = None
    if report.extras:
        extras = TraceQuestion("X", "Additional items", "Items newer filings have that the 2021 form does not",
                               [_row(metric.label, metric) for metric in report.extras.values()])
    filed = report.submission_date or "date not available"
    if report.revision_date:
        filed += f" (revised {report.revision_date})"
    return TraceView(report.source_file, report.source_url, report.pdf_url, filed, f"{report.taxonomy_release} ({report.family} layout)",
                     report.boundary, report.fy, report.previous_fy, questions, extras)


def _question(report, question):
    title = f"{'Essential' if question.id[0] == 'E' else 'Leadership'} {question.id[1:]}"
    view = TraceQuestion(question.id, title, short(question.text, 110))

    if question.kind == "table":
        view.rows = [_row(row.label, report.metrics[row.key]) for row in question.rows if not row.header]
    elif question.kind in ("yes_no", "text", "number"):
        keys = {"yes_no": (("Answer", ".answer"), ("Details", ".details")), "text": (("Details", ".details"),), "number": (("Percentage", ".value"),)}
        view.rows = [_row(label, report.metrics[question.id + suffix], both_years=False) for label, suffix in keys[question.kind]]
    elif question.kind == "list":
        table = report.tables[question.id]
        names = ", ".join(table.elements) or "none"
        view.remarks.append(f"The {len(table.rows)} row(s) of this table were read from: {names}." if table.rows
                            else f"The filing lists no rows. Elements looked for: {names}.")
    elif question.kind == "facilities":
        for facility in report.facilities:
            for row in question.rows:
                if not row.header:
                    view.rows.append(_row(f"{facility.name}: {row.label}", facility.metrics[row.key]))
        if not report.facilities:
            view.remarks.append("The structured filing lists no facility in an area of water stress.")

    if question.assurance:
        assurance = report.assurance.get(question.id)
        if assurance and assurance.elements:
            view.remarks.append("The assurance answer was read from: " + ", ".join(assurance.elements) + ".")
        else:
            view.remarks.append("Assurance: not reported (no element in the filing).")
    return view
