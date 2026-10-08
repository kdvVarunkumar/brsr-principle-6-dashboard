"""Command-line interface of `python flow.py hub`: every page in a folder behind a home page (choose a company) and a compare page (choose two companies)."""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.rendering.render import compare_hub_page_path
from brsr_p6.workflows.hub import generate_hub


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow.py hub",
        description=(
            "Put every page in a folder (the reports, trend pages, summaries, comparisons and error pages that the other commands "
            "wrote) behind a home page, index.html, where you choose a company and a year, and a compare page, "
            "compare_companies.html, where you choose two companies (a button on the home page opens it). "
            "By default every page is embedded, so each of the two is one self-contained file; keep them in the same folder."
        ),
        epilog="Example: python flow.py hub --open      (then, after running more commands, run it again to include the new pages)",
    )
    parser.add_argument("--dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder that holds the pages (default: output/)")
    parser.add_argument("--link", action="store_true",
                        help="Do not embed the pages: index.html only opens the files next to it (much smaller, but needs the folder)")
    parser.add_argument("--only-existing", "--no-compare", dest="only_existing", action="store_true",
                        help="Only gather the pages that already exist. By default the pages the two viewers would lack are made first, "
                             "from the filings already on disk (no internet): a comparison for every pair of companies with a report for the "
                             "same year, and a year-on-year summary and a multi-year trend for companies that have none. "
                             "(--no-compare is the older name of this option.)")
    parser.add_argument("--open", action="store_true", help="Open index.html in your web browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    made = generate_hub(args.dir, embed=not args.link, fill=not args.only_existing)
    if made is None:
        print(f"There is no HTML page in {args.dir} yet. Make one first, for example:  python flow.py --company \"Reliance\" --fy 2023-24")
        return 1
    path, count = made
    print(f"One page for all {count} pages ({'linked, not embedded' if args.link else 'embedded, one self-contained file'}) written to: {path}")
    compare_page = compare_hub_page_path(args.dir)
    if compare_page.exists():
        print(f"The page for comparing two companies (the button on that page opens it; keep the two files together): {compare_page}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(path.as_uri())
    return 0
