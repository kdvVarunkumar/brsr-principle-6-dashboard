"""Everything the Dashboard tab shows, decided in plain Python.  The template (dashboard.html) only prints it.

Same idea as sebi_view.py: the report goes in, simple objects come out (a DashboardView), and the HTML template just loops over
them.  Deciding things here is easy to test; deciding them inside HTML is not.

The pieces:  cards (dashboard_cards.py)  ->  topics with a headline sentence, a chart and shared notes
             -> at-a-glance summary and scoreboard  ->  safeguard tiles  ->  the "can I trust this?" panel.
"""

from collections import Counter
from dataclasses import dataclass, field

from brsr_p6 import friendly
from brsr_p6 import p6_mapping as mapping
from brsr_p6.comparison import IMPROVED, SAME, WORSE, has_number, trust_of
from brsr_p6.dashboard_cards import SCALABLE_UNITS, build_card
from brsr_p6.metric_info import ASSURANCE_NAMES, GLOSSARY, METRICS, SAFEGUARDS, STACKS, TOPICS, TOPICS_BY_ID
from brsr_p6.models import Status
from brsr_p6.units import UNIT_NOT_STATED
from brsr_p6.warning_kinds import DOUBTFUL

NUMERIC_KINDS = ("energy", "water", "mass", "air", "ghg", "intensity", "percent")
QUOTE_LIMIT = 600                 # characters of a company's own answer shown before "the full answer is in the SEBI tab"
UNIT_UNKNOWN = friendly.unit_text(UNIT_NOT_STATED)

# the one figure that speaks for a topic in sentences:  topic -> (card id, verb for the story, noun, name in "the X figure ...")
KEY_FIGURES = {
    "energy": ("energy_total", "used", "energy", "energy"),
    "climate": ("ghg_total", "released", "greenhouse gases", "greenhouse gas"),
    "water": ("water_in", "took in", "water", "water"),
    "waste": ("waste_total", "produced", "waste", "waste"),
}


# ------------------------------------------------------------------------------------------------ the objects
@dataclass
class NoteView:
    text: str                     # a warning, in the filing's own plain-English words
    titles: list                  # the figures it applies to


@dataclass
class SegmentView:
    label: str
    short: str                    # how a sentence names it
    vague: bool                   # a catch-all ("Other sources"): never named in a sentence
    percent: float
    percent_text: str
    amount_text: str
    css: str


@dataclass
class StackView:
    title: str
    segments: list
    missing: list                 # parts the filing did not report
    zero_note: str
    footnote: str
    aria: str


@dataclass
class SafeguardView:
    title: str
    what: str
    chip_class: str
    chip_text: str
    says_yes: bool = False
    says_no: bool = False
    more_label: str = ""          # "What the company says" / "Which projects" ...
    more: str = ""


@dataclass
class TopicView:
    id: str
    name: str
    icon: str
    sebi: str
    intro: str
    headline: str
    chip_class: str
    chip_text: str
    stat: str
    cards: list                   # big cards
    minis: list                   # small cards
    stack: object                 # StackView or None
    notes: list                   # NoteView: warnings shared by several cards, shown once
    improved: int = 0
    same: int = 0
    worse: int = 0


@dataclass
class SafeguardsView:
    topic: object
    headline: str
    items: list
    yes: int
    no: int


@dataclass
class TileView:
    id: str
    name: str
    icon: str
    chip_class: str
    chip_text: str
    stat: str


@dataclass
class GlanceView:
    title: str
    story: str
    improved: int
    same: int
    worse: int
    total: int
    tiles: list


@dataclass
class TrustView:
    total: int
    reported: int
    calculated: int
    converted: int
    not_reported: int
    with_notes: int
    notes: list                   # NoteView
    missing: list                 # titles of the figures that were not reported


@dataclass
class DashboardView:
    glance: GlanceView
    topics: list
    safeguards: SafeguardsView
    trust: TrustView
    glossary: tuple = field(default_factory=lambda: GLOSSARY)


