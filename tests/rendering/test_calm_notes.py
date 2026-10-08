"""Notes about a figure are CALM: neutral colours and an "i" symbol, never a yellow box or a warning triangle.

The numbers are still shown exactly as filed and a doubtful one still gets no verdict; only how the note LOOKS changed.  A note says how serious
it is in WORDS ("Note" for something unusual, "Doubtful" for a figure that may be wrong), not in colour.
"""

import re

from dashboard_samples import SCALE_SLIP, ZERO_MEANING, blank_report, put

from brsr_p6.rendering.render import TEMPLATE_DIR, render_page

AMBER = ("#fff3d4", "#e5b84a", "#7a4b00", "#fffdf6")          # the old yellow-ish colours


def page_with_notes():
    report = blank_report()
    put(report, "E5.nox", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])                  # a note: the 0 may mean "not measured"
    put(report, "E5.sox", 0, 0, unit="tonnes", warnings=[ZERO_MEANING])
    put(report, "E6.scope1", 64, 0, unit="tCO2e", warnings=[SCALE_SLIP])                  # doubtful: the scale looks wrong
    put(report, "E6.scope2", 5, 0, unit="tCO2e", warnings=[SCALE_SLIP])
    return render_page(report)


def test_no_page_has_a_warning_triangle():
    assert "⚠" not in page_with_notes()


def test_a_note_uses_the_i_symbol_in_the_dashboard_and_in_the_sebi_table():
    html = page_with_notes()
    assert "ⓘ Note for" in html                                   # the shared note under a topic
    assert 'class="fn fn-note"' in html and ">ⓘ1<" in html          # the mark next to a figure in the SEBI tab
    assert "ⓘ carry a note about the figure" in html              # the count in "Can I trust these numbers?"


def test_a_footnote_says_how_serious_it_is_in_words():
    html = page_with_notes()
    assert re.search(r'<li id="fn-E5-\d" class="check"><span class="fn-num">\d</span><strong>ⓘ Note:</strong> A reported 0 can mean', html)
    assert re.search(r'<li id="fn-E6-\d" class="warning"><span class="fn-num">\d</span><strong>ⓘ Doubtful:</strong> Scope 1\+2 emissions look', html)
    assert "Doubtful:</strong> A reported 0 can mean" not in html          # a mere "may be unmeasured" is not called doubtful any more


def test_a_card_does_not_repeat_see_the_note_below():
    """The topic already has ONE note under its cards; each card used to add a line pointing at it, six times in a row."""
    html = page_with_notes()
    assert "See the note below the figures" not in html
    assert "ⓘ Note on this figure" in html                         # the small label at the foot of the card is enough


def test_a_doubtful_card_keeps_its_words_and_its_no_verdict():
    html = page_with_notes()
    assert "<b>ⓘ Doubtful figure.</b>" in html and "· as filed" in html
    card = html[html.index('card doubtful'):]
    card = card[:card.index("</article>")]
    assert "chip-unsure" in card and "Got worse" not in card and "Improved" not in card      # no better / worse verdict for a figure that may be wrong


def test_no_style_sheet_uses_the_old_yellow_except_the_error_pages():
    for path in sorted(TEMPLATE_DIR.glob("*.css")) + [TEMPLATE_DIR / "style.css"]:
        if path.name == "error.css":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if line.strip().startswith("--err-"):                  # style.css keeps the amber for the error pages under its own name
                continue
            for colour in AMBER:
                assert colour not in line.lower(), f"{path.name}:{number} still uses the old yellow {colour}"


def test_the_note_colours_are_a_calm_blue_grey():
    css = (TEMPLATE_DIR / "style.css").read_text(encoding="utf-8")
    for token in ("--note-ink", "--note-bg", "--note-line"):
        assert re.search(rf"{token}:\s*#[0-9a-f]{{6}}", css), token
    assert "--warn-" not in css                                    # the old name is gone, so nothing can still point at it
    assert not [p.name for p in TEMPLATE_DIR.iterdir() if p.suffix in {".css", ".html"} and "var(--warn-" in p.read_text(encoding="utf-8")]
