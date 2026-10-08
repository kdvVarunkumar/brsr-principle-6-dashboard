"""Tests for brsr_p6/warning_kinds.py."""

from pathlib import Path

import pytest

from brsr_p6.extractor import build_report
from brsr_p6.warning_kinds import CHECK, DOUBTFUL, OK, is_known, kind_of, worst_kind
from brsr_p6.xbrl_reader import read_filing

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def test_a_scale_slip_is_doubtful():
    text = "Scope 1+2 emissions look about 1,000,000 times too small for this company's energy use (1.1e-07 tonnes per GJ)."
    assert kind_of(text) == DOUBTFUL and is_known(text)


def test_a_zero_intensity_and_parts_that_do_not_add_up_are_doubtful():
    assert kind_of("Reported as 0, but the total it relates to is not zero. A real intensity is never exactly 0, so ...") == DOUBTFUL
    assert kind_of("The rows above add up to 6,958,071.00 but the filing's own total is 6,826,744.00.") == DOUBTFUL


def test_a_missing_unit_or_an_ambiguous_zero_needs_a_check_but_is_not_doubtful():
    assert kind_of("This filing does not state the unit of its energy figures (the SEBI form says 'Joules or multiples'). Shown as filed.") == CHECK
    assert kind_of("A reported 0 can mean 'none', or 'not measured / not material'. The filing does not say which.") == CHECK
    assert kind_of("Unit 'tCO2e' is not one I can convert; shown as filed.") == CHECK


def test_an_unknown_warning_is_treated_as_doubtful():
    """When in doubt, say so: an unclassified warning must never lead to a confident 'Improved'."""
    assert not is_known("Something nobody has seen before")
    assert kind_of("Something nobody has seen before") == DOUBTFUL


def test_worst_kind_picks_the_most_serious():
    assert worst_kind([]) == OK
    assert worst_kind(["A reported 0 can mean 'none'"]) == CHECK
    assert worst_kind(["A reported 0 can mean 'none'", "The rows above add up to 1 but the filing's own total is 2."]) == DOUBTFUL


def test_every_warning_in_every_downloaded_filing_is_classified():
    """The guard: if a new warning sentence appears, this fails until someone decides how serious it is."""
    files = sorted(RAW.glob("*/*/*.xml"))
    if not files:
        pytest.skip("no filings downloaded")
    unknown = set()
    for path in files:
        report = build_report(read_filing(path), path.parts[-3], path.parts[-3], path.parts[-2])
        for metric in list(report.metrics.values()) + list(report.extras.values()):
            for cell in (metric.current, metric.previous):
                unknown |= {w for w in cell.warnings if not is_known(w)}
    assert not unknown, f"unclassified warnings: {sorted(unknown)}"
