"""Tests for brsr_p6/dashboard_cards.py: one figure -> one card."""

from dashboard_samples import NO_UNIT, SCALE_SLIP, ZERO_MEANING, blank_report, put

from brsr_p6.comparison import IMPROVED, SAME, UNSURE, WORSE
from brsr_p6.dashboard_cards import build_card, per_crore
from brsr_p6.metric_info import METRICS
from brsr_p6.models import Cell, Status

INFO = {info.id: info for info in METRICS}


def card(report, card_id):
    return build_card(report, INFO[card_id])


# ------------------------------------------------------------------------------------------------ a normal card
def test_a_normal_card_says_the_number_the_direction_and_where_it_came_from():
    report = blank_report()
    put(report, "E1.total", 464_200_812, 473_590_585)
    c = card(report, "energy_total")
    assert (c.big, c.unit, c.verdict, c.chip_text) == ("46.42", "crore GJ", IMPROVED, "✔ Improved")
    assert c.trend == "▼ 2.0% lower than last year" and c.better_label == "Lower is better ↓"
    assert [(b.label, b.text) for b in c.bars] == [("2023-24", "46.42"), ("2022-23", "47.36")]
    assert c.bars[1].percent == 100 and 97 < c.bars[0].percent < 99          # bars start at zero, the longer one is full width
    assert c.badge == "✔ Reported by the company" and c.alerts == [] and c.css == ""
    assert c.quote == "46.42 crore GJ" and c.delta_words == "2.0% less than last year"
    assert c.what and c.why                                                   # every card explains itself


def test_every_figure_has_a_title_a_what_and_a_direction():
    for info in METRICS:
        assert info.title and info.what and info.better, info.id
        if info.size == "card":
            assert info.why, f"{info.id} has no 'why it matters'"


# ------------------------------------------------------------------------------------------------ intensity per rupee crore
def test_intensity_is_shown_per_rupee_crore_and_the_filed_figure_is_kept_in_the_fine_print():
    report = blank_report()
    put(report, "E1.intensity", 8.07367e-05, 8.19236e-05, unit="GJ per ₹")
    c = card(report, "energy_intensity")
    assert (c.big, c.unit, c.title) == ("807", "GJ per ₹ crore", "Energy for every ₹ 1 crore of sales")
    assert "per ₹ crore" in c.badge and any("Filed as 8.07367e-05 GJ per ₹" in line for line in c.fine)


def test_an_intensity_in_an_unclear_unit_is_not_dressed_up_as_per_rupee_crore():
    report = blank_report()
    put(report, "E1.intensity", 1024.43, 1015.18, unit="(unit not stated)", warnings=[NO_UNIT])
    c = card(report, "energy_intensity")
    assert c.title == "Energy per unit of sales" and c.unit == "unit not stated" and "crore" not in c.badge
    assert c.trust == "check"


def test_per_crore_converts_only_per_rupee_units_and_without_float_noise():
    converted = per_crore(Cell(3.47e-05, "GJ per ₹", Status.CONVERTED))
    assert converted.value == 347.0 and converted.unit == "GJ per ₹ crore"
    untouched = Cell(5.0, "(unit not stated)", Status.REPORTED)
    assert per_crore(untouched) is untouched and per_crore(Cell()).status == Status.NOT_REPORTED


# ------------------------------------------------------------------------------------------------ missing and doubtful
def test_a_missing_figure_says_not_reported_and_never_shows_zero_or_an_arrow():
    c = card(blank_report(), "ghg_scope3")
    assert (c.big, c.has_number, c.unit, c.verdict, c.css) == ("Not reported", False, "", UNSURE, "empty")
    assert c.trend == "No figure for either year." and c.bars == [] and c.quote == ""
    assert "optional" in c.badge and "never means zero" in c.badge


def test_a_doubtful_figure_is_shown_as_filed_but_not_compared_or_quoted():
    report = blank_report()
    put(report, "E6.scope1", 64, 61, unit="tCO2e", warnings=[SCALE_SLIP])
    put(report, "E6.scope2", 5, 5, unit="tCO2e", warnings=[SCALE_SLIP])
    c = card(report, "ghg_total")
    assert (c.big, c.verdict, c.trust, c.css) == ("69", UNSURE, "doubtful", "doubtful")
    assert c.bars == [] and c.alerts == [SCALE_SLIP] and c.badge.startswith("⚠ Check this figure")


