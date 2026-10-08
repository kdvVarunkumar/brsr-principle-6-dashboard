"""Tests for the `flow.py compare` command (brsr_p6/cli/compare_cli.py)."""

from pathlib import Path

import pytest

from brsr_p6.cli import compare_cli
from brsr_p6.cli.compare_cli import build_parser, main
from brsr_p6.core.errors import NoFilingFound, SameCompany, UnknownCompany


class Named:
    def __init__(self, company_name, fy="2025-26"):
        self.company_name, self.fy = company_name, fy


PAGE = Path("output").resolve() / "TATASTEEL_vs_WIPRO_2025-26.html"          # absolute, because --open turns it into a file:// address


def succeed(company_a, company_b, fy, output_dir=None, progress=None):
    return PAGE, Named("Tata Steel Limited"), Named("Wipro Limited")


def fail_with(error):
    def fail(company_a, company_b, fy, output_dir=None, progress=None):
        raise error
    return fail


def test_the_parser_needs_two_companies_and_one_year():
    args = build_parser().parse_args(["--company-a", "Tata Steel", "--company-b", "Wipro", "--fy", "2025-26"])
    assert (args.company_a, args.company_b, args.fy, args.open, args.debug) == ("Tata Steel", "Wipro", "2025-26", False, False)
    assert args.output_dir.name == "output"
    for missing in (["--company-b", "Wipro", "--fy", "2025-26"], ["--company-a", "Tata Steel", "--fy", "2025-26"], ["--company-a", "A", "--company-b", "B"]):
        with pytest.raises(SystemExit) as excinfo:
            build_parser().parse_args(missing)
        assert excinfo.value.code == 2


def test_the_command_says_where_the_page_is_and_names_both_companies(monkeypatch, capsys):
    monkeypatch.setattr(compare_cli, "generate_comparison_page", succeed)
    assert main(["--company-a", "Tata Steel", "--company-b", "Wipro", "--fy", "2025-26"]) == 0
    out = capsys.readouterr().out
    assert "Tata Steel Limited and Wipro Limited, FY 2025-26" in out and "TATASTEEL_vs_WIPRO_2025-26.html" in out


def test_the_output_folder_and_the_progress_printer_are_passed_on(monkeypatch):
    seen = {}

    def spy(company_a, company_b, fy, output_dir=None, progress=None):
        seen.update(a=company_a, b=company_b, fy=fy, output_dir=output_dir, progress=progress)
        return succeed(company_a, company_b, fy)

    monkeypatch.setattr(compare_cli, "generate_comparison_page", spy)
    main(["--company-a", "A", "--company-b", "B", "--fy", "2025-26", "--output-dir", "samples"])
    assert (seen["a"], seen["b"], seen["fy"], seen["output_dir"], seen["progress"]) == ("A", "B", "2025-26", Path("samples"), print)


def test_open_shows_the_page_in_the_browser_only_when_asked(monkeypatch):
    opened = []
    monkeypatch.setattr(compare_cli.webbrowser, "open", opened.append)
    monkeypatch.setattr(compare_cli, "generate_comparison_page", succeed)
    main(["--company-a", "A", "--company-b", "B", "--fy", "2025-26"])
    assert opened == []
    main(["--company-a", "A", "--company-b", "B", "--fy", "2025-26", "--open"])
    assert opened == [PAGE.as_uri()]


def test_an_error_prints_our_message_and_writes_a_page_with_a_compare_command(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(compare_cli, "generate_comparison_page", fail_with(UnknownCompany("No NSE-listed company matches 'Xyzzy'.")))
    assert main(["--company-a", "Xyzzy", "--company-b", "Wipro", "--fy", "2023-24", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "No NSE-listed company matches 'Xyzzy'." in out and "explanation page was written" in out
    page = (tmp_path / "error_Xyzzy_vs_Wipro_2023-24.html").read_text(encoding="utf-8")
    assert "We could not find that company on NSE" in page and "No NSE-listed company matches &#39;Xyzzy&#39;." in page


def test_a_missing_filing_offers_compare_commands_for_the_years_nse_has(monkeypatch, tmp_path):
    error = NoFilingFound("NSE has no BRSR filing for Wipro Limited for FY 2021-22.", symbol="WIPRO", available=["2022-23", "2023-24"])
    monkeypatch.setattr(compare_cli, "generate_comparison_page", fail_with(error))
    main(["--company-a", "Tata Steel", "--company-b", "Wipro", "--fy", "2021-22", "--output-dir", str(tmp_path)])
    page = (tmp_path / "error_Tata_Steel_vs_Wipro_2021-22.html").read_text(encoding="utf-8")
    assert 'python flow.py compare --company-a &#34;WIPRO&#34; --company-b &#34;&lt;the other company&gt;&#34; --fy 2022-23' in page
    assert "python flow.py --company" not in page                        # the suggestion uses the command that failed, not the plain flow


def test_asking_for_the_same_company_twice_has_its_own_page(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(compare_cli, "generate_comparison_page", fail_with(SameCompany("'Wipro' and 'Wipro' are the same company.")))
    assert main(["--company-a", "Wipro", "--company-b", "Wipro", "--fy", "2025-26", "--output-dir", str(tmp_path)]) == 1
    page = (tmp_path / "error_Wipro_vs_Wipro_2025-26.html").read_text(encoding="utf-8")
    assert "A comparison needs two different companies" in page and "flow.py trends" in page


def test_an_unexpected_bug_is_explained_on_a_page_without_a_traceback(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(compare_cli, "generate_comparison_page", fail_with(KeyError("E1.total")))
    assert main(["--company-a", "A", "--company-b", "B", "--fy", "2025-26", "--output-dir", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "Unexpected problem" in out and "KeyError" in out and "--debug" in out and "Traceback" not in out
    assert "Something unexpected went wrong" in (tmp_path / "error_A_vs_B_2025-26.html").read_text(encoding="utf-8")


def test_debug_lets_a_bug_through_so_its_traceback_can_be_read(monkeypatch, tmp_path):
    monkeypatch.setattr(compare_cli, "generate_comparison_page", fail_with(KeyError("E1.total")))
    with pytest.raises(KeyError):
        main(["--company-a", "A", "--company-b", "B", "--fy", "2025-26", "--output-dir", str(tmp_path), "--debug"])
