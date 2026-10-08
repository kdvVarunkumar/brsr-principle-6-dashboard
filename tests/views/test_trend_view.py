"""Tests for brsr_p6/views/trend_view.py: what the multi-year trend page says."""

from dashboard_samples import SCALE_SLIP, blank_report, put

from brsr_p6.analysis.trend_model import NOT_FILED, UNREADABLE, YearEntry, build_trend
from brsr_p6.core.models import Status
from brsr_p6.views.trend_view import build_trend_view

NO_UNIT = "This filing does not state the unit of its energy figures (the SEBI form says 'Joules or multiples'). Shown as filed."
UNKNOWN = "(unit not stated)"


def year(fy, boundary="Standalone basis", family="modern", energy=None, previous=None, unit="GJ", water=None, warnings=()):
    r = blank_report("Test Company Limited")
    r.fy, r.boundary, r.family, r.submission_date = fy, boundary, family, "01-Jul-2024"
    if energy is not None:
        put(r, "E1.total", energy, previous, unit=unit, warnings=warnings)
    if water is not None:
        put(r, "E3.withdrawal_total", water, None, unit="kL")
    return YearEntry(fy, r)


def missing(fy, kind=NOT_FILED, problem="NSE has no BRSR filing for this year."):
    return YearEntry(fy, problem=problem, kind=kind)


def view_of(*entries):
    return build_trend_view(build_trend("Test Company Limited", "TESTCO", list(entries)))


def row(view, topic_id, label_start):
    topic = next(t for t in view.topics if t.id == topic_id)
    return next(r for r in topic.rows if r.label.startswith(label_start))


def texts(r):
    return [str(c.text) for c in r.cells]


# ------------------------------------------------------------------------------------------------ columns and the summary
def test_each_year_is_a_column_with_its_basis_and_where_its_figures_come_from():
    view = view_of(missing("2021-22"), year("2022-23", "Consolidated basis", "legacy", 100, 90), year("2023-24", "Standalone basis", energy=120, previous=100))
    first, second, third = view.columns
    assert (first.fy, first.basis_text, first.source) == ("2021-22", "Consolidated", "borrowed")
    assert first.note == "no filing on NSE; figures from the FY 2022-23 filing"
    assert (second.note, third.basis_text, third.note) == ("older SEBI layout", "Standalone", "")


def test_the_summary_counts_the_real_filings_and_names_the_borrowed_year():
    view = view_of(missing("2021-22"), year("2022-23", energy=100, previous=90), year("2023-24", energy=110, previous=100))
    assert view.summary.startswith("NSE has a BRSR filing for Test Company for 2 of the 3 years from FY 2021-22 to FY 2023-24.")
    assert "FY 2021-22 has no filing of its own; its figures come from the previous-year column of the FY 2022-23 filing." in view.summary
    assert "Every year is on a standalone basis." in view.summary


def test_the_summary_and_notes_say_when_the_basis_changes():
    view = view_of(year("2022-23", "Consolidated basis", energy=100, previous=90), year("2023-24", "Standalone basis", energy=60, previous=50))
    assert "The reporting basis changes during this period (consolidated in FY 2022-23 to standalone in FY 2023-24)" in view.summary
    note = next(n for n in view.notes if n.kind == "basis")
    assert "Consolidated basis" in note.text and "Standalone basis" in note.text and "only compare years on the same basis" in note.text


def test_a_year_that_could_not_be_read_is_explained_in_the_notes_with_its_own_reason():
    view = view_of(year("2022-23", energy=100, previous=90), missing("2023-24", UNREADABLE, "x.xml is not valid XML (line 3)."))
    note = next(n for n in view.notes if n.kind == "unreadable")
    assert "FY 2023-24: x.xml is not valid XML (line 3)." in note.text and "No figures are shown for this year." in note.text
    assert view.columns[1].note == "filing could not be read"


# ------------------------------------------------------------------------------------------------ the headline rows
def test_figures_share_one_scale_one_unit_and_bars_that_start_at_zero():
    view = view_of(year("2022-23", energy=400_000_000, previous=1), year("2023-24", energy=500_000_000, previous=1))
    r = row(view, "energy", "Total energy used")
    assert texts(r) == ["40", "50"] and r.unit == "crore GJ" and r.better_label == "Lower is better ↓"
    assert [round(c.bar) for c in r.cells] == [80, 100]


def test_a_missing_year_says_no_filing_and_a_missing_figure_says_not_reported_never_zero():
    view = view_of(year("2021-22", energy=100, previous=1), year("2022-23"), missing("2023-24"))
    r = row(view, "energy", "Total energy used")
    assert texts(r) == ["100", "Not reported", "No filing"]            # the last year has no later filing to borrow from
    assert [c.css for c in r.cells] == ["", "empty", "empty"] and r.cells[2].bar is None
    assert "0" not in texts(r)


