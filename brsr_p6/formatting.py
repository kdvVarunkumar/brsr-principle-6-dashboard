"""Showing numbers to people.  The saved data keeps full precision; this only decides how a number LOOKS.

Indian reports group digits as 2,47,98,900 (lakh / crore style), so we do the same.
"""

import re

from markupsafe import Markup, escape


def indian_grouping(digits: str) -> str:
    """'24798900' -> '2,47,98,900'."""
    if len(digits) <= 3:
        return digits
    head, last_three = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [last_three])


def format_number(value) -> str:
    """Plain-text version of a number, e.g. 24798900.25 -> '2,47,98,900.25', 0.000446 -> '0.000446', 4.6e-6 -> '4.60e-06'."""
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    size = abs(value)
    if size >= 1:
        text = f"{size:.2f}".rstrip("0").rstrip(".")           # at most 2 decimals, no useless zeros
        whole, _, decimals = text.partition(".")
        return sign + indian_grouping(whole) + ("." + decimals if decimals else "")
    if size >= 1e-4:
        return sign + f"{size:.3g}"
    return sign + f"{size:.2e}"                                 # very small numbers: 4.60e-06


_SCIENTIFIC = re.compile(r"^(-?[\d.]+)e([+-])0*(\d+)$")


def format_number_html(value) -> Markup:
    """Same as format_number but small numbers are written as 4.60×10⁻⁶ (safe to put in a page)."""
    text = format_number(value)
    match = _SCIENTIFIC.match(text)
    if not match:
        return Markup(escape(text))
    mantissa, sign, exponent = match.groups()
    minus = "−" if sign == "-" else ""
    return Markup(f"{escape(mantissa)}×10<sup>{minus}{escape(exponent)}</sup>")
