"""Tests for brsr_p6/workflows/hub.py: gathering the pages of a folder into the two viewer pages."""

import json
import re

from brsr_p6.rendering.render import COMPARE_HUB_FILE_NAME, HUB_FILE_NAME
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


def test_the_viewers_themselves_are_never_pages_of_their_own(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    write(tmp_path, "WIPRO_2024-25.html")
    write(tmp_path, "ITC_vs_WIPRO_2024-25.html", "ITC Limited vs Wipro Limited: BRSR Principle 6 compared, FY 2024-25")
    generate_hub(tmp_path)
    generate_hub(tmp_path)                                     # running again must not embed the old viewers
    assert (tmp_path / HUB_FILE_NAME).exists() and (tmp_path / COMPARE_HUB_FILE_NAME).exists()
    assert [name for name, _ in read_pages(tmp_path)] == ["ITC_2024-25.html", "ITC_vs_WIPRO_2024-25.html", "WIPRO_2024-25.html"]


def test_the_index_page_is_written_next_to_the_pages_and_says_how_many_pages_there_are(tmp_path):
    write(tmp_path, "ITC_2024-25.html", "ITC Limited: BRSR Principle 6, FY 2024-25")
    write(tmp_path, "WIPRO_2025-26.html", "Wipro Limited: BRSR Principle 6, FY 2025-26")
    path, count = generate_hub(tmp_path)
    assert (path, count) == (tmp_path / HUB_FILE_NAME, 2) and path.exists()
    data = data_of(path)
    assert [row["id"] for row in data["entries"]] == ["ITC_2024-25", "WIPRO_2025-26"] and [c["name"] for c in data["companies"]] == ["ITC Limited", "Wipro Limited"]


def test_embedded_pages_travel_inside_the_viewer_and_linked_pages_do_not(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    embedded = data_of(generate_hub(tmp_path, embed=True)[0])
    assert embedded["embed"] is True and "ITC_2024-25.html</body>" in embedded["entries"][0]["html"]
    linked = data_of(generate_hub(tmp_path, embed=False)[0])
    assert linked["embed"] is False and "html" not in linked["entries"][0]


def test_a_folder_without_pages_makes_no_viewer(tmp_path):
    assert generate_hub(tmp_path) is None and not (tmp_path / HUB_FILE_NAME).exists() and not (tmp_path / COMPARE_HUB_FILE_NAME).exists()
    assert generate_hub(tmp_path / "does_not_exist") is None


def test_missing_pages_are_made_first_only_when_asked_and_comparisons_go_to_the_compare_page(tmp_path, monkeypatch):
    from brsr_p6.workflows import hub

    write(tmp_path, "A_2023-24.html")
    write(tmp_path, "B_2023-24.html")
    asked = []

    def fake_comparisons(folder, loader):
        asked.append(("comparisons", folder))
        write(folder, "A_vs_B_2023-24.html", "A Limited vs B Limited: BRSR Principle 6 compared, FY 2023-24")
        return 1

    monkeypatch.setattr(hub, "generate_all_comparisons", fake_comparisons)
    monkeypatch.setattr(hub, "generate_missing_summaries", lambda folder, loader: asked.append(("summaries", folder)))
    monkeypatch.setattr(hub, "generate_missing_trends", lambda folder, loader: asked.append(("trends", folder)))
    path, count = generate_hub(tmp_path)
    assert asked == [] and count == 2                                          # off by default: the samples viewer must not gain pages
    assert not (tmp_path / COMPARE_HUB_FILE_NAME).exists()                      # no comparison, so no compare page and no button
    assert 'class="cta"' not in path.read_text(encoding="utf-8").split("<noscript>")[0]
    path, count = generate_hub(tmp_path, fill=True)
    assert asked == [("comparisons", tmp_path), ("summaries", tmp_path), ("trends", tmp_path)] and count == 3
    assert [row["id"] for row in data_of(path)["entries"]] == ["A_2023-24", "B_2023-24"]          # the index page does not list the comparison ...
    assert 'class="cta" href="compare_companies.html"' in path.read_text(encoding="utf-8")      # ... it has a button to the compare page
    entries = {row["id"]: row for row in data_of(tmp_path / COMPARE_HUB_FILE_NAME)["entries"]}
    assert list(entries) == ["A_vs_B_2023-24"] and entries["A_vs_B_2023-24"]["compare"]["b_name"] == "B Limited"


def test_a_compare_page_whose_comparisons_are_gone_is_removed_not_left_stale(tmp_path):
    write(tmp_path, "A_2023-24.html")
    write(tmp_path, "A_vs_B_2023-24.html", "A Limited vs B Limited: BRSR Principle 6 compared, FY 2023-24")
    generate_hub(tmp_path)
    assert (tmp_path / COMPARE_HUB_FILE_NAME).exists()
    (tmp_path / "A_vs_B_2023-24.html").unlink()
    generate_hub(tmp_path)
    assert not (tmp_path / COMPARE_HUB_FILE_NAME).exists()


def test_a_folder_with_no_page_makes_no_comparison_and_no_viewer(tmp_path):
    assert generate_hub(tmp_path, fill=True) is None and not list(tmp_path.glob("*"))


def test_the_title_of_the_viewer_can_be_chosen(tmp_path):
    write(tmp_path, "ITC_2024-25.html")
    assert "<h1>Sample pages</h1>" in generate_hub(tmp_path, title="Sample pages")[0].read_text(encoding="utf-8")
