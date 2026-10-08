"""Spot checks against REAL downloaded filings.  They are skipped automatically when the files are not on disk
(for example in a fresh clone), so the normal test run never needs the internet or the data folder.

Expected numbers come from the companies' own PDF reports, compared by hand (see context.md section 4b).
Fill the data folder first with:  python download_filings.py --company TATASTEEL
"""

import pytest

from brsr_p6.core.models import Status
from brsr_p6.core.paths import DEFAULT_RAW_DIR
from brsr_p6.extraction.extractor import build_report
from brsr_p6.parsing.xbrl_reader import read_filing

RAW = DEFAULT_RAW_DIR


def real_report(symbol, fy):
    files = sorted((RAW / symbol / fy).glob("*.xml"))
    if not files:
        pytest.skip(f"{symbol} FY {fy} is not downloaded")
    return build_report(read_filing(files[0]), symbol, symbol, fy)


def test_tata_steel_fy2025_26_matches_its_own_pdf():
    report = real_report("TATASTEEL", "2025-26")
    value = lambda key, year="current": getattr(report.metrics[key], year).value          # noqa: E731
    assert report.boundary == "Standalone basis" and report.family == "modern"
    assert value("E1.total") == pytest.approx(623_812_739, abs=1)             # PDF: 623.81 PJ
    assert value("E1.total", "previous") == pytest.approx(587_567_891, abs=1) # PDF: 587.56 PJ
    assert value("E3.surface") == pytest.approx(66_296_419, abs=1)            # PDF: 66,296 million litres
    assert value("E3.consumption") == pytest.approx(99_054_737, abs=1)        # PDF: 99,055 ML
    assert value("E5.nox") == 27_000 and value("E5.sox") == 67_000            # PDF: 27 and 67 kilotonnes
    assert value("E8.plastic") == 3_201 and value("E8.total") == 18_782_249   # PDF: 3,201 t and 1,87,82,249 t
    assert value("E8.landfill") == 17_513
    assert value("L9.value") == pytest.approx(82)


def test_tata_steel_scale_slip_is_flagged_but_not_corrected():
    scope1 = real_report("TATASTEEL", "2025-26").metrics["E6.scope1"].current
    assert scope1.value == 64                        # exactly as filed (the PDF says 64 MILLION tonnes)
    assert any("millions" in w for w in scope1.warnings)


def test_tata_steel_lists_and_facility_blocks_are_filled():
    report = real_report("TATASTEEL", "2025-26")
    assert len(report.tables["E10"].rows) == 25
    assert len(report.tables["E11"].rows) == 3
    assert len(report.facilities) == 1
    assert report.assurance["E6"].carried_out == "Yes"


def test_reliance_older_filing_uses_the_old_edition_but_reads_the_same_rows():
    report = real_report("RELIANCE", "2022-23")
    assert report.family == "legacy" and report.taxonomy_release == "2023-06-30"
    assert report.metrics["E1.total"].current.value == 473_590_585
    assert report.metrics["E1.total"].current.unit == "(unit not stated)"
    assert report.metrics["E5.nox"].current.value == 34_337                   # unit text 'Tonnes' was understood
    assert report.metrics["E6.scope1"].current.value == 37_095_658


def test_infosys_broken_xml_is_cleaned_and_still_readable():
    report = real_report("INFY", "2021-22")
    assert any("forbids" in w for w in report.warnings)
    assert report.metrics["E3.consumption"].current.value == 1_312_384
    assert report.metrics["E6.scope1"].current.status != Status.NOT_REPORTED


def test_boundary_can_change_between_years_for_the_same_company():
    assert real_report("WIPRO", "2023-24").boundary != real_report("WIPRO", "2024-25").boundary
