"""Tests for brsr_p6/workflows/missing_pages.py: the year-on-year summaries and trends the home page offers, made from saved filings.  All offline."""

from dashboard_samples import blank_report

from brsr_p6.core.fiscal_year import previous_fiscal_year
from brsr_p6.workflows.missing_pages import _latest_run, generate_missing_summaries, generate_missing_trends


def report(symbol, fy):
    made = blank_report(f"{symbol.title()} Limited")
    made.symbol, made.fy, made.previous_fy = symbol, fy, previous_fiscal_year(fy)
    return made


def loader_of(*saved):
    """A loader that has only the (symbol, year) filings given, and remembers what it was asked."""
    asked = []

    def load(symbol, fy):
        asked.append((symbol, fy))
        return report(symbol, fy) if (symbol, fy) in saved else None

    load.asked = asked
    return load


def report_pages(folder, *names):
    for name in names:
        (folder / f"{name}.html").write_text("<!doctype html><title>x</title><p>x</p>", encoding="utf-8")


def text(folder, name):
    return (folder / f"{name}.html").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------ year-on-year summaries
def test_a_summary_is_made_for_every_report_page_and_says_whether_last_years_own_filing_was_checked(tmp_path):
    report_pages(tmp_path, "AAA_2023-24", "AAA_2022-23", "BBB_2021-22")
    load = loader_of(("AAA", "2023-24"), ("AAA", "2022-23"), ("BBB", "2021-22"))
    assert generate_missing_summaries(tmp_path, load) == 3
    assert "own report was also checked" in text(tmp_path, "AAA_summary_2023-24")                                  # last year's filing is saved here
    assert "The FY 2021-22 filing is not saved on this computer" in text(tmp_path, "AAA_summary_2022-23")        # it is not: said, not guessed
    assert "BRSR reporting began with FY 2021-22, so there is no report for FY 2020-21" in text(tmp_path, "BBB_summary_2021-22")


def test_an_existing_summary_is_never_overwritten_and_not_even_loaded(tmp_path):
    report_pages(tmp_path, "AAA_2023-24", "AAA_summary_2023-24")
    (tmp_path / "AAA_summary_2023-24.html").write_text("made by summary.py", encoding="utf-8")
    load = loader_of(("AAA", "2023-24"))
    assert generate_missing_summaries(tmp_path, load) == 0
    assert text(tmp_path, "AAA_summary_2023-24") == "made by summary.py" and load.asked == []


def test_a_report_page_whose_filing_is_not_saved_gets_no_summary(tmp_path):
    report_pages(tmp_path, "AAA_2023-24")
    assert generate_missing_summaries(tmp_path, loader_of()) == 0 and not list(tmp_path.glob("*_summary_*"))


def test_only_report_pages_get_a_summary_not_trends_comparisons_or_summaries(tmp_path):
    report_pages(tmp_path, "AAA_trend_2021-22_to_2023-24", "AAA_vs_BBB_2023-24", "error_x_2023-24")
    load = loader_of(("AAA", "2023-24"))
    assert generate_missing_summaries(tmp_path, load) == 0 and load.asked == []


# ------------------------------------------------------------------------------------------------ multi-year trends
def test_the_newest_years_in_a_row_are_used_and_an_old_gap_ends_the_run():
    assert _latest_run(["2021-22", "2022-23", "2023-24"]) == ["2021-22", "2022-23", "2023-24"]
    assert _latest_run(["2021-22", "2023-24", "2024-25"]) == ["2023-24", "2024-25"]
    assert _latest_run(["2021-22", "2023-24"]) == ["2023-24"]


def test_a_trend_covers_the_years_a_company_has_in_a_row_and_is_named_after_them(tmp_path):
    report_pages(tmp_path, "AAA_2021-22", "AAA_2022-23", "AAA_2023-24")
    load = loader_of(("AAA", "2021-22"), ("AAA", "2022-23"), ("AAA", "2023-24"))
    assert generate_missing_trends(tmp_path, load) == 1
    page = text(tmp_path, "AAA_trend_2021-22_to_2023-24")
    assert "Aaa Limited" in page and "2021-22" in page and "2023-24" in page


def test_a_gap_in_the_saved_years_shortens_the_trend_instead_of_inventing_the_missing_year(tmp_path):
    report_pages(tmp_path, "AAA_2021-22", "AAA_2023-24", "AAA_2024-25")
    load = loader_of(("AAA", "2021-22"), ("AAA", "2023-24"), ("AAA", "2024-25"))
    assert generate_missing_trends(tmp_path, load) == 1
    assert (tmp_path / "AAA_trend_2023-24_to_2024-25.html").exists() and not list(tmp_path.glob("AAA_trend_2021-22*"))


def test_a_company_with_one_saved_year_gets_no_trend(tmp_path):
    report_pages(tmp_path, "AAA_2023-24", "BBB_2021-22", "BBB_2023-24")             # BBB has two pages, but only one filing on disk
    load = loader_of(("AAA", "2023-24"), ("BBB", "2023-24"))
    assert generate_missing_trends(tmp_path, load) == 0 and not list(tmp_path.glob("*_trend_*"))


def test_a_company_that_already_has_a_trend_page_keeps_it(tmp_path):
    report_pages(tmp_path, "AAA_2022-23", "AAA_2023-24", "AAA_trend_2021-22_to_2023-24")       # made by trends.py, which knows what NSE has
    load = loader_of(("AAA", "2022-23"), ("AAA", "2023-24"))
    assert generate_missing_trends(tmp_path, load) == 0 and load.asked == []
    assert not (tmp_path / "AAA_trend_2022-23_to_2023-24.html").exists()


def test_each_company_gets_its_own_trend(tmp_path):
    report_pages(tmp_path, "AAA_2022-23", "AAA_2023-24", "BBB_2022-23", "BBB_2023-24")
    load = loader_of(("AAA", "2022-23"), ("AAA", "2023-24"), ("BBB", "2022-23"), ("BBB", "2023-24"))
    assert generate_missing_trends(tmp_path, load) == 2
    assert sorted(p.name for p in tmp_path.glob("*_trend_*")) == ["AAA_trend_2022-23_to_2023-24.html", "BBB_trend_2022-23_to_2023-24.html"]
