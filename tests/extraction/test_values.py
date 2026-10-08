"""Tests for brsr_p6/extraction/values.py."""

import pytest

from brsr_p6.extraction.values import clean_number, clean_text, clean_yes_no


@pytest.mark.parametrize(
    "text, expected",
    [("12.5", 12.5), ("1,83,595", 183595.0), (" 1,234 ", 1234.0), ("0", 0.0), ("-3.5", -3.5), ("1e-7", 1e-7)],
)
def test_clean_number_reads_numbers(text, expected):
    assert clean_number(text) == expected


@pytest.mark.parametrize("text", [None, "", "  ", "NA", "N/A", "-", "nil", "Not applicable", "abc", "12 tonnes"])
def test_clean_number_never_turns_nothing_into_zero(text):
    assert clean_number(text) is None


@pytest.mark.parametrize(
    "text, answer, understood",
    [("true", "Yes", True), ("Yes", "Yes", True), ("Y", "Yes", True), ("false", "No", True), ("No", "No", True),
     ("NA", "Not applicable", True), ("n/a", "Not applicable", True), ("Maybe", "Maybe", False)],
)
def test_clean_yes_no(text, answer, understood):
    assert clean_yes_no(text) == (answer, understood)


def test_clean_text():
    assert clean_text("  a \n  b ") == "a b"
    assert clean_text("   ") is None
    assert clean_text(None) is None
