"""Tests for the command-line interface (brsr_p6/cli/main_cli.py)."""

from pathlib import Path

import pytest

from brsr_p6.cli import main_cli
from brsr_p6.cli.main_cli import build_parser, main
from brsr_p6.core.errors import UnknownCompany


def test_parser_reads_company_and_fy():
    args = build_parser().parse_args(["--company", "Tata Steel", "--fy", "2023-24"])
    assert args.company == "Tata Steel"
    assert args.fy == "2023-24"
    assert args.open is False


def test_missing_arguments_exit_with_error():
    # argparse calls sys.exit(2) when required options are missing.
    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args([])
    assert excinfo.value.code == 2


def test_parser_has_an_output_folder_and_a_debug_switch():
    args = build_parser().parse_args(["--company", "X", "--fy", "2023-24", "--output-dir", "samples", "--debug"])
    assert args.output_dir == Path("samples") and args.debug is True


def test_main_reports_where_the_page_was_written(monkeypatch, capsys):
    monkeypatch.setattr(main_cli, "generate_page", lambda company, fy, output_dir=None, progress=None: (Path("output/INFY_2022-23.html"), object()))
    assert main(["--company", "Infosys", "--fy", "2022-23"]) == 0
    assert "INFY_2022-23.html" in capsys.readouterr().out


def test_main_passes_the_output_folder_on(monkeypatch):
    seen = {}

    def fake(company, fy, output_dir=None, progress=None):
        seen["output_dir"] = output_dir
        return Path("x.html"), object()

    monkeypatch.setattr(main_cli, "generate_page", fake)
    main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", "samples"])
    assert seen["output_dir"] == Path("samples")


def fail_with(error):
    def fail(company, fy, output_dir=None, progress=None):
        raise error
    return fail


def test_an_error_prints_our_specific_message_writes_an_explanation_page_and_returns_1(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(main_cli, "generate_page", fail_with(UnknownCompany("No NSE-listed company matches 'Xyzzy'.")))
    assert main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "No NSE-listed company matches 'Xyzzy'." in out and "explanation page was written" in out
    page = (tmp_path / "error_Xyzzy_2022-23.html").read_text(encoding="utf-8")
    assert "No NSE-listed company matches &#39;Xyzzy&#39;." in page and "We could not find that company on NSE" in page


def test_an_unexpected_bug_is_explained_on_a_page_too_without_a_traceback(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(main_cli, "generate_page", fail_with(KeyError("E1.total")))
    assert main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "Unexpected problem" in out and "KeyError" in out and "--debug" in out and "Traceback" not in out
    assert "Something unexpected went wrong" in (tmp_path / "error_Infosys_2022-23.html").read_text(encoding="utf-8")


def test_debug_lets_an_unexpected_bug_through_so_its_traceback_can_be_read(monkeypatch, tmp_path):
    monkeypatch.setattr(main_cli, "generate_page", fail_with(KeyError("E1.total")))
    with pytest.raises(KeyError):
        main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", str(tmp_path), "--debug"])


def test_a_folder_that_cannot_be_written_does_not_hide_the_original_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(main_cli, "generate_page", fail_with(UnknownCompany("No match.")))
    blocker = tmp_path / "file_not_folder"
    blocker.write_text("x", encoding="utf-8")                      # a FILE where a folder is needed: writing must fail
    assert main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(blocker / "out")]) == 1
    out = capsys.readouterr().out
    assert "No match." in out and "Could not write the explanation page" in out


def test_opening_the_error_page_in_a_browser_is_optional(monkeypatch, tmp_path):
    opened = []
    monkeypatch.setattr(main_cli.webbrowser, "open", opened.append)
    monkeypatch.setattr(main_cli, "generate_page", fail_with(UnknownCompany("No match.")))
    main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path)])
    assert opened == []
    main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path), "--open"])
    assert len(opened) == 1 and opened[0].endswith("error_Xyzzy_2022-23.html")
