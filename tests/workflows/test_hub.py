"""Tests for brsr_p6/workflows/hub.py: gathering the pages of a folder into the one viewer page."""

import json
import re

from brsr_p6.rendering.render import HUB_FILE_NAME
from brsr_p6.workflows.hub import generate_hub, read_pages


def write(folder, name, title="A page"):
    (folder / name).write_text(f"<!doctype html><html><head><title>{title}</title></head><body>{name}</body></html>", encoding="utf-8")


def data_of(path):
    """The JSON the viewer's script reads, taken back out of the written page."""
    return json.loads(re.search(r'<script type="application/json" id="hub-data">(.*?)</script>', path.read_text(encoding="utf-8"), re.S).group(1))


def test_every_html_page_is_read_in_name_order_and_other_files_are_ignored(tmp_path):
    write(tmp_path, "WIPRO_2025-26.html")
    write(tmp_path, "ITC_2024-25.html")
    (tmp_path / "README.md").write_text("not a page")
    (tmp_path / "data.json").write_text("{}")
    assert [name for name, _ in read_pages(tmp_path)] == ["ITC_2024-25.html", "WIPRO_2025-26.html"]


def test_the_viewer_itself_is_never_one_of_its_own_pages(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    generate_hub(tmp_path)
    generate_hub(tmp_path)                                     # running again must not embed the old viewer
    assert [name for name, _ in read_pages(tmp_path)] == ["ITC_2024-25.html"]


def test_the_viewer_is_written_next_to_the_pages_and_says_how_many(tmp_path):
    write(tmp_path, "ITC_2024-25.html", "ITC Limited: BRSR Principle 6, FY 2024-25")
    write(tmp_path, "WIPRO_2025-26.html", "Wipro Limited: BRSR Principle 6, FY 2025-26")
    path, count = generate_hub(tmp_path)
    assert (path, count) == (tmp_path / HUB_FILE_NAME, 2) and path.exists()
    assert [row["id"] for row in data_of(path)["entries"]] == ["ITC_2024-25", "WIPRO_2025-26"]


def test_embedded_pages_travel_inside_the_viewer_and_linked_pages_do_not(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    embedded = data_of(generate_hub(tmp_path, embed=True)[0])
    assert embedded["embed"] is True and "ITC_2024-25.html</body>" in embedded["entries"][0]["html"]
    linked = data_of(generate_hub(tmp_path, embed=False)[0])
    assert linked["embed"] is False and "html" not in linked["entries"][0]


def test_a_folder_without_pages_makes_no_viewer(tmp_path):
    assert generate_hub(tmp_path) is None and not (tmp_path / HUB_FILE_NAME).exists()
    assert generate_hub(tmp_path / "does_not_exist") is None


def test_comparisons_are_made_first_only_when_asked_so_the_viewer_lists_them(tmp_path, monkeypatch):
    from brsr_p6.workflows import hub

    write(tmp_path, "A_2023-24.html")
    write(tmp_path, "B_2023-24.html")
    asked = []

    def fake_comparisons(folder):
        asked.append(folder)
        write(folder, "A_vs_B_2023-24.html", "A Limited vs B Limited: BRSR Principle 6 compared, FY 2023-24")
        return 1

    monkeypatch.setattr(hub, "generate_all_comparisons", fake_comparisons)
    path, count = generate_hub(tmp_path)
    assert asked == [] and count == 2                                          # off by default: the samples viewer must not gain pages
    path, count = generate_hub(tmp_path, compare=True)
    assert asked == [tmp_path] and count == 3
    entries = {row["id"]: row for row in data_of(path)["entries"]}
    assert entries["A_vs_B_2023-24"]["kind"] == "Company comparisons" and entries["A_vs_B_2023-24"]["compare"]["b_name"] == "B Limited"


def test_a_folder_with_no_page_makes_no_comparison_and_no_viewer(tmp_path):
    assert generate_hub(tmp_path, compare=True) is None and not list(tmp_path.glob("*"))


def test_the_title_of_the_viewer_can_be_chosen(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    assert "<h1>Sample pages</h1>" in generate_hub(tmp_path, title="Sample pages")[0].read_text(encoding="utf-8")
