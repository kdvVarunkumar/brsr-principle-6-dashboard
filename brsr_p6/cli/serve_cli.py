"""Command-line interface of `python flow.py serve`: the React Dashboard with the chat assistant (the work is in api/server.py)."""

import argparse
from pathlib import Path

from brsr_p6.api.server import DEFAULT_PORT, serve
from brsr_p6.core.paths import DEFAULT_RAW_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flow.py serve",
        description=("Open the React Dashboard (web/) at http://127.0.0.1:8000/ with the CopilotKit chat assistant. Serves the saved filings' "
                     "Dashboard data as JSON and starts the assistant's runtime. Read-only; stop it with Ctrl+C."),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port to listen on (default: {DEFAULT_PORT})")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR, help="Folder of saved filings (default: data/raw/)")
    parser.add_argument("--no-assistant", action="store_true", help="Do not start the assistant's runtime (only the page and the JSON)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the page in your web browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    serve(args.port, args.raw_dir, assistant=not args.no_assistant, open_browser=not args.no_open)
    return 0
