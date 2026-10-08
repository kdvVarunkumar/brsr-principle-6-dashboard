"""The one command of the project: `python flow.py`.

    python flow.py --company "Tata Steel" --fy 2025-26 --open     THE FLOW, end to end: download -> read -> clean and check -> write the report page
    python flow.py download ...                                    only the first step
    python flow.py extract ...                                     download if needed, read and clean, print as text, save the clean JSON
    python flow.py trends | summary | compare | hub | samples ...  the extensions, the viewer pages that hold them all, and the sample pages

Every other command is a sub-command of this one, so there is exactly one file to run.  If something goes wrong in the flow, it still writes a
page (output/error_<company>_<year>.html) that explains the problem, so the reason is shown where the report would have been.
"""

import argparse
import sys
import webbrowser
from pathlib import Path

from brsr_p6.cli import compare_cli, download_cli, extract_cli, hub_cli, samples_cli, summary_cli, trend_cli
from brsr_p6.cli.common import explain_failure
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.workflows.pipeline import generate_page

# the sub-commands: name -> (its main function, what it does).  `python flow.py <name> --help` shows that command's own options.
COMMANDS = {
    "download": (download_cli.main, "only download a company's filing(s) from NSE"),
    "extract": (extract_cli.main, "download if needed, read and clean one filing, print it as text, save the clean JSON"),
    "trends": (trend_cli.main, "one company over several years, side by side"),
    "summary": (summary_cli.main, "year-on-year: the 3 biggest improvements and setbacks"),
    "compare": (compare_cli.main, "two companies, one year, side by side"),
    "hub": (hub_cli.main, "the home page and the compare page that hold every generated page"),
    "samples": (samples_cli.main, "rebuild the committed sample pages in samples/"),
}


def _other_commands() -> str:
    width = max(len(name) for name in COMMANDS)
    lines = [f"  python flow.py {name:<{width}}  {what}" for name, (_, what) in COMMANDS.items()]
    return "Other commands (add --help to any of them for its options):\n" + "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Describe which options the flow accepts (this also powers `--help`)."""
    parser = argparse.ArgumentParser(
        prog="flow.py",
        description=(
            "The whole flow for a listed Indian company and a financial year: download its BRSR filing from NSE (if not already saved), "
            "read it, clean and check it, and write ONE HTML page with a plain-English dashboard and the SEBI-format Principle 6 report. "
            "If something goes wrong, an explanation page is written instead."
        ),
        epilog='Example: python flow.py --company "Tata Steel" --fy 2025-26 --open\n\n' + _other_commands(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
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


def run_flow(argv: list[str]) -> int:
    """The whole flow for one company and one year.  Returns 0 on success (the exit code the operating system sees)."""
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


def main(argv: list[str] | None = None) -> int:
    """`flow.py <command> ...` runs that command; anything else (or nothing) is the flow itself."""
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in COMMANDS:
        return COMMANDS[argv[0]][0](argv[1:])
    return run_flow(argv or ["--help"])        # a bare `python flow.py` shows the help, including the list of other commands
