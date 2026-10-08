"""Tests for the two viewer pages (templates/hub.html and compare_hub.html): their parts, their safety, and that they handle every page the project can make."""

import re

from html_checks import assert_well_formed

from brsr_p6.rendering.render import (COMPARE_HUB_FILE_NAME, HUB_FILE_NAME, compare_hub_page_path, hub_page_path, render_compare_hub_page, render_hub_page,
                                      write_compare_hub_page, write_hub_page)
from brsr_p6.views.hub_view import build_compare_hub_view, build_hub_view

PAGES = [
    ("TATASTEEL_2025-26.html", "<!doctype html><title>Tata Steel Limited: BRSR Principle 6, FY 2025-26</title><p>report</p>"),
    ("error_Xyzzy_Quux_2023-24.html", "<!doctype html><title>No report: We could not find that company on NSE</title><p>error</p>"),
]
COMPARISON = ("TATASTEEL_vs_WIPRO_2025-26.html", "<!doctype html><title>Tata Steel Limited vs Wipro Limited: BRSR Principle 6 compared, FY 2025-26</title><p>c</p>")


def index(pages=PAGES, **kwargs):
    return render_hub_page(build_hub_view(pages, **kwargs))


def compare_page(pages=PAGES + [COMPARISON], **kwargs):
    return render_compare_hub_page(build_compare_hub_view(pages, **kwargs))


def scripts(html):
    return len(re.findall(r"<script", html)), len(re.findall(r"</script", html))


# ------------------------------------------------------------------------------------------------ the index page: one company
def test_the_index_page_has_the_choices_of_one_company_and_a_frame_for_its_page():
    html = index()
    assert_well_formed(html)
    for part in ('id="company"', 'id="year"', 'data-view="report"', 'data-view="summary"', 'data-view="trend"', 'id="open-tab"', 'id="viewer"',
                 "Company", "Financial year", "Report", "Year-on-year", "Multi-year trend"):
        assert part in html, part


def test_the_index_page_is_simple_no_search_box_no_previous_next_no_hint_line_no_second_banner():
    html = index()
    for gone in ('id="page-search"', 'id="prev"', 'id="next"', "Type to narrow the list", "eyebrow", 'type="search"'):
        assert gone not in html, gone
    assert html.count("<h1>") == 1 and html.count("<header") == 1


def test_the_compare_button_is_shown_only_when_there_is_a_comparison():
    with_one = index(PAGES + [COMPARISON])
    assert '<a class="cta" href="compare_companies.html">Compare two companies' in with_one
    assert 'class="cta"' not in index(PAGES)


def test_the_error_pages_have_a_small_dropdown_of_their_own_with_their_count():
    html = index()
    assert 'id="other"' in html and "Error pages (1)" in html
    assert 'id="other"' not in index(PAGES[:1])


def test_the_frame_is_sandboxed_so_a_shown_page_cannot_run_a_script():
    for html in (index(), compare_page()):
        sandbox = re.search(r'<iframe[^>]*sandbox="([^"]*)"', html).group(1)
        assert "allow-scripts" not in sandbox and "allow-same-origin" not in sandbox


def test_the_only_scripts_of_each_viewer_are_its_own_data_and_its_own_code():
    for html in (index(), index(PAGES + [COMPARISON]), compare_page()):
        assert scripts(html) == (2, 2) and 'id="hub-data"' in html


def test_the_pages_inside_the_viewers_can_never_end_the_data_block_or_add_a_script():
    nasty = [("x_2024-25.html", "<!doctype html><title>t</title></script><script>alert(1)</script>")]
    comparison = [("A_vs_B_2024-25.html", "<!doctype html><title>A Ltd vs B Ltd: x, FY 2024-25</title></script><script>alert(1)</script>")]
    assert scripts(index(nasty)) == (2, 2) and scripts(compare_page(comparison)) == (2, 2)
    assert_well_formed(index(nasty))


