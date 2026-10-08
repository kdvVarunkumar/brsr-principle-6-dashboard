"""Command-line interface of `python flow.py trends`: one company over several financial years, as one HTML page.

Like the flow, a failure still writes a page (output/error_<company>_<years>.html) so the reason appears where the report would have been.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.cli.common import explain_failure
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.pipeline import generate_trend_page


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow.py trends",
        description=(
            "Show how a listed Indian company's BRSR Principle 6 (environment) figures changed over several financial years, "
            "side by side. Missing years are flagged (never skipped or filled with zero), changes of reporting basis and "
            "restated figures are marked. Filings are downloaded from NSE if needed."
        ),
        epilog='Example: python flow.py trends --company "Tata Steel" --from 2021-22 --to 2025-26 --open',
    )
    parser.add_argument("--company", required=True, help='Company name or NSE symbol, e.g. "Tata Steel" or TATASTEEL')
    parser.add_argument("--from", dest="fy_from", help="First financial year, e.g. 2021-22 (default: FY 2021-22, the first BRSR year)")
    parser.add_argument("--to", dest="fy_to", help="Last financial year, e.g. 2025-26 (default: the newest filing NSE has)")
    parser.add_argument("--open", action="store_true", help="Open the finished page in your web browser")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for the page (default: output/)")
    parser.add_argument("--debug", action="store_true", help="On an unexpected problem, show the full technical traceback")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    years_text = f"{args.fy_from or 'earliest'} to {args.fy_to or 'latest'}"

    try:
        page, trend = generate_trend_page(args.company, args.fy_from, args.fy_to, output_dir=args.output_dir, progress=print)
    except BrsrError as exc:
        return explain_failure(exc, args.company, years_text, args.output_dir, args.open, tool="trends")
    except Exception as exc:                                    # a bug: explain it on a page too (--debug shows the traceback)
        if args.debug:
            raise
        return explain_failure(exc, args.company, years_text, args.output_dir, args.open, tool="trends")

    first, last = trend.columns[0].fy, trend.columns[-1].fy
    print(f"\nTrend page for {trend.company_name}, FY {first} to FY {last}, written to: {page}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(page.as_uri())
    return 0
