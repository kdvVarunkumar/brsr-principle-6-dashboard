"""Everything the multi-year trend page shows, decided in plain Python.  The template (trends.html) only prints it.

Two kinds of table, one column per financial year:
  * HEADLINE tables, one per topic (Energy, Climate, Water, Air, Waste): the same figures as the one-year dashboard, each with a
    mini bar per year and a verdict for the trend.  The verdict only compares years on the SAME reporting basis and in the SAME unit,
    so a change from consolidated to standalone, or a missing unit, can never fake a "better" or "worse".
  * EVERY-FIGURE tables, one per SEBI question: all numbers of the SEBI template, year by year, with marks.
Missing years are flagged in their column header and show "No filing", never zero.
"""

from collections import Counter
from dataclasses import dataclass, field

from brsr_p6.analysis.comparison import IMPROVED, UNSURE, WORSE, compare, has_number
from brsr_p6.analysis.trend_model import BORROWED, BUG, NO_FILE, NONE, NOT_FILED, OWN, UNREADABLE, basis_changes, trend_cells
from brsr_p6.analysis.warning_kinds import CHECK, DOUBTFUL, worst_kind
from brsr_p6.core import friendly
from brsr_p6.core.formatting import format_number, format_number_html
from brsr_p6.core.models import Cell, Status
from brsr_p6.core.sebi_template import ESSENTIAL, QUESTIONS, Row
from brsr_p6.core.units import UNIT_NOT_STATED
from brsr_p6.views.dashboard_cards import BETTER_LABELS, CHIPS, SCALABLE_UNITS, figure_getter, per_crore, reading
from brsr_p6.views.dashboard_view import short_name
from brsr_p6.views.metric_info import METRICS, TOPICS

BASIS_TEXT = {"standalone": "Standalone", "consolidated": "Consolidated", "unknown": "Basis not stated"}
WHY_NO_FIGURES = {NOT_FILED: "no filing on NSE", NO_FILE: "file missing on NSE", UNREADABLE: "filing could not be read",
                  BUG: "problem reading the filing"}
MAX_RESTATEMENTS_LISTED = 15


# ------------------------------------------------------------------------------------------------ the objects
@dataclass
class ColumnView:
    fy: str
    basis_text: str            # "Standalone", "Consolidated", "Basis not stated" or ""
    basis: str                 # for the colour of the chip
    source: str                # OWN, BORROWED or NONE
    note: str                  # "older SEBI layout" / "from the FY 2022-23 filing" / "no filing on NSE" ...


@dataclass
class Mark:
    symbol: str
    title: str                 # the explanation (tooltip and screen-reader text)
    css: str = ""


@dataclass
class CellView:
    text: object               # a str or Markup
    unit: str = ""             # only when this year's unit differs from the row's
    bar: float | None = None   # width of the mini bar, 0-100
    css: str = ""              # "empty" or "doubtful"
    marks: list = field(default_factory=list)
    tags: list = field(default_factory=list)      # "calc." / "conv."


@dataclass
class RowView:
    label: str
    cells: list
    unit: str = ""             # the row's unit, e.g. "crore GJ"
    better_label: str = ""
    chip_class: str = ""
    chip_text: str = ""
    trend: str = ""
    heading: bool = False      # a sub-heading line of a SEBI table (no cells)


@dataclass
class TopicTable:
    id: str
    name: str
    icon: str
    rows: list


@dataclass
class QuestionTable:
    label: str                 # "Essential 1"
    text: str                  # SEBI's wording
    rows: list


@dataclass
class Restatement:
    fy: str
    label: str
    filed: str
    restated: str
    change: str
    in_fy: str


@dataclass
class Note:
    kind: str                  # "missing", "basis", "units", "restated", "unreadable"
    text: str


@dataclass
class TrendView:
    company_name: str
    symbol: str
    first_fy: str
    last_fy: str
    summary: str
    columns: list
    notes: list
    topics: list
    questions: list
    restatements: list
    restated_total: int


