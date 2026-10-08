"""The two viewer pages of a folder: which pages there are, what each is called and how they are grouped.

Every command writes its own HTML page (a report, a trend page, a summary, a comparison, an error page).  Two viewer pages put them in reach:

    index.html                pick ONE company and a year: its report (Dashboard tab and SEBI-format tab).  The year-on-year summary and the
                              multi-year trend of that company are one click away, and a big button opens the compare page
    compare_companies.html    pick a year and TWO companies: their comparison

This module decides the names and the grouping (plain Python, no files, no HTML); workflows/hub.py reads the folder and
templates/hub.html and compare_hub.html print the result.

Two ways to hold a page:
    embedded  the page's whole HTML travels inside the viewer file, so each viewer is ONE self-contained file (the two viewers link to each other)
    linked    the viewer only names the file next to it (tiny, but it needs the folder)
"""

import html
import json
import re
from dataclasses import asdict, dataclass, field

REPORTS, COMPARISONS, SUMMARIES, TRENDS, ERRORS, OTHER = ("Reports", "Company comparisons", "Year-on-year summaries", "Multi-year trends",
                                                          "Error pages", "Other pages")
HUB_TITLE = "BRSR Principle 6: Environmental Dashboard"     # the name in the top bar of the viewer
SAMPLES_TITLE = HUB_TITLE + " (sample reports)"
COMPARE_TITLE = "Compare two companies"
KINDS = (REPORTS, COMPARISONS, SUMMARIES, TRENDS, ERRORS, OTHER)          # the order of the groups in the list of links shown without a script
HOME_FILE = "index.html"                                                  # the viewer of single companies
COMPARE_FILE = "compare_companies.html"                                   # the viewer of two companies
VIEWER_FILES = (HOME_FILE, COMPARE_FILE)                                  # never one of the pages they show

_NAME = r"(?P<symbol>.+)"
_FY = r"\d{4}-\d{2}"
_REPORT_NAME = re.compile(rf"^{_NAME}_(?P<fy>{_FY})$")                                        # TATASTEEL_2025-26
_SUMMARY_NAME = re.compile(rf"^{_NAME}_summary_(?P<fy>{_FY})$")                               # TATASTEEL_summary_2025-26
_TREND_NAME = re.compile(rf"^{_NAME}_trend_(?P<first>{_FY})_to_(?P<last>{_FY})$")             # TATASTEEL_trend_2021-22_to_2025-26
_COMPARE_NAME = re.compile(rf"^(?P<a>.+?)_vs_(?P<b>.+)_(?P<fy>{_FY})$")                       # TATASTEEL_vs_WIPRO_2025-26
_COMPARE_TITLE = re.compile(rf"^(?P<a>.+?) vs (?P<b>.+?): .*FY (?P<fy>{_FY})")                # Tata Steel Limited vs Wipro Limited: ... FY 2025-26
_COMPANY_PAGES = {REPORTS: _REPORT_NAME, SUMMARIES: _SUMMARY_NAME, TRENDS: _TREND_NAME}      # the pages that belong to one company


@dataclass
class HubEntry:
    id: str                    # the file name without ".html": also the link to this page (index.html#TATASTEEL_2025-26)
    file: str
    label: str                 # what the viewer calls the page
    kind: str                  # one of KINDS
    html: str | None = None    # the page itself when embedded
    compare: dict | None = None    # a comparison page: {fy, a, b (symbols), a_name, b_name}; lets the compare page offer "company A vs company B"


@dataclass
class Company:
    """What the index page offers for one company: its years, and the trend pages that cover it.  A page id is "" when there is no such page."""
    symbol: str
    name: str
    years: list = field(default_factory=list)       # [{"fy", "report", "summary"}], newest year first
    trends: list = field(default_factory=list)      # [{"id", "first", "last"}], newest first


@dataclass
class HubView:
    """The index page."""
    title: str
    entries: list              # every page except the comparisons (those live on the compare page)
    embed: bool
    kinds: list = field(default_factory=list)       # the groups that have at least one page, in order (for the list of links shown without a script)
    companies: list = field(default_factory=list)   # a Company for every symbol that has a report, a summary or a trend page, by name
    others: list = field(default_factory=list)      # ids of the pages that belong to no company (error pages, anything else)
    others_label: str = ""                          # what the dropdown of those pages is called
    compare_count: int = 0                          # how many comparisons there are: the "Compare two companies" button is shown when there is one
    compare_file: str = COMPARE_FILE
    data_json: str = ""                             # everything the page's script needs, safe to put inside a <script> block


