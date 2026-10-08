"""Command-line interface of the download script (`python download_filings.py ...`)."""

import argparse
from pathlib import Path

from brsr_p6.core.errors import BrsrError
from brsr_p6.core.paths import PROJECT_ROOT
from brsr_p6.download.downloader import download_filings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="download_filings.py",
        description=(
            "Download a company's BRSR filings (XBRL, optionally PDF) from NSE into data/raw/<SYMBOL>/<FY>/. "
            "Files already on disk are reused; requests to NSE are paced politely."
        ),
        epilog=(
            'Examples:  python download_filings.py --company Reliance\n'
            '           python download_filings.py --company "Tata Steel" --fy 2023-24 --with-pdf'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--company", required=True, help='Company name or NSE symbol, e.g. "Reliance" or TATASTEEL')
    parser.add_argument("--fy", help="Only this financial year, e.g. 2023-24 (default: every year NSE has)")
    parser.add_argument("--with-pdf", action="store_true", help="Also download the PDF version (optional, for cross-checking)")
    parser.add_argument("--refresh", action="store_true", help="Ignore the saved filing list and ask NSE again")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = download_filings(args.company, fy=args.fy, include_pdf=args.with_pdf, refresh=args.refresh)
    except BrsrError as exc:  # every error we raise on purpose is a BrsrError with a ready-to-show message
        print(f"Error: {exc}")
        return 1

    print()
    print(f"Summary for {report.company.name} ({report.company.symbol})")
    for item in report.downloads:
        revised = f", revised {item.record.revision_date}" if item.record.revision_date else ""
        pdf = f", PDF {item.pdf_status}" if item.pdf_status else ""
        print(f"  FY {item.record.fy}: XML {item.xml_status}{pdf}, filed {item.record.submission_date}{revised}  -> {_short(item.xml_path)}")
        for note in item.notes:
            print(f"      note: {note}")
    if report.missing_years:
        print("  No BRSR filing on NSE for: " + ", ".join(f"FY {y}" for y in report.missing_years))
    print(f"  Requests sent to NSE in this run: {report.requests_made}")
    return 0


def _short(path: Path | None) -> str:
    if path is None:
        return "(no file)"
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)
