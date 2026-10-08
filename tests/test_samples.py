"""Tests for brsr_p6/samples.py and the committed pages in samples/.

The most useful test here is "the committed samples are up to date": it rebuilds every page from the filings on disk and compares it
with the file in samples/.  If the templates or the rules change and nobody re-runs `python make_samples.py`, this fails.
"""

import pytest
from html_checks import assert_well_formed

from brsr_p6 import samples
from brsr_p6.downloader import DEFAULT_RAW_DIR
from brsr_p6.error_view import build_error_view
from brsr_p6.errors import BrsrError
from brsr_p6.fiscal_year import fiscal_years_between
from brsr_p6.pipeline import load_saved_report
from brsr_p6.render import error_page_path, render_error_page, render_page
from brsr_p6.samples import SAMPLE_COMPANIES, SAMPLE_ERRORS, SAMPLE_TRENDS, SAMPLES_DIR, expected_files


def test_there_are_at_least_two_companies_and_the_assignments_error_cases():
    assert len(SAMPLE_COMPANIES) >= 2 and len({s.symbol for s in SAMPLE_COMPANIES}) == len(SAMPLE_COMPANIES)
    assert len(SAMPLE_ERRORS) >= 3 and len(SAMPLE_TRENDS) >= 2


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
            assert build_error_view(error, example.company, example.fy, example.trends).message == str(error)
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


def test_committed_error_pages_are_up_to_date():
    for example in SAMPLE_ERRORS:
        try:
            example.trigger()
        except BrsrError as error:
            path = error_page_path(example.company, example.fy, SAMPLES_DIR)
            committed = path.read_text(encoding="utf-8")
            assert committed == render_error_page(build_error_view(error, example.company, example.fy, example.trends)), f"{path.name} is out of date"
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
