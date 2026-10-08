"""Gather every page of a folder into the one viewer page (index.html): the part that reads files.

The pages are made by main.py, trends.py, summary.py (and the error pages by any of them).  This reads whatever HTML pages the folder
holds, hands them to views/hub_view.py to be named and grouped, and writes the viewer next to them.
"""

from pathlib import Path

from brsr_p6.core.paths import DEFAULT_OUTPUT_DIR
from brsr_p6.rendering.render import HUB_FILE_NAME, write_hub_page
from brsr_p6.views.hub_view import HUB_TITLE, build_hub_view
from brsr_p6.workflows.compare import generate_all_comparisons


def read_pages(folder: Path):
    """[(file name, HTML text)] of every page in the folder except the viewer itself, in name order."""
    paths = sorted(p for p in Path(folder).glob("*.html") if p.name != HUB_FILE_NAME)
    return [(p.name, p.read_text(encoding="utf-8")) for p in paths]


def generate_hub(folder: Path = DEFAULT_OUTPUT_DIR, embed=True, title=HUB_TITLE, compare=False):
    """Write <folder>/index.html.  Returns (path, number of pages), or None when the folder has no page yet.

    embed=True puts every page inside index.html (one self-contained file); embed=False only names the files next to it.
    compare=True first writes a comparison page for every pair of companies that have a report page for the same year in the folder
    (from the filings already on disk), so the viewer can offer "company A vs company B".  Needs no internet."""
    if compare:
        generate_all_comparisons(folder)
    pages = read_pages(folder)
    if not pages:
        return None
    return write_hub_page(build_hub_view(pages, embed, title), Path(folder)), len(pages)