def test_an_intensity_filed_as_zero_is_not_shown_as_a_real_zero():
    report = blank_report()
    put(report, "E6.intensity", 0, 0, unit="tCO2e per ₹",
        warnings=["Reported as 0, but the total it relates to is not zero. A real intensity is never exactly 0, so this 0 means "
                  "'rounded away or left blank'; it is not a real zero."])
    c = card(report, "ghg_intensity")
    assert (c.big, c.has_number, c.verdict, c.value) == ("Filed as 0", False, UNSURE, None)


def test_a_zero_last_year_is_not_called_worse():
    report = blank_report()
    put(report, "E3.withdrawal_total", 2_167_000, 0, unit="kL")
    c = card(report, "water_in")
    assert c.verdict == UNSURE and "was 0" in c.trend and c.bars == []


def test_years_in_different_units_are_not_compared():
    report = blank_report()
    put(report, "E1.total", 500, 400, unit="GJ")
    report.metrics["E1.total"].previous.unit = "(unit not stated)"
    assert card(report, "energy_total").trend == "The two years use different units."


def test_a_figure_that_only_needs_a_check_is_compared_with_an_asterisk_and_an_explanation():
    report = blank_report()
    put(report, "E1.total", 2_000_000, 1_600_000, unit="(unit not stated)", warnings=[NO_UNIT])
    c = card(report, "energy_total")
    assert (c.verdict, c.chip_text, c.trust) == (WORSE, "✖ Got worse*", "check")
    assert c.caveat.startswith("* ") and c.alerts == [NO_UNIT] and (c.big, c.unit) == ("20,00,000", "unit not stated")


# ------------------------------------------------------------------------------------------------ figures calculated by us
def test_renewable_share_is_calculated_marked_so_and_inherits_warnings():
    report = blank_report()
    put(report, "L1.re_total", 6_826_744, 6_705_340, warnings=[NO_UNIT])
    put(report, "L1.nre_total", 457_374_068, 466_885_245, warnings=[NO_UNIT])
    c = card(report, "renewable_share")
    assert (c.big, c.unit, c.verdict) == ("1.47", "% of all energy", SAME)
    assert c.badge.endswith("∑ Calculated by us from reported figures") and c.alerts == [NO_UNIT]
    assert any("renewable energy ÷ (renewable + non-renewable energy)" in line for line in c.fine)


def test_a_calculated_figure_needs_all_its_ingredients():
    report = blank_report()
    put(report, "E6.scope1", 36_900_275, 37_095_658, unit="tCO2e")            # Scope 2 is not reported
    assert card(report, "ghg_total").has_number is False
    put(report, "E6.scope2", 781_764, 850_070, unit="tCO2e")
    c = card(report, "ghg_total")
    assert (c.big, c.unit) == ("3.77", "crore tonnes CO₂e") and c.verdict == SAME


def test_recovered_share_cannot_exceed_100_percent():
    """Tata Steel files more waste 'recovered' than 'generated'; a share of (recovered + disposed) stays below 100."""
    report = blank_report()
    put(report, "E8.recovered_total", 18_842_200, 19_438_400, unit="tonnes")
    put(report, "E8.disposed_total", 21_909, 20_100, unit="tonnes")
    c = card(report, "waste_recovered")
    assert c.big == "99.9" and c.value < 100


# ------------------------------------------------------------------------------------------------ newer filings only, zeros
def test_waste_per_rupee_exists_only_when_the_filings_edition_has_it():
    report = blank_report()
    assert card(report, "waste_intensity") is None                           # an older edition has no such item
    put(report, "X.waste_rupee", 1.158e-07, 1.039e-07, unit="tonnes per ₹", extra=True)
    c = card(report, "waste_intensity")
    assert (c.big, c.unit) == ("1.16", "tonnes per ₹ crore") and c.verdict == WORSE


def test_zero_in_both_years_does_not_count_as_a_compared_figure():
    report = blank_report()
    put(report, "E5.voc", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    c = card(report, "air_voc")
    assert (c.verdict, c.headline, c.value) == (SAME, False, 0)
    assert c.trend == "No change: 0 in both years" and c.trust == "check"