# ------------------------------------------------------------------------------------------------ the entry point
def build_dashboard_view(report):
    topics = [_build_topic(report, topic) for topic in TOPICS if topic.id != "safeguards"]
    safeguards = _build_safeguards(report)
    return DashboardView(
        glance=_build_glance(report, topics, safeguards),
        topics=topics,
        safeguards=safeguards,
        trust=_build_trust(report, topics),
    )


# ------------------------------------------------------------------------------------------------ topics
def _build_topic(report, topic):
    cards = [card for card in (build_card(report, info) for info in METRICS if info.topic == topic.id) if card is not None]
    notes = _lift_shared_notes(cards)
    stack = _build_stack(report, topic.id)
    counts = Counter(card.verdict for card in cards if card.headline)
    improved, same, worse = counts[IMPROVED], counts[SAME], counts[WORSE]
    chip_class, chip_text = _topic_verdict(improved, same, worse)
    return TopicView(
        id=topic.id, name=topic.name, icon=topic.icon, sebi=topic.sebi, intro=topic.intro,
        headline=_headline(report, topic.id, {card.id: card for card in cards}, stack) or _fallback(cards),
        chip_class=chip_class, chip_text=chip_text, stat=_topic_stat(improved, same, worse),
        cards=[card for card in cards if card.size == "card"], minis=[card for card in cards if card.size == "mini"],
        stack=stack, notes=notes, improved=improved, same=same, worse=worse,
    )


def _topic_verdict(improved, same, worse):
    """One word for a whole topic, from its headline figures (cards we could not compare are left out)."""
    if improved and not worse:
        return "chip-good", "✔ Improved"
    if worse and not improved:
        return "chip-bad", "✖ Got worse"
    if improved and worse:
        return "chip-same", "◐ Mixed"
    if same:
        return "chip-same", "≈ About the same"
    return "chip-unsure", "? Can’t compare"


def _topic_stat(improved, same, worse):
    compared = improved + same + worse
    if improved and worse:
        return f"{improved} improved, {worse} worse"
    if not compared:
        return "no figures to compare"
    return f"{compared} figure{'s' if compared != 1 else ''} compared"


def _lift_shared_notes(cards):
    """A warning that appears on two or more cards of a topic is shown once under the cards instead of on every card."""
    counts = Counter(alert for card in cards for alert in card.alerts)
    notes = []
    for text in [text for text, n in counts.items() if n > 1]:
        titles = []
        for card in cards:
            if text in card.alerts:
                card.alerts.remove(text)
                card.shared_alert = True
                titles.append(card.title)
        notes.append(NoteView(text, titles))
    return notes


# ------------------------------------------------------------------------------------------------ "where does it go" bars
def _amount_text(cell):
    """'46.03 crore GJ' for one part of a bar."""
    divisor, word = friendly.scale_for(cell.value) if cell.unit in SCALABLE_UNITS else (1, "")
    return f"{friendly.number_text(cell.value, divisor)} {friendly.unit_text(cell.unit, word)}"


def _build_stack(report, topic_id):
    spec = next((s for s in STACKS if s.topic == topic_id), None)
    if spec is None:
        return None
    parts = [(part, report.metrics[part.key].current) for part in spec.parts]
    numbers = [(part, cell) for part, cell in parts if has_number(cell)]
    # Percentages of a whole make no sense when the parts look doubtful or are written in different units.
    if not numbers or trust_of(*(cell for _, cell in numbers)) == DOUBTFUL or len({cell.unit for _, cell in numbers}) > 1:
        return None
    drawn = [(part, cell) for part, cell in numbers if cell.value > 0]
    whole = sum(cell.value for _, cell in drawn)
    if not whole or all(part.vague for part, _ in drawn):
        return None                        # nothing to draw, or only "Other sources": a chart that says nothing
    if spec.sort:
        drawn.sort(key=lambda pair: -pair[1].value)
    segments = [SegmentView(part.label, part.short, part.vague, cell.value / whole * 100,
                            friendly.share_text(cell.value / whole * 100), _amount_text(cell), part.css) for part, cell in drawn]
    zeros = [part.label for part, cell in numbers if cell.value == 0]
    return StackView(
        title=spec.title, segments=segments,
        missing=[part.label for part, cell in parts if not has_number(cell)],
        zero_note=("Reported as 0 (not drawn): " + ", ".join(zeros) + ".") if zeros else "",
        footnote=spec.footnote,
        aria="; ".join(f"{s.label} {s.percent_text} percent" for s in segments),
    )


