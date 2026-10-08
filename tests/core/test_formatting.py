"""Tests for brsr_p6/core/formatting.py."""

import pytest

from brsr_p6.core.formatting import format_number, format_number_html, indian_grouping


@pytest.mark.parametrize("digits, expected", [
    ("7", "7"), ("999", "999"), ("1000", "1,000"), ("12345", "12,345"), ("123456", "1,23,456"),
    ("24798900", "2,47,98,900"), ("1878224900", "1,87,82,24,900"),
])
def test_indian_grouping(digits, expected):
    assert indian_grouping(digits) == expected


@pytest.mark.parametrize("value, expected", [
    (0, "0"), (64.0, "64"), (3.02, "3.02"), (24798900.25, "2,47,98,900.25"), (18782249, "1,87,82,249"),
    (-1500.5, "-1,500.5"), (0.0004464728, "0.000446"), (0.82, "0.82"), (4.6e-06, "4.60e-06"), (1.234567, "1.23"),
])
def test_format_number(value, expected):
    assert format_number(value) == expected


def test_html_version_writes_tiny_numbers_with_a_superscript():
    assert str(format_number_html(4.6e-06)) == "4.60×10<sup>−6</sup>"
    assert str(format_number_html(2.5e-12)) == "2.50×10<sup>−12</sup>"
    assert str(format_number_html(1234567)) == "12,34,567"
