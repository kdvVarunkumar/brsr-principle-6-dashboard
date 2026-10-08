"""Print a Principle6Report as plain text, laid out like the SEBI form.

This is a quick, readable view of the clean data (the real HTML pages come in Phases 5 and 6, built from the same data).
"""

import textwrap

from brsr_p6.core.formatting import format_number
from brsr_p6.core.models import Status
from brsr_p6.core.sebi_template import QUESTIONS
from brsr_p6.views.trace_view import cell_lines

LABEL_WIDTH = 62


def format_value(cell):
    """A cell as short text for a table."""
    if cell.status == Status.NOT_REPORTED:
        return "Not reported"
    if isinstance(cell.value, str):
        return cell.value
    return format_number(cell.value)


def marker(*cells):
    """c = calculated by us, k = converted by us, ! = has a warning."""
    flags = ""
    if any(c.status == Status.CALCULATED for c in cells):
        flags += "c"
    if any(c.status == Status.CONVERTED for c in cells):
        flags += "k"
    if any(c.warnings for c in cells):
        flags += "!"
    return flags


def render_text(report, only=None, trace=False):
    """The whole report as one string.  `only` = list of question ids such as ["E1", "E6"] to print just those.

    `trace=True` adds, under every value, the filing's element(s) and the text exactly as filed (the trace back to the filing)."""
    out = []
    add = out.append
    add("=" * 100)
    add(f"BRSR PRINCIPLE 6 (environment), SEBI format of May 2021")
    add(f"{report.company_name} ({report.symbol})   FY {report.fy}   (previous year: FY {report.previous_fy})")
    add(f"Reporting boundary: {report.boundary}")
    add(f"Filed on NSE: {report.submission_date or '?'}" + (f", revised {report.revision_date}" if report.revision_date else "")
        + f"   |   form edition: {report.taxonomy_release} ({report.family})   |   file: {report.source_file}")
    for warning in report.warnings:
        add(f"WARNING: {warning}")
    add("Marks:  c = calculated by us from reported numbers   k = converted by us   ! = doubtful, see the notes below the table")
    add("=" * 100)

    section = None
    for question in QUESTIONS:
        if only and question.id not in only:
            continue
        if question.section != section:
            section = question.section
            add("")
            add(section.upper())
        add("")
        add(_wrap(f"{question.number}. {question.text}", 100))

        if question.kind == "table":
            _table(out, report, question.rows, report.metrics, trace)
        elif question.kind == "yes_no":
            _answer(out, report, report.metrics[f"{question.id}.answer"].current, report.metrics[f"{question.id}.details"].current, trace)
        elif question.kind == "text":
            _answer(out, report, None, report.metrics[f"{question.id}.details"].current, trace)
        elif question.kind == "number":
            cell = report.metrics[f"{question.id}.value"].current
            add(f"   Answer: {format_value(cell)} {cell.unit if cell.status != Status.NOT_REPORTED else ''}".rstrip())
            if trace:
                _trace_lines(out, report, cell)
            _notes(out, [(question.id, cell, None)])
        elif question.kind == "list":
            _list(out, report.tables[question.id], trace)
        elif question.kind == "facilities":
            _facilities(out, report, question, trace)

        if question.remark:
            add(_wrap(f"   Remark: {question.remark}", 100))
        if question.id in report.assurance:
            assurance = report.assurance[question.id]
            agency = f" ({textwrap.shorten(assurance.agency, 110, placeholder=' ...')})" if assurance.agency else ""
            add(f"   Independent assessment / assurance by an external agency: {assurance.carried_out}{agency}")

    if report.extras and not only:
        add("")
        add("ADDITIONAL ITEMS IN THIS FILING (not part of the 2021 SEBI form; shown as filed)")
        _table(out, report, [_AsRow(m.key, m.label) for m in report.extras.values()], report.extras, trace)
    return "\n".join(out)


# ----------------------------------------------------------------------------------------------- pieces
class _AsRow:
    """Lets extras be printed with the same table code."""

    def __init__(self, key, label):
        self.key, self.label, self.header = key, label, False


def _wrap(text, width, indent=""):
    return "\n".join(textwrap.wrap(text, width, initial_indent=indent, subsequent_indent=indent)) or indent


