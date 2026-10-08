"""What an ERROR PAGE says.

When something goes wrong, `python main.py ...` still writes an HTML page (output/error_<company>_<year>.html) so the reason is
shown where the report would have been.  This module decides the words; templates/error.html only prints them
(the same "Python decides, the template prints" idea as sebi_view.py and dashboard_view.py).

Every error we raise on purpose (errors.py) carries its own specific sentence.  Here each kind of error also gets a plain title,
a few "what you can try" hints, and, where we know them, ready-to-run commands (the companies that matched, the years NSE has).
"""

from dataclasses import dataclass, field

from brsr_p6.core.errors import (AmbiguousCompany, BrsrError, FileNotAvailable, InvalidFiscalYear, InvalidYearRange, NoFilingFound,
                                 NSEUnavailable, UnknownCompany, UnparseableFiling, UnsupportedYear)
from brsr_p6.core.fiscal_year import parse_fiscal_year

EXAMPLE_YEAR = "2023-24"


@dataclass(frozen=True)
class ErrorInfo:
    kind: str          # the small label above the title
    title: str
    hints: tuple       # "what you can try"


@dataclass
class OptionView:
    label: str         # "Tata Steel Limited (TATASTEEL)" or "FY 2023-24"
    command: str       # a command to copy and run


@dataclass
class ErrorView:
    kind: str
    title: str
    message: str                                  # the specific sentence, exactly as the program raised it
    asked: str                                    # what the user typed
    hints: list
    options_title: str = ""                       # "Companies that match" / "Financial years NSE has for this company"
    options: list = field(default_factory=list)   # OptionView items
    technical: bool = False                       # True for an unexpected problem (a bug in this tool)


# One entry per kind of error.  (Order does not matter: the most specific class is looked up first.)
ERROR_INFO = {
    InvalidFiscalYear: ErrorInfo(
        "Financial year not understood", "We could not read that financial year",
        ("Write the year like 2023-24, meaning 1 April 2023 to 31 March 2024. 2023-2024, FY2023-24 and 2023/24 also work.",
         "BRSR filings exist for FY 2021-22 and later.")),
    UnsupportedYear: ErrorInfo(
        "Year too early", "BRSR filings start with FY 2021-22",
        ("BRSR reporting began with FY 2021-22 (for the top 1,000 listed companies), so nothing earlier exists. Try 2021-22 or later.",)),
    InvalidYearRange: ErrorInfo(
        "Year range not valid", "That range of years cannot be used",
        ("Give the earlier year first, for example --from 2021-22 --to 2025-26.",
         "BRSR filings exist for FY 2021-22 and later, and at most 10 years can be shown at a time.")),
    UnknownCompany: ErrorInfo(
        "Unknown company", "We could not find that company on NSE",
        ("Check the spelling, or type the company's NSE symbol (for example TATASTEEL, RELIANCE or INFY).",
         "Only companies listed on NSE can be found.")),
    AmbiguousCompany: ErrorInfo(
        "Several companies match", "Please choose one company",
        ("More than one company matches what you typed. Run the command again with the NSE symbol of the one you mean.",)),
    NoFilingFound: ErrorInfo(
        "No filing on NSE", "NSE has no BRSR filing for that company and year",
        ("Only the top 1,000 listed companies must file a BRSR, and only from FY 2021-22 onwards.",
         "A very recent year may simply not have been filed yet.")),
    NSEUnavailable: ErrorInfo(
        "NSE not reachable", "We could not get the data from NSE",
        ("Check your internet connection, then try again in a few minutes. NSE sometimes limits automated requests.",
         "Companies you have downloaded before keep working from the copy saved on disk. A company you have never downloaded needs "
         "the internet the first time.")),
    UnparseableFiling: ErrorInfo(
        "Filing could not be read", "The filing on NSE could not be read",
        ("The file is damaged, or it is not a BRSR XBRL file, so no figures can be read from it. We show nothing rather than guess.",
         "Try another financial year for the same company.",
         "The downloaded copy is kept under data/raw/. Delete that file and run again to download a fresh copy.")),
    FileNotAvailable: ErrorInfo(
        "File missing on NSE", "NSE lists this filing but the file is gone",
        ("Try another financial year, or try again later.",)),
    BrsrError: ErrorInfo("Problem", "We could not make this report", ("Check what you typed and try again.",)),
}

UNEXPECTED = ErrorInfo(
    "Unexpected problem", "Something unexpected went wrong",
    ("This is a bug in the tool, not a mistake in what you typed and not a problem with NSE.",
     "Run the same command again with --debug to see the technical details."),
)


def build_error_view(error, company_text="", fy_text="", tool="main"):
    """The ErrorView for an exception.  `company_text` and `fy_text` are what the user typed.

    `tool` is the command that failed ("main", "trends" or "summary"): the suggested commands then use that command."""
    if isinstance(error, BrsrError):
        info = next(ERROR_INFO[cls] for cls in type(error).__mro__ if cls in ERROR_INFO)
        message, unexpected = str(error), False
    else:                                                   # a bug: say so plainly, with the technical reason
        info = UNEXPECTED
        message, unexpected = f"{type(error).__name__}: {error}", True

    view = ErrorView(info.kind, info.title, message, _asked(company_text, fy_text), list(info.hints), technical=unexpected)
    if isinstance(error, AmbiguousCompany):
        view.options_title = "Companies that match what you typed"
        view.options = [OptionView(f"{c.name} ({c.symbol})", _command_for(tool, c.symbol, fy_text)) for c in error.candidates]
    elif isinstance(error, NoFilingFound) and error.symbol and error.available and tool == "trends":
        first, last = error.available[0], error.available[-1]
        view.options_title = "The years NSE has for this company"
        view.options = [OptionView(f"FY {first} to FY {last}", _trend_command(error.symbol, first, last))]
    elif isinstance(error, NoFilingFound) and error.symbol and error.available:
        view.options_title = "Financial years NSE has for this company"
        view.options = [OptionView(f"FY {fy}", _command(error.symbol, fy, _script(tool))) for fy in error.available]
    return view


def _asked(company_text, fy_text):
    parts = []
    if company_text:
        parts.append(f"Company: {company_text}")
    if fy_text:
        parts.append(f"Financial year: {fy_text}")
    return " · ".join(parts)


def _usable_year(fy_text):
    """The year the user typed if it is a real one, otherwise an example (so the suggested commands always work)."""
    try:
        return parse_fiscal_year(fy_text)
    except BrsrError:
        return EXAMPLE_YEAR


def _script(tool):
    return "summary.py" if tool == "summary" else "main.py"


def _command(symbol, fy, script="main.py"):
    return f'python {script} --company "{symbol}" --fy {fy}'


def _trend_command(symbol, first=None, last=None):
    years = f" --from {first} --to {last}" if first else ""
    return f'python trends.py --company "{symbol}"{years}'


def _command_for(tool, symbol, fy_text):
    """One command for one company, in the style of the command that failed."""
    if tool == "trends":
        return _trend_command(symbol)
    if tool == "summary":                                   # the summary picks the latest year by itself unless a real year was typed
        try:
            return _command(symbol, parse_fiscal_year(fy_text), "summary.py")
        except BrsrError:
            return f'python summary.py --company "{symbol}"'
    return _command(symbol, _usable_year(fy_text))
