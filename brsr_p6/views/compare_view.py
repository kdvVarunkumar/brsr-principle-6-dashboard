"""Two companies, one financial year, side by side (Extension 3).

How to compare FAIRLY (the page says all of this in words, see DEFINITION):
  * Totals (energy, water, waste, emissions) depend on how BIG a company is, so they are shown and never ranked.  The fair measures are the
    figures per Rs 1 crore of sales and the shares (renewable energy, recycled waste): only these get a "lower / higher" verdict.
  * Both numbers of a row are written in the same unit and the same scale (lakh / crore), so they can be read across at a glance.
  * A figure one company did not report is "Not reported", never 0, and its row is not compared.
  * Different or missing units, doubtful figures and figures rounded too coarsely are shown as filed and not compared.
  * Companies can report on different bases (standalone or consolidated): the page says which, and warns when they differ.
The comparison itself reuses analysis/comparison.py, the same rules as the dashboard (the second company plays the part of "last year").
"""

from dataclasses import dataclass, field

from brsr_p6.analysis.comparison import IMPROVED, SAME, WORSE, compare, has_number, trust_of
from brsr_p6.analysis.warning_kinds import DOUBTFUL
from brsr_p6.core import friendly
from brsr_p6.core.models import Cell
from brsr_p6.views.dashboard_cards import BETTER_LABELS, SCALABLE_UNITS, per_crore, reading
from brsr_p6.views.dashboard_view import short_name
from brsr_p6.views.metric_info import METRICS, TOPICS_BY_ID

DEFINITION = (
    "Both companies are read for the same financial year, each from its own filing on NSE.",
    "Totals (energy, water, waste, emissions) depend on how big a company is, so they are shown but not ranked. The fair measures are the "
    "figure per ₹ 1 crore of sales and the shares (renewable energy, recycled waste): only these get a “lower” or “higher” verdict.",
    "“Better” means lower for energy, greenhouse gases, water and waste per ₹ of sales, and higher for the renewable and recycled shares. "
    "Within 1% (for a share: half a percentage point) counts as “about the same”.",
    "Every figure is in one standard unit (GJ, kL, tonnes, tCO₂e), and the two numbers in a row use the same scale. A figure whose unit a "
    "company did not state is shown as filed but not compared.",
    "A figure a company did not report is shown as “Not reported”, never as 0, and that row is not compared. A figure that looks doubtful, "
    "or is rounded too coarsely, is shown as filed but not compared.",
    "Companies in different industries use energy, water and materials very differently, so a lower figure is not by itself a sign of better "
    "effort. Nothing is rated against a benchmark or a legal limit: the filings contain none.",
)

CHIP_GOOD, CHIP_SAME, CHIP_UNSURE = "chip-good", "chip-same", "chip-unsure"
MIN_SHARED_SCALE = 0.1      # the smaller number of a row must still be at least 0.1 of the shared lakh / crore unit


@dataclass
class FigureView:
    text: str                  # "62.38", "Not reported", "Filed as 0"
    unit: str = ""             # "crore GJ", "GJ per ₹ crore", "% of all energy"
    css: str = ""              # "missing" or "doubtful"
    warned: bool = False       # the figure carries a note


@dataclass
class ResultView:
    chip_class: str
    chip_text: str
    detail: str = ""
    winner: str = ""           # "a", "b", "same" or "" (not compared)


@dataclass
class RowView:
    title: str
    fair: bool                 # True: gets a verdict (per-sales figure or share); False: a total, shown for size only
    better: str                # "Lower is better ↓"
    a: FigureView
    b: FigureView
    result: ResultView


@dataclass
class TopicView:
    id: str
    name: str
    rows: list


@dataclass
class CompanyFacts:
    name: str
    short: str
    symbol: str
    boundary: str
    filed: str
    source_file: str
    source_url: str


@dataclass
class CompareView:
    fy: str
    a: CompanyFacts
    b: CompanyFacts
    story: str
    a_better: int
    b_better: int
    same: int
    unsure: int
    definition: tuple
    basis_note: str
    topics: list
    notes_a: list = field(default_factory=list)      # [(the figures it applies to, the note)]
    notes_b: list = field(default_factory=list)


