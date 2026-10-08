"""Tests for the hub.py command (brsr_p6/cli/hub_cli.py)."""

from pathlib import Path

from brsr_p6.cli import hub_cli
from brsr_p6.cli.hub_cli import build_parser, main


def write_page(folder, name="ITC_2024-25.html"):
    (folder / name).write_text("<!doctype html><html><head><title>ITC</title></head><body>x</body></html>", encoding="utf-8")


def test_the_parser_defaults_to_the_output_folder_and_embedding():
    args = build_parser().parse_args([])
    assert args.dir.name == "output" and args.link is False and args.open is False
    args = build_parser().parse_args(["--dir", "samples", "--link", "--open"])
    assert (args.dir, args.link, args.open) == (Path("samples"), True, True)


def test_comparisons_are_on_by_default_and_no_compare_turns_them_off(monkeypatch):
    seen = []
    monkeypatch.setattr(hub_cli, "generate_hub", lambda folder, embed=True, compare=False: seen.append((embed, compare)))
    assert build_parser().parse_args([]).no_compare is False and build_parser().parse_args(["--no-compare"]).no_compare is True
    main([])
    main(["--no-compare", "--link"])
    assert seen == [(True, True), (False, False)]


def test_the_command_writes_index_html_and_says_how_many_pages(tmp_path, capsys):
    write_page(tmp_path)
    write_page(tmp_path, "WIPRO_2025-26.html")
    assert main(["--dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "all 2 pages (embedded, one self-contained file)" in out and "index.html" in out
    assert (tmp_path / "index.html").exists()


def test_link_mode_is_named_in_the_message_and_makes_a_much_smaller_file(tmp_path, capsys):
    write_page(tmp_path)
    (tmp_path / "ITC_2024-25.html").write_text("<!doctype html><title>ITC</title>" + "<p>filler</p>" * 5000, encoding="utf-8")
    main(["--dir", str(tmp_path)])
    embedded = (tmp_path / "index.html").stat().st_size
    assert main(["--dir", str(tmp_path), "--link"]) == 0
    assert "linked, not embedded" in capsys.readouterr().out and (tmp_path / "index.html").stat().st_size < embedded / 3


def test_an_empty_folder_says_what_to_do_first_and_returns_1(tmp_path, capsys):
    assert main(["--dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "There is no HTML page in" in out and "python main.py" in out
    assert not (tmp_path / "index.html").exists()


def test_open_shows_the_viewer_in_the_browser(tmp_path, monkeypatch):
    write_page(tmp_path)
    opened = []
    monkeypatch.setattr(hub_cli.webbrowser, "open", opened.append)
    assert main(["--dir", str(tmp_path), "--open"]) == 0
    assert opened == [(tmp_path / "index.html").as_uri()]
