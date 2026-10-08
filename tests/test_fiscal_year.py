"""Tests for brsr_p6/fiscal_year.py."""

import pytest

from brsr_p6.errors import InvalidFiscalYear, UnsupportedYear
from brsr_p6.fiscal_year import format_fiscal_year, parse_fiscal_year


@pytest.mark.parametrize(
    "text",
    ["2023-24", "2023-2024", "FY2023-24", "fy 2023-24", " 2023/24 ", "FY 2023-2024"],
)
def test_accepts_common_spellings(text):
    assert parse_fiscal_year(text) == "2023-24"


def test_century_boundary():
    assert parse_fiscal_year("2099-00") == "2099-00"


@pytest.mark.parametrize("text", ["2020-21", "2019-20", "FY2010-11"])
def test_years_before_fy_2021_22_are_rejected_with_a_clear_message(text):
    with pytest.raises(UnsupportedYear) as excinfo:
        parse_fiscal_year(text)
    assert "FY 2021-22" in str(excinfo.value)


@pytest.mark.parametrize("text", ["banana", "2023", "2023-25", "23-24", "", "2023-24-25"])
def test_garbage_is_rejected(text):
    with pytest.raises(InvalidFiscalYear):
        parse_fiscal_year(text)


def test_none_is_rejected():
    with pytest.raises(InvalidFiscalYear):
        parse_fiscal_year(None)


def test_format_fiscal_year():
    assert format_fiscal_year(2025, 2026) == "2025-26"


# ----------------------------------------------------------------------------------------------- year ranges (trend page)
def test_next_fiscal_year():
    from brsr_p6.fiscal_year import next_fiscal_year
    assert next_fiscal_year("2023-24") == "2024-25" and next_fiscal_year("2099-00") == "2100-01"


def test_fiscal_years_between_lists_every_year_oldest_first():
    from brsr_p6.fiscal_year import fiscal_years_between
    assert fiscal_years_between("2021-22", "2023-24") == ["2021-22", "2022-23", "2023-24"]
    assert fiscal_years_between("2022-23", "2022-23") == ["2022-23"]


def test_a_range_must_start_before_it_ends_and_not_be_too_long():
    from brsr_p6.errors import InvalidYearRange
    from brsr_p6.fiscal_year import MAX_TREND_YEARS, fiscal_years_between
    with pytest.raises(InvalidYearRange, match="after the end year"):
        fiscal_years_between("2024-25", "2022-23")
    with pytest.raises(InvalidYearRange, match="at most"):
        fiscal_years_between("2021-22", f"{2021 + MAX_TREND_YEARS}-{(2022 + MAX_TREND_YEARS) % 100:02d}")