def test_a_title_cannot_inject_html_into_the_no_script_list_or_the_top_bar():
    evil = "<script>alert(1)</script>"
    html = index([("x_2024-25.html", "<!doctype html><title>&lt;script&gt;alert(1)&lt;/script&gt;</title>")], title=evil)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_without_a_script_the_index_page_still_lists_every_page_as_a_link_under_its_group():
    html = index(PAGES + [COMPARISON])
    fallback = html[html.index("<noscript>\n  <div"):html.index("</noscript>\n\n<section")]
    assert 'href="TATASTEEL_2025-26.html"' in fallback and 'href="error_Xyzzy_Quux_2023-24.html"' in fallback
    assert "<strong>Reports</strong>" in fallback and "<strong>Error pages</strong>" in fallback
    assert 'href="compare_companies.html"' in fallback and "TATASTEEL_vs_WIPRO" not in fallback              # the comparisons are on the compare page


def test_the_script_looks_for_pages_by_company_year_and_view_and_never_in_a_list_of_every_page():
    script = index()[index().index("<script>"):]
    assert "var companies = data.companies;" in script and "function pageFor(company, fy, view)" in script
    assert 'find([view, "report", "summary", "trend"]' in script            # a view the company has no page for gives way to one it has
    assert "button.disabled = !has;" in script and "Not made yet. To make it, run:" in script       # and its button is greyed out (saying how to make it), not hidden


# ------------------------------------------------------------------------------------------------ the compare page: two companies
def test_the_compare_page_has_a_year_and_two_company_dropdowns_a_way_back_and_a_frame():
    html = compare_page()
    assert_well_formed(html)
    for part in ('id="cmp-fy"', 'id="cmp-a"', 'id="cmp-b"', 'id="viewer"', 'id="open-tab"', "Financial year", "Company A", "Company B",
                 '<a class="back" href="index.html">← All reports</a>', "<h1>Compare two companies</h1>"):
        assert part in html, part
    assert "<title>Compare two companies: " in html


def test_the_compare_page_carries_the_comparisons_only_and_lists_them_as_links_without_a_script():
    html = compare_page()
    fallback = html[html.index("<noscript>\n  <div"):html.index("</noscript>\n\n<section")]
    assert 'href="TATASTEEL_vs_WIPRO_2025-26.html"' in fallback and "TATASTEEL_2025-26" not in fallback
    assert '"compare": {"fy": "2025-26", "a": "TATASTEEL", "b": "WIPRO"' in html or '"compare":{"fy":"2025-26","a":"TATASTEEL","b":"WIPRO"' in html
    assert "report</p>" not in html                                                                           # no report page travels in this file


def test_the_picker_keeps_the_order_the_user_chose_although_the_file_name_is_alphabetical():
    """RELIANCE_vs_TATASTEEL is one page whether the user picked Reliance first or Tata Steel first; showing it must not swap A and B."""
    script = compare_page()
    script = script[script.index("function showId"):script.index('pickFy.addEventListener("change"')]
    assert "if (!chosen) {" in script
    assert script.index("var chosen") < script.index("if (!chosen)") < script.index("pickFy.value = c.fy")        # the check comes before anything is rewritten
    assert "pickA.value === c.b && pickB.value === c.a" in script                                                # either order counts as "the pair the user picked"


def test_the_compare_page_opens_the_first_pair_of_the_newest_year_unless_the_address_names_one():
    script = compare_page()
    assert "if (!showId(fromHash())) { showPicked(); }" in script and ".sort().reverse()" in script


# ------------------------------------------------------------------------------------------------ both pages
def test_both_viewers_share_one_style_and_one_script_helper():
    one, two = index(PAGES + [COMPARISON]), compare_page()
    for html in (one, two):
        assert ".topbar {" in html and ".pickbar {" in html and "function makeViewer(entries)" in html
        assert "{%" not in html and "{{" not in html                                   # nothing of the templates is left over
    assert one.count("function setOptions") == two.count("function setOptions") == 1


def test_the_viewers_are_written_in_the_folder_they_describe(tmp_path):
    assert hub_page_path(tmp_path).name == HUB_FILE_NAME == "index.html"
    assert compare_hub_page_path(tmp_path).name == COMPARE_HUB_FILE_NAME == "compare_companies.html"
    path = write_hub_page(build_hub_view(PAGES), tmp_path / "new")
    other = write_compare_hub_page(build_compare_hub_view(PAGES + [COMPARISON]), tmp_path / "new")
    assert path.read_text(encoding="utf-8").startswith("<!doctype html>") and other.exists()
