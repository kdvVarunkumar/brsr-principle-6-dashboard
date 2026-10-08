"""Tests for brsr_p6/friendly.py (how numbers are said on the dashboard)."""

import pytest

from brsr_p6.friendly import CRORE, LAKH, number_text, percent_change_text, points_text, scale_for, share_text, unit_text


@pytest.mark.parametrize(
    "value, expected",
    [(464_200_812, (CRORE, "crore")), (10_000_000, (CRORE, "crore")), (9_999_999, (LAKH, "lakh")), (666_046, (LAKH, "lakh")),
     (100_000, (LAKH, "lakh")), (99_999, (1, "")), (32_485, (1, "")), (0, (1, ""))],
)
def test_scale_picks_crore_lakh_or_nothing(value, expected):
    assert scale_for(value) == expected


def test_scaled_numbers_have_two_decimals_at_most():
    assert number_text(464_200_812, CRORE) == "46.42"
    assert number_text(37_682_039, CRORE) == "3.77"
    assert number_text(666_046, LAKH) == "6.66"
    assert number_text(2_426_470, LAKH) == "24.26"
    assert number_text(30_000_000, CRORE) == "3"           # no useless zeros


@pytest.mark.parametrize(
    "value, expected",
    [(32_485, "32,485"), (1_280, "1,280"), (807.367, "807"), (65.539, "65.5"), (3.7682, "3.77"), (0.17, "0.17"), (0.0061, "0.0061"),
     (0, "0"), (99_229, "99,229"), (83_624, "83,624")],
)
def test_plain_numbers_choose_their_decimals_by_size(value, expected):
    assert number_text(value) == expected


def test_shares_and_changes_are_rounded_sensibly():
    assert [share_text(x) for x in (97.055, 1.471, 0.031, 0.004, 0)] == ["97.1", "1.47", "0.03", "<0.01", "0"]
    assert [percent_change_text(x) for x in (-1.98, 0.15, 14.13, 240.4)] == ["2.0%", "0.15%", "14.1%", "240%"]
    assert [points_text(x) for x in (0.055, -0.153, 12.34)] == ["0.06", "0.15", "12.3"]


def test_units_read_naturally():
    assert unit_text("GJ", "crore") == "crore GJ"
    assert unit_text("tCO2e", "crore") == "crore tonnes CO₂e"
    assert unit_text("tCO2e per ₹ crore") == "tCO₂e per ₹ crore"
    assert unit_text("(unit not stated)") == "unit not stated"
    assert unit_text("tonnes") == "tonnes"
