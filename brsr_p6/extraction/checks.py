"""Sanity checks.  They never change a number; they only ADD WARNINGS to cells that look doubtful.

Why: real filings contain slips (see context.md section 4c): a tiny intensity rounded to 0, a total that does not
equal its parts, an emissions figure typed in millions under a unit that means tonnes.  Our promise is to show the
reader the value as filed and say clearly when it is doubtful.
"""

from brsr_p6.core.models import Status

YEARS = ("current", "previous")

# (intensity row, the total it is "per rupee" of)
INTENSITY_PAIRS = (
    ("E1.intensity", "E1.total"),
    ("E1.intensity_optional", "E1.total"),
    ("E3.intensity", "E3.consumption"),
    ("E3.intensity_optional", "E3.consumption"),
    ("E6.intensity", "E6.scope1"),
    ("E6.intensity_optional", "E6.scope1"),
    ("L4.intensity", "L4.scope3"),
    ("L4.intensity_optional", "L4.scope3"),
)

AIR_ROWS = ("E5.nox", "E5.sox", "E5.pm", "E5.pop", "E5.voc", "E5.hap")

# (total row, the rows that should add up to it)
SUM_RULES = (
    ("E1.total", ("E1.electricity", "E1.fuel", "E1.other")),
    ("E3.withdrawal_total", ("E3.surface", "E3.ground", "E3.third_party", "E3.sea", "E3.others")),
    ("E8.total", ("E8.plastic", "E8.ewaste", "E8.biomedical", "E8.construction", "E8.battery", "E8.radioactive",
                  "E8.other_hazardous", "E8.other_non_hazardous")),
    ("E8.recovered_total", ("E8.recycled", "E8.reused", "E8.other_recovery")),
    ("E8.disposed_total", ("E8.incineration", "E8.landfill", "E8.other_disposal")),
    ("L1.re_total", ("L1.re_electricity", "L1.re_fuel", "L1.re_other")),
    ("L1.nre_total", ("L1.nre_electricity", "L1.nre_fuel", "L1.nre_other")),
    ("L2.total", ("L2.surface", "L2.ground", "L2.sea", "L2.third_party", "L2.others")),
)

# Burning fuel releases roughly 0.01 - 0.5 tonnes of CO2e per gigajoule.  Far outside that = something is off.
PLAUSIBLE_TONNES_PER_GJ = (0.003, 1.0)


def run_checks(report):
    _suspicious_zero_intensities(report)
    _air_zeros(report)
    _totals_add_up(report)
    _emission_scale(report)


def _number(report, key, year):
    """The numeric value of a cell, or None."""
    metric = report.metrics.get(key)
    if metric is None:
        return None
    cell = getattr(metric, year)
    if cell.status == Status.NOT_REPORTED or not isinstance(cell.value, (int, float)):
        return None
    return cell.value


def _warn(report, key, year, message):
    cell = getattr(report.metrics[key], year)
    if message not in cell.warnings:
        cell.warnings.append(message)


def _suspicious_zero_intensities(report):
    for intensity_key, total_key in INTENSITY_PAIRS:
        for year in YEARS:
            intensity, total = _number(report, intensity_key, year), _number(report, total_key, year)
            if intensity == 0 and total and total > 0:
                _warn(report, intensity_key, year,
                      "Reported as 0, but the total it relates to is not zero. A real intensity is never exactly 0, so this 0 means "
                      "'rounded away or left blank'; it is not a real zero.")


def _air_zeros(report):
    for key in AIR_ROWS:
        for year in YEARS:
            if _number(report, key, year) == 0:
                _warn(report, key, year,
                      "A reported 0 can mean 'none', or 'not measured / not material'. The filing does not say which.")


def _totals_add_up(report):
    for total_key, part_keys in SUM_RULES:
        for year in YEARS:
            total = _number(report, total_key, year)
            parts = [_number(report, key, year) for key in part_keys]
            if total is None or any(p is None for p in parts):
                continue  # only compare when every number is present
            difference = abs(sum(parts) - total)
            if difference > max(0.01 * abs(total), 1.0):
                _warn(report, total_key, year,
                      f"The rows above add up to {sum(parts):,.2f} but the filing's own total is {total:,.2f}.")


def _emission_scale(report):
    """Compare Scope 1 + 2 emissions (tonnes) with total energy (GJ): a wildly small ratio means a scale slip."""
    for year in YEARS:
        energy_cell = getattr(report.metrics["E1.total"], year)
        scope1, scope2 = _number(report, "E6.scope1", year), _number(report, "E6.scope2", year)
        if energy_cell.unit != "GJ" or not isinstance(energy_cell.value, (int, float)) or not energy_cell.value or not scope1:
            continue  # without a known energy unit or an emissions figure there is nothing to compare
        emissions = scope1 + (scope2 or 0)
        ratio = emissions / energy_cell.value
        low, high = PLAUSIBLE_TONNES_PER_GJ

        message = None
        if ratio < low / 300:  # far too small: look for a missing x1,000 or x1,000,000
            for factor, name in ((1_000, "thousands"), (1_000_000, "millions")):
                if low <= ratio * factor <= high:
                    message = (f"Scope 1+2 emissions look about {factor:,} times too small for this company's energy use "
                               f"({ratio:.1e} tonnes per GJ; normal is roughly 0.01 to 0.5). The figure may have been typed in {name} "
                               f"of tonnes. Shown exactly as filed; not corrected.")
                    break
        elif ratio > 2:
            message = (f"Scope 1+2 emissions look far too large for this company's energy use ({ratio:,.1f} tonnes per GJ; "
                       f"normal is roughly 0.01 to 0.5). Shown exactly as filed.")
        if message:
            for key in ("E6.scope1", "E6.scope2"):
                if _number(report, key, year) is not None:
                    _warn(report, key, year, message)
            # A company that typed its Scope 1+2 in millions usually did the same for Scope 3.
            if _number(report, "L4.scope3", year) is not None:
                _warn(report, "L4.scope3", year,
                      "Scope 1+2 look mis-scaled (see the warning on Scope 1) and Scope 3 was probably typed the same way. "
                      "Shown exactly as filed; not corrected.")
