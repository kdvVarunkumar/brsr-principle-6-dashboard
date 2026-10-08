"""The words of the dashboard, kept as DATA so they can be improved without touching any logic or HTML.

For every figure on the dashboard: a plain title, what it measures, why it matters and which direction is better.
Wording rule: short, no jargon (or the jargon is explained in the glossary), and never a claim the filing cannot support.
"""

from dataclasses import dataclass

from brsr_p6.comparison import CONTEXT, HIGHER, LOWER


@dataclass(frozen=True)
class MetricInfo:
    id: str
    topic: str                 # one of TOPICS
    title: str
    better: str                # LOWER, HIGHER or CONTEXT
    what: str                  # what it is
    why: str                   # why it matters
    source: str                # a SEBI row key such as "E1.total", or "derived:<name>" (see dashboard_cards.py)
    shape: str = "amount"      # "amount", "intensity" (shown per Rs crore) or "share" (a percentage)
    headline: bool = False     # counts in the scoreboard on top of the page
    size: str = "card"         # "card" (big) or "mini" (small)
    name: str = ""             # mini cards: the plain name under the abbreviation
    unit_words: str = ""       # shares: what the percent is of ("% of all energy")
    optional: bool = False     # a voluntary (Leadership) item: "not reported" is normal there
    only_if_present: bool = False   # newer filings only: leave the card out when the filing's edition has no such item
    also: tuple = ()           # more rows to mention in the fine print: ((label, SEBI row key), ...)
    title_as_filed: str = ""   # intensities: the title to use when the unit is unclear and the number could not be put per Rs crore
    replaces: str = ""         # intensities: the id of the total this per-sales figure is the fairer measure of (the summary page ranks one of the two)


@dataclass(frozen=True)
class Topic:
    id: str
    name: str
    icon: str                  # id of an <symbol> in the page's SVG icon set
    sebi: str                  # which SEBI questions it comes from
    intro: str                 # in plain words


@dataclass(frozen=True)
class Safeguard:
    id: str
    title: str
    what: str
    kind: str                  # "yes_no", "list", "percent" or "assurance"
    source: str                # question id ("E2"), table id ("E11") or row key ("L9.value")
    noun: str = ""             # lists: what the rows are ("projects")
    name_column: int = 0       # lists: which column of the table holds each row's name


@dataclass(frozen=True)
class StackPart:
    label: str                 # in the legend
    key: str                   # SEBI row key
    css: str                   # colour class in style.css
    short: str = ""            # how a sentence names it ("surface water")
    vague: bool = False        # a catch-all such as "Other sources": never named in a sentence


@dataclass(frozen=True)
class Stack:
    """A 'where does it go / come from' bar made of several parts that add up to a whole."""
    topic: str
    title: str
    parts: tuple
    sort: bool = False         # biggest part first?
    footnote: str = ""


# ----------------------------------------------------------------------------------------------------- topics
TOPICS = (
    Topic("energy", "Energy", "i-bolt", "SEBI Essential 1 · Leadership 1",
          "Factories, offices and vehicles run on electricity and fuel. Here is how much the company used, how much it uses for each "
          "₹ of sales, and how much came from renewable sources such as solar and wind."),
    Topic("climate", "Climate: greenhouse gases", "i-cloud", "SEBI Essential 6 · Leadership 4",
          "Burning fuel releases gases, mainly carbon dioxide (CO₂), that warm the planet. They are counted in tonnes of "
          "“CO₂-equivalent” (tCO₂e). Scope 1 is what the company releases itself; Scope 2 comes from the electricity it buys; "
          "Scope 3 is everything else in its supply chain (optional to report)."),
    Topic("water", "Water", "i-drop", "SEBI Essential 3-4 · Leadership 2-3",
          "Many industries use huge amounts of water to cool, clean or make products. Here is how much was taken in, how much the "
          "company says it used up, and where it came from."),
    Topic("air", "Air quality", "i-wind", "SEBI Essential 5",
          "Besides greenhouse gases, furnaces and chimneys release gases and particles that harm health and cause smog and acid rain. "
          "Lower is better for every one of them."),
    Topic("waste", "Waste", "i-bin", "SEBI Essential 8-9",
          "Waste can be recycled, reused, burned or buried. The better a company is at recovering it, the less ends up polluting "
          "land and air."),
    Topic("safeguards", "Nature and safeguards", "i-shield", "SEBI Essential 2, 4, 7, 10-12 · Leadership 7, 9",
          "Numbers alone cannot show whether a company is in control. These questions show whether it has the safeguards regulators "
          "expect. We show the company's own words so you can judge."),
)
TOPICS_BY_ID = {topic.id: topic for topic in TOPICS}

