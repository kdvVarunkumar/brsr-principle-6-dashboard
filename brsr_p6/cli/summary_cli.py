"""Command-line interface of `python flow.py summary`: what got better and what got worse since last year, as one HTML page.

Like the flow, a failure still writes a page (output/error_<company>_<year>.html) so the reason appears where the summary would have been.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.cli.common import explain_failure
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.pipeline import generate_summary_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow.py summary",
        description=(
            "Show the 3 biggest improvements and the 3 biggest setbacks in a listed Indian company's BRSR Principle 6 (environment) "
            "figures, compared with the year before, each explained in plain English. Without --fy the newest filing on NSE is used. "
            "Filings are downloaded from NSE if needed."
        ),
        epilog='Example: python flow.py summary --company "Tata Steel" --open',
    )
    parser.add_argument("--company", required=True, help='Company name or NSE symbol, e.g. "Tata Steel" or TATASTEEL')
    parser.add_argument("--fy", help="Financial year to summarise, e.g. 2025-26 (default: the newest filing NSE has)")
    parser.add_argument("--open", action="store_true", help="Open the finished page in your web browser")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for the page (default: output/)")
    parser.add_argument("--debug", action="store_true", help="On an unexpected problem, show the full technical traceback")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    fy_text = args.fy or "latest"

    try:
        page, report = generate_summary_page(args.company, args.fy, output_dir=args.output_dir, progress=print)
    except BrsrError as exc:
        return explain_failure(exc, args.company, fy_text, args.output_dir, args.open, tool="summary")
    except Exception as exc:                                    # a bug: explain it on a page too (--debug shows the traceback)
        if args.debug:
            raise
        return explain_failure(exc, args.company, fy_text, args.output_dir, args.open, tool="summary")

    print(f"\nSummary page for {report.company_name}, FY {report.fy} compared with FY {report.previous_fy}, written to: {page}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(page.as_uri())
    return 0
