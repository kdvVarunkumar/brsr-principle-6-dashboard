"""Tests for brsr_p6/extractor.py and brsr_p6/checks.py, using tiny fake filings."""

import pytest
from xbrl_samples import both_years, context, fact, write_xbrl

from brsr_p6.extractor import build_report
from brsr_p6.models import Status
from brsr_p6.xbrl_reader import read_filing


def report_for(tmp_path, facts="", release="2024-04-30", extra_contexts="", fy="2023-24"):
    filing = read_filing(write_xbrl(tmp_path, facts, release=release, extra_contexts=extra_contexts))
    return build_report(filing, "Test Company Limited", "TEST", fy)


# ------------------------------------------------------------------------------------------ newer filings
def test_electricity_is_built_from_renewable_plus_non_renewable_and_marked_calculated(tmp_path):
    facts = (both_years("TotalElectricityConsumptionFromRenewableSources", 100, 80, "Gigajoule")
             + both_years("TotalElectricityConsumptionFromNonRenewableSources", 900, 700, "Gigajoule"))
    metric = report_for(tmp_path, facts).metrics["E1.electricity"]
    assert (metric.current.value, metric.current.unit, metric.current.status) == (1000, "GJ", Status.CALCULATED)
    assert metric.previous.value == 780                                  # the previous year is read from the previous-year column
    assert "Renewable + non-renewable" in metric.current.note


def test_a_reported_total_is_reported_not_calculated(tmp_path):
    facts = both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 4000, "Gigajoule")
    cell = report_for(tmp_path, facts).metrics["E1.total"].current
    assert (cell.value, cell.status, cell.as_filed) == (5000, Status.REPORTED, "5000 Gigajoule")


def test_other_sources_adds_up_all_row_labelled_facts(tmp_path):
    contexts = context("D_o1", "OtherAxis", "Other1") + context("D_o2", "OtherAxis", "Other2")
    facts = (fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 3, "D_o1", "Gigajoule")
             + fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 4, "D_o2", "Gigajoule")
             + fact("EnergyConsumptionThroughOtherSourcesFromNonRenewableSources", 10, "DCYMain", "Gigajoule"))
    cell = report_for(tmp_path, facts, extra_contexts=contexts).metrics["E1.other"].current
    assert cell.value == 17 and cell.status == Status.CALCULATED


def test_other_sources_uses_the_plain_total_and_does_not_count_its_breakdown_rows_again(tmp_path):
    """Real case (Reliance FY23-24): the filing gives a total (131,327) AND a row with the same total; adding both doubled it."""
    contexts = context("D_o1", "OtherAxis", "Other1")
    facts = (fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 131327, "DCYMain", "Gigajoule")
             + fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 131327, "D_o1", "Gigajoule"))
    metric = report_for(tmp_path, facts, extra_contexts=contexts).metrics["L1.re_other"]
    assert metric.current.value == 131327


def test_air_emissions_are_converted_to_tonnes_and_the_original_is_kept(tmp_path):
    cell = report_for(tmp_path, both_years("NOx", 27, 24, "Kilotonne")).metrics["E5.nox"].current
    assert (cell.value, cell.unit, cell.status) == (27000, "tonnes", Status.CONVERTED)
    assert cell.as_filed == "27 Kilotonne"


def test_missing_items_are_not_reported_and_never_zero(tmp_path):
    report = report_for(tmp_path, both_years("NOx", 1, 1, "Kilotonne"))
    cell = report.metrics["E5.sox"].current
    assert cell.status == Status.NOT_REPORTED and cell.value is None
    assert report.metrics["E5.others"].current.status == Status.NOT_REPORTED       # SEBI row with no XBRL field at all


def test_an_NA_answer_is_not_a_number(tmp_path):
    cell = report_for(tmp_path, fact("TotalScope3Emissions", "NA", unit="tCO2e")).metrics["L4.scope3"].current
    assert cell.status == Status.NOT_REPORTED and "NA" in cell.note


def test_yes_no_answers_are_cleaned_and_the_original_is_kept(tmp_path):
    report = report_for(tmp_path, fact("HasTheEntityImplementedAMechanismForZeroLiquidDischarge", "true")
                        + fact("DoesTheEntityHaveAnyProjectRelatedToReducingGreenHouseGasEmission", "NA")
                        + fact("DetailsOfProjectRelatedToReducingGreenHouseGasEmissionExplanatoryTextBlock", "  Solar\n farm "))
    zld = report.metrics["E4.answer"].current
    assert (zld.value, zld.as_filed) == ("Yes", "true")
    assert report.metrics["E7.answer"].current.value == "Not applicable"
    assert report.metrics["E7.details"].current.value == "Solar farm"


