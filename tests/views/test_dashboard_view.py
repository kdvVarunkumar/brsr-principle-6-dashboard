"""Tests for brsr_p6/views/dashboard_view.py: topics, charts, sentences, safeguards and the trust panel."""

import pytest
from dashboard_samples import NO_UNIT, SCALE_SLIP, ZERO_MEANING, answer, blank_report, put

from brsr_p6.analysis.comparison import IMPROVED, SAME, UNSURE, WORSE
from brsr_p6.analysis.warning_kinds import DOUBTFUL
from brsr_p6.core.models import Assurance, Status
from brsr_p6.core.paths import DEFAULT_RAW_DIR
from brsr_p6.extraction.extractor import build_report
from brsr_p6.parsing.xbrl_reader import read_filing
from brsr_p6.views.dashboard_view import build_dashboard_view, short_name

RAW = DEFAULT_RAW_DIR


def topic(view, topic_id):
    return next(t for t in view.topics if t.id == topic_id)


def reliance_like():
    """Numbers close to Reliance FY 2023-24 (see design/dashboard_mockup.html)."""
    report = blank_report("Reliance Industries Limited")
    put(report, "E1.total", 464_200_812, 473_590_585)
    put(report, "E1.fuel", 460_315_753, 468_955_154)
    put(report, "E1.electricity", 3_753_732, 4_297_652)
    put(report, "E1.other", 131_327, 337_779)
    put(report, "L1.re_total", 6_826_744, 6_705_340)
    put(report, "L1.nre_total", 457_374_068, 466_885_245)
    put(report, "E6.scope1", 36_900_275, 37_095_658, unit="tCO2e")
    put(report, "E6.scope2", 781_764, 850_070, unit="tCO2e")
    put(report, "E3.withdrawal_total", 204_100_042, 200_518_912, unit="kL")
    for key, now, before in (("surface", 98_455_582, 93_018_091), ("sea", 90_578_519, 93_084_295), ("third_party", 12_418_520, 11_844_277),
                             ("ground", 2_426_470, 2_349_164), ("others", 220_951, 223_085)):
        put(report, f"E3.{key}", now, before, unit="kL")
    put(report, "E5.nox", 32_485, 34_337, unit="tonnes")
    put(report, "E5.voc", 46_877, 46_275, unit="tonnes")
    put(report, "E8.total", 666_046, 600_609, unit="tonnes")
    put(report, "E8.recovered_total", 646_429, 583_839, unit="tonnes")
    put(report, "E8.disposed_total", 19_617, 16_770, unit="tonnes")
    for key, now, before in (("recycled", 562_805, 516_500), ("reused", 83_624, 67_339), ("other_recovery", 0, 0),
                             ("incineration", 12_554, 8_976), ("landfill", 7_053, 7_784), ("other_disposal", 10, 10)):
        put(report, f"E8.{key}", now, before, unit="tonnes")
    return report


# ------------------------------------------------------------------------------------------------ names and topics
def test_company_names_are_shortened_for_sentences():
    assert short_name("Reliance Industries Limited") == "Reliance Industries"
    assert short_name("Infosys Ltd.") == "Infosys" and short_name("Tata Steel") == "Tata Steel"


def test_a_topic_is_judged_only_by_the_headline_figures_it_could_compare():
    view = build_dashboard_view(reliance_like())
    energy, water, air = topic(view, "energy"), topic(view, "water"), topic(view, "air")
    assert (energy.chip_text, energy.stat) == ("✔ Improved", "2 figures compared")      # intensity and renewable share not filed here
    assert water.chip_text == "✖ Got worse"
    assert (air.chip_text, air.stat) == ("◐ Mixed", "1 improved, 1 worse")


def test_a_topic_with_nothing_to_compare_says_so():
    climate = topic(build_dashboard_view(blank_report()), "climate")
    assert (climate.chip_text, climate.stat) == ("? Can’t compare", "no figures to compare")
    assert climate.headline == "The company reported too little here for a one-line summary."


def test_the_scoreboard_adds_up_the_topics():
    glance = build_dashboard_view(reliance_like()).glance
    assert glance.total == glance.improved + glance.same + glance.worse > 0
    # improved: energy total, NOx.  same: renewable share, Scope 1+2, share recovered.  worse: water, VOC, waste.
    assert (glance.improved, glance.same, glance.worse) == (2, 3, 3)
    assert [tile.id for tile in glance.tiles] == ["energy", "climate", "water", "air", "waste", "safeguards"]


