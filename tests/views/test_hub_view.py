"""Tests for brsr_p6/views/hub_view.py: how the pages of a folder are named, grouped and handed to the two viewer pages."""

import json

import pytest

from brsr_p6.views.hub_view import (COMPARE_FILE, COMPARE_TITLE, COMPARISONS, ERRORS, HOME_FILE, KINDS, OTHER, REPORTS, SUMMARIES, TRENDS, VIEWER_FILES,
                                    build_compare_hub_view, build_hub_view, compare_info, kind_of, label_for, page_title)


def page(title):
    return f"<!doctype html><html><head><title>{title}</title></head><body><p>x</p></body></html>"


PAGES = [
    ("TATASTEEL_2025-26.html", page("Tata Steel Limited: BRSR Principle 6, FY 2025-26")),
    ("TATASTEEL_2024-25.html", page("Tata Steel Limited: BRSR Principle 6, FY 2024-25")),
    ("TATASTEEL_trend_2021-22_to_2025-26.html", page("Tata Steel Limited: BRSR Principle 6 trends, FY 2021-22 to FY 2025-26")),
    ("TATASTEEL_summary_2025-26.html", page("Tata Steel Limited: what got better and worse in FY 2025-26")),
    ("TATASTEEL_vs_WIPRO_2025-26.html", page("Tata Steel Limited vs Wipro Limited: BRSR Principle 6 compared, FY 2025-26")),
    ("error_Xyzzy_Quux_2023-24.html", page("No report: We could not find that company on NSE")),
    ("WIPRO_2025-26.html", page("Wipro Limited: BRSR Principle 6, FY 2025-26")),
    ("notes.html", page("Some other page")),
]


def company(view, symbol):
    return next(c for c in view.companies if c.symbol == symbol)


# ------------------------------------------------------------------------------------------------ naming and grouping
@pytest.mark.parametrize("stem, kind", [
    ("TATASTEEL_2025-26", REPORTS), ("M_M_2024-25", REPORTS), ("TATASTEEL_summary_2025-26", SUMMARIES),
    ("TATASTEEL_trend_2021-22_to_2025-26", TRENDS), ("TATASTEEL_vs_WIPRO_2025-26", COMPARISONS), ("M_M_vs_ITC_2024-25", COMPARISONS),
    ("error_Xyzzy_vs_Quux_2023-24", ERRORS), ("error_Xyzzy_Quux_2023-24", ERRORS), ("notes", OTHER), ("index2", OTHER),
])
def test_a_page_is_grouped_by_what_its_file_name_says(stem, kind):
    assert kind_of(stem) == kind


def test_the_title_comes_from_the_pages_own_title_tag_tidied():
    assert page_title("<title>  Tata &amp; Sons:\n  BRSR </title>", "fallback") == "Tata & Sons: BRSR"
    assert page_title("<p>no title here</p>", "fallback") == "fallback" and page_title("<title> </title>", "fallback") == "fallback"


def test_an_error_page_label_says_what_was_asked_because_the_titles_are_all_alike():
    assert label_for(ERRORS, "error_Xyzzy_Quux_2023-24", "No report: x") == "No report: x (Xyzzy Quux 2023-24)"
    assert label_for(REPORTS, "TATASTEEL_2025-26", "Tata Steel") == "Tata Steel"


def test_the_two_viewers_are_named_and_are_never_pages_of_their_own():
    assert (HOME_FILE, COMPARE_FILE) == ("index.html", "compare_companies.html") and VIEWER_FILES == (HOME_FILE, COMPARE_FILE)


# ------------------------------------------------------------------------------------------------ the index page: one company at a time
def test_the_index_page_leaves_the_comparisons_to_the_compare_page():
    view = build_hub_view(PAGES)
    assert COMPARISONS not in [e.kind for e in view.entries] and COMPARISONS not in view.kinds
    assert len(view.entries) == len(PAGES) - 1 and view.compare_count == 1 and view.compare_file == COMPARE_FILE
    assert build_hub_view(PAGES[:1]).compare_count == 0


