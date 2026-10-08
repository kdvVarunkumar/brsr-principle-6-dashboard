"""Tests for the "too coarse to compare" rule: an intensity filed with ONE digit of precision cannot be compared with another year.

Real case (found by trying a company the tool was not built on): ICICI Bank filed its waste intensity as 0.0000000002 and then
0.0000000004.  That reads "exactly 100% more", but each figure can be off by up to half of its one digit, so the true change lies
anywhere from about +40% to +200%.  The figure stays as filed; only the claim about the change is withheld.
"""

import pytest
from xbrl_samples import both_years, write_xbrl

from brsr_p6.core.models import Status
from brsr_p6.extraction.extractor import build_report
from brsr_p6.extraction.values import significant_digits
from brsr_p6.parsing.xbrl_reader import read_filing

PHRASE = "rounded too coarsely"


def report_for(tmp_path, facts):
    return build_report(read_filing(write_xbrl(tmp_path, facts)), "Test Company Limited", "TEST", "2023-24")


def warnings_of(metric):
    return metric.current.warnings, metric.previous.warnings


# ------------------------------------------------------------------------------------------------ counting digits
@pytest.mark.parametrize("text, digits", [
    ("0.0000000004", 1), ("0.0000004786", 4), ("0.2", 1), ("0.20", 2), ("0.17", 2), ("4e-10", 1), ("4.5E-10", 2), ("2", 1),
    ("1200", 2), ("120", 2), ("1,83,595", 6), ("-0.08", 1), ("623812739.43", 11), ("0", 0), ("0.0", 0), ("", 0), ("NA", 0), ("1.2.3", 0),
])
def test_how_many_digits_of_precision_a_number_was_written_with(text, digits):
    assert significant_digits(text) == digits


# ------------------------------------------------------------------------------------------------ the check
def test_an_intensity_filed_with_one_digit_is_marked_too_coarse_in_both_years(tmp_path):
    metric = report_for(tmp_path, both_years("WaterIntensityPerRupeeOfTurnover", "0.0000000004", "0.0000000002", "KilolitersPerINR")).metrics["E3.intensity"]
    now, before = warnings_of(metric)
    assert len(now) == 1 and PHRASE in now[0] and "0.0000000004" in now[0]
    assert len(before) == 1 and "0.0000000002" in before[0]
    assert (metric.current.value, metric.previous.value) == (4e-10, 2e-10)              # the figure itself is never changed


def test_an_intensity_with_two_or_more_digits_is_left_alone(tmp_path):
    report = report_for(tmp_path, both_years("EnergyIntensityPerRupeeOfTurnover", "0.0000004786", "0.23", "GigajoulePerINR"))
    assert warnings_of(report.metrics["E1.intensity"]) == ([], [])


def test_only_the_one_digit_year_is_marked(tmp_path):
    metric = report_for(tmp_path, both_years("WaterIntensityPerRupeeOfTurnover", "0.0000004114", "0.0000004", "KilolitersPerINR")).metrics["E3.intensity"]
    now, before = warnings_of(metric)
    assert now == [] and len(before) == 1 and PHRASE in before[0]


def test_a_zero_intensity_keeps_its_own_warning_and_is_not_also_called_coarse(tmp_path):
    facts = (both_years("WaterIntensityPerRupeeOfTurnover", 0, 0, "KilolitersPerINR")
             + both_years("TotalVolumeOfWaterConsumption", 1000, 900, "Kilolitre"))
    now, _ = warnings_of(report_for(tmp_path, facts).metrics["E3.intensity"])
    assert len(now) == 1 and "never exactly 0" in now[0] and PHRASE not in now[0]


def test_an_amount_with_one_digit_is_not_an_intensity_and_is_not_marked(tmp_path):
    """5 tonnes of NOx is a plain whole number; the rule is only about rounded per-rupee ratios."""
    assert warnings_of(report_for(tmp_path, both_years("NOx", 5, 3, "Tonne")).metrics["E5.nox"]) == ([], [])


def test_the_waste_intensity_of_newer_filings_is_covered_too(tmp_path):
    extra = report_for(tmp_path, both_years("WasteIntensityPerRupeeOfTurnover", "0.0000000004", "0.0000000002", "TonnePerINR")).extras["X.waste_rupee"]
    assert PHRASE in extra.current.warnings[0] and PHRASE in extra.previous.warnings[0]


def test_a_value_the_filing_does_not_have_is_not_marked(tmp_path):
    cell = report_for(tmp_path, both_years("NOx", 1, 1, "Tonne")).metrics["E3.intensity"].current
    assert cell.status == Status.NOT_REPORTED and cell.warnings == []
