"""Tests for the TRACE: every value the extractor keeps remembers the filing's own element, year and text it came from.

The brief says "every figure shown must trace back to a filing".  The first half of this file uses tiny fake filings to check
the bookkeeping; the last test opens every REAL filing on disk and checks the trace against the raw XML text itself.
"""

import html
import re
from types import SimpleNamespace

import pytest
from xbrl_samples import both_years, context, fact, write_xbrl

from brsr_p6.core.models import Origin, Status
from brsr_p6.core.paths import DEFAULT_RAW_DIR
from brsr_p6.extraction.extractor import build_report
from brsr_p6.parsing import p6_mapping as mapping
from brsr_p6.parsing.xbrl_reader import read_filing

CURRENT, PREVIOUS = "2024-03-31", "2023-03-31"


def report_for(tmp_path, facts="", release="2024-04-30", extra_contexts="", fy="2023-24", record=None):
    filing = read_filing(write_xbrl(tmp_path, facts, release=release, extra_contexts=extra_contexts))
    return build_report(filing, "Test Company Limited", "TEST", fy, record=record)


# ------------------------------------------------------------------------------------------------ one value, one origin
def test_a_reported_number_remembers_its_element_year_unit_and_text(tmp_path):
    facts = both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 4000, "Gigajoule")
    metric = report_for(tmp_path, facts).metrics["E1.total"]
    assert metric.current.origin == [Origin("TotalEnergyConsumedFromRenewableAndNonRenewableSources", "5000", "Gigajoule", CURRENT)]
    assert metric.previous.origin == [Origin("TotalEnergyConsumedFromRenewableAndNonRenewableSources", "4000", "Gigajoule", PREVIOUS)]


def test_a_converted_number_keeps_the_origin_of_the_unit_it_was_filed_in(tmp_path):
    cell = report_for(tmp_path, both_years("NOx", 27, 24, "Kilotonne")).metrics["E5.nox"].current
    assert (cell.value, cell.unit, cell.status) == (27000, "tonnes", Status.CONVERTED)
    assert cell.origin == [Origin("NOx", "27", "Kilotonne", CURRENT)]                  # the trace says what the FILING said, not what we show


def test_a_calculated_number_lists_every_element_it_was_built_from(tmp_path):
    facts = (both_years("TotalElectricityConsumptionFromRenewableSources", 100, 80, "Gigajoule")
             + both_years("TotalElectricityConsumptionFromNonRenewableSources", 900, 700, "Gigajoule"))
    cell = report_for(tmp_path, facts).metrics["E1.electricity"].current
    assert cell.status == Status.CALCULATED
    assert [(o.element, o.raw) for o in cell.origin] == [("TotalElectricityConsumptionFromRenewableSources", "100"),
                                                         ("TotalElectricityConsumptionFromNonRenewableSources", "900")]


def test_row_labelled_facts_that_are_added_up_say_how_many_rows(tmp_path):
    contexts = context("D_o1", "OtherAxis", "Other1") + context("D_o2", "OtherAxis", "Other2")
    facts = (fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 3, "D_o1", "Gigajoule")
             + fact("EnergyConsumptionThroughOtherSourcesFromRenewableSources", 4, "D_o2", "Gigajoule")
             + fact("EnergyConsumptionThroughOtherSourcesFromNonRenewableSources", 10, "DCYMain", "Gigajoule"))
    cell = report_for(tmp_path, facts, extra_contexts=contexts).metrics["E1.other"].current
    assert [(o.element, o.raw, o.rows) for o in cell.origin] == [("EnergyConsumptionThroughOtherSourcesFromRenewableSources", "7", 2),
                                                                 ("EnergyConsumptionThroughOtherSourcesFromNonRenewableSources", "10", 1)]


def test_the_element_is_quoted_in_the_filings_own_spelling(tmp_path):
    """NSE spells tags inconsistently, and we look them up ignoring case.  The trace must quote what is really in the file."""
    facts = both_years("NOX", 5, 6, "Tonne")
    cell = report_for(tmp_path, facts).metrics["E5.nox"].current
    assert cell.value == 5 and cell.origin[0].element == "NOX"


def test_yes_no_answers_and_percentages_have_an_origin_too(tmp_path):
    tag = "PercentageOfValueChainPartnersByValueOfBusinessDoneWithSuchPartnersThatWereAssessedForEnvironmentalImpacts"
    report = report_for(tmp_path, fact("HasTheEntityImplementedAMechanismForZeroLiquidDischarge", "true") + fact(tag, "0.11"))
    answer = report.metrics["E4.answer"].current
    assert (answer.value, answer.origin) == ("Yes", [Origin("HasTheEntityImplementedAMechanismForZeroLiquidDischarge", "true", "", CURRENT)])
    percent = report.metrics["L9.value"].current
    assert (percent.value, percent.status) == (pytest.approx(11), Status.CONVERTED)
    assert percent.origin == [Origin(tag, "0.11", "", CURRENT)]


def test_an_older_filings_unit_text_element_is_part_of_the_trace(tmp_path):
    facts = both_years("Nox", 34, 37, "pure") + fact("UnitOfNox", "Kilotonnes/year")
    cell = report_for(tmp_path, facts, release="2021-09-30").metrics["E5.nox"].current
    assert [(o.element, o.raw) for o in cell.origin] == [("Nox", "34"), ("UnitOfNox", "Kilotonnes/year")]


