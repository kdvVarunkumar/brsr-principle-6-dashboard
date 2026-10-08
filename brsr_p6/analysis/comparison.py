"""This year against last year: is it better, worse, about the same, or can we not tell?

"Better" only ever means "better than the company's OWN figure last year".  There is no rating against other companies or legal
limits, because the filing contains neither.  Rules (see context.md D38 and D41):

  * a doubtful figure (warning_kinds.DOUBTFUL) is never compared (this includes an intensity rounded to one digit: too coarse);
  * a missing figure is never compared (and is never treated as 0);
  * two years in different units are never compared;
  * amounts count as "about the same" within +-1 %, shares within +-0.5 percentage points.
"""

from dataclasses import dataclass

from brsr_p6.analysis.warning_kinds import DOUBTFUL, OK, only_coarse, worst_kind
from brsr_p6.core.friendly import percent_change_text, points_text
from brsr_p6.core.models import Status

# which direction is better
LOWER, HIGHER, CONTEXT = "lower", "higher", "context"

# the answer
IMPROVED, WORSE, SAME, CONTEXT_ONLY, UNSURE = "improved", "worse", "same", "context", "unsure"

SAME_WITHIN_PERCENT = 1.0     # amounts
SAME_WITHIN_POINTS = 0.5      # shares (percentage points)
NO_CHANGE = 0.005             # a change that rounds to "0.00" is simply "no change"


@dataclass
class Comparison:
    verdict: str            # IMPROVED / WORSE / SAME / CONTEXT_ONLY / UNSURE
    arrow: str = ""         # "▲", "▼" or "" (nothing to point at)
    change: str = ""        # "2.0% lower than last year"
    reason: str = ""        # when UNSURE: why we cannot tell
    trust: str = OK         # warning_kinds.OK / CHECK / DOUBTFUL for the two figures together
    size: str = ""          # how big the change is: "2.0%" or "0.06 percentage points" ("" when it has no size)
    rising: bool = False    # True when this year's figure is higher
    amount: float | None = None   # the signed size of the change: percent for amounts, percentage points for shares (None: no size)


def has_number(cell):
    """True when the cell holds a real number (a missing figure is never a number)."""
    return cell.status != Status.NOT_REPORTED and isinstance(cell.value, (int, float))


def trust_of(*cells):
    """How much to trust the figures in these cells, from the warnings they carry."""
    return worst_kind([w for cell in cells for w in cell.warnings])


def compare(current, previous, better, shape="amount", earlier="last year"):
    """Compare two cells.  `better` is LOWER, HIGHER or CONTEXT; `shape` is "amount" or "share" (a percentage).

    `earlier` is how the older figure is called in the words: "last year" on the one-year page, "FY 2023-24" on a trend page."""
    trust = trust_of(current, previous)
    reason = _why_not(current, previous, trust, earlier)
    if reason:
        return Comparison(UNSURE, reason=reason, trust=trust)

    now, before = current.value, previous.value
    if shape == "share":
        points = now - before
        if abs(points) < NO_CHANGE:
            return Comparison(SAME, change=f"No change from {earlier}", trust=trust, amount=0.0)
        same = abs(points) < SAME_WITHIN_POINTS
        rising = points > 0
        size = f"{points_text(points)} percentage points"
        change = f"{size} {'above' if rising else 'below'} {earlier}"
    else:
        if before == 0:
            if now == 0:
                return Comparison(SAME, change="No change: 0 in both years", trust=trust)
            # A percentage of zero does not exist.  And a 0 last year may simply mean "not measured", so we do not guess.
            return Comparison(UNSURE, reason=f"{earlier[:1].upper() + earlier[1:]}'s figure was 0, so a percentage change cannot be worked out.", trust=trust)
        percent = (now - before) / before * 100
        if abs(percent) < NO_CHANGE:
            return Comparison(SAME, change=f"No change from {earlier}", trust=trust, amount=0.0)
        same = abs(percent) < SAME_WITHIN_PERCENT
        rising = percent > 0
        size = percent_change_text(percent)
        change = f"{size} {'higher' if rising else 'lower'} than {earlier}"

    amount = points if shape == "share" else percent
    return Comparison(_verdict(rising, same, better), "▲" if rising else "▼", change, trust=trust, size=size, rising=rising, amount=amount)


def _verdict(rising, same, better):
    if same:
        return SAME
    if better == CONTEXT:
        return CONTEXT_ONLY
    good = rising if better == HIGHER else not rising
    return IMPROVED if good else WORSE


def _why_not(current, previous, trust, earlier="last year"):
    """The reason these two cells cannot be compared, or "" when they can."""
    if trust == DOUBTFUL:
        if only_coarse(current.warnings + previous.warnings):
            return "Filed with one digit of precision, so too coarse to compare with another year."
        return "The figure looks doubtful, so we do not compare it."
    if not has_number(current) and not has_number(previous):
        return "No figure for either year."
    if not has_number(current):
        return "No figure for this year."
    if not has_number(previous):
        return f"No figure for {earlier}."
    if current.unit != previous.unit:
        return "The two years use different units."
    return ""