def test_pages_are_listed_group_by_group_and_alphabetically_inside_a_group():
    view = build_hub_view(PAGES)
    assert [e.kind for e in view.entries] == [REPORTS, REPORTS, REPORTS, SUMMARIES, TRENDS, ERRORS, OTHER]
    assert [e.id for e in view.entries if e.kind == REPORTS] == ["TATASTEEL_2024-25", "TATASTEEL_2025-26", "WIPRO_2025-26"]
    assert view.kinds == [kind for kind in KINDS if kind != COMPARISONS]               # the groups of the no-script list, in order


def test_a_group_with_no_page_is_not_listed():
    assert build_hub_view(PAGES[:1]).kinds == [REPORTS]


def test_every_company_has_its_years_newest_first_with_its_report_and_summary():
    view = build_hub_view(PAGES)
    assert [c.symbol for c in view.companies] == ["TATASTEEL", "WIPRO"] and [c.name for c in view.companies] == ["Tata Steel Limited", "Wipro Limited"]
    tata = company(view, "TATASTEEL")
    assert tata.years == [{"fy": "2025-26", "report": "TATASTEEL_2025-26", "summary": "TATASTEEL_summary_2025-26"},
                          {"fy": "2024-25", "report": "TATASTEEL_2024-25", "summary": ""}]            # "" = there is no such page
    assert tata.trends == [{"id": "TATASTEEL_trend_2021-22_to_2025-26", "first": "2021-22", "last": "2025-26"}]
    assert company(view, "WIPRO").years == [{"fy": "2025-26", "report": "WIPRO_2025-26", "summary": ""}] and company(view, "WIPRO").trends == []


def test_companies_are_listed_by_name_and_a_symbol_with_an_underscore_is_one_company():
    pages = [("M_M_2024-25.html", page("Mahindra Limited: BRSR Principle 6, FY 2024-25")), ("ITC_2024-25.html", page("ITC Limited: BRSR Principle 6, FY 2024-25"))]
    view = build_hub_view(pages)
    assert [(c.symbol, c.name) for c in view.companies] == [("ITC", "ITC Limited"), ("M_M", "Mahindra Limited")]


def test_a_company_with_only_a_summary_or_a_trend_page_is_still_offered_and_named_from_that_page():
    view = build_hub_view([("ABC_summary_2024-25.html", page("Abc Limited: what got better and worse in FY 2024-25")),
                           ("XYZ_trend_2022-23_to_2024-25.html", page("Xyz Limited: BRSR Principle 6 trends"))])
    assert company(view, "ABC").years == [{"fy": "2024-25", "report": "", "summary": "ABC_summary_2024-25"}] and company(view, "ABC").name == "Abc Limited"
    assert company(view, "XYZ").years == [] and company(view, "XYZ").trends[0]["last"] == "2024-25" and view.others == []


def test_a_title_without_a_company_name_falls_back_to_the_symbol():
    assert build_hub_view([("ABC_2024-25.html", page("untitled"))]).companies[0].name == "ABC"


def test_the_pages_that_belong_to_no_company_are_kept_for_the_small_dropdown_of_other_pages():
    view = build_hub_view(PAGES)
    assert view.others == ["error_Xyzzy_Quux_2023-24", "notes"] and view.others_label == OTHER
    only_errors = build_hub_view([PAGES[0], PAGES[5]])
    assert only_errors.others == ["error_Xyzzy_Quux_2023-24"] and only_errors.others_label == ERRORS
    assert build_hub_view(PAGES[:1]).others == [] and build_hub_view(PAGES[:1]).others_label == ""


def test_a_name_that_looks_like_a_summary_but_has_no_year_is_not_taken_for_a_company_page():
    view = build_hub_view([("foo_summary_bar.html", page("Foo")), ("ABC_2024-25.html", page("Abc Limited: x"))])
    assert [c.symbol for c in view.companies] == ["ABC"] and view.others == ["foo_summary_bar"]