def test_a_missing_year_in_the_middle_is_filled_from_the_next_filings_previous_year_column_and_marked():
    view = view_of(year("2021-22", energy=100, previous=1), missing("2022-23"), year("2023-24", energy=120, previous=110))
    assert texts(row(view, "energy", "Total energy used")) == ["100", "110", "120"]
    assert view.columns[1].source == "borrowed" and "figures from the FY 2023-24 filing" in view.columns[1].note


def test_a_doubtful_figure_never_shows_as_a_misleading_zero_on_the_scale_of_the_other_years():
    """Tata Steel: 8 crore tonnes in earlier years, then '64' (typed in millions): on a crore scale 64 would print as 0."""
    first = year("2022-23")
    put(first.report, "E6.scope1", 80_700_000, None, unit="tCO2e")
    put(first.report, "E6.scope2", 100_000, None, unit="tCO2e")
    second = year("2023-24")
    for key, value in (("E6.scope1", 64), ("E6.scope2", 5)):
        put(second.report, key, value, None, unit="tCO2e", warnings=[SCALE_SLIP])
    r = row(view_of(first, second), "climate", "Greenhouse gases released")
    assert texts(r) == ["8.08", "69"] and r.cells[1].unit == "tonnes CO₂e" and r.cells[1].css == "doubtful" and r.cells[1].bar is None
    assert r.chip_class == "chip-unsure" and "doubtful" in r.trend


def test_an_intensity_filed_as_zero_says_so_instead_of_showing_a_bare_zero():
    entry = year("2023-24")
    put(entry.report, "E6.intensity", 0, None, unit="tCO2e per ₹",
        warnings=["Reported as 0, but the total it relates to is not zero. A real intensity is never exactly 0, so ..."])
    r = row(view_of(entry), "climate", "Greenhouse gases for every")
    assert texts(r) == ["Filed as 0"] and r.cells[0].css == "doubtful"


def test_an_item_only_newer_filings_have_is_hidden_when_no_year_has_it_and_explained_when_some_do():
    older, newer = year("2022-23", family="legacy"), year("2023-24")
    assert not any(r.label.startswith("Waste for every") for t in view_of(older, newer).topics for r in t.rows)
    put(newer.report, "X.waste_rupee", 1.2e-07, None, unit="tonnes per ₹", extra=True)
    r = row(view_of(older, newer), "waste", "Waste for every")
    assert texts(r) == ["Not in the older form", "1.2"] and r.unit == "tonnes per ₹ crore"


def test_a_figure_in_a_different_unit_keeps_its_own_unit_and_is_marked():
    entry = year("2022-23", energy=2_000_000, previous=1, unit=UNKNOWN, warnings=[NO_UNIT])
    r = row(view_of(entry, year("2023-24", energy=500_000_000, previous=1)), "energy", "Total energy used")
    assert texts(r) == ["20,00,000", "50"] and r.cells[0].unit == "unit not stated"
    assert [m.symbol for m in r.cells[0].marks] == ["ⓘ", "u"] and r.unit == "crore GJ"


# ------------------------------------------------------------------------------------------------ the trend verdict
def test_the_verdict_compares_the_latest_year_with_the_first_year_on_the_same_basis():
    view = view_of(year("2022-23", energy=100, previous=1), year("2023-24", energy=110, previous=1), year("2024-25", energy=121, previous=1))
    r = row(view, "energy", "Total energy used")
    assert r.chip_text == "✖ Got worse" and r.trend == "▲ 21.0% higher than FY 2022-23"
    assert row(view_of(year("2022-23", energy=100, previous=1), year("2023-24", energy=80, previous=1)), "energy", "Total energy").chip_text == "✔ Improved"


def test_years_before_a_change_of_basis_are_left_out_of_the_comparison_and_the_text_says_so():
    """Tata Steel: consolidated in FY 2022-23, standalone from FY 2023-24. Energy 'doubled' only because the basis changed."""
    view = view_of(year("2022-23", "Consolidated basis", energy=900, previous=1), year("2023-24", energy=500, previous=1),
                   year("2024-25", energy=550, previous=1))
    r = row(view, "energy", "Total energy used")
    assert r.chip_text == "✖ Got worse" and r.trend.startswith("▲ 10.0% higher than FY 2023-24")
    assert "earlier years use another basis or unit and are not included" in r.trend


def test_when_only_one_year_is_on_the_latest_basis_the_verdict_refuses_and_says_why():
    view = view_of(year("2022-23", "Consolidated basis", energy=900, previous=1), year("2023-24", energy=500, previous=1))
    r = row(view, "energy", "Total energy used")
    assert (r.chip_class, r.chip_text) == ("chip-unsure", "? Can’t compare")
    assert r.trend == "FY 2022-23 is on a different basis (Consolidated instead of Standalone), so the years cannot be compared."


