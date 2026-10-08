"""Tests for brsr_p6/parsing/xbrl_reader.py (using tiny fake filings)."""

from datetime import date

import pytest
from xbrl_samples import both_years, context, fact, write_xbrl

from brsr_p6.core.errors import UnparseableFiling
from brsr_p6.parsing.xbrl_reader import read_filing


def test_years_are_decided_from_dates_and_facts_are_assigned_to_them(tmp_path):
    path = write_xbrl(tmp_path, both_years("TotalScope1Emissions", "64", "61", unit="tCO2e"))
    filing = read_filing(path)
    assert filing.current_end == date(2024, 3, 31) and filing.previous_end == date(2023, 3, 31)
    assert filing.facts_named("TotalScope1Emissions", "current")[0].text == "64"
    assert filing.facts_named("TotalScope1Emissions", "previous")[0].text == "61"
    assert filing.facts_named("TotalScope1Emissions", "current")[0].unit == "tCO2e"


@pytest.mark.parametrize("release, family", [
    ("2021-09-30", "legacy"), ("2023-06-30", "legacy"),      # both seen on real filings
    ("2024-04-30", "modern"), ("2025-05-31", "modern"), ("2026-02-28", "modern"),
])
def test_edition_of_the_form_decides_legacy_or_modern(tmp_path, release, family):
    filing = read_filing(write_xbrl(tmp_path, release=release))
    assert filing.family == family and filing.release == date.fromisoformat(release)


def test_tag_lookup_ignores_upper_and_lower_case(tmp_path):
    """NSE spells 'WithOutTreatment' in one tag and 'WithoutTreatment' in the next."""
    filing = read_filing(write_xbrl(tmp_path, fact("WaterDischargeToOthersWithoutTreatment", "7")))
    assert filing.facts_named("WaterDischargeToOthersWithOutTreatment")[0].text == "7"


def test_tags_that_contain_the_word_link_are_still_read(tmp_path):
    """A first version dropped every tag containing 'link' (e.g. WebLink...), which hid real answers."""
    filing = read_filing(write_xbrl(tmp_path, fact("DisclosureWebLinkOfEntityAtWhichBusinessContinuityPlanIsPlaced", "https://x.example/plan")))
    assert filing.text_of("DisclosureWebLinkOfEntityAtWhichBusinessContinuityPlanIsPlaced") == "https://x.example/plan"


def test_row_labels_separate_facts_and_plain_facts_ignore_them(tmp_path):
    contexts = context("D_Init1", "SpecificInitiativesAxis", "SpecificInitiativesDomain1") + context("D_Init2", "SpecificInitiativesAxis", "SpecificInitiativesDomain2")
    facts = fact("InitiativeUndertaken", "Solar roof", "D_Init1") + fact("InitiativeUndertaken", "Rain harvesting", "D_Init2") + fact("InitiativeUndertaken", "plain", "DCYMain")
    filing = read_filing(write_xbrl(tmp_path, facts, extra_contexts=contexts))
    assert [f.text for f in filing.facts_named("InitiativeUndertaken")] == ["plain"]       # dims=() means plain facts only
    assert len(filing.facts_named("InitiativeUndertaken", dims=None)) == 3                  # dims=None means any
    labels = filing.row_labels("InitiativeUndertaken")
    assert [l[0].split("=")[1] for l in labels] == ["SpecificInitiativesDomain1", "SpecificInitiativesDomain2"]


def test_row_labels_use_natural_order(tmp_path):
    contexts = "".join(context(f"D_{n}", "RowAxis", f"Row{n}") for n in (10, 2, 1))
    facts = "".join(fact("LocationOfOperationsOrOffices", f"loc{n}", f"D_{n}") for n in (10, 2, 1))
    filing = read_filing(write_xbrl(tmp_path, facts, extra_contexts=contexts))
    assert [l[0].split("=")[1] for l in filing.row_labels("LocationOfOperationsOrOffices")] == ["Row1", "Row2", "Row10"]


def test_single_day_facts_count_for_the_year_that_ends_that_day(tmp_path):
    contexts = context("I_Loc1", "RowAxis", "Row1", instant=True)
    filing = read_filing(write_xbrl(tmp_path, fact("TypeOfOperations", "Mining", "I_Loc1"), extra_contexts=contexts))
    assert filing.facts_named("TypeOfOperations", "current", dims=None)[0].text == "Mining"


def test_forbidden_characters_are_removed_with_a_warning(tmp_path):
    """Real case: Infosys FY2021-22 has 15 control characters inside long text answers."""
    data = write_xbrl(tmp_path, fact("DetailsOfWaste", "up-\x02date text")).read_bytes()
    path = write_xbrl(tmp_path, name="bad.xml", as_bytes=data)
    filing = read_filing(path)
    assert filing.text_of("DetailsOfWaste") == "up-date text"
    assert any("1 characters" in w for w in filing.warnings)


def test_broken_xml_gives_a_clear_error_with_position(tmp_path):
    path = write_xbrl(tmp_path, name="broken.xml", as_bytes=b'<?xml version="1.0"?><xbrli:xbrl xmlns:in-capmkt="https://www.sebi.gov.in/xbrl/2024-04-30/in-capmkt"><oops></xbrli:xbrl>')
    with pytest.raises(UnparseableFiling) as excinfo:
        read_filing(path)
    assert "broken.xml" in str(excinfo.value) and "line" in str(excinfo.value)


def test_a_file_that_is_not_a_brsr_filing_is_refused(tmp_path):
    path = write_xbrl(tmp_path, name="other.xml", as_bytes=b'<?xml version="1.0"?><html><body>Access denied</body></html>')
    with pytest.raises(UnparseableFiling) as excinfo:
        read_filing(path)
    assert "does not look like a SEBI BRSR" in str(excinfo.value)