# ------------------------------------------------------------------------------------------------ entry point
def build_trend_view(trend):
    columns = [_column_view(column) for column in trend.columns]
    topics = [TopicTable(topic.id, topic.name, topic.icon, rows) for topic in TOPICS
              if (rows := _headline_rows(trend, topic.id))]
    questions, restatements, unit_gaps = _question_tables(trend)
    restatements.sort(key=lambda r: -r[0])
    listed = [r[1] for r in restatements[:MAX_RESTATEMENTS_LISTED]]
    return TrendView(
        company_name=trend.company_name, symbol=trend.symbol, first_fy=trend.columns[0].fy, last_fy=trend.columns[-1].fy,
        summary=_summary(trend, len(restatements)), columns=columns,
        notes=_notes(trend, len(restatements), unit_gaps), topics=topics, questions=questions,
        restatements=listed, restated_total=len(restatements),
    )


# ------------------------------------------------------------------------------------------------ columns
def _column_view(column):
    if column.source == OWN:
        note = "older SEBI layout" if column.edition == "legacy" else ""
    elif column.source == BORROWED:
        note = f"{WHY_NO_FIGURES.get(column.kind, 'no filing')}; figures from the FY {column.borrowed_from} filing"
    else:
        note = WHY_NO_FIGURES.get(column.kind, "no figures")
    return ColumnView(column.fy, BASIS_TEXT.get(column.basis, ""), column.basis, column.source, note)


# ------------------------------------------------------------------------------------------------ headline tables
def _headline_rows(trend, topic_id):
    rows = []
    for info in (i for i in METRICS if i.topic == topic_id):
        finish = per_crore if info.shape == "intensity" else None
        items = trend_cells(trend, figure_getter(info), finish)
        if info.only_if_present and not any(has_number(item.cell) for item in items):
            continue                                            # an item that no edition of this company's filings has
        unit, divisor, word = _row_scale(items, info.shape)
        unit_text = info.unit_words if info.shape == "share" else friendly.unit_text(unit, word)
        chip_class, chip_text, trend_text = _row_trend(items, info)
        rows.append(RowView(
            label=info.title + (f" ({info.name})" if info.name else ""), cells=_headline_cells(items, info, unit, divisor, unit_text if unit else ""),
            unit=unit_text if unit else "", better_label=BETTER_LABELS[info.better],
            chip_class=chip_class, chip_text=chip_text, trend=trend_text))
    return rows


def _row_scale(items, shape):
    """(unit, divisor, word) for writing the whole row: the unit of the latest year, and lakh / crore picked from the biggest figure."""
    figures = [item.cell for item in items if has_number(item.cell)]
    if not figures:
        return "", 1, ""
    unit = figures[-1].unit
    if shape == "amount" and unit in SCALABLE_UNITS:
        divisor, word = friendly.scale_for(max(abs(c.value) for c in figures if c.unit == unit))
        return unit, divisor, word
    return unit, 1, ""


def _headline_cells(items, info, unit, divisor, unit_text):
    shape = info.shape
    same_unit = [i.cell.value for i in items if has_number(i.cell) and i.cell.unit == unit]
    top = 100.0 if shape == "share" else max((abs(v) for v in same_unit), default=0)
    cells = []
    for item in items:
        cell = item.cell
        if item.column.source == NONE:
            cells.append(CellView("No filing", css="empty"))
            continue
        if not has_number(cell):
            older_form = info.only_if_present and reading(item.column.report, info) is None
            cells.append(CellView("Not in the older form" if older_form else "Not reported", css="empty"))
            continue
        trust = worst_kind(cell.warnings)
        text, own_unit = _cell_text(cell, shape, unit, divisor, trust)
        view = CellView(text, unit=own_unit, css="doubtful" if trust == DOUBTFUL else "")
        if trust != DOUBTFUL and top and cell.unit == unit and not own_unit:
            view.bar = abs(cell.value) / top * 100
        view.marks = _marks(item, divisor if cell.unit == unit else 1, shape, unit_text, cell.unit != unit)
        cells.append(view)
    return cells


