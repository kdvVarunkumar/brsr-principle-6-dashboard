"""Fill the HTML templates with a Principle6Report and write the page.

Jinja2 is a "mail-merge for HTML": the templates in brsr_p6/templates/ contain the page layout with placeholders
like {{ report.fy }}, and Jinja2 replaces them with real values.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from brsr_p6.dashboard_view import build_dashboard_view
from brsr_p6.downloader import PROJECT_ROOT, safe_name
from brsr_p6.sebi_view import build_sebi_view

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"


def _environment():
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),   # text from filings is escaped, so it can never inject HTML or scripts
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_page(report) -> str:
    """The complete HTML page (as text) for one report."""
    sebi = build_sebi_view(report)
    dash = build_dashboard_view(report)
    return _environment().get_template("base.html").render(report=report, sebi=sebi, dash=dash)


def write_page(report, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Write output/<SYMBOL>_<FY>.html and return its path."""
    path = output_dir / f"{safe_name(report.symbol)}_{report.fy}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_page(report), encoding="utf-8")
    return path


def render_error_page(view) -> str:
    """The HTML of an error page (an ErrorView from error_view.py)."""
    return _environment().get_template("error.html").render(view=view)


def error_page_path(company_text, fy_text, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """output/error_<company>_<year>.html.  The 'error_' start means an error page can never overwrite a real report page."""
    company = safe_name(company_text.strip())[:40] or "unknown"
    year = safe_name(fy_text.strip())[:12] or "year"
    return output_dir / f"error_{company}_{year}.html"


def write_error_page(view, company_text, fy_text, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = error_page_path(company_text, fy_text, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_error_page(view), encoding="utf-8")
    return path
