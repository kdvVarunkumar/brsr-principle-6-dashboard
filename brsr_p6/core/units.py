"""Unit rules: turn each number into ONE standard unit per topic, and say so when we changed something.

Standard units we show:   energy -> GJ      water -> kL      waste and air pollutants -> tonnes      greenhouse gases -> tCO2e

Facts learned from real filings (see context.md):
  * Newer filings give a unit id such as "Gigajoule" or "Kg"; older filings give nothing ("pure") and sometimes a
    free-text unit in a separate tag such as UnitOfNox = "Kilotonnes/year".
  * "MtCO2e" and "tCO2e" both mean metric tonnes of CO2 equivalent (NOT million tonnes).
"""

from brsr_p6.core.models import Status

# unit id in the filing -> how many standard units one of them is worth
# (Terajoule and Megajoule are used by ITC and Wipro; Petajoule and Kilojoule are the other exact SI multiples.)
_ENERGY = {"Gigajoule": 1.0, "Terajoule": 1_000.0, "Petajoule": 1_000_000.0, "Megajoule": 0.001, "Kilojoule": 0.000_001}
_WATER = {"Kiloliters": 1.0}
_MASS = {"Tonne": 1.0, "Kilotonne": 1000.0, "Kg": 0.001}
_GHG = {"tCO2e": 1.0, "MtCO2e": 1.0, "ktCO2e": 1000.0}

# topic -> (table of known unit ids, name of the standard unit)
_TOPICS = {
    "energy": (_ENERGY, "GJ"),
    "water": (_WATER, "kL"),
    "mass": (_MASS, "tonnes"),    # waste
    "air": (_MASS, "tonnes"),     # air pollutants
    "ghg": (_GHG, "tCO2e"),
}

# "per rupee of turnover" units: unit id -> (how many standard units one of them is worth, the standard label)
_INTENSITY_UNITS = {
    "GigajoulePerINR": (1.0, "GJ per ₹"),
    "TerajoulePerINR": (1_000.0, "GJ per ₹"),
    "MegajoulePerINR": (0.001, "GJ per ₹"),
    "KilolitersPerINR": (1.0, "kL per ₹"),
    "tCO2ePerINR": (1.0, "tCO2e per ₹"),
    "MtCO2ePerINR": (1.0, "tCO2e per ₹"),
    "ktCO2ePerINR": (1_000.0, "tCO2e per ₹"),
    "TonnePerINR": (1.0, "tonnes per ₹"),
}
# the same idea for the free-text units of older filings (lower case, spaces removed)
_INTENSITY_TEXT = {
    "tco2e/rs": (1.0, "tCO2e per ₹"),
    "tco2e/inr": (1.0, "tCO2e per ₹"),
    "tco2e/₹": (1.0, "tCO2e per ₹"),
}

UNIT_NOT_STATED = "(unit not stated)"


def convert(kind, number, unit_id="", legacy_text=""):
    """Convert one number.  Returns (value, unit_label, status, note, warnings).

    kind         "energy", "water", "mass", "air", "ghg" or "intensity"
    unit_id      the unit id from the filing ("Gigajoule", "Kg", ...), "" or "pure" if none
    legacy_text  free-text unit from older filings (e.g. "Kilotonnes/year"), "" if none
    """
    unit_id = "" if unit_id in (None, "pure") else unit_id

    if kind == "intensity":
        return _intensity(number, unit_id, legacy_text)

    known_ids, standard = _TOPICS[kind]

    if unit_id in known_ids:  # the normal case in newer filings
        return _scaled(number, known_ids[unit_id], standard, unit_id)

    if unit_id:  # a unit id we do not know: do not guess, show as filed
        return number, unit_id, Status.REPORTED, "", [f"Unit '{unit_id}' is not one I can convert; shown as filed."]

    return _from_old_filing(kind, number, legacy_text, standard)


