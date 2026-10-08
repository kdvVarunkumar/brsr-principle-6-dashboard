"""Fill the HTML templates with a Principle6Report and write the page.

Jinja2 is a "mail-merge for HTML": the templates in brsr_p6/rendering/templates/ contain the page layout with placeholders
like {{ report.fy }}, and Jinja2 replaces them with real values.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR, safe_name
from brsr_p6.views.compare_view import build_compare_view
from brsr_p6.views.dashboard_view import build_dashboard_view
from brsr_p6.views.hub_view import COMPARE_FILE, HOME_FILE
from brsr_p6.views.sebi_view import build_sebi_view
from brsr_p6.views.summary_view import build_summary_view
from brsr_p6.views.trace_view import build_trace_view
from brsr_p6.views.trend_view import build_trend_view

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"      # brsr_p6/rendering/templates/, next to this file


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
    trace = build_trace_view(report)
    return _environment().get_template("base.html").render(report=report, sebi=sebi, dash=dash, trace=trace)


def write_page(report, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """Write output/<SYMBOL>_<FY>.html and return its path."""
    path = output_dir / f"{safe_name(report.symbol)}_{report.fy}.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_page(report), encoding="utf-8")
    return path


def render_trend_page(trend) -> str:
    """The HTML of the multi-year trend page for a Trend (trend_model.py)."""
    return _environment().get_template("trends.html").render(view=build_trend_view(trend))


def trend_page_name(symbol, first_fy, last_fy) -> str:
    return f"{safe_name(symbol)}_trend_{first_fy}_to_{last_fy}.html"


def trend_page_path(trend, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """output/<SYMBOL>_trend_<first year>_to_<last year>.html"""
    return output_dir / trend_page_name(trend.symbol, trend.columns[0].fy, trend.columns[-1].fy)


def write_trend_page(trend, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = trend_page_path(trend, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_trend_page(trend), encoding="utf-8")
    return path


def render_summary_page(report, previous=None, previous_note="") -> str:
    """The HTML of the year-on-year summary for the latest report (last year's own filing and the reason it may be missing are optional)."""
    view = build_summary_view(report, previous, previous_note)
    return _environment().get_template("summary.html").render(view=view)


def summary_page_path(report, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """output/<SYMBOL>_summary_<FY>.html"""
    return output_dir / f"{safe_name(report.symbol)}_summary_{report.fy}.html"


def write_summary_page(report, previous=None, previous_note="", output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = summary_page_path(report, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_summary_page(report, previous, previous_note), encoding="utf-8")
    return path


HUB_FILE_NAME = HOME_FILE                    # the viewer of single companies: output/index.html, samples/index.html
COMPARE_HUB_FILE_NAME = COMPARE_FILE         # the viewer of two companies, one click away from it


def render_hub_page(view) -> str:
    """The HTML of the index page: choose a company and a year (a HubView from hub_view.py)."""
    return _environment().get_template("hub.html").render(view=view)


def hub_page_path(folder: Path = DEFAULT_OUTPUT_DIR) -> Path:
    return folder / HUB_FILE_NAME


def write_hub_page(view, folder: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = hub_page_path(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_hub_page(view), encoding="utf-8")
    return path


def render_compare_hub_page(view) -> str:
    """The HTML of the compare page: choose a year and two companies (a CompareHubView from hub_view.py)."""
    return _environment().get_template("compare_hub.html").render(view=view)


def compare_hub_page_path(folder: Path = DEFAULT_OUTPUT_DIR) -> Path:
    return folder / COMPARE_HUB_FILE_NAME


def write_compare_hub_page(view, folder: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = compare_hub_page_path(folder)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_compare_hub_page(view), encoding="utf-8")
    return path


def render_compare_page(report_a, report_b) -> str:
    """The HTML of the two-company comparison (both reports are for the same financial year)."""
    return _environment().get_template("compare.html").render(view=build_compare_view(report_a, report_b))


def compare_page_path(report_a, report_b, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """output/<SYMBOL A>_vs_<SYMBOL B>_<FY>.html"""
    return output_dir / f"{safe_name(report_a.symbol)}_vs_{safe_name(report_b.symbol)}_{report_a.fy}.html"


def write_compare_page(report_a, report_b, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = compare_page_path(report_a, report_b, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_compare_page(report_a, report_b), encoding="utf-8")
    return path


def render_error_page(view) -> str:
    """The HTML of an error page (an ErrorView from error_view.py)."""
    return _environment().get_template("error.html").render(view=view)


def error_page_path(company_text, fy_text, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    """output/error_<company>_<year>.html.  The 'error_' start means an error page can never overwrite a real report page."""
    company = safe_name(company_text.strip())[:40] or "unknown"
    year = safe_name(fy_text.strip())[:24] or "year"
    return output_dir / f"error_{company}_{year}.html"


def write_error_page(view, company_text, fy_text, output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    path = error_page_path(company_text, fy_text, output_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_error_page(view), encoding="utf-8")
    return path
