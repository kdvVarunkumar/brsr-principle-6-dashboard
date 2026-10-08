"""Tests for brsr_p6/workflows/samples.py and the committed pages in samples/.

The most useful test here is "the committed samples are up to date": it rebuilds every page from the filings on disk and compares it
with the file in samples/.  If the templates or the rules change and nobody re-runs `python make_samples.py`, this fails.
"""

import json

import pytest
from html_checks import assert_well_formed

from brsr_p6.core.errors import BrsrError
from brsr_p6.core.fiscal_year import fiscal_years_between
from brsr_p6.core.paths import DEFAULT_RAW_DIR, SAMPLES_DIR
from brsr_p6.rendering.render import (error_page_path, render_compare_hub_page, render_error_page, render_hub_page, render_page,
                                      render_summary_page)
from brsr_p6.views.error_view import build_error_view
from brsr_p6.views.hub_view import SAMPLES_TITLE, build_compare_hub_view, build_hub_view
from brsr_p6.workflows import samples
from brsr_p6.workflows.hub import read_pages
from brsr_p6.workflows.pipeline import load_saved_report
from brsr_p6.workflows.samples import SAMPLE_COMPANIES, SAMPLE_COMPARISONS, SAMPLE_ERRORS, SAMPLE_SUMMARIES, SAMPLE_TRENDS, expected_files


def test_there_are_at_least_two_companies_and_the_assignments_error_cases():
    assert len(SAMPLE_COMPANIES) >= 2 and len({s.symbol for s in SAMPLE_COMPANIES}) == len(SAMPLE_COMPANIES)
    assert len(SAMPLE_ERRORS) >= 3 and len(SAMPLE_TRENDS) >= 2 and len(SAMPLE_SUMMARIES) >= 2


def test_every_sample_page_is_committed_and_well_formed():
    for name in expected_files():
        path = SAMPLES_DIR / name
        assert path.exists(), f"{name} is missing: run  python make_samples.py"
        assert_well_formed(path.read_text(encoding="utf-8"))


def test_the_samples_readme_lists_every_page():
    readme = (SAMPLES_DIR / "README.md").read_text(encoding="utf-8")
    for name in expected_files():
        assert f"({name})" in readme, name


def test_each_error_example_really_raises_the_error_it_claims(tmp_path):
    for example in SAMPLE_ERRORS:
        try:
            example.trigger()
        except BrsrError as error:
            assert build_error_view(error, example.company, example.fy, example.tool).message == str(error)
        except FileNotFoundError:
            pytest.skip("the saved filing list for an example is not on disk")
        else:
            pytest.fail(f"{example.company} {example.fy} did not raise an error")


def test_committed_report_pages_are_up_to_date():
    checked = 0
    for sample in SAMPLE_COMPANIES:
        report = load_saved_report(sample.symbol, sample.fy)
        if report is None:
            continue                                          # the filing is not on this machine: nothing to compare with
        committed = (SAMPLES_DIR / f"{sample.symbol}_{sample.fy}.html").read_text(encoding="utf-8")
        assert committed == render_page(report), f"{sample.symbol} {sample.fy} is out of date: run  python make_samples.py"
        checked += 1
    if not checked:
        pytest.skip("no sample filing is downloaded")


def test_committed_trend_pages_are_up_to_date(tmp_path):
    checked = 0
    for sample in SAMPLE_TRENDS:
        needed = [fy for fy in fiscal_years_between(sample.fy_from, sample.fy_to) if fy not in sample.not_filed]
        if any(load_saved_report(sample.symbol, fy) is None for fy in needed):
            continue                                          # a filing is not on this machine: nothing to compare with (and no internet in tests)
        page = samples._write_trend(sample, tmp_path, progress=lambda message: None)
        committed = (SAMPLES_DIR / page.name).read_text(encoding="utf-8")
        assert committed == page.read_text(encoding="utf-8"), f"{page.name} is out of date: run  python make_samples.py"
        checked += 1
    if not checked:
        pytest.skip("no trend sample filing is downloaded")


def test_the_trend_samples_show_the_cases_they_claim_to():
    tata = (SAMPLES_DIR / "TATASTEEL_trend_2021-22_to_2025-26.html").read_text(encoding="utf-8")
    assert "no filing on NSE; figures from the FY 2022-23 filing" in tata and "Reporting basis changed from" in tata and "mark-restated" in tata
    wipro = (SAMPLES_DIR / "WIPRO_trend_2023-24_to_2025-26.html").read_text(encoding="utf-8")
    assert wipro.count('class="basis basis-consolidated"') >= 2 and wipro.count('class="basis basis-standalone"') >= 1


def test_committed_summary_pages_are_up_to_date(tmp_path):
    checked = 0
    for sample in SAMPLE_SUMMARIES:
        found = samples._summary_reports(sample)
        if found is None:
            continue                                          # a filing is not on this machine: nothing to compare with (and no internet in tests)
        committed = (SAMPLES_DIR / f"{sample.symbol}_summary_{sample.fy}.html").read_text(encoding="utf-8")
        assert committed == render_summary_page(*found), f"{sample.symbol} summary {sample.fy} is out of date: run  python make_samples.py"
        checked += 1
    if not checked:
        pytest.skip("no summary sample filing is downloaded")


