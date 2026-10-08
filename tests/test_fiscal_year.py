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