def _trace_lines(out, report, current, previous=None):
    """With --trace, under a value: the filing's element(s) and the text as filed, for each year."""
    for year, cell in ((report.fy, current), (report.previous_fy, previous)):
        if cell is None:
            continue
        for line in cell_lines(cell):
            out.append(textwrap.fill(f"FY {year}: {line}", 100, initial_indent="        ↳ ", subsequent_indent="            "))


def _table(out, report, rows, metrics, trace=False):
    out.append(f"   {'Parameter':{LABEL_WIDTH}} {'FY ' + report.fy:>16} {'FY ' + report.previous_fy:>16}  {'Unit':<18} Marks")
    notes = []
    for row in rows:
        if row.header:
            out.append("   " + row.label)
            continue
        metric = metrics[row.key]
        cur, prev = metric.current, metric.previous
        lines = textwrap.wrap(row.label, LABEL_WIDTH) or [""]
        unit = cur.unit or prev.unit
        out.append(f"   {lines[0]:{LABEL_WIDTH}} {format_value(cur):>16} {format_value(prev):>16}  {unit:<18} {marker(cur, prev)}")
        for extra_line in lines[1:]:
            out.append("   " + extra_line)
        if trace:
            _trace_lines(out, report, cur, prev)
        notes.append((row.label, cur, prev))
    _notes(out, notes)


def _notes(out, items):
    """Under a table: each distinct note/warning once, with the rows it applies to (so 6 identical warnings become 1)."""
    groups = {}   # (prefix, message) -> {"labels": [...], "years": {...}}
    for label, cur, prev in items:
        short = label if len(label) <= 32 else label[:30] + "..."
        for year, cell in (("current year", cur), ("previous year", prev)):
            if cell is None:
                continue
            for prefix, text in [("note", cell.note), *[("WARNING", w) for w in cell.warnings]]:
                if text and (cell.status != Status.NOT_REPORTED or prefix == "WARNING"):
                    group = groups.setdefault((prefix, text), {"labels": [], "years": set()})
                    if short not in group["labels"]:
                        group["labels"].append(short)
                    group["years"].add(year)
    for (prefix, text), group in groups.items():
        labels = group["labels"]
        shown = ", ".join(labels[:2]) + (f" and {len(labels) - 2} more" if len(labels) > 2 else "")
        only_year = f" ({next(iter(group['years']))})" if len(group["years"]) == 1 else ""
        out.append(textwrap.fill(f"{prefix} [{shown}]{only_year}: {text}", 100, initial_indent="   ", subsequent_indent="      "))


def _answer(out, report, answer_cell, details_cell, trace=False):
    if answer_cell is not None:
        extra = f"  (as filed: '{answer_cell.as_filed}')" if answer_cell.status != Status.NOT_REPORTED and answer_cell.as_filed != answer_cell.value else ""
        out.append(f"   Answer: {format_value(answer_cell)}{extra}")
        if trace:
            _trace_lines(out, report, answer_cell)
    if details_cell.status == Status.NOT_REPORTED:
        out.append("   Details: Not reported")
    else:
        out.append("   Details:")
        out.append(_wrap(details_cell.value, 100, "      "))
    if trace:
        _trace_lines(out, report, details_cell)
    _notes(out, [("answer", answer_cell, None)] if answer_cell is not None else [])


def _list(out, table, trace=False):
    out.append("   Columns: " + " | ".join(table.columns))
    for row in table.rows:
        out.append("   " + " | ".join(row))
    if table.note:
        out.append(_wrap(f"   Note: {table.note}", 100))
    if trace and table.elements:
        out.append(textwrap.fill("Read from the filing's elements: " + ", ".join(table.elements), 100, initial_indent="        ↳ ", subsequent_indent="            "))


def _facilities(out, report, question, trace=False):
    if not report.facilities:
        out.append("   No facility in an area of water stress is listed in the structured filing.")
        return
    for number, facility in enumerate(report.facilities, start=1):
        out.append(f"   --- Facility {number}: {facility.name} | Nature of operations: {facility.nature}")
        _table(out, report, question.rows, facility.metrics, trace)