# ------------------------------------------------------------------------------------------------ nothing there
def test_a_value_the_filing_does_not_have_has_no_origin_and_says_what_was_looked_for(tmp_path):
    report = report_for(tmp_path, both_years("NOx", 1, 1, "Kilotonne"))
    cell = report.metrics["E5.sox"].current
    assert cell.status == Status.NOT_REPORTED and cell.origin == []
    assert cell.looked_for == list(mapping.SOURCES["E5.sox"].modern)           # "we searched for these elements and found nothing"


def test_a_row_with_no_xbrl_field_says_so_instead_of_naming_elements(tmp_path):
    cell = report_for(tmp_path, both_years("NOx", 1, 1, "Kilotonne")).metrics["E5.others"].current
    assert cell.origin == [] and cell.looked_for == [] and "no field" in cell.note


# ------------------------------------------------------------------------------------------------ the link to the filing
def record(url, pdf="https://example.org/f.pdf"):
    return SimpleNamespace(xbrl_url=url, pdf_url=pdf, submission_date="01-Jun-2024", revision_date=None)


def test_the_report_keeps_the_nse_links_of_the_filing(tmp_path):
    report = report_for(tmp_path, record=record("https://nsearchives.nseindia.com/corporate/xbrl/f.xml"))
    assert report.source_url == "https://nsearchives.nseindia.com/corporate/xbrl/f.xml" and report.pdf_url == "https://example.org/f.pdf"


@pytest.mark.parametrize("bad", ["", None, "javascript:alert(1)", "http://insecure.example/f.xml", "ftp://x/y"])
def test_only_an_https_link_is_kept_because_it_becomes_a_clickable_link(tmp_path, bad):
    report = report_for(tmp_path, record=record(bad, pdf=bad))
    assert report.source_url == "" and report.pdf_url == ""


def test_no_record_means_no_link(tmp_path):
    assert report_for(tmp_path).source_url == ""


# ------------------------------------------------------------------------------------------------ list tables and assurance
def test_a_list_table_names_the_elements_its_rows_came_from(tmp_path):
    contexts = context("D_1", "EIAAxis", "EIA1")
    facts = fact("WhetherTheConditionsOfEnvironmentalApprovalOrClearanceAreBeingCompliedWith", "true", "D_1")
    report = report_for(tmp_path, facts, extra_contexts=contexts)
    tables = [t for t in report.tables.values() if t.rows and any("Yes" in c for c in t.rows[0])]
    assert tables and "WhetherTheConditionsOfEnvironmentalApprovalOrClearanceAreBeingCompliedWith" in tables[0].elements


def test_an_empty_list_table_lists_the_elements_that_were_looked_for(tmp_path):
    report = report_for(tmp_path)
    assert all(table.elements for table in report.tables.values())


def test_the_assurance_answer_names_the_element_it_was_read_from(tmp_path):
    facts = fact("AnyIndependentAssessmentOrEvaluationOrAssuranceHasBeenCarriedOutByAnExternalAgencyForWaterWithdrawal", "true")
    assurance = report_for(tmp_path, facts).assurance["E3"]
    assert assurance.carried_out == "Yes" and assurance.elements == ["AnyIndependentAssessmentOrEvaluationOrAssuranceHasBeenCarriedOutByAnExternalAgencyForWaterWithdrawal"]


# ------------------------------------------------------------------------------------------------ the proof, on real filings
def all_cells(report):
    for metric in list(report.metrics.values()) + list(report.extras.values()):
        yield metric.key, metric.current, "current"
        yield metric.key, metric.previous, "previous"
    for facility in report.facilities:
        for metric in facility.metrics.values():
            yield metric.key, metric.current, "current"
            yield metric.key, metric.previous, "previous"


def facts_written_in(xml_text):
    """{(element, value text)} read straight from the raw XML with a regular expression (not with our own reader).

    The only tidying is the one the reader promises: line breaks and runs of spaces inside a value become one space."""
    pairs = re.findall(r"<(?:[\w.-]+:)?([\w.-]+)(?=[\s>/])[^>]*>\s*([^<]*?)\s*</", xml_text)
    return {(name, " ".join(html.unescape(text).split())) for name, text in pairs}


def real_filing_files():
    return sorted(DEFAULT_RAW_DIR.glob("*/*/*.xml")) if DEFAULT_RAW_DIR.exists() else []


def test_every_value_in_every_real_filing_traces_back_to_text_that_is_really_in_the_xml_file():
    files = real_filing_files()
    if not files:
        pytest.skip("no filings downloaded")
    checked = 0
    for path in files:
        filing = read_filing(path)
        report = build_report(filing, "X", path.parent.parent.name, path.parent.name)
        written = facts_written_in(path.read_bytes().decode("utf-8", errors="replace"))
        where = f"{path.parent.parent.name} {path.parent.name}"
        ends = {"current": filing.current_end.isoformat(), "previous": filing.previous_end.isoformat()}
        for key, cell, side in all_cells(report):
            if cell.status == Status.NOT_REPORTED:
                assert cell.origin == [], (where, key)
                continue
            assert cell.origin, f"{where} {key} {side}: a value with no trace"          # nothing is shown without a trace
            for origin in cell.origin:
                assert origin.period_end in ends.values(), (where, key, origin)
                if origin.rows == 1:                                                    # a sum of rows has no single text to find
                    assert (origin.element, origin.raw) in written, f"{where} {key} {side}: {origin.element} = {origin.raw!r} is not in the file"
                else:
                    assert any(name == origin.element for name, _ in written), (where, key, origin)
                checked += 1
    assert checked > 1000       # a real run covers thousands of values: the test is not passing on nothing