# ------------------------------------------------------------------------------------------------ sentences
def test_headlines_and_the_story_use_the_real_numbers():
    view = build_dashboard_view(reliance_like())
    assert topic(view, "energy").headline.startswith("Reliance Industries used 46.42 crore GJ of energy, 2.0% less than last year.")
    assert "1.47% of its energy came from renewable sources." in topic(view, "energy").headline
    assert topic(view, "climate").headline.endswith("98% of it came directly from the company's own operations.")
    assert "Its largest source was surface water (48.2%)." in topic(view, "water").headline
    assert "Compared with last year, 1 of the 2 air pollutants fell and VOC rose." == topic(view, "air").headline
    assert "97.1% of the waste handled was recycled or reused." in topic(view, "waste").headline
    story = view.glance.story
    assert story.startswith("In FY 2023-24, Reliance Industries used 46.42 crore GJ of energy (2.0% less than last year) and released")
    assert "20.41 crore kL of water" in story and "6.66 lakh tonnes of waste" in story


def test_a_doubtful_key_figure_is_left_out_of_the_text_and_the_text_says_why():
    report = reliance_like()
    for key in ("E6.scope1", "E6.scope2"):
        put(report, key, 64 if key.endswith("1") else 5, 61, unit="tCO2e", warnings=[SCALE_SLIP])
    view = build_dashboard_view(report)
    assert topic(view, "climate").headline == "The greenhouse gas figure looks doubtful, so we do not quote it."
    assert "64" not in view.glance.story and "The greenhouse gas figure looks doubtful, so we do not quote it." in view.glance.story
    assert topic(view, "climate").chip_text == "? Can’t compare"
    assert topic(view, "climate").stack is None                                  # no pie of numbers we do not believe


def test_a_figure_without_a_unit_is_not_quoted_in_a_sentence():
    report = reliance_like()
    put(report, "E1.total", 1_975_098, 1_596_500, unit="(unit not stated)", warnings=[NO_UNIT])
    view = build_dashboard_view(report)
    assert "does not state its unit, so we do not quote it" in topic(view, "energy").headline
    assert "1975098" not in view.glance.story and "19,75,098" not in view.glance.story


