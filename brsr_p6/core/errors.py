"""Custom errors. Each one carries a specific, human-readable message that the program shows to the user.

Why custom errors instead of plain `Exception`?
  * The code that catches them can tell *what* went wrong (unknown company vs. NSE down).
  * The message is the exact text we show, so users get a helpful explanation, not a Python traceback.
"""


class BrsrError(Exception):
    """Base class: every error we raise on purpose is a BrsrError."""


class InvalidFiscalYear(BrsrError):
    """The financial year text could not be understood (e.g. 'banana')."""


class UnsupportedYear(BrsrError):
    """A valid financial year, but earlier than FY 2021-22 (out of scope for this project)."""


class InvalidYearRange(BrsrError):
    """A multi-year request whose start year is after its end year, or that spans too many years."""


class UnknownCompany(BrsrError):
    """No NSE-listed equity matches the text the user typed."""


class AmbiguousCompany(BrsrError):
    """Several different companies match; the user must pick one (we list them)."""

    def __init__(self, message, candidates):
        super().__init__(message)
        self.candidates = candidates


class NoFilingFound(BrsrError):
    """NSE has no BRSR filing for this company / financial year.

    `symbol` and `available` (the financial years NSE does have, e.g. ["2022-23", "2023-24"]) let the error page offer
    ready-to-run commands instead of only a sentence.
    """

    def __init__(self, message, symbol="", available=()):
        super().__init__(message)
        self.symbol = symbol
        self.available = list(available)


class SameCompany(BrsrError):
    """A comparison was asked between a company and itself."""


class NSEUnavailable(BrsrError):
    """NSE could not be reached, refused the request, or returned something unexpected."""


class UnparseableFiling(BrsrError):
    """The downloaded file is not a readable SEBI BRSR XBRL file (broken XML, wrong kind of file...)."""


class FileNotAvailable(BrsrError):
    """NSE lists a file but the address no longer exists (HTTP 404/410). Only that one file is affected."""
