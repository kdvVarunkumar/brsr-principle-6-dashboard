"""The year-on-year summary: the 3 biggest improvements, the 3 biggest setbacks, and an honest list of what was left out.

How "better" is decided (the page states all of this in plain words, see DEFINITION):
  * "Better" only means better than the company's OWN figure for last year.  The filings contain no benchmark or legal limit.
  * Each figure has a direction (metric_info.py): lower is better for energy, greenhouse gases, water and waste per Rs of sales and
    for every air pollutant; higher is better for the renewable share of energy and the recycled share of waste.
  * A change under 1 % (a share: under half a percentage point) is "about the same" and is not ranked.
  * Amounts are ranked by their change in percent, shares by their change in percentage points.  (Ranking a share in percent would let
    a move from 0.07 % to 0.24 % beat a real improvement: it is a 269 % change but only 0.18 of a point.)
  * A total grows when a company grows, so where a per-Rs-of-sales figure exists it is ranked INSTEAD of the total, and the total is
    shown as context.  Otherwise one story would take two of the six places.
  * A figure that is missing, doubtful, in another unit or zero last year is not ranked: it is listed with the reason.
Both years come from the SAME filing (its previous-year column), so they are on the same reporting basis.
"""

from dataclasses import dataclass, field

from brsr_p6.analysis.comparison import HIGHER, IMPROVED, LOWER, SAME, SAME_WITHIN_PERCENT, SAME_WITHIN_POINTS, WORSE
from brsr_p6.analysis.trend_model import YearEntry, build_trend, trend_cells
from brsr_p6.core import friendly
from brsr_p6.core.formatting import format_number
from brsr_p6.views.dashboard_cards import CardView, build_card, figure_getter, per_crore
from brsr_p6.views.dashboard_view import short_name
from brsr_p6.views.metric_info import METRICS

TOP = 3                                  # how many improvements and how many setbacks are shown

DEFINITION = (
    "“Better” only means better than the company's own figures for last year. The filings contain no industry benchmark or legal limit, "
    "so a company is never rated against others.",
    "Each figure has a direction. Lower is better for energy, greenhouse gases, water and waste per ₹ of sales and for each air pollutant. "
    "Higher is better for the share of energy from renewable sources and the share of waste recycled or reused.",
    f"A change smaller than {SAME_WITHIN_PERCENT:g}% (for a share: smaller than {SAME_WITHIN_POINTS:g} of a percentage point) counts as "
    "“about the same” and is not ranked.",
    "Amounts are ranked by how much they changed in percent. Shares are ranked by how many percentage points they changed "
    "(a rise from 80% to 90% counts as 10).",
    "A company that grows will use more in total, so wherever a figure per ₹ of sales exists it is ranked instead of the total. "
    "The total is shown as context.",
    "Both years come from the same filing, so they use the same reporting basis. A figure that is missing, doubtful, in a different unit "
    "or was zero last year is not ranked; the page lists it with the reason.",
)

BETTER_HERE = {LOWER: "Lower is better here", HIGHER: "Higher is better here"}


# ------------------------------------------------------------------------------------------------ the objects
@dataclass
class Entry:
    rank: int
    card: CardView
    headline: str              # one plain sentence: what changed
    lines: list                # the numbers and what "better" means here
    notes: list = field(default_factory=list)      # context and caveats (the total, a restated figure)


@dataclass
class TableRow:
    title: str
    before: str
    now: str
    change: str                # "▼ 4.7%" or "▲ 0.18 points"
    chip_class: str
    chip_text: str
    shown: bool                # True when it is one of the entries above


@dataclass
class LeftOut:
    title: str
    reason: str


@dataclass
class SummaryView:
    company_name: str
    symbol: str
    fy: str
    previous_fy: str
    story: str
    definition: tuple
    best: list
    worst: list
    best_note: str             # said when there are fewer than 3 (or none)
    worst_note: str
    same: list                 # titles of the figures that stayed about the same
    table: list                # TableRow, best change first
    left_out: list             # LeftOut
    source_note: str
    improved: int = 0
    same_count: int = 0
    worse: int = 0