_SIZE_HINT = "Bigger companies use more, so also check the figure per ₹ of sales."

# ----------------------------------------------------------------------------------------------------- figures
METRICS = (
    # ---------------- energy
    MetricInfo("energy_total", "energy", "Total energy used", LOWER,
               "All the electricity, fuel and other energy the company used.",
               "Energy use drives both costs and greenhouse-gas emissions. " + _SIZE_HINT,
               "E1.total", headline=True),
    MetricInfo("energy_intensity", "energy", "Energy for every ₹ 1 crore of sales", LOWER,
               "Energy used divided by sales (called “energy intensity”).",
               "The fairest way to judge efficiency, because it still works when the company grows.",
               "E1.intensity", shape="intensity", headline=True, title_as_filed="Energy per unit of sales", replaces="energy_total"),
    MetricInfo("renewable_share", "energy", "Energy from renewable sources", HIGHER,
               "The part of all energy that came from renewables such as solar and wind.",
               "The more energy comes from renewables, the fewer greenhouse gases the same work causes.",
               "derived:renewable_share", shape="share", headline=True, unit_words="% of all energy", optional=True),

    # ---------------- climate
    MetricInfo("ghg_total", "climate", "Greenhouse gases released (Scope 1 + 2)", LOWER,
               "Gases from the company's own operations (Scope 1) plus from the electricity it buys (Scope 2).",
               "These gases trap heat in the atmosphere. This is the main number used to judge a company's climate impact.",
               "derived:ghg_scope_1_2", headline=True),
    MetricInfo("ghg_intensity", "climate", "Greenhouse gases for every ₹ 1 crore of sales", LOWER,
               "Scope 1 + 2 emissions divided by sales (“emission intensity”).",
               "Shows whether the company is getting cleaner per unit of business, even while it grows.",
               "E6.intensity", shape="intensity", headline=True, title_as_filed="Greenhouse gases per unit of sales", replaces="ghg_total"),
    MetricInfo("ghg_scope3", "climate", "Supply-chain emissions (Scope 3)", LOWER,
               "Emissions from suppliers, transport and customers, which the company does not control directly.",
               "For many companies this is the biggest part of their footprint, so a missing figure leaves a gap.",
               "L4.scope3", optional=True),

    # ---------------- water
    MetricInfo("water_in", "water", "Water taken in", LOWER,
               "All water drawn from rivers, groundwater, the sea or suppliers (1 kL = 1,000 litres).",
               "Fresh water is scarce in many parts of India. Taking less leaves more for people and farms.",
               "E3.withdrawal_total", headline=True, also=(("Water consumed", "E3.consumption"),)),
    MetricInfo("water_intensity", "water", "Water for every ₹ 1 crore of sales", LOWER,
               "Water consumed divided by sales (“water intensity”).",
               "Shows whether each ₹ of business needs more or less water than before.",
               "E3.intensity", shape="intensity", headline=True, title_as_filed="Water per unit of sales", replaces="water_in"),
    MetricInfo("water_out", "water", "Water given back (discharged)", CONTEXT,
               "Treated or untreated water the company released back to rivers, the sea or other receivers.",
               "Discharged water can carry pollutants. Whether it was treated first is the key question.",
               "L2.total", optional=True),

    # ---------------- air (small cards)
    MetricInfo("air_nox", "air", "NOx", LOWER, "From burning fuel; cause smog and breathing problems.", "", "E5.nox",
               headline=True, size="mini", name="nitrogen oxides"),
    MetricInfo("air_sox", "air", "SOx", LOWER, "From burning coal and oil; cause acid rain.", "", "E5.sox",
               headline=True, size="mini", name="sulphur oxides"),
    MetricInfo("air_pm", "air", "PM", LOWER, "Tiny dust and soot particles that reach deep into lungs.", "", "E5.pm",
               headline=True, size="mini", name="particulate matter"),
    MetricInfo("air_voc", "air", "VOC", LOWER, "Vapours from fuels and solvents that help form smog.", "", "E5.voc",
               headline=True, size="mini", name="volatile organic compounds"),
    MetricInfo("air_pop", "air", "POP", LOWER, "Long-lasting toxic chemicals.", "", "E5.pop", size="mini",
               name="persistent organic pollutants"),
    MetricInfo("air_hap", "air", "HAP", LOWER, "Toxic gases linked to cancer and other illness.", "", "E5.hap", size="mini",
               name="hazardous air pollutants"),

    # ---------------- waste
    MetricInfo("waste_total", "waste", "Waste produced", LOWER,
               "All waste produced, of every kind.",
               "Less waste means fewer resources thrown away and less to clean up. A growing company may produce more, so read it "
               "with the share recovered.",
               "E8.total", headline=True,
               also=(("Other hazardous waste (waste that can harm people or nature if not handled carefully)", "E8.other_hazardous"),)),
    MetricInfo("waste_intensity", "waste", "Waste for every ₹ 1 crore of sales", LOWER,
               "Waste produced divided by sales.",
               "Shows whether each ₹ of business creates more or less waste than before.",
               "X.waste_rupee", shape="intensity", headline=True, only_if_present=True, title_as_filed="Waste per unit of sales", replaces="waste_total"),
    MetricInfo("waste_recovered", "waste", "Waste recycled or reused", HIGHER,
               "The share of waste that was recycled, reused or otherwise recovered instead of burned or buried.",
               "Recovered waste does not end up in landfills or chimneys, so this is the best single sign of good waste handling.",
               "derived:recovered_share", shape="share", headline=True, unit_words="% of waste handled"),
)