def _cell_text(cell, shape, row_unit, divisor, trust):
    """(text, own unit): a figure is written on the row's scale, but never as a misleading 0 (a tiny figure keeps its own scale)."""
    if shape == "share":
        return friendly.share_text(cell.value) + "%", ""
    if cell.value == 0 and trust == DOUBTFUL:
        return "Filed as 0", ""                                  # an intensity "rounded away": not a real zero
    if cell.unit != row_unit:
        return friendly.number_text(cell.value), friendly.unit_text(cell.unit)
    text = friendly.number_text(cell.value, divisor)
    if cell.value and text == "0":                               # e.g. 64 tonnes on a crore scale
        own_divisor, own_word = friendly.scale_for(cell.value) if cell.unit in SCALABLE_UNITS else (1, "")
        return friendly.number_text(cell.value, own_divisor), friendly.unit_text(cell.unit, own_word)
    return text, ""


def _headline_text(value, shape, divisor):
    return friendly.share_text(value) + "%" if shape == "share" else friendly.number_text(value, divisor)


def _marks(item, divisor, shape, unit_text, other_unit=False):
    """The small symbols on a cell: restated, different basis, doubtful or noted, different unit."""
    marks = []
    if item.restated_to is not None:
        unit = "" if shape == "share" else f" {unit_text}"                 # a share already ends with "%"
        later = _headline_text(item.restated_to.value, shape, divisor) + unit
        filed = _headline_text(item.cell.value, shape, divisor) + unit
        marks.append(Mark("⟲", f"Restated: the FY {item.restated_in} filing gives {later.strip()} for this year instead of {filed.strip()}.",
                          "restated"))
    if item.basis_differs:
        marks.append(Mark("≠", "The next filing is on a different reporting basis, so its figure for this year cannot be compared "
                               "with this one.", "basis"))
    if item.cell.warnings:
        label = "Doubtful figure" if worst_kind(item.cell.warnings) == DOUBTFUL else "Note on this figure"
        marks.append(Mark("ⓘ", f"{label}: " + " ".join(item.cell.warnings), "note"))
    if other_unit:
        marks.append(Mark("u", "This year's unit differs from the other years, so it is not compared with them.", "unit"))
    return marks


def _row_trend(items, info):
    """(chip class, chip text, sentence) for a headline row: latest year against the earliest year of the same basis and unit."""
    shape = "share" if info.shape == "share" else "amount"
    figures = [i for i, item in enumerate(items) if has_number(item.cell)]
    if len(figures) < 2:
        return _unsure("Only one year has a figure." if figures else "No figure in any year.")
    latest = figures[-1]
    block = [latest]
    for i in range(latest - 1, -1, -1):                         # walk back while years are on the same basis and in the same unit
        item = items[i]
        if (not has_number(item.cell) or item.column.basis != items[latest].column.basis
                or item.cell.unit != items[latest].cell.unit):
            break
        block.append(i)
    if len(block) == 1:
        return _unsure(_why_alone(items, latest))

    first = block[-1]
    first_fy, last_fy = items[first].column.fy, items[latest].column.fy
    result = compare(items[latest].cell, items[first].cell, info.better, shape, earlier=f"FY {first_fy}")
    chip_class, chip_text = CHIPS[result.verdict]
    if result.verdict == UNSURE:
        return chip_class, chip_text, result.reason
    if result.trust == CHECK and result.verdict in (IMPROVED, WORSE):
        chip_text += "*"
    text = f"{result.arrow} {result.change}".strip()
    if any(has_number(items[i].cell) for i in range(first)):
        text += f". Compared over FY {first_fy} to FY {last_fy}: earlier years use another basis or unit and are not included."
    return chip_class, chip_text, text


