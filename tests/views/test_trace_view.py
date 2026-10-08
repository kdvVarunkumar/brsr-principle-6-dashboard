"""Tests for brsr_p6/views/trace_view.py: the words of the trace from a number to the filing."""

from dashboard_samples import blank_report

from brsr_p6.cli.extract_cli import build_parser
from brsr_p6.core.models import Cell, Facility, Metric, Origin, Status
from brsr_p6.core.sebi_template import QUESTIONS
from brsr_p6.views.report_text import render_text
from brsr_p6.views.trace_view import (MAX_TEXT, build_trace_view, cell_lines, figure_trace, nothing_text, origin_text, short, shown_text,
                                      tooltip)

CURRENT, PREVIOUS = "2024-03-31", "2023-03-31"


def traced(value, element, raw, unit="Gigajoule", status=Status.REPORTED, shown_unit="GJ", end=CURRENT):
    return Cell(value, shown_unit, status, f"{raw} {unit}", origin=[Origin(element, raw, unit, end)])


# ------------------------------------------------------------------------------------------------ the words
def test_an_origin_reads_as_element_equals_the_text_as_filed_and_its_unit():
    assert origin_text(Origin("TotalEnergyConsumed", "375373200", "Gigajoule", CURRENT)) == "TotalEnergyConsumed = 375373200 Gigajoule"


def test_an_origin_without_a_unit_does_not_invent_one():
    assert origin_text(Origin("HasTheEntityDoneIt", "true", "", CURRENT)) == "HasTheEntityDoneIt = true"


def test_a_sum_of_rows_says_how_many_rows():
    assert origin_text(Origin("OtherSources", "7", "Gigajoule", CURRENT, rows=2)) == "OtherSources = 7 Gigajoule (the sum of 2 rows)"


def test_a_long_text_is_cut_with_an_ellipsis_and_a_short_one_is_left_alone():
    assert short("a  b\n c") == "a b c"
    cut = short("word " * 100)
    assert len(cut) == MAX_TEXT and cut.endswith("…")


def test_what_is_shown_matches_the_sebi_tab():
    assert shown_text(traced(24798900.25, "E", "1")) == "2,47,98,900.25 GJ"
    assert shown_text(Cell("Yes", "", Status.REPORTED, "true")) == "Yes"
    assert shown_text(Cell()) == "Not reported"


def test_nothing_says_what_was_looked_for_or_that_the_form_has_no_field():
    assert nothing_text(Cell(note="Not found in the filing.", looked_for=["SOx", "Sox"])) == "Not found in the filing. Elements looked for: SOx, Sox."
    assert nothing_text(Cell(note="The structured filing has no field for this item.")) == "The structured filing has no field for this item."
    assert nothing_text(Cell()) == "Not found in the filing."


def test_a_hover_text_exists_only_for_a_value_that_has_a_trace():
    cell = traced(5, "NOx", "5", "Tonne")
    assert tooltip(cell) == "From the filing: NOx = 5 Tonne"
    assert tooltip(Cell()) == "" and tooltip(Cell(5, "GJ", Status.REPORTED)) == ""


def test_the_lines_of_a_cell_are_its_elements_or_the_reason_for_nothing():
    two = Cell(10, "GJ", Status.CALCULATED, origin=[Origin("A", "4", "Gigajoule", CURRENT), Origin("B", "6", "Gigajoule", CURRENT)])
    assert cell_lines(two) == ["A = 4 Gigajoule", "B = 6 Gigajoule"]
    assert cell_lines(Cell(looked_for=["X"])) == ["Not found in the filing. Elements looked for: X."]


# ------------------------------------------------------------------------------------------------ a dashboard card
def test_a_cards_trace_has_one_line_per_year_and_lists_every_ingredient_of_a_calculated_figure():
    report = blank_report()
    renewable = Metric("L1.re_total", "", traced(25, "RenewableTotal", "25"), traced(10, "RenewableTotal", "10", end=PREVIOUS))
    other = Metric("L1.nre_total", "", traced(75, "NonRenewableTotal", "75"), Cell())
    assert figure_trace(report, [renewable, other]) == [
        "FY 2023-24: RenewableTotal = 25 Gigajoule; NonRenewableTotal = 75 Gigajoule",
        "FY 2022-23: RenewableTotal = 10 Gigajoule",
    ]


def test_a_year_with_nothing_in_the_filing_says_so_instead_of_being_left_out():
    assert figure_trace(blank_report(), [Metric("k", "")]) == ["FY 2023-24: not in the filing", "FY 2022-23: not in the filing"]


# ------------------------------------------------------------------------------------------------ the full section
def test_there_is_one_trace_question_for_every_sebi_question_in_the_official_order():
    view = build_trace_view(blank_report())
    assert [q.id for q in view.questions] == [q.id for q in QUESTIONS]
    first = view.questions[0]
    assert (first.id, first.title) == ("E1", "Essential 1") and view.questions[-1].title.startswith("Leadership")


def test_every_value_row_of_every_table_question_is_traced_and_heading_rows_are_not():
    view = build_trace_view(blank_report())
    for question, traced_question in zip(QUESTIONS, view.questions):
        if question.kind == "table":
            assert [r.label for r in traced_question.rows] == [row.label for row in question.rows if not row.header], question.id


def test_a_row_shows_value_status_and_elements_for_both_years():
    report = blank_report()
    report.metrics["E1.total"].current = traced(5000, "TotalEnergy", "5000")
    report.metrics["E1.total"].previous = traced(4000, "TotalEnergy", "4000", end=PREVIOUS)
    row = next(r for r in build_trace_view(report).questions[0].rows if r.label.startswith("Total energy consumption"))
    assert (row.current.shown, row.current.status, row.current.lines) == ("5,000 GJ", "Reported by the company", ["TotalEnergy = 5000 Gigajoule"])
    assert row.previous.lines == ["TotalEnergy = 4000 Gigajoule"]