@dataclass
class _Candidate:
    info: object
    card: CardView
    score: float               # positive = better, in percent (amounts) or percentage points (shares)


# ------------------------------------------------------------------------------------------------ entry point
def build_summary_view(report, previous=None, previous_note=""):
    """`report` is the latest filing; `previous` (optional) is last year's own filing, used only to notice restated figures."""
    cards = {}
    for info in (i for i in METRICS if i.headline):
        card = build_card(report, info)
        if card is not None:
            cards[info.id] = (info, card)

    comparable = {i.id for i, c in cards.values() if c.verdict in (IMPROVED, WORSE, SAME)}
    replacement = {i.replaces: (i, c) for i, c in cards.values() if i.replaces and i.id in comparable}    # total id -> its per-sales figure

    ranked, same, left_out = [], [], []
    for info, card in cards.values():
        if info.id in replacement:
            left_out.append(LeftOut(card.title, _replaced_reason(card, replacement[info.id][1])))
        elif card.verdict in (IMPROVED, WORSE):
            ranked.append(_Candidate(info, card, card.change if info.better == HIGHER else -card.change))
        elif card.verdict == SAME and card.change is not None:
            same.append(_Candidate(info, card, card.change if info.better == HIGHER else -card.change))
        elif card.verdict == SAME:
            left_out.append(LeftOut(card.title, "Reported as 0 in both years, so there is nothing to compare."))
        else:
            left_out.append(LeftOut(card.title, card.trend))

    restated = _restated_figures(report, previous)
    best = sorted((c for c in ranked if c.card.verdict == IMPROVED), key=lambda c: -c.score)[:TOP]
    worst = sorted((c for c in ranked if c.card.verdict == WORSE), key=lambda c: c.score)[:TOP]
    entries_best = [_entry(n, c, cards, restated) for n, c in enumerate(best, 1)]
    entries_worst = [_entry(n, c, cards, restated) for n, c in enumerate(worst, 1)]

    counts = (sum(c.card.verdict == IMPROVED for c in ranked), len(same), sum(c.card.verdict == WORSE for c in ranked))
    shown = {c.card.id for c in best + worst}
    table = [_row(c, c.card.id in shown) for c in sorted(ranked + same, key=lambda c: -c.score)]
    name = short_name(report.company_name)
    return SummaryView(
        company_name=report.company_name, symbol=report.symbol, fy=report.fy, previous_fy=report.previous_fy,
        story=_story(name, report, entries_best, entries_worst, counts), definition=DEFINITION,
        best=entries_best, worst=entries_worst,
        best_note=_shortfall("improved", len(best), counts[0]), worst_note=_shortfall("got worse", len(worst), counts[2]),
        same=[_same_text(c, cards) for c in same], table=table, left_out=left_out,
        source_note=_source_note(report, previous, previous_note, [_title(c.card) for c in ranked + same if c.info.id in restated]),
        improved=counts[0], same_count=counts[1], worse=counts[2],
    )


# ------------------------------------------------------------------------------------------------ one entry
def _title(card):
    """The card's own title (it says 'per unit of sales' when the unit is unclear), plus the plain name of a pollutant."""
    return f"{card.title} ({card.name})" if card.name else card.title


def _tidy(text):
    """'0.2 unit not stated' reads badly; '0.2 (unit not stated)' does not."""
    return text.replace(" unit not stated", " (unit not stated)")


def _entry(rank, candidate, cards, restated):
    info, card = candidate.info, candidate.card
    return Entry(
        rank=rank, card=card, headline=_headline(info, card),
        lines=[_tidy(f"{card.previous_text}. This year: {card.quote}."),
               f"{BETTER_HERE[info.better]}, so this is {'an improvement' if card.verdict == IMPROVED else 'a step backwards'}."],
        notes=_notes(info, card, cards, restated.get(info.id)),
    )


def _headline(info, card):
    if info.shape == "share":
        before = card.previous_text.removeprefix("Last year: ")
        return f"{info.title} went {'up' if card.change > 0 else 'down'} from {before} to {card.big}%."
    return f"{_title(card)} was {card.delta_words}."