def _unsure(reason):
    chip_class, chip_text = CHIPS[UNSURE]
    return chip_class, chip_text, reason


def _why_alone(items, latest):
    if latest == 0:
        return "Only one year has a figure."
    before, now = items[latest - 1], items[latest]
    if not has_number(before.cell):
        return f"No figure for FY {before.column.fy}."
    if before.column.basis != now.column.basis:
        return (f"FY {before.column.fy} is on a different basis ({BASIS_TEXT[before.column.basis]} instead of "
                f"{BASIS_TEXT[now.column.basis]}), so the years cannot be compared.")
    return f"FY {before.column.fy} uses a different unit, so the years cannot be compared."


# ------------------------------------------------------------------------------------------------ every-figure tables
def _sebi_getter(key, current_only):
    def get(report, side):
        if current_only and side == "previous":
            return Cell()
        metric = report.metrics.get(key) or report.extras.get(key)
        return getattr(metric, side) if metric is not None else Cell()
    return get


def _question_tables(trend):
    """(tables, restatements, unit_gaps): unit_gaps counts, per year, the figures that state no unit."""
    tables, restatements, unit_gaps = [], [], Counter()
    for question in QUESTIONS:
        if question.kind == "table":
            rows = list(question.rows)
        elif question.kind == "yes_no":
            rows = [Row(f"{question.id}.answer", "Answer")]
        elif question.kind == "number":
            rows = [Row(f"{question.id}.value", "Percentage")]
        else:
            continue                                            # lists and facility tables stay in the one-year SEBI report
        current_only = question.kind != "table"
        views = []
        for row in rows:
            if row.header:
                views.append(RowView(row.label, [], heading=True))
                continue
            items = trend_cells(trend, _sebi_getter(row.key, current_only))
            views.append(_figure_row(row.label, items, current_only))
            for item in items:
                if item.cell.unit == UNIT_NOT_STATED and has_number(item.cell):
                    unit_gaps[item.column.fy] += 1
                if item.restated_to is not None:
                    restatements.append(_restatement(item, row.label, question))
        if any(not view.heading and any(c.css != "empty" for c in view.cells) for view in views):
            number = f"{'Essential' if question.section == ESSENTIAL else 'Leadership'} {question.number}"
            tables.append(QuestionTable(number, question.text, views))
    return tables, restatements, unit_gaps


def _figure_row(label, items, current_only):
    figures = [i.cell for i in items if has_number(i.cell)]
    row_unit = figures[-1].unit if figures else ""
    cells = []
    for item in items:
        cell = item.cell
        if item.column.source == NONE:
            cells.append(CellView("No filing", css="empty"))
        elif item.column.source == BORROWED and current_only:
            cells.append(CellView("Not in the previous-year column", css="empty"))
        elif cell.status == Status.NOT_REPORTED or cell.value is None:
            cells.append(CellView("Not reported", css="empty"))
        elif isinstance(cell.value, str):
            cells.append(CellView(cell.value))
        else:
            view = CellView(format_number_html(cell.value), unit="" if cell.unit == row_unit else cell.unit,
                            css="doubtful" if worst_kind(cell.warnings) == DOUBTFUL else "",
                            tags={Status.CALCULATED: ["calc."], Status.CONVERTED: ["conv."]}.get(cell.status, []))
            view.marks = _figure_marks(item)
            cells.append(view)
    return RowView(label, cells, unit=row_unit if row_unit != UNIT_NOT_STATED else "")