def test_percentage_filed_as_a_fraction_is_shown_as_percent(tmp_path):
    tag = "PercentageOfValueChainPartnersByValueOfBusinessDoneWithSuchPartnersThatWereAssessedForEnvironmentalImpacts"
    cell = report_for(tmp_path, fact(tag, 0.11, unit="pure")).metrics["L9.value"].current
    assert cell.value == pytest.approx(11) and cell.unit == "%" and cell.status == Status.CONVERTED


def test_boundary_and_edition_are_recorded(tmp_path):
    report = report_for(tmp_path, fact("ReportingBoundary", "Consolidated basis"))
    assert (report.boundary, report.family, report.taxonomy_release, report.previous_fy) == ("Consolidated basis", "modern", "2024-04-30", "2022-23")


def test_a_wrong_financial_year_is_flagged(tmp_path):
    report = report_for(tmp_path, fy="2021-22")      # the fake file's current year ends in 2024
    assert any("does not match FY 2021-22" in w for w in report.warnings)


# ------------------------------------------------------------------------------------------ sanity checks
def test_zero_intensity_next_to_a_non_zero_total_is_flagged(tmp_path):
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 4000, "Gigajoule")
             + both_years("EnergyIntensityPerRupeeOfTurnover", 0, 0, "GigajoulePerINR"))
    cell = report_for(tmp_path, facts).metrics["E1.intensity"].current
    assert cell.value == 0 and any("not a real zero" in w for w in cell.warnings)


def test_air_pollutant_zero_gets_the_not_measured_caveat(tmp_path):
    cell = report_for(tmp_path, both_years("PersistentOrganicPollutants", 0, 0, "Kilotonne")).metrics["E5.pop"].current
    assert cell.value == 0 and any("not measured" in w for w in cell.warnings)


def test_totals_that_do_not_add_up_are_flagged(tmp_path):
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 5000, "Gigajoule")
             + both_years("TotalElectricityConsumptionFromNonRenewableSources", 100, 100, "Gigajoule")
             + both_years("TotalFuelConsumptionFromNonRenewableSources", 200, 200, "Gigajoule")
             + both_years("EnergyConsumptionThroughOtherSourcesFromNonRenewableSources", 0, 0, "Gigajoule"))
    cell = report_for(tmp_path, facts).metrics["E1.total"].current
    assert any("add up to 300.00" in w for w in cell.warnings)


def test_totals_that_do_add_up_get_no_warning(tmp_path):
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 300, 300, "Gigajoule")
             + both_years("TotalElectricityConsumptionFromNonRenewableSources", 100, 100, "Gigajoule")
             + both_years("TotalFuelConsumptionFromNonRenewableSources", 200, 200, "Gigajoule")
             + both_years("EnergyConsumptionThroughOtherSourcesFromNonRenewableSources", 0, 0, "Gigajoule"))
    assert report_for(tmp_path, facts).metrics["E1.total"].current.warnings == []


def test_emissions_far_too_small_for_the_energy_use_are_flagged_as_probably_millions(tmp_path):
    """Tata Steel typed Scope 1 = 64 (million tonnes) under a unit that means tonnes."""
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 623_812_739, 587_567_891, "Gigajoule")
             + both_years("TotalScope1Emissions", 64, 61, "MtCO2e") + both_years("TotalScope2Emissions", 5, 5, "MtCO2e")
             + both_years("TotalScope3Emissions", 28, 23, "MtCO2e"))
    report = report_for(tmp_path, facts)
    for key in ("E6.scope1", "E6.scope2", "L4.scope3"):
        cell = report.metrics[key].current
        assert cell.value in (64, 5, 28) and cell.warnings, key      # the number is NEVER changed
    assert "millions" in report.metrics["E6.scope1"].current.warnings[0]


def test_plausible_emissions_get_no_scale_warning(tmp_path):
    """Reliance: 36.35 million tonnes of Scope 1 for 478 million GJ is normal (0.076 t/GJ)."""
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 478_033_842, 481_641_954, "Gigajoule")
             + both_years("TotalScope1Emissions", 36_350_070, 36_459_294, "MtCO2e"))
    assert report_for(tmp_path, facts).metrics["E6.scope1"].current.warnings == []


