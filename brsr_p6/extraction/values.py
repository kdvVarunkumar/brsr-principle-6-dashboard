"""Small cleaners for the raw text found in a filing (numbers, yes/no answers, free text)."""

import re

NOTHING = ("", "-", "--", "na", "n/a", "nil", "none", "null", "not applicable", "not available")


def clean_number(text):
    """'1,83,595' -> 183595.0, '12.5' -> 12.5.  'NA', '-', '' or anything unreadable -> None (never 0)."""
    if text is None:
        return None
    cleaned = str(text).strip().replace(",", "").replace(" ", "")
    if cleaned.lower() in NOTHING:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def significant_digits(text):
    """How many digits of precision a number written as text has: '0.0000000004' -> 1, '0.0000004786' -> 4, '4e-10' -> 1, '0.20' -> 2.

    Leading zeros never count.  Trailing zeros count after a decimal point ('0.20' was written to two digits) but not in a whole
    number ('1200' may be rounded to the hundred).  Unreadable text or zero -> 0."""
    mantissa = re.split(r"[eE]", str(text).strip().replace(",", ""))[0].lstrip("+-")
    if not re.fullmatch(r"\d*\.?\d*", mantissa):
        return 0
    if "." in mantissa:
        return len(mantissa.replace(".", "").lstrip("0"))
    return len(mantissa.lstrip("0").rstrip("0"))


def clean_yes_no(text):
    """Return (answer, understood).  'true'/'Yes'/'Y' -> 'Yes';  'false'/'No' -> 'No';  'NA'... -> 'Not applicable'.
    Anything else is returned unchanged with understood=False, so the caller can warn."""
    raw = (text or "").strip()
    word = raw.lower()
    if word in ("yes", "y", "true"):
        return "Yes", True
    if word in ("no", "n", "false"):
        return "No", True
    if word in NOTHING:
        return "Not applicable", True
    return raw, False


def clean_text(text):
    """Squeeze blank space; return None when there is nothing to show."""
    text = " ".join((text or "").split())
    return text or None