def test_the_summary_samples_show_the_cases_they_claim_to():
    tata = (SAMPLES_DIR / "TATASTEEL_summary_2025-26.html").read_text(encoding="utf-8")
    assert "1 improved, 3 stayed about the same and 4 got worse" in tata and "none of the figures shown was restated" in tata
    wipro = (SAMPLES_DIR / "WIPRO_summary_2025-26.html").read_text(encoding="utf-8")
    assert "9 improved, 0 stayed about the same and 0 got worse" in wipro and "These are the 3 biggest of the 9 figures that improved." in wipro
    assert "Nothing got worse by more than the “about the same” margin." in wipro and wipro.count('class="entry"') == 3
    reliance = (SAMPLES_DIR / "RELIANCE_summary_2022-23.html").read_text(encoding="utf-8")
    assert "NSE has no BRSR filing of its own for FY 2021-22." in reliance and "previous-year column of the FY 2022-23 filing" in reliance


def test_the_committed_viewers_list_every_sample_page_and_are_up_to_date():
    """samples/index.html (one company) and samples/compare_companies.html (two companies) must match what the code builds today."""
    pages = read_pages(SAMPLES_DIR)
    view = build_hub_view(pages, embed=False, title=SAMPLES_TITLE)
    compare_view = build_compare_hub_view(pages, embed=False, title=SAMPLES_TITLE)
    assert (SAMPLES_DIR / "index.html").read_text(encoding="utf-8") == render_hub_page(view), "samples/index.html is out of date: run  python make_samples.py"
    assert (SAMPLES_DIR / "compare_companies.html").read_text(encoding="utf-8") == render_compare_hub_page(compare_view), \
        "samples/compare_companies.html is out of date: run  python make_samples.py"
    shown = {entry.file for entry in view.entries} | {entry.file for entry in compare_view.entries}
    assert shown == set(expected_files()) - {"index.html", "compare_companies.html"}              # every page is behind one of the two viewers, and nothing else
    assert "html" not in json.loads(view.data_json)["entries"][0]                                  # linked, so the repository does not store each page twice


def test_the_viewers_group_the_samples_the_way_the_readme_does():
    pages = read_pages(SAMPLES_DIR)
    view = build_hub_view(pages, embed=False)
    counts = {kind: sum(entry.kind == kind for entry in view.entries) for kind in view.kinds}
    assert counts == {"Reports": len(SAMPLE_COMPANIES), "Year-on-year summaries": len(SAMPLE_SUMMARIES),
                      "Multi-year trends": len(SAMPLE_TRENDS), "Error pages": len(SAMPLE_ERRORS)}
    assert len(build_compare_hub_view(pages, embed=False).entries) == len(SAMPLE_COMPARISONS) == view.compare_count
    names = [company.name.casefold() for company in view.companies]
    assert names == sorted(names) and {company.symbol for company in view.companies} == {s.symbol for s in SAMPLE_COMPANIES}      # one entry per company, by name


def test_a_summary_sample_with_a_missing_previous_report_never_looks_for_one():
    reliance = next(s for s in SAMPLE_SUMMARIES if s.symbol == "RELIANCE")
    found = samples._summary_reports(reliance)
    if found is None:
        pytest.skip("Reliance FY 2022-23 is not downloaded")
    assert found[1] is None and found[2] == reliance.previous_note


def test_committed_error_pages_are_up_to_date():
    for example in SAMPLE_ERRORS:
        try:
            example.trigger()
        except BrsrError as error:
            path = error_page_path(example.company, example.fy, SAMPLES_DIR)
            committed = path.read_text(encoding="utf-8")
            assert committed == render_error_page(build_error_view(error, example.company, example.fy, example.tool)), f"{path.name} is out of date"
        except FileNotFoundError:
            continue


def test_make_samples_writes_every_page_and_the_readme(tmp_path, monkeypatch):
    monkeypatch.setattr(samples, "save_report", lambda report: None)          # do not touch data/parsed in a test
    if any(load_saved_report(s.symbol, s.fy) is None for s in SAMPLE_COMPANIES):
        pytest.skip("a sample filing is not downloaded (make_samples would use the internet)")
    pages = samples.make_samples(output_dir=tmp_path, progress=lambda message: None)
    written = {path.name for path in tmp_path.iterdir()}
    assert set(expected_files()) | {"README.md"} <= written and len(pages) == len(expected_files())


def test_the_filing_list_for_the_missing_year_example_comes_from_the_saved_listing():
    listing = DEFAULT_RAW_DIR / "TATASTEEL" / "filings_index.json"
    if not listing.exists():
        pytest.skip("Tata Steel's filing list is not on disk")
    with pytest.raises(BrsrError) as problem:
        samples._year_not_on_nse()
    assert "FY 2022-23" in str(problem.value)