# ----------------------------------------------------------------------------------------------------- safeguards
SAFEGUARDS = (
    Safeguard("pat", "Has sites covered by the government's energy-saving scheme (PAT)?",
              "PAT sets energy-saving targets for big industrial sites.", "yes_no", "E2"),
    Safeguard("zld", "Has a “zero liquid discharge” mechanism (no wastewater released)?",
              "Treats and reuses wastewater instead of releasing it.", "yes_no", "E4"),
    Safeguard("ghg_projects", "Has projects to cut greenhouse gases?",
              "Projects that reduce the company's own emissions.", "yes_no", "E7"),
    Safeguard("eia", "Checked the environmental impact of new projects?",
              "Impact assessments (EIAs) are studies done before building or expanding.", "list", "E11", noun="projects",
              name_column=0),
    Safeguard("sensitive", "Works in or near sensitive nature areas?",
              "Places such as national parks, wetlands and coastal zones need extra environmental approvals.", "list", "E10",
              noun="locations", name_column=1),
    Safeguard("laws", "Complies with environmental laws?",
              "Shown exactly as the company filed it.", "yes_no", "E12"),
    Safeguard("continuity", "Has an emergency and business-continuity plan?",
              "A plan for keeping operations safe and running in a crisis.", "yes_no", "L7"),
    Safeguard("suppliers", "Checks its suppliers' environmental impact?",
              "Share of supply-chain partners (by business value) assessed for environmental impact.", "percent", "L9.value"),
    Safeguard("assurance", "Figures independently checked by outside auditors?",
              "An independent check makes the numbers more trustworthy.", "assurance", ""),
)