def _figure_marks(item):
    marks = []
    if item.restated_to is not None:
        marks.append(Mark("⟲", f"Restated: the FY {item.restated_in} filing gives {format_number(item.restated_to.value)} "
                               f"{item.restated_to.unit} for this year instead of {format_number(item.cell.value)}.", "restated"))
    if item.basis_differs:
        marks.append(Mark("≠", "The next filing is on a different reporting basis, so its figure for this year cannot be compared "
                               "with this one.", "basis"))
    if item.cell.warnings:
        label = "Doubtful figure" if worst_kind(item.cell.warnings) == DOUBTFUL else "Note on this figure"
        marks.append(Mark("ⓘ", f"{label}: " + " ".join(item.cell.warnings), "note"))
    return marks


def _restatement(item, label, question):
    old, new = item.cell.value, item.restated_to.value
    change = (new - old) / old * 100 if old else 0
    return (abs(change), Restatement(
        fy=item.column.fy, label=f"{label} ({'Essential' if question.section == ESSENTIAL else 'Leadership'} {question.number})",
        filed=f"{format_number(old)} {item.cell.unit}", restated=f"{format_number(new)} {item.restated_to.unit}",
        change=f"{friendly.percent_change_text(change)} {'higher' if change > 0 else 'lower'}" if old else "from 0", in_fy=item.restated_in))


# ------------------------------------------------------------------------------------------------ notes and summary
def _summary(trend, restated_count):
    name = short_name(trend.company_name)
    columns = trend.columns
    figured = [c for c in columns if c.report is not None]
    own = [c for c in columns if c.source == OWN]
    first, last = columns[0].fy, columns[-1].fy
    parts = [f"NSE has a BRSR filing for {name} for {len(own)} of the {len(columns)} years from FY {first} to FY {last}."]
    borrowed = [c for c in columns if c.source == BORROWED]
    if borrowed:
        parts.append(" ".join(f"FY {c.fy} has no filing of its own; its figures come from the previous-year column of the "
                              f"FY {c.borrowed_from} filing." for c in borrowed))
    changes = basis_changes(trend)
    bases = {c.basis for c in figured}
    if changes:
        parts.append(f"The reporting basis changes during this period ({_basis_phrase(changes)}), so only years on the same basis are compared.")
    elif len(bases) == 1 and "unknown" not in bases:
        parts.append(f"Every year is on a {BASIS_TEXT[bases.pop()].lower()} basis.")
    if restated_count:
        parts.append(f"{restated_count} figures were restated in a later filing (marked ⟲).")
    return " ".join(parts)


def _basis_phrase(changes):
    return "; ".join(f"{before_text.replace(' basis', '').lower()} in FY {before} to {after_text.replace(' basis', '').lower()} in FY {after}"
                     for before, after, before_text, after_text in changes)


def _notes(trend, restated_count, unit_gaps):
    notes = []
    for column in trend.columns:
        if column.source == OWN:
            continue
        kind = "missing" if column.kind == NOT_FILED else "unreadable"
        text = f"FY {column.fy}: {column.problem}" if column.problem else f"FY {column.fy}: no figures."
        if column.source == BORROWED:
            text += (f" The figures shown for FY {column.fy} are the previous-year column of the FY {column.borrowed_from} filing, "
                     "so yes/no answers and texts are not available for it.")
        else:
            text += " No figures are shown for this year."
        notes.append(Note(kind, text))
    for before, after, before_text, after_text in basis_changes(trend):
        notes.append(Note("basis", f"Reporting basis changed from “{before_text}” in FY {before} to “{after_text}” in FY {after}. "
                                   "Figures before and after the change describe different things, so trend verdicts only compare "
                                   "years on the same basis."))
    if unit_gaps:
        years = ", ".join(f"FY {fy} ({count} figures)" for fy, count in sorted(unit_gaps.items()))
        notes.append(Note("units", f"These years state no unit for some figures (older SEBI layout): {years}. They are shown as filed "
                                   "and not compared with years that state one."))
    if restated_count:
        notes.append(Note("restated", f"{restated_count} figures were changed by the filing of the following year (marked ⟲). "
                                      "Each figure is shown as filed in its own year; hover over ⟲ to see the later figure."))
    return notes