# ------------------------------------------------------------------------------------------------ headline sentences
def short_name(company_name):
    """'Reliance Industries Limited' -> 'Reliance Industries'."""
    for suffix in (" Limited", " Ltd.", " Ltd"):
        if company_name.endswith(suffix):
            return company_name[: -len(suffix)]
    return company_name


def _usable(card):
    """A card whose number may be quoted in a sentence: it has a number, the number is not doubtful, and its unit is known."""
    return card is not None and card.has_number and card.trust != DOUBTFUL and card.unit != UNIT_UNKNOWN


def _not_quoted(card, label):
    """The sentence that says WHY a key figure is left out of the text ('' when it is simply not reported)."""
    if card is None or not card.has_number:
        return ""
    if card.trust == DOUBTFUL:
        return f"The {label} figure looks doubtful, so we do not quote it."
    if card.unit == UNIT_UNKNOWN:
        return f"The {label} figure does not state its unit, so we do not quote it."
    return ""


def _with(words):
    return f", {words}" if words else ""


def _join(items):
    """['a', 'b', 'c'] -> 'a, b and c'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _headline(report, topic_id, cards, stack):
    name = short_name(report.company_name)
    sentences = []
    if topic_id == "energy":
        total, renewable = cards.get("energy_total"), cards.get("renewable_share")
        if _usable(total):
            sentences.append(f"{name} used {total.quote} of energy{_with(total.delta_words)}.")
        if _usable(renewable):
            sentences.append(f"{renewable.big}% of its energy came from renewable sources.")
    elif topic_id == "climate":
        total = cards.get("ghg_total")
        if _usable(total):
            sentences.append(f"{name}'s Scope 1 + 2 emissions were {total.quote}{_with(total.delta_words)}.")
            share = _scope_1_share(report)
            if share is not None:
                sentences.append(f"{share}% of it came directly from the company's own operations.")
    elif topic_id == "water":
        total = cards.get("water_in")
        if _usable(total):
            sentences.append(f"{name} took in {total.quote} of water{_with(total.delta_words)}.")
            named = [s for s in (stack.segments if stack else []) if not s.vague]
            if named:
                biggest = max(named, key=lambda s: s.percent)
                sentences.append(f"Its largest source was {biggest.short or biggest.label.lower()} ({biggest.percent_text}%).")
    elif topic_id == "air":
        sentences.append(_air_sentence([c for c in cards.values() if c.size == "mini"]))
    elif topic_id == "waste":
        total, recovered = cards.get("waste_total"), cards.get("waste_recovered")
        if _usable(total):
            sentences.append(f"{name} produced {total.quote} of waste{_with(total.delta_words)}.")
        if _usable(recovered):
            sentences.append(f"{recovered.big}% of the waste handled was recycled or reused.")
    if topic_id in KEY_FIGURES:
        key_id, _, _, label = KEY_FIGURES[topic_id]
        sentences.append(_not_quoted(cards.get(key_id), label))
    return " ".join(s for s in sentences if s)


def _scope_1_share(report):
    """Percent of Scope 1 + 2 that is Scope 1, or None when either is missing or doubtful."""
    scope1, scope2 = report.metrics["E6.scope1"].current, report.metrics["E6.scope2"].current
    if not (has_number(scope1) and has_number(scope2)) or trust_of(scope1, scope2) == DOUBTFUL or not scope1.value + scope2.value:
        return None
    return round(scope1.value / (scope1.value + scope2.value) * 100)


def _air_sentence(cards):
    """The air pollutants in one or two sentences.  A pollutant reported as 0 in both years is named as a zero,
    never as 'about the same'."""
    zeros = [c for c in cards if c.value == 0 and c.verdict == SAME]
    compared = [c for c in cards if c.verdict in (IMPROVED, SAME, WORSE) and c not in zeros]
    fell = [c for c in compared if c.verdict == IMPROVED]
    rose = [c for c in compared if c.verdict == WORSE]
    steady = [c for c in compared if c.verdict == SAME]
    sentences = []
    if compared and len(fell) == len(compared) and len(compared) > 1:
        sentences.append(f"All {len(compared)} air pollutants fell compared with last year.")
    elif compared:
        clauses = []
        if fell:
            clauses.append(f"{len(fell)} of the {len(compared)} air pollutants fell")
        if rose:
            clauses.append(f"{_join([c.title for c in rose])} rose")
        if steady:
            clauses.append(f"{_join([c.title for c in steady])} stayed about the same")
        sentences.append("Compared with last year, " + _join(clauses) + ".")
    if zeros:
        sentences.append(f"{_join([c.title for c in zeros])} {'was' if len(zeros) == 1 else 'were'} reported as 0 in both years.")
    return " ".join(sentences)


def _fallback(cards):
    if any(card.trust == DOUBTFUL for card in cards):
        return "The figures in this section look doubtful, so we do not summarise them."
    return "The company reported too little here for a one-line summary."


# ------------------------------------------------------------------------------------------------ safeguards
def _build_safeguards(report):
    topic = TOPICS_BY_ID["safeguards"]
    items = [_safeguard(report, spec) for spec in SAFEGUARDS]
    yes, no = sum(item.says_yes for item in items), sum(item.says_no for item in items)
    return SafeguardsView(topic, _safeguards_headline(report, items, yes, no), items, yes, no)


def _safeguard(report, spec):
    view = SafeguardView(spec.title, spec.what, "chip-unsure", "∅ Not reported")
    if spec.kind == "yes_no":
        answer = report.metrics[f"{spec.source}.answer"].current
        if answer.status != Status.NOT_REPORTED:
            _set_answer(view, str(answer.value))
        details = report.metrics[f"{spec.source}.details"].current
        if _has_text(details):
            view.more_label, view.more = "What the company says", _excerpt(details.value)
    elif spec.kind == "list":
        table = report.tables[spec.source]
        count = len(table.rows)
        view.chip_class, view.chip_text = "chip-same", f"{count} {spec.noun} listed" if count else "None listed"
        if table.rows:
            view.more_label = f"Which {spec.noun}"
            view.more = " · ".join(row[spec.name_column] for row in table.rows)
        elif table.note:
            view.more_label, view.more = "About this", table.note
    elif spec.kind == "percent":
        cell = report.metrics[spec.source].current
        if has_number(cell):
            view.chip_class, view.chip_text = "chip-same", f"{friendly.share_text(cell.value)}% of partners checked"
    elif spec.kind == "assurance":
        _set_assurance(view, report)
    return view


def _has_text(cell):
    return cell.status != Status.NOT_REPORTED and isinstance(cell.value, str) and bool(cell.value.strip())


def _set_answer(view, answer):
    if answer == "Yes":
        view.chip_class, view.chip_text, view.says_yes = "chip-good", "✔ Yes", True
    elif answer == "No":
        view.chip_class, view.chip_text, view.says_no = "chip-same", "✖ No", True
    elif answer == "Not applicable":
        view.chip_class, view.chip_text = "chip-same", "n/a Not applicable"
    else:
        view.chip_class, view.chip_text = "chip-warn", f"⚠ {answer}"


def _set_assurance(view, report):
    notes = report.assurance
    checked = [qid for qid, note in notes.items() if note.carried_out == "Yes"]
    if checked:
        view.chip_class, view.chip_text, view.says_yes = "chip-good", f"✔ Yes · {len(checked)} of {len(notes)} sections", True
        left_out = [ASSURANCE_NAMES[qid] for qid in notes if qid not in checked]
        if left_out:
            view.what += " Not covered: " + ", ".join(left_out) + "."
        statement = next((notes[qid].agency for qid in checked if notes[qid].agency), "")
        if statement:
            view.more_label, view.more = "What the company says", _excerpt(statement)
    elif any(note.carried_out == "No" for note in notes.values()):
        view.chip_class, view.chip_text, view.says_no = "chip-same", "✖ No", True


def _excerpt(text):
    """The company's own words, shortened at a word boundary when very long."""
    text = " ".join(text.split())
    if len(text) <= QUOTE_LIMIT:
        return text
    return text[:QUOTE_LIMIT].rsplit(" ", 1)[0] + "… (the full answer is in the SEBI-format tab)"


