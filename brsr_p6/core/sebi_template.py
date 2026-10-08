"""SEBI's official Principle 6 layout (BRSR format, Annexure I of the SEBI circular dated 10 May 2021), written as data.

Why as data?  The SEBI view simply loops over QUESTIONS and prints each question, its table and its rows in the
official order with the official wording.  Nothing about the layout is hard-coded in the HTML.

How to read this file:
  * Question.id        "E1" = Essential Indicator 1, "L3" = Leadership Indicator 3.
  * Question.kind      "table"      rows with a current-year and a previous-year value
                       "yes_no"     a Yes/No answer plus optional details (text)
                       "text"       a free-text answer
                       "number"     a single number
                       "list"       a table written out row by row (columns below)
                       "facilities" one table per facility in an area of water stress (Leadership 3)
  * Row.key            the stable id of a row; the mapping (p6_mapping.py) says which XBRL tag feeds it.
  * Row.header=True    a heading line inside a table (it has no values).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Row:
    key: str
    label: str
    header: bool = False


@dataclass(frozen=True)
class Question:
    id: str
    section: str          # "Essential Indicators" or "Leadership Indicators"
    number: int           # the question number inside its section
    text: str             # the official wording
    kind: str
    rows: tuple = ()
    columns: tuple = ()   # for kind "list"
    assurance: bool = False   # the table ends with "Indicate if any independent assessment / assurance ..."
    unit_column: str = ""     # heading of the "Unit" column if SEBI's table has one (E5, E6, L4); "" = no such column
    remark: str = ""      # OUR remark about this question (not SEBI wording)


ESSENTIAL = "Essential Indicators"
LEADERSHIP = "Leadership Indicators"


def H(label):
    """A heading row inside a table."""
    return Row("", label, header=True)


# ------------------------------------------------------------------------------------ shared row groups
def _water_withdrawal_rows(prefix):
    return (
        H("Water withdrawal by source (in kilolitres)"),
        Row(f"{prefix}.surface", "(i) Surface water"),
        Row(f"{prefix}.ground", "(ii) Groundwater"),
        Row(f"{prefix}.third_party", "(iii) Third party water"),
        Row(f"{prefix}.sea", "(iv) Seawater / desalinated water"),
        Row(f"{prefix}.others", "(v) Others"),
        Row(f"{prefix}.withdrawal_total", "Total volume of water withdrawal (in kilolitres) (i + ii + iii + iv + v)"),
        Row(f"{prefix}.consumption", "Total volume of water consumption (in kilolitres)"),
        Row(f"{prefix}.intensity", "Water intensity per rupee of turnover (Water consumed / turnover)"),
        Row(f"{prefix}.intensity_optional", "Water intensity (optional) – the relevant metric may be selected by the entity"),
    )


def _water_discharge_rows(prefix, into):
    """`into` is 'To' (Leadership 2) or 'Into' (Leadership 3): the official labels differ slightly."""
    def destination(code, number, name):
        return (
            Row(f"{prefix}.{code}", f"({number}) {name}"),
            Row(f"{prefix}.{code}_no_treatment", "- No treatment"),
            Row(f"{prefix}.{code}_treated", "- With treatment – please specify level of treatment"),
        )
    return (
        H("Water discharge by destination and level of treatment (in kilolitres)"),
        *destination("surface", "i", f"{into} Surface water"),
        *destination("ground", "ii", f"{into} Groundwater"),
        *destination("sea", "iii", f"{into} Seawater"),
        *destination("third_party", "iv", "Sent to third-parties"),
        *destination("others", "v", "Others"),
        Row(f"{prefix}.total", "Total water discharged (in kilolitres)"),
    )


# ------------------------------------------------------------------------------------ the questions
QUESTIONS = (
    # ============================================================ ESSENTIAL INDICATORS
    Question("E1", ESSENTIAL, 1,
             "Details of total energy consumption (in Joules or multiples) and energy intensity, in the following format:",
             "table", assurance=True, rows=(
                 Row("E1.electricity", "Total electricity consumption (A)"),
                 Row("E1.fuel", "Total fuel consumption (B)"),
                 Row("E1.other", "Energy consumption through other sources (C)"),
                 Row("E1.total", "Total energy consumption (A+B+C)"),
                 Row("E1.intensity", "Energy intensity per rupee of turnover (Total energy consumption/ turnover in rupees)"),
                 Row("E1.intensity_optional", "Energy intensity (optional) – the relevant metric may be selected by the entity"),
             )),
    Question("E2", ESSENTIAL, 2,
             "Does the entity have any sites / facilities identified as designated consumers (DCs) under the Performance, Achieve and "
             "Trade (PAT) Scheme of the Government of India? (Y/N) If yes, disclose whether targets set under the PAT scheme have been "
             "achieved. In case targets have not been achieved, provide the remedial action taken, if any.",
             "yes_no"),
    Question("E3", ESSENTIAL, 3,
             "Provide details of the following disclosures related to water, in the following format:",
             "table", assurance=True, rows=_water_withdrawal_rows("E3")),
    Question("E4", ESSENTIAL, 4,
             "Has the entity implemented a mechanism for Zero Liquid Discharge? If yes, provide details of its coverage and implementation.",
             "yes_no"),
    Question("E5", ESSENTIAL, 5,
             "Please provide details of air emissions (other than GHG emissions) by the entity, in the following format:",
             "table", assurance=True, unit_column="Please specify unit", rows=(
                 Row("E5.nox", "NOx"),
                 Row("E5.sox", "SOx"),
                 Row("E5.pm", "Particulate matter (PM)"),
                 Row("E5.pop", "Persistent organic pollutants (POP)"),
                 Row("E5.voc", "Volatile organic compounds (VOC)"),
                 Row("E5.hap", "Hazardous air pollutants (HAP)"),
                 Row("E5.others", "Others – please specify"),
             )),
    Question("E6", ESSENTIAL, 6,
             "Provide details of greenhouse gas emissions (Scope 1 and Scope 2 emissions) & its intensity, in the following format:",
             "table", assurance=True, unit_column="Unit", rows=(
                 Row("E6.scope1", "Total Scope 1 emissions (Break-up of the GHG into CO2, CH4, N2O, HFCs, PFCs, SF6, NF3, if available)"),
                 Row("E6.scope2", "Total Scope 2 emissions (Break-up of the GHG into CO2, CH4, N2O, HFCs, PFCs, SF6, NF3, if available)"),
                 Row("E6.intensity", "Total Scope 1 and Scope 2 emissions per rupee of turnover"),
                 Row("E6.intensity_optional", "Total Scope 1 and Scope 2 emission intensity (optional) – the relevant metric may be selected by the entity"),
             ),
             remark="The gas-by-gas break-up (CO2, CH4, ...) is not part of the structured filing."),
    Question("E7", ESSENTIAL, 7,
             "Does the entity have any project related to reducing Green House Gas emission? If Yes, then provide details.",
             "yes_no"),
    Question("E8", ESSENTIAL, 8,
             "Provide details related to waste management by the entity, in the following format:",
             "table", assurance=True, rows=(
                 H("Total Waste generated (in metric tonnes)"),
                 Row("E8.plastic", "Plastic waste (A)"),
                 Row("E8.ewaste", "E-waste (B)"),
                 Row("E8.biomedical", "Bio-medical waste (C)"),
                 Row("E8.construction", "Construction and demolition waste (D)"),
                 Row("E8.battery", "Battery waste (E)"),
                 Row("E8.radioactive", "Radioactive waste (F)"),
                 Row("E8.other_hazardous", "Other Hazardous waste. Please specify, if any. (G)"),
                 Row("E8.other_non_hazardous",
                     "Other Non-hazardous waste generated (H). Please specify, if any. (Break-up by composition i.e. by materials relevant to the sector)"),
                 Row("E8.total", "Total (A + B + C + D + E + F + G + H)"),
                 H("For each category of waste generated, total waste recovered through recycling, re-using or other recovery operations (in metric tonnes)"),
                 Row("E8.recycled", "(i) Recycled"),
                 Row("E8.reused", "(ii) Re-used"),
                 Row("E8.other_recovery", "(iii) Other recovery operations"),
                 Row("E8.recovered_total", "Total"),
                 H("For each category of waste generated, total waste disposed by nature of disposal method (in metric tonnes)"),
                 Row("E8.incineration", "(i) Incineration"),
                 Row("E8.landfill", "(ii) Landfilling"),
                 Row("E8.other_disposal", "(iii) Other disposal operations"),
                 Row("E8.disposed_total", "Total"),
             ),
             remark="The SEBI form asks for recovery and disposal for each waste category; the structured filing gives only the totals "
                    "for all categories together, so that is what these rows show."),
    Question("E9", ESSENTIAL, 9,
             "Briefly describe the waste management practices adopted in your establishments. Describe the strategy adopted by your company "
             "to reduce usage of hazardous and toxic chemicals in your products and processes and the practices adopted to manage such wastes.",
             "text"),
    Question("E10", ESSENTIAL, 10,
             "If the entity has operations/offices in/around ecologically sensitive areas (such as national parks, wildlife sanctuaries, "
             "biosphere reserves, wetlands, biodiversity hotspots, forests, coastal regulation zones etc.) where environmental approvals / "
             "clearances are required, please specify details in the following format:",
             "list", columns=(
                 "S. No.", "Location of operations/offices", "Type of operations",
                 "Whether the conditions of environmental approval / clearance are being complied with? (Y/N) If no, the reasons thereof and corrective action taken, if any.",
             )),
    Question("E11", ESSENTIAL, 11,
             "Details of environmental impact assessments of projects undertaken by the entity based on applicable laws, in the current financial year:",
             "list", columns=(
                 "Name and brief details of project", "EIA Notification No.", "Date",
                 "Whether conducted by independent external agency (Yes / No)",
                 "Results communicated in public domain (Yes / No)", "Relevant Web link",
             )),
    Question("E12", ESSENTIAL, 12,
             "Is the entity compliant with the applicable environmental law/ regulations/ guidelines in India; such as the Water (Prevention "
             "and Control of Pollution) Act, Air (Prevention and Control of Pollution) Act, Environment protection act and rules thereunder (Y/N). "
             "If not, provide details of all such non-compliances, in the following format:",
             "yes_no",
             remark="SEBI asks for a table of non-compliances (law, details, fines, corrective action); the structured filing gives one free-text answer instead."),

    # ============================================================ LEADERSHIP INDICATORS
    Question("L1", LEADERSHIP, 1,
             "Provide break-up of the total energy consumed (in Joules or multiples) from renewable and non-renewable sources, in the following format:",
             "table", assurance=True, rows=(
                 H("From renewable sources"),
                 Row("L1.re_electricity", "Total electricity consumption (A)"),
                 Row("L1.re_fuel", "Total fuel consumption (B)"),
                 Row("L1.re_other", "Energy consumption through other sources (C)"),
                 Row("L1.re_total", "Total energy consumed from renewable sources (A+B+C)"),
                 H("From non-renewable sources"),
                 Row("L1.nre_electricity", "Total electricity consumption (D)"),
                 Row("L1.nre_fuel", "Total fuel consumption (E)"),
                 Row("L1.nre_other", "Energy consumption through other sources (F)"),
                 Row("L1.nre_total", "Total energy consumed from non-renewable sources (D+E+F)"),
             )),
    Question("L2", LEADERSHIP, 2,
             "Provide the following details related to water discharged:",
             "table", assurance=True, rows=_water_discharge_rows("L2", "To"),
             remark="The 'level of treatment' text is not part of the structured filing; only the volumes are."),
    Question("L3", LEADERSHIP, 3,
             "Water withdrawal, consumption and discharge in areas of water stress (in kilolitres): For each facility / plant located in areas "
             "of water stress, provide the following information: (i) Name of the area (ii) Nature of operations (iii) Water withdrawal, "
             "consumption and discharge in the following format:",
             "facilities", assurance=True,
             rows=_water_withdrawal_rows("L3") + _water_discharge_rows("L3d", "Into")),
    Question("L4", LEADERSHIP, 4,
             "Please provide details of total Scope 3 emissions & its intensity, in the following format:",
             "table", assurance=True, unit_column="Unit", rows=(
                 Row("L4.scope3", "Total Scope 3 emissions (Break-up of the GHG into CO2, CH4, N2O, HFCs, PFCs, SF6, NF3, if available)"),
                 Row("L4.intensity", "Total Scope 3 emissions per rupee of turnover"),
                 Row("L4.intensity_optional", "Total Scope 3 emission intensity (optional) – the relevant metric may be selected by the entity"),
             )),
    Question("L5", LEADERSHIP, 5,
             "With respect to the ecologically sensitive areas reported at Question 10 of Essential Indicators above, provide details of "
             "significant direct & indirect impact of the entity on biodiversity in such areas along-with prevention and remediation activities.",
             "text"),
    Question("L6", LEADERSHIP, 6,
             "If the entity has undertaken any specific initiatives or used innovative technology or solutions to improve resource efficiency, "
             "or reduce impact due to emissions / effluent discharge / waste generated, please provide details of the same as well as outcome "
             "of such initiatives, as per the following format:",
             "list", columns=(
                 "Sr. No", "Initiative undertaken",
                 "Details of the initiative (Web-link, if any, may be provided along-with summary)", "Outcome of the initiative",
             ),
             remark="The structured filing has no separate 'details' field for each initiative."),
    Question("L7", LEADERSHIP, 7,
             "Does the entity have a business continuity and disaster management plan? Give details in 100 words/ web link.",
             "yes_no"),
    Question("L8", LEADERSHIP, 8,
             "Disclose any significant adverse impact to the environment, arising from the value chain of the entity. What mitigation or "
             "adaptation measures have been taken by the entity in this regard.",
             "text"),
    Question("L9", LEADERSHIP, 9,
             "Percentage of value chain partners (by value of business done with such partners) that were assessed for environmental impacts.",
             "number"),
)

QUESTIONS_BY_ID = {q.id: q for q in QUESTIONS}


def label_of(key):
    """The official label of a row key, e.g. 'E1.electricity' -> 'Total electricity consumption (A)'."""
    for question in QUESTIONS:
        for row in question.rows:
            if row.key == key:
                return row.label
    return key
