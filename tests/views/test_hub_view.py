"""Tests for brsr_p6/views/hub_view.py: how the pages of a folder are named, grouped and handed to the viewer."""

import json

import pytest

from brsr_p6.views.hub_view import ERRORS, KINDS, OTHER, REPORTS, SUMMARIES, TRENDS, build_hub_view, kind_of, label_for, page_title


def page(title):
    return f"<!doctype html><html><head><title>{title}</title></head><body><p>x</p></body></html>"


PAGES = [
    ("TATASTEEL_2025-26.html", page("Tata Steel Limited: BRSR Principle 6, FY 2025-26")),
    ("TATASTEEL_trend_2021-22_to_2025-26.html", page("Tata Steel Limited: BRSR Principle 6 trends, FY 2021-22 to FY 2025-26")),
    ("TATASTEEL_summary_2025-26.html", page("Tata Steel Limited: what got better and worse in FY 2025-26")),
    ("error_Xyzzy_Quux_2023-24.html", page("No report: We could not find that company on NSE")),
    ("WIPRO_2025-26.html", page("Wipro Limited: BRSR Principle 6, FY 2025-26")),
    ("notes.html", page("Some other page")),
]


# ------------------------------------------------------------------------------------------------ naming and grouping
@pytest.mark.parametrize("stem, kind", [
    ("TATASTEEL_2025-26", REPORTS), ("M_M_2024-25", REPORTS), ("TATASTEEL_summary_2025-26", SUMMARIES),
    ("TATASTEEL_trend_2021-22_to_2025-26", TRENDS), ("error_Xyzzy_Quux_2023-24", ERRORS), ("notes", OTHER), ("index2", OTHER),
])
def test_a_page_is_grouped_by_what_its_file_name_says(stem, kind):
    assert kind_of(stem) == kind


def test_the_title_comes_from_the_pages_own_title_tag_tidied():
    assert page_title("<title>  Tata &amp; Sons:\n  BRSR </title>", "fallback") == "Tata & Sons: BRSR"
    assert page_title("<p>no title here</p>", "fallback") == "fallback" and page_title("<title> </title>", "fallback") == "fallback"


def test_an_error_page_label_says_what_was_asked_because_the_titles_are_all_alike():
    assert label_for(ERRORS, "error_Xyzzy_Quux_2023-24", "No report: x") == "No report: x (Xyzzy Quux 2023-24)"
    assert label_for(REPORTS, "TATASTEEL_2025-26", "Tata Steel") == "Tata Steel"


def test_pages_are_listed_group_by_group_and_alphabetically_inside_a_group():
    view = build_hub_view(PAGES)
    assert [e.kind for e in view.entries] == [REPORTS, REPORTS, SUMMARIES, TRENDS, ERRORS, OTHER]
    assert [e.id for e in view.entries if e.kind == REPORTS] == ["TATASTEEL_2025-26", "WIPRO_2025-26"]
    assert view.kinds == [kind for kind in KINDS]                        # every group is present here, in the dropdown's order


def test_a_group_with_no_page_is_not_listed():
    assert build_hub_view(PAGES[:1]).kinds == [REPORTS]


def test_the_search_text_covers_the_label_the_group_and_the_file_name_in_lower_case():
    entry = build_hub_view(PAGES).entries[0]
    assert entry.search == "tata steel limited: brsr principle 6, fy 2025-26 reports tatasteel_2025-26.html"
    summary = next(e for e in build_hub_view(PAGES).entries if e.kind == SUMMARIES)
    assert "year-on-year summaries" in summary.search and "better and worse" in summary.search


# ------------------------------------------------------------------------------------------------ the data the script reads
def test_the_pages_are_embedded_by_default_and_only_named_when_linked():
    embedded = json.loads(build_hub_view(PAGES).data_json)
    assert embedded["embed"] is True and embedded["entries"][0]["html"] == PAGES[0][1]
    linked = json.loads(build_hub_view(PAGES, embed=False).data_json)
    assert linked["embed"] is False and all("html" not in row for row in linked["entries"]) and linked["entries"][0]["file"] == "TATASTEEL_2025-26.html"


def test_what_travels_inside_a_script_block_can_never_end_it():
    """A page that contains </script> or <!-- must not break out of the viewer's data block."""
    nasty = ("evil.html", page("t") + "</script><script>alert(1)</script><!-- <script>")
    data = build_hub_view([nasty]).data_json
    assert "<" not in data and "</script" not in data.lower()
    assert json.loads(data)["entries"][0]["html"].endswith("<!-- <script>")      # and nothing is lost: the page comes back exactly


def test_text_from_a_title_is_data_not_markup():
    view = build_hub_view([("x_2024-25.html", page("<b>bold</b> &lt;i&gt;"))])
    assert view.entries[0].label == "<b>bold</b> <i>"                          # (the template escapes it; the viewer uses textContent)
