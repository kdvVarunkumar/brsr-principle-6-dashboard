"""Words for numbers on the dashboard.  The saved data keeps full precision; this only decides how a number is SAID.

Big numbers are written in lakh and crore (1 lakh = 1,00,000; 1 crore = 1,00,00,000), like the digit grouping of the SEBI tab.
"""

from brsr_p6.formatting import format_number, indian_grouping

LAKH = 100_000
CRORE = 10_000_000


def scale_for(value):
    """(divisor, word) for writing a big number: 46,42,00,812 -> (CRORE, 'crore'); 6,66,046 -> (LAKH, 'lakh'); 32,485 -> (1, '')."""
    size = abs(value)
    if size >= CRORE:
        return CRORE, "crore"
    if size >= LAKH:
        return LAKH, "lakh"
    return 1, ""


def number_text(value, divisor=1):
    """A number as people say it.  With a divisor (lakh / crore) always up to 2 decimals; otherwise the decimals depend on the size:
    32,485 · 807 · 65.5 · 3.77 · 0.17."""
    if divisor != 1:
        return _grouped(value / divisor, 2)
    size = abs(value)
    if size >= 100:
        return _grouped(value, 0)
    if size >= 10:
        return _grouped(value, 1)
    if size >= 1:
        return _grouped(value, 2)
    if size >= 1e-3:
        return f"{value:.2g}"
    return format_number(value)         # 0 and very small numbers


def _grouped(value, decimals):
    text = f"{abs(value):.{decimals}f}"
    whole, _, fraction = text.partition(".")
    fraction = fraction.rstrip("0")
    sign = "-" if value < 0 and (whole.strip("0") or fraction) else ""
    return sign + indian_grouping(whole) + ("." + fraction if fraction else "")


def share_text(percent):
    """A share of 0-100.  Small shares keep two decimals so a small change stays visible:
    97.055 -> '97.1', 1.471 -> '1.47', 0.031 -> '0.03', 0.004 -> '<0.01'."""
    if percent == 0:
        return "0"
    if round(percent, 1) == 100:
        return "100"
    if percent >= 10:
        return f"{percent:.1f}"
    if percent >= 0.01:
        return f"{percent:.2f}"
    return "<0.01"


def percent_change_text(change):
    """The size of a change in percent, without a sign: 2.0% · 0.15% · 240%."""
    size = abs(change)
    if size >= 100:
        return f"{size:.0f}%"
    if size < 1:
        return f"{size:.2f}%"
    return f"{size:.1f}%"


def points_text(points):
    """The size of a change in percentage points: 0.06 · 3.2"""
    size = abs(points)
    return f"{size:.1f}" if size >= 10 else f"{size:.2f}"


def unit_text(unit, word=""):
    """The unit as a reader should see it, with the lakh / crore word in front: ('GJ', 'crore') -> 'crore GJ'."""
    names = {"tCO2e": "tonnes CO2e", "(unit not stated)": "unit not stated"}
    text = names.get(unit, unit).replace("CO2", "CO₂")      # a proper subscript 2
    return f"{word} {text}".strip()
