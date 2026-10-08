"""Which XBRL tag feeds which row of the SEBI template.

Two editions of SEBI's XBRL form exist (see context.md section 4a):
  * "modern"  (released 2024-04-30 or later)  splits energy into renewable / non-renewable, uses real unit ids ...
  * "legacy"  (released before that)          matches the 2021 SEBI form row for row, but has no unit ids.
For every row we therefore list the tag(s) to use in each edition.

How to read an entry:
    "E1.electricity": Source("energy", modern=(tagA, tagB), legacy=(tagC,))
means: in a modern filing ADD tagA and tagB (the result is marked CALCULATED); in a legacy filing take tagC.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    kind: str                  # "energy", "water", "mass", "air", "ghg", "intensity", "percent", "yes_no", "text"
    modern: tuple = ()         # tag(s) in modern editions   (empty = the item does not exist there)
    legacy: tuple = ()         # tag(s) in legacy editions
    unit_text_tag: str = ""    # legacy only: the tag that holds the unit as free text (e.g. "UnitOfNox")
    add_all_rows: bool = False # add up every row-label variant of the tag (used for "other sources" of energy)
    how: str = ""              # plain words: how a CALCULATED value is built
    fixed_warning: str = ""    # a warning that always applies to this item


def same(kind, tag, **options):
    """Same tag in both editions."""
    return Source(kind, (tag,), (tag,), **options)


def both(kind, modern, legacy, **options):
    """Different tags in the two editions."""
    return Source(kind, modern if isinstance(modern, tuple) else (modern,), legacy if isinstance(legacy, tuple) else (legacy,), **options)


# ----------------------------------------------------------------------------------------- water rows
def _water_withdrawal(prefix, suffix=""):
    s = suffix
    return {
        f"{prefix}.surface": same("water", f"WaterWithdrawalBySurfaceWater{s}"),
        f"{prefix}.ground": same("water", f"WaterWithdrawalByGroundwater{s}"),
        f"{prefix}.third_party": same("water", f"WaterWithdrawalByThirdPartyWater{s}"),
        f"{prefix}.sea": same("water", f"WaterWithdrawalBySeawaterOrDesalinatedWater{s}"),
        f"{prefix}.others": same("water", f"WaterWithdrawalByOthers{s}"),
        f"{prefix}.withdrawal_total": same("water", f"TotalVolumeOfWaterWithdrawal{s}"),
        f"{prefix}.consumption": same("water", f"TotalVolumeOfWaterConsumption{s}"),
        f"{prefix}.intensity": same("intensity", f"WaterIntensityPerRupeeOfTurnover{s}"),
    }


def _water_discharge(prefix, suffix=""):
    s = suffix
    out = {f"{prefix}.total": same("water", f"TotalWaterDischargedInKilolitres{s}")}
    for code, tag in (
        ("surface", "WaterDischargeToSurfaceWater"),
        ("ground", "WaterDischargeToGroundwater"),
        ("sea", "WaterDischargeToSeawater"),
        ("third_party", "WaterDischargeBySentToThirdParties"),
        ("others", "WaterDischargeToOthers"),
    ):
        # NSE's tag names are not consistent: "WithOutTreatment" vs "WithoutTreatment"
        without = "WithoutTreatment" if code == "third_party" else "WithOutTreatment"
        out[f"{prefix}.{code}"] = same("water", f"{tag}{s}")
        out[f"{prefix}.{code}_no_treatment"] = same("water", f"{tag}{without}{s}")
        out[f"{prefix}.{code}_treated"] = same("water", f"{tag}WithTreatment{s}")
    return out


# ----------------------------------------------------------------------------------------- the main table
SOURCES = {
    # ---- E1 energy (the 2021 form wants electricity / fuel / other; modern filings split each into renewable + non-renewable)
    "E1.electricity": both("energy",
                           ("TotalElectricityConsumptionFromRenewableSources", "TotalElectricityConsumptionFromNonRenewableSources"),
                           "TotalElectricityConsumption",
                           how="Renewable + non-renewable electricity (this filing reports them separately)"),
    "E1.fuel": both("energy",
                    ("TotalFuelConsumptionFromRenewableSources", "TotalFuelConsumptionFromNonRenewableSources"),
                    "TotalFuelConsumption",
                    how="Renewable + non-renewable fuel (this filing reports them separately)"),
    "E1.other": both("energy",
                     ("EnergyConsumptionThroughOtherSourcesFromRenewableSources", "EnergyConsumptionThroughOtherSourcesFromNonRenewableSources"),
                     "EnergyConsumptionThroughOtherSources",
                     add_all_rows=True,
                     how="Renewable + non-renewable 'other sources' (this filing reports them separately)"),
    "E1.total": both("energy", "TotalEnergyConsumedFromRenewableAndNonRenewableSources", "TotalEnergyConsumption"),
    "E1.intensity": same("intensity", "EnergyIntensityPerRupeeOfTurnover"),
    "E1.intensity_optional": same("intensity", "EnergyIntensityTheRelevantMetricMayBeSelectedByTheEntity"),

    # ---- E5 air emissions (older filings keep the unit in a separate free-text tag)
    "E5.nox": both("air", "NOx", "Nox", unit_text_tag="UnitOfNox"),
    "E5.sox": both("air", "SOx", "Sox", unit_text_tag="UnitOfSox"),
    "E5.pm": same("air", "ParticulateMatter", unit_text_tag="UnitOfParticulateMatter"),
    "E5.pop": same("air", "PersistentOrganicPollutants", unit_text_tag="UnitOfPersistentOrganicPollutants"),
    "E5.voc": same("air", "VolatileOrganicCompounds", unit_text_tag="UnitOfVolatileOrganicCompounds"),
    "E5.hap": same("air", "HazardousAirPollutants", unit_text_tag="UnitOfHazardousAirPollutants"),
    "E5.others": Source("air"),   # no tag exists for "Others – please specify"

    # ---- E6 greenhouse gases
    "E6.scope1": same("ghg", "TotalScope1Emissions", unit_text_tag="UnitOfTotalScope1Emissions"),
    "E6.scope2": same("ghg", "TotalScope2Emissions", unit_text_tag="UnitOfTotalScope2Emissions"),
    "E6.intensity": both("intensity", "TotalScope1AndScope2EmissionsIntensityPerRupeeOfTurnover",
                         "TotalScope1AndScope2EmissionsPerRupeeOfTurnover",
                         unit_text_tag="UnitOfTotalScope1AndScope2EmissionsPerRupeeOfTurnover"),
    "E6.intensity_optional": both("intensity", "TotalScope1AndScope2EmissionsIntensityTheRelevantMetricMayBeSelectedByTheEntity",
                                  "TotalScope1AndScope2EmissionIntensity",
                                  unit_text_tag="UnitOfTotalScope1AndScope2EmissionIntensity"),

    # ---- E8 waste
    "E8.plastic": same("mass", "PlasticWaste"),
    "E8.ewaste": same("mass", "EWaste"),
    "E8.biomedical": same("mass", "BioMedicalWaste"),
    "E8.construction": same("mass", "ConstructionAndDemolitionWaste"),
    "E8.battery": same("mass", "BatteryWaste"),
    "E8.radioactive": same("mass", "RadioactiveWaste"),
    "E8.other_hazardous": same("mass", "OtherHazardousWaste"),
    "E8.other_non_hazardous": same("mass", "OtherNonHazardousWasteGenerated"),
    "E8.total": same("mass", "TotalWasteGenerated"),
    "E8.recycled": same("mass", "WasteRecoveredThroughRecycled"),
    "E8.reused": same("mass", "WasteRecoveredThroughReUsed"),
    "E8.other_recovery": same("mass", "WasteRecoveredThroughOtherRecoveryOperations"),
    "E8.recovered_total": same("mass", "TotalWasteRecovered"),
    "E8.incineration": same("mass", "WasteDisposedByIncineration"),
    "E8.landfill": same("mass", "WasteDisposedByLandfilling"),
    "E8.other_disposal": same("mass", "WasteDisposedByOtherDisposalOperations"),
    "E8.disposed_total": same("mass", "TotalWasteDisposed"),

    # ---- L1 energy: renewable / non-renewable (same tags in both editions)
    "L1.re_electricity": same("energy", "TotalElectricityConsumptionFromRenewableSources"),
    "L1.re_fuel": same("energy", "TotalFuelConsumptionFromRenewableSources"),
    "L1.re_other": same("energy", "EnergyConsumptionThroughOtherSourcesFromRenewableSources", add_all_rows=True),
    "L1.re_total": same("energy", "TotalEnergyConsumedFromRenewableSources"),
    "L1.nre_electricity": same("energy", "TotalElectricityConsumptionFromNonRenewableSources"),
    "L1.nre_fuel": same("energy", "TotalFuelConsumptionFromNonRenewableSources"),
    "L1.nre_other": same("energy", "EnergyConsumptionThroughOtherSourcesFromNonRenewableSources"),
    "L1.nre_total": same("energy", "TotalEnergyConsumedFromNonRenewableSources"),

    # ---- L4 Scope 3
    "L4.scope3": same("ghg", "TotalScope3Emissions", unit_text_tag="UnitOfTotalScope3Emissions"),
    "L4.intensity": same("intensity", "TotalScope3EmissionsPerRupeeOfTurnover", unit_text_tag="UnitOfTotalScope3EmissionsPerRupeeOfTurnover"),
    "L4.intensity_optional": both("intensity", "TotalScope3EmissionIntensityTheRelevantMetricMayBeSelectedByTheEntity",
                                  "TotalScope3EmissionIntensity", unit_text_tag="UnitOfTotalScope3EmissionIntensity"),

    # ---- yes/no questions and text answers (same tags in both editions)
    "E2.answer": same("yes_no", "DoesTheEntityHaveAnySitesOrFacilitiesIdentifiedAsDesignatedConsumersUnderThePerformanceAchieveAndTradeSchemeOfTheGovernmentOfIndia"),
    "E2.details": same("text", "DiscloseWhetherTargetsSetUnderThePatSchemeHaveBeenAchievedInCaseTargetsHaveNotBeenAchievedThenProvideTheRemedialActionTakenExplanatoryTextBlock"),
    "E4.answer": same("yes_no", "HasTheEntityImplementedAMechanismForZeroLiquidDischarge"),
    "E4.details": same("text", "DetailsOfCoverageAndImplementationIfForZeroLiquidDischargeExplanatoryTextBlock"),
    "E7.answer": same("yes_no", "DoesTheEntityHaveAnyProjectRelatedToReducingGreenHouseGasEmission"),
    "E7.details": same("text", "DetailsOfProjectRelatedToReducingGreenHouseGasEmissionExplanatoryTextBlock"),
    "E9.details": same("text", "DetailsOfWasteManagementPracticesAdoptedInYourEstablishmentsAndTheStrategyAdoptedByCompanyToReduceUsageOfHazardousAndToxicChemicalsExplanatoryTextBlock"),
    "E12.answer": same("yes_no", "IsTheEntityCompliantWithTheApplicableEnvironmentalLaw"),
    "E12.details": same("text", "TheEntityHasNotApplicableEnvironmentalLawExplanatoryTextBlock"),
    "L5.details": same("text", "DetailsOfSignificantDirectAndIndirectImpactOfTheEntityOnBiodiversityInSuchAreasAlongWithPreventionAndRemediationActivitiesExplanatoryTextBlock"),
    "L7.answer": same("yes_no", "DoesTheEntityHaveABusinessContinuityAndDisasterManagementPlan"),
    "L7.details": same("text", "DisclosureWebLinkOfEntityAtWhichBusinessContinuityAndDisasterManagementPlanIsPlaced"),
    "L8.details": same("text", "DiscloseAnySignificantAdverseImpactToTheEnvironmentArisingFromTheValueChainOfTheEntityWhatMitigationOrAdaptationMeasuresHaveBeenTakenByTheEntityInThisRegardExplanatoryTextBlock"),
    "L9.value": same("percent", "PercentageOfValueChainPartnersByValueOfBusinessDoneWithSuchPartnersThatWereAssessedForEnvironmentalImpacts"),
}

SOURCES.update(_water_withdrawal("E3"))
SOURCES["E3.intensity_optional"] = same("intensity", "WaterIntensityTheRelevantMetricMayBeSelectedByTheEntity")
SOURCES.update(_water_discharge("L2"))

# Leadership 3: the same water rows, one block per facility.  The tags end in "PerArea" and carry a facility label.
FACILITY_SOURCES = {}
FACILITY_SOURCES.update(_water_withdrawal("L3", suffix="PerArea"))
FACILITY_SOURCES.update(_water_discharge("L3d", suffix="PerArea"))
FACILITY_NAME_TAG = "NameOfTheArea"
FACILITY_NATURE_TAG = "NatureOfOperations"

# ----------------------------------------------------------------------------------------- list tables
# For each list question: one entry per column.  A column is a tuple of tags (several tags are joined with "; ");
# an empty tuple means the structured filing has no field for that column.
LIST_COLUMNS = {
    "E10": [
        None,   # "S. No." is just 1, 2, 3 ...
        ("LocationOfOperationsOrOffices",),
        ("TypeOfOperations",),
        ("WhetherTheConditionsOfEnvironmentalApprovalOrClearanceAreBeingCompliedWith",
         "ReasonsAndCorrectiveActionTakenIfTheConditionsOfEnvironmentalApprovalOrClearanceAreNotBeingCompliedWith"),
    ],
    "E11": [
        ("NameAndBriefDetailsOfProject",),
        ("EIANotificationNumber",),
        ("DateOfEnvironmentalImpactAssessments",),
        ("WhetherConductedByIndependentExternalAgencyP6",),
        ("ResultsCommunicatedInPublicDomainP6",),
        (),
    ],
    "L6": [
        None,
        ("InitiativeUndertaken",),
        (),
        ("OutcomeOfTheInitiative",),
    ],
}

# ----------------------------------------------------------------------------------------- assurance notes
# topic word that appears in the tag names of that table's "independent assurance?" and "name of agency" tags
ASSURANCE_TOPICS = {
    "E1": "EnergyConsumption",
    "E3": "WaterWithdrawal",
    "E5": "AirEmissions",
    "E6": "GreenHouseGasEmissions",
    "E8": "WasteManagement",
    "L1": "EnergyConsumption",     # the Leadership variant has "Leadership" in its tag name
    "L2": "WaterDischarged",
    "L3": "AreasOfWaterStress",
    "L4": "TotalScope3Emissions",
}

# ----------------------------------------------------------------------------------------- extras (newer filings only)
# Items modern filings carry that the 2021 SEBI form does not have.  Shown separately, never mixed into the SEBI tables.
_PPP_WARNING = ("PPP-adjusted figures are per million US dollars, but filings label their unit 'per rupee'. "
                "The unit label here is unreliable; shown as filed.")
_PHYSICAL_WARNING = ("This is per unit of physical output (for example per tonne of steel). The filing's unit label leaves out "
                     "the 'per tonne'; shown as filed.")
EXTRAS = {
    "X.energy_physical": ("Energy intensity in terms of physical output",
                          Source("intensity", ("EnergyIntensityInTermOfPhysicalOutput",), fixed_warning=_PHYSICAL_WARNING)),
    "X.energy_ppp": ("Energy intensity adjusted for Purchasing Power Parity (PPP)",
                     Source("intensity", ("EnergyIntensityPerRupeeOfTurnoverAdjustingForPurchasingPowerParity",), fixed_warning=_PPP_WARNING)),
    "X.water_physical": ("Water intensity in terms of physical output",
                         Source("intensity", ("WaterIntensityInTermOfPhysicalOutput",), fixed_warning=_PHYSICAL_WARNING)),
    "X.water_ppp": ("Water intensity adjusted for Purchasing Power Parity (PPP)",
                    Source("intensity", ("WaterIntensityPerRupeeOfTurnoverAdjustingForPurchasingPowerParity",), fixed_warning=_PPP_WARNING)),
    "X.ghg_physical": ("Scope 1 + 2 emission intensity in terms of physical output",
                       Source("intensity", ("TotalScope1AndScope2EmissionsIntensityInTermOfPhysicalOutput",), fixed_warning=_PHYSICAL_WARNING)),
    "X.ghg_ppp": ("Scope 1 + 2 emission intensity adjusted for Purchasing Power Parity (PPP)",
                  Source("intensity", ("TotalScope1AndScope2EmissionsIntensityPerRupeeOfTurnoverAdjustedForPurchasingPowerParity",), fixed_warning=_PPP_WARNING)),
    "X.waste_rupee": ("Waste intensity per rupee of turnover", Source("intensity", ("WasteIntensityPerRupeeOfTurnover",))),
    "X.waste_ppp": ("Waste intensity adjusted for Purchasing Power Parity (PPP)",
                    Source("intensity", ("WasteIntensityPerRupeeOfTurnoverAdjustingForPurchasingPowerParity",), fixed_warning=_PPP_WARNING)),
    "X.waste_physical": ("Waste intensity in terms of physical output",
                         Source("intensity", ("WasteIntensityInTermOfPhysicalOutput",), fixed_warning=_PHYSICAL_WARNING)),
}
