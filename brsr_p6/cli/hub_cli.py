"""Command-line interface of hub.py: every page in a folder behind ONE page with a dropdown and a search box."""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.hub import generate_hub


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hub.py",
        description=(
            "Put every page in a folder (the reports, trend pages, summaries and error pages that main.py, trends.py and summary.py "
            "wrote) behind one page, index.html, with a search box and a dropdown to choose the page. "
            "By default every page is embedded, so index.html is one self-contained file."
        ),
        epilog="Example: python hub.py --open      (then, after running more commands, run it again to include the new pages)",
    )
    parser.add_argument("--dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Folder that holds the pages (default: output/)")
    parser.add_argument("--link", action="store_true",
                        help="Do not embed the pages: index.html only opens the files next to it (much smaller, but needs the folder)")
    parser.add_argument("--open", action="store_true", help="Open index.html in your web browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    made = generate_hub(args.dir, embed=not args.link)
    if made is None:
        print(f"There is no HTML page in {args.dir} yet. Make one first, for example:  python main.py --company \"Reliance\" --fy 2023-24")
        return 1
    path, count = made
    print(f"One page for all {count} pages ({'linked, not embedded' if args.link else 'embedded, one self-contained file'}) written to: {path}")
    print("Open it in your web browser (double-click the file), or run again with --open.")
    if args.open:
        webbrowser.open(path.as_uri())
    return 0