def test_a_gap_a_unit_change_or_a_single_figure_stops_the_comparison_with_a_reason():
    gap = row(view_of(year("2021-22", energy=100, previous=1), missing("2022-23"), year("2023-24", energy=120)), "energy", "Total energy")
    assert gap.chip_text == "? Can’t compare" and gap.trend == "No figure for FY 2022-23."
    unit = row(view_of(year("2022-23", energy=500, previous=1, unit=UNKNOWN), year("2023-24", energy=500, previous=1)), "energy", "Total energy")
    assert unit.trend == "FY 2022-23 uses a different unit, so the years cannot be compared."
    one = row(view_of(year("2022-23", energy=500, previous=1)), "energy", "Total energy")
    assert one.trend == "Only one year has a figure."


def test_the_verdict_is_not_given_when_the_year_to_compare_is_zero():
    view = view_of(year("2022-23", water=0), year("2023-24", water=5_000))
    r = row(view, "water", "Water taken in")
    assert r.chip_text == "? Can’t compare" and "FY 2022-23's figure was 0" in r.trend


# ------------------------------------------------------------------------------------------------ marks and notes
def test_a_restated_figure_is_marked_and_the_mark_names_the_later_figure():
    view = view_of(year("2022-23", energy=100_000, previous=1), year("2023-24", energy=500_000, previous=140_000))
    cell = row(view, "energy", "Total energy used").cells[0]
    mark = next(m for m in cell.marks if m.symbol == "⟲")
    assert mark.title == "Restated: the FY 2023-24 filing gives 1.4 lakh GJ for this year instead of 1 lakh GJ."
    assert any(n.kind == "restated" for n in view.notes) and view.restated_total >= 1
    assert view.restatements[0].fy == "2022-23" and view.restatements[0].in_fy == "2023-24"


def test_a_difference_across_a_change_of_basis_gets_the_basis_mark_not_the_restated_mark():
    view = view_of(year("2022-23", "Consolidated basis", energy=900, previous=1), year("2023-24", energy=500, previous=300))
    marks = [m.symbol for m in row(view, "energy", "Total energy used").cells[0].marks]
    assert "≠" in marks and "⟲" not in marks and view.restated_total == 0


def test_unit_notes_are_merged_into_one_and_count_the_figures_without_a_unit():
    entry = year("2022-23", family="legacy", energy=2_000_000, previous=1, unit=UNKNOWN, warnings=[NO_UNIT])
    put(entry.report, "E3.withdrawal_total", 5, None, unit=UNKNOWN)
    notes = [n for n in view_of(entry, year("2023-24")).notes if n.kind == "units"]
    assert len(notes) == 1 and "FY 2022-23 (2 figures)" in notes[0].text


# ------------------------------------------------------------------------------------------------ every figure, year by year
def test_every_sebi_table_with_numbers_appears_with_the_official_wording_and_rows():
    view = view_of(year("2022-23", energy=100, previous=1, water=50), year("2023-24", energy=120, previous=100, water=60))
    labels = {q.label: q for q in view.questions}
    assert "Essential 1" in labels and "Essential 3" in labels and "Essential 5" not in labels      # tables with no figure at all are left out
    e1 = labels["Essential 1"]
    assert e1.text.startswith("Details of total energy consumption")
    total = next(r for r in e1.rows if r.label.startswith("Total energy consumption (A+B+C)"))
    assert texts(total) == ["100", "120"] and total.unit == "GJ"
    water = labels["Essential 3"]
    assert any(r.heading and r.label.startswith("Water withdrawal by source") for r in water.rows)      # SEBI's sub-headings are kept


def test_yes_no_answers_are_shown_per_year_and_a_borrowed_year_cannot_have_one():
    from dashboard_samples import answer
    own = year("2022-23")
    answer(own.report, "E2", "Yes")
    view = view_of(missing("2021-22"), own)
    e2 = next(q for q in view.questions if q.label == "Essential 2")
    cells = e2.rows[0].cells
    assert texts(e2.rows[0]) == ["Not in the previous-year column", "Yes"] and cells[0].css == "empty"


def test_calculated_and_converted_figures_keep_their_labels_in_the_big_tables():
    entry = year("2022-23")
    put(entry.report, "E1.electricity", 10, None, status=Status.CALCULATED)
    put(entry.report, "E1.fuel", 20, None, status=Status.CONVERTED)
    e1 = next(q for q in view_of(entry).questions if q.label == "Essential 1")
    by_label = {r.label: r for r in e1.rows if not r.heading}
    assert by_label["Total electricity consumption (A)"].cells[0].tags == ["calc."]
    assert by_label["Total fuel consumption (B)"].cells[0].tags == ["conv."]


def test_the_biggest_restatements_are_listed_first_and_capped():
    first, second = year("2022-23", energy=100, previous=1), year("2023-24", energy=500, previous=130)
    put(first.report, "E3.withdrawal_total", 1000, None, unit="kL")
    put(second.report, "E3.withdrawal_total", 1, 2000, unit="kL")
    view = view_of(first, second)
    assert [r.change for r in view.restatements[:2]] == ["100% higher", "30.0% higher"]
    assert view.restatements[0].label.startswith("Total volume of water withdrawal")
