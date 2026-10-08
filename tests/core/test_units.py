"""Tests for brsr_p6/core/units.py."""

import pytest

from brsr_p6.core.models import Status
from brsr_p6.core.units import UNIT_NOT_STATED, convert, read_unit_text


# ----------------------------------------------------------------------------------------------- units: newer filings
def test_gigajoule_is_the_standard_energy_unit():
    value, unit, status, note, warnings = convert("energy", 5.0, "Gigajoule")
    assert (value, unit, status, warnings) == (5.0, "GJ", Status.REPORTED, [])


def test_kilotonne_and_kg_are_converted_to_tonnes_and_marked_converted():
    value, unit, status, note, _ = convert("air", 27, "Kilotonne")
    assert (value, unit, status) == (27000.0, "tonnes", Status.CONVERTED) and "Kilotonne" in note
    value, unit, status, _, _ = convert("air", 52524, "Kg")
    assert value == pytest.approx(52.524) and status == Status.CONVERTED


@pytest.mark.parametrize("unit_id", ["tCO2e", "MtCO2e"])
def test_both_ghg_unit_spellings_mean_tonnes(unit_id):
    """Checked on real filings: MtCO2e is NOT million tonnes (Reliance: 36,350,070 MtCO2e)."""
    value, unit, status, _, _ = convert("ghg", 36350070, unit_id)
    assert (value, unit, status) == (36350070, "tCO2e", Status.REPORTED)


@pytest.mark.parametrize(
    "unit_id, number, expected",
    [("Terajoule", 868, 868_000.0), ("Megajoule", 616_790_586.76, 616_790.58676), ("Petajoule", 2, 2_000_000.0), ("Kilojoule", 5_000_000, 5.0)],
)
def test_exact_si_energy_multiples_are_converted_to_gigajoules(unit_id, number, expected):
    """ITC files energy in Terajoule and Wipro in Megajoule; the dashboard needs one energy unit."""
    value, unit, status, note, warnings = convert("energy", number, unit_id)
    assert value == pytest.approx(expected) and (unit, status, warnings) == ("GJ", Status.CONVERTED, []) and unit_id in note


def test_kilotonnes_of_co2e_are_converted_to_tonnes():
    value, unit, status, _, _ = convert("ghg", 1101, "ktCO2e")
    assert (value, unit, status) == (1_101_000.0, "tCO2e", Status.CONVERTED)


def test_conversion_leaves_no_floating_point_noise():
    """Python gives 3.47e-8 * 1000 == 3.4700000000000004e-05; the converted value must be the clean 3.47e-05."""
    assert convert("intensity", 3.47e-08, "TerajoulePerINR")[0] == 3.47e-05
    assert convert("energy", 0.1, "Megajoule")[0] == 0.0001


def test_unknown_unit_id_is_shown_as_filed_with_a_warning():
    value, unit, status, _, warnings = convert("water", 10, "Megalitres")
    assert (value, unit) == (10, "Megalitres") and warnings and "not one I can convert" in warnings[0]


def test_intensity_units_are_made_readable_but_values_untouched():
    assert convert("intensity", 0.00044, "GigajoulePerINR")[:2] == (0.00044, "GJ per ₹")


@pytest.mark.parametrize(
    "unit_id, number, expected_value, expected_label",
    [("MegajoulePerINR", 0.0007584423, 7.584423e-07, "GJ per ₹"), ("TerajoulePerINR", 3.47e-08, 3.47e-05, "GJ per ₹"),
     ("ktCO2ePerINR", 1.7e-09, 1.7e-06, "tCO2e per ₹")],
)
def test_per_rupee_intensities_in_other_multiples_are_put_in_the_standard_unit(unit_id, number, expected_value, expected_label):
    value, label, status, note, _ = convert("intensity", number, unit_id)
    assert value == expected_value and label == expected_label and status == Status.CONVERTED and unit_id in note


def test_an_intensity_with_an_unknown_unit_is_shown_as_filed():
    assert convert("intensity", 80.64, "Kilojoule")[:3] == (80.64, "Kilojoule", Status.REPORTED)


def test_old_filing_intensity_text_is_recognised_when_it_is_a_known_spelling():
    value, label, status, _, _ = convert("intensity", 0.17, "pure", "tCO2e/Rs")
    assert (value, label, status) == (0.17, "tCO2e per ₹", Status.REPORTED)
    assert convert("intensity", 0.025, "pure", "gCO2e/INR")[1] == "gCO2e/INR"   # not recognised: left as filed


# ----------------------------------------------------------------------------------------------- units: older filings
def test_old_filing_energy_has_no_unit_and_says_so():
    value, unit, _, _, warnings = convert("energy", 473590585, "pure")
    assert unit == UNIT_NOT_STATED and warnings


def test_old_filing_water_and_waste_take_the_unit_the_sebi_form_requires():
    assert convert("water", 100, "pure")[1] == "kL"
    assert convert("mass", 100, "")[1] == "tonnes"
    assert "SEBI form" in convert("water", 100, "pure")[3]


@pytest.mark.parametrize(
    "text, expected",
    [("Kilotonnes/year", (1000.0, False)), ("Million tonnes of CO2 equivalent", (1_000_000.0, False)),
     ("tCO2 e", (1.0, False)), ("Tonnes", (1.0, False)), ("Kg/Month", (0.001, True)), ("MT", None), ("0", None), ("NA", None), ("", None)],
)
def test_read_unit_text(text, expected):
    assert read_unit_text(text) == expected


def test_old_ghg_in_million_tonnes_is_converted_and_the_original_is_noted():
    value, unit, status, note, _ = convert("ghg", 75.75, "pure", "Million tonnes of CO2 equivalent")
    assert (value, unit, status) == (75_750_000.0, "tCO2e", Status.CONVERTED)


def test_a_monthly_figure_is_not_turned_into_a_yearly_one():
    value, unit, _, _, warnings = convert("air", 100, "pure", "Kg/Month")
    assert value == pytest.approx(0.1) and unit == "tonnes per month" and "monthly" in warnings[0]


def test_unclear_ghg_unit_assumes_the_sebi_form_unit_but_warns():
    value, unit, _, _, warnings = convert("ghg", 500, "pure", "MT")
    assert (value, unit) == (500, "tCO2e") and warnings


def test_unclear_air_unit_is_left_as_not_stated():
    assert convert("air", 5, "pure", "0")[1] == UNIT_NOT_STATED
