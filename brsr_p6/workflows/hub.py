"""Gather every page of a folder into the two viewer pages: the part that reads files.

The pages are made by main.py, trends.py, summary.py, compare.py (and the error pages by any of them).  This reads whatever HTML pages the
folder holds, hands them to views/hub_view.py to be named and grouped, and writes the viewers next to them:

    index.html                one company at a time (its report, summary and trend)
    compare_companies.html    two companies in one year (only when the folder holds at least one comparison)
"""

from pathlib import Path

from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.rendering.render import compare_hub_page_path, write_compare_hub_page, write_hub_page
from brsr_p6.views.hub_view import HUB_TITLE, VIEWER_FILES, build_compare_hub_view, build_hub_view
from brsr_p6.workflows.compare import generate_all_comparisons


def read_pages(folder: Path):
    """[(file name, HTML text)] of every page in the folder except the two viewers themselves, in name order."""
    paths = sorted(p for p in Path(folder).glob("*.html") if p.name not in VIEWER_FILES)
    return [(p.name, p.read_text(encoding="utf-8")) for p in paths]


def generate_hub(folder: Path = DEFAULT_OUTPUT_DIR, embed=True, title=HUB_TITLE, compare=False):
    """Write <folder>/index.html (and compare_companies.html).  Returns (path of index.html, number of pages), or None when the folder has no page yet.

    embed=True puts every page inside its viewer (each viewer is one self-contained file); embed=False only names the files next to it.
    compare=True first writes a comparison page for every pair of companies that have a report page for the same year in the folder
    (from the filings already on disk), so the compare page can offer "company A vs company B".  Needs no internet."""
    if compare:
        generate_all_comparisons(folder)
    pages = read_pages(folder)
    if not pages:
        return None
    index = write_hub_page(build_hub_view(pages, embed, title), Path(folder))
    comparisons = build_compare_hub_view(pages, embed, title)
    if comparisons.entries:
        write_compare_hub_page(comparisons, Path(folder))
    else:
        compare_hub_page_path(Path(folder)).unlink(missing_ok=True)       # an old compare page would offer comparisons that are gone
    return index, len(pages)