# ------------------------------------------------------------------------------------------------ the data the script reads
def test_the_pages_are_embedded_by_default_and_only_named_when_linked():
    embedded = json.loads(build_hub_view(PAGES).data_json)
    assert embedded["embed"] is True and embedded["entries"][0]["html"] == PAGES[1][1]                # the first report in the list: TATASTEEL_2024-25
    linked = json.loads(build_hub_view(PAGES, embed=False).data_json)
    assert linked["embed"] is False and all("html" not in row for row in linked["entries"]) and linked["entries"][0]["file"] == "TATASTEEL_2024-25.html"


def test_the_script_gets_the_companies_and_the_other_pages_and_no_comparison():
    data = json.loads(build_hub_view(PAGES).data_json)
    assert [c["symbol"] for c in data["companies"]] == ["TATASTEEL", "WIPRO"] and data["others"] == ["error_Xyzzy_Quux_2023-24", "notes"]
    assert data["companies"][0]["years"][0] == {"fy": "2025-26", "report": "TATASTEEL_2025-26", "summary": "TATASTEEL_summary_2025-26"}
    assert not [row for row in data["entries"] if "_vs_" in row["id"]]


def test_what_travels_inside_a_script_block_can_never_end_it():
    """A page that contains </script> or <!-- must not break out of the viewer's data block."""
    nasty = ("evil_2024-25.html", page("t") + "</script><script>alert(1)</script><!-- <script>")
    for data in (build_hub_view([nasty]).data_json, build_compare_hub_view([("A_vs_B_2024-25.html", nasty[1])]).data_json):
        assert "<" not in data and "</script" not in data.lower()
    assert json.loads(build_hub_view([nasty]).data_json)["entries"][0]["html"].endswith("<!-- <script>")      # and nothing is lost: the page comes back exactly


def test_text_from_a_title_is_data_not_markup():
    view = build_hub_view([("x_2024-25.html", page("<b>bold</b> &lt;i&gt;"))])
    assert view.entries[0].label == "<b>bold</b> <i>"                          # (the template escapes it; the viewer uses textContent)


# ------------------------------------------------------------------------------------------------ the compare page: two companies, one year
def test_a_comparison_page_says_who_is_compared_in_which_year_from_its_name_and_title():
    title = "Tata Steel Limited vs Wipro Limited: BRSR Principle 6 compared, FY 2025-26"
    assert compare_info("TATASTEEL_vs_WIPRO_2025-26", title) == {
        "fy": "2025-26", "a": "TATASTEEL", "b": "WIPRO", "a_name": "Tata Steel Limited", "b_name": "Wipro Limited"}
    assert compare_info("M_M_vs_L_T_2024-25", "x") == {"fy": "2024-25", "a": "M_M", "b": "L_T", "a_name": "M_M", "b_name": "L_T"}     # no usable title: symbols
    assert compare_info("TATASTEEL_2025-26", title) is None and compare_info("TATASTEEL_summary_2025-26", title) is None


def test_the_compare_page_gets_only_the_comparisons_and_each_says_who_is_compared():
    view = build_compare_hub_view(PAGES)
    assert [e.id for e in view.entries] == ["TATASTEEL_vs_WIPRO_2025-26"] and view.title == COMPARE_TITLE and view.home_file == HOME_FILE
    assert view.entries[0].compare["a_name"] == "Tata Steel Limited"
    rows = json.loads(view.data_json)["entries"]
    assert [row["id"] for row in rows] == ["TATASTEEL_vs_WIPRO_2025-26"] and rows[0]["compare"]["fy"] == "2025-26" and rows[0]["html"] == PAGES[4][1]
    assert "compare" in json.loads(build_compare_hub_view(PAGES, embed=False).data_json)["entries"][0]            # linked pages still carry it


def test_with_no_comparison_the_compare_page_has_no_entry_and_the_index_page_no_button():
    assert build_compare_hub_view(PAGES[:1]).entries == [] and build_hub_view(PAGES[:1]).compare_count == 0


def test_the_compare_page_remembers_the_name_of_the_tool_it_belongs_to():
    assert build_compare_hub_view(PAGES, title="Sample pages").project == "Sample pages"