# ----------------------------------------------------------------------------------------------------- "where does it go" bars
STACKS = (
    Stack("energy", "What kind of energy was it?",
          (StackPart("Fuel", "E1.fuel", "c2"), StackPart("Electricity", "E1.electricity", "c1"),
           StackPart("Other sources", "E1.other", "c5")), sort=True),
    Stack("climate", "Where do the greenhouse gases come from?",
          (StackPart("Scope 1: the company's own operations", "E6.scope1", "c1"),
           StackPart("Scope 2: electricity it buys", "E6.scope2", "c3"),
           StackPart("Scope 3: its supply chain", "L4.scope3", "c2"))),
    Stack("water", "Where did the water come from?",
          (StackPart("Surface water (rivers, lakes)", "E3.surface", "c2", "surface water"),
           StackPart("Seawater", "E3.sea", "c4", "seawater"),
           StackPart("Bought from suppliers", "E3.third_party", "c3", "water bought from suppliers"),
           StackPart("Groundwater", "E3.ground", "c1", "groundwater"),
           StackPart("Other sources", "E3.others", "c5", "other sources", vague=True)), sort=True),
    Stack("waste", "What happened to the waste?",
          (StackPart("Recycled", "E8.recycled", "g1"), StackPart("Reused", "E8.reused", "g2"),
           StackPart("Other recovery", "E8.other_recovery", "g3"),
           StackPart("Burned (incinerated)", "E8.incineration", "o1"), StackPart("Buried in landfill", "E8.landfill", "o2"),
           StackPart("Other disposal", "E8.other_disposal", "o3")),
          footnote="Green shades = recovered; orange and brown = disposed."),
)

# plain names for the sections an auditor may have checked (SEBI question id -> words)
ASSURANCE_NAMES = {
    "E1": "energy", "E3": "water", "E5": "air pollutants", "E6": "greenhouse gases (Scope 1 + 2)", "E8": "waste",
    "L1": "renewable energy split", "L2": "water discharge", "L3": "water in water-stressed areas", "L4": "Scope 3 emissions",
}

# ----------------------------------------------------------------------------------------------------- glossary
GLOSSARY = (
    ("GJ (gigajoule)", "A unit of energy. 1 GJ equals about 278 kWh, the “units” on an electricity bill."),
    ("kL (kilolitre)", "1,000 litres of water, the same as fifty 20-litre water cans."),
    ("tCO₂e (tonnes of CO₂-equivalent)",
     "One way to count all greenhouse gases together, by how much each warms the planet compared with CO₂."),
    ("Scope 1 / 2 / 3",
     "Scope 1: released by the company itself. Scope 2: released by whoever makes the electricity it buys. "
     "Scope 3: everything else along its supply chain."),
    ("Intensity (“per ₹ of sales”)",
     "The amount used or released for each ₹ of turnover. It lets you compare a company with itself even when it grows. "
     "We show it per ₹ 1 crore."),
    ("Lakh and crore", "1 lakh = 1,00,000 (a hundred thousand). 1 crore = 1,00,00,000 (ten million)."),
    ("Renewable energy", "Energy from sources that do not run out, such as sun, wind and flowing water."),
    ("NOx, SOx, PM, VOC, POP, HAP", "Air pollutants, listed in the Air quality section. None of them are greenhouse gases."),
    ("Zero liquid discharge", "Treating and reusing all wastewater so none is released."),
    ("PAT scheme", "“Perform, Achieve and Trade”: the Government of India's energy-saving targets for big industrial sites."),
    ("EIA", "Environmental Impact Assessment: a study of a project's effect on nature, done before it is built."),
    ("Standalone vs consolidated",
     "Standalone covers the company on its own. Consolidated adds its subsidiaries. The two should not be compared with each other."),
)
