"""Tests for brsr_p6/views/sebi_view.py: the step that decides what each cell of the SEBI page shows."""

from xbrl_samples import both_years, context, fact, write_xbrl

from brsr_p6.core.models import Cell, Status
from brsr_p6.extraction.extractor import build_report
from brsr_p6.parsing.xbrl_reader import read_filing
from brsr_p6.views.sebi_view import Footnotes, build_sebi_view, cell_view


def view_for(tmp_path, facts="", extra_contexts=""):
    report = build_report(read_filing(write_xbrl(tmp_path, facts, extra_contexts=extra_contexts)), "Test Co", "TEST", "2023-24")
    return report, build_sebi_view(report)


def question(view, qid):
    return next(q for section in view.sections for q in section.questions if q.id == qid)


def row(view, qid, label_start):
    return next(r for r in question(view, qid).table.rows if r.label.startswith(label_start))


def test_footnote_numbers_are_reused_for_the_same_message():
    notes = Footnotes()
    assert notes.number("note", "A") == 1
    assert notes.number("warning", "B") == 2
    assert notes.number("note", "A") == 1          # same message, same number
    assert notes.number("warning", "A") == 3       # a warning with the same words is a different footnote
    assert notes.as_list() == [(1, "note", "A"), (2, "warning", "B"), (3, "warning", "A")]


def test_missing_values_are_written_as_not_reported_never_blank_or_zero():
    cell = cell_view(Cell(), Footnotes())
    assert cell.missing and cell.text == "Not reported"


def test_reported_number_gets_indian_digit_grouping_and_its_unit():
    cell = cell_view(Cell(24798900.25, "GJ", Status.REPORTED), Footnotes())
    assert (str(cell.text), cell.unit, cell.tags) == ("2,47,98,900.25", "GJ", [])


def test_calculated_and_converted_values_are_labelled():
    notes = Footnotes()
    assert cell_view(Cell(5, "GJ", Status.CALCULATED, note="sum"), notes).tags == ["calculated"]
    assert cell_view(Cell(5, "tonnes", Status.CONVERTED), notes).tags == ["converted"]


def test_warnings_and_notes_become_numbered_footnotes(tmp_path):
    facts = (both_years("TotalEnergyConsumedFromRenewableAndNonRenewableSources", 5000, 4000, "Gigajoule")
             + both_years("EnergyIntensityPerRupeeOfTurnover", 0, 0, "GigajoulePerINR"))
    _, view = view_for(tmp_path, facts)
    table = question(view, "E1").table
    intensity = row(view, "E1", "Energy intensity per rupee")
    assert intensity.current.warns == intensity.previous.warns == [1]            # both years share footnote 1
    assert any(kind == "warning" and "not a real zero" in text for _, kind, text in table.footnotes)


def test_tables_with_a_unit_column_move_the_unit_out_of_the_cell(tmp_path):
    _, view = view_for(tmp_path, both_years("NOx", 27, 24, "Kilotonne"))
    e5 = question(view, "E5")
    assert e5.table.unit_column == "Please specify unit"
    nox = row(view, "E5", "NOx")
    assert nox.unit == "tonnes" and nox.current.unit == ""
    assert question(view, "E1").table.unit_column == ""                          # E1 has no unit column in SEBI's form


def test_sections_follow_the_sebi_order(tmp_path):
    _, view = view_for(tmp_path)
    assert [s.title for s in view.sections] == ["Essential Indicators", "Leadership Indicators"]
    assert [q.number for q in view.sections[0].questions] == list(range(1, 13))
    assert [q.number for q in view.sections[1].questions] == list(range(1, 10))


def test_yes_no_text_and_number_questions(tmp_path):
    facts = (fact("HasTheEntityImplementedAMechanismForZeroLiquidDischarge", "true")
             + fact("DetailsOfCoverageAndImplementationIfForZeroLiquidDischargeExplanatoryTextBlock", "All sites"))
    _, view = view_for(tmp_path, facts)
    zld = question(view, "E4")
    assert zld.answer.text == "Yes" and zld.details == "All sites"
    assert question(view, "E9").answer is None and question(view, "E9").details is None     # text question, nothing reported
    assert question(view, "L9").answer.missing


def test_list_questions_mark_unreported_cells_as_muted(tmp_path):
    contexts = context("D_1", "RowAxis", "Row1")
    facts = fact("LocationOfOperationsOrOffices", "Jamnagar", "D_1")
    _, view = view_for(tmp_path, facts, extra_contexts=contexts)
    rows = question(view, "E10").listing.rows
    assert rows[0][1] == ("Jamnagar", False)
    assert rows[0][2] == ("Not reported", True)


def test_extras_block_exists_only_when_the_filing_has_extra_items(tmp_path):
    assert view_for(tmp_path)[1].extras is None
    facts = both_years("WasteIntensityPerRupeeOfTurnover", 0.0000134, 0.0000131, "TonnePerINR")
    assert view_for(tmp_path, facts)[1].extras.rows[0].label == "Waste intensity per rupee of turnover"
