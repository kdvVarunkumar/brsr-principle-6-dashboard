"""One figure of the dashboard -> one card.

A card is built in four small steps:
  1. find the figure's two cells (this year, last year) in the report, or calculate them from other rows;
  2. intensities are shown "per Rs 1 crore of sales" (the filed per-rupee number is too tiny to read);
  3. compare the two years (comparison.py);
  4. work out the words: big number, unit, trend, bars, badge, warnings and fine print.

Nothing here knows about HTML.  The template only prints what a CardView says.
"""

from dataclasses import dataclass, field

from brsr_p6.analysis.comparison import CONTEXT, CONTEXT_ONLY, HIGHER, IMPROVED, LOWER, SAME, UNSURE, WORSE, compare, has_number
from brsr_p6.analysis.warning_kinds import CHECK, DOUBTFUL, OK, only_coarse
from brsr_p6.core import friendly
from brsr_p6.core.formatting import format_number
from brsr_p6.core.models import Cell, Metric, Status
from brsr_p6.core.units import tidy_number
from brsr_p6.views.trace_view import figure_trace

# verdict -> (css class of the chip, words in the chip).  Words and symbols, never colour alone.
CHIPS = {
    IMPROVED: ("chip-good", "✔ Improved"),
    WORSE: ("chip-bad", "✖ Got worse"),
    SAME: ("chip-same", "≈ About the same"),
    CONTEXT_ONLY: ("chip-same", "ℹ Context only"),
    UNSURE: ("chip-unsure", "? Can’t compare"),
}
BETTER_LABELS = {LOWER: "Lower is better ↓", HIGHER: "Higher is better ↑", CONTEXT: "Context only"}

# units that are written in lakh / crore
SCALABLE_UNITS = ("GJ", "kL", "tonnes", "tCO2e")


@dataclass
class BarView:
    label: str          # the financial year
    percent: float      # width of the bar, 0-100 (bars always start at zero)
    text: str           # the number written next to the bar
    is_previous: bool


@dataclass
class CardView:
    id: str
    title: str
    size: str                 # "card" or "mini"
    name: str                 # mini cards: the plain name under the abbreviation
    better_label: str
    big: str                  # the big number, or "Not reported" / "Filed as 0"
    unit: str
    has_number: bool          # False: `big` is words, not a number
    verdict: str
    chip_class: str
    chip_text: str
    trend: str
    previous_text: str        # "Last year: 47.36 crore GJ"
    bars: list
    what: str
    why: str
    fine: list                # lines for the "Fine print" box
    alerts: list              # warnings in the filing's own words (plain English)
    badge: str
    trust: str                # warning_kinds.OK / CHECK / DOUBTFUL
    caveat: str = ""          # explains the * after a chip
    headline: bool = False    # counts in the scoreboard
    value: object = None      # the number shown (None when `big` is words)
    quote: str = ""           # "46.42 crore GJ": the value as a sentence would say it ("" when unusable)
    delta_words: str = ""     # "2.0% less than last year" ("" when we cannot compare)
    shared_alert: bool = False    # its warning is shown once under the topic instead of on this card
    change: float | None = None   # how much it changed: percent for amounts, percentage points for shares (None: not comparable)
    css: str = ""             # "doubtful" or "empty"
    trace: list = field(default_factory=list)   # "FY 2023-24: TotalEnergyConsumed = 375373200 Gigajoule", one line per year
    alert_title: str = "Check this figure."     # the bold words that start the warning box


# ------------------------------------------------------------------------------------------------ step 1: the figure
def reading(report, info):
    """The Metric (this year + last year) behind a card, or None when the card must be left out."""
    if info.source.startswith("derived:"):
        return _derive(report, info.source.partition(":")[2])
    metric = report.metrics.get(info.source) or report.extras.get(info.source)
    if metric is None and info.only_if_present:
        return None                       # an older edition of the form simply has no such item
    return metric or Metric(info.source, "")