def _safeguards_headline(report, items, yes, no):
    name = short_name(report.company_name)
    text = f"{name} answers “Yes” to {yes} of the {len(items)} safeguard questions and “No” to {no}."
    places = len(report.tables["E10"].rows)                      # E10 = operations in or near sensitive areas
    if places:
        text += f" It lists {places} {'place' if places == 1 else 'places'} in or near sensitive nature areas."
    return text


# ------------------------------------------------------------------------------------------------ at a glance
def _build_glance(report, topics, safeguards):
    cards = {card.id: card for topic in topics for card in topic.cards + topic.minis}
    improved = sum(topic.improved for topic in topics)
    same = sum(topic.same for topic in topics)
    worse = sum(topic.worse for topic in topics)
    tiles = [TileView(t.id, t.name, t.icon, t.chip_class, t.chip_text, t.stat) for t in topics]
    tiles.append(_safeguards_tile(safeguards))
    return GlanceView(
        title=f"How is {short_name(report.company_name)} doing on the environment?",
        story=_story(report, cards), improved=improved, same=same, worse=worse, total=improved + same + worse, tiles=tiles,
    )


def _safeguards_tile(safeguards):
    topic, total = safeguards.topic, len(safeguards.items)
    others = total - safeguards.yes - safeguards.no
    if safeguards.yes and not safeguards.no:
        chip_class, chip_text = "chip-good", f"✔ {safeguards.yes} of {total} “Yes”"
    else:
        chip_class, chip_text = "chip-same", f"{safeguards.yes} of {total} “Yes”"
    return TileView(topic.id, topic.name, topic.icon, chip_class, chip_text, f"{safeguards.no} “No”, {others} with details or n/a")


