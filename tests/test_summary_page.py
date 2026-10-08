"""Tests for the year-on-year summary page: rendering (templates/summary.html), the summary.py command, and real filings."""

from pathlib import Path

import pytest
from dashboard_samples import blank_report, put
from html_checks import assert_well_formed
from test_summary_view import demo_report, last_years_own_report

from brsr_p6 import summary_cli
from brsr_p6.comparison import HIGHER, IMPROVED, SAME, WORSE
from brsr_p6.dashboard_cards import build_card
from brsr_p6.downloader import DEFAULT_RAW_DIR
from brsr_p6.errors import InvalidFiscalYear, NoFilingFound, UnknownCompany, UnparseableFiling
from brsr_p6.metric_info import METRICS
from brsr_p6.pipeline import load_saved_report
from brsr_p6.render import render_summary_page, summary_page_path, write_summary_page
from brsr_p6.summary_cli import build_parser, main
from brsr_p6.summary_view import TOP, build_summary_view


# ------------------------------------------------------------------------------------------------ the page
def test_the_summary_page_is_well_formed_and_has_every_part():
    html = render_summary_page(demo_report())
    assert_well_formed(html)
    for text in ("Test Company Limited", "FY 2023-24 compared with FY 2022-23", "What got better, and what got worse, in FY 2023-24?",
                 "How we decide what is “better”", "The biggest improvements", "The biggest setbacks", "Every figure we compared",
                 "Not ranked, and why", "Where last year's figures come from", 'class="sumtable"', "Lower is better here, so this is a step backwards."):
        assert text in html, text


def test_the_page_shows_exactly_three_entries_per_list():
    html = render_summary_page(demo_report())
    best = html[html.index('id="sum-best-h"'):html.index('id="sum-worst-h"')]
    worst = html[html.index('id="sum-worst-h"'):html.index('id="sum-table-h"')]
    assert best.count('class="entry"') == TOP and worst.count('class="entry"') == TOP


def test_the_shown_figures_are_starred_in_the_table():
    html = render_summary_page(demo_report())
    table = html[html.index('class="sumtable"'):html.index("</table>")]
    assert table.count("★") == 6 and table.count('class="shown"') == 6


def test_a_page_with_nothing_comparable_still_renders_and_says_why():
    html = render_summary_page(blank_report())
    assert_well_formed(html)
    assert "figures can be compared between FY 2022-23 and FY 2023-24" in html and "Not ranked, and why" in html
    assert "Every figure we compared" not in html                                       # no empty table
    assert 'class="entry"' not in html


def test_text_from_a_filing_cannot_inject_html_into_the_summary_page():
    evil = "<script>alert(1)</script>"
    report = demo_report()
    report.company_name = evil
    html = render_summary_page(report, None, evil)
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;alert(1)&lt;/script&gt;" in html


def test_the_missing_previous_report_note_appears_on_the_page():
    html = render_summary_page(demo_report(), None, "NSE has no BRSR filing of its own for FY 2022-23.")
    assert "NSE has no BRSR filing of its own for FY 2022-23." in html


def test_a_restated_figure_is_explained_on_the_page():
    html = render_summary_page(demo_report(), last_years_own_report(40_000))
    assert "restates it as 46,000 tonnes" in html


def test_the_file_name_names_the_company_and_the_year(tmp_path):
    report = demo_report()
    assert summary_page_path(report, tmp_path).name == "TEST_summary_2023-24.html"
    path = write_summary_page(report, output_dir=tmp_path / "new")
    assert path.exists() and path.read_text(encoding="utf-8").startswith("<!doctype html>")


# ------------------------------------------------------------------------------------------------ the command
def test_the_parser_reads_a_company_and_an_optional_year():
    args = build_parser().parse_args(["--company", "Tata Steel", "--fy", "2024-25", "--open"])
    assert (args.company, args.fy, args.open) == ("Tata Steel", "2024-25", True)
    defaults = build_parser().parse_args(["--company", "Reliance"])
    assert defaults.fy is None and defaults.debug is False


def fake_generate(report, seen=None):
    def generate(company, fy, output_dir=None, progress=None):
        if seen is not None:
            seen.update(company=company, fy=fy, output_dir=output_dir)
        return Path("output/TEST_summary_2023-24.html"), report
    return generate


def test_the_command_reports_where_the_summary_was_written(monkeypatch, capsys):
    seen = {}
    monkeypatch.setattr(summary_cli, "generate_summary_page", fake_generate(demo_report(), seen))
    assert main(["--company", "Test", "--fy", "2023-24", "--output-dir", "samples"]) == 0
    out = capsys.readouterr().out
    assert "TEST_summary_2023-24.html" in out and "FY 2023-24 compared with FY 2022-23" in out
    assert seen == {"company": "Test", "fy": "2023-24", "output_dir": Path("samples")}


def fail_with(error):
    def fail(company, fy, output_dir=None, progress=None):
        raise error
    return fail


def test_a_missing_year_writes_an_error_page_with_summary_commands(monkeypatch, capsys, tmp_path):
    error = NoFilingFound("NSE has no BRSR filing for Tata Steel for FY 2019-20.", symbol="TATASTEEL", available=["2022-23", "2025-26"])
    monkeypatch.setattr(summary_cli, "generate_summary_page", fail_with(error))
    assert main(["--company", "Tata Steel", "--fy", "2019-20", "--output-dir", str(tmp_path)]) == 1
    assert "explanation page was written" in capsys.readouterr().out
    page = (tmp_path / "error_Tata_Steel_2019-20.html").read_text(encoding="utf-8")
    assert "python summary.py --company" in page and "--fy 2022-23" in page and "--fy 2025-26" in page and "main.py --company" not in page