# ------------------------------------------------------------------------------------------------ entry point
def build_compare_view(report_a, report_b):
    """`report_a` and `report_b` are the two companies' Principle6Reports for the SAME financial year."""
    a, b = _facts(report_a), _facts(report_b)
    topics, notes_a, notes_b = [], {}, {}
    for info in (i for i in METRICS if i.headline):
        cell_a, cell_b = _current(report_a, info), _current(report_b, info)
        if info.only_if_present and reading(report_a, info) is None and reading(report_b, info) is None:
            continue                                     # an item neither company's edition of the form has
        row = _row(info, cell_a, cell_b, a.short, b.short)
        for cell, notes in ((cell_a, notes_a), (cell_b, notes_b)):
            for warning in cell.warnings:
                notes.setdefault(warning, []).append(row.title)
        if not topics or topics[-1].id != info.topic:
            topics.append(TopicView(info.topic, TOPICS_BY_ID[info.topic].name, []))
        topics[-1].rows.append(row)

    fair = [row for topic in topics for row in topic.rows if row.fair]
    count = lambda winner: sum(row.result.winner == winner for row in fair)           # noqa: E731
    a_better, b_better, same = count("a"), count("b"), count("same")
    unsure = len(fair) - a_better - b_better - same
    return CompareView(
        fy=report_a.fy, a=a, b=b, story=_story(a.short, b.short, report_a.fy, a_better, b_better, same, unsure),
        a_better=a_better, b_better=b_better, same=same, unsure=unsure, definition=DEFINITION,
        basis_note=_basis_note(report_a.boundary, report_b.boundary, a.short, b.short), topics=topics,
        notes_a=_notes(notes_a), notes_b=_notes(notes_b),
    )


# ------------------------------------------------------------------------------------------------ one row
def _current(report, info):
    """This year's Cell of a dashboard figure (an intensity per Rs crore), or an empty cell when the filing has none."""
    metric = reading(report, info)
    cell = metric.current if metric is not None else Cell()
    return per_crore(cell) if info.shape == "intensity" else cell


def _row(info, cell_a, cell_b, name_a, name_b):
    divisor, word = _common_scale(info, cell_a, cell_b)
    return RowView(
        title=info.title if not info.name else f"{info.title} ({info.name})", fair=info.shape != "amount", better=BETTER_LABELS[info.better],
        a=_figure(cell_a, info, divisor, word), b=_figure(cell_b, info, divisor, word),
        result=_result(info, cell_a, cell_b, name_a, name_b),
    )


def _common_scale(info, cell_a, cell_b):
    """(divisor, word) so both numbers of a row use the same lakh / crore scale (the bigger one decides)."""
    cells = [c for c in (cell_a, cell_b) if has_number(c)]
    if info.shape == "amount" and cells and len({c.unit for c in cells}) == 1 and cells[0].unit in SCALABLE_UNITS:
        divisor, word = friendly.scale_for(max(abs(c.value) for c in cells))
        smallest = min((abs(c.value) for c in cells if c.value), default=0)
        if not smallest or smallest / divisor >= MIN_SHARED_SCALE:
            return divisor, word
    return 1, ""                      # otherwise full numbers: "1,88,23,457" and "790", never "1.88 crore" next to "0 crore"


def _figure(cell, info, divisor, word):
    if not has_number(cell):
        return FigureView("Not reported", css="missing")
    doubtful = trust_of(cell) == DOUBTFUL
    if doubtful and cell.value == 0 and info.shape == "intensity":
        return FigureView("Filed as 0", css="doubtful", warned=True)          # an intensity of 0 is rounding, not a measurement
    if info.shape == "share":
        text, unit = friendly.share_text(cell.value), info.unit_words
    else:
        text, unit = friendly.number_text(cell.value, divisor), friendly.unit_text(cell.unit, word)
    return FigureView(text, unit, css="doubtful" if doubtful else "", warned=bool(cell.warnings))


def _result(info, cell_a, cell_b, name_a, name_b):
    if info.shape == "amount":                                                # a total: size only, never ranked
        if not (has_number(cell_a) and has_number(cell_b)):
            return ResultView(CHIP_UNSURE, "? Not compared", _missing_text(cell_a, cell_b, name_a, name_b))
        return ResultView(CHIP_SAME, "Depends on size", _size_text(cell_a, cell_b, name_a, name_b))

    comparison = compare(cell_a, cell_b, info.better, "share" if info.shape == "share" else "amount", earlier=name_b)
    if comparison.verdict in (IMPROVED, WORSE):
        a_wins = comparison.verdict == IMPROVED
        word = "lower" if info.better == "lower" else "higher"
        times = _times_text(cell_a, cell_b, name_a, name_b, 2) if info.shape == "intensity" else ""        # a share is better said in points
        detail = times or f"{name_a} is {comparison.change}"
        return ResultView(CHIP_GOOD, f"✔ {name_a if a_wins else name_b} is {word}", detail, "a" if a_wins else "b")
    if comparison.verdict == SAME:
        same = "Identical figures" if comparison.change.startswith("No change") else f"{name_a} is {comparison.change}"
        return ResultView(CHIP_SAME, "≈ About the same", same, "same")
    return ResultView(CHIP_UNSURE, "? Can’t compare", _reason(comparison.reason, cell_a, cell_b, name_a, name_b))