@dataclass
class CompareHubView:
    """The compare page."""
    title: str
    project: str               # the name of the whole tool (the top bar of the index page)
    entries: list              # the comparisons only
    embed: bool
    home_file: str = HOME_FILE
    data_json: str = ""


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


def _entries(pages, embed):
    """[(file name, HTML text)] -> HubEntry list, group by group and alphabetically inside a group."""
    entries = []
    for file, text in pages:
        stem = file.removesuffix(".html")
        kind = kind_of(stem)
        label = label_for(kind, stem, page_title(text, stem))
        entries.append(HubEntry(stem, file, label, kind, text if embed else None, compare_info(stem, label) if kind == COMPARISONS else None))
    entries.sort(key=lambda e: (KINDS.index(e.kind), e.label.casefold(), e.file))
    return entries


def _companies(entries):
    """(a Company for every symbol with a report, summary or trend page, the ids of every page that is not one of them).

    The symbol and the years come from the file names, the company's name from the page title ("Tata Steel Limited: BRSR Principle 6, ..."):
    the reports come first in `entries`, so a report's title names the company when there is one."""
    names, years, trends, placed = {}, {}, {}, set()
    for entry in entries:
        named = _COMPANY_PAGES[entry.kind].match(entry.id) if entry.kind in _COMPANY_PAGES else None
        if not named:
            continue
        placed.add(entry.id)
        symbol = named["symbol"]
        head, colon, _ = entry.label.partition(": ")
        names.setdefault(symbol, head if colon else symbol)
        if entry.kind == TRENDS:
            trends.setdefault(symbol, []).append({"id": entry.id, "first": named["first"], "last": named["last"]})
        else:
            year = years.setdefault(symbol, {}).setdefault(named["fy"], {"fy": named["fy"], "report": "", "summary": ""})
            year["report" if entry.kind == REPORTS else "summary"] = entry.id
    companies = [Company(symbol, names[symbol],
                         sorted(years.get(symbol, {}).values(), key=lambda year: year["fy"], reverse=True),
                         sorted(trends.get(symbol, []), key=lambda trend: (trend["last"], trend["first"]), reverse=True)) for symbol in names]
    companies.sort(key=lambda company: (company.name.casefold(), company.symbol))
    return companies, placed


def build_hub_view(pages, embed=True, title=HUB_TITLE):
    """The index page.  `pages` is a list of (file name, HTML text), for example [("TATASTEEL_2025-26.html", "<!doctype html>...")]."""
    everything = _entries(pages, embed)
    entries = [e for e in everything if e.kind != COMPARISONS]
    companies, placed = _companies(entries)
    others = [e for e in entries if e.id not in placed]
    kinds = [kind for kind in KINDS if any(e.kind == kind for e in entries)]
    label = ERRORS if all(e.kind == ERRORS for e in others) else OTHER
    data = {"embed": embed, "entries": [_row(e, embed) for e in entries], "companies": [asdict(c) for c in companies], "others": [e.id for e in others]}
    return HubView(title, entries, embed, kinds, companies, [e.id for e in others], label if others else "",
                   len(everything) - len(entries), COMPARE_FILE, _json(data))


def build_compare_hub_view(pages, embed=True, title=HUB_TITLE):
    """The compare page: the comparisons among `pages` (the same list the index page is built from)."""
    entries = [e for e in _entries(pages, embed) if e.kind == COMPARISONS]
    return CompareHubView(COMPARE_TITLE, title, entries, embed, HOME_FILE, _json({"embed": embed, "entries": [_row(e, embed) for e in entries]}))


def _row(entry, embed):
    return {"id": entry.id, "file": entry.file, "label": entry.label, "kind": entry.kind, **({"html": entry.html} if embed else {}),
            **({"compare": entry.compare} if entry.compare else {})}


def _json(data):
    """The page's data as JSON that is safe inside <script>: every '<' is written \\u003c, so nothing in a page can end the block."""
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
