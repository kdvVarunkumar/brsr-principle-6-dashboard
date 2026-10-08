"""Command-line interface of `python extract_report.py ...`: download if needed -> read -> clean -> print + save."""

import argparse
import sys

from brsr_p6.core.errors import BrsrError
from brsr_p6.extraction.report_io import save_report
from brsr_p6.views.report_text import render_text
from brsr_p6.workflows.pipeline import load_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract_report.py",
        description=(
            "Read a company's BRSR filing for one financial year, clean it into the SEBI Principle 6 layout, "
            "print it and save it as JSON in data/parsed/. Downloads the filing first if it is not on disk."
        ),
        epilog='Example: python extract_report.py --company Reliance --fy 2023-24 --questions E1,E6',
    )
    parser.add_argument("--company", required=True, help='Company name or NSE symbol, e.g. "Reliance" or TATASTEEL')
    parser.add_argument("--fy", required=True, help="Financial year, e.g. 2023-24")
    parser.add_argument("--questions", help="Only print these questions, e.g. E1,E6,L4 (default: all)")
    parser.add_argument("--quiet", action="store_true", help="Do not print the report, only save the JSON")
    parser.add_argument("--trace", action="store_true",
                        help="Under every value, print the filing's XBRL element(s) it was read from and the text exactly as filed")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # so symbols such as the rupee sign print on Windows

    try:
        report, download = load_report(args.company, args.fy)
    except BrsrError as exc:
        print(f"Error: {exc}")
        return 1

    saved = save_report(report)
    if not args.quiet:
        only = [q.strip().upper() for q in args.questions.split(",")] if args.questions else None
        print(render_text(report, only=only, trace=args.trace))
        print()
    print(f"Saved clean data to {saved}  (requests sent to NSE in this run: {download.requests_made})")
    return 0
