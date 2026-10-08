"""The "all pages in one place" viewer: which pages there are, what each is called and how they are grouped.

Every command writes its own HTML page (a report, a trend page, a summary, an error page).  The hub puts them all behind one page with a
search box and a dropdown.  This module decides the names and the order (plain Python, no files, no HTML); workflows/hub.py reads the
folder and templates/hub.html prints the result.

Two ways to hold a page:
    embedded  the page's whole HTML travels inside the hub file, so the hub is ONE self-contained file you can move or send
    linked    the hub only names the file next to it (tiny, but it needs the folder)
"""

import html
import json
import re
from dataclasses import dataclass, field

REPORTS, COMPARISONS, SUMMARIES, TRENDS, ERRORS, OTHER = ("Reports", "Company comparisons", "Year-on-year summaries", "Multi-year trends",
                                                          "Error pages", "Other pages")
HUB_TITLE = "BRSR Principle 6: Environmental Dashboard"     # the name in the header of the viewer
SAMPLES_TITLE = HUB_TITLE + " (sample reports)"
KINDS = (REPORTS, COMPARISONS, SUMMARIES, TRENDS, ERRORS, OTHER)          # the order of the groups (the comparisons are not in the main dropdown, they have their own)

_REPORT_NAME = re.compile(r"^.+_\d{4}-\d{2}$")                # TATASTEEL_2025-26
_COMPARE_NAME = re.compile(r"^(?P<a>.+?)_vs_(?P<b>.+)_(?P<fy>\d{4}-\d{2})$")                    # TATASTEEL_vs_WIPRO_2025-26
_COMPARE_TITLE = re.compile(r"^(?P<a>.+?) vs (?P<b>.+?): .*FY (?P<fy>\d{4}-\d{2})")           # Tata Steel Limited vs Wipro Limited: ... FY 2025-26


@dataclass
class HubEntry:
    id: str                    # the file name without ".html": also the link to this page (index.html#TATASTEEL_2025-26)
    file: str
    label: str                 # what the dropdown shows
    kind: str                  # one of KINDS
    search: str                # lower-case text the search box looks in
    html: str | None = None    # the page itself when embedded
    compare: dict | None = None    # a comparison page: {fy, a, b (symbols), a_name, b_name}; lets the viewer offer "company A vs company B"


@dataclass
class HubView:
    title: str
    entries: list
    embed: bool
    kinds: list = field(default_factory=list)       # the groups that have at least one page, in order
    data_json: str = ""                             # everything the viewer's script needs, safe to put inside a <script> block
    page_count: int = 0                             # the pages in the main dropdown and search (everything except the comparisons)
    compare_count: int = 0                          # the comparisons: kept out of the main dropdown, they have their own picker


def kind_of(stem):
    """Which group a page belongs to, from its file name (the names are made by render.py)."""
    if stem.startswith("error_"):
        return ERRORS
    if _COMPARE_NAME.match(stem):
        return COMPARISONS
    if "_trend_" in stem:
        return TRENDS
    if "_summary_" in stem:
        return SUMMARIES
    return REPORTS if _REPORT_NAME.match(stem) else OTHER


def page_title(text, fallback):
    """The text of the page's <title>, tidied (the fallback when there is none)."""
    match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
    title = " ".join(html.unescape(match.group(1)).split()) if match else ""
    return title or fallback


def label_for(kind, stem, title):
    """An error page's title is the same for every company, so the name of what was asked is added: 'No report: ... (Xyzzy Quux 2023-24)'."""
    if kind == ERRORS:
        asked = stem.removeprefix("error_").replace("_", " ")
        return f"{title} ({asked})" if asked else title
    return title


def compare_info(stem, title):
    """Who is compared in which year, from a comparison page's file name (symbols) and title (full names); None for any other page."""
    named = _COMPARE_NAME.match(stem)
    if not named:
        return None
    titled = _COMPARE_TITLE.match(title)
    return {"fy": named["fy"], "a": named["a"], "b": named["b"],
            "a_name": titled["a"] if titled else named["a"], "b_name": titled["b"] if titled else named["b"]}


def build_hub_view(pages, embed=True, title=HUB_TITLE):
    """`pages` is a list of (file name, HTML text), for example [("TATASTEEL_2025-26.html", "<!doctype html>...")]."""
    entries = []
    for file, text in pages:
        stem = file.removesuffix(".html")
        kind = kind_of(stem)
        label = label_for(kind, stem, page_title(text, stem))
        compare = compare_info(stem, label) if kind == COMPARISONS else None
        entries.append(HubEntry(stem, file, label, kind, f"{label} {kind} {file}".lower(), text if embed else None, compare))
    entries.sort(key=lambda e: (KINDS.index(e.kind), e.label.casefold(), e.file))
    kinds = [kind for kind in KINDS if any(e.kind == kind for e in entries)]
    compare_count = sum(1 for e in entries if e.compare)
    return HubView(title, entries, embed, kinds, _data_json(entries, embed), len(entries) - compare_count, compare_count)


def _data_json(entries, embed):
    """The viewer's data as JSON that is safe inside <script>: every '<' is written \\u003c, so nothing in a page can end the block."""
    rows = [{"id": e.id, "file": e.file, "label": e.label, "kind": e.kind, "search": e.search, **({"html": e.html} if embed else {}), **({"compare": e.compare} if e.compare else {})} for e in entries]
    return json.dumps({"embed": embed, "entries": rows}, ensure_ascii=False).replace("<", "\\u003c")
