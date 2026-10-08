"""Tests for the one command, `python flow.py` (brsr_p6/cli/flow_cli.py): the flow itself and the dispatch to the sub-commands."""

from pathlib import Path

import pytest

from brsr_p6.cli import flow_cli
from brsr_p6.cli.flow_cli import COMMANDS, build_parser, main
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
    monkeypatch.setattr(flow_cli, "generate_page", lambda company, fy, output_dir=None, progress=None: (Path("output/INFY_2022-23.html"), object()))
    assert main(["--company", "Infosys", "--fy", "2022-23"]) == 0
    assert "INFY_2022-23.html" in capsys.readouterr().out


def test_main_passes_the_output_folder_on(monkeypatch):
    seen = {}

    def fake(company, fy, output_dir=None, progress=None):
        seen["output_dir"] = output_dir
        return Path("x.html"), object()

    monkeypatch.setattr(flow_cli, "generate_page", fake)
    main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", "samples"])
    assert seen["output_dir"] == Path("samples")


def fail_with(error):
    def fail(company, fy, output_dir=None, progress=None):
        raise error
    return fail


def test_an_error_prints_our_specific_message_writes_an_explanation_page_and_returns_1(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(flow_cli, "generate_page", fail_with(UnknownCompany("No NSE-listed company matches 'Xyzzy'.")))
    assert main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "No NSE-listed company matches 'Xyzzy'." in out and "explanation page was written" in out
    page = (tmp_path / "error_Xyzzy_2022-23.html").read_text(encoding="utf-8")
    assert "No NSE-listed company matches &#39;Xyzzy&#39;." in page and "We could not find that company on NSE" in page


def test_an_unexpected_bug_is_explained_on_a_page_too_without_a_traceback(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(flow_cli, "generate_page", fail_with(KeyError("E1.total")))
    assert main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "Unexpected problem" in out and "KeyError" in out and "--debug" in out and "Traceback" not in out
    assert "Something unexpected went wrong" in (tmp_path / "error_Infosys_2022-23.html").read_text(encoding="utf-8")


def test_debug_lets_an_unexpected_bug_through_so_its_traceback_can_be_read(monkeypatch, tmp_path):
    monkeypatch.setattr(flow_cli, "generate_page", fail_with(KeyError("E1.total")))
    with pytest.raises(KeyError):
        main(["--company", "Infosys", "--fy", "2022-23", "--output-dir", str(tmp_path), "--debug"])


def test_a_folder_that_cannot_be_written_does_not_hide_the_original_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(flow_cli, "generate_page", fail_with(UnknownCompany("No match.")))
    blocker = tmp_path / "file_not_folder"
    blocker.write_text("x", encoding="utf-8")                      # a FILE where a folder is needed: writing must fail
    assert main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(blocker / "out")]) == 1
    out = capsys.readouterr().out
    assert "No match." in out and "Could not write the explanation page" in out


# ------------------------------------------------------------------------------------------------ the sub-commands
def test_every_other_command_is_a_sub_command_of_the_one_file():
    assert set(COMMANDS) == {"download", "extract", "trends", "summary", "compare", "hub", "samples"}
    for name, (run, what) in COMMANDS.items():
        assert callable(run) and what


@pytest.mark.parametrize("name", sorted(COMMANDS))
def test_a_sub_command_gets_the_rest_of_the_line_and_names_itself_in_its_help(name, monkeypatch, capsys):
    seen = []
    monkeypatch.setitem(COMMANDS, name, (lambda argv: seen.append(argv) or 0, "x"))
    assert main([name, "--company", "Tata Steel", "--fy", "2025-26"]) == 0
    assert seen == [["--company", "Tata Steel", "--fy", "2025-26"]]                    # the command word is removed, nothing else changes


@pytest.mark.parametrize("name", ["download", "extract", "trends", "summary", "compare", "hub", "samples"])
def test_the_help_of_a_sub_command_says_flow_py_and_its_name(name, capsys):
    with pytest.raises(SystemExit) as stop:
        main([name, "--help"])
    assert stop.value.code == 0 and f"usage: flow.py {name}" in capsys.readouterr().out


def test_a_bare_command_shows_the_help_with_the_list_of_other_commands(capsys):
    with pytest.raises(SystemExit) as stop:
        main([])
    out = capsys.readouterr().out
    assert stop.value.code == 0 and "usage: flow.py" in out and "--company" in out
    for name in COMMANDS:
        assert f"python flow.py {name}" in out


def test_a_company_that_is_named_like_a_command_is_still_a_company(monkeypatch):
    seen = {}
    monkeypatch.setattr(flow_cli, "generate_page", lambda company, fy, output_dir=None, progress=None: (seen.update(company=company) or Path("x.html"), object()))
    assert main(["--company", "trends", "--fy", "2023-24"]) == 0 and seen["company"] == "trends"       # only the FIRST word can be a command


def test_the_example_in_the_help_is_the_one_command_that_does_everything(capsys):
    with pytest.raises(SystemExit):
        main(["--help"])
    assert 'python flow.py --company "Tata Steel" --fy 2025-26 --open' in capsys.readouterr().out


def test_the_samples_command_rebuilds_the_samples_and_says_how_many(monkeypatch, capsys):
    from brsr_p6.cli import samples_cli

    monkeypatch.setattr(samples_cli, "make_samples", lambda: [Path("a.html"), Path("b.html")])
    assert main(["samples"]) == 0
    assert "2 sample pages are in the samples/ folder" in capsys.readouterr().out


def test_opening_the_error_page_in_a_browser_is_optional(monkeypatch, tmp_path):
    opened = []
    monkeypatch.setattr(flow_cli.webbrowser, "open", opened.append)
    monkeypatch.setattr(flow_cli, "generate_page", fail_with(UnknownCompany("No match.")))
    main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path)])
    assert opened == []
    main(["--company", "Xyzzy", "--fy", "2022-23", "--output-dir", str(tmp_path), "--open"])
    assert len(opened) == 1 and opened[0].endswith("error_Xyzzy_2022-23.html")