def _from_old_filing(kind, number, legacy_text, standard):
    """Older filings state no unit id.  Use the free-text unit if there is one, else the SEBI form's own unit."""
    if kind == "energy":  # SEBI's form only says "Joules or multiples": the multiple is genuinely unknown
        return number, UNIT_NOT_STATED, Status.REPORTED, "", [
            "This filing does not state the unit of its energy figures (the SEBI form says 'Joules or multiples'). Shown as filed."
        ]

    if kind in ("water", "mass"):  # the SEBI form fixes these units (kilolitres, metric tonnes)
        note = f"The filing states no unit; {standard} as required by the SEBI form."
        return number, standard, Status.REPORTED, note, []

    # air pollutants and greenhouse gases: older filings carry the unit as free text in a separate tag
    parsed = read_unit_text(legacy_text)
    if parsed is None:
        if kind == "ghg":
            return number, standard, Status.REPORTED, "", [
                f"The filing's unit text ('{legacy_text or 'none'}') is unclear; metric tonnes of CO2e assumed, as in the SEBI form."
            ]
        return number, UNIT_NOT_STATED, Status.REPORTED, "", ["The filing does not state a usable unit for this figure. Shown as filed."]

    factor, per_month = parsed
    value = tidy_number(number * factor)
    status = Status.REPORTED if factor == 1.0 else Status.CONVERTED
    note = "" if factor == 1.0 else f"Converted from '{legacy_text}' to {standard} (x {factor:g}); the filed figure is kept in the saved data."
    warnings = []
    label = standard
    if per_month:  # a monthly rate is NOT a yearly total: never silently multiply by 12
        label = f"{standard} per month"
        warnings.append(f"Filed as a monthly figure ('{legacy_text}'), not a yearly one. Shown as filed; not converted to a yearly total.")
    return value, label, status, note, warnings


def read_unit_text(text):
    """Understand a free-text unit.  Returns (factor_to_standard, is_per_month) or None if we cannot tell."""
    t = (text or "").lower().replace(" ", "")
    if t in ("", "0", "na", "n/a", "-", "nil", "none"):
        return None
    per_month = "month" in t
    if "kilotonne" in t or "ktco2" in t:
        return 1000.0, per_month
    if "million" in t:
        return 1_000_000.0, per_month
    if "kg" in t or "kilogram" in t:
        return 0.001, per_month
    if "tonne" in t or "tco2" in t:
        return 1.0, per_month
    return None  # e.g. just "MT": could mean metric or million tonnes, so we do not guess


def _scaled(number, factor, label, original_unit):
    """Multiply by the unit factor.  Returns the same 5-tuple as convert(); a factor of 1 changes nothing."""
    if factor == 1.0:
        return number, label, Status.REPORTED, "", []
    note = f"Converted from {original_unit} to {label} (x {factor:g}); the filed figure is kept in the saved data."
    return tidy_number(number * factor), label, Status.CONVERTED, note, []


def tidy_number(number):
    """Drop floating-point noise: 3.47e-8 * 1000 is 3.4700000000000004e-05 in Python; we want 3.47e-05."""
    return float(f"{number:.12g}")


def _intensity(number, unit_id, legacy_text):
    """Per-rupee intensities are put in one standard unit when the unit is a known exact multiple; others are shown as filed."""
    if unit_id:
        if unit_id in _INTENSITY_UNITS:
            factor, label = _INTENSITY_UNITS[unit_id]
            return _scaled(number, factor, label, unit_id)
        return number, unit_id, Status.REPORTED, "", []
    text = (legacy_text or "").strip()
    if text.lower() in ("", "0", "na", "n/a", "-", "nil"):
        return number, UNIT_NOT_STATED, Status.REPORTED, "", ["The filing does not state the unit of this intensity figure. Shown as filed."]
    known = _INTENSITY_TEXT.get(text.lower().replace(" ", ""))
    if known:
        return _scaled(number, known[0], known[1], text)
    return number, text, Status.REPORTED, "", []