def test_pollutants_reported_as_zero_are_named_as_zeros_not_as_about_the_same():
    report = blank_report()
    for key in ("nox", "voc", "pop"):
        put(report, f"E5.{key}", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    air = topic(build_dashboard_view(report), "air")
    assert air.headline == "NOx, VOC and POP were reported as 0 in both years."
    assert air.chip_text == "? Can’t compare"                                    # zero against zero is not a comparison


def test_all_pollutants_falling_gets_its_own_sentence():
    report = blank_report()
    put(report, "E5.nox", 10, 20, unit="tonnes")
    put(report, "E5.sox", 5, 8, unit="tonnes")
    assert topic(build_dashboard_view(report), "air").headline == "All 2 air pollutants fell compared with last year."


# ------------------------------------------------------------------------------------------------ shared notes
def test_a_warning_shared_by_several_cards_is_shown_once_under_them():
    report = blank_report()
    for key in ("nox", "sox", "pm"):
        put(report, f"E5.{key}", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    air = topic(build_dashboard_view(report), "air")
    assert len(air.notes) == 1 and air.notes[0].text == ZERO_MEANING and air.notes[0].titles == ["NOx", "SOx", "PM"]
    nox = next(c for c in air.minis if c.id == "air_nox")
    assert nox.alerts == [] and nox.shared_alert is True and nox.trust == "check"


def test_a_warning_on_one_card_stays_on_that_card():
    report = blank_report()
    put(report, "E5.nox", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    air = topic(build_dashboard_view(report), "air")
    assert air.notes == [] and next(c for c in air.minis if c.id == "air_nox").alerts == [ZERO_MEANING]


# ------------------------------------------------------------------------------------------------ "where does it go" bars
def test_the_water_bar_is_sorted_biggest_first_and_adds_up_to_100():
    stack = topic(build_dashboard_view(reliance_like()), "water").stack
    assert [s.label for s in stack.segments][:2] == ["Surface water (rivers, lakes)", "Seawater"]
    assert sum(s.percent for s in stack.segments) == pytest.approx(100)
    assert stack.segments[0].percent_text == "48.2" and stack.segments[0].amount_text == "9.85 crore kL"


def test_the_waste_bar_keeps_its_order_and_names_the_zeros():
    stack = topic(build_dashboard_view(reliance_like()), "waste").stack
    assert [s.label for s in stack.segments] == ["Recycled", "Reused", "Burned (incinerated)", "Buried in landfill", "Other disposal"]
    assert "Other recovery" in stack.zero_note and stack.footnote.startswith("Green shades")
    assert stack.segments[-1].percent_text == "<0.01"


def test_the_climate_bar_lists_what_was_not_reported_instead_of_hiding_it():
    stack = topic(build_dashboard_view(reliance_like()), "climate").stack
    assert [s.percent_text for s in stack.segments] == ["97.9", "2.07"] and stack.missing == ["Scope 3: its supply chain"]


def test_no_bar_is_drawn_for_doubtful_parts_mixed_units_or_a_single_catch_all():
    mixed = reliance_like()
    put(mixed, "E1.fuel", 460_315_753, 468_955_154, unit="(unit not stated)")
    assert topic(build_dashboard_view(mixed), "energy").stack is None
    only_other = blank_report()
    put(only_other, "E3.others", 2_167_000, 0, unit="kL")
    assert topic(build_dashboard_view(only_other), "water").stack is None
    assert topic(build_dashboard_view(blank_report()), "energy").stack is None


# ------------------------------------------------------------------------------------------------ safeguards
def test_safeguard_answers_become_chips_and_counts():
    report = reliance_like()
    answer(report, "E2", "Yes", "RIL has several sites under the PAT scheme.")
    answer(report, "E4", "No")
    answer(report, "E12", "Not applicable", "Not Applicable")
    report.tables["E11"].rows = [["Dahej expansion", "SO 1533"], ["Nagothane expansion", "SO 1533"]]
    report.tables["E10"].rows = [["1", "Jamnagar"]]
    put(report, "L9.value", 38.01, None, unit="%")
    report.assurance["E1"] = Assurance("Yes", "Deloitte did an independent assurance.")
    report.assurance["E3"] = Assurance("No", "")
    sg = build_dashboard_view(report).safeguards
    by = {item.title.split()[0] + str(i): item for i, item in enumerate(sg.items)}
    pat, zld, eia, sensitive, laws, suppliers, auditors = (sg.items[i] for i in (0, 1, 3, 4, 5, 7, 8))
    assert (pat.chip_text, pat.more_label, pat.more) == ("✔ Yes", "What the company says", "RIL has several sites under the PAT scheme.")
    assert zld.chip_text == "✖ No" and zld.says_no
    assert eia.chip_text == "2 projects listed" and eia.more == "Dahej expansion · Nagothane expansion"
    assert sensitive.chip_text == "1 locations listed" and sensitive.more == "Jamnagar"
    assert laws.chip_text == "n/a Not applicable" and not laws.says_yes and not laws.says_no
    assert suppliers.chip_text == "38.0% of partners checked"
    assert auditors.chip_text == "✔ Yes · 1 of 9 sections" and "Not covered:" in auditors.what
    assert (sg.yes, sg.no) == (2, 1) and "answers “Yes” to 2 of the 9 safeguard questions and “No” to 1" in sg.headline
    assert "lists 1 place in or near sensitive nature areas" in sg.headline
    assert by


def test_missing_safeguard_answers_are_not_reported_never_no():
    sg = build_dashboard_view(blank_report()).safeguards
    assert all(item.chip_text in ("∅ Not reported", "None listed") for item in sg.items)
    assert (sg.yes, sg.no) == (0, 0)


def test_a_very_long_answer_is_shortened_and_points_to_the_sebi_tab():
    report = blank_report()
    answer(report, "E4", "Yes", "word " * 400)
    more = build_dashboard_view(report).safeguards.items[1].more
    assert len(more) < 700 and more.endswith("(the full answer is in the SEBI-format tab)")


# ------------------------------------------------------------------------------------------------ trust panel
def test_the_trust_panel_counts_where_the_numbers_came_from():
    report = reliance_like()
    put(report, "E5.pop", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    trust = build_dashboard_view(report).trust
    assert trust.total == trust.reported + trust.calculated + trust.converted + trust.not_reported
    assert trust.reported > 0 and trust.not_reported > 0 and trust.with_notes == 1
    assert [n.text for n in trust.notes] == [ZERO_MEANING] and trust.notes[0].titles == ["POP"]
    assert "Supply-chain emissions (Scope 3)" in trust.missing


def test_converted_and_calculated_numbers_are_counted_separately():
    report = blank_report()
    put(report, "E1.total", 1, 1, status=Status.CONVERTED)
    put(report, "E1.electricity", 1, 1, status=Status.CALCULATED)
    trust = build_dashboard_view(report).trust
    assert (trust.converted, trust.calculated) == (1, 1)


# ------------------------------------------------------------------------------------------------ real filings
def real_reports():
    files = sorted(RAW.glob("*/*/*.xml"))
    if not files:
        pytest.skip("no filings downloaded")
    for path in files:
        yield path.parts[-3], build_report(read_filing(path), path.parts[-3], path.parts[-3], path.parts[-2])


def test_reliance_fy2023_24_dashboard_matches_the_design_mockup():
    files = sorted((RAW / "RELIANCE" / "2023-24").glob("*.xml"))
    if not files:
        pytest.skip("Reliance FY 2023-24 is not downloaded")
    view = build_dashboard_view(build_report(read_filing(files[0]), "Reliance Industries Limited", "RELIANCE", "2023-24"))
    cards = {c.id: c for t in view.topics for c in t.cards + t.minis}
    assert (cards["energy_total"].big, cards["energy_total"].unit) == ("46.42", "crore GJ")
    assert (cards["energy_intensity"].big, cards["energy_intensity"].unit) == ("807", "GJ per ₹ crore")
    assert (cards["ghg_total"].big, cards["ghg_total"].unit) == ("3.77", "crore tonnes CO₂e")
    assert (cards["water_in"].big, cards["water_in"].verdict) == ("20.41", WORSE)
    assert cards["air_sox"].verdict == IMPROVED and cards["air_voc"].verdict == WORSE
    assert (cards["waste_total"].big, cards["waste_recovered"].big) == ("6.66", "97.1")
    assert (view.trust.total, view.trust.reported, view.trust.calculated, view.trust.converted) == (80, 69, 3, 1)


def test_tata_steels_misscaled_emissions_never_get_a_verdict():
    files = sorted((RAW / "TATASTEEL" / "2025-26").glob("*.xml"))
    if not files:
        pytest.skip("Tata Steel FY 2025-26 is not downloaded")
    view = build_dashboard_view(build_report(read_filing(files[0]), "Tata Steel Limited", "TATASTEEL", "2025-26"))
    cards = {c.id: c for t in view.topics for c in t.cards}
    assert cards["ghg_total"].verdict == UNSURE and cards["ghg_total"].trust == DOUBTFUL
    assert cards["ghg_intensity"].big == "Filed as 0" and cards["ghg_scope3"].verdict == UNSURE
    assert "64" not in view.glance.story


def test_dashboard_rules_hold_for_every_downloaded_filing():
    """Whatever the company: no invented numbers, no verdict on doubtful or missing figures, every figure explained."""
    for symbol, report in real_reports():
        view = build_dashboard_view(report)
        for t in view.topics:
            assert t.headline and t.intro, symbol
            for c in t.cards + t.minis:
                assert c.title and c.what and c.badge, (symbol, c.id)
                if not c.has_number:
                    assert c.value is None and c.quote == "" and c.bars == [], (symbol, c.id)
                if c.trust == DOUBTFUL or c.verdict == UNSURE:
                    assert c.verdict == UNSURE and c.bars == [] and c.delta_words == "", (symbol, c.id)
                if c.verdict in (IMPROVED, WORSE, SAME):
                    assert c.trust != DOUBTFUL and c.has_number, (symbol, c.id)
            counted = [c.verdict for c in t.cards + t.minis if c.headline]       # only comparable headline figures are counted
            assert (t.improved, t.same, t.worse) == (counted.count(IMPROVED), counted.count(SAME), counted.count(WORSE)), (symbol, t.id)
            if t.stack:
                assert sum(s.percent for s in t.stack.segments) == pytest.approx(100), (symbol, t.id)
        assert view.glance.story and view.glance.total == view.glance.improved + view.glance.same + view.glance.worse
