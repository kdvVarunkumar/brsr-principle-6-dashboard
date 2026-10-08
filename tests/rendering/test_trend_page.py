"""Tests for the multi-year trend page: rendering (templates/trends.html), the trends.py command, and real filings."""

from pathlib import Path

import pytest
from dashboard_samples import blank_report, put
from html_checks import assert_well_formed

from brsr_p6.analysis.trend_model import NOT_FILED, UNREADABLE, YearEntry, build_trend
from brsr_p6.cli import trend_cli
from brsr_p6.cli.trend_cli import build_parser, main
from brsr_p6.core.errors import NoFilingFound, UnknownCompany
from brsr_p6.core.fiscal_year import fiscal_years_between
from brsr_p6.core.paths import DEFAULT_RAW_DIR
from brsr_p6.rendering.render import render_trend_page, trend_page_path, write_trend_page
from brsr_p6.views.trend_view import build_trend_view
from brsr_p6.workflows.pipeline import load_saved_report


def year(fy, boundary="Standalone basis", energy=None, previous=None):
    r = blank_report("Test Company Limited")
    r.fy, r.boundary, r.family, r.submission_date = fy, boundary, "modern", "01-Jul-2024"
    if energy is not None:
        put(r, "E1.total", energy, previous, unit="GJ")
    return YearEntry(fy, r)


def demo_trend(*extra):
    return build_trend("Test Company Limited", "TESTCO", [YearEntry("2021-22", problem="NSE has no BRSR filing for this year.", kind=NOT_FILED),
                                                          year("2022-23", "Consolidated basis", 900, 800), year("2023-24", energy=500, previous=300),
                                                          year("2024-25", energy=550, previous=520), *extra])


# ------------------------------------------------------------------------------------------------ the page
def test_the_trend_page_is_well_formed_and_has_every_part():
    html = render_trend_page(demo_trend())
    assert_well_formed(html)
    for text in ("Test Company Limited", "Trends from FY 2021-22 to FY 2024-25", "How have the environmental figures changed over the years?",
                 "Read this before comparing years", "FY 2021-22", "no filing on NSE; figures from the FY 2022-23 filing", "Consolidated", "Standalone",
                 "Trend (same basis)", "Every figure, year by year", 'class="trendtable"', "Total energy used", "Essential 1"):
        assert text in html, text


def test_every_year_is_a_column_in_every_table():
    html = render_trend_page(demo_trend())
    first_table = html[html.index('<table class="trendtable">'):html.index("</table>")]
    assert first_table.count('class="yearcol') == 4


def test_the_table_class_does_not_collide_with_the_dashboards_flex_rule():
    """A class called 'trend' once turned the table into a flexbox (the dashboard's .trend rule); never use that name for the table."""
    html = render_trend_page(demo_trend())
    assert '<table class="trend"' not in html and '<table class="trend ' not in html and '<table class="trendtable' in html


def test_text_from_a_filing_cannot_inject_html_into_the_trend_page():
    evil = "<script>alert(1)</script>"
    trend = build_trend("Test Company Limited", "TESTCO", [year("2022-23", energy=1, previous=1), YearEntry("2023-24", problem=evil, kind=UNREADABLE)])
    html = render_trend_page(trend)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_the_page_never_prints_a_bare_zero_for_a_year_without_a_filing():
    trend = build_trend("T", "T", [year("2022-23", energy=10, previous=1), YearEntry("2023-24", problem="x", kind=NOT_FILED)])
    html = render_trend_page(trend)
    assert ">No filing<" in html and '<span class="v num">0</span>' not in html


def test_the_file_name_names_the_company_and_the_years(tmp_path):
    trend = demo_trend()
    assert trend_page_path(trend, tmp_path).name == "TESTCO_trend_2021-22_to_2024-25.html"
    path = write_trend_page(trend, tmp_path / "new")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("<!doctype html>")


# ------------------------------------------------------------------------------------------------ the command
def test_the_parser_reads_company_and_an_optional_range():
    args = build_parser().parse_args(["--company", "Tata Steel", "--from", "2021-22", "--to", "2025-26", "--open"])
    assert (args.company, args.fy_from, args.fy_to, args.open) == ("Tata Steel", "2021-22", "2025-26", True)
    defaults = build_parser().parse_args(["--company", "Reliance"])
    assert defaults.fy_from is None and defaults.fy_to is None and defaults.debug is False


def fake_generate(trend, seen=None):
    def generate(company, fy_from, fy_to, output_dir=None, progress=None):
        if seen is not None:
            seen.update(company=company, fy_from=fy_from, fy_to=fy_to, output_dir=output_dir)
        return Path("output/TESTCO_trend.html"), trend
    return generate