def _reason(reason, cell_a, cell_b, name_a, name_b):
    """compare() talks about 'years'; here the two things compared are two companies."""
    if reason == "The two years use different units.":
        return f"The two companies state different units ({cell_a.unit} and {cell_b.unit}), so they cannot be compared."
    if reason == "No figure for this year.":
        return f"{name_a} did not report this."
    if reason == f"No figure for {name_b}.":
        return f"{name_b} did not report this."
    if reason == "No figure for either year.":
        return "Neither company reported this."
    return reason.replace("with another year", "with another company")


def _missing_text(cell_a, cell_b, name_a, name_b):
    if not has_number(cell_a) and not has_number(cell_b):
        return "Neither company reported this."
    return f"{name_a if not has_number(cell_a) else name_b} did not report this."


def _size_text(cell_a, cell_b, name_a, name_b):
    """'Tata Steel's figure is 6.4 times Wipro's' for a total, only when both are in the same unit and neither looks doubtful."""
    if cell_a.unit != cell_b.unit:
        return f"The two companies state different units ({cell_a.unit} and {cell_b.unit})."
    if trust_of(cell_a, cell_b) == DOUBTFUL:
        return "Not compared: a figure looks doubtful."
    if not cell_a.value and not cell_b.value:
        return "Both companies reported 0."
    if not cell_a.value or not cell_b.value:
        return f"{name_a if not cell_a.value else name_b} reported 0."
    return _times_text(cell_a, cell_b, name_a, name_b, 1.05) or "About equal in size"


def _times_text(cell_a, cell_b, name_a, name_b, minimum):
    """'Tata Steel's figure is 589 times Wipro's' when the figures differ by at least this factor ('' when they are closer or not positive)."""
    if not (cell_a.value and cell_b.value) or cell_a.value < 0 or cell_b.value < 0:
        return ""
    ratio = cell_a.value / cell_b.value
    big, small, times = (name_a, name_b, ratio) if ratio >= 1 else (name_b, name_a, 1 / ratio)
    return f"{big}'s figure is {friendly.number_text(times)} times {small}'s" if times >= minimum else ""


# ------------------------------------------------------------------------------------------------ the page's words
def _facts(report):
    return CompanyFacts(report.company_name, short_name(report.company_name), report.symbol, report.boundary,
                        report.submission_date or "date not available", report.source_file, report.source_url)


def _story(name_a, name_b, fy, a_better, b_better, same, unsure):
    fair = a_better + b_better + same + unsure
    if not (a_better + b_better + same):
        return (f"None of the {fair} fair measures could be compared between {name_a} and {name_b} for FY {fy}: "
                "see the rows below for the reason in each case.")
    return (f"We compared {name_a} and {name_b} for FY {fy} on {fair} fair measures (per ₹ 1 crore of sales, and shares): "
            f"{name_a} is better on {a_better}, {name_b} is better on {b_better}, {same} are about the same and {unsure} could not be compared. "
            "Totals are shown for size but not ranked.")


def _basis(boundary):
    text = (boundary or "").lower()
    return "standalone" if "standalone" in text else "consolidated" if "consolidated" in text else ""


def _basis_note(boundary_a, boundary_b, name_a, name_b):
    basis_a, basis_b = _basis(boundary_a), _basis(boundary_b)
    if basis_a and basis_a == basis_b:
        return ""
    if basis_a and basis_b:
        return (f"{name_a} reports on a {basis_a} basis and {name_b} on a {basis_b} basis, so their figures do not cover the same scope "
                "(a consolidated figure includes the subsidiaries). Totals are not like-for-like; read the per-₹ figures and shares with care.")
    missing = name_a if not basis_a else name_b
    return f"{missing} does not state whether its figures are standalone or consolidated, so the two may not cover the same scope."


def _notes(by_warning):
    return [(", ".join(dict.fromkeys(titles)), warning) for warning, titles in by_warning.items()]
