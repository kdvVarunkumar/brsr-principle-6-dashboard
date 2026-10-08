"""Financial-year helpers.

An Indian financial year runs 1 April to 31 March, so "2023-24" means 1 Apr 2023 to 31 Mar 2024.
We always use the short canonical form "2023-24" for folder names and messages.
"""

import re

from brsr_p6.errors import InvalidFiscalYear, UnsupportedYear

# The assignment only covers FY 2021-22 and later.
EARLIEST_START_YEAR = 2021

# Accepts: 2023-24, 2023-2024, FY2023-24, FY 2023-24, 2023/24 (case-insensitive).
_FY_PATTERN = re.compile(r"^(?:FY)?\s*(\d{4})\s*[-/]\s*(\d{4}|\d{2})$", re.IGNORECASE)


def format_fiscal_year(start_year: int, end_year: int) -> str:
    """(2023, 2024) -> '2023-24'."""
    return f"{start_year}-{end_year % 100:02d}"


def previous_fiscal_year(fy: str) -> str:
    """'2023-24' -> '2022-23'."""
    start = int(fy[:4])
    return format_fiscal_year(start - 1, start)


def parse_fiscal_year(text: str) -> str:
    """Turn what the user typed into the canonical 'YYYY-YY' form, or raise a clear error."""
    match = _FY_PATTERN.match((text or "").strip())
    if not match:
        raise InvalidFiscalYear(
            f"'{text}' is not a financial year I understand. Use a form like 2023-24 (1 Apr 2023 to 31 Mar 2024)."
        )

    start = int(match.group(1))
    end_text = match.group(2)
    if len(end_text) == 4:
        end = int(end_text)
    else:  # two digits, e.g. '24' -> same century as the start year
        end = (start // 100) * 100 + int(end_text)
        if end < start:
            end += 100

    if end != start + 1:
        raise InvalidFiscalYear(
            f"'{text}' is not a valid financial year: the two years must be consecutive (for example 2023-24)."
        )

    if start < EARLIEST_START_YEAR:
        raise UnsupportedYear(
            f"FY {format_fiscal_year(start, end)} is earlier than FY 2021-22. "
            "This tool only covers BRSR filings for FY 2021-22 and later."
        )

    return format_fiscal_year(start, end)