# ------------------------------------------------------------------------------------------ older filings
def test_legacy_filing_uses_its_own_tags_and_free_text_units(tmp_path):
    facts = (both_years("TotalElectricityConsumption", 4_270_996, 4_049_102, "pure")
             + both_years("TotalEnergyConsumption", 473_590_585, 485_801_414, "pure")
             + both_years("Nox", 34, 37, "pure") + fact("UnitOfNox", "Kilotonnes/year")
             + both_years("TotalScope1Emissions", 75.75, 75.7, "pure") + fact("UnitOfTotalScope1Emissions", "Million tonnes of CO2 equivalent")
             + both_years("TotalVolumeOfWaterConsumption", 200, 202, "pure"))
    report = report_for(tmp_path, facts, release="2021-09-30", fy="2023-24")
    assert report.family == "legacy"

    electricity = report.metrics["E1.electricity"].current
    assert electricity.value == 4_270_996 and electricity.status == Status.REPORTED       # a direct tag, so not "calculated"
    assert electricity.unit == "(unit not stated)" and electricity.warnings                # energy has no unit in old filings

    nox = report.metrics["E5.nox"].current
    assert (nox.value, nox.unit, nox.status) == (34_000, "tonnes", Status.CONVERTED)

    scope1 = report.metrics["E6.scope1"].current
    assert (scope1.value, scope1.unit) == (75_750_000, "tCO2e")

    water = report.metrics["E3.consumption"].current
    assert (water.value, water.unit) == (200, "kL") and "SEBI form" in water.note


# ------------------------------------------------------------------------------------------ list tables, facilities, assurance, extras
def test_list_table_rows_come_from_row_labelled_facts_in_natural_order(tmp_path):
    axis = "OperationsOrOfficesAxis"
    contexts = "".join(context(f"D_{n}", axis, f"Op{n}") for n in (2, 1, 10)) + "".join(context(f"I_{n}", axis, f"Op{n}", instant=True) for n in (2, 1, 10))
    facts = ""
    for n in (2, 1, 10):
        facts += fact("LocationOfOperationsOrOffices", f"Place {n}", f"D_{n}")
        facts += fact("TypeOfOperations", "Mining", f"I_{n}")                  # this tag sits in a single-day context
        facts += fact("WhetherTheConditionsOfEnvironmentalApprovalOrClearanceAreBeingCompliedWith", "true" if n != 2 else "false", f"D_{n}")
    table = report_for(tmp_path, facts, extra_contexts=contexts).tables["E10"]
    assert [row[1] for row in table.rows] == ["Place 1", "Place 2", "Place 10"]
    assert table.rows[0] == ["1", "Place 1", "Mining", "Yes"]
    assert table.rows[1][3] == "No"


def test_an_empty_list_table_says_so(tmp_path):
    table = report_for(tmp_path).tables["E11"]
    assert table.rows == [] and "lists no rows" in table.note


def test_facility_blocks_in_water_stressed_areas(tmp_path):
    contexts = (context("D_f1", "FacilityAxis", "Facility1") + context("P_f1", "FacilityAxis", "Facility1", year="previous"))
    facts = (fact("NameOfTheArea", "Rewari", "D_f1") + fact("NatureOfOperations", "Storage", "D_f1")
             + fact("TotalVolumeOfWaterConsumptionPerArea", 500, "D_f1", "Kiloliters")
             + fact("TotalVolumeOfWaterConsumptionPerArea", 450, "P_f1", "Kiloliters"))
    (facility,) = report_for(tmp_path, facts, extra_contexts=contexts).facilities
    assert (facility.name, facility.nature) == ("Rewari", "Storage")
    consumption = facility.metrics["L3.consumption"]
    assert (consumption.current.value, consumption.previous.value, consumption.current.unit) == (500, 450, "kL")


def test_assurance_note_is_found_for_a_table(tmp_path):
    facts = (fact("AnyIndependentAssessmentOrEvaluationOrAssuranceHasBeenCarriedOutByAnExternalAgencyForWaterWithdrawal", "true")
             + fact("NameOfTheExternalAgencyInCaseAnyIndependentAssessmentOrEvaluationOrAssuranceHasBeenCarriedOutByAnExternalAgencyForWaterWithdrawalExplanatoryTextBlock", "KPMG"))
    assurance = report_for(tmp_path, facts).assurance
    assert (assurance["E3"].carried_out, assurance["E3"].agency) == ("Yes", "KPMG")
    assert assurance["E8"].carried_out == "Not reported"


def test_extras_appear_only_when_the_filing_has_them_and_ppp_gets_a_unit_warning(tmp_path):
    none = report_for(tmp_path)
    assert none.extras == {}
    facts = both_years("EnergyIntensityPerRupeeOfTurnoverAdjustingForPurchasingPowerParity", 9081.18, 9160.39, "GigajoulePerINR")
    extra = report_for(tmp_path, facts).extras["X.energy_ppp"].current
    assert extra.value == 9081.18 and any("unit label" in w for w in extra.warnings)