def _derive(report, name):
    """A Metric calculated from other rows, the same way for both years.  The inputs' warnings travel with the result."""
    keys, calculate, describe, how, unit = DERIVED[name]
    metric = Metric("derived", "")
    for year in ("current", "previous"):
        cells = [getattr(report.metrics[key], year) for key in keys]
        if all(has_number(c) for c in cells) and len({c.unit for c in cells}) == 1:
            values = [c.value for c in cells]
            value = calculate(values)
            if value is not None:
                warnings, origin = [], []
                for cell in cells:
                    warnings += [w for w in cell.warnings if w not in warnings]
                    origin += cell.origin                                  # a calculated figure keeps the trace of every ingredient
                setattr(metric, year, Cell(value, unit or cells[0].unit, Status.CALCULATED, describe(values), how, warnings, origin))
    return metric


def _total(values):
    return sum(values)


def _first_as_percent_of_all(values):
    return values[0] / sum(values) * 100 if sum(values) else None


def _plus(values):
    return " + ".join(format_number(v) for v in values)


def _ratio(values):
    return f"{format_number(values[0])} ÷ ({_plus(values)})"


# figures calculated from other rows:  name -> (the rows, how to calculate, how to write the sum out, plain words, unit)
# (an empty unit means "the unit of the rows")
DERIVED = {
    "ghg_scope_1_2": (("E6.scope1", "E6.scope2"), _total, _plus, "Scope 1 + Scope 2", ""),
    "renewable_share": (("L1.re_total", "L1.nre_total"), _first_as_percent_of_all, _ratio,
                        "renewable energy ÷ (renewable + non-renewable energy)", "%"),
    "recovered_share": (("E8.recovered_total", "E8.disposed_total"), _first_as_percent_of_all, _ratio,
                        "waste recovered ÷ (recovered + disposed)", "%"),
}


# ------------------------------------------------------------------------------------------------ step 2: per Rs crore
def per_crore(cell):
    """A per-rupee intensity written per Rs 1 crore (x 10,000,000).  Only the unit changes; anything else is returned as it is."""
    if not has_number(cell) or not cell.unit.endswith(" per ₹"):
        return cell
    return Cell(tidy_number(cell.value * friendly.CRORE), cell.unit + " crore", cell.status, cell.as_filed, cell.note, cell.warnings, cell.origin)


def _is_per_crore(cell):
    """True when per_crore() really converted this cell (an intensity in an unclear unit is left as filed)."""
    return cell.unit.endswith(" per ₹ crore")


