"""Command-line interface of `python flow.py compare`: two companies, one financial year, side by side, as one HTML page.

Like the flow, a failure still writes a page (output/error_<companies>_<year>.html) so the reason appears where the comparison would have been.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.cli.common import explain_failure
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.compare import generate_comparison_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow.py compare",
        description=(
            "Compare two listed Indian companies' BRSR Principle 6 (environment) figures for ONE financial year, side by side. "
            "Totals are shown but not ranked (a bigger company uses more); the verdicts are on the fair measures: the figure per "
            "rupee of sales and the shares. Units are made the same, and anything a company did not report is said so. "
            "Filings are downloaded from NSE if needed."
        ),
        epilog='Example: python flow.py compare --company-a "Tata Steel" --company-b "Wipro" --fy 2025-26 --open',
    )
    parser.add_argument("--company-a", required=True, help='First company: name or NSE symbol, e.g. "Tata Steel" or TATASTEEL')
    parser.add_argument("--company-b", required=True, help='Second company, e.g. "Wipro" or WIPRO')
    parser.add_argument("--fy", required=True, help="The financial year, the same for both, e.g. 2025-26 (FY 2021-22 or later)")
    parser.add_argument("--open", action="store_true", help="Open the finished page in your web browser")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for the page (default: output/)")
    parser.add_argument("--debug", action="store_true", help="On an unexpected problem, show the full technical traceback")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    asked = f"{args.company_a} vs {args.company_b}"

    try:
        page, report_a, report_b = generate_comparison_page(args.company_a, args.company_b, args.fy, output_dir=args.output_dir, progress=print)
    except BrsrError as exc:
        return explain_failure(exc, asked, args.fy, args.output_dir, args.open, tool="compare")
    except Exception as exc:                                    # a bug: explain it on a page too (--debug shows the traceback)
        if args.debug:
            raise
        return explain_failure(exc, asked, args.fy, args.output_dir, args.open, tool="compare")

    print(f"\nComparison page for {report_a.company_name} and {report_b.company_name}, FY {report_a.fy}, written to: {page}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(page.as_uri())
    return 0