def _total_context(info, cards):
    """'For comparison, total energy used was 6.2% more than last year.' for a per-sales figure (else '')."""
    total = next((c for i, c in cards.values() if i.id == info.replaces), None) if info.replaces else None
    if total is None or not total.delta_words:
        return ""
    return f"For comparison, {total.title[0].lower() + total.title[1:]} was {total.delta_words}."


def _same_text(candidate, cards):
    """A figure that stayed about the same, with the total's story when the total moved more."""
    card = candidate.card
    before = card.previous_text.removeprefix("Last year: ")
    text = _tidy(f"{_title(card)}: {before} last year, {card.quote} this year.")
    context = _total_context(candidate.info, cards)
    return f"{text} {context}" if context else text


def _notes(info, card, cards, restated):
    notes = [_total_context(info, cards)] if _total_context(info, cards) else []
    if restated is not None:
        notes.append(f"Last year's own report gave {_cell_text(restated.cell)} for this; this year's filing restates it as "
                     f"{_cell_text(restated.restated_to)}. The comparison uses the newer figure.")
    return notes


def _cell_text(cell):
    return f"{format_number(cell.value)} {cell.unit}".strip()


def _replaced_reason(total_card, intensity_card):
    reason = f"Not ranked on its own: “{intensity_card.title}” is the fairer measure, because a total grows when a company grows."
    return reason + (f" For the record, it was {total_card.delta_words}." if total_card.delta_words else "")


# ------------------------------------------------------------------------------------------------ restated figures
def _restated_figures(report, previous):
    """{figure id: TrendCell} for the figures last year's OWN report gave differently from this year's filing (a restatement)."""
    if previous is None:
        return {}
    trend = build_trend(report.company_name, report.symbol, [YearEntry(previous.fy, previous), YearEntry(report.fy, report)])
    found = {}
    for info in (i for i in METRICS if i.headline):
        item = trend_cells(trend, figure_getter(info), per_crore if info.shape == "intensity" else None)[0]
        if item.restated_to is not None:
            found[info.id] = item
    return found


# ------------------------------------------------------------------------------------------------ table, story and notes
def _row(candidate, shown):
    card, info = candidate.card, candidate.info
    if card.change == 0:
        change = "no change"
    else:
        size = f"{friendly.points_text(card.change)} points" if info.shape == "share" else friendly.percent_change_text(card.change)
        change = f"{'▲' if card.change > 0 else '▼'} {size}"
    before = card.previous_text.removeprefix("Last year: ")
    return TableRow(_title(card), _tidy(before), _tidy(card.quote), change, card.chip_class, card.chip_text, shown)


def _shortfall(word, shown, total):
    if total == 0:
        return f"Nothing {word} by more than the “about the same” margin."
    if shown < TOP:
        return f"Only {shown} figure{'s' if shown != 1 else ''} {word}."
    return f"These are the {TOP} biggest of the {total} figures that {word}." if total > TOP else ""


def _story(name, report, best, worst, counts):
    improved, same, worse = counts
    if improved + same + worse == 0:
        return (f"None of {name}'s figures can be compared between FY {report.previous_fy} and FY {report.fy}: "
                "see the list at the bottom of the page for the reason for each.")
    parts = [f"We compared {improved + same + worse} figures for {name} between FY {report.previous_fy} and FY {report.fy}: "
             f"{improved} improved, {same} stayed about the same and {worse} got worse."]
    if best:
        parts.append(f"Biggest improvement: {best[0].headline}")
    if worst:
        parts.append(f"Biggest setback: {worst[0].headline}")
    return " ".join(parts)


def _source_note(report, previous, previous_note, restated_titles):
    base = (f"Last year's figures (FY {report.previous_fy}) are the previous-year column of the FY {report.fy} filing, "
            "so both years are on the same basis.")
    if previous is None:
        return base + (f" {previous_note} " if previous_note else " ") + "That column is the company's own figure for last year."
    if restated_titles:
        return base + (" Last year's own report was also checked. These figures were restated since, and the comparison uses the newer "
                       f"figure: {', '.join(restated_titles)}.")
    return base + " Last year's own report was also checked: none of the figures shown was restated."