# ------------------------------------------------------------------------------------------------ steps 3 and 4: the card
def build_card(report, info):
    """The CardView for one figure, or None when the filing's edition has no such item."""
    metric = reading(report, info)
    if metric is None:
        return None
    filed_now, filed_before = metric.current, metric.previous
    now, before = filed_now, filed_before
    if info.shape == "intensity":
        now, before = per_crore(now), per_crore(before)

    comparison = compare(now, before, info.better, "share" if info.shape == "share" else "amount")
    divisor, word = _scale(info, now)
    chip_class, chip_text = CHIPS[comparison.verdict]
    caveat = ""
    if comparison.trust == CHECK and comparison.verdict in (IMPROVED, WORSE):
        chip_text += "*"
        caveat = "* This comparison relies on a figure that carries a note below."

    zero_not_real = has_number(now) and now.value == 0 and comparison.trust == DOUBTFUL     # e.g. an intensity "rounded away"
    both_zero = has_number(now) and has_number(before) and now.value == 0 and before.value == 0
    shown = has_number(now) and not zero_not_real
    big = _number(info, now, divisor) if shown else ("Filed as 0" if zero_not_real else "Not reported")
    unit = _unit(info, now, word) if shown else ""

    title = info.title
    if info.shape == "intensity" and has_number(now) and not _is_per_crore(now):
        title = info.title_as_filed or info.title        # the unit is unclear, so we cannot promise "per ₹ 1 crore"
    badge = "⚠ Check this figure · filed as 0" if zero_not_real else _badge(info, filed_now, now, comparison.trust)

    return CardView(
        id=info.id, title=title, size=info.size, name=info.name, better_label=BETTER_LABELS[info.better],
        big=big, unit=unit, has_number=shown, verdict=comparison.verdict, chip_class=chip_class, chip_text=chip_text,
        trend=_trend(info, comparison, before),
        previous_text=_previous_text(info, before, divisor, word),
        bars=_bars(report, info, now, before, divisor) if info.size == "card" and comparison.verdict != UNSURE else [],
        what=info.what, why=info.why,
        fine=_fine_print(report, info, metric, now, before),
        alerts=_alerts(now, before), badge=badge,
        trust=comparison.trust, caveat=caveat,
        headline=info.headline and not both_zero,        # "0 then, 0 now" says nothing about getting better or worse
        value=now.value if shown else None,
        quote=(big + ("" if unit.startswith("%") else " ") + unit).strip() if shown else "",
        delta_words=_delta_words(comparison),
        change=comparison.amount,
        css="doubtful" if comparison.trust == DOUBTFUL else ("empty" if not has_number(now) else ""),
        trace=figure_trace(report, _rows_behind(report, info, metric)),
        alert_title=_alert_title(comparison.trust, now.warnings + before.warnings),
    )


def _alert_title(trust, warnings):
    """What to call the warning box: a figure that is merely rounded too coarsely is not 'doubtful' (nobody made a mistake)."""
    if only_coarse(warnings):
        return "Too coarse to compare."
    return "Doubtful figure." if trust == DOUBTFUL else "Check this figure."


def _rows_behind(report, info, metric):
    """The SEBI row(s) a card's figure is read or calculated from (for its trace to the filing)."""
    if info.source.startswith("derived:"):
        return [report.metrics[key] for key in DERIVED[info.source.partition(":")[2]][0]]
    return [metric]


def figure_getter(info):
    """A function (report, side) -> Cell for one dashboard figure, side being "current" or "previous".

    Lets the trend and summary pages ask for the same figure the dashboard card shows, from any filing."""
    def get(report, side):
        metric = reading(report, info)
        return getattr(metric, side) if metric is not None else Cell()
    return get


def _scale(info, cell):
    """(divisor, word) for writing this card's numbers: lakh / crore only for plain amounts."""
    if has_number(cell) and info.shape == "amount" and cell.unit in SCALABLE_UNITS:
        return friendly.scale_for(cell.value)
    return 1, ""


def _number(info, cell, divisor):
    if info.shape == "share":
        return friendly.share_text(cell.value)
    return friendly.number_text(cell.value, divisor)


def _unit(info, cell, word):
    return info.unit_words if info.shape == "share" else friendly.unit_text(cell.unit, word)


def _trend(info, comparison, before):
    if comparison.verdict == UNSURE:
        return comparison.reason
    text = f"{comparison.arrow} {comparison.change}".strip()
    if info.shape == "share":
        text += f" (last year {friendly.share_text(before.value)}%)"
    return text


def _previous_text(info, before, divisor, word):
    if not has_number(before):
        return ""
    if info.shape == "share":
        return f"Last year: {friendly.share_text(before.value)}%"
    return f"Last year: {friendly.number_text(before.value, divisor)} {friendly.unit_text(before.unit, word)}"


def _bars(report, info, now, before, divisor):
    """This year against last year, both starting at zero.  Shares are drawn on a 0-100 scale, so a thin bar means a small share."""
    top = 100.0 if info.shape == "share" else max(now.value, before.value)
    if not top:
        return []
    bars = []
    for label, cell, is_previous in ((report.fy, now, False), (report.previous_fy, before, True)):
        if info.shape == "share":
            text = friendly.share_text(cell.value) + "%"
        else:
            text = friendly.number_text(cell.value, divisor)
        bars.append(BarView(label, cell.value / top * 100, text, is_previous))
    return bars


