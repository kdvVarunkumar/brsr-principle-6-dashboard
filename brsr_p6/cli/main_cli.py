"""Command-line interface of main.py: reads what the user typed after `python main.py` and makes the report page.

If anything goes wrong, the same command still writes a page (output/error_<company>_<year>.html) that explains the problem,
so the reason is shown where the report would have been.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.cli.common import explain_failure
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.pipeline import generate_page


def build_parser() -> argparse.ArgumentParser:
    """Describe which options the program accepts (this also powers `--help`)."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Generate a BRSR Principle 6 (environment) report page for a listed Indian company: a plain-English dashboard "
            "and a SEBI-format report in one HTML file. The filing is downloaded from NSE if needed. "
            "If something goes wrong, an explanation page is written instead."
        ),
        epilog='Example: python main.py --company "Tata Steel" --fy 2023-24 --open',
    )
    parser.add_argument(
        "--company",
        required=True,
        help='Company name or NSE symbol, e.g. "Tata Steel" or TATASTEEL',
    )
    parser.add_argument(
        "--fy",
        required=True,
        help="Financial year, e.g. 2023-24 (FY 2021-22 or later)",
    )
    parser.add_argument("--open", action="store_true", help="Open the finished page in your web browser")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder for the page (default: output/)")
    parser.add_argument("--debug", action="store_true", help="On an unexpected problem, show the full technical traceback")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the program. Returns 0 on success (the exit code the operating system sees)."""
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # so symbols such as the rupee sign print on Windows

    try:
        page, report = generate_page(args.company, args.fy, output_dir=args.output_dir, progress=print)
    except BrsrError as exc:   # every error we raise on purpose carries a message meant for the user
        return explain_failure(exc, args.company, args.fy, args.output_dir, args.open)
    except Exception as exc:   # anything else is a bug.  This is the outermost layer, so it is the right place to catch it.
        if args.debug:
            raise
        return explain_failure(exc, args.company, args.fy, args.output_dir, args.open)

    print(f"\nReport page written to: {page}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(page.as_uri())
    return 0