def test_the_command_reports_where_the_trend_page_was_written(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(trend_cli, "generate_trend_page", fake_generate(demo_trend(), seen))
    assert main(["--company", "Test", "--from", "2021-22", "--to", "2024-25", "--output-dir", "samples"]) == 0
    out = capsys.readouterr().out
    assert "TESTCO_trend.html" in out and "FY 2021-22 to FY 2024-25" in out
    assert seen == {"company": "Test", "fy_from": "2021-22", "fy_to": "2024-25", "output_dir": Path("samples")}


def fail_with(error):
    def fail(company, fy_from, fy_to, output_dir=None, progress=None):
        raise error
    return fail


def test_a_failed_trend_request_writes_an_error_page_with_trends_commands(monkeypatch, capsys, tmp_path):
    error = NoFilingFound("NSE has no BRSR filing for Tata Steel in FY 2018-19 to FY 2019-20.", symbol="TATASTEEL", available=["2022-23", "2025-26"])
    monkeypatch.setattr(trend_cli, "generate_trend_page", fail_with(error))
    assert main(["--company", "Tata Steel", "--from", "2021-22", "--to", "2025-26", "--output-dir", str(tmp_path)]) == 1
    assert "explanation page was written" in capsys.readouterr().out
    page = (tmp_path / "error_Tata_Steel_2021-22_to_2025-26.html").read_text(encoding="utf-8")
    assert "python trends.py --company" in page and "--from 2022-23 --to 2025-26" in page and "main.py --company" not in page


def test_an_unknown_company_in_a_trend_request_gets_the_unknown_company_page(monkeypatch, tmp_path):
    monkeypatch.setattr(trend_cli, "generate_trend_page", fail_with(UnknownCompany("No NSE-listed company matches 'Xyzzy'.")))
    main(["--company", "Xyzzy", "--output-dir", str(tmp_path)])
    page = (tmp_path / "error_Xyzzy_earliest_to_latest.html").read_text(encoding="utf-8")
    assert "We could not find that company on NSE" in page


def test_a_bug_in_a_trend_request_is_explained_and_debug_shows_the_traceback(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(trend_cli, "generate_trend_page", fail_with(KeyError("E1.total")))
    assert main(["--company", "Test", "--output-dir", str(tmp_path)]) == 1
    assert "Unexpected problem" in capsys.readouterr().out
    with pytest.raises(KeyError):
        main(["--company", "Test", "--output-dir", str(tmp_path), "--debug"])


# ------------------------------------------------------------------------------------------------ real filings on disk
def disk_trend(symbol):
    years = sorted(p.name for p in (DEFAULT_RAW_DIR / symbol).iterdir() if p.is_dir() and list(p.glob("*.xml")))
    entries = []
    for fy in fiscal_years_between("2021-22", years[-1]):
        report = load_saved_report(symbol, fy)
        entries.append(YearEntry(fy, report) if report else YearEntry(fy, problem="NSE has no BRSR filing for this year.", kind=NOT_FILED))
    return build_trend(next((e.report.company_name for e in entries if e.report), symbol), symbol, entries)


def downloaded_companies():
    if not DEFAULT_RAW_DIR.exists():
        return []
    return sorted(p.name for p in DEFAULT_RAW_DIR.iterdir() if p.is_dir() and any(p.glob("*/*.xml")))


def test_the_trend_page_is_well_formed_and_honest_for_every_downloaded_company():
    companies = downloaded_companies()
    if not companies:
        pytest.skip("no filings downloaded")
    for symbol in companies:
        trend = disk_trend(symbol)
        view = build_trend_view(trend)
        assert_well_formed(render_trend_page(trend))
        for topic in view.topics:
            for row in topic.rows:
                assert len(row.cells) == len(trend.columns), (symbol, row.label)
                for cell, column in zip(row.cells, trend.columns):
                    assert str(cell.text), (symbol, row.label)
                    if column.source == "none":
                        assert str(cell.text) == "No filing" and cell.bar is None, (symbol, row.label)      # never a zero for a missing year
                    if cell.css in ("empty", "doubtful"):
                        assert cell.bar is None, (symbol, row.label)
                    assert all(mark.title for mark in cell.marks), (symbol, row.label)


def test_tata_steels_basis_change_is_detected_and_keeps_the_verdict_on_one_basis():
    if load_saved_report("TATASTEEL", "2022-23") is None or load_saved_report("TATASTEEL", "2025-26") is None:
        pytest.skip("Tata Steel filings are not downloaded")
    view = build_trend_view(disk_trend("TATASTEEL"))
    assert [c.basis_text for c in view.columns][:3] == ["Consolidated", "Consolidated", "Standalone"]
    assert view.columns[0].source == "borrowed" and "FY 2022-23" in view.columns[0].note          # FY 2021-22 is not on NSE
    energy = next(r for t in view.topics for r in t.rows if r.label == "Total energy used")
    assert "since" not in energy.trend and "FY 2023-24" in energy.trend                            # compared on the standalone years only
    assert any(n.kind == "basis" for n in view.notes) and any(n.kind == "missing" for n in view.notes)