def _delta_words(comparison):
    """For headline sentences: '2.0% less than last year' / 'about the same as last year' / '' (cannot compare)."""
    if comparison.verdict == UNSURE:
        return ""
    if comparison.verdict == SAME:
        return "about the same as last year"
    if comparison.size:
        return f"{comparison.size} {'more' if comparison.rising else 'less'} than last year"
    return comparison.change[0].lower() + comparison.change[1:]


def _alerts(*cells):
    """The warnings of these cells in the filing's own plain-English words, each once."""
    alerts = []
    for cell in cells:
        alerts += [w for w in cell.warnings if w not in alerts]
    return alerts


def _badge(info, filed, shown, trust):
    """Where the number came from: one short line at the bottom of the card."""
    if not has_number(shown):
        if info.optional:
            return "∅ Not reported. This is an optional (Leadership) disclosure; “not reported” never means zero."
        return "∅ Not reported by the company. “Not reported” never means zero."
    if shown.status == Status.CALCULATED:
        source = "∑ Calculated by us from reported figures"
    elif info.shape == "intensity" and _is_per_crore(shown):
        source = "⇄ Reported by the company · " + ("unit changed by us · " if filed.status == Status.CONVERTED else "") + "shown per ₹ crore"
    elif shown.status == Status.CONVERTED:
        source = "⇄ Reported by the company · unit changed by us"
    else:
        source = "✔ Reported by the company"
    return ("⚠ Check this figure · " if trust != OK else "") + source


# ------------------------------------------------------------------------------------------------ fine print
def sebi_ref(key):
    """'E1.total' -> 'Essential 1';  'L4.scope3' -> 'Leadership 4';  'X.waste_rupee' -> 'an extra item in newer filings'."""
    kind, number = key[:1], key.partition(".")[0][1:]
    return {"E": f"Essential {number}", "L": f"Leadership {number}"}.get(kind, "an extra item in newer filings")


def _both_years(now, before):
    """'46,42,00,812 GJ (last year 47,35,90,585)': full numbers, Indian digit grouping."""
    text = f"{format_number(now.value)} {now.unit}".strip()
    if has_number(before):
        text += f" (last year {format_number(before.value)})"
    return text


def _fine_print(report, info, metric, now, before):
    lines = []
    if has_number(now):
        if info.shape == "intensity" and _is_per_crore(now):
            last = f" (last year {metric.previous.as_filed})" if has_number(metric.previous) else ""
            lines.append(f"Filed as {metric.current.as_filed}{last}. We show it per ₹ crore (× {friendly.CRORE:,}); only the unit changed.")
        elif now.status == Status.CALCULATED:
            last = f" (last year {before.as_filed})" if has_number(before) else ""
            lines.append(f"Calculated by us: {now.note}. This year: {now.as_filed}{last}.")
        elif now.status == Status.CONVERTED and now.as_filed:
            last = f" (last year {before.as_filed})" if has_number(before) else ""
            lines.append(f"Filed as {now.as_filed}{last}. We changed the unit to {now.unit}.")
        else:
            lines.append(f"Filed as {_both_years(now, before)}.")
    for label, key in info.also:
        other = report.metrics.get(key)
        if other is not None and has_number(other.current):
            lines.append(f"Also in the filing: {label}: {_both_years(other.current, other.previous)}.")
    lines.append(_source_line(info, metric))
    return lines


def _source_line(info, metric):
    if info.source.startswith("derived:"):
        keys = DERIVED[info.source.partition(":")[2]][0]
        return "Source in the SEBI tab: " + " and ".join(sorted({sebi_ref(key) for key in keys})) + "."
    return f"Source in the SEBI tab: {sebi_ref(info.source)}, “{metric.label}”."