def test_a_damaged_latest_filing_gets_the_unreadable_filing_page(monkeypatch, tmp_path):
    error = UnparseableFiling("The FY 2025-26 filing of Tata Steel Limited could not be used: not valid XML.")
    monkeypatch.setattr(summary_cli, "generate_summary_page", fail_with(error))
    main(["--company", "Tata Steel", "--output-dir", str(tmp_path)])
    page = (tmp_path / "error_Tata_Steel_latest.html").read_text(encoding="utf-8")
    assert "could not be used: not valid XML." in page and "We show nothing rather than guess." in page


def test_an_unknown_company_gets_the_unknown_company_page(monkeypatch, tmp_path):
    monkeypatch.setattr(summary_cli, "generate_summary_page", fail_with(UnknownCompany("No NSE-listed company matches 'Xyzzy'.")))
    main(["--company", "Xyzzy", "--output-dir", str(tmp_path)])
    assert "We could not find that company on NSE" in (tmp_path / "error_Xyzzy_latest.html").read_text(encoding="utf-8")


def test_a_bad_year_gets_its_own_page_and_the_suggested_command_has_no_garbage_year(monkeypatch, tmp_path):
    monkeypatch.setattr(summary_cli, "generate_summary_page", fail_with(InvalidFiscalYear("'banana' is not a financial year.")))
    main(["--company", "Tata Steel", "--fy", "banana", "--output-dir", str(tmp_path)])
    page = (tmp_path / "error_Tata_Steel_banana.html").read_text(encoding="utf-8")
    assert "banana" in page and "--fy banana" not in page


def test_a_bug_is_explained_and_debug_shows_the_traceback(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(summary_cli, "generate_summary_page", fail_with(KeyError("E1.total")))
    assert main(["--company", "Test", "--output-dir", str(tmp_path)]) == 1
    assert "Unexpected problem" in capsys.readouterr().out
    with pytest.raises(KeyError):
        main(["--company", "Test", "--output-dir", str(tmp_path), "--debug"])


# ------------------------------------------------------------------------------------------------ real filings on disk
def downloaded_years():
    """[(symbol, fy)] for every filing on disk: any of them can be summarised, because each carries last year's column."""
    if not DEFAULT_RAW_DIR.exists():
        return []
    return sorted((p.parent.name, p.name) for p in DEFAULT_RAW_DIR.glob("*/*") if p.is_dir() and any(p.glob("*.xml")))


def score(entry):
    """Positive = better, in percent (amounts) or percentage points (shares): the number the summary ranks by."""
    better = next(i.better for i in METRICS if i.id == entry.card.id)
    return entry.card.change if better == HIGHER else -entry.card.change


def test_the_summary_is_honest_and_well_formed_for_every_downloaded_filing():
    years = downloaded_years()
    if not years:
        pytest.skip("no filings downloaded")
    for symbol, fy in years:
        report = load_saved_report(symbol, fy)
        view = build_summary_view(report)
        where = (symbol, fy)
        assert_well_formed(render_summary_page(report))

        assert len(view.best) <= TOP and len(view.worst) <= TOP, where
        assert all(e.card.verdict == IMPROVED for e in view.best) and all(e.card.verdict == WORSE for e in view.worst), where
        assert [score(e) for e in view.best] == sorted((score(e) for e in view.best), reverse=True), where     # best first
        assert [score(e) for e in view.worst] == sorted(score(e) for e in view.worst), where                   # worst first

        titles = [row.title for row in view.table]
        assert len(titles) == len(set(titles)), where                                                          # a figure appears once
        cards = {i.id: build_card(report, i) for i in METRICS if i.headline}
        comparable = {i for i, c in cards.items() if c is not None and c.verdict in (IMPROVED, WORSE, SAME)}
        for intensity in (i for i in METRICS if i.replaces and i.id in comparable):                            # never a total AND its per-sales figure
            total = next(i for i in METRICS if i.id == intensity.replaces)
            assert total.title not in titles, (where, total.id)
            assert any(item.title == total.title and "fairer measure" in item.reason for item in view.left_out), (where, total.id)

        assert len(view.table) + len(view.left_out) == sum(c is not None for c in cards.values()), where       # nothing silently dropped
        assert all(item.reason for item in view.left_out), where
        assert view.improved == sum("Improved" in r.chip_text for r in view.table), where
        assert view.same_count == sum("About the same" in r.chip_text for r in view.table), where
        assert view.worse == sum("Got worse" in r.chip_text for r in view.table), where


def test_tata_steels_summary_matches_the_filing():
    this, before = load_saved_report("TATASTEEL", "2025-26"), load_saved_report("TATASTEEL", "2024-25")
    if this is None or before is None:
        pytest.skip("Tata Steel filings are not downloaded")
    view = build_summary_view(this, before)
    assert (view.improved, view.same_count, view.worse) == (1, 3, 4)
    assert [e.card.id for e in view.best] == ["water_intensity"] and [e.card.id for e in view.worst] == ["air_sox", "air_nox", "air_pm"]
    assert view.worst[0].headline == "SOx (sulphur oxides) was 45.7% more than last year."
    assert "none of the figures shown was restated" in view.source_note
    assert any(item.title == "Total energy used" and "fairer measure" in item.reason for item in view.left_out)
    assert any("total energy used was 6.2% more than last year" in text for text in view.same)              # the rise is not hidden