def _story(report, cards):
    """Two or three plain sentences built only from figures that are present and not doubtful."""
    clauses, left_out = {}, []
    for card_id, verb, noun, label in KEY_FIGURES.values():
        card = cards.get(card_id)
        if _usable(card):
            clauses[card_id] = f"{verb} {card.quote} of {noun}" + (f" ({card.delta_words})" if card.delta_words else "")
        elif _not_quoted(card, label):
            left_out.append(_not_quoted(card, label))
    recovered = cards.get("waste_recovered")
    if "waste_total" in clauses and _usable(recovered):
        clauses["waste_total"] += f", of which {recovered.big}% was recycled or reused"

    name = short_name(report.company_name)
    first = [clauses[card_id] for card_id in ("energy_total", "ghg_total") if card_id in clauses]
    second = [clauses[card_id] for card_id in ("water_in", "waste_total") if card_id in clauses]

    sentences = []
    if first:
        sentences.append(f"In FY {report.fy}, {name} {_join(first)}.")
    if second:
        sentences.append(f"{'It' if first else f'In FY {report.fy}, {name}'} {_join(second)}.")
    sentences += left_out
    return " ".join(sentences) or f"{name} reported too little in these areas for a summary."


# ------------------------------------------------------------------------------------------------ can I trust this?
def _build_trust(report, topics):
    cells = []
    for key, metric in list(report.metrics.items()) + list(report.extras.items()):
        source = mapping.SOURCES.get(key) or (mapping.EXTRAS[key][1] if key in mapping.EXTRAS else None)
        if source is not None and source.kind in NUMERIC_KINDS:
            cells.append(metric.current)
    statuses = Counter(cell.status for cell in cells)

    merged = {}
    missing = []
    for topic in topics:
        for note in topic.notes:
            merged.setdefault(note.text, []).extend(note.titles)
        for card in topic.cards + topic.minis:
            for alert in card.alerts:
                merged.setdefault(alert, []).append(card.title)
            if card.css == "empty":
                missing.append(card.title)
    return TrustView(
        total=len(cells), reported=statuses[Status.REPORTED], calculated=statuses[Status.CALCULATED],
        converted=statuses[Status.CONVERTED], not_reported=statuses[Status.NOT_REPORTED],
        with_notes=sum(1 for cell in cells if cell.warnings),
        notes=[NoteView(text, titles) for text, titles in merged.items()], missing=missing,
    )
