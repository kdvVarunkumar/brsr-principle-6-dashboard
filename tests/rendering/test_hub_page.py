"""Tests for the viewer page (templates/hub.html): its parts, its safety, and that it handles every page the project can make."""

import re

from html_checks import assert_well_formed

from brsr_p6.rendering.render import HUB_FILE_NAME, hub_page_path, render_hub_page, write_hub_page
from brsr_p6.views.hub_view import build_hub_view

PAGES = [
    ("TATASTEEL_2025-26.html", "<!doctype html><title>Tata Steel Limited: BRSR Principle 6, FY 2025-26</title><p>report</p>"),
    ("error_Xyzzy_Quux_2023-24.html", "<!doctype html><title>No report: We could not find that company on NSE</title><p>error</p>"),
]


def test_the_viewer_has_a_search_box_a_dropdown_buttons_and_a_frame_for_the_page():
    html = render_hub_page(build_hub_view(PAGES))
    assert_well_formed(html)
    for part in ('id="page-search"', 'id="page-select"', 'id="prev"', 'id="next"', 'id="open-tab"', 'id="viewer"', "2 pages in one place"):
        assert part in html, part


def test_the_frame_is_sandboxed_so_a_shown_page_cannot_run_a_script():
    html = render_hub_page(build_hub_view(PAGES))
    sandbox = re.search(r'<iframe[^>]*sandbox="([^"]*)"', html).group(1)
    assert "allow-scripts" not in sandbox and "allow-same-origin" not in sandbox


def test_the_only_scripts_in_the_viewer_are_its_own_data_and_its_own_code():
    html = render_hub_page(build_hub_view(PAGES))
    assert len(re.findall(r"<script", html)) == 2 and 'id="hub-data"' in html


def test_the_pages_inside_the_viewer_can_never_end_its_data_block_or_add_a_script():
    nasty = [("x_2024-25.html", "<!doctype html><title>t</title></script><script>alert(1)</script>")]
    html = render_hub_page(build_hub_view(nasty))
    assert len(re.findall(r"<script", html)) == 2 and len(re.findall(r"</script", html)) == 2
    assert_well_formed(html)


def test_a_title_cannot_inject_html_into_the_no_script_list_or_the_heading():
    evil = "<script>alert(1)</script>"
    html = render_hub_page(build_hub_view([("x_2024-25.html", "<!doctype html><title>&lt;script&gt;alert(1)&lt;/script&gt;</title>")], title=evil))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_without_a_script_the_viewer_still_lists_every_page_as_a_link_under_its_group():
    html = render_hub_page(build_hub_view(PAGES))
    fallback = html[html.index("<noscript>\n    <div"):html.index("</noscript>\n\n  <section")]
    assert 'href="TATASTEEL_2025-26.html"' in fallback and 'href="error_Xyzzy_Quux_2023-24.html"' in fallback
    assert "<strong>Reports</strong>" in fallback and "<strong>Error pages</strong>" in fallback


def test_the_viewer_is_written_as_index_html_in_the_folder_it_describes(tmp_path):
    assert hub_page_path(tmp_path).name == HUB_FILE_NAME == "index.html"
    path = write_hub_page(build_hub_view(PAGES), tmp_path / "new")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("<!doctype html>")
