"""Command-line interface of `python flow.py samples`: rebuild the committed sample pages in samples/ (the work is in workflows/samples.py)."""

import argparse
import sys

from brsr_p6.workflows.samples import make_samples


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="flow.py samples",
        description=("Rebuild the sample pages in samples/ (reports, trends, summaries, comparisons, error pages and the two viewer pages) "
                     "from the filings saved in data/raw/. Run it after changing a template or a rule; a test fails if the committed samples are out of date."),
    )


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pages = make_samples()
    print(f"\n{len(pages)} sample pages are in the samples/ folder (see samples/README.md).")
    return 0
