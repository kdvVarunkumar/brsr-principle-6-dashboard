"""A small read-only web server (standard library only).

    GET /api/filings                       {"TATASTEEL": ["2022-23", ...], ...}   what is saved on disk
    GET /api/dashboard?symbol=X&fy=2023-24 the Dashboard of that filing (see dashboard_json.dashboard_to_dict)
    GET /  and the files next to it        the built React app (web/dist, made by `npm run build` in web/)

It listens on this computer only (127.0.0.1) and answers only GET requests.  Problems come back as {"error": "..."} with a 4xx status.
"""

import json
import mimetypes
import re
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from brsr_p6.api.assistant import start_runtime
from brsr_p6.api.dashboard_json import available_filings, dashboard_to_dict
from brsr_p6.core.errors import BrsrError
from brsr_p6.core.fiscal_year import parse_fiscal_year
from brsr_p6.core.paths import DEFAULT_RAW_DIR, WEB_DIR
from brsr_p6.workflows.pipeline import load_saved_report

DEFAULT_PORT = 8000
ALLOWED_ORIGIN = re.compile(r"^http://(localhost|127\.0\.0\.1)(:\d+)?$")   # a page on this computer (for example the Vite dev server)
mimetypes.add_type("text/javascript", ".js")


def answer(path: str, raw_dir: Path = DEFAULT_RAW_DIR):
    """(status, JSON-ready body) for an /api/ request path.  No server involved, so it is easy to test."""
    url = urlparse(path)
    query = {key: values[0] for key, values in parse_qs(url.query).items()}
    if url.path == "/api/filings":
        return HTTPStatus.OK, available_filings(raw_dir)
    if url.path == "/api/dashboard":
        symbol = query.get("symbol", "").strip().upper()
        if not symbol or "fy" not in query:
            return HTTPStatus.BAD_REQUEST, {"error": "Both symbol and fy are needed, e.g. /api/dashboard?symbol=TATASTEEL&fy=2023-24"}
        try:
            fy = parse_fiscal_year(query["fy"])
        except BrsrError as problem:
            return HTTPStatus.BAD_REQUEST, {"error": str(problem)}
        report = load_saved_report(symbol, fy, raw_dir)
        if report is None:
            return HTTPStatus.NOT_FOUND, {"error": f"No saved filing for {symbol} {fy}. Run: python flow.py download --company {symbol} --fy {fy}"}
        return HTTPStatus.OK, dashboard_to_dict(report)
    return HTTPStatus.NOT_FOUND, {"error": "Unknown address. Try /api/filings or /api/dashboard?symbol=X&fy=YYYY-YY"}


def app_file(url_path: str, dist_dir: Path) -> Path | None:
    """The built React file for a URL path ('/' is index.html), or None.  Nothing outside dist_dir can be reached."""
    dist = Path(dist_dir).resolve()
    wanted = (dist / (unquote(url_path).lstrip("/") or "index.html")).resolve()
    return wanted if wanted.is_relative_to(dist) and wanted.is_file() else None


def respond(path: str, raw_dir: Path, dist_dir: Path):
    """(status, content type, bytes) for any request path: JSON for /api/, otherwise a file of the built React app."""
    url_path = urlparse(path).path
    if not url_path.startswith("/api/"):
        file = app_file(url_path, dist_dir)
        if file is not None:
            return HTTPStatus.OK, mimetypes.guess_type(file.name)[0] or "application/octet-stream", file.read_bytes()
        if url_path == "/":
            message = {"error": "The React app is not built yet: run `npm install` and `npm run build` in web/ (see web/README.md)."}
            return HTTPStatus.NOT_FOUND, "application/json; charset=utf-8", json.dumps(message).encode("utf-8")
    status, body = answer(path, raw_dir)
    return status, "application/json; charset=utf-8", json.dumps(body, ensure_ascii=False).encode("utf-8")


def make_handler(raw_dir: Path, dist_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            status, content_type, payload = respond(self.path, raw_dir, dist_dir)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            origin = self.headers.get("Origin", "")
            if ALLOWED_ORIGIN.match(origin):
                self.send_header("Access-Control-Allow-Origin", origin)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):    # keep the terminal quiet
            pass

    return Handler


def serve(port: int = DEFAULT_PORT, raw_dir: Path = DEFAULT_RAW_DIR, web_dir: Path = WEB_DIR, assistant: bool = True, open_browser: bool = True) -> None:
    """Run until Ctrl+C.  With assistant=True the CopilotKit runtime is started too (and stopped again at the end)."""
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(raw_dir, Path(web_dir) / "dist"))
    runtime = None
    if assistant:
        runtime, message = start_runtime(web_dir)
        print(message)
    print(f"Open http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    if open_browser:
        webbrowser.open(f"http://127.0.0.1:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if runtime is not None:
            runtime.terminate()