def test_a_calculated_row_keeps_our_note_and_a_converted_row_does_not_pretend_to_be_reported():
    report = blank_report()
    report.metrics["E1.electricity"].current = Cell(10, "GJ", Status.CALCULATED, "4 + 6", "Renewable + non-renewable electricity",
                                                    origin=[Origin("A", "4", "Gigajoule", CURRENT), Origin("B", "6", "Gigajoule", CURRENT)])
    report.metrics["E5.nox"].current = Cell(27000, "tonnes", Status.CONVERTED, "27 Kilotonne", "Kilotonne to tonnes", origin=[Origin("NOx", "27", "Kilotonne", CURRENT)])
    view = build_trace_view(report)
    electricity = next(r for r in view.questions[0].rows if "electricity" in r.label)
    assert (electricity.current.status, electricity.current.note) == ("Calculated by us from reported figures", "Renewable + non-renewable electricity")
    nox = next(r for q in view.questions if q.id == "E5" for r in q.rows if r.label.startswith("NOx"))
    assert nox.current.status == "Unit changed by us" and nox.current.lines == ["NOx = 27 Kilotonne"]


def test_a_missing_row_is_marked_missing_and_says_what_was_looked_for():
    report = blank_report()
    report.metrics["E5.sox"].current = Cell(note="Not found in the filing.", looked_for=["SOx"])
    row = next(r for q in build_trace_view(report).questions if q.id == "E5" for r in q.rows if r.label.startswith("SOx"))
    assert row.current.missing and row.current.shown == "Not reported" and row.current.lines == ["Not found in the filing. Elements looked for: SOx."]


def test_yes_no_and_text_questions_are_asked_for_the_current_year_only():
    question = next(q for q in build_trace_view(blank_report()).questions if q.id == "E2")
    assert [r.label for r in question.rows] == ["Answer", "Details"] and all(r.previous.not_asked for r in question.rows)


def test_list_tables_and_assurance_say_which_elements_they_were_read_from():
    report = blank_report()
    report.tables["E11"].rows = [["1", "Project"]]
    report.tables["E11"].elements = ["NameOfProject", "EiaNotificationNumber"]
    report.tables["E10"].elements = ["WhetherConditionsAreComplied"]
    report.assurance["E3"].elements = ["AnyIndependentAssuranceForWaterWithdrawal"]
    questions = {q.id: q for q in build_trace_view(report).questions}
    assert questions["E11"].remarks[0] == "The 1 row(s) of this table were read from: NameOfProject, EiaNotificationNumber."
    assert questions["E10"].remarks[0] == "The filing lists no rows. Elements looked for: WhetherConditionsAreComplied."
    assert "AnyIndependentAssuranceForWaterWithdrawal" in questions["E3"].remarks[-1]
    assert questions["E1"].remarks[-1].startswith("Assurance: not reported")


def test_facility_rows_carry_the_facilitys_name():
    report = blank_report()
    l3 = next(q for q in QUESTIONS if q.id == "L3")
    rows = {row.key: Metric(row.key, row.label, traced(1, "WaterAtFacility", "1", "Kilolitre", shown_unit="kL")) for row in l3.rows if not row.header}
    report.facilities = [Facility("Plant A", "Mining", rows)]
    question = next(q for q in build_trace_view(report).questions if q.id == "L3")
    assert question.rows and all(r.label.startswith("Plant A: ") for r in question.rows)
    assert question.rows[0].current.lines == ["WaterAtFacility = 1 Kilolitre"]


def test_extras_appear_only_when_the_filing_has_some():
    report = blank_report()
    assert build_trace_view(report).extras is None
    report.extras["X.new"] = Metric("X.new", "A new item", traced(3, "NewItem", "3"), Cell())
    assert [r.label for r in build_trace_view(report).extras.rows] == ["A new item"]


def test_the_text_report_shows_the_trace_only_when_asked():
    report = blank_report()
    report.metrics["E1.total"].current = traced(5000, "TotalEnergy", "5000")
    report.metrics["E1.total"].previous = traced(4000, "TotalEnergy", "4000", end=PREVIOUS)
    assert "↳" not in render_text(report, only=["E1"])
    text = render_text(report, only=["E1"], trace=True)
    assert "↳ FY 2023-24: TotalEnergy = 5000 Gigajoule" in text and "↳ FY 2022-23: TotalEnergy = 4000 Gigajoule" in text


def test_the_text_report_with_trace_works_for_every_kind_of_question():
    """Tables, yes/no, text, number, list and facility questions all print (an empty filing says what was looked for)."""
    text = render_text(blank_report(), trace=True)
    assert "Parameter" in text and "Answer" in text


def test_extract_report_has_a_trace_option_that_is_off_by_default():
    assert build_parser().parse_args(["--company", "x", "--fy", "2023-24"]).trace is False
    assert build_parser().parse_args(["--company", "x", "--fy", "2023-24", "--trace"]).trace is True


def test_the_filing_facts_are_copied_from_the_report():
    report = blank_report()
    report.source_file, report.source_url, report.pdf_url = "f.xml", "https://nse.example/f.xml", "https://nse.example/f.pdf"
    report.submission_date, report.revision_date, report.taxonomy_release, report.family = "03-Jun-2026", "10-Jun-2026", "2026-02-28", "modern"
    view = build_trace_view(report)
    assert (view.source_file, view.source_url, view.pdf_url) == ("f.xml", "https://nse.example/f.xml", "https://nse.example/f.pdf")
    assert view.filed == "03-Jun-2026 (revised 10-Jun-2026)" and view.edition == "2026-02-28 (modern layout)"
